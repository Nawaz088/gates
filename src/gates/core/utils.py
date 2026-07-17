from __future__ import annotations

import secrets
import string

_alphabet = string.ascii_lowercase + string.digits


def generate_cuid2(length: int = 24) -> str:
    """Generate a 24-character cuid2-like identifier."""
    return "g" + "".join(secrets.choice(_alphabet) for _ in range(length - 1))
