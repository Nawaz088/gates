from __future__ import annotations

from datetime import timedelta

from fastapi import Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from gates.core.auth import (
    REFRESH_EXPIRE_DAYS,
    issue_jwt,
    issue_refresh_token,
    set_session_cookies,
    unset_session_cookies,
)
from gates.core.cache import delete as cache_delete
from gates.core.cache import get as cache_get
from gates.core.cache import setex as cache_setex
from gates.core.clock import now
from gates.core.errors import UnauthorizedError
from gates.core.instance import get_instance_id
from gates.db.models.session import Session
from gates.webhooks.service import dispatch_event


async def create_session(
    db: AsyncSession,
    user_id: str,
    client_id: str | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> Session:
    instance_id = await get_instance_id(db)
    expire_at = now() + timedelta(days=REFRESH_EXPIRE_DAYS)

    session = Session(
        user_id=user_id,
        instance_id=instance_id,
        client_id=client_id,
        ip_address=ip_address,
        user_agent=user_agent,
        expire_at=expire_at,
        last_active_at=now(),
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    await dispatch_event(db, "session.created", {"id": session.id, "user_id": session.user_id})
    return session


async def get_session(db: AsyncSession, session_id: str) -> Session | None:
    return await db.get(Session, session_id)


async def list_user_sessions(
    db: AsyncSession,
    user_id: str,
    include_revoked: bool = False,
) -> list[Session]:
    query = select(Session).where(Session.user_id == user_id)
    if not include_revoked:
        query = query.where(Session.status == "active")
    query = query.order_by(Session.created_at.desc())
    result = await db.execute(query)
    return list(result.scalars().all())


async def touch_session(db: AsyncSession, session_id: str) -> Session | None:
    session = await get_session(db, session_id)
    if session is None:
        return None
    session.last_active_at = now()
    await db.commit()
    await db.refresh(session)
    return session


async def revoke_session(db: AsyncSession, session_id: str) -> None:
    session = await db.get(Session, session_id)
    if session is None:
        return
    session.status = "revoked"
    await db.commit()
    await cache_delete(f"session:{session_id}:refresh")
    await dispatch_event(db, "session.revoked", {"id": session_id, "user_id": session.user_id})


async def revoke_all_sessions(
    db: AsyncSession,
    user_id: str,
    exclude_session_id: str | None = None,
) -> int:
    query = select(Session).where(
        Session.user_id == user_id,
        Session.status == "active",
    )
    result = await db.execute(query)
    sessions = list(result.scalars().all())

    count = 0
    for s in sessions:
        if s.id != exclude_session_id:
            s.status = "revoked"
            await cache_delete(f"session:{s.id}:refresh")
            count += 1
    await db.commit()
    return count


async def end_session(db: AsyncSession, session_id: str) -> None:
    session = await db.get(Session, session_id)
    if session is None:
        return
    session.status = "ended"
    await db.commit()
    await cache_delete(f"session:{session_id}:refresh")
    await dispatch_event(db, "session.ended", {"id": session_id, "user_id": session.user_id})


async def refresh_session(
    response: Response,
    db: AsyncSession,
    current_refresh_token: str | None,
) -> Session:
    if not current_refresh_token:
        raise UnauthorizedError(message="No refresh token provided.")

    stored = await cache_get(f"refresh:{current_refresh_token}")
    if stored is None:
        raise UnauthorizedError(message="Invalid or expired refresh token.")

    session_id = stored
    session = await get_session(db, session_id)
    if session is None or not session.is_valid:
        raise UnauthorizedError(message="Session is no longer valid.")

    await cache_delete(f"refresh:{current_refresh_token}")

    new_raw = issue_refresh_token()[0]
    await cache_setex(
        f"refresh:{new_raw}",
        REFRESH_EXPIRE_DAYS * 86400,
        session.id,
    )

    jwt = issue_jwt(
        user_id=session.user_id,
        session_id=session.id,
    )

    set_session_cookies(response, jwt, new_raw)
    session.last_active_at = now()
    await db.commit()
    await db.refresh(session)
    return session


async def issue_session_tokens(
    response: Response,
    db: AsyncSession,
    user_id: str,
    email: str | None = None,
    username: str | None = None,
    client_id: str | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> Session:
    session = await create_session(
        db,
        user_id=user_id,
        client_id=client_id,
        ip_address=ip_address,
        user_agent=user_agent,
    )

    jwt = issue_jwt(
        user_id=user_id,
        session_id=session.id,
        email=email,
        username=username,
    )

    raw_refresh = issue_refresh_token()[0]
    await cache_setex(
        f"refresh:{raw_refresh}",
        REFRESH_EXPIRE_DAYS * 86400,
        session.id,
    )

    set_session_cookies(response, jwt, raw_refresh)
    return session


async def logout(response: Response, db: AsyncSession, session_id: str) -> None:
    await revoke_session(db, session_id)
    unset_session_cookies(response)
