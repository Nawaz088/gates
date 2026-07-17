from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from gates.db.models.instance import Instance

_DEFAULT_INSTANCE_ID = "default"


async def ensure_default_instance(db: AsyncSession) -> str:
    result = await db.execute(select(Instance).limit(1))
    instance = result.scalar_one_or_none()
    if instance is None:
        instance = Instance(
            id=_DEFAULT_INSTANCE_ID,
            name="default",
            environment="development",
        )
        db.add(instance)
        await db.commit()
        await db.refresh(instance)
    return instance.id


async def get_instance_id(_db: AsyncSession) -> str:
    return _DEFAULT_INSTANCE_ID
