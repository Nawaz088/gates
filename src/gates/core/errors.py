from __future__ import annotations

from typing import Any


class GatesError(Exception):
    """Base exception for all gates errors."""

    def __init__(
        self,
        *,
        code: str = "",
        http_status: int | None = None,
        message: str = "",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__()
        self.code = code or getattr(type(self), "code", "unknown")
        self.http_status = (
            http_status
            if http_status is not None
            else getattr(type(self), "http_status", 400)
        )
        self.message = message or getattr(type(self), "message", "")
        self.details = details if details is not None else {}

    def __str__(self) -> str:
        return f"[{self.http_status}] {self.code}: {self.message}"


class NotFoundError(GatesError):
    code = "not_found"
    http_status = 404
    message = "The requested resource was not found."


class ConflictError(GatesError):
    code = "conflict"
    http_status = 409
    message = "The resource already exists."


class UnauthorizedError(GatesError):
    code = "unauthorized"
    http_status = 401
    message = "Authentication is required."


class ForbiddenError(GatesError):
    code = "forbidden"
    http_status = 403
    message = "You do not have permission to perform this action."


class ValidationError(GatesError):
    code = "validation_error"
    http_status = 422
    message = "The request data is invalid."


class RateLimitError(GatesError):
    code = "rate_limit_exceeded"
    http_status = 429
    message = "Too many requests."


class StepUpRequiredError(GatesError):
    code = "step_up_required"
    http_status = 403
    message = "Re-authentication is required for this action."


class FormPasswordIncorrectError(GatesError):
    code = "form_password_incorrect"
    http_status = 422
    message = "The provided password is incorrect."


class FormIdentifierExistsError(GatesError):
    code = "form_identifier_exists"
    http_status = 422
    message = "An account with this identifier already exists."
