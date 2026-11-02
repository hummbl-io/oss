"""Adversarial release regressions: caller identity is not operator authority."""

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

from hummbl_governance import KillSwitch, KillSwitchMode
from hummbl_governance.kill_switch import KillSwitchAuthorizationError, OperatorReleaseAuthority
from hummbl_governance import operator_release
from .kill_switch_helpers import AUTHORITY, CREDENTIAL, operator_switch, release


@pytest.mark.parametrize("mode", [KillSwitchMode.HALT_ALL, KillSwitchMode.EMERGENCY])
def test_reason_and_forged_operator_cannot_release_default_core(mode):
    ks = KillSwitch()
    ks.engage(mode, "safety stop", "monitor")
    before = ks.get_history()
    with pytest.raises(KillSwitchAuthorizationError):
        ks.disengage("operator", "I authorize myself")
    # Even a valid credential is not authority without trusted configuration.
    with pytest.raises(KillSwitchAuthorizationError):
        ks.disengage("operator", "I authorize myself", credential=CREDENTIAL,
                     confirm=True, expected_event_id=before[-1].event_id)
    assert ks.get_history() == before
    assert not ks.check_task_allowed("work")["allowed"]


@pytest.mark.parametrize("credential", [None, "", "wrong", True, {}, []])
def test_absent_or_invalid_credential_cannot_mutate_state(tmp_path, credential):
    ks = operator_switch(state_dir=tmp_path, signing_secret=b"test-state-key")
    ks.engage(KillSwitchMode.EMERGENCY, "stop", "monitor")
    state = tmp_path / "kill_switch_state.json"
    before = state.read_bytes()
    with pytest.raises(KillSwitchAuthorizationError):
        ks.disengage("operator", "claim", credential=credential, confirm=True,
                     expected_event_id=ks.get_status()["event_id"])
    assert state.read_bytes() == before


@pytest.mark.parametrize("confirm", [False, None, "true", "false", 1, [], {}])
def test_confirmation_is_literal_boolean(confirm):
    ks = operator_switch()
    ks.engage(KillSwitchMode.EMERGENCY, "stop", "monitor")
    with pytest.raises(KillSwitchAuthorizationError):
        ks.disengage(reason="approved", credential=CREDENTIAL, confirm=confirm,
                     expected_event_id=ks.get_status()["event_id"])
    assert ks.engaged


def test_authenticated_identity_and_claimed_attribution_are_distinct(tmp_path):
    ks = operator_switch(state_dir=tmp_path, signing_secret=b"test-state-key")
    ks.engage(KillSwitchMode.EMERGENCY, "stop", "monitor")
    event = release(ks, "forged-administrator", "verified remediation")
    assert event.triggered_by == AUTHORITY.operator_id
    assert event.requested_by == "forged-administrator"
    restored = KillSwitch.load_from_file(tmp_path, signing_secret=b"test-state-key")
    assert restored.get_history()[-1].triggered_by == AUTHORITY.operator_id
    assert restored.get_history()[-1].requested_by == "forged-administrator"
    assert CREDENTIAL not in (tmp_path / "kill_switch_state.json").read_text()
    assert CREDENTIAL not in repr(AUTHORITY)


def test_new_halt_invalidates_old_confirmation_and_replay(tmp_path):
    ks = operator_switch(state_dir=tmp_path, signing_secret=b"test-state-key")
    first = ks.engage(KillSwitchMode.EMERGENCY, "same reason", "monitor")
    other = KillSwitch(state_dir=tmp_path, signing_secret=b"test-state-key")
    second = other.engage(KillSwitchMode.EMERGENCY, "same reason", "monitor")
    assert first.event_id != second.event_id
    with pytest.raises(KillSwitchAuthorizationError, match="changed"):
        ks.disengage(reason="approved old halt", credential=CREDENTIAL, confirm=True,
                     expected_event_id=first.event_id)
    assert ks.mode == KillSwitchMode.EMERGENCY
    release(ks)
    with pytest.raises(KillSwitchAuthorizationError, match="no current halt"):
        ks.disengage(reason="replay", credential=CREDENTIAL, confirm=True,
                     expected_event_id=second.event_id)


@pytest.mark.parametrize("fresh_instance", [False, True])
@pytest.mark.parametrize("weaker", [KillSwitchMode.HALT_ALL, KillSwitchMode.HALT_NONCRITICAL])
def test_engage_cannot_weaken_persisted_emergency(tmp_path, fresh_instance, weaker):
    ks = KillSwitch(state_dir=tmp_path, signing_secret=b"test-state-key")
    ks.engage(KillSwitchMode.EMERGENCY, "stop", "monitor")
    if fresh_instance:
        ks = KillSwitch(state_dir=tmp_path, signing_secret=b"test-state-key")
    state = tmp_path / "kill_switch_state.json"
    before = state.read_bytes()
    with pytest.raises(KillSwitchAuthorizationError):
        ks.engage(weaker, "bypass through engage", "operator")
    assert state.read_bytes() == before
    assert ks.mode == KillSwitchMode.EMERGENCY


