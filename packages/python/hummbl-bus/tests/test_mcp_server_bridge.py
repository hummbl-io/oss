from __future__ import annotations

import json
from unittest.mock import patch

import pytest

from hummbl_bus.mcp_server import handle_tool


def _ok_bridge_response(body: bytes = b'{"status":"ok"}') -> object:
    """Build a fake HTTPResponse-like context manager for urllib.open."""

    class _FakeResp:
        def __init__(self, body: bytes) -> None:
            self._body = body
            self.status = 200

        def read(self) -> bytes:
            return self._body

        def __enter__(self) -> _FakeResp:
            return self

        def __exit__(self, *args: object) -> None:
            pass

    return _FakeResp(body)


def test_bus_post_uses_bridge_first(monkeypatch: pytest.MonkeyPatch) -> None:
    """bus_post must call the HTTP bridge, not the local file."""
    monkeypatch.setenv("BUS_BRIDGE_TOKEN", "test-token")
    monkeypatch.delenv("BUS_FILE", raising=False)

    captured: dict[str, object] = {}

    def fake_open(request, timeout=None):
        captured["url"] = request.full_url
        captured["headers"] = dict(request.header_items())
        captured["data"] = json.loads(request.data.decode("utf-8"))
        return _ok_bridge_response()

    with patch("hummbl_bus.mcp_server.HTTP_OPENER") as mock_opener:
        mock_opener.open.side_effect = fake_open
        result = handle_tool("bus_post", {
            "from_agent": "devin",
            "to": "all",
            "type": "STATUS",
            "message": "bridge-path-test marker=regression-bridge",
        })

    assert result["posted"] is True
    assert result["method"] == "bridge"
    assert captured["url"].endswith("/bus")
    assert captured["data"]["from"] == "devin"
    assert captured["data"]["to"] == "all"
    assert captured["data"]["type"] == "STATUS"
    # bus_post auto-prepends host=<machine> to the message body per
    # bus-protocol.md §75; the original payload follows the tag.
    assert captured["data"]["message"].startswith("host=")
    assert captured["data"]["message"].endswith("bridge-path-test marker=regression-bridge")
    assert "origin_machine" in captured["data"]
    assert "request_id" in captured["data"]


def test_bus_post_injects_host_tag(monkeypatch: pytest.MonkeyPatch) -> None:
    """Agent-originated posts must carry host=<machine> in the body (bus-protocol.md §75).
    The MCP server auto-injects it so the bridge doesn't 400 on a missing tag."""
    monkeypatch.setenv("BUS_BRIDGE_TOKEN", "test-token")
    monkeypatch.setenv("BUS_ORIGIN_MACHINE", "anvil")
    monkeypatch.delenv("BUS_FILE", raising=False)

    captured: dict[str, object] = {}

    def fake_open(request, timeout=None):
        captured["data"] = json.loads(request.data.decode("utf-8"))
        return _ok_bridge_response()

    with patch("hummbl_bus.mcp_server.HTTP_OPENER") as mock_opener:
        mock_opener.open.side_effect = fake_open
        result = handle_tool("bus_post", {
            "from_agent": "devin",
            "to": "claude-code",
            "type": "PROPOSAL",
            "message": "review please",
        })

    assert result["posted"] is True
    assert captured["data"]["message"] == "host=anvil review please"


def test_bus_post_preserves_caller_supplied_host_tag(monkeypatch: pytest.MonkeyPatch) -> None:
    """If the caller already supplied host=, the server must not double-inject."""
    monkeypatch.setenv("BUS_BRIDGE_TOKEN", "test-token")
    monkeypatch.setenv("BUS_ORIGIN_MACHINE", "anvil")
    monkeypatch.delenv("BUS_FILE", raising=False)

    captured: dict[str, object] = {}

    def fake_open(request, timeout=None):
        captured["data"] = json.loads(request.data.decode("utf-8"))
        return _ok_bridge_response()

    with patch("hummbl_bus.mcp_server.HTTP_OPENER") as mock_opener:
        mock_opener.open.side_effect = fake_open
        handle_tool("bus_post", {
            "from_agent": "devin",
            "type": "STATUS",
            "message": "host=delta status from delta",
        })

    assert captured["data"]["message"] == "host=delta status from delta"


