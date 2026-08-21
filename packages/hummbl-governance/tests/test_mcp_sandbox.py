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

"""Tests for mcp_sandbox.py — agent sandboxing MCP server."""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT))

import mcp_sandbox  # noqa: E402


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture(autouse=True)
def _clean_sandboxes():
    """Each test gets a clean sandbox registry."""
    mcp_sandbox._sandboxes.clear()
    yield
    mcp_sandbox._sandboxes.clear()


@pytest.fixture()
def basic_sandbox(tmp_path, monkeypatch):
    """Create a sandbox and return its ID."""
    monkeypatch.setattr(mcp_sandbox, "STATE_DIR", tmp_path / "sandbox")
    result = mcp_sandbox.handle_tool("sandbox_create", {"agent_name": "test-agent"})
    return result["sandbox"]["id"]


# ---------------------------------------------------------------------------
# sandbox_create
# ---------------------------------------------------------------------------
def test_sandbox_create_returns_id(tmp_path, monkeypatch):
    monkeypatch.setattr(mcp_sandbox, "STATE_DIR", tmp_path / "sandbox")
    result = mcp_sandbox.handle_tool("sandbox_create", {"agent_name": "my-agent"})
    assert result["created"] is True
    assert result["sandbox"]["id"].startswith("sbx-")


def test_sandbox_create_stores_agent_name(tmp_path, monkeypatch):
    monkeypatch.setattr(mcp_sandbox, "STATE_DIR", tmp_path / "sandbox")
    result = mcp_sandbox.handle_tool("sandbox_create", {"agent_name": "my-agent"})
    assert result["sandbox"]["agent"] == "my-agent"


def test_sandbox_create_with_allowed_tools(tmp_path, monkeypatch):
    monkeypatch.setattr(mcp_sandbox, "STATE_DIR", tmp_path / "sandbox")
    result = mcp_sandbox.handle_tool("sandbox_create", {
        "agent_name": "restricted-agent",
        "allowed_tools": ["read", "write"],
    })
    assert result["sandbox"]["allowed_tools"] == ["read", "write"]


def test_sandbox_create_with_blocked_paths(tmp_path, monkeypatch):
    monkeypatch.setattr(mcp_sandbox, "STATE_DIR", tmp_path / "sandbox")
    result = mcp_sandbox.handle_tool("sandbox_create", {
        "agent_name": "agent",
        "blocked_paths": ["/etc", "/root"],
    })
    assert "/etc" in result["sandbox"]["blocked_paths"]


def test_sandbox_create_with_cost_cap(tmp_path, monkeypatch):
    monkeypatch.setattr(mcp_sandbox, "STATE_DIR", tmp_path / "sandbox")
    result = mcp_sandbox.handle_tool("sandbox_create", {
        "agent_name": "agent",
        "max_cost": 5.0,
    })
    assert result["sandbox"]["max_cost"] == 5.0


def test_sandbox_create_default_cost_cap(tmp_path, monkeypatch):
    monkeypatch.setattr(mcp_sandbox, "STATE_DIR", tmp_path / "sandbox")
    result = mcp_sandbox.handle_tool("sandbox_create", {"agent_name": "agent"})
    assert result["sandbox"]["max_cost"] == 10.0


# ---------------------------------------------------------------------------
# sandbox_check
# ---------------------------------------------------------------------------
def test_sandbox_check_allows_unlisted_tool_when_no_allowlist(basic_sandbox):
    result = mcp_sandbox.handle_tool("sandbox_check", {
        "sandbox_id": basic_sandbox,
        "tool": "any_tool",
    })
    assert result["allowed"] is True


def test_sandbox_check_allows_listed_tool(tmp_path, monkeypatch):
    monkeypatch.setattr(mcp_sandbox, "STATE_DIR", tmp_path / "sandbox")
    sb = mcp_sandbox.handle_tool("sandbox_create", {
        "agent_name": "agent",
        "allowed_tools": ["read", "search"],
    })["sandbox"]["id"]
    result = mcp_sandbox.handle_tool("sandbox_check", {"sandbox_id": sb, "tool": "read"})
    assert result["allowed"] is True


