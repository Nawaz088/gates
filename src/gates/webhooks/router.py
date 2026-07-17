from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from gates.core.auth import get_current_session
from gates.db.session import get_session
from gates.webhooks.events import EVENTS
from gates.webhooks.service import (
    create_endpoint,
    delete_endpoint,
    get_endpoint,
    list_deliveries,
    list_endpoints,
    redeliver,
    update_endpoint,
)

router = APIRouter(prefix="/v1/webhooks/endpoints", tags=["webhooks"])


class EndpointCreateRequest(BaseModel):
    url: str = Field(..., max_length=1024)
    events: list[str] = Field(..., min_length=1)
    enabled: bool = True


class EndpointUpdateRequest(BaseModel):
    url: str | None = Field(None, max_length=1024)
    events: list[str] | None = None
    enabled: bool | None = None


class EndpointResponse(BaseModel):
    id: str
    url: str
    events: list[str]
    enabled: bool
    secret: str = ""


class DeliveryResponse(BaseModel):
    id: str
    endpoint_id: str
    event: str
    response_status: int | None = None
    response_body: str | None = None
    attempt: int = 1
    max_attempts: int = 6
    delivered_at: str | None = None
    next_retry_at: str | None = None
    created_at: str | None = None


@router.get("")
async def api_list_endpoints(
    db: AsyncSession = Depends(get_session),
    _auth: dict[str, Any] = Depends(get_current_session),
) -> dict[str, Any]:
    endpoints = await list_endpoints(db)
    return {
        "data": [
            {
                "id": e.id,
                "url": e.url,
                "events": e.events,
                "enabled": e.enabled,
                "created_at": str(e.created_at),
            }
            for e in endpoints
        ],
        "total_count": len(endpoints),
    }


@router.post("", status_code=201)
async def api_create_endpoint(
    body: EndpointCreateRequest,
    db: AsyncSession = Depends(get_session),
    _auth: dict[str, Any] = Depends(get_current_session),
) -> dict[str, Any]:
    endpoint = await create_endpoint(db, body.url, body.events, body.enabled)
    raw_secret = getattr(endpoint, "_raw_secret", "")
    return {
        "id": endpoint.id,
        "url": endpoint.url,
        "events": endpoint.events,
        "enabled": endpoint.enabled,
        "secret": raw_secret,
    }


@router.get("/{endpoint_id}")
async def api_get_endpoint(
    endpoint_id: str,
    db: AsyncSession = Depends(get_session),
    _auth: dict[str, Any] = Depends(get_current_session),
) -> dict[str, Any]:
    endpoint = await get_endpoint(db, endpoint_id)
    return {
        "id": endpoint.id,
        "url": endpoint.url,
        "events": endpoint.events,
        "enabled": endpoint.enabled,
        "created_at": str(endpoint.created_at),
    }


@router.patch("/{endpoint_id}")
async def api_update_endpoint(
    endpoint_id: str,
    body: EndpointUpdateRequest,
    db: AsyncSession = Depends(get_session),
    _auth: dict[str, Any] = Depends(get_current_session),
) -> dict[str, Any]:
    endpoint = await update_endpoint(
        db, endpoint_id,
        url=body.url,
        events=body.events,
        enabled=body.enabled,
    )
    return {
        "id": endpoint.id,
        "url": endpoint.url,
        "events": endpoint.events,
        "enabled": endpoint.enabled,
    }


@router.delete("/{endpoint_id}", status_code=204)
async def api_delete_endpoint(
    endpoint_id: str,
    db: AsyncSession = Depends(get_session),
    _auth: dict[str, Any] = Depends(get_current_session),
) -> None:
    await delete_endpoint(db, endpoint_id)


@router.get("/{endpoint_id}/deliveries")
async def api_list_deliveries(
    endpoint_id: str,
    db: AsyncSession = Depends(get_session),
    _auth: dict[str, Any] = Depends(get_current_session),
) -> dict[str, Any]:
    deliveries = await list_deliveries(db, endpoint_id)
    return {
        "data": [
            {
                "id": d.id,
                "endpoint_id": d.endpoint_id,
                "event": d.event,
                "response_status": d.response_status,
                "response_body": d.response_body,
                "attempt": d.attempt,
                "max_attempts": d.max_attempts,
                "delivered_at": str(d.delivered_at) if d.delivered_at else None,
                "next_retry_at": str(d.next_retry_at) if d.next_retry_at else None,
                "created_at": str(d.created_at),
            }
            for d in deliveries
        ],
        "total_count": len(deliveries),
    }


@router.post("/{endpoint_id}/deliveries/{delivery_id}/redeliver")
async def api_redeliver(
    endpoint_id: str,
    delivery_id: str,
    db: AsyncSession = Depends(get_session),
    _auth: dict[str, Any] = Depends(get_current_session),
) -> dict[str, Any]:
    delivery = await redeliver(db, endpoint_id, delivery_id)
    return {
        "id": delivery.id,
        "status": "redelivered",
        "response_status": delivery.response_status,
    }


@router.get("/events")
async def api_list_events(
    _auth: dict[str, Any] = Depends(get_current_session),
) -> dict[str, Any]:
    return {"data": EVENTS, "total_count": len(EVENTS)}
