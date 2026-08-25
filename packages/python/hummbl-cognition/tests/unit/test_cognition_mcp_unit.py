"""Tests for the Cognitive Ledger MCP server."""
from hummbl_cognition.mcp_server import (
    PROTOCOL_VERSION,
    SERVER_NAME,
    SERVER_VERSION,
    TOOLS,
    handle_tool,
)


class TestConstants:
    def test_server_name(self):
        assert SERVER_NAME == "cognitive-ledger"

    def test_version(self):
        assert SERVER_VERSION == "0.1.0"

    def test_protocol(self):
        assert PROTOCOL_VERSION == "2024-11-05"

    def test_tools_count(self):
        assert len(TOOLS) >= 5


class TestHandleTool:
    def test_ledger_stats(self):
        result = handle_tool("ledger_stats", {})
        assert isinstance(result, dict)
        assert "total_entries" in result

    def test_ledger_search(self):
        result = handle_tool("ledger_search", {"query": "test", "limit": 5})
        assert isinstance(result, dict)

    def test_boot_context(self):
        result = handle_tool("boot_context", {})
        assert isinstance(result, dict)

    def test_unknown_tool(self):
        result = handle_tool("nonexistent", {})
        assert "error" in result
