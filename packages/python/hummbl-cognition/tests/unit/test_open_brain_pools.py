"""Tests for the Open Brain pools that reach fleet memory outside the primary ledger.

Covers:
- Briefings resolved from the fleet governance checkout and from an override
- Closeout (secondary) ledgers: retrieval, since filter, malformed lines, dedup
- Handoff and AAR text pools, newest-first scanning
- validate_integrity reporting one break once instead of cascading
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from hummbl_cognition.ledger_writer import post_entry, validate_integrity
from hummbl_cognition.models import LedgerEntry, LedgerEntryType, LedgerScope
from hummbl_cognition.retriever import OpenBrainRetriever


@pytest.fixture
def retriever(tmp_path, monkeypatch):
    """A retriever whose home and state dirs are isolated under tmp_path."""
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: home))
    for var in (
        "HUMMBL_BRIEFINGS_DIRS",
        "HUMMBL_SECONDARY_LEDGERS",
        "HUMMBL_HANDOFF_DIRS",
        "HUMMBL_AAR_DIRS",
    ):
        monkeypatch.delenv(var, raising=False)
    state = tmp_path / "PROJECTS" / "_state"
    state.mkdir(parents=True)
    return OpenBrainRetriever(state_dir=state), home


def _write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


class TestBriefingsPool:
    def test_reads_fleet_briefings_by_default(self, retriever):
        r, home = retriever
        _write(home / ".agents" / "_state" / "briefings" / "b.md", "zebra migration sitrep")
        results = r.search("zebra migration", sources=["briefings"])
        assert [x.source for x in results] == ["briefings"]

    def test_env_override_replaces_defaults(self, retriever, monkeypatch, tmp_path):
        r, home = retriever
        _write(home / ".agents" / "_state" / "briefings" / "b.md", "zebra default")
        custom = tmp_path / "custom"
        _write(custom / "c.md", "zebra custom")
        monkeypatch.setenv("HUMMBL_BRIEFINGS_DIRS", str(custom))
        results = r.search("zebra", sources=["briefings"])
        assert [x.metadata["file"] for x in results] == ["c.md"]


class TestCloseoutsPool:
    def _ledger(self, home: Path, rows: list) -> Path:
        lines = [r if isinstance(r, str) else json.dumps(r) for r in rows]
        return _write(
            home / ".agents" / "state" / "cognition" / "ledger.jsonl",
            "\n".join(lines) + "\n",
        )

    def test_finds_closeout_entries(self, retriever):
        r, home = retriever
        self._ledger(home, [
            {"id": "clp-aaaaaaaaaaaa", "agent": "devin", "timestamp": "2026-10-29T15:56:06Z",
             "type": "discovery", "content": "SESSION CLOSE deploy-audit zone estate verified"},
        ])
        results = r.search("deploy-audit estate", sources=["closeouts"])
        assert len(results) == 1
        assert results[0].source == "closeouts"
        assert results[0].entry_id == "clp-aaaaaaaaaaaa"
        assert results[0].metadata["agent"] == "devin"

    def test_since_filter_and_malformed_lines(self, retriever):
        r, home = retriever
        self._ledger(home, [
            "not json",
            {"id": "clp-old000000000", "timestamp": "2026-09-01T00:00:00Z", "content": "quokka old"},
            {"id": "clp-new000000000", "timestamp": "2026-10-29T00:00:00Z", "content": "quokka new"},
        ])
        results = r.search("quokka", sources=["closeouts"], since="2026-10-01T00:00:00Z")
        assert [x.entry_id for x in results] == ["clp-new000000000"]

    def test_env_override_and_missing_file(self, retriever, monkeypatch, tmp_path):
        r, _ = retriever
        other = _write(tmp_path / "other.jsonl", json.dumps(
            {"id": "clp-bbbbbbbbbbbb", "timestamp": "2026-10-29T00:00:00Z", "content": "narwhal"}
        ) + "\n")
        monkeypatch.setenv(
            "HUMMBL_SECONDARY_LEDGERS", os.pathsep.join([str(tmp_path / "absent.jsonl"), str(other)])
        )
        results = r.search("narwhal", sources=["closeouts"])
        assert [x.entry_id for x in results] == ["clp-bbbbbbbbbbbb"]

    def test_duplicate_ids_returned_once(self, retriever):
        r, home = retriever
        row = {"id": "clp-cccccccccccc", "timestamp": "2026-10-29T00:00:00Z", "content": "ocelot"}
        self._ledger(home, [row, row])
        assert len(r.search("ocelot", sources=["closeouts"])) == 1


class TestHandoffAndAarPools:
    def test_handoffs_default_dirs(self, retriever):
        r, home = retriever
        _write(home / ".agents" / "state" / "handoffs" / "h.md", "axolotl handoff")
        _write(home / ".agents" / "_state" / "handoff" / "g.md", "axolotl legacy handoff")
        results = r.search("axolotl", sources=["handoffs"])
        assert sorted(x.metadata["file"] for x in results) == ["g.md", "h.md"]

    def test_aar_pool(self, retriever):
        r, home = retriever
        _write(home / ".agents" / "docs" / "aar" / "AAR-x.md", "capybara retrospective")
        results = r.search("capybara", sources=["aar"])
        assert [x.source for x in results] == ["aar"]

    def test_newest_by_mtime_scans_recent_files_first(self, retriever, tmp_path):
        r, _ = retriever
        pool = tmp_path / "pool"
        for i in range(3):
            f = _write(pool / f"{'zab'[i]}.md", "gecko")
            os.utime(f, (1_000 + i, 1_000 + i))
        # Name order would pick z.md; mtime order picks b.md (newest).
        results = r._search_text_pool(
            "gecko", pool_name="aar", search_dir=pool, glob_pattern="*.md",
            max_files=1, newest_by_mtime=True,
        )
        assert [x.metadata["file"] for x in results] == ["b.md"]


class TestValidateDoesNotCascade:
    def test_one_tampered_entry_does_not_poison_later_links(self, tmp_path):
        ledger = tmp_path / "ledger.jsonl"
        for i in range(4):
            post_entry(
                LedgerEntry.create(
                    agent="tester",
                    vendor="local",
                    model="test-model",
                    entry_type=LedgerEntryType.DISCOVERY,
                    scope=LedgerScope.PROJECT,
                    content=f"entry {i}",
                ),
                ledger_path=ledger,
            )
        lines = ledger.read_text(encoding="utf-8").splitlines()
        tampered = json.loads(lines[1])
        tampered["content"] = "entry 1, altered after hashing"
        lines[1] = json.dumps(tampered)
        ledger.write_text("\n".join(lines) + "\n", encoding="utf-8")

        valid, errors = validate_integrity(ledger_path=ledger)
        # Line 2 fails its content hash and line 3's link to it is genuinely
        # broken. Line 4 still links to line 3 and must not be reported.
        assert valid == 2
        assert len(errors) == 2
        assert errors[0].startswith("Line 2: content_hash mismatch")
        assert errors[1].startswith("Line 3: previous_hash chain mismatch")
