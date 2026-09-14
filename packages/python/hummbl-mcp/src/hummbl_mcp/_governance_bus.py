"""Governance bus stub — provides minimal interface for MCP modules."""
from __future__ import annotations
from typing import Any
import hashlib
import json


class GovernanceBus:
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self._entries: list[dict] = []

    def post(self, *args: Any, **kwargs: Any) -> None:
        pass

    def query(self, *args: Any, **kwargs: Any) -> list:
        return []


def _compute_entry_signature(entry: dict) -> str:
    payload = json.dumps(entry, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode()).hexdigest()


def get_governance_bus(*args: Any, **kwargs: Any) -> GovernanceBus:
    return GovernanceBus()


def _is_idp_enabled() -> bool:
    import os
    return os.environ.get("ENABLE_IDP", "").lower() in ("1", "true", "yes")
