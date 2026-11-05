"""Minimal JSON-RPC stdio dispatcher for HUMMBL MCP shim servers.

Extracted from the hand-rolled loops duplicated across the
``hummbl-mcp-*`` shim packages. Each shim declares its tool list and a
``{tool_name: handler}`` mapping; this module owns the MCP protocol
plumbing (``initialize``, ``tools/list``, ``tools/call``), response
shaping, and the stdin read loop.
"""

from __future__ import annotations

import json
import sys
import traceback
from collections.abc import Callable
from typing import Any

PROTOCOL_VERSION = "2024-11-05"

Handler = Callable[[dict], dict]


def _result(req_id: Any, result: dict) -> dict:
    return {"jsonrpc": "2.0", "id": req_id, "result": result}


def _error(req_id: Any, code: int, message: str) -> dict:
    return {"jsonrpc": "2.0", "id": req_id, "error": {"code": code, "message": message}}


def _tool_error_result(exc: Exception) -> dict:
    return {
        "content": [
            {
                "type": "text",
                "text": json.dumps({"error": str(exc), "traceback": traceback.format_exc()}),
            }
        ]
    }


def handle_request(
    request: dict,
    *,
    server_name: str,
    server_version: str,
    tools: list[dict],
    handlers: dict[str, Handler],
) -> dict:
    """Dispatch one JSON-RPC request against the declared tool surface."""
    req_id = request.get("id")
    method = request.get("method")

    if method == "initialize":
        return _result(
            req_id,
            {
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": {"tools": {}},
                "serverInfo": {"name": server_name, "version": server_version},
            },
        )
    if method == "tools/list":
        return _result(req_id, {"tools": tools})
    if method == "tools/call":
        params = request.get("params", {})
        tool_name = params.get("name")
        args = params.get("arguments", {})
        handler = handlers.get(tool_name)
        if handler is None:
            return _error(req_id, -32601, f"Tool not found: {tool_name}")
        try:
            return _result(req_id, handler(args))
        except Exception as exc:  # noqa: BLE001 - protocol boundary: report, don't crash
            return _result(req_id, _tool_error_result(exc))
    return _error(req_id, -32601, f"Method not found: {method}")


def serve_stdio(
    *,
    server_name: str,
    server_version: str,
    tools: list[dict],
    handlers: dict[str, Handler],
    stdin=None,
    stdout=None,
) -> None:
    """Run the newline-delimited JSON-RPC loop until stdin closes.

    Malformed lines and handler crashes are swallowed per-line so one bad
    request cannot kill the server (matches existing shim behavior).
    """
    stdin = stdin if stdin is not None else sys.stdin
    stdout = stdout if stdout is not None else sys.stdout
    for line in stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
            res = handle_request(
                req,
                server_name=server_name,
                server_version=server_version,
                tools=tools,
                handlers=handlers,
            )
            stdout.write(json.dumps(res) + "\n")
            stdout.flush()
        except Exception:  # noqa: BLE001 - protocol boundary
            pass