def test_sandbox_check_denies_unlisted_tool(tmp_path, monkeypatch):
    monkeypatch.setattr(mcp_sandbox, "STATE_DIR", tmp_path / "sandbox")
    sb = mcp_sandbox.handle_tool("sandbox_create", {
        "agent_name": "agent",
        "allowed_tools": ["read"],
    })["sandbox"]["id"]
    result = mcp_sandbox.handle_tool("sandbox_check", {"sandbox_id": sb, "tool": "exec"})
    assert result["allowed"] is False


def test_sandbox_check_denies_blocked_path(tmp_path, monkeypatch):
    monkeypatch.setattr(mcp_sandbox, "STATE_DIR", tmp_path / "sandbox")
    sb = mcp_sandbox.handle_tool("sandbox_create", {
        "agent_name": "agent",
        "blocked_paths": ["/etc"],
    })["sandbox"]["id"]
    result = mcp_sandbox.handle_tool("sandbox_check", {
        "sandbox_id": sb, "tool": "read", "path": "/etc/passwd",
    })
    assert result["allowed"] is False


def test_sandbox_check_denies_cost_exceeded(tmp_path, monkeypatch):
    monkeypatch.setattr(mcp_sandbox, "STATE_DIR", tmp_path / "sandbox")
    sb = mcp_sandbox.handle_tool("sandbox_create", {
        "agent_name": "agent",
        "max_cost": 1.0,
    })["sandbox"]["id"]
    result = mcp_sandbox.handle_tool("sandbox_check", {
        "sandbox_id": sb, "tool": "call", "cost": 2.0,
    })
    assert result["allowed"] is False


def test_sandbox_check_tracks_cumulative_cost(basic_sandbox):
    mcp_sandbox.handle_tool("sandbox_check", {"sandbox_id": basic_sandbox, "tool": "a", "cost": 1.0})
    result = mcp_sandbox.handle_tool("sandbox_check", {"sandbox_id": basic_sandbox, "tool": "b", "cost": 1.0})
    assert result["allowed"] is True
    assert result["cost_remaining"] == pytest.approx(8.0)


def test_sandbox_check_unknown_sandbox():
    result = mcp_sandbox.handle_tool("sandbox_check", {"sandbox_id": "sbx-notreal", "tool": "x"})
    assert "error" in result


# ---------------------------------------------------------------------------
# sandbox_validate_output
# ---------------------------------------------------------------------------
def test_sandbox_validate_output_clean(basic_sandbox):
    result = mcp_sandbox.handle_tool("sandbox_validate_output", {
        "sandbox_id": basic_sandbox,
        "output": "Hello, world! This is clean output.",
    })
    assert result["valid"] is True
    assert result["issues"] == []


def test_sandbox_validate_output_api_key_leak(basic_sandbox):
    result = mcp_sandbox.handle_tool("sandbox_validate_output", {
        "sandbox_id": basic_sandbox,
        "output": "Here is your key: sk-abcdefghijklmnopqrstuvwxyz1234567890",
    })
    assert result["valid"] is False
    assert any(i["type"] == "secret_leak" for i in result["issues"])


def test_sandbox_validate_output_github_pat(basic_sandbox):
    result = mcp_sandbox.handle_tool("sandbox_validate_output", {
        "sandbox_id": basic_sandbox,
        "output": "token: ghp_" + "A" * 36,
    })
    assert result["valid"] is False


def test_sandbox_validate_output_excessive_length(basic_sandbox):
    result = mcp_sandbox.handle_tool("sandbox_validate_output", {
        "sandbox_id": basic_sandbox,
        "output": "x" * 100001,
    })
    assert result["valid"] is False
    assert any(i["type"] == "excessive_output" for i in result["issues"])


def test_sandbox_validate_output_unknown_sandbox():
    result = mcp_sandbox.handle_tool("sandbox_validate_output", {
        "sandbox_id": "sbx-ghost",
        "output": "text",
    })
    assert "error" in result


