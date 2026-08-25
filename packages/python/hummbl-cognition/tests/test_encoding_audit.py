"""Tests verifying encoding fixes from the audit pass.

These tests ensure that file I/O operations use explicit ``encoding="utf-8"``
so that the package works correctly on platforms where the default encoding
is not UTF-8 (e.g. Windows with cp1252).
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from hummbl_cognition.ledger_writer import post_entry, read_entries
from hummbl_cognition.models import LedgerEntry, LedgerEntryType, LedgerScope
from hummbl_cognition.state_manager import read_state, write_state
from hummbl_cognition.models import SharedState


def _make_entry(**overrides) -> LedgerEntry:
    defaults = dict(
        agent="test-agent",
        vendor="anthropic",
        model="claude-opus-4-6",
        entry_type=LedgerEntryType.LESSON,
        scope=LedgerScope.PROJECT,
        content="A valuable lesson learned",
    )
    defaults.update(overrides)
    return LedgerEntry.create(**defaults)


class TestUtf8LedgerRoundtrip:
    """Ledger files must be written and read as UTF-8 regardless of locale."""

    def test_unicode_content_roundtrip(self, tmp_ledger_path: Path) -> None:
        """Entries with non-ASCII content survive a write→read cycle."""
        unicode_content = "Learning: café résumé naïve — 日本語 emoji 🎉"
        entry = _make_entry(content=unicode_content)
        post_entry(entry, ledger_path=tmp_ledger_path)

        entries = read_entries(ledger_path=tmp_ledger_path, limit=10)
        assert len(entries) == 1
        assert entries[0].content == unicode_content

    def test_ledger_file_is_utf8_bytes(self, tmp_ledger_path: Path) -> None:
        """The raw file bytes should be valid UTF-8."""
        entry = _make_entry(content="Unicode: αβγδ → ✓")
        post_entry(entry, ledger_path=tmp_ledger_path)
        raw = tmp_ledger_path.read_bytes()
        # Should decode without error
        raw.decode("utf-8")


class TestUtf8StateRoundtrip:
    """State files must be written and read as UTF-8 regardless of locale."""

    def test_unicode_state_roundtrip(self, tmp_state_path: Path) -> None:
        state = SharedState(version=1, updated_by="café-agent")
        state.active_agents["café-agent"] = {"task": "résumé writing — 日本語"}
        write_state(state, state_path=tmp_state_path)

        restored = read_state(tmp_state_path)
        assert restored.updated_by == "café-agent"
        assert "café-agent" in restored.active_agents
        assert restored.active_agents["café-agent"]["task"] == "résumé writing — 日本語"

    def test_state_file_is_utf8_bytes(self, tmp_state_path: Path) -> None:
        state = SharedState(version=1, updated_by="αβγδ")
        write_state(state, state_path=tmp_state_path)
        raw = tmp_state_path.read_bytes()
        raw.decode("utf-8")
