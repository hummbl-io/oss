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

"""Tests for mcp_server.py — governance MCP server (stdio JSON-RPC).

Tests the tool handlers directly plus protocol-level initialize/tools/list/tools/call
round-trips via subprocess stdin/stdout.
"""

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Path setup so we can import the top-level mcp_server module
# ---------------------------------------------------------------------------
_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT))

import mcp_server  # noqa: E402


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture(autouse=True)
def _fresh_instances(tmp_path, monkeypatch):
    """Each test gets a clean state dir and fresh singleton instances."""
    monkeypatch.setitem(mcp_server._instances, "ks", None)
    mcp_server._instances.clear()
    monkeypatch.setattr(mcp_server, "STATE_DIR", str(tmp_path / "state"))
    monkeypatch.setattr(mcp_server, "DB_PATH", str(tmp_path / "state" / "costs.db"))
    monkeypatch.setattr(mcp_server, "AUDIT_DIR", str(tmp_path / "state" / "audit"))
    yield
    mcp_server._instances.clear()


# ---------------------------------------------------------------------------
# governance_status
# ---------------------------------------------------------------------------
def test_governance_status_returns_all_keys():
    result = mcp_server.handle_tool("governance_status", {})
    assert "kill_switch" in result
    assert "circuit_breaker" in result
    assert "cost_governor" in result


def test_governance_status_kill_switch_disengaged():
    result = mcp_server.handle_tool("governance_status", {})
    assert result["kill_switch"]["engaged"] is False


def test_governance_status_circuit_breaker_closed():
    result = mcp_server.handle_tool("governance_status", {})
    assert result["circuit_breaker"]["state"] == "CLOSED"


# ---------------------------------------------------------------------------
# kill_switch_status
# ---------------------------------------------------------------------------
def test_kill_switch_status_basic():
    result = mcp_server.handle_tool("kill_switch_status", {})
    assert "status" in result
    assert "history" in result


def test_kill_switch_status_history_is_list():
    result = mcp_server.handle_tool("kill_switch_status", {"history_limit": 3})
    assert isinstance(result["history"], list)


# ---------------------------------------------------------------------------
# kill_switch_engage / disengage
# ---------------------------------------------------------------------------
def test_kill_switch_engage_requires_confirm():
    result = mcp_server.handle_tool("kill_switch_engage", {
        "mode": "HALT_NONCRITICAL",
        "reason": "test",
        "confirm": False,
    })
    assert "error" in result


def test_kill_switch_engage_halt_noncritical():
    result = mcp_server.handle_tool("kill_switch_engage", {
        "mode": "HALT_NONCRITICAL",
        "reason": "unit test",
        "confirm": True,
        "triggered_by": "pytest",
    })
    assert result["engaged"] is True
    assert result["mode"] == "HALT_NONCRITICAL"


def test_kill_switch_engage_halt_all():
    result = mcp_server.handle_tool("kill_switch_engage", {
        "mode": "HALT_ALL",
        "reason": "full stop",
        "confirm": True,
    })
    assert result["engaged"] is True


def test_kill_switch_engage_emergency():
    result = mcp_server.handle_tool("kill_switch_engage", {
        "mode": "EMERGENCY",
        "reason": "emergency",
        "confirm": True,
    })
    assert result["engaged"] is True


def test_kill_switch_engage_invalid_mode():
    result = mcp_server.handle_tool("kill_switch_engage", {
        "mode": "BOGUS",
        "reason": "test",
        "confirm": True,
    })
    assert "error" in result


def test_kill_switch_disengage():
    mcp_server.handle_tool("kill_switch_engage", {
        "mode": "HALT_NONCRITICAL",
        "reason": "engage first",
        "confirm": True,
    })
    result = mcp_server.handle_tool("kill_switch_disengage", {
        "reason": "all clear",
        "triggered_by": "pytest",
    })
    assert result["disengaged"] is True


# ---------------------------------------------------------------------------
# circuit_breaker_status
# ---------------------------------------------------------------------------
def test_circuit_breaker_status():
    result = mcp_server.handle_tool("circuit_breaker_status", {})
    assert "state" in result
    assert "failure_count" in result
    assert result["state"] == "CLOSED"


# ---------------------------------------------------------------------------
# cost_budget_check / cost_record_usage
# ---------------------------------------------------------------------------
def test_cost_budget_check_returns_decision():
    result = mcp_server.handle_tool("cost_budget_check", {})
    assert "decision" in result


def test_cost_record_usage():
    result = mcp_server.handle_tool("cost_record_usage", {
        "provider": "anthropic",
        "model": "claude-opus-4-6",
        "tokens_in": 1000,
        "tokens_out": 500,
        "cost": 0.05,
    })
    assert result["recorded"] is True
    assert result["cost"] == 0.05


