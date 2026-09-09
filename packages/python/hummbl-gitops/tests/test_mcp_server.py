"""Tests for the local stdio MCP server.

Tests the JSON-RPC protocol over stdio: initialize, tools/list, tools/call,
and error handling. Uses subprocess to simulate a real stdio session.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


def _send_mcp_request(proc: subprocess.Popen, request: dict) -> dict:
    """Send a JSON-RPC request to the MCP server and read the response."""
    line = json.dumps(request) + "\n"
    proc.stdin.write(line.encode())
    proc.stdin.flush()

    response_line = proc.stdout.readline()
    if not response_line:
        return {}
    return json.loads(response_line.decode())


def _start_mcp_server(tmp_path: Path) -> subprocess.Popen:
    """Start the MCP server subprocess with a temp state dir."""
    env = os.environ.copy()
    env["HUMMBL_GITOPS_STATE_DIR"] = str(tmp_path)
    # Use the venv python so hummbl_gitops is importable
    python_exe = sys.executable

    proc = subprocess.Popen(
        [python_exe, "-m", "hummbl_gitops.mcp_server"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
    )
    return proc


class TestMCPInitialize:
    """Test the MCP initialize handshake."""

    def test_initialize_returns_server_info(self, tmp_path: Path) -> None:
        proc = _start_mcp_server(tmp_path)
        try:
            response = _send_mcp_request(proc, {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
            })
            assert response["jsonrpc"] == "2.0"
            assert response["id"] == 1
            result = response["result"]
            assert result["serverInfo"]["name"] == "hummbl-gitops"
            assert result["serverInfo"]["version"] == "0.0.1"
            assert "tools" in result["capabilities"]
        finally:
            proc.stdin.close()
            proc.wait(timeout=5)

    def test_initialize_has_protocol_version(self, tmp_path: Path) -> None:
        proc = _start_mcp_server(tmp_path)
        try:
            response = _send_mcp_request(proc, {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "initialize",
            })
            assert "protocolVersion" in response["result"]
        finally:
            proc.stdin.close()
            proc.wait(timeout=5)


class TestMCPToolsList:
    """Test the tools/list method."""

    def test_lists_all_8_tools(self, tmp_path: Path) -> None:
        proc = _start_mcp_server(tmp_path)
        try:
            _send_mcp_request(proc, {"jsonrpc": "2.0", "id": 1, "method": "initialize"})
            response = _send_mcp_request(proc, {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/list",
            })
            tools = response["result"]["tools"]
            assert len(tools) == 8

            tool_names = {t["name"] for t in tools}
            expected = {
                "pre_push_check",
                "pre_pr_gate",
                "claim_review",
                "review_coverage",
                "watch_ci",
                "check_main_moved",
                "sync_receipts",
                "auto_rebase",
            }
            assert tool_names == expected
        finally:
            proc.stdin.close()
            proc.wait(timeout=5)

    def test_tools_have_input_schemas(self, tmp_path: Path) -> None:
        proc = _start_mcp_server(tmp_path)
        try:
            _send_mcp_request(proc, {"jsonrpc": "2.0", "id": 1, "method": "initialize"})
            response = _send_mcp_request(proc, {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/list",
            })
            for tool in response["result"]["tools"]:
                assert "inputSchema" in tool, f"Tool {tool['name']} missing inputSchema"
                assert tool["inputSchema"]["type"] == "object"
        finally:
            proc.stdin.close()
            proc.wait(timeout=5)


class TestMCPToolCall:
    """Test tools/call for specific tools."""

    def test_claim_review_valid_aspect(self, tmp_path: Path) -> None:
        proc = _start_mcp_server(tmp_path)
        try:
            _send_mcp_request(proc, {"jsonrpc": "2.0", "id": 1, "method": "initialize"})
            response = _send_mcp_request(proc, {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {
                    "name": "claim_review",
                    "arguments": {"pr": 500, "aspect": "security", "agent": "devin"},
                },
            })
            assert "result" in response
            text = response["result"]["content"][0]["text"]
            assert "pr=500" in text
            assert "aspect=security" in text
        finally:
            proc.stdin.close()
            proc.wait(timeout=5)

    def test_claim_review_invalid_aspect(self, tmp_path: Path) -> None:
        proc = _start_mcp_server(tmp_path)
        try:
            _send_mcp_request(proc, {"jsonrpc": "2.0", "id": 1, "method": "initialize"})
            response = _send_mcp_request(proc, {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {
                    "name": "claim_review",
                    "arguments": {"pr": 501, "aspect": "nonexistent"},
                },
            })
            assert response["result"].get("isError", False) is True
        finally:
            proc.stdin.close()
            proc.wait(timeout=5)

    def test_review_coverage_empty(self, tmp_path: Path) -> None:
        proc = _start_mcp_server(tmp_path)
        try:
            _send_mcp_request(proc, {"jsonrpc": "2.0", "id": 1, "method": "initialize"})
            response = _send_mcp_request(proc, {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {
                    "name": "review_coverage",
                    "arguments": {"pr": 600},
                },
            })
            text = response["result"]["content"][0]["text"]
            assert "No reviews recorded" in text
        finally:
            proc.stdin.close()
            proc.wait(timeout=5)

    def test_claim_then_coverage_roundtrip(self, tmp_path: Path) -> None:
        """Claim via MCP, then query coverage via MCP."""
        proc = _start_mcp_server(tmp_path)
        try:
            _send_mcp_request(proc, {"jsonrpc": "2.0", "id": 1, "method": "initialize"})

            # Claim
            _send_mcp_request(proc, {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {
                    "name": "claim_review",
                    "arguments": {"pr": 700, "aspect": "security", "agent": "devin"},
                },
            })

            # Query coverage
            response = _send_mcp_request(proc, {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {
                    "name": "review_coverage",
                    "arguments": {"pr": 700},
                },
            })
            text = response["result"]["content"][0]["text"]
            assert "security: devin" in text
        finally:
            proc.stdin.close()
            proc.wait(timeout=5)

    def test_unknown_tool_returns_error(self, tmp_path: Path) -> None:
        proc = _start_mcp_server(tmp_path)
        try:
            _send_mcp_request(proc, {"jsonrpc": "2.0", "id": 1, "method": "initialize"})
            response = _send_mcp_request(proc, {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {"name": "nonexistent_tool", "arguments": {}},
            })
            assert response["result"].get("isError", False) is True
        finally:
            proc.stdin.close()
            proc.wait(timeout=5)


class TestMCPErrorHandling:
    """Test protocol-level error handling."""

    def test_parse_error(self, tmp_path: Path) -> None:
        proc = _start_mcp_server(tmp_path)
        try:
            proc.stdin.write(b"not valid json\n")
            proc.stdin.flush()
            response_line = proc.stdout.readline()
            response = json.loads(response_line.decode())
            assert response["error"]["code"] == -32700
        finally:
            proc.stdin.close()
            proc.wait(timeout=5)

    def test_method_not_found(self, tmp_path: Path) -> None:
        proc = _start_mcp_server(tmp_path)
        try:
            _send_mcp_request(proc, {"jsonrpc": "2.0", "id": 1, "method": "initialize"})
            response = _send_mcp_request(proc, {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "nonexistent/method",
            })
            assert response["error"]["code"] == -32601
        finally:
            proc.stdin.close()
            proc.wait(timeout=5)

    def test_shutdown_terminates(self, tmp_path: Path) -> None:
        proc = _start_mcp_server(tmp_path)
        try:
            _send_mcp_request(proc, {"jsonrpc": "2.0", "id": 1, "method": "initialize"})
            _send_mcp_request(proc, {"jsonrpc": "2.0", "id": 2, "method": "shutdown"})
            proc.wait(timeout=5)
            assert proc.returncode == 0
        except subprocess.TimeoutExpired:
            proc.kill()
            pytest.fail("Server did not shut down within timeout")
