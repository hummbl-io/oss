"""Regression tests for mcp_ollama_router agent-identity verification.

Covers the fail-closed posture: when DCT_SECRET is configured, a supplied
agent_identity_token must be verified — an unavailable IDP verifier or a
malformed configuration must reject, never silently accept.
"""

import sys

import pytest


def _import_router():
    """Import mcp_ollama_router, which rebinds sys.stdout at import time."""
    saved = sys.stdout
    try:
        from hummbl_mcp import mcp_ollama_router
    finally:
        sys.stdout = saved
    return mcp_ollama_router


router = _import_router()


@pytest.fixture
def clean_env(monkeypatch):
    monkeypatch.delenv("DCT_SECRET", raising=False)
    return monkeypatch


class _FakeToken:
    def __init__(self, subject="agent-x", expired=False, sig_ok=True):
        self.subject = subject
        self._expired = expired
        self._sig_ok = sig_ok

    def verify_signature(self, _secret):
        return self._sig_ok

    def is_expired(self):
        return self._expired


class _FakeTokenClass:
    token = None

    @classmethod
    def from_env_string(cls, _s):
        if cls.token is None:
            raise ValueError("malformed token")
        return cls.token


class _FakeManager:
    def __init__(self, secret=None):
        pass


def _stub_verifier(monkeypatch, token):
    _FakeTokenClass.token = token
    # Names only exist when hummbl_governance imports; create them when absent.
    monkeypatch.setattr(router, "DelegationTokenCapabilityToken", _FakeTokenClass, raising=False)
    monkeypatch.setattr(router, "DelegationTokenManager", _FakeManager, raising=False)


def test_secret_set_idp_unavailable_fails_closed(clean_env, monkeypatch):
    """(a) DCT_SECRET configured + IDP verifier unavailable -> token rejected.

    This test FAILS against the pre-fix code, which returned True before
    consulting DCT_SECRET.
    """
    clean_env.setenv("DCT_SECRET", "test-secret")
    monkeypatch.setattr(router, "_IDP_AVAILABLE", False)
    assert router._verify_agent_identity_token("any-token", "agent-x") is False


def test_secret_set_invalid_token_rejected(clean_env, monkeypatch):
    """(b) DCT_SECRET set + IDP available + malformed/invalid token -> rejected."""
    clean_env.setenv("DCT_SECRET", "test-secret")
    monkeypatch.setattr(router, "_IDP_AVAILABLE", True)
    _stub_verifier(monkeypatch, token=None)  # from_env_string raises
    assert router._verify_agent_identity_token("garbage", "agent-x") is False

    _stub_verifier(monkeypatch, token=_FakeToken(sig_ok=False))
    assert router._verify_agent_identity_token("bad-sig", "agent-x") is False


def test_secret_set_valid_token_accepted(clean_env, monkeypatch):
    """(c) DCT_SECRET set + valid token via stubbed verifier -> accepted."""
    clean_env.setenv("DCT_SECRET", "test-secret")
    monkeypatch.setattr(router, "_IDP_AVAILABLE", True)
    _stub_verifier(monkeypatch, token=_FakeToken(subject="agent-x"))
    assert router._verify_agent_identity_token("good-token", "agent-x") is True


def test_malformed_configuration_explicit_error(clean_env, monkeypatch):
    """(d) Malformed configuration -> explicit rejection, not silent degrade."""
    # Whitespace-only secret is configured-but-malformed.
    clean_env.setenv("DCT_SECRET", "   ")
    monkeypatch.setattr(router, "_IDP_AVAILABLE", True)
    assert router._verify_agent_identity_token("any-token", "agent-x") is False

    # Secret set but verifier unavailable is also malformed-for-purpose.
    clean_env.setenv("DCT_SECRET", "real-secret")
    monkeypatch.setattr(router, "_IDP_AVAILABLE", False)
    assert router._verify_agent_identity_token("any-token", "agent-x") is False


def test_no_secret_configured_still_fail_open(clean_env, monkeypatch):
    """Adjacent posture preserved: no DCT_SECRET -> verification skipped (True)."""
    monkeypatch.setattr(router, "_IDP_AVAILABLE", True)
    assert router._verify_agent_identity_token("any-token", "agent-x") is True

    monkeypatch.setattr(router, "_IDP_AVAILABLE", False)
    assert router._verify_agent_identity_token("any-token", "agent-x") is True
