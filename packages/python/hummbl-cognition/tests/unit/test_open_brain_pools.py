"""Tests for the Open Brain pools that reach fleet memory outside the primary ledger.

Covers:
- Briefings resolved from the fleet governance checkout and from an override
- Closeout (secondary) ledgers: retrieval, since/scope/type filters, exclude_ids,
  tail-boundary handling, malformed lines, dedup
- Handoff and AAR text pools, newest-first scanning, since by file-name date or mtime, trimmed overrides
- validate_integrity reporting one break once instead of cascading
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from hummbl_cognition.ledger_writer import post_entry, validate_integrity
from hummbl_cognition.models import LedgerEntry, LedgerEntryType, LedgerScope
from hummbl_cognition import retriever as retriever_module
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

    def test_since_compares_instants_across_offsets(self, retriever):
        r, home = retriever
        self._ledger(home, [
            # 2026-10-29T03:00Z, earlier than the bound despite sorting later as text.
            {"id": "clp-early0000000", "timestamp": "2026-10-29T05:00:00+02:00", "content": "tapir"},
            # 2026-10-29T05:00Z, later than the bound.
            {"id": "clp-late00000000", "timestamp": "2026-10-29T01:00:00-04:00", "content": "tapir"},
        ])
        results = r.search("tapir", sources=["closeouts"], since="2026-10-29T04:00:00Z")
        assert [x.entry_id for x in results] == ["clp-late00000000"]

    def test_small_limit_still_returns_a_closeout(self, retriever):
        r, home = retriever
        self._ledger(home, [
            {"id": "clp-dddddddddddd", "timestamp": "2026-10-29T00:00:00Z", "content": "okapi"},
        ])
        assert len(r.search("okapi", sources=["closeouts"], limit=1)) == 1
    def test_scope_and_entry_type_filters_apply(self, retriever):
        r, home = retriever
        self._ledger(home, [
            {"id": "clp-project00000", "timestamp": "2026-10-29T00:00:00Z",
             "scope": "project", "type": "discovery", "content": "kudu"},
            {"id": "clp-file00000000", "timestamp": "2026-10-29T00:00:00Z",
             "scope": "file", "type": "lesson", "content": "kudu"},
        ])
        by_scope = r.search("kudu", sources=["closeouts"], scope="project")
        by_type = r.search("kudu", sources=["closeouts"], entry_type="lesson")
        assert [x.entry_id for x in by_scope] == ["clp-project00000"]
        assert [x.entry_id for x in by_type] == ["clp-file00000000"]

    def test_caller_exclude_ids_mask_closeouts(self, retriever):
        r, home = retriever
        self._ledger(home, [
            {"id": "clp-masked000000", "timestamp": "2026-10-29T00:00:00Z", "content": "dingo"},
        ])
        assert r.search("dingo", sources=["closeouts"], exclude_ids={"clp-masked000000"}) == []

    def test_record_starting_on_tail_boundary_is_kept(self, retriever, monkeypatch):
        r, home = retriever
        filler = json.dumps({"id": "clp-filler000000", "timestamp": "2026-10-29T00:00:00Z",
                             "content": "x" * 40})
        needle = json.dumps({"id": "clp-needle000000", "timestamp": "2026-10-29T00:00:00Z",
                             "content": "serval"})
        raw = self._ledger(home, [filler, needle]).read_bytes()
        # Cap the read so it starts exactly at the first byte of the needle record
        # (measured from the file, since text mode may write CRLF line endings).
        cap = len(raw) - raw.index(needle.encode())
        monkeypatch.setattr(retriever_module, "_BUS_CACHE_MAX_BYTES", cap)
        assert [x.entry_id for x in r.search("serval", sources=["closeouts"])] == [
            "clp-needle000000"
        ]

    def test_partial_record_at_tail_boundary_is_dropped(self, retriever, monkeypatch):
        r, home = retriever
        first = json.dumps({"id": "clp-first0000000", "timestamp": "2026-10-29T00:00:00Z",
                            "content": "serval " + "y" * 40})
        last = json.dumps({"id": "clp-last00000000", "timestamp": "2026-10-29T00:00:00Z",
                           "content": "serval"})
        raw = self._ledger(home, [first, last]).read_bytes()
        # Start the read ten bytes inside the first record; only the last one is kept.
        cap = len(raw) - raw.index(last.encode()) + 10
        monkeypatch.setattr(retriever_module, "_BUS_CACHE_MAX_BYTES", cap)
        assert [x.entry_id for x in r.search("serval", sources=["closeouts"])] == [
            "clp-last00000000"
        ]

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

    def test_override_paths_are_trimmed(self, retriever, monkeypatch, tmp_path):
        r, _ = retriever
        first, second = tmp_path / "first", tmp_path / "second"
        _write(first / "a.md", "wombat one")
        _write(second / "b.md", "wombat two")
        monkeypatch.setenv("HUMMBL_HANDOFF_DIRS", f"{first}{os.pathsep} {second} ")
        results = r.search("wombat", sources=["handoffs"])
        assert sorted(x.metadata["file"] for x in results) == ["a.md", "b.md"]

    def test_since_skips_markdown_older_than_bound(self, retriever):
        r, home = retriever
        aar = home / ".agents" / "docs" / "aar"
        old = _write(aar / "old.md", "pangolin")
        new = _write(aar / "new.md", "pangolin")
        os.utime(old, (1_000_000_000, 1_000_000_000))  # 2001-09-09
        os.utime(new, (1_900_000_000, 1_900_000_000))  # 2030-03-17
        results = r.search("pangolin", sources=["aar"], since="2026-01-01T00:00:00Z")
        assert [x.metadata["file"] for x in results] == ["new.md"]
    def test_since_prefers_date_in_file_name_over_mtime(self, retriever):
        r, home = retriever
        aar = home / ".agents" / "docs" / "aar"
        stale = _write(aar / "AAR-20260105-stale.md", "civet")      # fresh mtime, old name
        recent = _write(aar / "2026-10-29_recent.md", "civet")      # old mtime, new name
        os.utime(recent, (1_000_000_000, 1_000_000_000))
        assert stale.stat().st_mtime > 1_700_000_000
        results = r.search("civet", sources=["aar"], since="2026-06-01T00:00:00Z")
        assert [x.metadata["file"] for x in results] == ["2026-10-29_recent.md"]

    def test_since_keeps_a_dated_file_for_its_whole_day(self, retriever):
        r, home = retriever
        _write(home / ".agents" / "_state" / "briefings" / "2026-10-29.md", "lynx")
        results = r.search("lynx", sources=["briefings"], since="2026-10-29T18:00:00Z")
        assert [x.metadata["file"] for x in results] == ["2026-10-29.md"]

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
