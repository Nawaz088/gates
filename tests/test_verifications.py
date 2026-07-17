from __future__ import annotations

import hashlib

from gates.domains.otp.service import _hash_code
from gates.domains.magic_links.service import _hash_token


class TestOTP:
    def test_code_hash_consistent(self) -> None:
        code = "123456"
        assert _hash_code(code) == hashlib.sha256(code.encode()).hexdigest()

    def test_code_hash_different(self) -> None:
        assert _hash_code("123456") != _hash_code("654321")


class TestMagicLinks:
    def test_token_hash_consistent(self) -> None:
        token = "abc123token"
        assert _hash_token(token) == hashlib.sha256(token.encode()).hexdigest()

    def test_token_hash_different(self) -> None:
        assert _hash_token("token-a") != _hash_token("token-b")