def test_cost_record_usage_reflected_in_check():
    mcp_server.handle_tool("cost_record_usage", {
        "provider": "openai",
        "model": "gpt-4o",
        "tokens_in": 100,
        "tokens_out": 100,
        "cost": 0.01,
    })
    result = mcp_server.handle_tool("cost_budget_check", {})
    assert "decision" in result


# ---------------------------------------------------------------------------
# audit_query
# ---------------------------------------------------------------------------
def test_audit_query_empty_no_filters():
    result = mcp_server.handle_tool("audit_query", {})
    assert "count" in result
    assert "entries" in result
    assert result["count"] == 0


def test_audit_query_by_intent_id():
    result = mcp_server.handle_tool("audit_query", {"intent_id": "intent-abc"})
    assert "entries" in result


def test_audit_query_by_task_id():
    result = mcp_server.handle_tool("audit_query", {"task_id": "task-xyz"})
    assert "entries" in result


def test_audit_query_limit_respected():
    result = mcp_server.handle_tool("audit_query", {"limit": 5})
    assert result["count"] <= 5


# ---------------------------------------------------------------------------
# compliance_report
# ---------------------------------------------------------------------------
def test_compliance_report_returns_report_key():
    result = mcp_server.handle_tool("compliance_report", {})
    assert "report" in result or "error" in result


def test_compliance_report_soc2():
    result = mcp_server.handle_tool("compliance_report", {"framework": "soc2"})
    assert "report" in result or "error" in result


# ---------------------------------------------------------------------------
# health_check
# ---------------------------------------------------------------------------
def test_health_check_returns_overall_healthy():
    result = mcp_server.handle_tool("health_check", {})
    assert "overall_healthy" in result
    assert "probes" in result


def test_health_check_probes_have_expected_names():
    result = mcp_server.handle_tool("health_check", {})
    probe_names = {p["name"] for p in result["probes"]}
    assert "kill_switch" in probe_names
    assert "cost_governor" in probe_names


def test_health_check_healthy_when_no_issues():
    result = mcp_server.handle_tool("health_check", {})
    assert result["overall_healthy"] is True


# ---------------------------------------------------------------------------
# Unknown tool
# ---------------------------------------------------------------------------
def test_unknown_tool_returns_error():
    result = mcp_server.handle_tool("nonexistent_tool", {})
    assert "error" in result


# ---------------------------------------------------------------------------
# Protocol-level: JSON-RPC via subprocess stdin/stdout
# ---------------------------------------------------------------------------
def _rpc(messages):
    """Send JSON-RPC messages to mcp_server via subprocess and return parsed responses."""
    server_path = str(_REPO_ROOT / "mcp_server.py")
    env = os.environ.copy()
    env["GOVERNANCE_STATE_DIR"] = str(Path(tempfile.mkdtemp()) / "state")

    proc = subprocess.Popen(
        [sys.executable, server_path],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        text=True,
    )
    inp = "\n".join(json.dumps(m) for m in messages) + "\n"
    try:
        stdout, _ = proc.communicate(input=inp, timeout=10)
    except subprocess.TimeoutExpired:
        proc.kill()
        stdout, _ = proc.communicate()

    responses = []
    for line in stdout.splitlines():
        line = line.strip()
        if line:
            try:
                responses.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return responses


def test_protocol_initialize():
    responses = _rpc([
        {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
    ])
    assert len(responses) == 1
    r = responses[0]
    assert r["id"] == 1
    assert "result" in r
    assert r["result"]["serverInfo"]["name"] == "hummbl-governance"


def test_protocol_tools_list():
    responses = _rpc([
        {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
        {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
    ])
    tools_resp = next(r for r in responses if r["id"] == 2)
    tool_names = {t["name"] for t in tools_resp["result"]["tools"]}
    assert "governance_status" in tool_names
    assert "kill_switch_status" in tool_names
    assert "health_check" in tool_names


def test_protocol_tools_call_governance_status():
    responses = _rpc([
        {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
        {
            "jsonrpc": "2.0", "id": 2,
            "method": "tools/call",
            "params": {"name": "governance_status", "arguments": {}},
        },
    ])
    call_resp = next(r for r in responses if r["id"] == 2)
    assert "result" in call_resp
    content = call_resp["result"]["content"][0]["text"]
    data = json.loads(content)
    assert "kill_switch" in data


def test_protocol_ping():
    responses = _rpc([
        {"jsonrpc": "2.0", "id": 99, "method": "ping", "params": {}},
    ])
    assert any(r["id"] == 99 for r in responses)


def test_protocol_unknown_method():
    responses = _rpc([
        {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
        {"jsonrpc": "2.0", "id": 2, "method": "bogus/method", "params": {}},
    ])
    err_resp = next(r for r in responses if r["id"] == 2)
    assert "error" in err_resp
