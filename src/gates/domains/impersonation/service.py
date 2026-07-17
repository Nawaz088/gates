from __future__ import annotations

from datetime import timedelta
from typing import Any

from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from gates.core.auth import issue_jwt, issue_refresh_token, set_session_cookies
from gates.core.cache import setex as cache_setex
from gates.core.clock import now
from gates.core.errors import ForbiddenError, NotFoundError
from gates.core.instance import get_instance_id
from gates.db.models.session import Session
from gates.db.models.user import User

REFRESH_EXPIRE_DAYS = 1


async def impersonate(
    db: AsyncSession,
    admin_user_id: str,
    target_user_id: str,
    response: Response,
) -> dict[str, Any]:
    target = await db.get(User, target_user_id)
    if target is None:
        raise NotFoundError(message="Target user not found.")

    if target.banned:
        raise ForbiddenError(message="Cannot impersonate a banned user.")

    instance_id = await get_instance_id(db)
    expire_at = now() + timedelta(days=REFRESH_EXPIRE_DAYS)

    session = Session(
        user_id=target_user_id,
        instance_id=instance_id,
        status="active",
        expire_at=expire_at,
        last_active_at=now(),
    )
    db.add(session)
    await db.flush()
    await db.refresh(session)

    jwt = issue_jwt(
        user_id=target_user_id,
        session_id=session.id,
    )
    raw_refresh = issue_refresh_token()[0]
    await cache_setex(f"refresh:{raw_refresh}", REFRESH_EXPIRE_DAYS * 86400, session.id)
    set_session_cookies(response, jwt, raw_refresh)
    await db.commit()

    return {
        "status": "impersonating",
        "actor": {"type": "impersonation", "admin_id": admin_user_id},
        "target_user_id": target_user_id,
        "session_id": session.id,
    }
