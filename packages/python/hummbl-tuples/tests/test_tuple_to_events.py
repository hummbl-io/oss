#!/usr/bin/env python3
"""Tests for tuple-to-events converter (issue #38)."""

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from tuple_to_events import tuple_to_cloudevent, tuple_to_ndjson, convert_trace


def test_cloudevent_basic():
    """tuple_to_cloudevent should produce a valid CloudEvent 1.0 dict."""
    t = {
        "tuple_type": "CONTRACT",
        "id": "test-001",
        "time": "2026-07-01T00:00:00Z",
        "state": "ok",
        "agent": "test-agent",
        "tool": "test-tool",
        "intent_id": "intent-001",
        "tuple_data": {"contract_id": "test"},
    }
    event = tuple_to_cloudevent(t)
    assert event["specversion"] == "1.0"
    assert event["id"] == "test-001"
    assert event["time"] == "2026-07-01T00:00:00Z"
    assert event["type"] == "hummbl.tuple.CONTRACT.ok"
    assert event["source"] == "/hummbl/tuples/test-agent"
    assert event["subject"] == "intent-001"
    assert event["datacontenttype"] == "application/json"
    assert event["data"] == t


def test_cloudevent_no_state():
    """Tuples without state should not include state in type."""
    t = {"tuple_type": "BASEN", "id": "test-002", "time": "2026-07-01T00:00:00Z", "tuple_data": {}}
    event = tuple_to_cloudevent(t)
    assert event["type"] == "hummbl.tuple.BASEN"


def test_cloudevent_no_intent_id():
    """Tuples without intent_id should not have subject."""
    t = {"tuple_type": "CONTRACT", "id": "test-003", "time": "2026-07-01T00:00:00Z", "state": "ok", "tuple_data": {}}
    event = tuple_to_cloudevent(t)
    assert "subject" not in event


def test_cloudevent_extension_attrs():
    """Extension attributes should be present when fields exist."""
    t = {
        "tuple_type": "CONTRACT",
        "id": "test-004",
        "time": "2026-07-01T00:00:00Z",
        "state": "blocked",
        "drift": 0.5,
        "tier": 2,
        "agent": "agent-x",
        "tool": "tool-y",
        "tuple_data": {},
    }
    event = tuple_to_cloudevent(t)
    assert event["hummbltuple_type"] == "CONTRACT"
    assert event["hummblstate"] == "blocked"
    assert event["hummblrift"] == 0.5
    assert event["hummbltier"] == 2
    assert event["hummbltool"] == "tool-y"


def test_ndjson_format():
    """tuple_to_ndjson should produce a JSON string."""
    t = {"tuple_type": "CONTRACT", "id": "test", "tuple_data": {}}
    line = tuple_to_ndjson(t)
    parsed = json.loads(line)
    assert parsed["tuple_type"] == "CONTRACT"
    assert parsed["id"] == "test"


def test_convert_trace_cloudevents():
    """convert_trace should produce a list of CloudEvents."""
    trace = [
        {"tuple_type": "CONTRACT", "id": "1", "time": "2026-07-01T00:00:00Z", "state": "ok", "tuple_data": {}},
        {"tuple_type": "EVIDENCE", "id": "2", "time": "2026-07-01T00:00:01Z", "state": "ok", "tuple_data": {}},
    ]
    events = convert_trace(trace, "cloudevents")
    assert isinstance(events, list)
    assert len(events) == 2
    assert events[0]["type"] == "hummbl.tuple.CONTRACT.ok"
    assert events[1]["type"] == "hummbl.tuple.EVIDENCE.ok"


def test_convert_trace_ndjson():
    """convert_trace should produce NDJSON string."""
    trace = [
        {"tuple_type": "CONTRACT", "id": "1", "tuple_data": {}},
        {"tuple_type": "EVIDENCE", "id": "2", "tuple_data": {}},
    ]
    result = convert_trace(trace, "ndjson")
    assert isinstance(result, str)
    lines = result.strip().split("\n")
    assert len(lines) == 2
    json.loads(lines[0])
    json.loads(lines[1])


def test_convert_trace_unsupported_format():
    """convert_trace should raise ValueError for unsupported format."""
    try:
        convert_trace([], "xml")
        assert False, "Should have raised ValueError"
    except ValueError:
        pass


def test_data_is_full_tuple():
    """The data field should contain the full original tuple."""
    t = {
        "tuple_type": "CONTRACT",
        "id": "test-full",
        "time": "2026-07-01T00:00:00Z",
        "state": "ok",
        "tuple_data": {"contract_id": "full-test", "delegatee": "service"},
    }
    event = tuple_to_cloudevent(t)
    assert event["data"] == t, "data field should contain the full tuple"


if __name__ == "__main__":
    test_cloudevent_basic()
    test_cloudevent_no_state()
    test_cloudevent_no_intent_id()
    test_cloudevent_extension_attrs()
    test_ndjson_format()
    test_convert_trace_cloudevents()
    test_convert_trace_ndjson()
    test_convert_trace_unsupported_format()
    test_data_is_full_tuple()
    print("All tuple-to-events tests passed")
