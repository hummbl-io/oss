"""Regression tests for oss#345: MCPGateway dispatch wiring and mcp_git_vault option-injection guards."""

import json
from pathlib import Path
from unittest.mock import patch

from hummbl_mcp.mcp_gateway import MCPGateway
from hummbl_mcp.mcp_git_vault import handle_git_diff, handle_git_stage
from hummbl_mcp.protocol import JsonRpcRequest, ToolDefinition
from hummbl_mcp.server import HummblMCPServer


def _make_server(blocked_tools=None, kill_switch_state=None, monkeypatch=None):
    if monkeypatch and kill_switch_state:
        monkeypatch.setenv("MCP_KILL_SWITCH_STATE", kill_switch_state)
    tdef = ToolDefinition(
        name="demo_write",
        description="demo write tool",
        input_schema={"type": "object", "properties": {"path": {"type": "string"}}},
    )
    server = HummblMCPServer(
        tool_definitions=[tdef],
        handlers={"demo_write": lambda args: {"ok": True, "args": args}},
    )
    if blocked_tools is not None:
        server.gateway = MCPGateway(
            bus_poster=lambda *a: None,
            blocked_tools=blocked_tools,
        )
    return server


def test_server_blocks_tool_on_gateway_blocked_list():
    server = _make_server(blocked_tools=["demo_write"])
    resp = server.handle(
        JsonRpcRequest(
            jsonrpc="2.0",
            id=1,
            method="tools/call",
            params={"name": "demo_write", "arguments": {"path": "ok.txt"}},
        )
    )
    assert resp is not None
    assert resp["result"]["isError"] is True
    payload = json.loads(resp["result"]["content"][0]["text"])
    assert payload["verdict"] == "BLOCK"
    assert "BLOCKED_TOOL" in payload["error"]


def test_server_blocks_path_traversal_via_gateway():
    server = _make_server()
    resp = server.handle(
        JsonRpcRequest(
            jsonrpc="2.0",
            id=2,
            method="tools/call",
            params={"name": "demo_write", "arguments": {"path": "../../etc/passwd"}},
        )
    )
    assert resp is not None
    assert resp["result"]["isError"] is True
    payload = json.loads(resp["result"]["content"][0]["text"])
    assert payload["verdict"] == "BLOCK"
    assert "PATH_TRAVERSAL" in payload["error"]


def test_server_allows_clean_tool_call():
    server = _make_server()
    resp = server.handle(
        JsonRpcRequest(
            jsonrpc="2.0",
            id=3,
            method="tools/call",
            params={"name": "demo_write", "arguments": {"path": "safe/file.txt"}},
        )
    )
    assert resp is not None
    assert resp["result"]["isError"] is False
    payload = json.loads(resp["result"]["content"][0]["text"])
    assert payload["ok"] is True


def test_vault_git_diff_rejects_option_shaped_path(tmp_path: Path):
    with patch("hummbl_mcp.mcp_git_vault.get_git_root", return_value=str(tmp_path)):
        res = handle_git_diff({"paths": ["--output=/tmp/pwned"]})
    assert res["isError"] is True
    assert "Option-shaped path" in res["content"][0]["text"]


def test_vault_git_diff_rejects_outside_workspace_path(tmp_path: Path):
    with patch("hummbl_mcp.mcp_git_vault.get_git_root", return_value=str(tmp_path)):
        res = handle_git_diff({"paths": ["../outside.txt"]})
    assert res["isError"] is True
    assert "resolves outside the workspace" in res["content"][0]["text"]


def test_vault_git_stage_rejects_option_shaped_path(tmp_path: Path):
    with patch("hummbl_mcp.mcp_git_vault.get_git_root", return_value=str(tmp_path)):
        res = handle_git_stage({"paths": ["--all"]})
    assert res["isError"] is True
    assert "Option-shaped path" in res["content"][0]["text"]
