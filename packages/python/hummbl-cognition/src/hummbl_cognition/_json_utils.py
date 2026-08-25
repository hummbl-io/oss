"""Shared JSON utility — single source of truth for canonical JSON serialization."""

from __future__ import annotations

import json
from typing import Any


def canonical_json(obj: dict[str, Any]) -> str:
    """Serialize dict to canonical JSON (sorted keys, compact separators).

    Produces a deterministic byte sequence suitable for hashing.
    Uses ``ensure_ascii=True`` (the json.dumps default).
    """
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))


def canonical_json_ascii_safe(obj: dict[str, Any]) -> str:
    """Serialize dict to canonical JSON with ``ensure_ascii=False``.

    Identical to :func:`canonical_json` but preserves Unicode characters
    instead of escaping them.  Used by modules whose receipts may contain
    non-ASCII content that must hash consistently.
    """
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
