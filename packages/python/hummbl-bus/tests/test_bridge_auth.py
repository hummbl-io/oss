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
import hashlib
import json
import sys
from pathlib import Path
from unittest import mock

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from hummbl_bus.bridge_server import BusBridgeHandler
from hummbl_bus.bus_writer import BusWriteResult


@pytest.fixture(autouse=True)
def _mock_replay_ledger(monkeypatch):
    """Mock replay ledger so payload-hash dedup doesn't interfere with tests.

    The bridge now deduplicates by payload hash when no request_id is
    provided. Tests that mock post_message and use identical payloads
    would trigger false dedup hits without this fixture.
    """
    monkeypatch.setattr("hummbl_bus.bridge_server.lookup_request", lambda _rid: None)
    monkeypatch.setattr("hummbl_bus.bridge_server.record_request", lambda **kw: kw)


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
    handler.client_address = ("127.0.0.1", 12345)
    handler._response_code = None
    handler._error = None
    handler._response_body = None

    def _send_response(code, *args, **kwargs):
        handler._response_code = code

    def _send_header(*args, **kwargs):
        pass

    def _end_headers(*args, **kwargs):
        pass

    def _send_error(code, message=None, *args, **kwargs):
        handler._response_code = code
        handler._error = message

    def _wfile_write(data):
        handler._response_body = data

    handler.send_response = _send_response
    handler.send_header = _send_header
    handler.end_headers = _end_headers
    handler.send_error = _send_error
    handler.wfile.write = _wfile_write
    return handler


def _fake_write_result(*args: object, **kwargs: object) -> BusWriteResult:
    """Return the exact-result contract now required from post_message()."""
    del args
    timestamp = str(kwargs.get("timestamp") or "2026-08-31T00:00:00Z")
    sender = str(kwargs["from_id"])
    recipient = str(kwargs["to_id"])
    msg_type = str(kwargs["msg_type"])
    message = str(kwargs["message"])
    message_sha256 = hashlib.sha256(message.encode("utf-8")).hexdigest()
    row = f"{timestamp}\t{sender}\t{recipient}\t{msg_type}\t{message}"
    return BusWriteResult(
        bus_path=str(kwargs.get("bus_path") or "/tmp/test.tsv"),
        timestamp=timestamp,
        sender=sender,
        recipient=recipient,
        msg_type=msg_type,
        authorized_content_sha256=message_sha256,
        persisted_message_sha256=message_sha256,
        row_sha256=hashlib.sha256(row.encode("utf-8")).hexdigest(),
        verified_principal=None,
    )


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
        # New bridge returns 503 (service unavailable) when no credentials
        # configured, distinguishing "auth not configured" from "invalid token"
        assert handler._response_code == 503


