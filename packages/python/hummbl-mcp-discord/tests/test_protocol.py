"""Protocol tests for the discord MCP shim's JSON-RPC handling.

Pins the wire behavior that the shared hummbl-mcp-stdio dispatcher
must preserve when this shim migrates.
"""

from __future__ import annotations

import io
import json

import discord_mcp_server as srv


def _call(method, params=None, req_id=1):
    req = {"jsonrpc": "2.0", "id": req_id, "method": method}
    if params is not None:
        req["params"] = params
    return srv.handle_request(req)


def test_initialize_returns_server_info():
    res = _call("initialize")
    assert res["jsonrpc"] == "2.0"
    assert res["id"] == 1
    result = res["result"]
    assert result["protocolVersion"] == "2024-11-05"
    assert result["serverInfo"] == {"name": "discord", "version": "0.1.0"}
    assert result["capabilities"] == {"tools": {}}


def test_tools_list_declares_two_tools():
    res = _call("tools/list")
    names = [t["name"] for t in res["result"]["tools"]]
    assert names == ["discord_channel_summarize", "discord_draft_reply"]


def test_non_dict_request_returns_invalid_request():
    res = srv.handle_request([1, 2, 3])
    assert res["error"]["code"] == -32600
    assert res["error"]["message"] == "Invalid Request"


def test_non_dict_params_normalized():
    res = _call("tools/call", params=None)
    res = srv.handle_request(
        {"jsonrpc": "2.0", "id": 9, "method": "tools/call", "params": [1, 2]}
    )
    assert res["error"]["code"] == -32601


def test_unknown_method_returns_method_not_found():
    res = _call("bogus/method")
    assert res["error"]["code"] == -32601
    assert "Method not found" in res["error"]["message"]


def test_unknown_tool_returns_tool_not_found():
    res = _call("tools/call", {"name": "nope", "arguments": {}})
    assert res["error"]["code"] == -32601
    assert "Tool not found" in res["error"]["message"]


def test_main_loop_roundtrip_and_bad_lines(monkeypatch):
    lines = [
        json.dumps({"jsonrpc": "2.0", "id": 7, "method": "initialize"}),
        "not json",
        "",
        json.dumps({"jsonrpc": "2.0", "id": 8, "method": "tools/list"}),
    ]
    stdout = io.StringIO()
    monkeypatch.setattr("sys.stdin", io.StringIO("\n".join(lines) + "\n"))
    monkeypatch.setattr("sys.stdout", stdout)
    srv.main()
    out_lines = [json.loads(l) for l in stdout.getvalue().splitlines() if l.strip()]
    assert [r["id"] for r in out_lines] == [7, 8]
    assert out_lines[0]["result"]["serverInfo"]["name"] == "discord"
