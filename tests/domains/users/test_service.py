from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from gates.core.errors import (
    ForbiddenError,
    FormPasswordIncorrectError,
    NotFoundError,
    ValidationError,
)


async def test_create_user(db_session: AsyncSession) -> None:
    from gates.domains.users.service import create_user

    user = await create_user(
        db_session,
        email="test@example.com",
        password="strong-password-123",
        first_name="Test",
        last_name="User",
    )
    assert user.id is not None
    assert user.first_name == "Test"
    assert user.last_name == "User"
    assert user.password_hash is not None
    assert user.password_hash != "strong-password-123"
    assert user.primary_email_id is not None


async def test_create_user_duplicate_email(db_session: AsyncSession) -> None:
    from gates.domains.users.service import create_user

    await create_user(db_session, email="dup@example.com", password="password123")
    with pytest.raises(FormPasswordIncorrectError):
        await create_user(db_session, email="dup@example.com", password="password456")


async def test_create_user_short_password(db_session: AsyncSession) -> None:
    from gates.domains.users.service import create_user

    with pytest.raises(ValidationError):
        await create_user(db_session, email="test@example.com", password="short")


async def test_authenticate_user(db_session: AsyncSession) -> None:
    from gates.domains.users.service import authenticate_user, create_user

    await create_user(
        db_session,
        email="auth@example.com",
        password="correct-password",
        first_name="Auth",
    )
    user = await authenticate_user(db_session, "auth@example.com", "correct-password")
    assert user.first_name == "Auth"
    assert user.last_sign_in_at is not None


async def test_authenticate_user_wrong_password(db_session: AsyncSession) -> None:
    from gates.domains.users.service import authenticate_user, create_user

    await create_user(db_session, email="wrongpw@example.com", password="real-password")
    with pytest.raises(FormPasswordIncorrectError):
        await authenticate_user(db_session, "wrongpw@example.com", "wrong-password")


async def test_authenticate_user_banned(db_session: AsyncSession) -> None:
    from gates.domains.users.service import authenticate_user, ban_user, create_user

    user = await create_user(
        db_session, email="banned@example.com", password="password123"
    )
    await ban_user(db_session, user.id)
    with pytest.raises(ForbiddenError):
        await authenticate_user(db_session, "banned@example.com", "password123")


async def test_get_user_not_found(db_session: AsyncSession) -> None:
    from gates.domains.users.service import get_user

    with pytest.raises(NotFoundError):
        await get_user(db_session, "nonexistent-id")


async def test_update_user(db_session: AsyncSession) -> None:
    from gates.domains.users.service import create_user, update_user

    user = await create_user(db_session, email="update@example.com", password="password123")
    updated = await update_user(db_session, user.id, first_name="Updated")
    assert updated.first_name == "Updated"


async def test_ban_unban_user(db_session: AsyncSession) -> None:
    from gates.domains.users.service import ban_user, create_user, unban_user

    user = await create_user(db_session, email="ban@example.com", password="password123")
    banned = await ban_user(db_session, user.id, reason="testing")
    assert banned.banned is True
    assert banned.ban_reason == "testing"
    unbanned = await unban_user(db_session, user.id)
    assert unbanned.banned is False


async def test_lock_unlock_user(db_session: AsyncSession) -> None:
    from gates.domains.users.service import create_user, lock_user, unlock_user

    user = await create_user(db_session, email="lock@example.com", password="password123")
    locked = await lock_user(db_session, user.id)
    assert locked.locked_until is not None
    unlocked = await unlock_user(db_session, user.id)
    assert unlocked.locked_until is None
    assert unlocked.failed_attempts == 0


async def test_change_password(db_session: AsyncSession) -> None:
    from gates.domains.users.service import authenticate_user, change_password, create_user

    user = await create_user(
        db_session, email="changepw@example.com", password="old-password"
    )
    await change_password(db_session, user.id, "old-password", "new-password-456")
    auth_user = await authenticate_user(db_session, "changepw@example.com", "new-password-456")
    assert auth_user.id == user.id


async def test_reset_password_flow(db_session: AsyncSession) -> None:
    from gates.domains.users.service import (
        authenticate_user,
        create_user,
        request_password_reset,
        reset_password,
    )

    await create_user(
        db_session, email="reset@example.com", password="original-password"
    )
    result = await request_password_reset(db_session, "reset@example.com")
    token = result["token"]
    await reset_password(db_session, "reset@example.com", token, "new-reset-password")
    user = await authenticate_user(db_session, "reset@example.com", "new-reset-password")
    assert user is not None


async def test_sign_up_router(client_with_db) -> None:
    resp = await client_with_db.post("/v1/sign_ups", json={
        "email_address": ["signup@example.com"],
        "password": "test-password-123",
        "firstName": "Signup",
        "lastName": "User",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "complete"
    assert data["user"]["firstName"] == "Signup"


async def test_sign_in_router(client_with_db) -> None:
    resp = await client_with_db.post("/v1/sign_ins", json={
        "identifier": "signin@example.com",
        "password": "test-password",
    })
    assert resp.status_code == 422
