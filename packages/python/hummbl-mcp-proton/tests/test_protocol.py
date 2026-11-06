"""Protocol tests for the proton MCP shim's stdio JSON-RPC loop.

The shim writes responses directly via send_response/send_error, so these
tests drive main() over stdin/stdout — which also pins the newline framing
regression (responses must be newline-delimited JSON, not literal "\\n").
"""

from __future__ import annotations

import io
import json

import proton_mcp_server as srv


def _roundtrip(lines):
    stdout = io.StringIO()
    import sys
    from unittest.mock import patch

    with patch.object(sys, "stdin", io.StringIO("\n".join(lines) + "\n")), patch.object(
        sys, "stdout", stdout
    ):
        srv.main()
    return [json.loads(l) for l in stdout.getvalue().splitlines() if l.strip()]


def test_initialize_and_tools_list_roundtrip():
    out = _roundtrip(
        [
            json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize"}),
            json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/list"}),
        ]
    )
    assert [r["id"] for r in out] == [1, 2]
    assert out[0]["result"]["serverInfo"]["name"] == "proton"
    assert out[0]["result"]["protocolVersion"] == "2024-11-05"
    names = [t["name"] for t in out[1]["result"]["tools"]]
    assert "proton_mail_send" in names


def test_unknown_method_returns_method_not_found():
    out = _roundtrip(
        [json.dumps({"jsonrpc": "2.0", "id": 3, "method": "bogus/method"})]
    )
    assert out[0]["error"]["code"] == -32601
    assert "Method not found" in out[0]["error"]["message"]


def test_non_dict_json_lines_are_skipped():
    out = _roundtrip(
        [
            "123",
            "[1, 2]",
            json.dumps({"jsonrpc": "2.0", "id": 6, "method": "ping"}),
        ]
    )
    assert [r["id"] for r in out] == [6]


def test_bad_lines_do_not_crash_or_emit():
    out = _roundtrip(
        [
            "not json",
            "",
            json.dumps({"jsonrpc": "2.0", "id": 4, "method": "initialize"}),
        ]
    )
    assert [r["id"] for r in out] == [4]
