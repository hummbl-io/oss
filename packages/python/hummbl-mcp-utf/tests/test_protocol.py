"""Protocol tests for the UTF MCP shim's stdio JSON-RPC loop.

The shim writes responses directly via send_response/send_error, so these
tests drive main() over stdin/stdout — pinning the newline-delimited
framing the shared hummbl-mcp-stdio dispatcher must preserve.
"""

from __future__ import annotations

import io
import json
import sys
from unittest.mock import patch

import utf_mcp_server as srv


def _roundtrip(lines):
    stdout = io.StringIO()
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
    assert out[0]["result"]["serverInfo"]["name"] == "hummbl-tier-framework"
    assert out[0]["result"]["protocolVersion"] == "2024-11-05"
    assert len(out[1]["result"]["tools"]) > 0


def test_ping_returns_empty_result():
    out = _roundtrip([json.dumps({"jsonrpc": "2.0", "id": 3, "method": "ping"})])
    assert out[0]["id"] == 3
    assert out[0]["result"] == {}


def test_unknown_method_returns_method_not_found():
    out = _roundtrip(
        [json.dumps({"jsonrpc": "2.0", "id": 4, "method": "bogus/method"})]
    )
    assert out[0]["error"]["code"] == -32601
    assert "Method not found" in out[0]["error"]["message"]


def test_bad_lines_do_not_crash_or_emit():
    out = _roundtrip(
        [
            "not json",
            "",
            json.dumps({"jsonrpc": "2.0", "id": 5, "method": "initialize"}),
        ]
    )
    assert [r["id"] for r in out] == [5]
