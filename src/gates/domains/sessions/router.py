from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Cookie, Depends
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from gates.core.auth import get_current_session
from gates.core.errors import NotFoundError
from gates.db.session import get_session
from gates.domains.sessions.schemas import SessionResponse
from gates.domains.sessions.service import (
    end_session,
    list_user_sessions,
    refresh_session,
    revoke_all_sessions,
    revoke_session,
)
from gates.domains.sessions.service import (
    get_session as _get_session,
)

router = APIRouter(prefix="/v1/sessions", tags=["sessions"])


@router.get("")
async def api_list_sessions(
    db: AsyncSession = Depends(get_session),
    auth: dict[str, Any] = Depends(get_current_session),
) -> dict[str, Any]:
    sessions = await list_user_sessions(db, auth["user_id"])
    return {
        "data": [SessionResponse.model_validate(s) for s in sessions],
        "total_count": len(sessions),
    }


@router.get("/{session_id}")
async def api_get_session(
    session_id: str,
    db: AsyncSession = Depends(get_session),
    _auth: dict[str, Any] = Depends(get_current_session),
) -> SessionResponse:
    session = await _get_session(db, session_id)
    if session is None:
        raise NotFoundError(message="Session not found.")
    return SessionResponse.model_validate(session)


@router.post("/{session_id}/revoke")
async def api_revoke_session(
    session_id: str,
    db: AsyncSession = Depends(get_session),
    _auth: dict[str, Any] = Depends(get_current_session),
) -> dict[str, Any]:
    await revoke_session(db, session_id)
    return {"status": "revoked"}


@router.post("/revoke_all")
async def api_revoke_all_sessions(
    db: AsyncSession = Depends(get_session),
    auth: dict[str, Any] = Depends(get_current_session),
) -> dict[str, Any]:
    count = await revoke_all_sessions(db, auth["user_id"], exclude_session_id=auth["session_id"])
    return {"status": "revoked", "count": count}


@router.post("/{session_id}/end")
async def api_end_session(
    session_id: str,
    db: AsyncSession = Depends(get_session),
    _auth: dict[str, Any] = Depends(get_current_session),
) -> dict[str, Any]:
    await end_session(db, session_id)
    return {"status": "ended"}


@router.post("/refresh")
async def api_refresh_session(
    response: Response,
    db: AsyncSession = Depends(get_session),
    refresh_token: str | None = Cookie(None, alias="__session_refresh"),
) -> dict[str, Any]:
    session = await refresh_session(response, db, refresh_token)
    return {
        "status": "refreshed",
        "session": SessionResponse.model_validate(session).model_dump(),
    }


@router.get("/{session_id}/tokens")
async def api_get_session_tokens(
    session_id: str,
    db: AsyncSession = Depends(get_session),
    _auth: dict[str, Any] = Depends(get_current_session),
) -> dict[str, Any]:
    session = await _get_session(db, session_id)
    if session is None:
        raise NotFoundError(message="Session not found.")
    return {
        "object": "session_token",
        "jwt": "",
        "session_id": session.id,
        "user_id": session.user_id,
    }