# ---------------------------------------------------------------------------
# sandbox_status
# ---------------------------------------------------------------------------
def test_sandbox_status_specific(basic_sandbox):
    result = mcp_sandbox.handle_tool("sandbox_status", {"sandbox_id": basic_sandbox})
    assert "sandbox" in result
    assert result["sandbox"]["id"] == basic_sandbox


def test_sandbox_status_all(tmp_path, monkeypatch):
    monkeypatch.setattr(mcp_sandbox, "STATE_DIR", tmp_path / "sandbox")
    mcp_sandbox.handle_tool("sandbox_create", {"agent_name": "a1"})
    mcp_sandbox.handle_tool("sandbox_create", {"agent_name": "a2"})
    result = mcp_sandbox.handle_tool("sandbox_status", {})
    assert result["active_sandboxes"] == 2
    assert len(result["sandboxes"]) == 2


def test_sandbox_status_unknown():
    result = mcp_sandbox.handle_tool("sandbox_status", {"sandbox_id": "sbx-ghost"})
    assert "error" in result


# ---------------------------------------------------------------------------
# sandbox_destroy
# ---------------------------------------------------------------------------
def test_sandbox_destroy_returns_receipt(basic_sandbox):
    result = mcp_sandbox.handle_tool("sandbox_destroy", {"sandbox_id": basic_sandbox})
    assert result["destroyed"] is True
    assert "total_actions" in result
    assert "total_cost" in result


def test_sandbox_destroy_removes_from_registry(basic_sandbox):
    mcp_sandbox.handle_tool("sandbox_destroy", {"sandbox_id": basic_sandbox})
    result = mcp_sandbox.handle_tool("sandbox_status", {"sandbox_id": basic_sandbox})
    assert "error" in result


def test_sandbox_destroy_unknown():
    result = mcp_sandbox.handle_tool("sandbox_destroy", {"sandbox_id": "sbx-ghost"})
    assert "error" in result


def test_sandbox_destroy_includes_duration(basic_sandbox):
    result = mcp_sandbox.handle_tool("sandbox_destroy", {"sandbox_id": basic_sandbox})
    assert "duration_sec" in result
    assert result["duration_sec"] >= 0


# ---------------------------------------------------------------------------
# Unknown tool
# ---------------------------------------------------------------------------
def test_unknown_tool():
    result = mcp_sandbox.handle_tool("no_such_tool", {})
    assert "error" in result


# ---------------------------------------------------------------------------
# Protocol-level: subprocess JSON-RPC
# ---------------------------------------------------------------------------
def _rpc_sandbox(messages, tmp_dir):
    server_path = str(_REPO_ROOT / "mcp_sandbox.py")
    env = os.environ.copy()
    env["SANDBOX_STATE_DIR"] = str(tmp_dir)

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


def test_sandbox_protocol_initialize(tmp_path):
    responses = _rpc_sandbox([
        {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
    ], tmp_path)
    assert any(r.get("id") == 1 and "result" in r for r in responses)
    r = next(r for r in responses if r.get("id") == 1)
    assert r["result"]["serverInfo"]["name"] == "hummbl-sandbox"


def test_sandbox_protocol_tools_list(tmp_path):
    responses = _rpc_sandbox([
        {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
        {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
    ], tmp_path)
    tools_resp = next(r for r in responses if r.get("id") == 2)
    names = {t["name"] for t in tools_resp["result"]["tools"]}
    assert "sandbox_create" in names
    assert "sandbox_check" in names
    assert "sandbox_destroy" in names


def test_sandbox_protocol_create_and_status(tmp_path):
    responses = _rpc_sandbox([
        {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
        {
            "jsonrpc": "2.0", "id": 2,
            "method": "tools/call",
            "params": {"name": "sandbox_create", "arguments": {"agent_name": "test-agent"}},
        },
        {
            "jsonrpc": "2.0", "id": 3,
            "method": "tools/call",
            "params": {"name": "sandbox_status", "arguments": {}},
        },
    ], tmp_path)
    status_resp = next(r for r in responses if r.get("id") == 3)
    data = json.loads(status_resp["result"]["content"][0]["text"])
    assert data["active_sandboxes"] == 1
