"""Tests for MCP Cognitive State server JSON-RPC handlers.

Depends on PR #470 (cognition/mcp_cognitive_state.py). These tests will
pass once that module lands on main. Expected to fail with ImportError
until then.
"""

import pytest

# Guard import — module may not exist yet (PR #470)
try:
    from hummbl_cognition.mcp_cognitive_state import handle_request

    _MODULE_AVAILABLE = True
except ImportError:
    _MODULE_AVAILABLE = False

pytestmark = pytest.mark.skipif(
    not _MODULE_AVAILABLE,
    reason="hummbl_cognition.mcp_cognitive_state not yet available (PR #470)",
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _req(method, params=None, req_id=1):
    return {"jsonrpc": "2.0", "id": req_id, "method": method, "params": params or {}}


# ---------------------------------------------------------------------------
# Initialize
# ---------------------------------------------------------------------------


class TestInitialize:
    def test_returns_server_info(self):
        resp = handle_request(_req("initialize"))
        assert resp is not None
        result = resp["result"]
        assert "serverInfo" in result
        assert "name" in result["serverInfo"]
        assert "version" in result["serverInfo"]


# ---------------------------------------------------------------------------
# Tools list
# ---------------------------------------------------------------------------


class TestToolsList:
    def test_returns_expected_tool_count(self):
        resp = handle_request(_req("tools/list"))
        tools = resp["result"]["tools"]
        assert len(tools) == 6

    def test_tool_names(self):
        resp = handle_request(_req("tools/list"))
        names = {t["name"] for t in resp["result"]["tools"]}
        expected = {
            "state_read",
            "state_update_agent",
            "state_claim_file",
            "state_release_file",
            "state_flags",
            "state_summary",
        }
        assert names == expected


# ---------------------------------------------------------------------------
# Tool calls — valid args
# ---------------------------------------------------------------------------


class TestToolCallsValid:
    def test_state_read_returns_content(self):
        resp = handle_request(
            _req("tools/call", {"name": "state_read", "arguments": {}})
        )
        assert resp is not None
        assert "content" in resp["result"]

    def test_state_summary_returns_content(self):
        resp = handle_request(
            _req("tools/call", {"name": "state_summary", "arguments": {}})
        )
        assert resp is not None
        assert "content" in resp["result"]

    def test_state_flags_returns_content(self):
        resp = handle_request(
            _req("tools/call", {"name": "state_flags", "arguments": {}})
        )
        assert resp is not None
        assert "content" in resp["result"]


# ---------------------------------------------------------------------------
# Tool calls — missing required args
# ---------------------------------------------------------------------------


class TestToolCallsMissingArgs:
    def test_unknown_tool_returns_error(self):
        resp = handle_request(
            _req("tools/call", {"name": "nonexistent_tool", "arguments": {}})
        )
        assert resp is not None
        result = resp["result"]
        assert result.get("isError") is True


# ---------------------------------------------------------------------------
# Notifications
# ---------------------------------------------------------------------------


class TestNotifications:
    def test_initialized_notification_returns_none(self):
        resp = handle_request({"jsonrpc": "2.0", "method": "notifications/initialized"})
        assert resp is None

    def test_cancelled_notification_returns_none(self):
        resp = handle_request({"jsonrpc": "2.0", "method": "notifications/cancelled"})
        assert resp is None
