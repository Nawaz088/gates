from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from gates.db.session import get_session
from gates.domains.magic_links.service import create_magic_link
from gates.domains.otp.service import send_otp, verify_otp

router = APIRouter(prefix="/v1/verifications", tags=["verifications"])


class StartVerificationRequest(BaseModel):
    strategy: str = Field(..., pattern=r"^(email_code|email_link|phone_code)$")
    target: str = Field(..., max_length=255)


class StartVerificationResponse(BaseModel):
    id: str
    strategy: str
    target: str
    status: str = "pending"


class AttemptVerificationRequest(BaseModel):
    code: str = Field(..., min_length=4, max_length=8)


class AttemptVerificationResponse(BaseModel):
    id: str
    status: str = "complete"
    verified: bool = True


@router.post("")
async def start_verification(
    body: StartVerificationRequest,
    db: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    if body.strategy == "email_link":
        verification, _ = await create_magic_link(
            db, email=body.target,
        )
        return {
            "id": verification.id,
            "strategy": body.strategy,
            "target": body.target,
            "status": "pending",
        }

    verification = await send_otp(
        db,
        target=body.target,
        strategy=body.strategy,
    )
    return {
        "id": verification.id,
        "strategy": body.strategy,
        "target": body.target,
        "status": "pending",
    }


@router.post("/{verification_id}/attempt")
async def attempt_verification(
    verification_id: str,
    body: AttemptVerificationRequest,
    db: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    verification = await verify_otp(db, verification_id, body.code)
    return {
        "id": verification.id,
        "status": "complete",
        "verified": True,
    }