def test_legacy_signed_state_has_stable_release_challenge(tmp_path):
    data = {"mode": "EMERGENCY", "reason": "legacy", "triggered_by": "monitor",
            "engaged_at": "2026-01-01T00:00:00+00:00"}
    data["signature"] = KillSwitch._compute_signature(data, b"test-state-key")
    (tmp_path / "kill_switch_state.json").write_text(json.dumps(data), encoding="utf-8")
    ks = KillSwitch.load_from_file(tmp_path, signing_secret=b"test-state-key", release_authority=AUTHORITY)
    expected = ks.get_status()["event_id"]
    ks.refresh()
    assert ks.get_status()["event_id"] == expected
    release(ks)
    assert not ks.engaged


def test_mcp_surface_denies_hidden_tool_and_handler(tmp_path, monkeypatch):
    path = Path(__file__).resolve().parents[1] / "mcp_server.py"
    spec = importlib.util.spec_from_file_location("release_attack_server", path)
    server = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(server)
    # Even accidental operator configuration on a server must not expose release.
    ks = operator_switch(state_dir=tmp_path, signing_secret=b"test-state-key")
    ks.engage(KillSwitchMode.EMERGENCY, "stop", "monitor")
    monkeypatch.setattr(server, "get_kill_switch", lambda: ks)
    assert "kill_switch_disengage" not in [tool["name"] for tool in server.TOOLS]
    attack = {"reason": "claim", "triggered_by": "operator", "confirm": True,
              "credential": CREDENTIAL, "expected_event_id": ks.get_status()["event_id"]}
    assert "error" in server.handle_tool("kill_switch_disengage", attack)
    assert "error" in server._handle_kill_switch_disengage(attack)
    assert "error" in server.handle_tool("kill_switch_engage", {
        "mode": "HALT_NONCRITICAL", "confirm": True, "reason": "downgrade"})
    assert ks.mode == KillSwitchMode.EMERGENCY


