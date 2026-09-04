"""Regression test for MCP server stdio encoding.

Verifies that the MCP server correctly handles non-ASCII UTF-8 content in
JSON-RPC payloads. On Windows, sys.stdin/sys.stdout default to CP1252,
which corrupts non-ASCII bytes (em-dashes, smart quotes, accented
characters) via mojibake before json.loads ever sees them. The fix
reconfigures stdio to UTF-8 at the start of main().

Origin: 2026-09-02 session -- bus_post encoding corruption on Windows
(anvil, CP1252 system codepage). Em-dash U+2014 (UTF-8: E2 80 94) was
decoded as CP1252 (C3 A2 E2 82 AC E2 80 9D = a-EUR-quot) then re-encoded
as UTF-8 for storage, producing mojibake in messages.tsv.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


def _rpc(msg_id: int | str, method: str, params: dict | None = None) -> bytes:
    """Build a JSON-RPC request as UTF-8 bytes."""
    msg = {"jsonrpc": "2.0", "id": msg_id, "method": method}
    if params is not None:
        msg["params"] = params
    return (json.dumps(msg) + "\n").encode("utf-8")


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


def test_mcp_stdio_preserves_non_ascii_round_trip(tmp_path: Path) -> None:
    """Post a message with an em-dash via the MCP server subprocess and
    verify it round-trips without CP1252 mojibake.

    The test sends UTF-8 bytes to the subprocess stdin (mimicking what a
    real MCP client does). Without the UTF-8 reconfigure fix, Windows
    decodes the em-dash bytes as CP1252, corrupting the content before
    json.loads sees it.
    """
    bus_file = tmp_path / "messages.tsv"
    em_dash = "\u2014"  # —
    test_message = f"primitives/ {em_dash} formal definitions"

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

    env = os.environ.copy()
    env["BUS_FILE"] = str(bus_file)
    env["FM_TEST_MODE"] = "1"  # relax sender identity validation for test agent

    # Spawn the MCP server. We must send/receive raw bytes -- if we let
    # subprocess decode through the system codepage we'd reproduce the
    # very bug we're testing.
    proc = subprocess.run(
        [sys.executable, "-m", "hummbl_bus.mcp_server"],
        input=requests,
        capture_output=True,
        env=env,
        timeout=30,
    )

    assert proc.returncode == 0, f"MCP server exited {proc.returncode}: {proc.stderr.decode('utf-8', errors='replace')}"

    responses = _parse_responses(proc.stdout)
    assert len(responses) >= 2, f"Expected >=2 responses, got {len(responses)}: {responses}"

    # Verify the bus file contains the em-dash, not mojibake
    raw = bus_file.read_bytes()
    decoded = raw.decode("utf-8")
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
    assert len(messages) >= 1, f"No messages in bus_read response: {inner}"
    assert em_dash in messages[0]["message"], (
        f"Em-dash not in read-back message. "
        f"Got: {messages[0]['message']!r}"
    )
