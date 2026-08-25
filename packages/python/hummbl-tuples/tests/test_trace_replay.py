#!/usr/bin/env python3
"""Tests for trace replay debugger (issue #34)."""

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from trace_replay import TraceReplay, load_trace


def test_replay_init():
    """TraceReplay should initialize with cursor at 0."""
    trace = [{"tuple_type": "CONTRACT", "id": "1"}, {"tuple_type": "EVIDENCE", "id": "2"}]
    r = TraceReplay(trace)
    assert r.cursor == 0
    assert r.current == trace[0]


def test_step_forward():
    """step_forward should advance the cursor."""
    trace = [{"id": "1"}, {"id": "2"}, {"id": "3"}]
    r = TraceReplay(trace)
    r.step_forward()
    assert r.cursor == 1
    r.step_forward()
    assert r.cursor == 2


def test_step_backward():
    """step_backward should move the cursor back."""
    trace = [{"id": "1"}, {"id": "2"}, {"id": "3"}]
    r = TraceReplay(trace)
    r.goto(2)
    r.step_backward()
    assert r.cursor == 1


def test_goto():
    """goto should jump to a specific index."""
    trace = [{"id": "1"}, {"id": "2"}, {"id": "3"}]
    r = TraceReplay(trace)
    r.goto(2)
    assert r.cursor == 2
    assert r.current == trace[2]


def test_goto_out_of_range():
    """goto with out-of-range index should not move cursor."""
    trace = [{"id": "1"}]
    r = TraceReplay(trace)
    r.goto(5)
    assert r.cursor == 0


def test_reset():
    """reset should move cursor to 0."""
    trace = [{"id": "1"}, {"id": "2"}]
    r = TraceReplay(trace)
    r.goto(1)
    r.reset()
    assert r.cursor == 0


def test_list_agents():
    """list_agents should return unique agent IDs."""
    trace = [
        {"agent": "alpha"},
        {"agent": "beta"},
        {"agent": "alpha"},
    ]
    r = TraceReplay(trace)
    agents = r.list_agents()
    assert agents == ["alpha", "beta"]


def test_filter_by_agent():
    """filter_by_agent should return only events for the given agent."""
    trace = [
        {"agent": "alpha", "id": "1"},
        {"agent": "beta", "id": "2"},
        {"agent": "alpha", "id": "3"},
    ]
    r = TraceReplay(trace)
    alpha_events = r.filter_by_agent("alpha")
    assert len(alpha_events) == 2
    assert alpha_events[0]["id"] == "1"
    assert alpha_events[1]["id"] == "3"


def test_get_state_at():
    """get_state_at should reconstruct agent state."""
    trace = [
        {"agent": "alpha", "tuple_type": "CONTRACT", "state": "ok", "tool": "tool1"},
        {"agent": "alpha", "tuple_type": "EVIDENCE", "state": "ok", "tool": "tool2"},
        {"agent": "beta", "tuple_type": "SYSTEM", "state": "blocked", "tool": "tool1"},
    ]
    r = TraceReplay(trace)
    states = r.get_state_at(2)
    assert "alpha" in states
    assert "beta" in states
    assert states["alpha"]["event_count"] == 2
    assert states["beta"]["event_count"] == 1
    assert "CONTRACT" in states["alpha"]["tuple_types"]
    assert "tool1" in states["alpha"]["tools_used"]


def test_checkpoint():
    """checkpoint should capture state at a given index."""
    trace = [
        {"agent": "alpha", "tuple_type": "CONTRACT", "id": "1"},
        {"agent": "beta", "tuple_type": "EVIDENCE", "id": "2"},
    ]
    r = TraceReplay(trace)
    cp = r.checkpoint(1)
    assert cp["checkpoint_index"] == 1
    assert cp["total_events"] == 2
    assert cp["event_at_checkpoint"]["id"] == "2"


def test_summary():
    """summary should return trace metadata."""
    trace = [
        {"agent": "alpha", "tuple_type": "CONTRACT", "state": "ok"},
        {"agent": "beta", "tuple_type": "EVIDENCE", "state": "blocked"},
    ]
    r = TraceReplay(trace)
    s = r.summary()
    assert s["total_events"] == 2
    assert "alpha" in s["agents"]
    assert "beta" in s["agents"]
    assert "CONTRACT" in s["tuple_types"]
    assert "ok" in s["states"]


def test_format_event():
    """format_event should produce a readable string."""
    event = {"tuple_type": "CONTRACT", "id": "test-001", "state": "ok", "agent": "alpha", "time": "2026-07-01"}
    r = TraceReplay([])
    formatted = r.format_event(event, 0)
    assert "CONTRACT" in formatted
    assert "test-001" in formatted
    assert "alpha" in formatted


def test_is_at_start_end():
    """is_at_start and is_at_end should report cursor position correctly."""
    trace = [{"id": "1"}, {"id": "2"}, {"id": "3"}]
    r = TraceReplay(trace)
    assert r.is_at_start
    assert not r.is_at_end
    r.goto(2)
    assert not r.is_at_start
    assert r.is_at_end


if __name__ == "__main__":
    test_replay_init()
    test_step_forward()
    test_step_backward()
    test_goto()
    test_goto_out_of_range()
    test_reset()
    test_list_agents()
    test_filter_by_agent()
    test_get_state_at()
    test_checkpoint()
    test_summary()
    test_format_event()
    test_is_at_start_end()
    print("All trace replay tests passed")
