from __future__ import annotations

from datetime import timedelta
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from gates.core.clock import now
from gates.core.errors import (
    ForbiddenError,
    FormIdentifierExistsError,
    FormPasswordIncorrectError,
    NotFoundError,
    ValidationError,
)
from gates.core.instance import ensure_default_instance, get_instance_id
from gates.core.security import hash_password, random_token_str, verify_password
from gates.db.models.email_address import EmailAddress
from gates.db.models.user import User


async def create_user(
    db: AsyncSession,
    email: str | None = None,
    password: str | None = None,
    username: str | None = None,
    first_name: str | None = None,
    last_name: str | None = None,
    public_metadata: dict[str, Any] | None = None,
    private_metadata: dict[str, Any] | None = None,
    unsafe_metadata: dict[str, Any] | None = None,
    external_id: str | None = None,
) -> User:
    instance_id = await ensure_default_instance(db)

    if email:
        existing = await db.execute(
            select(EmailAddress).where(EmailAddress.email == email)
        )
        if existing.scalar_one_or_none():
            raise FormIdentifierExistsError()

    if username:
        existing = await db.execute(
            select(User).where(User.username == username, User.instance_id == instance_id)
        )
        if existing.scalar_one_or_none():
            raise FormIdentifierExistsError(details={"field": "username"})

    if password and len(password) < 8:
        raise ValidationError(message="Password must be at least 8 characters.")

    if password and len(password) > 128:
        raise ValidationError(message="Password must be at most 128 characters.")

    password_hash_value = hash_password(password) if password else None

    user = User(
        instance_id=instance_id,
        external_id=external_id,
        username=username,
        first_name=first_name,
        last_name=last_name,
        password_hash=password_hash_value,
        public_metadata=public_metadata or {},
        private_metadata=private_metadata or {},
        unsafe_metadata=unsafe_metadata or {},
    )
    db.add(user)
    await db.flush()

    if email:
        email_addr = EmailAddress(
            user_id=user.id,
            instance_id=instance_id,
            email=email.strip().lower(),
            verified_at=None,
        )
        db.add(email_addr)
        await db.flush()
        user.primary_email_id = email_addr.id

    await db.commit()
    await db.refresh(user)
    return user


async def authenticate_user(
    db: AsyncSession,
    identifier: str,
    password: str,
) -> User:
    instance_id = await get_instance_id(db)

    if "@" in identifier:
        email_result = await db.execute(
            select(EmailAddress).where(EmailAddress.email == identifier)
        )
        email_row = email_result.scalar_one_or_none()
        if email_row is None:
            raise FormPasswordIncorrectError()
        user = await db.get(User, email_row.user_id)
    else:
        user_result = await db.execute(
            select(User).where(User.username == identifier, User.instance_id == instance_id)
        )
        user = user_result.scalar_one_or_none()

    if user is None:
        raise FormPasswordIncorrectError()

    if user.banned:
        raise ForbiddenError(code="user_banned", message="This user has been banned.")

    if user.locked_until and now() < user.locked_until:
        raise ForbiddenError(
            code="user_locked",
            message="Account is temporarily locked due to too many failed attempts.",
        )

    if not verify_password(password, user.password_hash):
        user.failed_attempts = (user.failed_attempts or 0) + 1
        if user.failed_attempts >= 5:
            user.locked_until = now() + timedelta(minutes=30)
        await db.commit()
        raise FormPasswordIncorrectError()

    user.failed_attempts = 0
    user.locked_until = None
    user.last_sign_in_at = now()
    await db.commit()
    await db.refresh(user)
    return user


async def get_user(db: AsyncSession, user_id: str) -> User:
    user = await db.get(User, user_id)
    if user is None:
        raise NotFoundError(message=f"User {user_id} not found.")
    return user


