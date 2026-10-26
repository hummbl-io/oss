"""Fail-closed state and credential regressions for the shared kill switch."""

import json

import pytest

import hummbl_governance.kill_switch as module
from hummbl_governance.kill_switch import (
    KillSwitch, KillSwitchMode, KillSwitchTamperError,
    KillSwitchConfigurationError, KillSwitchPersistenceError,
)


@pytest.fixture(autouse=True)
def isolated_core(tmp_path, monkeypatch):
    """Never use production state or credentials in these tests."""
    monkeypatch.setenv("GOVERNANCE_STATE_DIR", str(tmp_path))
    monkeypatch.delenv("HUMMBL_SIGNING_SECRET", raising=False)
    monkeypatch.delenv("DCT_SECRET", raising=False)
    monkeypatch.setattr(module, "_core_instance", None)


def provision(tmp_path, monkeypatch):
    """Create a signed emergency and explicitly approve its release."""
    monkeypatch.setenv("HUMMBL_SIGNING_SECRET", "regression-test-only-key")
    writer = KillSwitch(state_dir=tmp_path)
    writer.engage(KillSwitchMode.EMERGENCY, "bootstrap", "test-operator")
    writer.disengage("test-operator", "bootstrap approved")
    return writer


def test_missing_credentials_fail_before_shared_core_or_state_creation(tmp_path):
    """An absent key must not create an unsigned persistent core."""
    with pytest.raises(KillSwitchConfigurationError, match="Signing"):
        module.get_kill_switch_core()
    assert module._core_instance is None
    assert not list(tmp_path.iterdir())


def test_unsigned_writes_are_rejected_before_creating_a_file(tmp_path):
    """The base writer cannot produce state its mandatory loader rejects."""
    writer = KillSwitch(state_dir=tmp_path)
    with pytest.raises(KillSwitchConfigurationError, match="Signing"):
        writer.engage(KillSwitchMode.EMERGENCY, "stop", "test-operator")
    assert not list(tmp_path.iterdir())


def test_retained_core_rechecks_external_state(tmp_path, monkeypatch):
    """Holding a reference must not bypass verification at the decision point."""
    writer = provision(tmp_path, monkeypatch)
    core = module.get_kill_switch_core()
    assert core.check_task_allowed("work")["allowed"]
    writer.engage(KillSwitchMode.EMERGENCY, "external stop", "test-operator")
    assert core.check_task_allowed("work")["allowed"] is False
    assert core.get_status()["mode"] == "EMERGENCY"
    assert module.get_kill_switch_core() is core


@pytest.mark.parametrize("damage", [
    "tampered", "unsigned", "wrong_key", "truncated", "array", "bad_signature_type",
    "non_ascii_signature", "signed_missing_mode", "signed_unknown_mode", "deleted",
])
def test_invalid_state_rejected_on_every_read_and_restart(tmp_path, monkeypatch, damage):
    """A cached DISENGAGED value cannot hide damaged or absent authority."""
    provision(tmp_path, monkeypatch)
    core = module.get_kill_switch_core()
    state = tmp_path / "kill_switch_state.json"
    data = json.loads(state.read_text())
    if damage == "tampered":
        data["reason"] = "altered without signing"
    elif damage == "unsigned":
        data.pop("signature")
    elif damage == "wrong_key":
        monkeypatch.setenv("HUMMBL_SIGNING_SECRET", "wrong-test-key")
    elif damage == "bad_signature_type":
        data["signature"] = []
    elif damage == "non_ascii_signature":
        data["signature"] = "\u2603"
    elif damage.startswith("signed_"):
        data.pop("signature")
        if damage == "signed_missing_mode":
            data.pop("mode")
        else:
            data["mode"] = "NOT_A_MODE"
        data["signature"] = KillSwitch._compute_signature(data, b"regression-test-only-key")
    if damage == "deleted":
        state.unlink()
    else:
        state.write_text(
            "{" if damage == "truncated" else "[]" if damage == "array" else json.dumps(data),
            encoding="utf-8",
        )
    before = state.read_bytes() if state.exists() else None
    for read in (module.get_kill_switch_core, core.get_status, core.get_history,
                 lambda: core.mode, lambda: core.engaged,
                 lambda: core.check_task_allowed("safety_monitoring"),
                 lambda: core.check_or_raise("work")):
        with pytest.raises(KillSwitchTamperError):
            read()
    monkeypatch.setattr(module, "_core_instance", None)
    with pytest.raises(KillSwitchTamperError):
        module.get_kill_switch_core()
    assert (state.read_bytes() if state.exists() else None) == before


def test_empty_directory_requires_explicit_signed_initialization(tmp_path, monkeypatch):
    """Even with credentials, absence is not proof of DISENGAGED state."""
    monkeypatch.setenv("HUMMBL_SIGNING_SECRET", "regression-test-only-key")
    with pytest.raises(KillSwitchTamperError, match="missing"):
        module.get_kill_switch_core()
    assert not list(tmp_path.iterdir())
    writer = KillSwitch(state_dir=tmp_path)
    writer.engage(KillSwitchMode.EMERGENCY, "operator initialization", "test-operator")
    assert module.get_kill_switch_core().check_task_allowed("work")["allowed"] is False
    writer.disengage("test-operator", "separately approved release")
    assert module.get_kill_switch_core().check_task_allowed("work")["allowed"] is True


