from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from gates.core.permissions import require_scopes
from gates.db.session import get_session
from gates.domains.blocklist.service import add_blocklist, list_blocklist, remove_blocklist

router = APIRouter(prefix="/v1/blocklist_identifiers", tags=["blocklist"])


class BlocklistCreateRequest(BaseModel):
    type: str = Field(..., pattern=r"^(email|domain|ip|phone|username)$")
    value: str = Field(..., max_length=255)
    reason: str | None = Field(None, max_length=500)


@router.get("")
async def api_list_blocklist(
    type: str | None = None,
    db: AsyncSession = Depends(get_session),
    _auth: dict[str, Any] = Depends(require_scopes("gates:blocklist:read")),
) -> dict[str, Any]:
    entries = await list_blocklist(db, type_=type)
    return {
        "data": [
            {"id": e.id, "type": e.type, "value": e.value,
             "reason": e.reason, "created_at": str(e.created_at)}
            for e in entries
        ],
        "total_count": len(entries),
    }


@router.post("", status_code=201)
async def api_add_blocklist(
    body: BlocklistCreateRequest,
    db: AsyncSession = Depends(get_session),
    auth: dict[str, Any] = Depends(require_scopes("gates:blocklist:manage")),
) -> dict[str, Any]:
    entry = await add_blocklist(db, body.type, body.value, body.reason, auth.get("user_id"))
    return {"id": entry.id, "type": entry.type, "value": entry.value}


@router.delete("/{entry_id}", status_code=204)
async def api_remove_blocklist(
    entry_id: str,
    db: AsyncSession = Depends(get_session),
    _auth: dict[str, Any] = Depends(require_scopes("gates:blocklist:manage")),
) -> None:
    await remove_blocklist(db, entry_id)
