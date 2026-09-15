"""Tests for MCP server argument validation — graceful errors instead of crashes."""

import json
import sys
from io import StringIO

import pytest

from hummbl_bus.mcp_server import handle_tool


class TestBusPostValidation:
    def test_empty_args_returns_error_not_crash(self):
        result = handle_tool("bus_post", {})
        assert "error" in result
        assert "type" in result["error"]

    def test_missing_message_returns_error(self):
        result = handle_tool("bus_post", {"type": "STATUS"})
        assert "error" in result
        assert "message" in result["error"]

    def test_missing_type_returns_error(self):
        result = handle_tool("bus_post", {"message": "hello"})
        assert "error" in result
        assert "type" in result["error"]

    @pytest.mark.parametrize("msg_type", ["DECISION", "DIRECTIVE", "decision"])
    def test_privileged_type_is_never_sent_or_locally_appended(self, msg_type):
        result = handle_tool(
            "bus_post",
            {"type": msg_type, "message": "host=anvil approve"},
        )
        assert result["posted"] is False
        assert "privileged" in result["error"]


class TestBusSearchValidation:
    def test_empty_args_returns_error_not_crash(self):
        result = handle_tool("bus_search", {})
        assert "error" in result
        assert "query" in result["error"]


class TestBusReadNoRequiredArgs:
    def test_empty_args_does_not_crash(self):
        # bus_read has no required args — should return a count
        result = handle_tool("bus_read", {})
        assert "count" in result
        assert "messages" in result


class TestUnknownTool:
    def test_unknown_tool_returns_error(self):
        result = handle_tool("nonexistent", {})
        assert "error" in result
