from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from jinja2 import Environment, FileSystemLoader
from sqlalchemy.ext.asyncio import AsyncSession

from gates.core.auth import get_current_session
from gates.db.session import get_session

router = APIRouter(tags=["hosted"])

TEMPLATE_DIR = "src/gates/templates"
_env = Environment(loader=FileSystemLoader(Path(TEMPLATE_DIR).resolve()))


def _html(name: str, **context: object) -> HTMLResponse:
    template = _env.get_template(name)
    return HTMLResponse(template.render(**context))


@router.get("/sign-in", response_class=HTMLResponse)
async def hosted_sign_in(request: Request) -> HTMLResponse:
    error = request.query_params.get("error", "")
    return _html("sign_in.html", title="Sign in", error=error)


@router.get("/sign-up", response_class=HTMLResponse)
async def hosted_sign_up() -> HTMLResponse:
    return _html("sign_up.html", title="Create account")


@router.get("/forgot-password", response_class=HTMLResponse)
async def hosted_forgot_password() -> HTMLResponse:
    return _html("forgot_password.html", title="Reset password")


@router.get("/verify", response_class=HTMLResponse)
async def hosted_verify(_token: str = "", _redirect: str = "") -> HTMLResponse:
    return _html("verify.html", title="Verify email", verification_id="")


@router.get("/user/profile", response_class=HTMLResponse)
async def hosted_user_profile(
    _request: Request,
    db: AsyncSession = Depends(get_session),
    auth: dict[str, Any] = Depends(get_current_session),
) -> HTMLResponse:
    from gates.domains.users.service import get_user

    user = await get_user(db, auth["user_id"])
    return _html("user_profile.html", title="Profile", user=user, email=auth.get("email"))


@router.get("/user/security", response_class=HTMLResponse)
async def hosted_user_security() -> HTMLResponse:
    return _html("user_profile.html", title="Security")
