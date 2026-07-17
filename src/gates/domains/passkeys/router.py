from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from gates.core.auth import get_current_session
from gates.db.session import get_session
from gates.domains.passkeys.service import (
    delete_passkey,
    finish_authentication,
    finish_registration,
    list_passkeys,
    start_authentication,
    start_registration,
)

router = APIRouter(prefix="/v1/passkeys", tags=["passkeys"])


@router.post("/registration/start")
async def api_registration_start(
    db: AsyncSession = Depends(get_session),
    auth: dict[str, Any] = Depends(get_current_session),
) -> dict[str, Any]:
    return await start_registration(
        db, auth["user_id"], auth.get("email") or auth["user_id"]
    )


@router.post("/registration/finish")
async def api_registration_finish(
    body: dict[str, Any],
    db: AsyncSession = Depends(get_session),
    auth: dict[str, Any] = Depends(get_current_session),
) -> dict[str, Any]:
    credential = body.get("credential", body)
    name = body.get("name")
    passkey = await finish_registration(db, auth["user_id"], credential, name=name)
    return {"status": "created", "id": passkey.id, "name": passkey.name}


@router.post("/authentication/start")
async def api_authentication_start(
    db: AsyncSession = Depends(get_session),
    auth: dict[str, Any] = Depends(get_current_session),
) -> dict[str, Any]:
    return await start_authentication(db, auth["user_id"])


@router.post("/authentication/finish")
async def api_authentication_finish(
    body: dict[str, Any],
    db: AsyncSession = Depends(get_session),
    auth: dict[str, Any] = Depends(get_current_session),
) -> dict[str, Any]:
    credential = body.get("credential", body)
    passkey = await finish_authentication(db, credential, auth["user_id"])
    return {"status": "verified", "id": passkey.id, "name": passkey.name}


@router.get("")
async def api_list_passkeys(
    db: AsyncSession = Depends(get_session),
    auth: dict[str, Any] = Depends(get_current_session),
) -> dict[str, Any]:
    pks = await list_passkeys(db, auth["user_id"])
    return {
        "data": [
            {
                "id": pk.id,
                "name": pk.name,
                "last_used_at": str(pk.last_used_at) if pk.last_used_at else None,
                "created_at": str(pk.created_at),
            }
            for pk in pks
        ],
        "total_count": len(pks),
    }


@router.delete("/{passkey_id}", status_code=204)
async def api_delete_passkey(
    passkey_id: str,
    db: AsyncSession = Depends(get_session),
    _auth: dict[str, Any] = Depends(get_current_session),
) -> None:
    await delete_passkey(db, passkey_id)
