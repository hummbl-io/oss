"""Tests for hummbl-governance API server auth hardening (STD-004 P0 fix).

Covers:
- Bearer token auth (fail-closed when GOVERNANCE_API_TOKEN not configured)
- Constant-time comparison (hmac.compare_digest)
- CORS origin is opt-in (no wildcard by default)
- Kill switch disengage is forbidden through the general API
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
    """General API credentials must never authorize operator release."""

    def test_disengage_without_confirm_rejected(self, monkeypatch):
        monkeypatch.setenv("GOVERNANCE_API_ALLOW_NO_AUTH", "1")
        ks = mock.MagicMock()
        monkeypatch.setattr(api_server, "_ks", ks)
        handler = _make_handler("POST", "/api/v1/kill-switch/disengage", body={"reason": "test"})
        api_server.GovernanceHandler.do_POST(handler)
        assert handler._response_code == 403
        body = _read_response(handler)
        assert "Operator-only" in body["error"]
        ks.disengage.assert_not_called()

    def test_disengage_with_confirm_rejected(self, monkeypatch):
        monkeypatch.setenv("GOVERNANCE_API_TOKEN", "agent-api-token")
        ks = mock.MagicMock()
        monkeypatch.setattr(api_server, "_ks", ks)
        handler = _make_handler(
            "POST", "/api/v1/kill-switch/disengage",
            body={"confirm": True, "reason": "test", "triggered_by": "forged-operator"},
            headers={"Authorization": "Bearer agent-api-token"},
        )
        api_server.GovernanceHandler.do_POST(handler)
        assert handler._response_code == 403
        ks.disengage.assert_not_called()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])


@pytest.fixture
def persistent_api(tmp_path, monkeypatch):
    from types import SimpleNamespace
    from hummbl_governance import KillSwitchMode
    from .kill_switch_helpers import operator_switch, release

    monkeypatch.setenv("HUMMBL_SIGNING_SECRET", "synthetic-api-state-key")
    monkeypatch.delenv("DCT_SECRET", raising=False)
    monkeypatch.setenv("GOVERNANCE_API_TOKEN", "synthetic-agent-api-token")
    monkeypatch.delenv("GOVERNANCE_API_TOKEN_FILE", raising=False)
    monkeypatch.setattr(api_server, "STATE_DIR", tmp_path)
    monkeypatch.setattr(api_server, "DB_PATH", tmp_path / "costs.db")
    model = SimpleNamespace(code="P1", name="model", transformation="perspect", definition="test")
    engine = SimpleNamespace(get_model=lambda _: model, generate_system_prompt=mock.Mock(return_value="prompt"))
    monkeypatch.setattr(api_server, "ReasoningEngine", lambda: engine)
    writer = operator_switch(state_dir=tmp_path)
    writer.engage(KillSwitchMode.EMERGENCY, "bootstrap", "test-operator")
    release(writer)
    api_server.init_services()
    return writer, engine


def _authenticated_request(method, path, body=None):
    handler = _make_handler(method, path, body,
                            {"Authorization": "Bearer synthetic-agent-api-token"})
    getattr(api_server.GovernanceHandler, "do_" + method)(handler)
    return handler._response_code, _read_response(handler)


def test_rest_reads_and_enforcement_follow_external_halt_and_release(persistent_api):
    from hummbl_governance import KillSwitchMode
    from .kill_switch_helpers import release

    writer, engine = persistent_api
    cached = api_server._ks
    assert _authenticated_request("POST", "/api/v1/apply", {"model": "P1"})[0] == 200
    for mode in (KillSwitchMode.EMERGENCY, KillSwitchMode.DISENGAGED):
        if mode == KillSwitchMode.EMERGENCY:
            writer.engage(mode, "external incident", "monitor")
        else:
            release(writer)
        assert api_server._ks is cached
        assert _authenticated_request("GET", "/api/v1/kill-switch")[1]["mode"] == mode.name
        assert _authenticated_request("GET", "/api/v1/status")[1]["kill_switch"]["mode"] == mode.name
        assert _authenticated_request("GET", "/api/v1/health")[1]["healthy"] is (mode == KillSwitchMode.DISENGAGED)
        engine.generate_system_prompt.reset_mock()
        code, _ = _authenticated_request("POST", "/api/v1/apply", {"model": "P1"})
        assert code == (200 if mode == KillSwitchMode.DISENGAGED else 503)
        assert engine.generate_system_prompt.called is (mode == KillSwitchMode.DISENGAGED)


@pytest.mark.parametrize("damage", ["deleted", "tampered", "missing_key", "wrong_key"])
def test_rest_fails_closed_when_cached_disengaged_state_becomes_unverifiable(persistent_api, monkeypatch, damage):
    _, engine = persistent_api
    state = api_server.STATE_DIR / "kill_switch_state.json"
    if damage == "deleted":
        state.unlink()
    elif damage == "tampered":
        state.write_text("{}", encoding="utf-8")
    elif damage == "missing_key":
        monkeypatch.delenv("HUMMBL_SIGNING_SECRET")
    else:
        monkeypatch.setenv("HUMMBL_SIGNING_SECRET", "wrong-synthetic-state-key")
    before = state.read_bytes() if state.exists() else None
    for path in ("status", "kill-switch", "health", "score"):
        assert _authenticated_request("GET", "/api/v1/" + path)[0] == 503
    assert _authenticated_request("POST", "/api/v1/apply", {"model": "P1"})[0] == 503
    engine.generate_system_prompt.assert_not_called()
    assert (state.read_bytes() if state.exists() else None) == before
