"""Tests for hummbl-bus bridge server auth hardening (S-001/S-002/S-003 P0 fixes).

Covers:
- Bearer token auth (fail-closed when BUS_BRIDGE_TOKEN not configured)
- Constant-time comparison (hmac.compare_digest)
- Client-supplied bus_path rejected (S-003 path traversal fix)
- Sender identity enforcement default True for local callers (S-001 fix)
- Bridge sets enforce_sender_identity=False (Bearer authenticates the client;
  sender identity is metadata — avoids coupling to local registry)
- BUS_BRIDGE_ALLOW_NO_AUTH=1 bypass for tests/dev
- Remote agents not in local registry accepted when Bearer-authenticated
"""

from __future__ import annotations

import io
import json
import sys
from pathlib import Path
from unittest import mock

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from hummbl_bus.bridge_server import BusBridgeHandler


def _make_post_handler(
    *, body: dict[str, object], path: str = "/bus", headers: dict | None = None
):
    """Construct a BusBridgeHandler with a fake POST request."""
    encoded = json.dumps(body).encode("utf-8")
    all_headers = {"Content-Length": str(len(encoded))}
    if headers:
        all_headers.update(headers)

    handler = object.__new__(BusBridgeHandler)
    handler.path = path
    handler.headers = all_headers
    handler.rfile = io.BytesIO(encoded)
    handler.wfile = io.BytesIO()
    handler._response_code = None
    handler._error = None

    def _send_response(code, *args, **kwargs):
        handler._response_code = code

    def _send_header(*args, **kwargs):
        pass

    def _end_headers(*args, **kwargs):
        pass

    def _send_error(code, message=None, *args, **kwargs):
        handler._response_code = code
        handler._error = message

    handler.send_response = _send_response
    handler.send_header = _send_header
    handler.end_headers = _end_headers
    handler.send_error = _send_error
    return handler


class TestFailClosedDefault:
    """P0 fix (S-002): bridge must fail-closed when token not configured."""

    def test_post_rejected_when_token_not_configured(self, monkeypatch):
        monkeypatch.delenv("BUS_BRIDGE_TOKEN", raising=False)
        monkeypatch.delenv("BUS_BRIDGE_TOKEN_FILE", raising=False)
        monkeypatch.delenv("BUS_BRIDGE_ALLOW_NO_AUTH", raising=False)
        handler = _make_post_handler(
            body={"from": "codex", "to": "all", "type": "STATUS", "message": "test"}
        )
        BusBridgeHandler.do_POST(handler)
        assert handler._response_code == 401


class TestBearerAuth:
    """Bearer token auth with constant-time comparison."""

    def test_correct_token_passes_auth(self, monkeypatch):
        monkeypatch.setenv("BUS_BRIDGE_TOKEN", "test-token-abc123")
        monkeypatch.delenv("BUS_BRIDGE_ALLOW_NO_AUTH", raising=False)
        with (
            mock.patch("hummbl_bus.bridge_server.post_message") as mock_post,
            mock.patch(
                "hummbl_bus.bridge_server._resolve_bus_path",
                return_value=Path("/tmp/test.tsv"),
            ),
        ):
            handler = _make_post_handler(
                body={
                    "from": "codex",
                    "to": "all",
                    "type": "STATUS",
                    "message": "test",
                },
                headers={"Authorization": "Bearer test-token-abc123"},
            )
            BusBridgeHandler.do_POST(handler)
            assert handler._response_code == 200
            mock_post.assert_called_once()
            # S-001 fix: the DEFAULT for enforce_sender_identity is True
            # (production-safe). The bridge explicitly sets it to False
            # because the Bearer token authenticates the HTTP client and the
            # sender identity is metadata the authenticated client vouches
            # for. See TestRemoteAgentNotInLocalRegistry for the rationale.
            assert mock_post.call_args.kwargs.get("enforce_sender_identity") is False
            assert mock_post.call_args.kwargs.get("validate_sender_identity") is True

    def test_wrong_token_rejected(self, monkeypatch):
        monkeypatch.setenv("BUS_BRIDGE_TOKEN", "test-token-abc123")
        monkeypatch.delenv("BUS_BRIDGE_ALLOW_NO_AUTH", raising=False)
        handler = _make_post_handler(
            body={"from": "codex", "to": "all", "type": "STATUS", "message": "test"},
            headers={"Authorization": "Bearer wrong-token"},
        )
        BusBridgeHandler.do_POST(handler)
        assert handler._response_code == 401

    def test_missing_authorization_header_rejected(self, monkeypatch):
        monkeypatch.setenv("BUS_BRIDGE_TOKEN", "test-token-abc123")
        monkeypatch.delenv("BUS_BRIDGE_ALLOW_NO_AUTH", raising=False)
        handler = _make_post_handler(
            body={"from": "codex", "to": "all", "type": "STATUS", "message": "test"}
        )
        BusBridgeHandler.do_POST(handler)
        assert handler._response_code == 401

    def test_compare_digest_used_for_auth(self):
        """Structural guard: hmac.compare_digest must be used."""
        src = (
            Path(__file__).resolve().parent.parent
            / "src"
            / "hummbl_bus"
            / "bridge_server.py"
        )
        text = src.read_text(encoding="utf-8")
        assert "hmac.compare_digest" in text, (
            "bridge_server must use hmac.compare_digest for auth"
        )


