"""Tests for hummbl_cognition.query — ledger search, supersedes resolution."""

from __future__ import annotations

from pathlib import Path

import pytest

from hummbl_cognition.ledger_writer import post_entry, read_entries
from hummbl_cognition.models import LedgerEntry, LedgerEntryType, LedgerScope
from hummbl_cognition.query import (
    active_entries,
    latest_by_scope,
    query_entries,
)


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


@pytest.fixture
def populated_ledger(tmp_ledger_path: Path) -> Path:
    """Create a ledger with a few entries for query tests."""
    post_entry(
        _make_entry(
            content="First lesson about Python testing",
            scope=LedgerScope.PROJECT,
            tags=("python", "testing"),
        ),
        ledger_path=tmp_ledger_path,
    )
    post_entry(
        _make_entry(
            content="Second lesson about Rust safety",
            scope=LedgerScope.MODULE,
            entry_type=LedgerEntryType.DECISION,
            tags=("rust",),
        ),
        ledger_path=tmp_ledger_path,
    )
    post_entry(
        _make_entry(
            content="Third lesson about Python async",
            scope=LedgerScope.PROJECT,
            tags=("python", "async"),
        ),
        ledger_path=tmp_ledger_path,
    )
    return tmp_ledger_path


class TestQueryEntries:
    def test_query_all(self, populated_ledger: Path) -> None:
        results = query_entries(ledger_path=populated_ledger, limit=100)
        assert len(results) == 3

    def test_query_by_type(self, populated_ledger: Path) -> None:
        results = query_entries(
            ledger_path=populated_ledger, entry_type="decision"
        )
        assert len(results) == 1
        assert results[0].type == "decision"

    def test_query_by_scope(self, populated_ledger: Path) -> None:
        results = query_entries(
            ledger_path=populated_ledger, scope="module"
        )
        assert len(results) == 1
        assert results[0].scope == "module"

    def test_query_by_agent(self, populated_ledger: Path) -> None:
        results = query_entries(
            ledger_path=populated_ledger, agent="test-agent"
        )
        assert len(results) == 3

    def test_query_by_tags(self, populated_ledger: Path) -> None:
        results = query_entries(
            ledger_path=populated_ledger, tags=["python"]
        )
        assert len(results) == 2

    def test_query_limit(self, populated_ledger: Path) -> None:
        results = query_entries(ledger_path=populated_ledger, limit=1)
        assert len(results) == 1

    def test_query_empty_ledger(self, tmp_ledger_path: Path) -> None:
        results = query_entries(ledger_path=tmp_ledger_path)
        assert results == []


class TestActiveEntries:
    def test_active_without_supersedes(self, populated_ledger: Path) -> None:
        entries = active_entries(ledger_path=populated_ledger)
        assert len(entries) == 3

    def test_active_filters_superseded(self, tmp_ledger_path: Path) -> None:
        e1 = _make_entry(content="Original lesson")
        r1 = post_entry(e1, ledger_path=tmp_ledger_path)
        e2 = _make_entry(content="Corrected lesson", supersedes=r1.id)
        post_entry(e2, ledger_path=tmp_ledger_path)

        entries = active_entries(ledger_path=tmp_ledger_path)
        # The original should be filtered out, only the correction remains
        ids = {e.id for e in entries}
        assert r1.id not in ids
        assert len(entries) == 1


class TestLatestByScope:
    def test_latest_per_scope(self, populated_ledger: Path) -> None:
        result = latest_by_scope(ledger_path=populated_ledger)
        # Two scopes: project and module
        assert "project" in result
        assert "module" in result
        assert result["project"].scope == "project"
        assert result["module"].scope == "module"

    def test_latest_empty_ledger(self, tmp_ledger_path: Path) -> None:
        result = latest_by_scope(ledger_path=tmp_ledger_path)
        assert result == {}
