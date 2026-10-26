"""Exercise a persistent MCP reader and the separate governance writer process."""

import json
import os
import selectors
import subprocess
import sys
from pathlib import Path

import pytest

pytest.importorskip("hummbl_governance")
from hummbl_governance.kill_switch import KillSwitch, KillSwitchMode


@pytest.fixture
def state_env(tmp_path, monkeypatch):
    """Provision signed state through explicit operator transitions."""
    monkeypatch.setenv("GOVERNANCE_STATE_DIR", str(tmp_path))
    monkeypatch.setenv("HUMMBL_SIGNING_SECRET", "regression-test-only-key")
    monkeypatch.delenv("DCT_SECRET", raising=False)
    writer = KillSwitch(state_dir=tmp_path)
    writer.engage(KillSwitchMode.EMERGENCY, "initialization", "test-operator")
    writer.disengage("test-operator", "initialization approved")
    return os.environ.copy()


@pytest.fixture
def reader(state_env):
    """Keep one real stdio MCP process alive across multiple requests."""
    process = subprocess.Popen(
        [sys.executable, "-m", "hummbl_mcp.mcp_kill_switch"],
        env=state_env, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL, text=True, bufsize=1,
    )

    def call(name, arguments=None):
        request = {"id": 1, "method": "tools/call", "params": {
            "name": name, "arguments": arguments or {},
        }}
        process.stdin.write(json.dumps(request) + "\n")
        process.stdin.flush()
        with selectors.DefaultSelector() as selector:
            selector.register(process.stdout, selectors.EVENT_READ)
            assert selector.select(timeout=10), "MCP response timed out"
        line = process.stdout.readline()
        assert line, f"MCP reader exited: {process.poll()}"
        return json.loads(line)["result"]

    yield call
    process.stdin.close()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=5)
    process.stdout.close()


def payload(result):
    """Require a successful tool result before decoding its payload."""
    assert not result.get("isError"), result
    return json.loads(result["content"][0]["text"])


def governance_transition(env, mode):
    """Use the existing governance handlers in an independent interpreter."""
    code = """
import sys
import mcp_server
if sys.argv[1] == "DISENGAGED":
    result = mcp_server._handle_kill_switch_disengage({
        "reason": "operator approved recovery", "triggered_by": "test-operator"})
else:
    result = mcp_server._handle_kill_switch_engage({
        "mode": sys.argv[1], "confirm": True,
        "reason": "external emergency", "triggered_by": "test-operator"})
assert "error" not in result, result
"""
    subprocess.run([sys.executable, "-c", code, mode], env=env,
                   check=True, capture_output=True, text=True, timeout=10)


def test_existing_server_observes_governance_emergency_and_release(reader, state_env):
    """A signed external emergency blocks even critical tasks without a restart."""
    assert payload(reader("ks_check_task", {"task_name": "work"}))["allowed"]
    governance_transition(state_env, "EMERGENCY")
    assert payload(reader("ks_status"))["mode"] == "EMERGENCY"
    for task in ("work", "safety_monitoring"):
        decision = payload(reader("ks_check_task", {"task_name": task}))
        assert decision["allowed"] is False
        assert decision["action"] == "block"
    governance_transition(state_env, "DISENGAGED")
    assert payload(reader("ks_status"))["mode"] == "DISENGAGED"
    assert payload(reader("ks_check_task", {"task_name": "work"}))["allowed"]


def test_server_reverifies_and_recovers_only_from_signed_state(reader, state_env):
    """Bad or deleted state never permits work in an existing MCP process."""
    assert payload(reader("ks_status"))["mode"] == "DISENGAGED"
    governance_transition(state_env, "EMERGENCY")
    state = Path(state_env["GOVERNANCE_STATE_DIR"]) / "kill_switch_state.json"
    signed_emergency = state.read_bytes()
    invalid = json.loads(signed_emergency)
    invalid["mode"] = "DISENGAGED"
    state.write_text(json.dumps(invalid), encoding="utf-8")
    for name in ("ks_status", "ks_check_task", "ks_history"):
        result = reader(name, {"task_name": "work"})
        assert result.get("isError") is True
        assert "allowed" not in json.loads(result["content"][0]["text"])
    state.unlink()
    assert reader("ks_check_task", {"task_name": "work"}).get("isError") is True
    state.write_bytes(signed_emergency)
    assert payload(reader("ks_status"))["mode"] == "EMERGENCY"
    assert payload(reader("ks_check_task", {"task_name": "work"}))["allowed"] is False


@pytest.mark.parametrize("fault", ["missing_key", "wrong_key", "missing_state", "unsigned"])
def test_fresh_mcp_process_fails_closed(state_env, fault):
    """Restarting cannot bypass credential or state-integrity failures."""
    env = state_env.copy()
    state = Path(env["GOVERNANCE_STATE_DIR"]) / "kill_switch_state.json"
    if fault == "missing_key":
        env.pop("HUMMBL_SIGNING_SECRET")
    elif fault == "wrong_key":
        env["HUMMBL_SIGNING_SECRET"] = "incorrect-test-key"
    elif fault == "missing_state":
        state.unlink()
    else:
        data = json.loads(state.read_text())
        data.pop("signature")
        state.write_text(json.dumps(data), encoding="utf-8")
    before = state.read_bytes() if state.exists() else None
    requests = [
        {"id": i, "method": "tools/call", "params": {
            "name": name, "arguments": {"task_name": "work"},
        }}
        for i, name in enumerate(("ks_status", "ks_check_task", "ks_history"))
    ]
    run = subprocess.run(
        [sys.executable, "-m", "hummbl_mcp.mcp_kill_switch"], env=env,
        input="".join(json.dumps(r) + "\n" for r in requests),
        capture_output=True, text=True, check=True, timeout=10,
    )
    responses = [json.loads(line) for line in run.stdout.splitlines()]
    assert len(responses) == 3
    for response in responses:
        assert response["result"].get("isError") is True
        assert "allowed" not in json.loads(response["result"]["content"][0]["text"])
    assert (state.read_bytes() if state.exists() else None) == before


def test_dedicated_server_keeps_read_only_tool_boundary(reader):
    """The repair must not add a release or integrity-repair tool."""
    result = payload(reader("ks_disengage", {"confirm": True}))
    assert result == {"error": "Unknown tool: ks_disengage"}


def test_concurrent_writer_exposes_complete_signed_snapshots(reader, state_env):
    """Repeated cross-process replacements never expose a partial or allow state."""
    governance_transition(state_env, "EMERGENCY")
    code = """
import os
from pathlib import Path
from hummbl_governance.kill_switch import KillSwitch, KillSwitchMode
writer = KillSwitch.load_from_file(Path(os.environ["GOVERNANCE_STATE_DIR"]))
for i in range(80):
    mode = KillSwitchMode.HALT_ALL if i % 2 else KillSwitchMode.EMERGENCY
    writer.engage(mode, "concurrent transition", "test-operator")
"""
    writer = subprocess.Popen(
        [sys.executable, "-c", code], env=state_env,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    try:
        for _ in range(80):
            result = payload(reader("ks_check_task", {"task_name": "work"}))
            assert result["allowed"] is False
            assert result["action"] == "block"
        assert writer.wait(timeout=10) == 0
    finally:
        if writer.poll() is None:
            writer.kill()
            writer.wait(timeout=5)
