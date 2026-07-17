from __future__ import annotations

import re

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from gates.core.errors import ConflictError, NotFoundError, ValidationError
from gates.core.instance import get_instance_id
from gates.db.models.blocklist import Blocklist

EMAIL_RE = re.compile(r"^[^@]+@[^@]+\.[^@]+$")
DOMAIN_RE = re.compile(r"^([a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}$")
IP_RE = re.compile(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$")
PHONE_RE = re.compile(r"^\+[1-9]\d{6,14}$")
USERNAME_RE = re.compile(r"^[a-zA-Z0-9_.-]{3,32}$")

BLOCKLIST_TYPES = {"email", "domain", "ip", "phone", "username"}


def _validate(type_: str, value: str) -> None:
    if type_ not in BLOCKLIST_TYPES:
        raise ValidationError(message=f"Invalid blocklist type: {type_}")
    validators = {
        "email": EMAIL_RE,
        "domain": DOMAIN_RE,
        "ip": IP_RE,
        "phone": PHONE_RE,
        "username": USERNAME_RE,
    }
    validator = validators.get(type_)
    if validator and not validator.match(value):
        raise ValidationError(message=f"Invalid format for {type_}: {value}")


async def add_blocklist(
    db: AsyncSession,
    type_: str,
    value: str,
    reason: str | None = None,
    created_by: str | None = None,
) -> Blocklist:
    instance_id = await get_instance_id(db)
    _validate(type_, value)

    existing = await db.execute(
        select(Blocklist).where(
            Blocklist.instance_id == instance_id,
            Blocklist.type == type_,
            Blocklist.value == value,
        )
    )
    if existing.scalar_one_or_none():
        raise ConflictError(message=f"'{value}' is already in the blocklist.")

    entry = Blocklist(
        instance_id=instance_id,
        type=type_,
        value=value,
        reason=reason,
        created_by=created_by,
    )
    db.add(entry)
    await db.commit()
    await db.refresh(entry)
    return entry


async def remove_blocklist(db: AsyncSession, entry_id: str) -> None:
    entry = await db.get(Blocklist, entry_id)
    if entry is None:
        raise NotFoundError(message="Blocklist entry not found.")
    await db.delete(entry)
    await db.commit()


async def list_blocklist(
    db: AsyncSession,
    type_: str | None = None,
) -> list[Blocklist]:
    instance_id = await get_instance_id(db)
    query = select(Blocklist).where(Blocklist.instance_id == instance_id)
    if type_:
        query = query.where(Blocklist.type == type_)
    query = query.order_by(Blocklist.created_at.desc())
    result = await db.execute(query)
    return list(result.scalars().all())


async def is_blocked(db: AsyncSession, type_: str, value: str) -> bool:
    instance_id = await get_instance_id(db)
    result = await db.execute(
        select(Blocklist).where(
            Blocklist.instance_id == instance_id,
            Blocklist.type == type_,
            Blocklist.value == value,
        )
    )
    return result.scalar_one_or_none() is not None
