from __future__ import annotations

import logging
from typing import Any

from gates.config import settings

log = logging.getLogger("gates.email")


async def send_email(
    to: str,
    subject: str,
    text_body: str,
    html_body: str | None = None,
) -> dict[str, Any]:
    provider = settings.email_provider

    if provider == "postmark":
        return await _send_postmark(to, subject, text_body, html_body)
    elif provider == "ses":
        return await _send_ses(to, subject, text_body, html_body)
    else:
        log.info("Email stub: to=%s subject=%s body=%s", to, subject, text_body[:100])
        return {"status": "logged", "provider": "stub"}


async def _send_postmark(
    to: str,
    subject: str,
    text_body: str,
    html_body: str | None = None,
) -> dict[str, Any]:
    if not settings.postmark_token:
        log.warning("POSTMARK_TOKEN not set — falling back to stub for %s", to)
        return {"status": "logged", "provider": "postmark_stub"}

    import httpx

    payload: dict[str, Any] = {
        "From": f"noreply@{settings.cookie_domain}",
        "To": to,
        "Subject": subject,
        "TextBody": text_body,
    }
    if html_body:
        payload["HtmlBody"] = html_body

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://api.postmarkapp.com/email",
            json=payload,
            headers={
                "Accept": "application/json",
                "X-Postmark-Server-Token": settings.postmark_token,
            },
        )
    resp.raise_for_status()
    return resp.json()  # type: ignore[no-any-return]


async def _send_ses(
    to: str,
    subject: str,
    text_body: str,
    _html_body: str | None = None,
) -> dict[str, Any]:
    import boto3
    from botocore.config import Config

    client = boto3.client(
        "ses",
        region_name=settings.ses_region,
        config=Config(connect_timeout=10, read_timeout=10),
    )
    resp = client.send_email(
        Source=f"noreply@{settings.cookie_domain}",
        Destination={"ToAddresses": [to]},
        Message={
            "Subject": {"Data": subject},
            "Body": {"Text": {"Data": text_body}},
        },
    )
    return {"status": "sent", "message_id": resp.get("MessageId")}
