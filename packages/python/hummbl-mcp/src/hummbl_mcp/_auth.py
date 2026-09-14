"""Auth stub — provides token verification."""
from __future__ import annotations
from typing import Any


def verify_token(token: str, *args: Any, **kwargs: Any) -> bool:
    """Stub token verification — always returns False in standalone mode."""
    return False


def get_auth_token(*args: Any, **kwargs: Any) -> str | None:
    return None
