from __future__ import annotations

import secrets
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt as pyjwt
from argon2 import PasswordHasher
from argon2.exceptions import VerificationError, VerifyMismatchError

from gates.config import settings

_argon2_hasher = PasswordHasher(
    time_cost=3,
    memory_cost=65536,  # 64 MiB
    parallelism=4,
    hash_len=32,
    salt_len=16,
)


def hash_password(password: str) -> str:
    return _argon2_hasher.hash(password)


def verify_password(password: str, password_hash: str | None) -> bool:
    if password_hash is None:
        return False
    try:
        return _argon2_hasher.verify(password_hash, password)
    except (VerifyMismatchError, VerificationError):
        return False


def random_token_bytes(n: int = 32) -> bytes:
    return secrets.token_bytes(n)


def random_token_str(n: int = 32) -> str:
    return secrets.token_urlsafe(n)


def random_numeric_code(length: int = 6) -> str:
    """Generate a numeric OTP code (no leading zero)."""
    low = 10 ** (length - 1)
    high = 10**length - 1
    return str(secrets.randbelow(high - low + 1) + low)


def create_jwt(
    claims: dict[str, Any],
    key: str | None = None,
    algorithm: str | None = None,
    expire_minutes: int | None = None,
) -> str:
    key = key or settings.jwt_signing_key
    algorithm = algorithm or settings.jwt_algorithm
    expire_minutes = expire_minutes or settings.jwt_expire_minutes

    now = datetime.now(UTC)
    payload = {
        **claims,
        "iat": now,
        "exp": now + timedelta(minutes=expire_minutes),
    }
    return pyjwt.encode(payload, key, algorithm=algorithm)


def decode_jwt(
    token: str,
    key: str | None = None,
    algorithms: list[str] | None = None,
) -> dict[str, Any]:
    key = key or settings.jwt_signing_key
    algorithms = algorithms or [settings.jwt_algorithm]
    return pyjwt.decode(token, key, algorithms=algorithms)
