from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from gates.core.auth import get_current_session
from gates.db.session import get_session
from gates.domains.oauth_idp.service import (
    authorize,
    create_application,
    delete_application,
    exchange_token,
    list_applications,
    userinfo,
)

router = APIRouter(prefix="/v1/oauth", tags=["oauth_idp"])


class AppCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    redirect_uris: list[str] = Field(..., min_length=1)
    scopes: list[str] = Field(default_factory=lambda: ["openid", "email", "profile"])
    homepage_url: str | None = None


class TokenRequest(BaseModel):
    client_id: str
    client_secret: str
    code: str
    redirect_uri: str


@router.get("/applications")
async def api_list_apps(
    db: AsyncSession = Depends(get_session),
    _auth: dict[str, Any] = Depends(get_current_session),
) -> dict[str, Any]:
    apps = await list_applications(db)
    return {
        "data": [
            {"id": a.id, "name": a.name, "client_id": a.client_id,
             "redirect_uris": a.redirect_uris, "scopes": a.scopes}
            for a in apps
        ],
        "total_count": len(apps),
    }


@router.post("/applications", status_code=201)
async def api_create_app(
    body: AppCreateRequest,
    db: AsyncSession = Depends(get_session),
    _auth: dict[str, Any] = Depends(get_current_session),
) -> dict[str, Any]:
    app, secret = await create_application(
        db, body.name, body.redirect_uris, body.scopes, body.homepage_url,
    )
    return {
        "id": app.id,
        "name": app.name,
        "client_id": app.client_id,
        "client_secret": secret,
        "redirect_uris": app.redirect_uris,
    }


@router.delete("/applications/{app_id}", status_code=204)
async def api_delete_app(
    app_id: str,
    db: AsyncSession = Depends(get_session),
    _auth: dict[str, Any] = Depends(get_current_session),
) -> None:
    await delete_application(db, app_id)


@router.get("/authorize")
async def api_authorize(
    client_id: str,
    redirect_uri: str = "",
    scope: str = "openid",
    _response_type: str = "code",
    db: AsyncSession = Depends(get_session),
    auth: dict[str, Any] = Depends(get_current_session),
) -> dict[str, Any]:
    redirect = await authorize(db, client_id, redirect_uri, scope, auth["user_id"])
    return {"redirect_url": redirect}


@router.post("/token")
async def api_token(
    body: TokenRequest,
    db: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    return await exchange_token(
        db, body.client_id, body.client_secret, body.code, body.redirect_uri
    )


@router.get("/userinfo")
async def api_userinfo(
    db: AsyncSession = Depends(get_session),
    auth: dict[str, Any] = Depends(get_current_session),
) -> dict[str, Any]:
    return await userinfo(db, auth.get("session_id", ""))
