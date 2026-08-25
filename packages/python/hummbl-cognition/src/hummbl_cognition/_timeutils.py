"""Shared time utility — single source of truth for UTC timestamp formatting."""

from __future__ import annotations

from datetime import datetime, timezone


def utc_now() -> str:
    """Return current UTC timestamp in ISO 8601 Z format (second precision).

    Format: ``YYYY-MM-DDTHH:MM:SSZ``
    """
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def utc_now_micros() -> str:
    """Return current UTC timestamp in ISO 8601 Z format (microsecond precision).

    Format: ``YYYY-MM-DDTHH:MM:SS.ffffffZ``
    """
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
