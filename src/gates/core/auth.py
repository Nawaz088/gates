from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from fastapi import Depends, Request
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from gates.config import settings
from gates.core.clock import now
from gates.core.errors import StepUpRequiredError, UnauthorizedError
from gates.core.security import create_jwt as _create_jwt
from gates.core.security import decode_jwt as _decode_jwt
from gates.core.security import random_token_str
from gates.db.session import get_session

SESSION_COOKIE = "__session"
REFRESH_COOKIE = "__session_refresh"
CSRF_COOKIE = "__session_csrf"
JWT_EXPIRE_MINUTES = 60
REFRESH_EXPIRE_DAYS = 60
IDLE_TIMEOUT_DAYS = 7
STEP_UP_WINDOW_SECONDS = 600


def issue_jwt(
    user_id: str,
    session_id: str,
    email: str | None = None,
    username: str | None = None,
    fva: int | None = None,
    org_id: str | None = None,
    org_role: str | None = None,
    org_permissions: list[str] | None = None,
) -> str:
    claims: dict[str, Any] = {
        "sub": user_id,
        "sid": session_id,
    }
    if email:
        claims["email"] = email
    if username:
        claims["username"] = username
    if fva is not None:
        claims["fva"] = fva
    if org_id:
        claims["org_id"] = org_id
        claims["org_role"] = org_role
        claims["org_permissions"] = org_permissions or []

    return _create_jwt(claims, expire_minutes=JWT_EXPIRE_MINUTES)


def decode_jwt(token: str) -> dict[str, Any]:
    return _decode_jwt(token)


def issue_refresh_token() -> tuple[str, str]:
    raw = random_token_str(32)
    return raw, raw


def set_session_cookies(response: Response, jwt: str, refresh_token: str) -> None:
    same_site: str = settings.cookie_same_site
    response.set_cookie(
        key=SESSION_COOKIE,
        value=jwt,
        httponly=True,
        secure=settings.cookie_secure,
        samesite=same_site,  # type: ignore[arg-type]
        max_age=JWT_EXPIRE_MINUTES * 60,
        domain=settings.cookie_domain,
        path="/",
    )
    response.set_cookie(
        key=REFRESH_COOKIE,
        value=refresh_token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite=same_site,  # type: ignore[arg-type]
        max_age=REFRESH_EXPIRE_DAYS * 86400,
        domain=settings.cookie_domain,
        path="/",
    )


def unset_session_cookies(response: Response) -> None:
    for cookie in (SESSION_COOKIE, REFRESH_COOKIE, CSRF_COOKIE):
        response.delete_cookie(
            key=cookie,
            path="/",
            domain=settings.cookie_domain,
        )


def require_step_up(fva: int | None) -> None:
    if fva is None:
        return
    age = (now() - datetime.fromtimestamp(fva, tz=UTC)).total_seconds()
    if age > STEP_UP_WINDOW_SECONDS:
        raise StepUpRequiredError()


async def get_current_session(
    request: Request,
    db: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    token = request.cookies.get(SESSION_COOKIE)
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]

    if not token:
        raise UnauthorizedError(message="No session token provided.")

    from gates.domains.api_keys.service import authenticate_api_key

    if token.startswith("gates_"):
        api_key = await authenticate_api_key(db, token)
        if api_key is None:
            raise UnauthorizedError(message="Invalid or revoked API key.")

        api_key.last_used_at = now()
        await db.commit()

        return {
            "user_id": api_key.created_by or "",
            "session_id": f"apikey:{api_key.id}",
            "fva": None,
            "org_id": None,
            "org_role": None,
            "org_permissions": [],
            "scopes": api_key.scopes,
            "email": None,
            "username": None,
            "auth_type": "api_key",
        }

    try:
        payload = decode_jwt(token)
    except Exception:
        raise UnauthorizedError(message="Invalid or expired session token.") from None

    from gates.domains.sessions.service import get_session as _get_session

    session = await _get_session(db, payload.get("sid", ""))
    if session is None:
        raise UnauthorizedError(message="Session not found.")

    if session.status != "active":
        raise UnauthorizedError(message=f"Session is {session.status}.")

    if session.is_expired:
        raise UnauthorizedError(message="Session has expired.")

    return {
        "user_id": payload["sub"],
        "session_id": payload["sid"],
        "fva": payload.get("fva"),
        "org_id": payload.get("org_id"),
        "org_role": payload.get("org_role"),
        "org_permissions": payload.get("org_permissions", []),
        "scopes": [],
        "email": payload.get("email"),
        "username": payload.get("username"),
        "auth_type": "session",
    }
