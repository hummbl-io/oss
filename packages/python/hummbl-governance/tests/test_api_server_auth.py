"""Tests for hummbl-governance API server auth hardening (STD-004 P0 fix).

Covers:
- Bearer token auth (fail-closed when GOVERNANCE_API_TOKEN not configured)
- Constant-time comparison (hmac.compare_digest)
- CORS origin is opt-in (no wildcard by default)
- Kill switch disengage requires confirm=true (matches engage gate)
- GOVERNANCE_API_ALLOW_NO_AUTH=1 bypass for tests/dev
"""

from __future__ import annotations

import io
import json
import sys
from pathlib import Path
from unittest import mock

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import api_server


def _make_handler(
    method: str = "GET",
    path: str = "/api/v1/status",
    body: dict | None = None,
    headers: dict | None = None,
):
    """Construct a GovernanceHandler with a fake request (no real socket)."""
    handler = object.__new__(api_server.GovernanceHandler)
    handler.path = path
    handler.command = method
    handler.headers = headers or {}
    handler._response_code = None
    handler._response_body = None

    if body is not None:
        encoded = json.dumps(body).encode("utf-8")
        handler.headers = {**handler.headers, "Content-Length": str(len(encoded))}
        handler.rfile = io.BytesIO(encoded)
    else:
        handler.rfile = io.BytesIO()
    handler.wfile = io.BytesIO()

    def _send_response(code, *args, **kwargs):
        handler._response_code = code

    def _send_header(*args, **kwargs):
        pass

    def _end_headers(*args, **kwargs):
        pass

    handler.send_response = _send_response
    handler.send_header = _send_header
    handler.end_headers = _end_headers
    return handler


def _read_response(handler):
    body = handler.wfile.getvalue().decode("utf-8")
    return json.loads(body) if body else {}


class TestFailClosedDefault:
    """P0 fix: API server must fail-closed when token not configured."""

    def test_get_rejected_when_token_not_configured(self, monkeypatch):
        monkeypatch.delenv("GOVERNANCE_API_TOKEN", raising=False)
        monkeypatch.delenv("GOVERNANCE_API_TOKEN_FILE", raising=False)
        monkeypatch.delenv("GOVERNANCE_API_ALLOW_NO_AUTH", raising=False)
        monkeypatch.setattr(api_server, "_ks", mock.MagicMock())
        handler = _make_handler("GET", "/api/v1/audit")
        api_server.GovernanceHandler.do_GET(handler)
        assert handler._response_code == 401
        body = _read_response(handler)
        assert "GOVERNANCE_API_TOKEN not configured" in body["error"]

    def test_post_rejected_when_token_not_configured(self, monkeypatch):
        monkeypatch.delenv("GOVERNANCE_API_TOKEN", raising=False)
        monkeypatch.delenv("GOVERNANCE_API_TOKEN_FILE", raising=False)
        monkeypatch.delenv("GOVERNANCE_API_ALLOW_NO_AUTH", raising=False)
        monkeypatch.setattr(api_server, "_ks", mock.MagicMock())
        handler = _make_handler("POST", "/api/v1/kill-switch/engage", body={"mode": "HALT_ALL", "confirm": True})
        api_server.GovernanceHandler.do_POST(handler)
        assert handler._response_code == 401

    def test_health_endpoint_bypasses_auth_for_compatibility(self, monkeypatch):
        monkeypatch.delenv("GOVERNANCE_API_TOKEN", raising=False)
        monkeypatch.delenv("GOVERNANCE_API_TOKEN_FILE", raising=False)
        monkeypatch.delenv("GOVERNANCE_API_ALLOW_NO_AUTH", raising=False)
        monkeypatch.setattr(api_server, "_ks", mock.MagicMock())
        monkeypatch.setattr(api_server, "_cg", mock.MagicMock())
        monkeypatch.setattr(api_server, "_cb", mock.MagicMock())
        handler = _make_handler("GET", "/api/v1/health")
        api_server.GovernanceHandler.do_GET(handler)
        assert handler._response_code == 200

    def test_status_endpoint_requires_auth(self, monkeypatch):
        monkeypatch.delenv("GOVERNANCE_API_TOKEN", raising=False)
        monkeypatch.delenv("GOVERNANCE_API_TOKEN_FILE", raising=False)
        monkeypatch.delenv("GOVERNANCE_API_ALLOW_NO_AUTH", raising=False)
        handler = _make_handler("GET", "/api/v1/status")
        api_server.GovernanceHandler.do_GET(handler)
        assert handler._response_code == 401


