from __future__ import annotations

import hashlib
import secrets
from typing import Any

import pyotp
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from gates.core.clock import now
from gates.core.crypto import decrypt, encrypt
from gates.core.errors import NotFoundError, ValidationError
from gates.core.instance import get_instance_id
from gates.db.models.backup_code import BackupCode
from gates.db.models.mfa_factor import MfaFactor
from gates.db.models.user import User

BACKUP_CODE_COUNT = 10


async def enroll_totp(
    db: AsyncSession,
    user_id: str,
    friendly_name: str | None = None,
) -> dict[str, Any]:
    instance_id = await get_instance_id(db)
    user = await db.get(User, user_id)
    if user is None:
        raise NotFoundError(message="User not found.")

    existing = await db.execute(
        select(MfaFactor).where(
            MfaFactor.user_id == user_id,
            MfaFactor.type == "totp",
            MfaFactor.status == "verified",
        )
    )
    if existing.scalar_one_or_none():
        raise ValidationError(message="TOTP is already enabled for this user.")

    secret = pyotp.random_base32()
    secret_enc = encrypt(secret)

    factor = MfaFactor(
        user_id=user_id,
        instance_id=instance_id,
        type="totp",
        status="unverified",
        secret_enc=secret_enc,
        friendly_name=friendly_name or "Authenticator App",
    )
    db.add(factor)
    await db.flush()
    await db.refresh(factor)

    totp = pyotp.TOTP(secret)
    provisioning_uri = totp.provisioning_uri(
        name=user.email_addresses[0].email if user.email_addresses else user_id,
        issuer_name="Gates",
    )

    return {
        "factor_id": factor.id,
        "secret": secret,
        "provisioning_uri": provisioning_uri,
        "qr_code_data_url": "",
    }


async def verify_totp(
    db: AsyncSession,
    user_id: str,
    factor_id: str,
    code: str,
) -> MfaFactor:
    factor = await db.get(MfaFactor, factor_id)
    if factor is None or factor.user_id != user_id:
        raise NotFoundError(message="MFA factor not found.")

    if factor.type != "totp":
        raise ValidationError(message="Factor is not TOTP.")

    if not factor.secret_enc:
        raise ValidationError(message="MFA factor has no secret.")
    secret = decrypt(factor.secret_enc)
    totp = pyotp.TOTP(secret)

    if not totp.verify(code, valid_window=1):
        raise ValidationError(message="Invalid TOTP code.")

    factor.status = "verified"
    user = await db.get(User, user_id)
    if user:
        user.two_factor_enabled = True

    codes = []
    for _ in range(BACKUP_CODE_COUNT):
        raw = secrets.token_hex(4)
        hashed = hashlib.sha256(raw.encode()).hexdigest()
        bc = BackupCode(
            user_id=user_id,
            mfa_factor_id=factor.id,
            code_hash=hashed,
        )
        db.add(bc)
        codes.append(raw)

    await db.commit()
    await db.refresh(factor)

    factor._backup_codes = codes  # type: ignore[attr-defined]
    return factor


async def verify_totp_challenge(
    db: AsyncSession,
    user_id: str,
    code: str,
) -> bool:
    factors = await db.execute(
        select(MfaFactor).where(
            MfaFactor.user_id == user_id,
            MfaFactor.type == "totp",
            MfaFactor.status == "verified",
        )
    )
    for factor in factors.scalars().all():
        if not factor.secret_enc:
            continue
        secret = decrypt(factor.secret_enc)
        totp = pyotp.TOTP(secret)
        if totp.verify(code, valid_window=1):
            return True
    return False


async def verify_backup_code(
    db: AsyncSession,
    user_id: str,
    code: str,
) -> bool:
    code_hash = hashlib.sha256(code.encode()).hexdigest()
    result = await db.execute(
        select(BackupCode).where(
            BackupCode.user_id == user_id,
            BackupCode.code_hash == code_hash,
            BackupCode.used_at.is_(None),
        )
    )
    bc = result.scalar_one_or_none()
    if bc is None:
        return False
    bc.used_at = now()
    await db.commit()
    return True


async def disable_mfa(db: AsyncSession, user_id: str) -> None:
    factors = await db.execute(
        select(MfaFactor).where(MfaFactor.user_id == user_id)
    )
    for factor in factors.scalars().all():
        await db.delete(factor)

    codes = await db.execute(
        select(BackupCode).where(BackupCode.user_id == user_id)
    )
    for bc in codes.scalars().all():
        await db.delete(bc)

    user = await db.get(User, user_id)
    if user:
        user.two_factor_enabled = False

    await db.commit()


async def list_factors(db: AsyncSession, user_id: str) -> list[MfaFactor]:
    result = await db.execute(
        select(MfaFactor).where(MfaFactor.user_id == user_id)
    )
    return list(result.scalars().all())
