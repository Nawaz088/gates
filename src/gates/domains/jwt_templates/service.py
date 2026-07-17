from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from gates.core.errors import ConflictError, NotFoundError, ValidationError
from gates.core.instance import get_instance_id
from gates.db.models.jwt_template import JwtTemplate


async def create_template(
    db: AsyncSession,
    name: str,
    algorithm: str = "HS256",
    lifetime: int = 3600,
    claims: dict[str, Any] | None = None,
    signing_key: str | None = None,
) -> JwtTemplate:
    instance_id = await get_instance_id(db)

    existing = await db.execute(
        select(JwtTemplate).where(
            JwtTemplate.instance_id == instance_id, JwtTemplate.name == name
        )
    )
    if existing.scalar_one_or_none():
        raise ConflictError(message=f"JWT template '{name}' already exists.")

    if algorithm not in ("HS256", "RS256"):
        raise ValidationError(message=f"Unsupported algorithm: {algorithm}")

    template = JwtTemplate(
        instance_id=instance_id,
        name=name,
        algorithm=algorithm,
        lifetime=lifetime,
        claims=claims or {},
        signing_key=signing_key,
    )
    db.add(template)
    await db.commit()
    await db.refresh(template)
    return template


async def list_templates(db: AsyncSession) -> list[JwtTemplate]:
    instance_id = await get_instance_id(db)
    result = await db.execute(
        select(JwtTemplate).where(JwtTemplate.instance_id == instance_id)
    )
    return list(result.scalars().all())


async def get_template(db: AsyncSession, template_id: str) -> JwtTemplate:
    tpl = await db.get(JwtTemplate, template_id)
    if tpl is None:
        raise NotFoundError(message="JWT template not found.")
    return tpl


async def update_template(
    db: AsyncSession,
    template_id: str,
    name: str | None = None,
    algorithm: str | None = None,
    lifetime: int | None = None,
    claims: dict[str, Any] | None = None,
    signing_key: str | None = None,
) -> JwtTemplate:
    tpl = await get_template(db, template_id)
    if name is not None:
        tpl.name = name
    if algorithm is not None:
        if algorithm not in ("HS256", "RS256"):
            raise ValidationError(message=f"Unsupported algorithm: {algorithm}")
        tpl.algorithm = algorithm
    if lifetime is not None:
        tpl.lifetime = lifetime
    if claims is not None:
        tpl.claims = claims
    if signing_key is not None:
        tpl.signing_key = signing_key
    await db.commit()
    await db.refresh(tpl)
    return tpl


async def delete_template(db: AsyncSession, template_id: str) -> None:
    tpl = await get_template(db, template_id)
    await db.delete(tpl)
    await db.commit()
