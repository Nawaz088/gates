from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from gates.core.auth import get_current_session
from gates.core.errors import NotFoundError
from gates.db.models.email_address import EmailAddress
from gates.db.models.session import Session
from gates.db.models.user import User
from gates.db.session import get_session

router = APIRouter(prefix="/v1/users", tags=["gdpr"])


@router.get("/{user_id}/export")
async def export_user_data(
    user_id: str,
    db: AsyncSession = Depends(get_session),
    auth: dict[str, Any] = Depends(get_current_session),
) -> dict[str, Any]:
    if auth["user_id"] != user_id:
        raise NotFoundError(message="User not found.")

    user = await db.get(User, user_id)
    if user is None:
        raise NotFoundError(message="User not found.")

    emails_result = await db.execute(
        select(EmailAddress).where(EmailAddress.user_id == user_id)
    )
    emails = emails_result.scalars().all()

    sessions_result = await db.execute(
        select(Session).where(Session.user_id == user_id)
    )
    sessions = sessions_result.scalars().all()

    return {
        "user": {
            "id": user.id,
            "external_id": user.external_id,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "image_url": user.image_url,
            "created_at": str(user.created_at),
            "updated_at": str(user.updated_at),
            "last_sign_in_at": str(user.last_sign_in_at) if user.last_sign_in_at else None,
            "public_metadata": user.public_metadata,
        },
        "email_addresses": [
            {
                "id": e.id,
                "email": e.email,
                "verified_at": str(e.verified_at) if e.verified_at else None,
                "created_at": str(e.created_at),
            }
            for e in emails
        ],
        "sessions": [
            {
                "id": s.id,
                "status": s.status,
                "created_at": str(s.created_at),
                "last_active_at": str(s.last_active_at),
            }
            for s in sessions
        ],
    }
