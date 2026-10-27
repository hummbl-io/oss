"""Tests for the kill-switch MCP server (hummbl_mcp.mcp_kill_switch).

Regression coverage for the defect where every tool call raised
``NameError: name 'get_kill_switch_core' is not defined`` because the
accessor imported from ``hummbl_governance.kill_switch`` did not exist.

These tests exercise the real governance core (no mocks of the unit
under test): the status tool must return a real state, and engage /
disengage transitions on the shared core must be visible through the
check-task and history tools.
"""

import json

import pytest

pytest.importorskip("hummbl_governance")

import hummbl_governance.kill_switch as ks_module
from hummbl_governance.kill_switch import KillSwitchMode

from hummbl_mcp import mcp_kill_switch as server


@pytest.fixture(autouse=True)
def _fresh_core(tmp_path, monkeypatch):
    """Give each test an isolated, disengaged shared core."""
    monkeypatch.setenv("GOVERNANCE_STATE_DIR", str(tmp_path))
    monkeypatch.setattr(ks_module, "_core_instance", None)
    yield
    monkeypatch.setattr(ks_module, "_core_instance", None)


def _call_tool(name, arguments=None):
    response = server.handle_request(
        {
            "method": "tools/call",
            "id": 1,
            "params": {"name": name, "arguments": arguments or {}},
        }
    )
    assert response is not None
    result = response["result"]
    assert result.get("isError") is not True, result
    return json.loads(result["content"][0]["text"])


def test_status_tool_returns_real_state():
    payload = _call_tool("ks_status")
    assert payload["mode"] == "DISENGAGED"
    assert payload["engaged"] is False
    assert "safety_monitoring" in payload["critical_tasks"]
    assert "error" not in payload


def test_check_task_allowed_when_disengaged():
    payload = _call_tool("ks_check_task", {"task_name": "briefing_generation"})
    assert payload["task"] == "briefing_generation"
    assert payload["allowed"] is True
    assert payload["action"] == "allow"


def test_check_task_reflects_engagement_and_release():
    core = ks_module.get_kill_switch_core()
    core.engage(
        KillSwitchMode.EMERGENCY,
        reason="test engagement",
        triggered_by="test",
    )
    try:
        payload = _call_tool("ks_check_task", {"task_name": "briefing_generation"})
        assert payload["allowed"] is False
        assert payload["action"] == "block"

        status = _call_tool("ks_status")
        assert status["mode"] == "EMERGENCY"
        assert status["engaged"] is True
    finally:
        core.disengage(triggered_by="test")

    payload = _call_tool("ks_check_task", {"task_name": "briefing_generation"})
    assert payload["allowed"] is True


def test_history_tool_reports_transitions():
    core = ks_module.get_kill_switch_core()
    core.engage(
        KillSwitchMode.HALT_NONCRITICAL,
        reason="test engagement",
        triggered_by="test",
    )
    core.disengage(triggered_by="test")

    payload = _call_tool("ks_history", {"limit": 10})
    assert payload["count"] >= 2
    modes = [event["mode"] for event in payload["events"]]
    assert "HALT_NONCRITICAL" in modes
    assert "DISENGAGED" in modes
