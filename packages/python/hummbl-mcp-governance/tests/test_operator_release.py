"""Agent-facing release boundaries belong to the standalone wrapper package."""

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
