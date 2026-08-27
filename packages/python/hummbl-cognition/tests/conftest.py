"""Shared pytest fixtures for hummbl-cognition tests."""

from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture
def tmp_ledger_path(tmp_path: Path) -> Path:
    """Return a temporary ledger file path that does not yet exist."""
    return tmp_path / "ledger.jsonl"


@pytest.fixture
def tmp_state_path(tmp_path: Path) -> Path:
    """Return a temporary state.json file path that does not yet exist."""
    return tmp_path / "state.json"
