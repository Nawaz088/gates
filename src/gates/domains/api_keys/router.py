from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from gates.core.permissions import require_scopes
from gates.db.session import get_session
from gates.domains.api_keys.schemas import (
    ApiKeyCreateRequest,
    ApiKeyCreateResponse,
    ApiKeyResponse,
)
from gates.domains.api_keys.service import (
    create_api_key,
    get_api_key,
    list_api_keys,
    revoke_api_key,
)

router = APIRouter(prefix="/v1/api_keys", tags=["api_keys"])


@router.get("")
async def api_list_keys(
    db: AsyncSession = Depends(get_session),
    _auth: dict[str, Any] = Depends(require_scopes("gates:api_key:read")),
) -> dict[str, Any]:
    keys = await list_api_keys(db)
    return {
        "data": [ApiKeyResponse.model_validate(k).model_dump() for k in keys],
        "total_count": len(keys),
    }


@router.post("", status_code=201)
async def api_create_key(
    body: ApiKeyCreateRequest,
    db: AsyncSession = Depends(get_session),
    auth: dict[str, Any] = Depends(require_scopes("gates:api_key:manage")),
) -> dict[str, Any]:
    api_key, raw = await create_api_key(
        db,
        name=body.name,
        scopes=body.scopes,
        description=body.description,
        created_by=auth.get("user_id"),
    )
    return ApiKeyCreateResponse(
        id=api_key.id,
        name=api_key.name,
        description=api_key.description,
        key_prefix=api_key.key_prefix,
        scopes=api_key.scopes,
        key=raw,
        created_at=api_key.created_at,
    ).model_dump()


@router.get("/{key_id}")
async def api_get_key(
    key_id: str,
    db: AsyncSession = Depends(get_session),
    _auth: dict[str, Any] = Depends(require_scopes("gates:api_key:read")),
) -> dict[str, Any]:
    api_key = await get_api_key(db, key_id)
    return ApiKeyResponse.model_validate(api_key).model_dump()


@router.delete("/{key_id}")
async def api_revoke_key(
    key_id: str,
    db: AsyncSession = Depends(get_session),
    _auth: dict[str, Any] = Depends(require_scopes("gates:api_key:manage")),
) -> dict[str, Any]:
    api_key = await revoke_api_key(db, key_id)
    return {"status": "revoked", "id": api_key.id}
