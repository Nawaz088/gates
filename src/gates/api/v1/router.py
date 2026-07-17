from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Request, Response
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.ext.asyncio import AsyncSession

from gates.api.v1.verifications import router as verifications_router
from gates.core.auth import get_current_session
from gates.db.session import get_session
from gates.domains.api_keys.router import router as api_keys_router
from gates.domains.email_addresses.router import router as email_router
from gates.domains.mfa.router import router as mfa_router
from gates.domains.oauth.router import router as oauth_router
from gates.domains.organizations.router import router as orgs_router
from gates.domains.passkeys.router import router as passkeys_router
from gates.domains.phone_numbers.router import router as phone_router
from gates.domains.sessions.router import router as sessions_router
from gates.domains.sessions.service import (
    issue_session_tokens,
    logout,
    refresh_session,
)
from gates.domains.users.router import router as users_router
from gates.domains.users.schemas import UserResponse
from gates.domains.users.service import (
    authenticate_user,
    change_password,
    create_user,
    request_password_reset,
    reset_password,
)
from gates.webhooks.router import router as webhooks_router

router = APIRouter(prefix="/v1")
router.include_router(users_router)
router.include_router(email_router)
router.include_router(sessions_router)
router.include_router(api_keys_router)
router.include_router(phone_router)
router.include_router(verifications_router)
router.include_router(mfa_router)
router.include_router(oauth_router)
router.include_router(orgs_router)
router.include_router(passkeys_router)
router.include_router(webhooks_router)


class SignUpRequest(BaseModel):
    email_address: list[str] = Field(default_factory=list)
    password: str | None = Field(None, min_length=8, max_length=128)
    first_name: str | None = None
    last_name: str | None = None
    username: str | None = Field(None, min_length=3, max_length=32)


class SignInRequest(BaseModel):
    identifier: str
    password: str


class SignInResponse(BaseModel):
    status: str = "complete"
    user: UserResponse | None = None
    session_id: str = ""


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirmRequest(BaseModel):
    email: EmailStr
    token: str
    new_password: str = Field(..., min_length=8, max_length=128)


class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=128)


@router.post("/sign_ups")
async def sign_up(
    response: Response,
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
    await issue_session_tokens(
        response, db,
        user_id=user.id,
        email=email,
        username=user.username,
    )
    return {
        "status": "complete",
        "user": UserResponse.model_validate(user).model_dump(),
    }


@router.post("/sign_ins")
async def sign_in(
    response: Response,
    request: Request,
    body: SignInRequest,
    db: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    user = await authenticate_user(db, body.identifier, body.password)
    await issue_session_tokens(
        response, db,
        user_id=user.id,
        email=user.primary_email_id,
        username=user.username,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    return {
        "status": "complete",
        "user": UserResponse.model_validate(user).model_dump(),
    }


@router.post("/sign_outs")
async def sign_out(
    response: Response,
    db: AsyncSession = Depends(get_session),
    auth: dict[str, Any] = Depends(get_current_session),
) -> dict[str, Any]:
    await logout(response, db, auth["session_id"])
    return {"status": "signed_out"}


@router.post("/passwords/reset")
async def password_reset_request(
    body: PasswordResetRequest,
    db: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    await request_password_reset(db, body.email)
    return {"status": "complete"}


@router.post("/passwords/reset/confirm")
async def password_reset_confirm(
    body: PasswordResetConfirmRequest,
    db: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    await reset_password(db, body.email, body.token, body.new_password)
    return {"status": "complete"}


@router.post("/passwords/change")
async def password_change(
    body: PasswordChangeRequest,
    db: AsyncSession = Depends(get_session),
    auth: dict[str, Any] = Depends(get_current_session),
) -> dict[str, Any]:
    await change_password(db, auth["user_id"], body.current_password, body.new_password)
    return {"status": "complete"}


@router.post("/tokens")
async def exchange_refresh_token(
    response: Response,
    request: Request,
    db: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    refresh_token = request.cookies.get("__session_refresh")
    session = await refresh_session(response, db, refresh_token)
    return {
        "status": "refreshed",
        "session_id": session.id,
    }


@router.get("/health")
async def v1_health() -> dict[str, Any]:
    return {"status": "ok", "version": "v1"}
