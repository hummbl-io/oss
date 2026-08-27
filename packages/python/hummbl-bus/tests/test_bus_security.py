from __future__ import annotations

import logging

import pytest
from hummbl_bus.bus_policy import (
    BusSecurityPolicy,
    PolicyLevel,
    get_bus_policy,
    reset_bus_policy,
)


def test_warn_policy_logs_unsigned_message(caplog: pytest.LogCaptureFixture) -> None:
    policy = BusSecurityPolicy(level="warn")

    with caplog.at_level(logging.WARNING):
        policy.check_signing(secret=None, from_id="codex", msg_type="STATUS")

    assert "Unsigned bus message from codex" in caplog.text


def test_strict_policy_rejects_unsigned_status() -> None:
    policy = BusSecurityPolicy(level="strict")

    with pytest.raises(ValueError):
        policy.check_signing(secret=None, from_id="codex", msg_type="STATUS")


def test_strict_policy_allows_heartbeat_without_secret() -> None:
    policy = BusSecurityPolicy(level="strict")

    policy.check_signing(secret=None, from_id="codex", msg_type="HEARTBEAT")


def test_get_bus_policy_tracks_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BUS_SECURITY_POLICY", "strict")
    reset_bus_policy()

    assert get_bus_policy().level == PolicyLevel.STRICT
