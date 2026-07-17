from __future__ import annotations

import hashlib
import hmac
import time
from datetime import timedelta
from typing import Any

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from gates.core.clock import now
from gates.core.crypto import decrypt, encrypt
from gates.core.errors import NotFoundError, ValidationError
from gates.core.instance import get_instance_id
from gates.core.security import random_token_str
from gates.db.models.webhook_delivery import WebhookDelivery
from gates.db.models.webhook_endpoint import WebhookEndpoint
from gates.webhooks.events import EVENT_SET

RETRY_DELAYS = [30, 300, 1800, 7200, 28800, 86400]
MAX_ATTEMPTS = 6
HTTP_TIMEOUT = 10


def sign_payload(payload: bytes, secret: str) -> tuple[str, str]:
    """HMAC-SHA256 sign a payload and return (signature_header, expected_signature)."""
    timestamp = str(int(time.time()))
    data = timestamp.encode() + b"." + payload
    sig = hmac.new(secret.encode(), data, hashlib.sha256).hexdigest()
    header = f"t={timestamp},v1={sig}"
    return header, sig


def verify_signature(
    payload: bytes,
    header: str,
    secret: str,
    max_age: int = 300,
) -> bool:
    parts = header.split(",")
    if len(parts) < 2:
        return False
    ts_part = parts[0]
    sig_part = parts[1]
    if not ts_part.startswith("t=") or not sig_part.startswith("v1="):
        return False
    timestamp = int(ts_part[2:])
    if abs(time.time() - timestamp) > max_age:
        return False
    data = ts_part[2:].encode() + b"." + payload
    expected = hmac.new(secret.encode(), data, hashlib.sha256).hexdigest()
    return hmac.compare_digest(sig_part[3:], expected)


async def create_endpoint(
    db: AsyncSession,
    url: str,
    events: list[str],
    enabled: bool = True,
) -> WebhookEndpoint:
    instance_id = await get_instance_id(db)

    for e in events:
        if e not in EVENT_SET:
            raise ValidationError(message=f"Unknown event: {e}")

    raw_secret = random_token_str(32)
    secret_enc = encrypt(raw_secret)

    endpoint = WebhookEndpoint(
        instance_id=instance_id,
        url=url,
        secret_enc=secret_enc,
        events=events,
        enabled=enabled,
    )
    db.add(endpoint)
    await db.commit()
    await db.refresh(endpoint)

    endpoint._raw_secret = raw_secret  # type: ignore[attr-defined]
    return endpoint


async def get_endpoint(db: AsyncSession, endpoint_id: str) -> WebhookEndpoint:
    endpoint = await db.get(WebhookEndpoint, endpoint_id)
    if endpoint is None:
        raise NotFoundError(message="Webhook endpoint not found.")
    return endpoint


async def list_endpoints(db: AsyncSession) -> list[WebhookEndpoint]:
    instance_id = await get_instance_id(db)
    result = await db.execute(
        select(WebhookEndpoint).where(WebhookEndpoint.instance_id == instance_id)
        .order_by(WebhookEndpoint.created_at.desc())
    )
    return list(result.scalars().all())


async def update_endpoint(
    db: AsyncSession,
    endpoint_id: str,
    url: str | None = None,
    events: list[str] | None = None,
    enabled: bool | None = None,
) -> WebhookEndpoint:
    endpoint = await get_endpoint(db, endpoint_id)
    if url is not None:
        endpoint.url = url
    if events is not None:
        for e in events:
            if e not in EVENT_SET:
                raise ValidationError(message=f"Unknown event: {e}")
        endpoint.events = events
    if enabled is not None:
        endpoint.enabled = enabled
    await db.commit()
    await db.refresh(endpoint)
    return endpoint


async def delete_endpoint(db: AsyncSession, endpoint_id: str) -> None:
    endpoint = await get_endpoint(db, endpoint_id)
    await db.delete(endpoint)
    await db.commit()


async def list_deliveries(
    db: AsyncSession,
    endpoint_id: str,
    limit: int = 50,
) -> list[WebhookDelivery]:
    result = await db.execute(
        select(WebhookDelivery)
        .where(WebhookDelivery.endpoint_id == endpoint_id)
        .order_by(WebhookDelivery.created_at.desc())
        .limit(limit)
    )
    return list(result.scalars().all())


async def dispatch_event(
    db: AsyncSession,
    event: str,
    payload: dict[str, Any],
) -> list[WebhookDelivery]:
    if event not in EVENT_SET:
        return []

    instance_id = await get_instance_id(db)
    result = await db.execute(
        select(WebhookEndpoint).where(
            WebhookEndpoint.instance_id == instance_id,
            WebhookEndpoint.enabled == True,  # noqa: E712
        )
    )
    endpoints = [e for e in result.scalars().all() if event in e.events]
    deliveries: list[WebhookDelivery] = []

    for endpoint in endpoints:
        delivery = WebhookDelivery(
            endpoint_id=endpoint.id,
            event=event,
            payload=payload,
            max_attempts=MAX_ATTEMPTS,
        )
        db.add(delivery)
        await db.flush()
        await db.refresh(delivery)

        await _attempt_delivery(db, endpoint, delivery)

        deliveries.append(delivery)

    await db.commit()
    return deliveries


async def _attempt_delivery(
    _db: AsyncSession,
    endpoint: WebhookEndpoint,
    delivery: WebhookDelivery,
) -> None:
    try:
        payload_bytes = delivery.payload
        import json
        body = json.dumps(payload_bytes).encode()

        secret_enc = decrypt(endpoint.secret_enc)
        sig_header, _ = sign_payload(body, secret_enc)

        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
            resp = await client.post(
                endpoint.url,
                content=body,
                headers={
                    "Content-Type": "application/json",
                    "Gates-Signature": sig_header,
                    "User-Agent": "Gates-Webhook/1.0",
                },
            )

        delivery.response_status = resp.status_code
        delivery.response_body = resp.text[:10000]
        delivery.delivered_at = now()

        if 200 <= resp.status_code < 300:
            return

    except Exception as exc:
        delivery.response_body = str(exc)[:10000]

    delivery.attempt += 1
    if delivery.attempt < delivery.max_attempts:
        delay = RETRY_DELAYS[min(delivery.attempt - 1, len(RETRY_DELAYS) - 1)]
        delivery.next_retry_at = now() + timedelta(seconds=delay)
    else:
        delivery.delivered_at = now()


async def redeliver(
    db: AsyncSession,
    endpoint_id: str,
    delivery_id: str,
) -> WebhookDelivery:
    endpoint = await get_endpoint(db, endpoint_id)
    delivery = await db.get(WebhookDelivery, delivery_id)
    if delivery is None:
        raise NotFoundError(message="Delivery not found.")

    delivery.attempt = 1
    delivery.response_status = None
    delivery.response_body = None
    delivery.delivered_at = None
    delivery.next_retry_at = None
    await _attempt_delivery(db, endpoint, delivery)
    await db.commit()
    await db.refresh(delivery)
    return delivery
