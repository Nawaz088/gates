from __future__ import annotations

from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from gates.core.clock import now
from gates.core.errors import ConflictError, NotFoundError, ValidationError
from gates.core.instance import get_instance_id
from gates.core.security import random_token_str
from gates.db.models.email_address import EmailAddress
from gates.webhooks.service import dispatch_event


async def add_email(
    db: AsyncSession,
    user_id: str,
    email: str,
    verified: bool = False,
) -> EmailAddress:
    instance_id = await get_instance_id(db)

    result = await db.execute(
        select(EmailAddress).where(EmailAddress.email == email)
    )
    if result.scalar_one_or_none():
        raise ConflictError(message="This email address is already in use.")

    token = random_token_str(32) if not verified else None

    email_addr = EmailAddress(
        user_id=user_id,
        instance_id=instance_id,
        email=email.strip().lower(),
        verification_token=token,
        verification_token_expires_at=now() + timedelta(hours=24) if token else None,
        verified_at=now() if verified else None,
    )
    db.add(email_addr)
    await db.commit()
    await db.refresh(email_addr)
    await dispatch_event(
        db, "email.created",
        {"id": email_addr.id, "user_id": user_id, "email": email},
    )
    return email_addr


async def verify_email(db: AsyncSession, email_id: str, token: str) -> EmailAddress:
    email_addr = await db.get(EmailAddress, email_id)
    if email_addr is None:
        raise NotFoundError(message="Email address not found.")

    if email_addr.verified_at is not None:
        raise ValidationError(message="Email already verified.")

    if email_addr.verification_token != token:
        raise ValidationError(message="Invalid verification token.")

    expires = email_addr.verification_token_expires_at
    if expires and now() > expires:
        raise ValidationError(message="Verification token has expired.")

    email_addr.verified_at = now()
    email_addr.verification_token = None
    email_addr.verification_token_expires_at = None
    await db.commit()
    await db.refresh(email_addr)
    await dispatch_event(
        db, "email.verified",
        {"id": email_addr.id, "user_id": email_addr.user_id, "email": email_addr.email},
    )
    return email_addr


async def remove_email(db: AsyncSession, email_id: str) -> None:
    email_addr = await db.get(EmailAddress, email_id)
    if email_addr is None:
        raise NotFoundError(message="Email address not found.")
    user_id = email_addr.user_id
    email = email_addr.email
    await db.delete(email_addr)
    await db.commit()
    await dispatch_event(db, "email.deleted", {"id": email_id, "user_id": user_id, "email": email})


async def list_user_emails(
    db: AsyncSession,
    user_id: str,
) -> list[EmailAddress]:
    result = await db.execute(
        select(EmailAddress).where(EmailAddress.user_id == user_id)
    )
    return list(result.scalars().all())
