from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from gates.core.auth import issue_jwt, issue_refresh_token, set_session_cookies
from gates.core.cache import setex as cache_setex
from gates.core.clock import now
from gates.core.crypto import encrypt
from gates.core.errors import NotFoundError
from gates.core.instance import ensure_default_instance, get_instance_id
from gates.db.models.external_account import ExternalAccount
from gates.db.models.session import Session
from gates.db.models.user import User
from gates.domains.oauth.apple import AppleProvider
from gates.domains.oauth.base import OAuthProvider, OAuthUserInfo
from gates.domains.oauth.github import GitHubProvider
from gates.domains.oauth.google import GoogleProvider
from gates.domains.oauth.microsoft import MicrosoftProvider

_PROVIDERS: dict[str, type[OAuthProvider]] = {
    "google": GoogleProvider,
    "github": GitHubProvider,
    "apple": AppleProvider,
    "microsoft": MicrosoftProvider,
}

REFRESH_EXPIRE_DAYS = 60


def get_provider(name: str) -> OAuthProvider:
    cls = _PROVIDERS.get(name)
    if cls is None:
        msg = f"Unsupported OAuth provider: {name}"
        raise ValueError(msg)
    return cls()


def get_authorize_url(provider: str, redirect_uri: str, state: str) -> str:
    return get_provider(provider).get_authorize_url(redirect_uri, state)


async def _build_external_account(
    db: AsyncSession,
    instance_id: str,
    user_id: str,
    provider: str,
    user_info: OAuthUserInfo,
    token: dict[str, Any],
) -> ExternalAccount:
    account = ExternalAccount(
        user_id=user_id,
        instance_id=instance_id,
        provider=provider,
        provider_user_id=user_info.provider_user_id,
        email=user_info.email,
        scopes=list(token.get("scope", "").split()),
        access_token_enc=encrypt(token.get("access_token", "")),
        refresh_token_enc=(
            encrypt(token["refresh_token"]) if token.get("refresh_token") else None
        ),
        token_expires_at=(
            datetime.fromtimestamp(token["expires_at"], tz=UTC)
            if token.get("expires_at") else None
        ),
        passwordless=True,
    )
    db.add(account)
    await db.flush()
    await db.refresh(account)
    return account


async def _create_session_and_issue_tokens(
    db: AsyncSession,
    response: Response,
    user: User,
    instance_id: str,
    email: str | None,
) -> dict[str, Any]:
    expire_at = now() + timedelta(days=REFRESH_EXPIRE_DAYS)
    session = Session(
        user_id=user.id,
        instance_id=instance_id,
        status="active",
        expire_at=expire_at,
        last_active_at=now(),
    )
    db.add(session)
    await db.flush()
    await db.refresh(session)

    jwt = issue_jwt(user_id=user.id, session_id=session.id, email=email)
    raw_refresh = issue_refresh_token()[0]
    await cache_setex(f"refresh:{raw_refresh}", REFRESH_EXPIRE_DAYS * 86400, session.id)
    set_session_cookies(response, jwt, raw_refresh)
    await db.commit()

    return {"status": "complete", "user_id": user.id, "session_id": session.id}


async def handle_callback(
    db: AsyncSession,
    provider: str,
    code: str,
    redirect_uri: str,
    response: Response,
) -> dict[str, Any]:
    p = get_provider(provider)
    token = await p.fetch_token(redirect_uri, code)
    user_info = await p.get_userinfo(token)
    instance_id = await get_instance_id(db)

    existing = await db.execute(
        select(ExternalAccount).where(
            ExternalAccount.instance_id == instance_id,
            ExternalAccount.provider == provider,
            ExternalAccount.provider_user_id == user_info.provider_user_id,
        )
    )
    ext_account = existing.scalar_one_or_none()

    if ext_account:
        user = await db.get(User, ext_account.user_id)
        if user is None:
            raise NotFoundError(message="User not found for external account.")
        return await _create_session_and_issue_tokens(
            db, response, user, instance_id, user_info.email
        )

    user_by_email = None
    if user_info.email:
        match = await db.execute(
            select(ExternalAccount).where(
                ExternalAccount.instance_id == instance_id,
                ExternalAccount.email == user_info.email,
            )
        )
        linked = match.scalar_one_or_none()
        if linked:
            user_by_email = await db.get(User, linked.user_id)

    if user_by_email:
        user = user_by_email
    else:
        await ensure_default_instance(db)
        user = User(
            instance_id=instance_id,
            first_name=user_info.first_name,
            last_name=user_info.last_name,
            image_url=user_info.picture,
        )
        db.add(user)
        await db.flush()
        await db.refresh(user)

    await _build_external_account(db, instance_id, user.id, provider, user_info, token)
    return await _create_session_and_issue_tokens(db, response, user, instance_id, user_info.email)
