#!/usr/bin/env python3
"""Tests for trace diffing CLI (issue #35)."""

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from trace_diff import _field_diff, _tuple_fingerprint, _tuple_key, diff_traces, format_summary


def test_tuple_key():
    """_tuple_key should produce stable keys."""
    t = {"tuple_type": "CONTRACT", "id": "abc123", "time": "2026-01-01"}
    assert _tuple_key(t) == "CONTRACT:abc123"


def test_tuple_key_no_id():
    """_tuple_key should fall back to time when id is missing."""
    t = {"tuple_type": "EVIDENCE", "time": "2026-01-01"}
    assert _tuple_key(t) == "EVIDENCE:2026-01-01"


def test_fingerprint_excludes_id_time():
    """_tuple_fingerprint should exclude id and time."""
    t1 = {"tuple_type": "CONTRACT", "id": "a", "time": "t1", "state": "ok"}
    t2 = {"tuple_type": "CONTRACT", "id": "b", "time": "t2", "state": "ok"}
    assert _tuple_fingerprint(t1) == _tuple_fingerprint(t2)


def test_diff_identical_traces():
    """Identical traces should have magnitude 0."""
    trace = [{"tuple_type": "CONTRACT", "id": "1", "tuple_data": {}}]
    diff = diff_traces(trace, trace)
    assert diff["summary"]["magnitude"] == 0.0
    assert diff["summary"]["matched_count"] == 1
    assert diff["summary"]["modified_count"] == 0


def test_diff_extra_in_b():
    """Trace B with extra tuples should show only_in_b."""
    a = [{"tuple_type": "CONTRACT", "id": "1", "tuple_data": {}}]
    b = [
        {"tuple_type": "CONTRACT", "id": "1", "tuple_data": {}},
        {"tuple_type": "EVIDENCE", "id": "2", "tuple_data": {}},
    ]
    diff = diff_traces(a, b)
    assert diff["summary"]["only_in_b_count"] == 1
    assert diff["summary"]["only_in_a_count"] == 0


def test_diff_modified_tuple():
    """Tuples with same key but different content should show as modified."""
    a = [{"tuple_type": "CONTRACT", "id": "1", "state": "ok", "tuple_data": {}}]
    b = [{"tuple_type": "CONTRACT", "id": "1", "state": "blocked", "tuple_data": {}}]
    diff = diff_traces(a, b)
    assert diff["summary"]["modified_count"] == 1
    assert len(diff["modified"]) == 1
    assert diff["modified"][0]["diff_fields"][0]["field"] == "state"


def test_diff_fixture_traces():
    """Diff should work on fixture trace files."""
    trace_a_path = REPO_ROOT / "tests" / "fixtures" / "traces" / "trace_a.json"
    trace_b_path = REPO_ROOT / "tests" / "fixtures" / "traces" / "trace_b.json"
    with trace_a_path.open("r", encoding="utf-8") as f:
        trace_a = json.load(f)
    with trace_b_path.open("r", encoding="utf-8") as f:
        trace_b = json.load(f)

    diff = diff_traces(trace_a, trace_b)
    # trace_a has 2 tuples, trace_b has 3 (1 matched, 1 modified, 1 only in B)
    assert diff["summary"]["trace_a_length"] == 2
    assert diff["summary"]["trace_b_length"] == 3
    assert diff["summary"]["only_in_b_count"] == 1
    assert diff["summary"]["modified_count"] == 1
    assert diff["summary"]["magnitude"] > 0


def test_format_summary():
    """format_summary should produce human-readable output."""
    trace = [{"tuple_type": "CONTRACT", "id": "1", "tuple_data": {}}]
    diff = diff_traces(trace, trace)
    summary = format_summary(diff)
    assert "Trace Diff Summary" in summary
    assert "0.0 (0.0=identical" in summary


def test_field_diff():
    """_field_diff should find changed fields."""
    a = {"state": "ok", "drift": 0.0}
    b = {"state": "blocked", "drift": 0.0}
    diffs = _field_diff(a, b)
    assert len(diffs) == 1
    assert diffs[0]["field"] == "state"
    assert diffs[0]["value_a"] == "ok"
    assert diffs[0]["value_b"] == "blocked"


def test_empty_traces():
    """Empty traces should produce a valid diff."""
    diff = diff_traces([], [])
    assert diff["summary"]["magnitude"] == 0.0
    assert diff["summary"]["trace_a_length"] == 0


if __name__ == "__main__":
    test_tuple_key()
    test_tuple_key_no_id()
    test_fingerprint_excludes_id_time()
    test_diff_identical_traces()
    test_diff_extra_in_b()
    test_diff_modified_tuple()
    test_diff_fixture_traces()
    test_format_summary()
    test_field_diff()
    test_empty_traces()
    print("All trace diffing tests passed")
