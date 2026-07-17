from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.ext.asyncio import AsyncSession

from gates.db.session import get_session
from gates.domains.email_addresses.router import router as email_router
from gates.domains.users.router import router as users_router
from gates.domains.users.schemas import UserResponse
from gates.domains.users.service import (
    authenticate_user,
    change_password,
    create_user,
    request_password_reset,
    reset_password,
)

router = APIRouter(prefix="/v1")
router.include_router(users_router)
router.include_router(email_router)


class SignUpRequest(BaseModel):
    email_address: list[str] = Field(default_factory=list)
    password: str | None = Field(None, min_length=8, max_length=128)
    first_name: str | None = None
    last_name: str | None = None
    username: str | None = Field(None, min_length=3, max_length=32)


class SignUpResponse(BaseModel):
    status: str = "complete"
    user: UserResponse | None = None


class SignInRequest(BaseModel):
    identifier: str
    password: str


class SignInResponse(BaseModel):
    status: str = "complete"
    user: UserResponse | None = None


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetResponse(BaseModel):
    status: str = "complete"


class PasswordResetConfirmRequest(BaseModel):
    email: EmailStr
    token: str
    new_password: str = Field(..., min_length=8, max_length=128)


class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=128)


class PasswordChangeResponse(BaseModel):
    status: str = "complete"


@router.post("/sign_ups")
async def sign_up(
    body: SignUpRequest,
    db: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    email = body.email_address[0] if body.email_address else None
    user = await create_user(
        db,
        email=email,
        password=body.password,
        username=body.username,
        first_name=body.first_name,
        last_name=body.last_name,
    )
    return SignUpResponse(user=UserResponse.model_validate(user)).model_dump()


@router.post("/sign_ins")
async def sign_in(
    body: SignInRequest,
    db: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    user = await authenticate_user(db, body.identifier, body.password)
    return SignInResponse(user=UserResponse.model_validate(user)).model_dump()


@router.post("/passwords/reset")
async def password_reset_request(
    body: PasswordResetRequest,
    db: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    await request_password_reset(db, body.email)
    return PasswordResetResponse().model_dump()


@router.post("/passwords/reset/confirm")
async def password_reset_confirm(
    body: PasswordResetConfirmRequest,
    db: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    await reset_password(db, body.email, body.token, body.new_password)
    return PasswordChangeResponse().model_dump()


@router.post("/passwords/change")
async def password_change(
    body: PasswordChangeRequest,
    db: AsyncSession = Depends(get_session),
    user_id: str = "TODO",
) -> dict[str, Any]:
    await change_password(db, user_id, body.current_password, body.new_password)
    return PasswordChangeResponse().model_dump()


@router.get("/health")
async def v1_health() -> dict[str, Any]:
    return {"status": "ok", "version": "v1"}