class TestPathTraversalRejected:
    """P0 fix (S-003): client-supplied bus_path must be rejected."""

    def test_client_supplied_bus_path_rejected(self, monkeypatch):
        monkeypatch.setenv("BUS_BRIDGE_ALLOW_NO_AUTH", "1")
        with mock.patch("hummbl_bus.bridge_server.post_message") as mock_post:
            handler = _make_post_handler(
                body={
                    "from": "codex",
                    "to": "all",
                    "type": "STATUS",
                    "message": "traversal attempt",
                    "bus_path": "/etc/passwd",
                }
            )
            BusBridgeHandler.do_POST(handler)
            assert handler._response_code == 400
            assert "bus_path" in (handler._error or "")
            mock_post.assert_not_called()


class TestAllowNoAuthBypass:
    """BUS_BRIDGE_ALLOW_NO_AUTH=1 bypasses fail-closed for tests/dev."""

    def test_allow_no_auth_bypasses_post(self, monkeypatch):
        monkeypatch.delenv("BUS_BRIDGE_TOKEN", raising=False)
        monkeypatch.delenv("BUS_BRIDGE_TOKEN_FILE", raising=False)
        monkeypatch.setenv("BUS_BRIDGE_ALLOW_NO_AUTH", "1")
        with (
            mock.patch("hummbl_bus.bridge_server.post_message") as mock_post,
            mock.patch(
                "hummbl_bus.bridge_server._resolve_bus_path",
                return_value=Path("/tmp/test.tsv"),
            ),
        ):
            handler = _make_post_handler(
                body={"from": "codex", "to": "all", "type": "STATUS", "message": "test"}
            )
            BusBridgeHandler.do_POST(handler)
            assert handler._response_code == 200
            mock_post.assert_called_once()


