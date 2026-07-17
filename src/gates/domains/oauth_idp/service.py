from __future__ import annotations

import hashlib
from datetime import timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from gates.core.clock import now
from gates.core.errors import NotFoundError, UnauthorizedError, ValidationError
from gates.core.instance import get_instance_id
from gates.core.security import random_token_str
from gates.db.models.oauth_application import OAuthApplication
from gates.db.models.oauth_consent import OAuthConsent
from gates.db.models.user import User

AUTH_CODE_TTL = 600


def _hash_secret(secret: str) -> str:
    return hashlib.sha256(secret.encode()).hexdigest()


def _generate_client_credentials() -> tuple[str, str, str]:
    client_id = f"gates_{random_token_str(16)}"
    client_secret = random_token_str(32)
    return client_id, client_secret, _hash_secret(client_secret)


async def create_application(
    db: AsyncSession,
    name: str,
    redirect_uris: list[str],
    scopes: list[str] | None = None,
    homepage_url: str | None = None,
) -> tuple[OAuthApplication, str]:
    instance_id = await get_instance_id(db)
    client_id, client_secret, secret_hash = _generate_client_credentials()

    app = OAuthApplication(
        instance_id=instance_id,
        name=name,
        client_id=client_id,
        client_secret_hash=secret_hash,
        redirect_uris=redirect_uris,
        scopes=scopes or ["openid", "email", "profile"],
        homepage_url=homepage_url,
    )
    db.add(app)
    await db.commit()
    await db.refresh(app)
    return app, client_secret


async def list_applications(db: AsyncSession) -> list[OAuthApplication]:
    instance_id = await get_instance_id(db)
    result = await db.execute(
        select(OAuthApplication).where(OAuthApplication.instance_id == instance_id)
    )
    return list(result.scalars().all())


async def get_application(db: AsyncSession, app_id: str) -> OAuthApplication:
    app = await db.get(OAuthApplication, app_id)
    if app is None:
        raise NotFoundError(message="Application not found.")
    return app


async def delete_application(db: AsyncSession, app_id: str) -> None:
    app = await get_application(db, app_id)
    await db.delete(app)
    await db.commit()


async def authorize(
    db: AsyncSession,
    client_id: str,
    redirect_uri: str,
    scopes: str,
    user_id: str,
) -> str:
    result = await db.execute(
        select(OAuthApplication).where(OAuthApplication.client_id == client_id)
    )
    app = result.scalar_one_or_none()
    if app is None:
        raise ValidationError(message="Invalid client_id.")

    if redirect_uri not in app.redirect_uris:
        raise ValidationError(message="Invalid redirect_uri.")

    requested_scopes = scopes.split()
    for s in requested_scopes:
        if s not in app.scopes:
            raise ValidationError(message=f"Scope '{s}' is not allowed.")

    consent = await db.execute(
        select(OAuthConsent).where(
            OAuthConsent.oauth_application_id == app.id,
            OAuthConsent.user_id == user_id,
            OAuthConsent.revoked_at.is_(None),
        )
    )
    existing_consent = consent.scalar_one_or_none()
    if existing_consent is None:
        existing_consent = OAuthConsent(
            oauth_application_id=app.id,
            user_id=user_id,
            granted_scopes=requested_scopes,
        )
        db.add(existing_consent)
    else:
        merged = list(set(existing_consent.granted_scopes + requested_scopes))
        existing_consent.granted_scopes = merged

    code = random_token_str(32)
    _auth_codes[code] = {
        "client_id": client_id,
        "user_id": user_id,
        "redirect_uri": redirect_uri,
        "scopes": requested_scopes,
        "expires_at": now() + timedelta(seconds=AUTH_CODE_TTL),
    }

    await db.commit()
    return f"{redirect_uri}?code={code}"


_auth_codes: dict[str, dict[str, Any]] = {}


async def exchange_token(
    db: AsyncSession,
    client_id: str,
    client_secret: str,
    code: str,
    redirect_uri: str,
) -> dict[str, Any]:
    code_data = _auth_codes.pop(code, None)
    if code_data is None:
        raise ValidationError(message="Invalid authorization code.")

    if code_data["expires_at"] < now():
        raise ValidationError(message="Authorization code has expired.")

    if code_data["client_id"] != client_id:
        raise ValidationError(message="Client ID mismatch.")

    if code_data["redirect_uri"] != redirect_uri:
        raise ValidationError(message="Redirect URI mismatch.")

    result = await db.execute(
        select(OAuthApplication).where(OAuthApplication.client_id == client_id)
    )
    app = result.scalar_one_or_none()
    if app is None:
        raise ValidationError(message="Application not found.")

    if _hash_secret(client_secret) != app.client_secret_hash:
        raise UnauthorizedError(message="Invalid client_secret.")

    access_token = random_token_str(32)

    return {
        "access_token": access_token,
        "token_type": "Bearer",
        "expires_in": 3600,
        "scope": " ".join(code_data["scopes"]),
    }


async def userinfo(db: AsyncSession, access_token: str) -> dict[str, Any]:
    user_id = _token_to_user.get(access_token)
    if user_id is None:
        raise UnauthorizedError(message="Invalid or expired access token.")

    user = await db.get(User, user_id)
    if user is None:
        raise NotFoundError(message="User not found.")

    return {
        "sub": user.id,
        "email": None,
        "name": f"{user.first_name or ''} {user.last_name or ''}".strip(),
        "preferred_username": user.username,
    }


_token_to_user: dict[str, str] = {}
