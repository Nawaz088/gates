from __future__ import annotations

import jwt as pyjwt
import pytest

from gates.core.errors import (
    ConflictError,
    ForbiddenError,
    FormIdentifierExistsError,
    FormPasswordIncorrectError,
    GatesError,
    NotFoundError,
    RateLimitError,
    StepUpRequiredError,
    UnauthorizedError,
    ValidationError,
)
from gates.core.security import (
    create_jwt,
    decode_jwt,
    hash_password,
    random_numeric_code,
    random_token_str,
    verify_password,
)


class TestErrors:
    def test_gates_error_str(self) -> None:
        err = GatesError(code="test", http_status=400, message="testing")
        assert "[400] test: testing" in str(err)

    def test_not_found(self) -> None:
        err = NotFoundError()
        assert err.http_status == 404
        assert err.code == "not_found"

    def test_unauthorized(self) -> None:
        err = UnauthorizedError()
        assert err.http_status == 401

    def test_forbidden(self) -> None:
        err = ForbiddenError()
        assert err.http_status == 403

    def test_conflict(self) -> None:
        err = ConflictError()
        assert err.http_status == 409

    def test_validation(self) -> None:
        err = ValidationError()
        assert err.http_status == 422

    def test_rate_limit(self) -> None:
        err = RateLimitError()
        assert err.http_status == 429

    def test_step_up(self) -> None:
        err = StepUpRequiredError()
        assert err.code == "step_up_required"

    def test_form_password_incorrect(self) -> None:
        err = FormPasswordIncorrectError()
        assert err.code == "form_password_incorrect"

    def test_form_identifier_exists(self) -> None:
        err = FormIdentifierExistsError()
        assert err.code == "form_identifier_exists"


class TestPasswordHashing:
    def test_hash_and_verify(self) -> None:
        pw = "correct-horse-battery-staple"
        h = hash_password(pw)
        assert h != pw
        assert verify_password(pw, h) is True

    def test_wrong_password(self) -> None:
        h = hash_password("real-password")
        assert verify_password("wrong-password", h) is False

    def test_none_hash(self) -> None:
        assert verify_password("anything", None) is False

    def test_no_two_hashes_are_equal(self) -> None:
        pw = "test-password"
        hashes = {hash_password(pw) for _ in range(5)}
        assert len(hashes) == 5


class TestJWT:
    def test_create_and_decode(self) -> None:
        token = create_jwt({"sub": "user_abc123"}, key="test-secret-key", algorithm="HS256")
        decoded = decode_jwt(token, key="test-secret-key", algorithms=["HS256"])
        assert decoded["sub"] == "user_abc123"

    def test_expired_token_raises(self) -> None:
        token = create_jwt(
            {"sub": "user_abc123"},
            key="test-secret",
            expire_minutes=-1,
        )
        with pytest.raises(pyjwt.ExpiredSignatureError):
            decode_jwt(token, key="test-secret")


class TestRandomUtils:
    def test_random_token_str_length(self) -> None:
        token = random_token_str(32)
        assert len(token) > 32

    def test_random_numeric_code_length(self) -> None:
        code = random_numeric_code(6)
        assert len(code) == 6
        assert code.isdigit()

    def test_random_numeric_code_no_leading_zero(self) -> None:
        for _ in range(100):
            code = random_numeric_code(6)
            assert code[0] != "0"

    def test_random_numeric_code_varied_lengths(self) -> None:
        for length in [4, 6, 8]:
            code = random_numeric_code(length)
            assert len(code) == length
