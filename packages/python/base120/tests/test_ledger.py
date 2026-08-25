# Copyright 2024-2026 HUMMBL, LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# SPDX-License-Identifier: Apache-2.0

"""Tests for base120.ledger — VERUM-aligned append-only audit log."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from base120.ledger import Ledger
from base120.models import OperatorTuple

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_tuple(code: str = "P6", state: str = "rec", drift: float = 0.15) -> OperatorTuple:
    return OperatorTuple(
        id=code,
        time="2026-04-14T00:00:00Z",
        state=state,
        drift=drift,
    )


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------

class TestConstruction:
    def test_custom_path(self, tmp_path: Path):
        p = tmp_path / "test.jsonl"
        ledger = Ledger(p)
        assert ledger.path == p

    def test_default_path_is_home_base120(self):
        ledger = Ledger()
        assert ledger.path == Path.home() / ".base120" / "ledger.jsonl"

    def test_path_accepts_str(self, tmp_path: Path):
        p = tmp_path / "str.jsonl"
        ledger = Ledger(str(p))
        assert ledger.path == p


# ---------------------------------------------------------------------------
# append()
# ---------------------------------------------------------------------------

class TestAppend:
    def test_creates_file(self, tmp_path: Path):
        ledger = Ledger(tmp_path / "new.jsonl")
        assert not ledger.path.exists()
        ledger.append(_make_tuple())
        assert ledger.path.exists()

    def test_creates_parent_dirs(self, tmp_path: Path):
        ledger = Ledger(tmp_path / "deep" / "nested" / "log.jsonl")
        ledger.append(_make_tuple())
        assert ledger.path.exists()

    def test_writes_valid_json_line(self, tmp_path: Path):
        ledger = Ledger(tmp_path / "l.jsonl")
        t = _make_tuple("DE1", "root cause", 0.0)
        ledger.append(t)
        lines = ledger.path.read_text().splitlines()
        assert len(lines) == 1
        obj = json.loads(lines[0])
        assert obj["id"] == "DE1"
        assert obj["state"] == "root cause"
        assert obj["drift"] == 0.0

    def test_each_append_one_line(self, tmp_path: Path):
        ledger = Ledger(tmp_path / "l.jsonl")
        ledger.append(_make_tuple("P1", drift=0.1))
        ledger.append(_make_tuple("P2", drift=0.2))
        ledger.append(_make_tuple("P3", drift=0.3))
        lines = ledger.path.read_text().splitlines()
        assert len(lines) == 3

    def test_append_is_ordered(self, tmp_path: Path):
        ledger = Ledger(tmp_path / "l.jsonl")
        for i in range(1, 6):
            ledger.append(_make_tuple(f"P{i}", drift=i * 0.1))
        entries = ledger.project()
        codes = [e.id for e in entries]
        assert codes == ["P1", "P2", "P3", "P4", "P5"]

    def test_second_session_appends_not_overwrites(self, tmp_path: Path):
        p = tmp_path / "l.jsonl"
        Ledger(p).append(_make_tuple("P1"))
        Ledger(p).append(_make_tuple("P2"))
        assert len(Ledger(p).project()) == 2

    def test_all_four_fields_written(self, tmp_path: Path):
        ledger = Ledger(tmp_path / "l.jsonl")
        t = OperatorTuple(id="SY20", time="2026-04-14T12:00:00Z", state="synthesize", drift=0.05)
        ledger.append(t)
        obj = json.loads(ledger.path.read_text().strip())
        assert obj == {"id": "SY20", "time": "2026-04-14T12:00:00Z", "state": "synthesize", "drift": 0.05}


# ---------------------------------------------------------------------------
# project()
# ---------------------------------------------------------------------------

class TestProject:
    def test_empty_returns_empty(self, tmp_path: Path):
        ledger = Ledger(tmp_path / "empty.jsonl")
        assert ledger.project() == []

    def test_nonexistent_file_returns_empty(self, tmp_path: Path):
        ledger = Ledger(tmp_path / "missing.jsonl")
        assert ledger.project() == []

    def test_returns_operator_tuples(self, tmp_path: Path):
        ledger = Ledger(tmp_path / "l.jsonl")
        ledger.append(_make_tuple())
        entries = ledger.project()
        assert all(isinstance(e, OperatorTuple) for e in entries)

    def test_all_entries_no_limit(self, tmp_path: Path):
        ledger = Ledger(tmp_path / "l.jsonl")
        for i in range(5):
            ledger.append(_make_tuple(f"P{i+1}"))
        assert len(ledger.project()) == 5

    def test_project_n_returns_last_n(self, tmp_path: Path):
        ledger = Ledger(tmp_path / "l.jsonl")
        for i in range(5):
            ledger.append(_make_tuple(f"P{i+1}"))
        last2 = ledger.project(n=2)
        assert len(last2) == 2
        assert last2[0].id == "P4"
        assert last2[1].id == "P5"

    def test_project_n_larger_than_count_returns_all(self, tmp_path: Path):
        ledger = Ledger(tmp_path / "l.jsonl")
        ledger.append(_make_tuple("P1"))
        ledger.append(_make_tuple("P2"))
        assert len(ledger.project(n=100)) == 2

    def test_project_n_zero_returns_empty(self, tmp_path: Path):
        ledger = Ledger(tmp_path / "l.jsonl")
        ledger.append(_make_tuple())
        assert ledger.project(n=0) == []

    def test_project_negative_n_raises(self, tmp_path: Path):
        ledger = Ledger(tmp_path / "l.jsonl")
        ledger.append(_make_tuple())
        with pytest.raises(ValueError, match="non-negative"):
            ledger.project(n=-1)

    def test_corrupted_json_line_raises(self, tmp_path: Path):
        p = tmp_path / "l.jsonl"
        p.write_text('{"id": "P6", "time": "t", "state": "s", "drift": 0.1}\n{bad json}\n', encoding="utf-8")
        ledger = Ledger(p)
        with pytest.raises(ValueError, match="Corrupted ledger line 2"):
            ledger.project()

    def test_missing_fields_raises(self, tmp_path: Path):
        p = tmp_path / "l.jsonl"
        p.write_text('{"id": "P6", "time": "t"}\n', encoding="utf-8")
        ledger = Ledger(p)
        with pytest.raises(ValueError, match="missing fields"):
            ledger.project()

    def test_roundtrip_all_fields(self, tmp_path: Path):
        ledger = Ledger(tmp_path / "l.jsonl")
        t = OperatorTuple(id="IN10", time="2026-04-14T08:00:00Z", state="red team it", drift=0.3)
        ledger.append(t)
        recovered = ledger.project()[0]
        assert recovered == t


# ---------------------------------------------------------------------------
# cut()
# ---------------------------------------------------------------------------

class TestCut:
    def test_returns_entries_above_threshold(self, tmp_path: Path):
        ledger = Ledger(tmp_path / "l.jsonl")
        ledger.append(_make_tuple("P1", drift=0.1))
        ledger.append(_make_tuple("P2", drift=0.7))
        ledger.append(_make_tuple("P3", drift=0.3))
        high = ledger.cut(max_drift=0.5)
        assert len(high) == 1
        assert high[0].id == "P2"

    def test_boundary_is_exclusive(self, tmp_path: Path):
        ledger = Ledger(tmp_path / "l.jsonl")
        ledger.append(_make_tuple("P1", drift=0.5))
        # drift == max_drift is NOT included (strictly greater)
        assert ledger.cut(max_drift=0.5) == []

    def test_strictly_greater_is_included(self, tmp_path: Path):
        ledger = Ledger(tmp_path / "l.jsonl")
        ledger.append(_make_tuple("P1", drift=0.5001))
        assert len(ledger.cut(max_drift=0.5)) == 1

    def test_empty_ledger_returns_empty(self, tmp_path: Path):
        ledger = Ledger(tmp_path / "l.jsonl")
        assert ledger.cut(max_drift=0.5) == []

    def test_no_entries_above_returns_empty(self, tmp_path: Path):
        ledger = Ledger(tmp_path / "l.jsonl")
        ledger.append(_make_tuple(drift=0.1))
        ledger.append(_make_tuple(drift=0.2))
        assert ledger.cut(max_drift=0.9) == []

    def test_all_entries_above_returns_all(self, tmp_path: Path):
        ledger = Ledger(tmp_path / "l.jsonl")
        for i in range(3):
            ledger.append(_make_tuple(f"P{i+1}", drift=0.9))
        assert len(ledger.cut(max_drift=0.0)) == 3

    def test_preserves_order(self, tmp_path: Path):
        ledger = Ledger(tmp_path / "l.jsonl")
        ledger.append(_make_tuple("P1", drift=0.8))
        ledger.append(_make_tuple("P2", drift=0.2))
        ledger.append(_make_tuple("P3", drift=0.9))
        high = ledger.cut(max_drift=0.5)
        assert [e.id for e in high] == ["P1", "P3"]


# ---------------------------------------------------------------------------
# VERUM invariants (structural)
# ---------------------------------------------------------------------------

class TestVERUMInvariants:
    def test_no_delete_method(self):
        assert not hasattr(Ledger, "delete")

    def test_no_modify_method(self):
        assert not hasattr(Ledger, "modify")
        assert not hasattr(Ledger, "update")
        assert not hasattr(Ledger, "replace")

    def test_exactly_three_public_methods(self):
        """Minimal operators: append, project, cut — no more."""
        public = [
            m for m in dir(Ledger)
            if not m.startswith("_") and callable(getattr(Ledger, m)) and m != "path"
        ]
        assert set(public) == {"append", "project", "cut"}, f"Unexpected methods: {public}"
