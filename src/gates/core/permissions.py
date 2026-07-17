from __future__ import annotations

from typing import Any

from fastapi import Depends

from gates.core.auth import get_current_session
from gates.core.errors import ForbiddenError
from gates.domains.roles.registry import SYSTEM_PERMISSION_SET


def require_scopes(*required: str) -> Any:
    """Returns a FastAPI dependency that checks the caller has ALL the required scopes.

    Usage:
        @router.get("/users")
        async def list_users(
            _auth: dict[str, Any] = Depends(require_scopes("gates:users:read")),
        ):
            ...
    """
    for scope in required:
        if scope not in SYSTEM_PERMISSION_SET and not scope.startswith("gates:"):
            msg = f"Unknown scope: {scope}"
            raise ValueError(msg)

    class ScopeChecker:
        async def __call__(
            self,
            auth: dict[str, Any] = Depends(get_current_session),
        ) -> dict[str, Any]:
            user_scopes = set(auth.get("scopes", []))

            if "gates:*" in user_scopes:
                return auth

            for scope in required:
                if scope not in user_scopes:
                    raise ForbiddenError(
                        code="insufficient_permissions",
                        message=f"Missing required scope: {scope}",
                    )
            return auth

    return ScopeChecker()
