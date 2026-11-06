"""Protocol tests for the 1Password MCP shim's JSON-RPC dispatch.

Pins the wire behavior that the shared hummbl-mcp-stdio dispatcher
must preserve when this shim migrates.
"""

from __future__ import annotations

import io
import json

from onepassword_mcp_server import OnePasswordServer


def _dispatch(req):
    return OnePasswordServer().dispatch(req)


def test_initialize_returns_server_info():
    res = _dispatch({"jsonrpc": "2.0", "id": 1, "method": "initialize"})
    assert res["jsonrpc"] == "2.0"
    assert res["id"] == 1
    result = res["result"]
    assert result["protocolVersion"] == "2024-11-05"
    assert result["serverInfo"] == {"name": "onepassword-mcp", "version": "1.0.0"}
    assert result["capabilities"] == {"tools": {}}


def test_tools_list_declares_five_tools():
    res = _dispatch({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
    names = [t["name"] for t in res["result"]["tools"]]
    assert names == [
        "onepassword_get",
        "onepassword_list",
        "onepassword_vaults",
        "onepassword_fields",
        "onepassword_resolve",
    ]


def test_unknown_method_returns_method_not_found():
    res = _dispatch({"jsonrpc": "2.0", "id": 3, "method": "bogus/method"})
    assert res["error"]["code"] == -32601
    assert "Method not found" in res["error"]["message"]


def test_unknown_tool_returns_error_result():
    res = _dispatch(
        {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "tools/call",
            "params": {"name": "nope", "arguments": {}},
        }
    )
    assert res["result"]["isError"] is True


def test_notification_returns_none():
    assert (
        _dispatch({"jsonrpc": "2.0", "method": "notifications/initialized"})
        is None
    )


def test_run_roundtrip_parse_error_and_bad_lines():
    srv = OnePasswordServer()
    inp = io.StringIO(
        "\n".join(
            [
                json.dumps({"jsonrpc": "2.0", "id": 7, "method": "initialize"}),
                "not json",
                "",
                json.dumps({"jsonrpc": "2.0", "id": 8, "method": "tools/list"}),
            ]
        )
        + "\n"
    )
    out = io.StringIO()
    srv.run(stdin=inp, stdout=out)
    out_lines = [json.loads(l) for l in out.getvalue().splitlines() if l.strip()]
    # initialize (7), parse-error response (id null), tools/list (8)
    assert [r.get("id") for r in out_lines] == [7, None, 8]
    assert out_lines[0]["result"]["serverInfo"]["name"] == "onepassword-mcp"
