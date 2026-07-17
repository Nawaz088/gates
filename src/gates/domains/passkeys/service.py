from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from webauthn import verify_authentication_response, verify_registration_response
from webauthn.helpers.structs import PublicKeyCredentialDescriptor, PublicKeyCredentialType

from gates.config import settings
from gates.core.cache import get as cache_get
from gates.core.cache import setex as cache_setex
from gates.core.clock import now
from gates.core.errors import NotFoundError, ValidationError
from gates.core.security import random_token_str
from gates.db.models.passkey import Passkey
from gates.db.models.user import User

RP_NAME = "Gates"
CHALLENGE_TTL = 300


def _rp_id() -> str:
    return settings.cookie_domain


def _origin() -> str:
    return settings.public_url


async def start_registration(
    db: AsyncSession,
    user_id: str,
    user_name: str | None = None,
) -> dict[str, Any]:
    user = await db.get(User, user_id)
    if user is None:
        raise NotFoundError(message="User not found.")

    challenge = random_token_str(32)

    existing = await db.execute(
        select(Passkey.credential_id).where(Passkey.user_id == user_id)
    )
    exclude_creds = [
        PublicKeyCredentialDescriptor(type=PublicKeyCredentialType.PUBLIC_KEY, id=row[0])
        for row in existing.fetchall()
    ]

    challenge_key = f"webauthn:challenge:{user_id}"
    await cache_setex(challenge_key, CHALLENGE_TTL, challenge)

    return {
        "challenge": challenge,
        "rp_id": _rp_id(),
        "rp_name": RP_NAME,
        "user_id": user_id,
        "user_name": user_name or user_id,
        "pubkey_cred_params": [
            {"type": "public-key", "alg": -7},
            {"type": "public-key", "alg": -257},
        ],
        "timeout": 60000,
        "exclude_credentials": [
            {"type": "public-key", "id": list(cred.id)}
            for cred in exclude_creds
        ],
        "authenticator_selection": {
            "resident_key": "required",
            "user_verification": "required",
        },
    }


async def finish_registration(
    db: AsyncSession,
    user_id: str,
    credential: dict[str, Any],
    name: str | None = None,
) -> Passkey:
    challenge_key = f"webauthn:challenge:{user_id}"
    expected_challenge = await cache_get(challenge_key)
    if not expected_challenge:
        raise ValidationError(message="Registration challenge not found or expired.")

    try:
        verification = verify_registration_response(
            credential=credential,
            expected_challenge=expected_challenge.encode(),
            expected_origin=_origin(),
            expected_rp_id=_rp_id(),
        )
    except Exception as exc:
        raise ValidationError(message=f"Registration verification failed: {exc}") from exc

    response_data = credential.get("response", {})
    transports: list[str] = list(response_data.get("transports", []))

    passkey = Passkey(
        user_id=user_id,
        credential_id=verification.credential_id,
        public_key=verification.credential_public_key,
        sign_count=verification.sign_count,
        transports=transports,
        aaguid=verification.aaguid or None,
        backup_eligible=verification.credential_backed_up,
        backup_state=verification.credential_backed_up,
        name=name or f"Passkey {now().isoformat()}",
    )
    db.add(passkey)
    await db.commit()
    await db.refresh(passkey)
    return passkey


async def start_authentication(
    db: AsyncSession,
    user_id: str | None = None,
) -> dict[str, Any]:
    challenge = random_token_str(32)

    allow_creds: list[PublicKeyCredentialDescriptor] = []
    if user_id:
        existing = await db.execute(
            select(Passkey.credential_id).where(Passkey.user_id == user_id)
        )
        allow_creds = [
            PublicKeyCredentialDescriptor(type=PublicKeyCredentialType.PUBLIC_KEY, id=row[0])
            for row in existing.fetchall()
        ]

    cache_key = f"webauthn:challenge:{user_id or 'anonymous'}"
    await cache_setex(cache_key, CHALLENGE_TTL, challenge)

    return {
        "challenge": challenge,
        "rp_id": _rp_id(),
        "timeout": 60000,
        "allow_credentials": [
            {"type": "public-key", "id": list(cred.id)}
            for cred in allow_creds
        ],
        "user_verification": "required",
    }


async def finish_authentication(
    db: AsyncSession,
    credential: dict[str, Any],
    user_id: str | None = None,
) -> Passkey:
    cache_key = f"webauthn:challenge:{user_id or 'anonymous'}"
    expected_challenge = await cache_get(cache_key)
    if not expected_challenge:
        raise ValidationError(message="Authentication challenge not found or expired.")

    cred_id = bytes(credential.get("id", []))
    if not cred_id:
        raise ValidationError(message="No credential ID in response.")

    result = await db.execute(
        select(Passkey).where(Passkey.credential_id == cred_id)
    )
    passkey = result.scalar_one_or_none()
    if passkey is None:
        raise NotFoundError(message="Passkey not found.")

    try:
        verification = verify_authentication_response(
            credential=credential,
            expected_challenge=expected_challenge.encode(),
            expected_origin=_origin(),
            expected_rp_id=_rp_id(),
            credential_public_key=passkey.public_key,
            credential_current_sign_count=passkey.sign_count,
        )
    except Exception as exc:
        raise ValidationError(message=f"Authentication verification failed: {exc}") from exc

    passkey.sign_count = verification.new_sign_count
    passkey.last_used_at = now()
    await db.commit()
    await db.refresh(passkey)
    return passkey


async def list_passkeys(db: AsyncSession, user_id: str) -> list[Passkey]:
    result = await db.execute(
        select(Passkey).where(Passkey.user_id == user_id)
    )
    return list(result.scalars().all())


async def delete_passkey(db: AsyncSession, passkey_id: str) -> None:
    pk = await db.get(Passkey, passkey_id)
    if pk is None:
        raise NotFoundError(message="Passkey not found.")
    await db.delete(pk)
    await db.commit()
