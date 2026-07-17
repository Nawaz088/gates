from __future__ import annotations

import secrets

from fastapi import APIRouter, Depends
from fastapi.responses import RedirectResponse, Response
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from gates.db.session import get_session
from gates.domains.oauth.service import get_authorize_url, handle_callback

router = APIRouter(prefix="/v1/oauth", tags=["oauth"])


class AuthorizeQuery(BaseModel):
    provider: str
    redirect: str = "/"


@router.get("/authorize")
async def oauth_authorize(
    provider: str,
    redirect: str = "/",
) -> RedirectResponse:
    state = secrets.token_urlsafe(16)
    auth_url = get_authorize_url(provider, redirect, state)
    return RedirectResponse(url=auth_url)


@router.get("/callback/{provider}")
async def oauth_callback(
    provider: str,
    code: str,
    _state: str | None = None,
    db: AsyncSession = Depends(get_session),
) -> RedirectResponse:
    result = await handle_callback(db, provider, code, "/", Response())
    session_id = result.get("session_id", "")
    return RedirectResponse(url=f"/?session_id={session_id}")
