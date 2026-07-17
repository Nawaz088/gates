from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from gates.db.session import get_session
from gates.domains.oidc.service import (
    create_connection,
    get_authorize_url,
    get_connection,
    list_connections,
    process_callback,
)

router = APIRouter(prefix="/v1/sso/oidc", tags=["oidc"])


class OIDCCreateRequest(BaseModel):
    name: str
    issuer: str
    client_id: str
    client_secret: str
    discovery_url: str | None = None
    scopes: list[str] = ["openid", "email", "profile"]
    domains: list[str] = []


@router.get("/{connection_id}/authorize")
async def oidc_authorize(
    connection_id: str,
    db: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    conn = await get_connection(db, connection_id)
    url = get_authorize_url(conn, "/", "")
    return {"redirect_url": url}


@router.post("/{connection_id}/callback")
async def oidc_callback(
    connection_id: str,
    code: str,
    db: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    conn = await get_connection(db, connection_id)
    user_info = await process_callback(conn, code, "/")
    return user_info


@router.get("/connections")
async def api_list_oidc_connections(
    db: AsyncSession = Depends(get_session),
) -> list[dict[str, Any]]:
    conns = await list_connections(db)
    return [
        {"id": c.id, "name": c.name, "issuer": c.issuer, "active": c.active}
        for c in conns
    ]


@router.post("/connections")
async def api_create_oidc_connection(
    body: OIDCCreateRequest,
    db: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    conn = await create_connection(
        db,
        name=body.name,
        issuer=body.issuer,
        client_id=body.client_id,
        client_secret=body.client_secret,
        discovery_url=body.discovery_url,
        scopes=body.scopes,
        domains=body.domains,
    )
    return {"id": conn.id, "name": conn.name, "active": conn.active}
