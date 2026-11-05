"""Protocol tests for the voice MCP shim's JSON-RPC handling.

These pin the wire behavior that the shared hummbl-mcp-stdio dispatcher
must preserve when this shim migrates.
"""

from __future__ import annotations

import io
import json
from unittest.mock import patch

import voice_mcp_server as srv


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
    assert result["serverInfo"] == {"name": "hummbl-mcp-voice", "version": "0.1.0"}
    assert result["capabilities"] == {"tools": {}}


def test_tools_list_declares_three_tools():
    res = _call("tools/list")
    names = [t["name"] for t in res["result"]["tools"]]
    assert names == [
        "voice_dispatch_call",
        "voice_retrieve_call_logs",
        "voice_download_recording",
    ]


def test_unknown_method_returns_method_not_found():
    res = _call("bogus/method")
    assert res["error"]["code"] == -32601
    assert "Method not found" in res["error"]["message"]


def test_unknown_tool_returns_tool_not_found():
    res = _call("tools/call", {"name": "nope", "arguments": {}})
    assert res["error"]["code"] == -32601
    assert "Tool not found" in res["error"]["message"]


def test_tool_error_becomes_error_content():
    with patch.object(
        srv, "tool_voice_dispatch_call", side_effect=RuntimeError("api down")
    ):
        res = _call(
            "tools/call",
            {
                "name": "voice_dispatch_call",
                "arguments": {"phone_number": "+1", "assistant_id": "a1"},
            },
        )
    payload = json.loads(res["result"]["content"][0]["text"])
    assert "api down" in payload["error"]
    assert "traceback" in payload


def test_missing_tool_args_returns_error_content():
    res = _call(
        "tools/call",
        {"name": "voice_dispatch_call", "arguments": {}},
    )
    payload = json.loads(res["result"]["content"][0]["text"])
    assert "required" in payload["error"]


def test_non_dict_request_returns_invalid_request():
    res = srv.handle_request(["not", "a", "dict"])
    assert res["error"]["code"] == -32600


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