class TestRemoteAgentNotInLocalRegistry:
    """Peer-review fix (BUS-ENFORCE-REGRESSION): bridge must accept
    Bearer-authenticated posts from fleet agents not in the local registry.

    The Bearer token authenticates the HTTP client. The sender identity in
    the message body is metadata the authenticated client vouches for.
    enforce_sender_identity=False at the bridge prevents coupling to the
    local registry/agents_v2.json (which may not list devin, opencode,
    apex, sov, kai, echo, soma, nexus, auditor, hermes, human).
    """

    def test_bearer_authenticated_remote_agent_accepted(self, monkeypatch):
        """A Bearer-authenticated post from a fleet agent not in _RESERVED_AGENT_IDS
        (e.g. 'devin') is accepted — enforce_sender_identity is False at the bridge."""
        monkeypatch.setenv("BUS_BRIDGE_TOKEN", "test-token-abc123")
        monkeypatch.delenv("BUS_BRIDGE_ALLOW_NO_AUTH", raising=False)
        with (
            mock.patch("hummbl_bus.bridge_server.post_message") as mock_post,
            mock.patch(
                "hummbl_bus.bridge_server._resolve_bus_path",
                return_value=Path("/tmp/test.tsv"),
            ),
        ):
            handler = _make_post_handler(
                body={
                    "from": "devin",
                    "to": "operator",
                    "type": "STATUS",
                    "message": "remote post",
                },
                headers={"Authorization": "Bearer test-token-abc123"},
            )
            BusBridgeHandler.do_POST(handler)
            assert handler._response_code == 200, (
                f"expected 200, got {handler._response_code} err={handler._error}"
            )
            mock_post.assert_called_once()
            # Verify enforce_sender_identity=False was passed (the fix)
            _, kwargs = mock_post.call_args
            assert kwargs.get("enforce_sender_identity") is False

    def test_bridge_passes_validate_true_for_observability(self, monkeypatch):
        """validate_sender_identity stays True so unknown senders are logged (fleet observability)."""
        monkeypatch.setenv("BUS_BRIDGE_TOKEN", "test-token-abc123")
        monkeypatch.delenv("BUS_BRIDGE_ALLOW_NO_AUTH", raising=False)
        with (
            mock.patch("hummbl_bus.bridge_server.post_message") as mock_post,
            mock.patch(
                "hummbl_bus.bridge_server._resolve_bus_path",
                return_value=Path("/tmp/test.tsv"),
            ),
        ):
            handler = _make_post_handler(
                body={
                    "from": "devin",
                    "to": "operator",
                    "type": "STATUS",
                    "message": "remote post",
                },
                headers={"Authorization": "Bearer test-token-abc123"},
            )
            BusBridgeHandler.do_POST(handler)
            assert handler._response_code == 200
            _, kwargs = mock_post.call_args
            assert kwargs.get("validate_sender_identity") is True


class TestReservedAgentIdsRegistry:
    """B4 fix: _RESERVED_AGENT_IDS must include all approved fleet agents
    from agent-roster.md so local callers with enforce_sender_identity=True
    (the default) don't crash with ValueError."""

    def test_all_approved_fleet_agents_in_reserved_ids(self):
        """All approved fleet agents from agent-roster.md are in
        _RESERVED_AGENT_IDS — local callers with enforce_sender_identity=True
        must succeed."""
        from hummbl_bus.bus_writer import _RESERVED_AGENT_IDS

        roster_agents = [
            "claude-code",
            "codex",
            "apex",
            "agy",
            "sov",
            "kai",
            "echo",
            "soma",
            "human",
            "devin",
            "opencode",
            "nexus",
            "auditor",
            "hermes",
        ]
        for agent in roster_agents:
            assert agent in _RESERVED_AGENT_IDS, (
                f"Agent '{agent}' from agent-roster.md is missing from "
                f"_RESERVED_AGENT_IDS — local callers with enforce_sender_identity=True "
                f"will crash with ValueError (B4 regression)"
            )

    def test_unknown_identity_rejected_by_default(self):
        """Unknown identity not in _RESERVED_AGENT_IDS is rejected when
        enforce_sender_identity=True (the fail-closed default)."""
        from hummbl_bus.bus_writer import _RESERVED_AGENT_IDS

        assert "evil-attacker" not in _RESERVED_AGENT_IDS
        assert "not-a-real-agent" not in _RESERVED_AGENT_IDS

    def test_gemini_cli_not_approved_sender(self):
        """gemini-cli is SUPERSEDED by agy (2026-06-25). It must NOT be
        in _RESERVED_AGENT_IDS as a current terminal sender. Historical
        compatibility is preserved via the 'gemini' model-only entry."""
        from hummbl_bus.bus_writer import _RESERVED_AGENT_IDS

        assert "gemini-cli" not in _RESERVED_AGENT_IDS, (
            "gemini-cli is SUPERSEDED by agy — must not be approved as current terminal sender"
        )

    def test_agy_accepted_gemini_not_interchangeable(self):
        """agy is the admitted executing surface. gemini is model-only.
        Using a Gemini model through agy does not imply sender identity 'gemini'.
        Both agy and gemini are in the registry (agy as approved sender,
        gemini as conditional model-only sender) but they are NOT interchangeable."""
        from hummbl_bus.bus_writer import _RESERVED_AGENT_IDS

        assert "agy" in _RESERVED_AGENT_IDS, (
            "agy must be approved as current terminal sender"
        )
        # gemini remains in registry as model-only/conditional sender, but agy is the
        # canonical surface when using Gemini models via Antigravity CLI
        assert "gemini" in _RESERVED_AGENT_IDS, (
            "gemini remains as conditional model-only sender"
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