async def list_users(
    db: AsyncSession,
    offset: int = 0,
    limit: int = 100,
) -> tuple[list[User], int]:
    instance_id = await get_instance_id(db)
    count_q = select(func.count(User.id)).where(User.instance_id == instance_id)
    total = await db.scalar(count_q) or 0

    query = (
        select(User)
        .where(User.instance_id == instance_id)
        .offset(offset)
        .limit(limit)
        .order_by(User.created_at.desc())
    )
    result = await db.execute(query)
    users = list(result.scalars().all())
    return users, total


async def update_user(
    db: AsyncSession,
    user_id: str,
    **kwargs: Any,
) -> User:
    user = await get_user(db, user_id)

    allowed = {
        "external_id", "username", "first_name", "last_name",
        "primary_email_id", "primary_phone_id",
        "public_metadata", "private_metadata", "unsafe_metadata",
    }
    for key, value in kwargs.items():
        if key in allowed and value is not None:
            setattr(user, key, value)

    await db.commit()
    await db.refresh(user)
    return user


async def delete_user(db: AsyncSession, user_id: str) -> None:
    user = await get_user(db, user_id)
    await db.delete(user)
    await db.commit()


async def ban_user(db: AsyncSession, user_id: str, reason: str | None = None) -> User:
    user = await get_user(db, user_id)
    user.banned = True
    user.ban_reason = reason
    await db.commit()
    await db.refresh(user)
    return user


async def unban_user(db: AsyncSession, user_id: str) -> User:
    user = await get_user(db, user_id)
    user.banned = False
    user.ban_reason = None
    await db.commit()
    await db.refresh(user)
    return user


async def lock_user(db: AsyncSession, user_id: str, duration_minutes: int = 30) -> User:
    user = await get_user(db, user_id)
    user.locked_until = now() + timedelta(minutes=duration_minutes)
    await db.commit()
    await db.refresh(user)
    return user


async def unlock_user(db: AsyncSession, user_id: str) -> User:
    user = await get_user(db, user_id)
    user.locked_until = None
    user.failed_attempts = 0
    await db.commit()
    await db.refresh(user)
    return user


async def change_password(
    db: AsyncSession,
    user_id: str,
    current_password: str,
    new_password: str,
) -> User:
    user = await get_user(db, user_id)

    if not verify_password(current_password, user.password_hash):
        raise FormPasswordIncorrectError()

    if len(new_password) < 8:
        raise ValidationError(message="New password must be at least 8 characters.")

    if len(new_password) > 128:
        raise ValidationError(message="New password must be at most 128 characters.")

    user.password_hash = hash_password(new_password)
    await db.commit()
    await db.refresh(user)
    return user


async def request_password_reset(db: AsyncSession, email: str) -> dict[str, str]:
    token = random_token_str(32)
    result = await db.execute(
        select(EmailAddress).where(EmailAddress.email == email)
    )
    email_row = result.scalar_one_or_none()
    if email_row:
        email_row.verification_token = token
        email_row.verification_token_expires_at = now() + timedelta(minutes=10)
        await db.commit()

    return {"token": token}


async def reset_password(
    db: AsyncSession,
    email: str,
    token: str,
    new_password: str,
) -> User:
    if len(new_password) < 8:
        raise ValidationError(message="Password must be at least 8 characters.")

    result = await db.execute(
        select(EmailAddress).where(
            EmailAddress.email == email,
            EmailAddress.verification_token == token,
        )
    )
    email_row = result.scalar_one_or_none()
    if email_row is None:
        raise ValidationError(message="Invalid or expired token.")

    if email_row.verification_token_expires_at and now() > email_row.verification_token_expires_at:
        raise ValidationError(message="Token has expired.")

    user = await db.get(User, email_row.user_id)
    if user is None:
        raise NotFoundError(message="User not found.")

    user.password_hash = hash_password(new_password)
    email_row.verification_token = None
    email_row.verification_token_expires_at = None
    await db.commit()
    await db.refresh(user)
    return user
