from __future__ import annotations

import hashlib
from datetime import timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from gates.core.clock import now
from gates.core.email import send_email
from gates.core.errors import ValidationError
from gates.core.instance import get_instance_id
from gates.core.security import random_numeric_code
from gates.db.models.verification import Verification

OTP_LENGTH = 6
OTP_MAX_ATTEMPTS = 5
OTP_TTL_MINUTES = 10


def _hash_code(code: str) -> str:
    return hashlib.sha256(code.encode()).hexdigest()


async def send_otp(
    db: AsyncSession,
    target: str,
    user_id: str | None = None,
    strategy: str = "email_code",
) -> Verification:
    instance_id = await get_instance_id(db)
    code = random_numeric_code(OTP_LENGTH)
    code_hash = _hash_code(code)

    verification = Verification(
        instance_id=instance_id,
        user_id=user_id,
        type="email_verification" if "@" in target else "phone_verification",
        strategy=strategy,
        target=target,
        code_hash=code_hash,
        expires_at=now() + timedelta(minutes=OTP_TTL_MINUTES),
        extra_data={"attempts": 0},
    )
    db.add(verification)
    await db.commit()
    await db.refresh(verification)

    if "@" in target:
        expires = OTP_TTL_MINUTES
        await send_email(
            to=target,
            subject="Your verification code",
            text_body=(
                f"Your verification code is: {code}\n\n"
                f"This code expires in {expires} minutes."
            ),
            html_body=(
                f"<p>Your verification code is: <strong>{code}</strong></p>"
                f"<p>This code expires in {expires} minutes.</p>"
            ),
        )

    return verification


async def verify_otp(
    db: AsyncSession,
    verification_id: str,
    code: str,
) -> Verification:
    verification = await db.get(Verification, verification_id)
    if verification is None:
        raise ValidationError(message="Verification not found.")

    if verification.consumed_at is not None:
        raise ValidationError(message="Verification already consumed.")

    if verification.expires_at and now() > verification.expires_at:
        raise ValidationError(message="Verification code has expired.")

    if verification.attempts >= OTP_MAX_ATTEMPTS:
        raise ValidationError(message="Too many failed attempts.")

    verification.attempts += 1

    if not verification.code_hash:
        raise ValidationError(message="No code associated with this verification.")

    if verification.code_hash != _hash_code(code):
        await db.commit()
        remaining = OTP_MAX_ATTEMPTS - verification.attempts
        raise ValidationError(
            message=f"Incorrect code. {remaining} attempt(s) remaining."
        )

    verification.consumed_at = now()
    await db.commit()
    await db.refresh(verification)
    return verification