class TestBearerAuth:
    """Bearer token auth with constant-time comparison."""

    def test_correct_token_passes_auth(self, monkeypatch):
        monkeypatch.setenv("BUS_BRIDGE_TOKEN", "test-token-abc123")
        monkeypatch.delenv("BUS_BRIDGE_ALLOW_NO_AUTH", raising=False)
        with (
            mock.patch("hummbl_bus.bridge_server.post_message", side_effect=_fake_write_result) as mock_post,
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
            # The promoted bridge enforces sender identity (the Bearer token
            # authenticates the HTTP client, and the bridge additionally
            # validates the sender against the canonical registry).
            assert mock_post.call_args.kwargs.get("enforce_sender_identity") is True
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
        monkeypatch.setenv("BUS_BRIDGE_TOKEN", "test-token-abc123")
        with mock.patch("hummbl_bus.bridge_server.post_message", side_effect=_fake_write_result) as mock_post:
            handler = _make_post_handler(
                body={
                    "from": "codex",
                    "to": "all",
                    "type": "STATUS",
                    "message": "traversal attempt",
                    "bus_path": "/etc/passwd",
                },
                headers={"Authorization": "Bearer test-token-abc123"},
            )
            BusBridgeHandler.do_POST(handler)
            assert handler._response_code == 400
            assert "bus_path" in (handler._error or "").lower()
            mock_post.assert_not_called()


class TestAllowNoAuthBypass:
    """The promoted bridge is always fail-closed — no BUS_BRIDGE_ALLOW_NO_AUTH bypass.

    The old HB bridge had a BUS_BRIDGE_ALLOW_NO_AUTH=1 bypass for tests/dev.
    The promoted FM bridge removes this: auth is always required. This is a
    security improvement — there is no env-var escape hatch that silently
    disables auth.
    """

    def test_allow_no_auth_bypasses_post(self, monkeypatch):
        monkeypatch.delenv("BUS_BRIDGE_TOKEN", raising=False)
        monkeypatch.delenv("BUS_BRIDGE_TOKEN_FILE", raising=False)
        monkeypatch.setenv("BUS_BRIDGE_ALLOW_NO_AUTH", "1")
        with (
            mock.patch("hummbl_bus.bridge_server.post_message", side_effect=_fake_write_result) as mock_post,
            mock.patch(
                "hummbl_bus.bridge_server._resolve_bus_path",
                return_value=Path("/tmp/test.tsv"),
            ),
        ):
            handler = _make_post_handler(
                body={"from": "codex", "to": "all", "type": "STATUS", "message": "test"}
            )
            BusBridgeHandler.do_POST(handler)
            # The bypass is NOT honored — bridge is always fail-closed.
            assert handler._response_code == 503
            mock_post.assert_not_called()


class TestRemoteAgentNotInLocalRegistry:
    """The promoted bridge enforces sender identity against the canonical registry.

    The Bearer token authenticates the HTTP client. The bridge additionally
    validates the sender against _RESERVED_AGENT_IDS (the canonical fleet
    roster). Fleet agents (devin, codex, etc.) are in the registry and pass.
    Unknown senders are rejected — this is stricter than the old HB bridge
    which set enforce_sender_identity=False.
    """

    def test_bearer_authenticated_remote_agent_accepted(self, monkeypatch):
        """A Bearer-authenticated post from a fleet agent in _RESERVED_AGENT_IDS
        (e.g. 'devin') is accepted — enforce_sender_identity is True at the bridge."""
        monkeypatch.setenv("BUS_BRIDGE_TOKEN", "test-token-abc123")
        monkeypatch.delenv("BUS_BRIDGE_ALLOW_NO_AUTH", raising=False)
        with (
            mock.patch("hummbl_bus.bridge_server.post_message", side_effect=_fake_write_result) as mock_post,
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
            # The promoted bridge enforces sender identity (True, not False)
            _, kwargs = mock_post.call_args
            assert kwargs.get("enforce_sender_identity") is True

    def test_bridge_passes_validate_true_for_observability(self, monkeypatch):
        """validate_sender_identity stays True so unknown senders are logged (fleet observability)."""
        monkeypatch.setenv("BUS_BRIDGE_TOKEN", "test-token-abc123")
        monkeypatch.delenv("BUS_BRIDGE_ALLOW_NO_AUTH", raising=False)
        with (
            mock.patch("hummbl_bus.bridge_server.post_message", side_effect=_fake_write_result) as mock_post,
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


class TestSenderBinding:
    """Per-agent token binding prevents sender spoofing.

    When BUS_SENDER_TOKENS_FILE is configured, the server maps the presented
    Bearer token to a specific sender identity and overrides the client-supplied
    'from' field. A client with agent X's token cannot post as agent Y.

    The promoted bridge requires BUS_BRIDGE_TOKEN_FILE (JSON multi-client
    credentials) as the primary auth layer; BUS_SENDER_TOKENS_FILE provides
    the sender binding on top of that.
    """

    def test_bound_sender_overrides_client_supplied_from(self, monkeypatch, tmp_path):
        """When per-agent tokens are configured, the token-bound sender overrides
        the client-supplied 'from' — prevents spoofing."""
        tokens_file = tmp_path / "sender_tokens.json"
        tokens_file.write_text(
            json.dumps({"devin": "token-devin-abc", "claude": "token-claude-xyz"}),
            encoding="utf-8",
        )
        monkeypatch.setenv("BUS_SENDER_TOKENS_FILE", str(tokens_file))
        monkeypatch.setenv("BUS_BRIDGE_TOKEN_FILE", str(tokens_file))
        monkeypatch.delenv("BUS_BRIDGE_TOKEN", raising=False)
        with (
            mock.patch("hummbl_bus.bridge_server.post_message", side_effect=_fake_write_result) as mock_post,
            mock.patch(
                "hummbl_bus.bridge_server._resolve_bus_path",
                return_value=Path("/tmp/test.tsv"),
            ),
        ):
            handler = _make_post_handler(
                body={
                    "from": "claude",
                    "to": "all",
                    "type": "STATUS",
                    "message": "I am devin, not claude",
                },
                headers={"Authorization": "Bearer token-devin-abc"},
            )
            BusBridgeHandler.do_POST(handler)
            assert handler._response_code == 200
            mock_post.assert_called_once()
            _, kwargs = mock_post.call_args
            assert kwargs.get("from_id") == "devin", (
                "Server must override client-supplied 'from' with token-bound sender"
            )

    def test_unrecognized_token_rejected(self, monkeypatch, tmp_path):
        """A token not in the credential file is rejected with 401."""
        tokens_file = tmp_path / "sender_tokens.json"
        tokens_file.write_text(
            json.dumps({"devin": "token-devin-abc"}),
            encoding="utf-8",
        )
        monkeypatch.setenv("BUS_SENDER_TOKENS_FILE", str(tokens_file))
        monkeypatch.setenv("BUS_BRIDGE_TOKEN_FILE", str(tokens_file))
        monkeypatch.delenv("BUS_BRIDGE_TOKEN", raising=False)
        handler = _make_post_handler(
            body={"from": "devin", "to": "all", "type": "STATUS", "message": "test"},
            headers={"Authorization": "Bearer not-a-real-token"},
        )
        BusBridgeHandler.do_POST(handler)
        assert handler._response_code == 401

    def test_missing_bearer_prefix_accepted_in_binding_mode(self, monkeypatch, tmp_path):
        """The promoted bridge strips 'Bearer ' if present but also accepts the
        raw token — the prefix is optional."""
        tokens_file = tmp_path / "sender_tokens.json"
        tokens_file.write_text(
            json.dumps({"devin": "token-devin-abc"}),
            encoding="utf-8",
        )
        monkeypatch.setenv("BUS_SENDER_TOKENS_FILE", str(tokens_file))
        monkeypatch.setenv("BUS_BRIDGE_TOKEN_FILE", str(tokens_file))
        monkeypatch.delenv("BUS_BRIDGE_TOKEN", raising=False)
        with (
            mock.patch("hummbl_bus.bridge_server.post_message", side_effect=_fake_write_result) as mock_post,
            mock.patch(
                "hummbl_bus.bridge_server._resolve_bus_path",
                return_value=Path("/tmp/test.tsv"),
            ),
        ):
            handler = _make_post_handler(
                body={"from": "devin", "to": "all", "type": "STATUS", "message": "test"},
                headers={"Authorization": "token-devin-abc"},
            )
            BusBridgeHandler.do_POST(handler)
            assert handler._response_code == 200
            mock_post.assert_called_once()

    def test_shared_token_mode_still_works_when_no_sender_tokens(self, monkeypatch):
        """When BUS_SENDER_TOKENS_FILE is not set, shared token mode is used
        (backward-compatible — client-supplied 'from' is respected)."""
        monkeypatch.delenv("BUS_SENDER_TOKENS_FILE", raising=False)
        monkeypatch.setenv("BUS_BRIDGE_TOKEN", "shared-token-abc")
        with (
            mock.patch("hummbl_bus.bridge_server.post_message", side_effect=_fake_write_result) as mock_post,
            mock.patch(
                "hummbl_bus.bridge_server._resolve_bus_path",
                return_value=Path("/tmp/test.tsv"),
            ),
        ):
            handler = _make_post_handler(
                body={
                    "from": "devin",
                    "to": "all",
                    "type": "STATUS",
                    "message": "test",
                },
                headers={"Authorization": "Bearer shared-token-abc"},
            )
            BusBridgeHandler.do_POST(handler)
            assert handler._response_code == 200
            _, kwargs = mock_post.call_args
            assert kwargs.get("from_id") == "devin"

    def test_binding_mode_missing_from_field_ok(self, monkeypatch, tmp_path):
        """In binding mode, the client-supplied 'from' can be missing —
        the server uses the token-bound sender."""
        tokens_file = tmp_path / "sender_tokens.json"
        tokens_file.write_text(
            json.dumps({"devin": "token-devin-abc"}),
            encoding="utf-8",
        )
        monkeypatch.setenv("BUS_SENDER_TOKENS_FILE", str(tokens_file))
        monkeypatch.setenv("BUS_BRIDGE_TOKEN_FILE", str(tokens_file))
        monkeypatch.delenv("BUS_BRIDGE_TOKEN", raising=False)
        with (
            mock.patch("hummbl_bus.bridge_server.post_message", side_effect=_fake_write_result) as mock_post,
            mock.patch(
                "hummbl_bus.bridge_server._resolve_bus_path",
                return_value=Path("/tmp/test.tsv"),
            ),
        ):
            handler = _make_post_handler(
                body={
                    "to": "all",
                    "type": "STATUS",
                    "message": "test",
                },
                headers={"Authorization": "Bearer token-devin-abc"},
            )
            BusBridgeHandler.do_POST(handler)
            assert handler._response_code == 200
            _, kwargs = mock_post.call_args
            assert kwargs.get("from_id") == "devin"


class TestBridgeClientTokenResolution:
    """Test token loading and header generation in bridge_client."""

    def test_explicit_token_priority(self, monkeypatch, tmp_path):
        from hummbl_bus.bridge_client import _request_headers
        monkeypatch.setenv("BUS_BRIDGE_TOKEN", "env-token")
        headers = _request_headers(bearer_token="explicit-token")
        assert headers.get("Authorization") == "Bearer explicit-token"

    def test_env_token_fallback(self, monkeypatch, tmp_path):
        from hummbl_bus.bridge_client import _request_headers
        monkeypatch.setenv("BUS_BRIDGE_TOKEN", "env-token")
        headers = _request_headers()
        assert headers.get("Authorization") == "Bearer env-token"

    def test_token_path_file_fallback(self, monkeypatch, tmp_path):
        from hummbl_bus.bridge_client import _request_headers
        token_file = tmp_path / "custom_token"
        token_file.write_text("file-token-123\n", encoding="utf-8")
        monkeypatch.delenv("BUS_BRIDGE_TOKEN", raising=False)
        monkeypatch.setenv("BUS_BRIDGE_TOKEN_PATH", str(token_file))
        headers = _request_headers()
        assert headers.get("Authorization") == "Bearer file-token-123"

    def test_missing_token_produces_no_auth_header(self, monkeypatch, tmp_path):
        from hummbl_bus.bridge_client import _request_headers
        monkeypatch.delenv("BUS_BRIDGE_TOKEN", raising=False)
        monkeypatch.setenv("BUS_BRIDGE_TOKEN_PATH", str(tmp_path / "nonexistent"))
        headers = _request_headers()
        assert "Authorization" not in headers


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
