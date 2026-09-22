"""Exercise real UTF-8 MCP stdio against an isolated, temporary local bus.

The local persistence fixture starts in UTF-8; ping regressions also force
other initial stream encodings to exercise the server's reconfiguration.
Bridge calls are stubbed before main(), inherited bus routing/credentials
are removed, and a socket audit guard terminates the child on network attempts.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


_NETWORK_DENIED_EXIT = 97
_CHILD_BOOTSTRAP = r"""
import os
import sys

def deny_network(event, args):
    if event in {"socket.__new__", "socket.connect", "socket.bind",
                 "socket.getaddrinfo", "socket.gethostbyname", "socket.sendto"}:
        os.write(2, b"MCP fixture network access denied\n")
        os._exit(97)  # Cannot be swallowed by a bridge fallback's except block.

sys.addaudithook(deny_network)
if sys.argv[2] == "probe-network-guard":
    import socket
    socket.socket()  # Guard must terminate before allocating a socket.
    raise AssertionError("network guard did not terminate the child")

sys.path.insert(0, sys.argv[1])
from hummbl_bus import mcp_server

mcp_server._bridge_post = lambda *args, **kwargs: (False, "isolated local fixture")
mcp_server._bridge_get = lambda *args, **kwargs: (False, "isolated local fixture")
if sys.argv[3]:
    for stream in (sys.stdin, sys.stdout):
        stream.reconfigure(encoding=sys.argv[3], errors="strict")

if sys.argv[2] == "serve-memory":
    import io
    original_stdout = sys.stdout
    sys.stdin = io.StringIO(sys.stdin.buffer.read().decode("utf-8"))
    sys.stdout = io.StringIO()
    mcp_server.main()
    original_stdout.write(sys.stdout.getvalue())
    original_stdout.flush()
else:
    mcp_server.main()
