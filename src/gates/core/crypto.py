from __future__ import annotations

from cryptography.fernet import Fernet as _Fernet

from gates.config import settings


def _get_fernet(key: str | None = None) -> _Fernet:
    raw = key or settings.field_encryption_key
    if not raw:
        msg = "GATES_FIELD_ENCRYPTION_KEY is not set"
        raise RuntimeError(msg)
    return _Fernet(raw.encode("utf-8") if isinstance(raw, str) else raw)


def encrypt(plaintext: str, key: str | None = None) -> str:
    f = _get_fernet(key)
    return f.encrypt(plaintext.encode("utf-8")).decode("utf-8")


def decrypt(ciphertext: str, key: str | None = None) -> str:
    f = _get_fernet(key)
    return f.decrypt(ciphertext.encode("utf-8")).decode("utf-8")
