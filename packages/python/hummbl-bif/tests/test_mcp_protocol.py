"""Tests for MCP JSON-RPC protocol handlers."""
import json
import io
import sys
import pytest
from unittest.mock import patch
from mcp_server import (
    send_response,
    send_error,
    _handle_initialize,
    _handle_tools_call,
    TOOLS,
    SERVER_NAME,
    SERVER_VERSION,
    PROTOCOL_VERSION,
)


def capture_response(fn, *args):
    """Capture stdout from an MCP handler function."""
    captured = io.StringIO()
    with patch("sys.stdout", captured):
        fn(*args)
    output = captured.getvalue().strip()
    return json.loads(output)


class TestMCPProtocol:
    def test_initialize_returns_protocol_version(self):
        response = capture_response(_handle_initialize, "test-id")
        assert response["result"]["protocolVersion"] == PROTOCOL_VERSION

    def test_initialize_returns_server_info(self):
        response = capture_response(_handle_initialize, "test-id")
        info = response["result"]["serverInfo"]
        assert info["name"] == SERVER_NAME
        assert info["version"] == SERVER_VERSION

    def test_initialize_response_has_correct_id(self):
        response = capture_response(_handle_initialize, "my-id-123")
        assert response["id"] == "my-id-123"

    def test_tools_list_returns_5_tools(self):
        assert len(TOOLS) == 5

    def test_tools_have_required_fields(self):
        required = {"name", "description", "inputSchema"}
        for tool in TOOLS:
            assert required.issubset(set(tool.keys())), f"Missing keys in {tool['name']}"

    def test_tools_call_start_session(self):
        response = capture_response(
            _handle_tools_call, "call-1",
            {"name": "bif_start_session", "arguments": {"domain": "TestDomain"}}
        )
        content = json.loads(response["result"]["content"][0]["text"])
        assert "session_id" in content

    def test_tools_call_get_template(self):
        response = capture_response(
            _handle_tools_call, "call-2",
            {"name": "bif_get_template", "arguments": {"phase": 1, "batch_number": 1}}
        )
        content = json.loads(response["result"]["content"][0]["text"])
        assert "batch_name" in content

    def test_tools_call_unknown_tool_returns_error_in_content(self):
        response = capture_response(
            _handle_tools_call, "call-3",
            {"name": "nonexistent_tool", "arguments": {}}
        )
        content = json.loads(response["result"]["content"][0]["text"])
        assert "error" in content

    def test_send_response_is_valid_jsonrpc(self):
        captured = io.StringIO()
        with patch("sys.stdout", captured):
            send_response("msg-1", {"key": "value"})
        msg = json.loads(captured.getvalue())
        assert msg["jsonrpc"] == "2.0"
        assert msg["id"] == "msg-1"
        assert msg["result"] == {"key": "value"}

    def test_send_error_is_valid_jsonrpc(self):
        captured = io.StringIO()
        with patch("sys.stdout", captured):
            send_error("msg-2", -32601, "Method not found")
        msg = json.loads(captured.getvalue())
        assert msg["jsonrpc"] == "2.0"
        assert msg["error"]["code"] == -32601
        assert msg["error"]["message"] == "Method not found"