def test_key_restoration_preserves_emergency_and_does_not_rewrite_state(tmp_path, monkeypatch):
    """Credential repair is not authorization to release an emergency."""
    writer = provision(tmp_path, monkeypatch)
    core = module.get_kill_switch_core()
    writer.engage(KillSwitchMode.EMERGENCY, "stop", "test-operator")
    state = tmp_path / "kill_switch_state.json"
    original = state.read_bytes()
    monkeypatch.delenv("HUMMBL_SIGNING_SECRET")
    for read in (module.get_kill_switch_core, core.get_status, core.get_history,
                 lambda: core.check_task_allowed("work")):
        with pytest.raises(KillSwitchConfigurationError):
            read()
    with pytest.raises(KillSwitchConfigurationError):
        writer.disengage("test-operator")
    assert state.read_bytes() == original
    monkeypatch.setenv("HUMMBL_SIGNING_SECRET", "regression-test-only-key")
    assert core.get_status()["mode"] == "EMERGENCY"
    assert core.check_task_allowed("work")["allowed"] is False
    assert state.read_bytes() == original
    writer.disengage("test-operator", "approved release")
    assert core.check_task_allowed("work")["allowed"] is True


@pytest.mark.parametrize("secret_var", ["HUMMBL_SIGNING_SECRET", "DCT_SECRET"])
def test_supported_signing_credentials(secret_var, tmp_path, monkeypatch):
    """Both existing credential sources still produce verifiable state."""
    monkeypatch.setenv(secret_var, "regression-test-only-key")
    writer = KillSwitch(state_dir=tmp_path)
    writer.engage(KillSwitchMode.EMERGENCY, "stop", "test-operator")
    assert module.get_kill_switch_core().mode == KillSwitchMode.EMERGENCY


@pytest.mark.parametrize("transition", ["engage", "disengage"])
@pytest.mark.parametrize("operation", ["fsync", "replace"])
def test_failed_atomic_replace_preserves_state_and_requires_emergency_recovery(
    tmp_path, monkeypatch, transition, operation,
):
    """Failed persistence cannot announce success or enable local decisions."""
    provision(tmp_path, monkeypatch)
    core = module.get_kill_switch_core()
    if transition == "disengage":
        core.engage(KillSwitchMode.EMERGENCY, "stop", "test-operator")
    state = tmp_path / "kill_switch_state.json"
    before = state.read_bytes()
    notifications = []
    core.subscribe(notifications.append)

    def fail_replace(*args):
        raise OSError("injected storage failure")

    with monkeypatch.context() as patch:
        patch.setattr(module.os, operation, fail_replace)
        with pytest.raises(KillSwitchPersistenceError):
            if transition == "engage":
                core.engage(KillSwitchMode.EMERGENCY, "stop", "test-operator")
            else:
                core.disengage("test-operator")
    assert state.read_bytes() == before
    assert not notifications
    assert not list(tmp_path.glob(".kill-switch-*"))
    for read in (core.get_status, module.get_kill_switch_core,
                 lambda: core.check_task_allowed("work"),
                 lambda: core.disengage("test-operator")):
        with pytest.raises(KillSwitchPersistenceError):
            read()
    core.engage(KillSwitchMode.EMERGENCY, "storage restored", "test-operator")
    assert core.check_task_allowed("work")["allowed"] is False
    core.disengage("test-operator", "approved release")
    assert core.check_task_allowed("work")["allowed"] is True


def test_secret_lost_before_write_preserves_valid_file(tmp_path, monkeypatch):
    """A retained writer cannot truncate or replace state without a key."""
    writer = provision(tmp_path, monkeypatch)
    state = tmp_path / "kill_switch_state.json"
    before = state.read_bytes()
    monkeypatch.delenv("HUMMBL_SIGNING_SECRET")
    with pytest.raises(KillSwitchConfigurationError):
        writer.engage(KillSwitchMode.EMERGENCY, "stop", "test-operator")
    assert state.read_bytes() == before
    with pytest.raises(KillSwitchPersistenceError):
        writer.check_task_allowed("work")


def test_disengage_cannot_resign_tampered_state(tmp_path, monkeypatch):
    """The normal release operation is not an integrity-repair bypass."""
    writer = provision(tmp_path, monkeypatch)
    state = tmp_path / "kill_switch_state.json"
    data = json.loads(state.read_text())
    data["reason"] = "tampered"
    state.write_text(json.dumps(data), encoding="utf-8")
    before = state.read_bytes()
    with pytest.raises(KillSwitchTamperError):
        writer.disengage("test-operator")
    assert state.read_bytes() == before


def test_refresh_preserves_local_subscribers_and_history(tmp_path, monkeypatch):
    """Reloading does not replace the singleton or fabricate notifications."""
    writer = provision(tmp_path, monkeypatch)
    core = module.get_kill_switch_core()
    notifications = []
    core.subscribe(notifications.append)
    core.engage(KillSwitchMode.HALT_ALL, "local stop", "test-operator", affected_tasks=7)
    count = len(core.get_history())
    for _ in range(3):
        assert module.get_kill_switch_core() is core
    assert len(core.get_history()) == count
    assert core.get_history()[-1].affected_tasks == 7
    writer.engage(KillSwitchMode.EMERGENCY, "external stop", "test-operator")
    assert core.get_history()[-1].mode == KillSwitchMode.EMERGENCY
    assert len(notifications) == 1
    core.disengage("test-operator", "approved release")
    assert len(notifications) == 2
