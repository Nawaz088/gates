from __future__ import annotations

# Rate limiting — Redis token bucket.
# Stub for phase 1. Full implementation in §11.5.


async def check_rate_limit(
    _key: str = "",
    _max_requests: int = 30,
    _window_seconds: int = 60,
) -> bool:
    return True
