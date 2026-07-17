from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from gates.core.auth import get_current_session
from gates.db.session import get_session
from gates.domains.mfa.service import (
    disable_mfa,
    enroll_totp,
    list_factors,
    verify_backup_code,
    verify_totp,
    verify_totp_challenge,
)

router = APIRouter(prefix="/v1/users/{user_id}/mfa_factors", tags=["mfa"])


class TotpEnrollResponse(BaseModel):
    factor_id: str
    secret: str
    provisioning_uri: str
    backup_codes: list[str] = []


class VerifyCodeRequest(BaseModel):
    code: str = Field(..., min_length=6, max_length=6)


@router.get("")
async def api_list_factors(
    user_id: str,
    db: AsyncSession = Depends(get_session),
    _auth: dict[str, Any] = Depends(get_current_session),
) -> dict[str, Any]:
    factors = await list_factors(db, user_id)
    return {
        "data": [
            {
                "id": f.id,
                "type": f.type,
                "status": f.status,
                "friendly_name": f.friendly_name,
                "created_at": str(f.created_at),
            }
            for f in factors
        ],
        "total_count": len(factors),
    }


@router.post("")
async def api_enroll_totp(
    user_id: str,
    db: AsyncSession = Depends(get_session),
    _auth: dict[str, Any] = Depends(get_current_session),
) -> dict[str, Any]:
    result = await enroll_totp(db, user_id)
    return {
        "factor_id": result["factor_id"],
        "secret": result["secret"],
        "provisioning_uri": result["provisioning_uri"],
    }


@router.post("/{factor_id}/verify")
async def api_verify_totp(
    user_id: str,
    factor_id: str,
    body: VerifyCodeRequest,
    db: AsyncSession = Depends(get_session),
    _auth: dict[str, Any] = Depends(get_current_session),
) -> dict[str, Any]:
    factor = await verify_totp(db, user_id, factor_id, body.code)
    codes = getattr(factor, "_backup_codes", [])
    return {
        "status": "verified",
        "factor_id": factor.id,
        "backup_codes": codes,
    }


@router.post("/challenge")
async def api_challenge_totp(
    user_id: str,
    body: VerifyCodeRequest,
    db: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    if await verify_totp_challenge(db, user_id, body.code):
        return {"status": "verified"}
    if await verify_backup_code(db, user_id, body.code):
        return {"status": "verified", "method": "backup_code"}
    return {"status": "failed"}


@router.delete("", status_code=204)
async def api_disable_mfa(
    user_id: str,
    db: AsyncSession = Depends(get_session),
    _auth: dict[str, Any] = Depends(get_current_session),
) -> None:
    await disable_mfa(db, user_id)
