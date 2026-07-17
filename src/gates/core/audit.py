from __future__ import annotations

from typing import Any

# Audit logging — stub for phase 1.
# Full implementation in §11.8.


async def write_audit_log(
    _instance_id: str = "",
    _actor_type: str = "",
    _actor_id: str = "",
    _event: str = "",
    _ip_address: str | None = None,
    _user_agent: str | None = None,
    _metadata: dict[str, Any] | None = None,
) -> None:
    pass