class TestBearerAuth:
    """Bearer token auth with constant-time comparison."""

    def test_correct_token_passes_auth(self, monkeypatch):
        monkeypatch.setenv("GOVERNANCE_API_TOKEN", "test-token-abc123")
        monkeypatch.delenv("GOVERNANCE_API_ALLOW_NO_AUTH", raising=False)
        monkeypatch.setattr(api_server, "_ks", mock.MagicMock(engaged=False, mode=mock.MagicMock(name="DISENGAGED")))
        monkeypatch.setattr(api_server, "_cg", mock.MagicMock())
        monkeypatch.setattr(api_server, "_cb", mock.MagicMock())
        handler = _make_handler("GET", "/api/v1/status", headers={"Authorization": "Bearer test-token-abc123"})
        api_server.GovernanceHandler.do_GET(handler)
        assert handler._response_code == 200

    def test_wrong_token_rejected(self, monkeypatch):
        monkeypatch.setenv("GOVERNANCE_API_TOKEN", "test-token-abc123")
        monkeypatch.delenv("GOVERNANCE_API_ALLOW_NO_AUTH", raising=False)
        handler = _make_handler("GET", "/api/v1/audit", headers={"Authorization": "Bearer wrong-token"})
        api_server.GovernanceHandler.do_GET(handler)
        assert handler._response_code == 401

    def test_missing_authorization_header_rejected(self, monkeypatch):
        monkeypatch.setenv("GOVERNANCE_API_TOKEN", "test-token-abc123")
        monkeypatch.delenv("GOVERNANCE_API_ALLOW_NO_AUTH", raising=False)
        handler = _make_handler("GET", "/api/v1/audit")
        api_server.GovernanceHandler.do_GET(handler)
        assert handler._response_code == 401

    def test_compare_digest_used_for_auth(self):
        """Structural guard: hmac.compare_digest must be used, not ==."""
        src = Path(api_server.__file__).read_text(encoding="utf-8")
        assert "hmac.compare_digest" in src, "api_server must use hmac.compare_digest for auth"


class TestAllowNoAuthBypass:
    """GOVERNANCE_API_ALLOW_NO_AUTH=1 bypasses fail-closed for tests/dev."""

    def test_allow_no_auth_bypasses_get(self, monkeypatch):
        monkeypatch.delenv("GOVERNANCE_API_TOKEN", raising=False)
        monkeypatch.delenv("GOVERNANCE_API_TOKEN_FILE", raising=False)
        monkeypatch.setenv("GOVERNANCE_API_ALLOW_NO_AUTH", "1")
        monkeypatch.setattr(api_server, "_ks", mock.MagicMock(engaged=False, mode=mock.MagicMock(name="DISENGAGED")))
        monkeypatch.setattr(api_server, "_cg", mock.MagicMock())
        monkeypatch.setattr(api_server, "_cb", mock.MagicMock())
        handler = _make_handler("GET", "/api/v1/status")
        api_server.GovernanceHandler.do_GET(handler)
        assert handler._response_code == 200


class TestCorsOptIn:
    """CORS wildcard is opt-in, not default."""

    def test_no_cors_header_by_default(self, monkeypatch):
        monkeypatch.setenv("GOVERNANCE_API_ALLOW_NO_AUTH", "1")
        monkeypatch.delenv("GOVERNANCE_API_CORS_ORIGIN", raising=False)
        monkeypatch.setattr(api_server, "_ks", mock.MagicMock(engaged=False, mode=mock.MagicMock(name="DISENGAGED")))
        monkeypatch.setattr(api_server, "_cg", mock.MagicMock())
        monkeypatch.setattr(api_server, "_cb", mock.MagicMock())
        handler = _make_handler("GET", "/api/v1/health")
        # Capture headers via a side dict
        sent_headers = []

        def _capture_header(name, value=None):
            sent_headers.append((name, value))

        handler.send_header = _capture_header
        api_server.GovernanceHandler.do_GET(handler)
        cors = [h for h in sent_headers if h[0].lower() == "access-control-allow-origin"]
        assert cors == [], "CORS header must not be emitted by default"

    def test_explicit_cors_origin_emitted(self, monkeypatch):
        monkeypatch.setenv("GOVERNANCE_API_ALLOW_NO_AUTH", "1")
        monkeypatch.setenv("GOVERNANCE_API_CORS_ORIGIN", "https://example.com")
        monkeypatch.setattr(api_server, "_ks", mock.MagicMock(engaged=False, mode=mock.MagicMock(name="DISENGAGED")))
        monkeypatch.setattr(api_server, "_cg", mock.MagicMock())
        monkeypatch.setattr(api_server, "_cb", mock.MagicMock())
        handler = _make_handler("GET", "/api/v1/health")
        sent_headers = []

        def _capture_header(name, value=None):
            sent_headers.append((name, value))

        handler.send_header = _capture_header
        api_server.GovernanceHandler.do_GET(handler)
        cors = [h for h in sent_headers if h[0].lower() == "access-control-allow-origin"]
        assert cors == [("Access-Control-Allow-Origin", "https://example.com")]


class TestKillSwitchDisengageGate:
    """P0 fix: disengage must require confirm=true (matches engage gate)."""

    def test_disengage_without_confirm_rejected(self, monkeypatch):
        monkeypatch.setenv("GOVERNANCE_API_ALLOW_NO_AUTH", "1")
        ks = mock.MagicMock()
        monkeypatch.setattr(api_server, "_ks", ks)
        handler = _make_handler("POST", "/api/v1/kill-switch/disengage", body={"reason": "test"})
        api_server.GovernanceHandler.do_POST(handler)
        assert handler._response_code == 400
        body = _read_response(handler)
        assert "confirm=true" in body["error"]
        ks.disengage.assert_not_called()

    def test_disengage_with_confirm_proceeds(self, monkeypatch):
        monkeypatch.setenv("GOVERNANCE_API_ALLOW_NO_AUTH", "1")
        ks = mock.MagicMock()
        monkeypatch.setattr(api_server, "_ks", ks)
        handler = _make_handler("POST", "/api/v1/kill-switch/disengage", body={"confirm": True, "reason": "test"})
        api_server.GovernanceHandler.do_POST(handler)
        assert handler._response_code == 200
        ks.disengage.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