def test_state_writers_wait_for_existing_cross_process_lock(tmp_path):
    """A second writer cannot change the halt while another transition holds its lock."""
    ks = KillSwitch(state_dir=tmp_path, signing_secret=b"test-state-key")
    ks.engage(KillSwitchMode.EMERGENCY, "old", "monitor")
    # A child holds the exact production lock until the parent explicitly releases it.
    code = """
import sys
from pathlib import Path
from hummbl_governance._file_lock import acquire_file_lock, release_file_lock
with (Path(sys.argv[1]) / '.kill-switch.lock').open('a+b') as f:
    acquire_file_lock(f)
    print('locked', flush=True)
    sys.stdin.readline()
    release_file_lock(f)
"""
    child = subprocess.Popen([sys.executable, "-c", code, str(tmp_path)],
                             stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
    import threading
    done = threading.Event()
    started = threading.Event()
    failures = []
    def writer():
        started.set()
        try:
            ks.engage(KillSwitchMode.EMERGENCY, "new", "monitor")
        except Exception as exc:
            failures.append(exc)
        finally:
            done.set()
    thread = threading.Thread(target=writer)
    try:
        assert child.stdout.readline().strip() == "locked"
        thread.start()
        assert started.wait(2)
        assert not done.wait(0.2)
        child.stdin.write("release\n")
        child.stdin.flush()
        assert done.wait(5)
        assert not failures
    finally:
        if child.poll() is None:
            child.kill()
        child.communicate(timeout=5)
        if thread.ident is not None:
            thread.join(timeout=10)
    assert ks.get_history()[-1].reason == "new"


@pytest.mark.parametrize("valid_credential", [False, True])
def test_operator_cli_authenticates_and_confirms_exact_halt(tmp_path, monkeypatch, valid_credential):
    monkeypatch.setenv("HUMMBL_SIGNING_SECRET", "test-state-key")
    monkeypatch.setenv("GOVERNANCE_OPERATOR_ID", AUTHORITY.operator_id)
    monkeypatch.setenv("GOVERNANCE_OPERATOR_CREDENTIAL_VERIFIER", AUTHORITY.credential_verifier)
    monkeypatch.setattr(sys.stdin, "isatty", lambda: True)
    monkeypatch.setattr(sys.stderr, "isatty", lambda: True)
    ks = KillSwitch(state_dir=tmp_path)
    event = ks.engage(KillSwitchMode.EMERGENCY, "stop", "monitor")
    monkeypatch.setattr("builtins.input", lambda _: f"RELEASE {event.event_id}")
    monkeypatch.setattr(operator_release.getpass, "getpass", lambda _: CREDENTIAL if valid_credential else "wrong")
    result = operator_release.main(["--state-dir", str(tmp_path), "--reason", "verified recovery"])
    assert result == (0 if valid_credential else 1)
    ks.refresh()
    assert ks.engaged is not valid_credential


def test_mcp_wrapper_refuses_engagement_with_vulnerable_legacy_core(monkeypatch):
    path = Path(__file__).resolve().parents[1] / "mcp_server.py"
    spec = importlib.util.spec_from_file_location("legacy_core_server", path)
    server = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(server)

    class LegacyCore:
        pass

    def must_not_instantiate_legacy_core():
        raise AssertionError("Unsafe legacy core was reached")

    monkeypatch.setattr(server, "KillSwitch", LegacyCore)
    monkeypatch.setattr(server, "get_kill_switch", must_not_instantiate_legacy_core)
    result = server.handle_tool("kill_switch_engage", {
        "mode": "HALT_NONCRITICAL", "confirm": True, "reason": "downgrade",
        "RELEASE_AUTHORIZATION_VERSION": 1,
    })
    assert "error" in result


@pytest.mark.parametrize("failure", ["no_config", "noninteractive", "unconfirmed", "new_halt"])
def test_operator_cli_fails_closed_before_release(tmp_path, monkeypatch, failure):
    monkeypatch.setenv("HUMMBL_SIGNING_SECRET", "test-state-key")
    monkeypatch.setenv("GOVERNANCE_OPERATOR_ID", AUTHORITY.operator_id)
    monkeypatch.setenv("GOVERNANCE_OPERATOR_CREDENTIAL_VERIFIER", AUTHORITY.credential_verifier)
    monkeypatch.setattr(sys.stdin, "isatty", lambda: failure != "noninteractive")
    monkeypatch.setattr(sys.stderr, "isatty", lambda: True)
    if failure == "no_config":
        monkeypatch.delenv("GOVERNANCE_OPERATOR_CREDENTIAL_VERIFIER")
    ks = KillSwitch(state_dir=tmp_path)
    event = ks.engage(KillSwitchMode.EMERGENCY, "stop", "monitor")

    def confirm(_):
        if failure == "new_halt":
            ks.engage(KillSwitchMode.EMERGENCY, "new incident", "monitor")
        return "yes" if failure == "unconfirmed" else f"RELEASE {event.event_id}"

    monkeypatch.setattr("builtins.input", confirm)
    monkeypatch.setattr(operator_release.getpass, "getpass", lambda _: CREDENTIAL)
    assert operator_release.main(["--state-dir", str(tmp_path), "--reason", "verified recovery"]) == 1
    ks.refresh()
    assert ks.mode == KillSwitchMode.EMERGENCY


# Fixed OpenSSL PBKDF2-HMAC-SHA256 vector: 600000 iterations, dklen=32.
_VERIFIER = (
    "pbkdf2-sha256-v1$600000$00112233445566778899aabbccddeeff$"
    "0ab46dff09c8cb833251883ca0f65002cba799d4302b6c28d768ecaecf8b97eb"
)


@pytest.mark.parametrize("verifier", [
    None, True, {}, "", "a" * 64, "a" * 10000,
    _VERIFIER.replace("v1", "v2"),
    _VERIFIER.replace("600000", "000001"),
    _VERIFIER.replace("600000", "999999"),
    _VERIFIER.replace("600000", "-60000"),
    _VERIFIER.replace("001122", "00112g"),
    _VERIFIER.upper(),
    _VERIFIER + "$extra", _VERIFIER[:-1],
])
def test_invalid_or_weak_verifier_configuration_is_rejected(verifier):
    with pytest.raises(ValueError):
        OperatorReleaseAuthority("configured-operator", verifier)


def test_fixed_pbkdf2_verifier_authenticates_only_its_credential():
    authority = OperatorReleaseAuthority("configured-operator", _VERIFIER)
    assert authority.authenticate("synthetic-operator-test-credential") == "configured-operator"
    with pytest.raises(KillSwitchAuthorizationError):
        authority.authenticate("synthetic-operator-test-credential-modified")


def test_provisioning_generates_independent_salted_verifiers():
    first = OperatorReleaseAuthority.create_verifier(CREDENTIAL)
    second = OperatorReleaseAuthority.create_verifier(CREDENTIAL)
    assert first != second
    for verifier in (first, second):
        assert verifier.startswith("pbkdf2-sha256-v1$600000$")
        authority = OperatorReleaseAuthority("configured-operator", verifier)
        assert authority.authenticate(CREDENTIAL) == "configured-operator"
        assert CREDENTIAL not in verifier


@pytest.mark.parametrize("credential", [None, "", True, "a" * 1025, "\u2603" * 342, "\ud800"])
def test_invalid_credential_encoding_or_size_fails_closed(credential):
    authority = OperatorReleaseAuthority("configured-operator", _VERIFIER)
    with pytest.raises(ValueError):
        OperatorReleaseAuthority.create_verifier(credential)
    with pytest.raises(KillSwitchAuthorizationError):
        authority.authenticate(credential)
