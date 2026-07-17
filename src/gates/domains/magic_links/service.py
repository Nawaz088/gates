from __future__ import annotations

import hashlib
from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from gates.config import settings
from gates.core.clock import now
from gates.core.email import send_email
from gates.core.errors import ValidationError
from gates.core.instance import get_instance_id
from gates.core.security import random_token_str
from gates.db.models.verification import Verification

MAGIC_LINK_TTL_MINUTES = 10


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


async def create_magic_link(
    db: AsyncSession,
    email: str,
    user_id: str | None = None,
    redirect_url: str | None = None,
) -> tuple[Verification, str]:
    instance_id = await get_instance_id(db)
    raw_token = random_token_str(32)
    token_hash = _hash_token(raw_token)

    old_verifications = await db.execute(
        select(Verification).where(
            Verification.target == email,
            Verification.strategy == "email_link",
            Verification.consumed_at.is_(None),
        )
    )
    for v in old_verifications.scalars().all():
        v.consumed_at = now()

    verification = Verification(
        instance_id=instance_id,
        user_id=user_id,
        type="magic_link",
        strategy="email_link",
        target=email,
        token_hash=token_hash,
        expires_at=now() + timedelta(minutes=MAGIC_LINK_TTL_MINUTES),
        extra_data={"redirect_url": redirect_url} if redirect_url else {},
    )
    db.add(verification)
    await db.commit()
    await db.refresh(verification)

    link = f"{settings.public_url}/verify?token={raw_token}&redirect={redirect_url or ''}"
    expires = MAGIC_LINK_TTL_MINUTES

    await send_email(
        to=email,
        subject="Sign in to your account",
        text_body=f"Click this link to sign in: {link}\n\nThis link expires in {expires} minutes.",
        html_body=(
            f"<p><a href='{link}'>Click here to sign in</a></p>"
            f"<p>This link expires in {expires} minutes.</p>"
        ),
    )

    return verification, raw_token


async def verify_magic_link(
    db: AsyncSession,
    token: str,
) -> Verification:
    token_hash = _hash_token(token)

    result = await db.execute(
        select(Verification).where(
            Verification.token_hash == token_hash,
            Verification.strategy == "email_link",
            Verification.consumed_at.is_(None),
        )
    )
    verification = result.scalar_one_or_none()
    if verification is None:
        raise ValidationError(message="Invalid or expired magic link.")

    if verification.expires_at and now() > verification.expires_at:
        raise ValidationError(message="Magic link has expired.")

    verification.consumed_at = now()
    await db.commit()
    await db.refresh(verification)
    return verification