"""


def _isolated_env(tmp_path: Path) -> dict[str, str]:
    env = {
        key: value
        for key, value in os.environ.items()
        if not key.upper().startswith(("BUS_", "COORDINATION"))
    }
    env.update(
        BUS_FILE=str(tmp_path / "messages.tsv"),
        BUS_BRIDGE_TOKEN_PATH=str(tmp_path / "absent-tokens" / "token"),
        BUS_ALLOWED_ROOTS=str(tmp_path),
        BUS_SECURITY_POLICY="permissive",
        BUS_ORIGIN_MACHINE="unknown",
        BUS_ORIGIN_SURFACE="test",
        FM_TEST_MODE="1",
    )
    return env


def _run_isolated_server(
    tmp_path: Path,
    requests: bytes,
    *,
    probe: bool = False,
    initial_encoding: str | None = None,
    memory_streams: bool = False,
):
    package_src = Path(__file__).resolve().parents[1] / "src"
    mode = "probe-network-guard" if probe else "serve-memory" if memory_streams else "serve"
    return subprocess.run(
        [
            sys.executable, "-I", "-S", "-B", "-X", "utf8", "-c", _CHILD_BOOTSTRAP,
            str(package_src), mode, initial_encoding or "",
        ],
        input=requests,
        capture_output=True,
        env=_isolated_env(tmp_path),
        cwd=tmp_path,
        timeout=30,
    )


def _rpc(msg_id: int | str, method: str, params: dict | None = None) -> bytes:
    """Build a JSON-RPC request as UTF-8 bytes."""
    msg = {"jsonrpc": "2.0", "id": msg_id, "method": method}
    if params is not None:
        msg["params"] = params
    return (json.dumps(msg, ensure_ascii=False) + "\n").encode("utf-8")


def _parse_responses(stdout_bytes: bytes) -> list[dict]:
    """Parse newline-delimited JSON-RPC responses from stdout bytes."""
    results = []
    for line in stdout_bytes.decode("utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            results.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return results


def test_mcp_stdio_network_guard_fails_closed(tmp_path: Path) -> None:
    proc = _run_isolated_server(tmp_path, b"", probe=True)
    assert proc.returncode == _NETWORK_DENIED_EXIT
    assert b"MCP fixture network access denied" in proc.stderr
    assert not (tmp_path / "messages.tsv").exists()


@pytest.mark.parametrize("initial_encoding", ["cp1252", "ascii", "utf-8"])
def test_mcp_stdio_reconfigures_initial_encoding(tmp_path: Path, initial_encoding: str) -> None:
    """A raw UTF-8 request retains its Unicode ID under every initial encoding."""
    msg_id = "caf\u00e9 \u2014 \u65e5\u672c"
    request = _rpc(msg_id, "ping")
    assert msg_id.encode("utf-8") in request

    proc = _run_isolated_server(tmp_path, request, initial_encoding=initial_encoding)

    assert proc.returncode == 0, proc.stderr.decode("utf-8", errors="replace")
    assert json.loads(proc.stdout.decode("utf-8")) == {
        "jsonrpc": "2.0", "id": msg_id, "result": {},
    }
    assert not (tmp_path / "messages.tsv").exists()


def test_mcp_stdio_accepts_stringio_streams(tmp_path: Path) -> None:
    """Embedding main() with in-memory streams requires no reconfigure method."""
    msg_id = "caf\u00e9 \u2014 \u65e5\u672c"

    proc = _run_isolated_server(tmp_path, _rpc(msg_id, "ping"), memory_streams=True)

    assert proc.returncode == 0, proc.stderr.decode("utf-8", errors="replace")
    assert json.loads(proc.stdout.decode("utf-8")) == {
        "jsonrpc": "2.0", "id": msg_id, "result": {},
    }
    assert not (tmp_path / "messages.tsv").exists()


def test_mcp_stdio_preserves_non_ascii_round_trip(tmp_path: Path, monkeypatch) -> None:
    """Round-trip actual UTF-8 stdin bytes through an explicitly local bus."""
    bus_file = tmp_path / "messages.tsv"
    em_dash = "\u2014"  # —
    test_message = f"primitives/ {em_dash} caf\u00e9 \u201cdefinitions\u201d"

    # Build the JSON-RPC request sequence: initialize, post, read
    requests = b""
    requests += _rpc(1, "initialize")
    requests += _rpc(
        2,
        "tools/call",
        {
            "name": "bus_post",
            "arguments": {
                "from_agent": "test-mcp-encoding",
                "to": "all",
                "type": "STATUS",
                "message": test_message,
            },
        },
    )
    requests += _rpc(
        3,
        "tools/call",
        {"name": "bus_read", "arguments": {"limit": 5}},
    )

    # Prove both MCP bridge and bus_writer forwarding inputs are scrubbed.
    for key in ("BUS_BRIDGE_TOKEN", "BUS_SENDER_TOKEN_PATH_TEST_MCP_ENCODING",
                "BUS_REMOTE_URL", "BUS_CANONICAL_BRIDGE_URL", "COORDINATION_BUS"):
        monkeypatch.setenv(key, "inherited-fixture-value-must-not-reach-child")
    assert "inherited-fixture-value-must-not-reach-child" not in _isolated_env(tmp_path).values()
    assert em_dash.encode("utf-8") in requests  # Not merely ASCII \\u2014 JSON.
    proc = _run_isolated_server(tmp_path, requests)

    assert proc.returncode == 0, f"MCP server exited {proc.returncode}: {proc.stderr.decode('utf-8', errors='replace')}"

    responses = _parse_responses(proc.stdout)
    assert {response.get("id") for response in responses} == {1, 2, 3}
    assert all("error" not in response for response in responses), responses
    post_response = next(response for response in responses if response["id"] == 2)
    posted = json.loads(post_response["result"]["content"][0]["text"])
    assert posted["posted"] is True
    assert posted["method"] == "local_fallback"

    # Verify the bus file contains the em-dash, not mojibake
    raw = bus_file.read_bytes()
    decoded = raw.decode("utf-8")
    assert len(decoded.splitlines()) == 1
    assert decoded.rstrip("\r\n").endswith(test_message)
    assert em_dash in decoded, (
        f"Em-dash not found in bus file. "
        f"Expected U+2014 in: {decoded!r}"
    )
    # Explicitly check for the CP1252 mojibake pattern
    mojibake = "\u00e2\u20ac\u201d"  # â€"
    assert mojibake not in decoded, (
        f"CP1252 mojibake detected in bus file: {decoded!r}"
    )

    # Verify the bus_read response contains the em-dash. The MCP server
    # uses json.dumps with default ensure_ascii=True, so the em-dash is
    # escaped as \u2014 in the outer JSON. We parse the nested content
    # to check the actual string value.
    read_response = None
    for resp in responses:
        if resp.get("id") == 3:
            read_response = resp
            break
    assert read_response is not None, f"bus_read response not found in {responses}"
    # The result content is a list of {type: "text", text: "<json string>"}
    content = read_response["result"]["content"]
    inner = json.loads(content[0]["text"])
    messages = inner["messages"]
    assert len(messages) == 1, f"Expected only the temporary fixture row: {inner}"
    assert messages[0]["message"] == f"host=unknown {test_message}"
