"""Kill-switch fail-closed behavior for MCPGateway and HummblMCPServer.

The previous gateway called ``get_state()`` / ``KillSwitchCore`` (neither
exists on the live ``KillSwitch`` API) and returned DISENGAGED on any
exception, so HALT_ALL did not block tool calls unless an env override
was set. These tests pin the opposite: a live ``mode`` of HALT_ALL blocks
without env, and an unreadable switch blocks.
"""

from __future__ import annotations

import pytest

import hummbl_mcp.mcp_gateway as gateway_mod
from hummbl_mcp.mcp_gateway import MCPCallRequest, MCPGateway, MCPVerdict
from hummbl_mcp.protocol import TOOL_BLOCKED, JsonRpcRequest
from hummbl_mcp.server import HummblMCPServer


class _Mode:
    def __init__(self, name: str) -> None:
        self.name = name


class _Switch:
    """Duck-typed KillSwitch: exposes ``mode``, not ``get_state``."""

    def __init__(self, mode_name: str) -> None:
        self.mode = _Mode(mode_name)

    def get_state(self) -> None:
        raise AssertionError("MCPGateway must not call get_state()")


class _BrokenSwitch:
    @property
    def mode(self) -> str:
        raise RuntimeError("cannot read kill switch")

    def get_state(self) -> None:
        raise AssertionError("MCPGateway must not call get_state()")


class _StatusOnlySwitch:
    def get_status(self) -> dict[str, str]:
        return {"mode": "HALT_ALL"}

    def get_state(self) -> None:
        raise AssertionError("MCPGateway must not call get_state()")


def _request(tool_name: str = "list_notes") -> MCPCallRequest:
    return MCPCallRequest(
        tool_name=tool_name,
        adapter="test",
        arguments={"path": "notes.md"},
        delegation_token="signed-for-test",
    )


def _gateway(kill_switch: object) -> MCPGateway:
    return MCPGateway(kill_switch=kill_switch, bus_poster=lambda *_args: None)


def test_halt_all_blocks_without_env_override(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("MCP_KILL_SWITCH_STATE", raising=False)
    decision = _gateway(_Switch("HALT_ALL")).evaluate(_request())
    assert decision.verdict == MCPVerdict.BLOCK
    assert decision.allowed is False
    assert any(finding.rule == "KILL_SWITCH" for finding in decision.findings)


def test_emergency_blocks_read_tools(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("MCP_KILL_SWITCH_STATE", raising=False)
    decision = _gateway(_Switch("EMERGENCY")).evaluate(_request("list_notes"))
    assert decision.verdict == MCPVerdict.BLOCK


def test_halt_noncritical_blocks_write_allows_read(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("MCP_KILL_SWITCH_STATE", raising=False)
    gateway = _gateway(_Switch("HALT_NONCRITICAL"))
    write = gateway.evaluate(_request("write_file"))
    read = gateway.evaluate(_request("list_notes"))
    assert write.verdict == MCPVerdict.BLOCK
    assert any(finding.rule == "WRITE_TOOL_HALTED" for finding in write.findings)
    assert read.allowed is True


def test_disengaged_allows_signed_read(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("MCP_KILL_SWITCH_STATE", raising=False)
    decision = _gateway(_Switch("DISENGAGED")).evaluate(_request())
    assert decision.verdict == MCPVerdict.ALLOW


def test_unreadable_instance_fail_closes(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("MCP_KILL_SWITCH_STATE", raising=False)
    decision = _gateway(_BrokenSwitch()).evaluate(_request())
    assert decision.verdict == MCPVerdict.BLOCK
    assert any("UNAVAILABLE" in finding.message for finding in decision.findings)


def test_status_fallback_blocks_halt_all(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("MCP_KILL_SWITCH_STATE", raising=False)
    decision = _gateway(_StatusOnlySwitch()).evaluate(_request())
    assert decision.verdict == MCPVerdict.BLOCK


def test_missing_core_without_env_fail_closes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(gateway_mod, "get_kill_switch_core", None)
    monkeypatch.delenv("MCP_KILL_SWITCH_STATE", raising=False)
    gateway = MCPGateway(bus_poster=lambda *_args: None)
    decision = gateway.evaluate(_request())
    assert decision.verdict == MCPVerdict.BLOCK
    assert any("UNAVAILABLE" in finding.message for finding in decision.findings)


def test_env_override_only_when_core_absent(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(gateway_mod, "get_kill_switch_core", None)
    monkeypatch.setenv("MCP_KILL_SWITCH_STATE", "HALT_ALL")
    gateway = MCPGateway(bus_poster=lambda *_args: None)
    decision = gateway.evaluate(_request())
    assert decision.verdict == MCPVerdict.BLOCK


def test_instance_halt_wins_over_env_disengage(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("MCP_KILL_SWITCH_STATE", "DISENGAGED")
    decision = _gateway(_Switch("HALT_ALL")).evaluate(_request())
    assert decision.verdict == MCPVerdict.BLOCK


def test_live_kill_switch_mode_blocks_without_env(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pytest.importorskip("hummbl_governance")
    from hummbl_governance.kill_switch import KillSwitch, KillSwitchMode

    monkeypatch.delenv("MCP_KILL_SWITCH_STATE", raising=False)
    switch = KillSwitch(require_hmac=False)
    switch.engage(KillSwitchMode.HALT_ALL, reason="test", triggered_by="test")
    decision = _gateway(switch).evaluate(_request())
    assert decision.verdict == MCPVerdict.BLOCK


def test_server_does_not_run_handler_when_halted(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("MCP_KILL_SWITCH_STATE", raising=False)
    ran = {"count": 0}

    def _handler(_args: dict) -> dict:
        ran["count"] += 1
        return {"ok": True}

    server = HummblMCPServer(
        tool_definitions=[],
        handlers={"demo_write": _handler},
        kill_switch=_Switch("HALT_ALL"),
    )
    request = JsonRpcRequest(
        method="tools/call",
        params={"name": "demo_write", "arguments": {"_delegation_token": "t"}},
        id=1,
    )
    response = server.handle(request)
    assert response is not None
    assert "error" in response
    assert response["error"]["code"] == TOOL_BLOCKED
    assert ran["count"] == 0


def test_server_runs_handler_when_disengaged(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("MCP_KILL_SWITCH_STATE", raising=False)

    def _handler(_args: dict) -> dict:
        return {"ok": True}

    server = HummblMCPServer(
        tool_definitions=[],
        handlers={"list_notes": _handler},
        kill_switch=_Switch("DISENGAGED"),
    )
    request = JsonRpcRequest(
        method="tools/call",
        params={"name": "list_notes", "arguments": {"_delegation_token": "t"}},
        id=1,
    )
    response = server.handle(request)
    assert response is not None
    assert "error" not in response
    assert response["result"]["isError"] is False
