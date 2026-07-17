from __future__ import annotations

import pytest

from gates.core.auth import decode_jwt, issue_jwt


class TestSessionTokens:
    def test_issue_and_decode_jwt(self) -> None:
        jwt = issue_jwt(
            user_id="user_abc123",
            session_id="session_xyz789",
            email="test@example.com",
            username="testuser",
        )
        payload = decode_jwt(jwt)
        assert payload["sub"] == "user_abc123"
        assert payload["sid"] == "session_xyz789"
        assert payload["email"] == "test@example.com"
        assert payload["username"] == "testuser"

    def test_jwt_with_org_context(self) -> None:
        jwt = issue_jwt(
            user_id="user_abc",
            session_id="session_def",
            org_id="org_001",
            org_role="org:admin",
            org_permissions=["org:read", "org:write"],
        )
        payload = decode_jwt(jwt)
        assert payload["org_id"] == "org_001"
        assert payload["org_role"] == "org:admin"
        assert payload["org_permissions"] == ["org:read", "org:write"]

    def test_jwt_without_optional_fields(self) -> None:
        jwt = issue_jwt(user_id="user_abc", session_id="session_def")
        payload = decode_jwt(jwt)
        assert payload["sub"] == "user_abc"
        assert payload["sid"] == "session_def"
        assert "email" not in payload
        assert "org_id" not in payload

    def test_jwt_expires(self) -> None:
        from gates.core.security import create_jwt

        jwt = create_jwt({"sub": "test"}, expire_minutes=-1)
        import jwt as pyjwt

        try:
            decode_jwt(jwt)
            pytest.fail("Should have raised")
        except pyjwt.ExpiredSignatureError:
            pass
