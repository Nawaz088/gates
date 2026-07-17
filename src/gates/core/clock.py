from __future__ import annotations

from datetime import UTC, datetime


def now() -> datetime:
    """Injectable current time — swap in tests via time_machine."""
    return datetime.now(UTC)
