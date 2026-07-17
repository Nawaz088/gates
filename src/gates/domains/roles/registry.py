from __future__ import annotations

SYSTEM_PERMISSIONS: list[str] = [
    "org:read",
    "org:manage",
    "org:delete",
    "org:create",
    "org:member:read",
    "org:member:manage",
    "org:invitation:read",
    "org:invitation:create",
    "org:invitation:revoke",
    "org:domain:read",
    "org:domain:manage",
    "org:role:read",
    "org:role:manage",
    "user:read",
    "user:create",
    "user:update",
    "user:delete",
    "user:ban",
    "user:impersonate",
    "session:read",
    "session:revoke",
    "webhook:read",
    "webhook:manage",
    "api_key:read",
    "api_key:manage",
    "billing:read",
    "billing:manage",
]

SYSTEM_PERMISSION_SET = frozenset(SYSTEM_PERMISSIONS)

SYSTEM_ROLES: dict[str, list[str]] = {
    "org:admin": list(SYSTEM_PERMISSIONS),
    "org:member": ["org:read", "org:member:read"],
    "basic_member": ["org:read", "org:member:read"],
}
