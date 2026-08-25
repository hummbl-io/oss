"""Subprocess tests for the BIF MCP stdio server."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
SERVER = REPO_ROOT / "mcp_server.py"


def _request(process: subprocess.Popen, payload: dict) -> dict:
    assert process.stdin is not None
    assert process.stdout is not None
    process.stdin.write(json.dumps(payload) + "\n")
    process.stdin.flush()
    line = process.stdout.readline()
    assert line, "MCP server did not emit a response"
    return json.loads(line)


def test_mcp_server_starts_and_accepts_tool_invocation(tmp_path) -> None:
    env = {**os.environ, "BIF_SESSIONS_DIR": str(tmp_path / "sessions")}
    process = subprocess.Popen(
        [sys.executable, str(SERVER)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env,
    )
    try:
        initialize = _request(
            process,
            {"jsonrpc": "2.0", "id": "init-1", "method": "initialize", "params": {}},
        )
        assert initialize["result"]["serverInfo"]["name"] == "bif"

        tools = _request(
            process,
            {"jsonrpc": "2.0", "id": "tools-1", "method": "tools/list", "params": {}},
        )
        tool_names = {tool["name"] for tool in tools["result"]["tools"]}
        assert "bif_start_session" in tool_names

        call = _request(
            process,
            {
                "jsonrpc": "2.0",
                "id": "call-1",
                "method": "tools/call",
                "params": {
                    "name": "bif_start_session",
                    "arguments": {"domain": "MCP Test Domain"},
                },
            },
        )
        content = json.loads(call["result"]["content"][0]["text"])
        assert content["domain"] == "MCP Test Domain"
        assert (tmp_path / "sessions" / f"{content['session_id']}.json").exists()
    finally:
        process.terminate()
        process.wait(timeout=5)
