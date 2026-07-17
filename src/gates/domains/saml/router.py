from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from gates.db.session import get_session
from gates.domains.saml.service import (
    build_auth_request,
    create_connection,
    list_connections,
    process_acs_response,
    process_slo,
)

router = APIRouter(prefix="/v1/sso/saml", tags=["saml"])


@router.get("/{connection_id}/login")
async def saml_login(
    connection_id: str,
    db: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    url = await build_auth_request(db, connection_id, {})
    return {"redirect_url": url}


@router.post("/{connection_id}/acs")
async def saml_acs(
    connection_id: str,
    request: Request,
    db: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    form = await request.form()
    post_data = dict(form)
    result = await process_acs_response(db, connection_id, {}, post_data)
    return result


@router.get("/{connection_id}/slo")
async def saml_slo(
    connection_id: str,
    db: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    url = await process_slo(db, connection_id, {})
    return {"redirect_url": url}


@router.get("/connections")
async def api_list_saml_connections(
    db: AsyncSession = Depends(get_session),
) -> list[dict[str, Any]]:
    conns = await list_connections(db)
    return [
        {"id": c.id, "name": c.name, "idp_entity_id": c.idp_entity_id, "active": c.active}
        for c in conns
    ]


@router.post("/connections")
async def api_create_saml_connection(
    body: dict[str, Any],
    db: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    conn = await create_connection(
        db,
        name=body["name"],
        idp_entity_id=body["idp_entity_id"],
        idp_sso_url=body["idp_sso_url"],
        idp_certificate=body["idp_certificate"],
        sp_entity_id=body["sp_entity_id"],
        acs_url=body["acs_url"],
        domains=body.get("domains"),
        attribute_mapping=body.get("attribute_mapping"),
    )
    return {"id": conn.id, "name": conn.name, "active": conn.active}
