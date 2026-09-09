"""Config stub — provides timeout constants."""
from __future__ import annotations
import os

SUBPROCESS_TIMEOUT_NORMAL: float = float(os.environ.get("SUBPROCESS_TIMEOUT_NORMAL", "30"))
SUBPROCESS_TIMEOUT_LONG: float = float(os.environ.get("SUBPROCESS_TIMEOUT_LONG", "120"))


def get_config(*args, **kwargs) -> dict:
    return {}
