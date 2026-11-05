"""Protocol tests for the omnichannel MCP shim's JSON-RPC handling.

Pins the wire behavior that the shared hummbl-mcp-stdio dispatcher
must preserve when this shim migrates.
"""

from __future__ import annotations

import io
import json

import omnichannel_mcp_server as srv


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
    assert result["serverInfo"]["name"] == "omnichannel-governance-gate"
    assert result["capabilities"] == {"tools": {}}


def test_tools_list_declares_three_tools():
    res = _call("tools/list")
    names = [t["name"] for t in res["result"]["tools"]]
    assert names == [
        "omni_draft_message",
        "omni_broadcast_urgent",
        "omni_list_pending_drafts",
    ]


def test_unknown_method_returns_method_not_found():
    res = _call("bogus/method")
    assert res["error"]["code"] == -32601
    assert "Method not found" in res["error"]["message"]


def test_unknown_tool_returns_tool_not_found():
    res = _call("tools/call", {"name": "nope", "arguments": {}})
    assert res["error"]["code"] == -32601
    assert "Tool not found" in res["error"]["message"]


def test_list_pending_drafts_roundtrip():
    res = _call(
        "tools/call",
        {"name": "omni_list_pending_drafts", "arguments": {}},
    )
    assert res["result"]["content"][0]["type"] == "text"


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
    assert (
        out_lines[0]["result"]["serverInfo"]["name"]
        == "omnichannel-governance-gate"
    )
