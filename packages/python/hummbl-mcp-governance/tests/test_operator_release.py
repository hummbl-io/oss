"""Agent-facing release boundaries belong to the standalone wrapper package."""

from pathlib import Path

import pytest

import governance_mcp_server as server


def test_release_tool_and_former_handler_never_reach_core(monkeypatch):
    def must_not_reach_core():
        raise AssertionError("Agent release reached the core")

    monkeypatch.setattr(server, "get_kill_switch", must_not_reach_core)
    assert "kill_switch_disengage" not in [tool["name"] for tool in server.TOOLS]
    attack = {"reason": "self approval", "triggered_by": "operator", "confirm": True,
              "credential": "forged-credential", "expected_event_id": "forged-halt"}
    assert "error" in server.handle_tool("kill_switch_disengage", attack)
    assert "error" in server._handle_kill_switch_disengage(attack)


def test_legacy_core_cannot_weaken_a_halt_through_engage(monkeypatch):
    class LegacyCore:
        pass

    def must_not_reach_core():
        raise AssertionError("Unsafe legacy core was reached")

    monkeypatch.setattr(server, "KillSwitch", LegacyCore)
    monkeypatch.setattr(server, "get_kill_switch", must_not_reach_core)
    result = server.handle_tool("kill_switch_engage", {
        "mode": "HALT_NONCRITICAL", "confirm": True, "reason": "downgrade",
        "RELEASE_AUTHORIZATION_VERSION": 1,
    })
    assert "error" in result


def test_reader_tracks_external_transitions_or_rejects_unsupported_core(tmp_path, monkeypatch):
    """Exercise current core integration; legacy dependency must refuse all reads."""
    monkeypatch.setattr(server, "STATE_DIR", str(tmp_path))
    monkeypatch.setattr(server, "DB_PATH", str(tmp_path / "costs.db"))
    monkeypatch.setattr(server, "AUDIT_DIR", str(tmp_path / "audit"))
    monkeypatch.setattr(server, "_instances", {})
    monkeypatch.setenv("HUMMBL_SIGNING_SECRET", "synthetic-wrapper-state-key")
    monkeypatch.delenv("DCT_SECRET", raising=False)
    if getattr(server.KillSwitch, "AUTHORITATIVE_READS_VERSION", 0) != 1:
        with pytest.raises(RuntimeError, match="authoritative"):
            server.handle_tool("kill_switch_status", {})
        assert not list(tmp_path.iterdir())
        return

    from hummbl_governance.kill_switch import KillSwitchMode, KillSwitchTamperError, OperatorReleaseAuthority
    credential = "synthetic-separate-wrapper-operator-credential"
    authority = OperatorReleaseAuthority("test-operator", OperatorReleaseAuthority.create_verifier(credential))
    writer = server.KillSwitch(state_dir=tmp_path, release_authority=authority)

    def release():
        writer.disengage(reason="approved", credential=credential, confirm=True,
                         expected_event_id=writer.get_status()["event_id"])

    writer.engage(KillSwitchMode.EMERGENCY, "bootstrap", "monitor")
    release()
    retained = server.get_kill_switch()
    assert retained.check_task_allowed("work")["allowed"]
    for mode in (KillSwitchMode.EMERGENCY, KillSwitchMode.DISENGAGED):
        if mode == KillSwitchMode.EMERGENCY:
            writer.engage(mode, "external incident", "monitor")
        else:
            release()
        expected = mode == KillSwitchMode.DISENGAGED
        assert server.get_kill_switch() is retained
        assert retained.check_task_allowed("work")["allowed"] is expected
        assert server.handle_tool("kill_switch_status", {})["status"]["mode"] == mode.name
        assert server.handle_tool("governance_status", {})["kill_switch"]["mode"] == mode.name
        probe = next(p for p in server.handle_tool("health_check", {})["probes"] if p["name"] == "kill_switch")
        assert probe["healthy"] is expected
    # Never return cached DISENGAGED after the authority disappears.
    state = Path(server.STATE_DIR) / "kill_switch_state.json"
    state.unlink()
    with pytest.raises(KillSwitchTamperError, match="missing"):
        server.handle_tool("kill_switch_status", {})
    assert server.handle_tool("health_check", {})["overall_healthy"] is False
    assert not state.exists()


def test_release_capable_but_stale_legacy_core_is_not_cached(monkeypatch, tmp_path):
    class StaleCore:
        RELEASE_AUTHORIZATION_VERSION = 1

        @classmethod
        def load_from_file(cls, *args, **kwargs):
            raise AssertionError("Unsafe snapshot loader was reached")

    monkeypatch.setattr(server, "KillSwitch", StaleCore)
    monkeypatch.setattr(server, "STATE_DIR", str(tmp_path))
    monkeypatch.setattr(server, "_instances", {})
    with pytest.raises(RuntimeError, match="authoritative"):
        server.get_kill_switch()
    assert not server._instances
    assert not list(tmp_path.iterdir())
