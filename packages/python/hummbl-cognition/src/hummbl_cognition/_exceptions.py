"""Shared exception types — single source of truth for cross-module exceptions."""

from __future__ import annotations


class ConcurrencyError(Exception):
    """Raised when optimistic concurrency check fails."""
