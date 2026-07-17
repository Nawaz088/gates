from __future__ import annotations

from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from gates.core.clock import now
from gates.core.errors import ConflictError, NotFoundError, ValidationError
from gates.core.instance import get_instance_id
from gates.core.security import random_numeric_code
from gates.core.sms import send_sms
from gates.db.models.phone_number import PhoneNumber
from gates.db.models.verification import Verification
from gates.domains.otp.service import _hash_code

OTP_TTL_MINUTES = 10


async def add_phone(
    db: AsyncSession,
    user_id: str,
    phone_number: str,
    verified: bool = False,
) -> PhoneNumber:
    instance_id = await get_instance_id(db)

    result = await db.execute(
        select(PhoneNumber).where(PhoneNumber.phone_number == phone_number)
    )
    if result.scalar_one_or_none():
        raise ConflictError(message="This phone number is already in use.")

    phone = PhoneNumber(
        user_id=user_id,
        instance_id=instance_id,
        phone_number=phone_number,
        verified_at=now() if verified else None,
    )
    db.add(phone)
    await db.flush()

    if not verified:
        code = random_numeric_code(6)
        verification = Verification(
            instance_id=instance_id,
            user_id=user_id,
            type="phone_verification",
            strategy="phone_code",
            target=phone_number,
            code_hash=_hash_code(code),
            expires_at=now() + timedelta(minutes=OTP_TTL_MINUTES),
        )
        db.add(verification)
        await db.flush()

        expires = OTP_TTL_MINUTES
        await send_sms(
            to=phone_number,
            body=f"Your verification code is: {code}\n\nThis code expires in {expires} minutes.",
        )
        phone._verification_id = verification.id  # type: ignore[attr-defined]

    await db.commit()
    await db.refresh(phone)
    return phone


async def verify_phone(db: AsyncSession, phone_id: str, code: str) -> PhoneNumber:
    phone = await db.get(PhoneNumber, phone_id)
    if phone is None:
        raise NotFoundError(message="Phone number not found.")

    ver_id = getattr(phone, "_verification_id", None)
    if ver_id is None:
        raise ValidationError(message="No pending verification for this phone number.")

    verification = await db.get(Verification, ver_id)
    if verification is None or verification.consumed_at is not None:
        raise ValidationError(message="Verification expired or already used.")

    if verification.code_hash != _hash_code(code):
        raise ValidationError(message="Invalid verification code.")

    verification.consumed_at = now()
    phone.verified_at = now()
    await db.commit()
    await db.refresh(phone)
    return phone


async def remove_phone(db: AsyncSession, phone_id: str) -> None:
    phone = await db.get(PhoneNumber, phone_id)
    if phone is None:
        raise NotFoundError(message="Phone number not found.")
    await db.delete(phone)
    await db.commit()


async def list_user_phones(db: AsyncSession, user_id: str) -> list[PhoneNumber]:
    result = await db.execute(
        select(PhoneNumber).where(PhoneNumber.user_id == user_id)
    )
    return list(result.scalars().all())


async def set_default_two_factor(
    db: AsyncSession,
    user_id: str,
    phone_id: str,
) -> PhoneNumber:
    phone = await db.get(PhoneNumber, phone_id)
    if phone is None:
        raise NotFoundError(message="Phone number not found.")
    if phone.user_id != user_id:
        raise ValidationError(message="Phone number does not belong to this user.")
    if phone.verified_at is None:
        raise ValidationError(message="Phone number must be verified.")

    others = await db.execute(
        select(PhoneNumber).where(
            PhoneNumber.user_id == user_id,
            PhoneNumber.default_two_factor == True,  # noqa: E712
        )
    )
    for other in others.scalars().all():
        other.default_two_factor = False

    phone.default_two_factor = True
    await db.commit()
    await db.refresh(phone)
    return phone
