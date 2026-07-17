from __future__ import annotations

import time
from typing import Any

"""Simple in-memory cache for refresh tokens.

Swappable with Redis later. Interface mirrors redis-py.
"""

_data: dict[str, Any] = {}
_ttl: dict[str, float] = {}


async def setex(key: str, seconds: int, value: str) -> None:
    _data[key] = value
    if seconds > 0:
        _ttl[key] = time.time() + seconds


async def get(key: str) -> str | None:
    if key in _ttl and time.time() > _ttl[key]:
        _data.pop(key, None)
        _ttl.pop(key, None)
        return None
    return _data.get(key)


async def delete(key: str) -> None:
    _data.pop(key, None)
    _ttl.pop(key, None)


async def exists(key: str) -> bool:
    val = await get(key)
    return val is not None
