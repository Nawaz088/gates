from __future__ import annotations

from gates.webhooks.service import sign_payload, verify_signature


class TestWebhookSigning:
    def test_sign_and_verify(self) -> None:
        payload = b'{"event": "user.created", "id": "abc123"}'
        secret = "whsec_test_secret_key_32_bytes_long!!"

        header, _ = sign_payload(payload, secret)
        assert verify_signature(payload, header, secret) is True

    def test_verify_wrong_secret(self) -> None:
        payload = b'{"event": "user.created"}'
        secret = "correct-secret"
        wrong_secret = "wrong-secret"

        header, _ = sign_payload(payload, secret)
        assert verify_signature(payload, header, wrong_secret) is False

    def test_verify_tampered_payload(self) -> None:
        payload = b'{"event": "user.created"}'
        secret = "test-secret"

        header, _ = sign_payload(payload, secret)
        tampered = b'{"event": "user.deleted"}'
        assert verify_signature(tampered, header, secret) is False

    def test_verify_invalid_header(self) -> None:
        payload = b'{"event": "user.created"}'
        secret = "test-secret"

        assert verify_signature(payload, "", secret) is False
        assert verify_signature(payload, "invalid", secret) is False
        assert verify_signature(payload, "t=123,v1=abc", "wrong-secret") is False

    def test_signature_header_format(self) -> None:
        payload = b'{"test": true}'
        secret = "my-secret"

        header, sig = sign_payload(payload, secret)
        assert header.startswith("t=")
        assert ",v1=" in header
        assert header.endswith(sig)
