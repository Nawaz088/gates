from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from gates.core.errors import NotFoundError, ValidationError
from gates.core.instance import get_instance_id
from gates.core.security import random_token_str
from gates.db.models.api_key import ApiKey

_API_KEY_PREFIX = "gates_"


def _hash_key(raw: str) -> str:
    import hashlib
    return hashlib.sha256(raw.encode()).hexdigest()


def _generate_api_key() -> tuple[str, str, str]:
    raw = _API_KEY_PREFIX + random_token_str(32)
    prefix = raw[:8]
    h = _hash_key(raw)
    return raw, prefix, h


async def create_api_key(
    db: AsyncSession,
    name: str,
    scopes: list[str] | None = None,
    description: str | None = None,
    created_by: str | None = None,
) -> tuple[ApiKey, str]:
    from gates.domains.roles.registry import SYSTEM_PERMISSION_SET

    for s in (scopes or []):
        api_scope = s.replace("gates:", "", 1) if s.startswith("gates:") else s
        if api_scope != "*" and api_scope not in SYSTEM_PERMISSION_SET:
            raise ValidationError(message=f"Unknown scope: {s}")

    instance_id = await get_instance_id(db)
    raw, prefix, key_hash = _generate_api_key()

    api_key = ApiKey(
        instance_id=instance_id,
        name=name,
        description=description,
        key_prefix=prefix,
        key_hash=key_hash,
        scopes=scopes or [],
        created_by=created_by,
    )
    db.add(api_key)
    await db.commit()
    await db.refresh(api_key)
    return api_key, raw


async def list_api_keys(db: AsyncSession) -> list[ApiKey]:
    instance_id = await get_instance_id(db)
    result = await db.execute(
        select(ApiKey)
        .where(ApiKey.instance_id == instance_id, ApiKey.revoked_at.is_(None))
        .order_by(ApiKey.created_at.desc())
    )
    return list(result.scalars().all())


async def get_api_key(db: AsyncSession, key_id: str) -> ApiKey:
    api_key = await db.get(ApiKey, key_id)
    if api_key is None:
        raise NotFoundError(message="API key not found.")
    return api_key


async def revoke_api_key(db: AsyncSession, key_id: str) -> ApiKey:
    api_key = await get_api_key(db, key_id)
    if api_key.revoked_at is not None:
        raise ValidationError(message="API key is already revoked.")
    api_key.revoked_at = datetime.now(UTC)
    await db.commit()
    await db.refresh(api_key)
    return api_key


async def authenticate_api_key(db: AsyncSession, raw_key: str) -> ApiKey | None:
    if not raw_key.startswith(_API_KEY_PREFIX):
        return None

    prefix = raw_key[:8]
    key_hash = _hash_key(raw_key)

    result = await db.execute(
        select(ApiKey).where(
            ApiKey.key_prefix == prefix,
            ApiKey.key_hash == key_hash,
            ApiKey.revoked_at.is_(None),
        )
    )
    api_key = result.scalar_one_or_none()
    return api_key