def test_bus_post_host_tag_lowercases_and_falls_back_to_unknown(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Windows gethostname() returns uppercase (ANVIL); non-canonical names fall back to 'unknown'."""
    monkeypatch.setenv("BUS_BRIDGE_TOKEN", "test-token")
    monkeypatch.setenv("BUS_ORIGIN_MACHINE", "ANVIL")
    monkeypatch.delenv("BUS_FILE", raising=False)

    captured: dict[str, object] = {}

    def fake_open(request, timeout=None):
        captured["data"] = json.loads(request.data.decode("utf-8"))
        return _ok_bridge_response()

    with patch("hummbl_bus.mcp_server.HTTP_OPENER") as mock_opener:
        mock_opener.open.side_effect = fake_open
        handle_tool("bus_post", {
            "from_agent": "devin",
            "type": "STATUS",
            "message": "uppercase host test",
        })

    assert captured["data"]["message"] == "host=anvil uppercase host test"

    # Non-canonical hostname -> "unknown" (still accepted by the bridge).
    monkeypatch.setenv("BUS_ORIGIN_MACHINE", "random-laptop-42")
    captured.clear()

    with patch("hummbl_bus.mcp_server.HTTP_OPENER") as mock_opener:
        mock_opener.open.side_effect = fake_open
        handle_tool("bus_post", {
            "from_agent": "devin",
            "type": "STATUS",
            "message": "noncanonical host test",
        })

    assert captured["data"]["message"] == "host=unknown noncanonical host test"


def test_bus_post_returns_false_when_bridge_fails_no_fallback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Bridge failure with no explicit BUS_FILE must return posted:false, not
    silently write to the package-relative default."""
    monkeypatch.setenv("BUS_BRIDGE_TOKEN", "test-token")
    monkeypatch.delenv("BUS_FILE", raising=False)

    import urllib.error

    def fake_open(request, timeout=None):
        raise urllib.error.URLError("connection refused")

    with patch("hummbl_bus.mcp_server.HTTP_OPENER") as mock_opener:
        mock_opener.open.side_effect = fake_open
        result = handle_tool("bus_post", {
            "type": "STATUS",
            "message": "no-fallback-test",
        })

    assert result["posted"] is False
    assert "error" in result
    assert "BUS_FILE not set" in result["error"]


def test_bus_post_falls_back_to_local_when_bus_file_set(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: pytest.TempPathFactory,
) -> None:
    """Bridge failure with explicit BUS_FILE must fall back to local write."""
    monkeypatch.setenv("BUS_BRIDGE_TOKEN", "test-token")
    bus_file = tmp_path / "fallback" / "messages.tsv"
    monkeypatch.setenv("BUS_FILE", str(bus_file))

    import urllib.error

    def fake_open(request, timeout=None):
        raise urllib.error.URLError("bridge down")

    with patch("hummbl_bus.mcp_server.HTTP_OPENER") as mock_opener:
        mock_opener.open.side_effect = fake_open
        result = handle_tool("bus_post", {
            "from_agent": "devin",
            "to": "all",
            "type": "STATUS",
            "message": "fallback-test marker=regression-fallback",
        })

    assert result["posted"] is True
    assert result["method"] in ("local_fallback", "direct_append")
    assert "warning" in result
    assert bus_file.exists()
    content = bus_file.read_text(encoding="utf-8")
    assert "fallback-test marker=regression-fallback" in content


def test_bus_post_missing_token_returns_false(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """No bridge token and no BUS_FILE must return posted:false."""
    monkeypatch.delenv("BUS_BRIDGE_TOKEN", raising=False)
    monkeypatch.delenv("BUS_BRIDGE_TOKEN_PATH", raising=False)
    monkeypatch.delenv("BUS_FILE", raising=False)

    with patch("hummbl_bus.mcp_server._load_bridge_token", return_value=None):
        result = handle_tool("bus_post", {
            "type": "STATUS",
            "message": "no-token-test",
        })

    assert result["posted"] is False
    assert "error" in result
    assert "missing BUS_BRIDGE_TOKEN" in result["error"]
