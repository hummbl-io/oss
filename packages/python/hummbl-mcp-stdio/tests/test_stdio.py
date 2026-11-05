"""Tests for the shared MCP stdio dispatcher."""

import io
import json

from hummbl_mcp_stdio import PROTOCOL_VERSION, handle_request, serve_stdio

TOOLS = [
    {
        "name": "echo",
        "description": "Echo args",
        "inputSchema": {"type": "object", "properties": {"msg": {"type": "string"}}},
    }
]


def _echo(args: dict) -> dict:
    return {"content": [{"type": "text", "text": args.get("msg", "")}]}


def _boom(args: dict) -> dict:
    raise RuntimeError("kaput")


HANDLERS = {"echo": _echo, "boom": _boom}
KW = dict(server_name="test-server", server_version="0.0.1", tools=TOOLS, handlers=HANDLERS)


def _req(method, params=None, req_id=1):
    r = {"jsonrpc": "2.0", "id": req_id, "method": method}
    if params is not None:
        r["params"] = params
    return r


class TestHandleRequest:
    def test_initialize(self):
        res = handle_request(_req("initialize"), **KW)
        assert res["result"]["protocolVersion"] == PROTOCOL_VERSION
        assert res["result"]["serverInfo"] == {"name": "test-server", "version": "0.0.1"}
        assert res["result"]["capabilities"] == {"tools": {}}

    def test_tools_list(self):
        res = handle_request(_req("tools/list"), **KW)
        assert res["result"]["tools"] == TOOLS

    def test_tools_call_success(self):
        res = handle_request(
            _req("tools/call", {"name": "echo", "arguments": {"msg": "hi"}}), **KW
        )
        assert res["result"]["content"][0]["text"] == "hi"

    def test_tools_call_unknown_tool(self):
        res = handle_request(_req("tools/call", {"name": "nope"}), **KW)
        assert res["error"]["code"] == -32601
        assert "Tool not found" in res["error"]["message"]

    def test_tools_call_handler_exception_returns_error_content(self):
        res = handle_request(_req("tools/call", {"name": "boom"}), **KW)
        payload = json.loads(res["result"]["content"][0]["text"])
        assert payload["error"] == "kaput"
        assert "RuntimeError" in payload["traceback"]

    def test_unknown_method(self):
        res = handle_request(_req("resources/list"), **KW)
        assert res["error"]["code"] == -32601


class TestServeStdio:
    def test_roundtrip_and_malformed_lines(self):
        stdin = io.StringIO(
            "not json\n"
            + json.dumps(_req("initialize", req_id=1))
            + "\n\n"
            + json.dumps(_req("tools/call", {"name": "echo", "arguments": {"msg": "yo"}}, req_id=2))
            + "\n"
        )
        stdout = io.StringIO()
        serve_stdio(stdin=stdin, stdout=stdout, **KW)
        lines = [json.loads(l) for l in stdout.getvalue().strip().splitlines()]
        assert len(lines) == 2
        assert lines[0]["result"]["serverInfo"]["name"] == "test-server"
        assert lines[1]["result"]["content"][0]["text"] == "yo"
