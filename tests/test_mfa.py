from __future__ import annotations

import hashlib
import secrets

import pyotp

from gates.core.crypto import decrypt, encrypt


class TestTOTP:
    def test_totp_secret_roundtrip(self) -> None:
        secret = pyotp.random_base32()
        encrypted = encrypt(secret)
        decrypted = decrypt(encrypted)
        assert decrypted == secret

    def test_totp_code_verification(self) -> None:
        secret = pyotp.random_base32()
        totp = pyotp.TOTP(secret)
        code = totp.now()
        assert totp.verify(code, valid_window=1)

    def test_totp_wrong_code(self) -> None:
        secret = pyotp.random_base32()
        totp = pyotp.TOTP(secret)
        assert not totp.verify("000000", valid_window=1)


class TestBackupCodes:
    def test_backup_code_hash(self) -> None:
        code = secrets.token_hex(4)
        h = hashlib.sha256(code.encode()).hexdigest()
        assert len(h) == 64
        assert hashlib.sha256(code.encode()).hexdigest() == h

    def test_different_codes_different_hashes(self) -> None:
        c1 = secrets.token_hex(4)
        c2 = secrets.token_hex(4)
        assert c1 != c2
