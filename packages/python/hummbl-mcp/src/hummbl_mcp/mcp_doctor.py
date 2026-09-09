"""Lead Doctor MCP Server -- expose system health via JSON-RPC (MCP stdio).

Tools exposed:
  doctor_check    -- Run a fresh health check. Returns current status + all probe results.
  doctor_history  -- Return N most recent health snapshots.
  doctor_trend    -- Uptime stats + chronic issues over a time window.
  doctor_probes   -- Return status of specific probes (by name).

Usage:
    python -m hummbl_mcp.mcp_doctor

Add to .mcp.json:
    "doctor": {
        "command": "/path/to/venv/bin/python",
        "args": ["-m", "hummbl_mcp.mcp_doctor"]
    }
"""

from __future__ import annotations

import json
import logging
import sys
from typing import Any

logger = logging.getLogger(__name__)

SERVER_NAME = "lead-doctor"
SERVER_VERSION = "0.1.0"
PROTOCOL_VERSION = "2024-11-05"

MCP_TOOLS: list[dict[str, Any]] = [
    {
        "name": "doctor_check",
        "description": (
            "Run a fresh system health check. Returns overall status (healthy/degraded/unhealthy), "
            "per-probe statuses and messages, and whether any probes changed since last check."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "json": {
                    "type": "boolean",
                    "description": "Return raw JSON dict instead of formatted text (default: false)",
                }
            },
        },
    },
    {
        "name": "doctor_history",
        "description": "Return recent health snapshots in reverse-chronological order.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": "Max snapshots to return (default: 20)",
                }
            },
        },
    },
    {
        "name": "doctor_trend",
        "description": (
            "Uptime statistics over a rolling window: healthy%, degraded%, unhealthy%, "
            "MTTR, chronic probe failures, and remediation hints."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "hours": {
                    "type": "number",
                    "description": "Window size in hours (default: 24)",
                }
            },
        },
    },
    {
        "name": "doctor_probes",
        "description": (
            "Return status + message for one or more specific probes by name. "
            "Use doctor_check first to see probe names."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "names": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Probe names to inspect, e.g. ['signal', 'coordination_bus']",
                }
            },
            "required": ["names"],
        },
    },
]


# ---------------------------------------------------------------------------
# Handlers
# ---------------------------------------------------------------------------

def _get_doctor():
    """Return a LeadDoctor instance (bus posting disabled for read-only MCP use)."""
    from hummbl_mcp._lead_doctor import LeadDoctor
    # Disable bus posting from MCP context — the real watcher handles that.
    # Set cooldowns to a very large number so MCP checks never spam the bus.
    return LeadDoctor(bus_cooldown_seconds=86400, global_bus_cooldown_seconds=86400)


def handle_doctor_check(args: dict) -> dict[str, Any]:
    doc = _get_doctor()
    snapshot = doc.check()
    return {
        "timestamp": snapshot.timestamp,
        "overall_status": snapshot.overall_status,
        "transition": snapshot.transition,
        "changed_probes": snapshot.changed_probes,
        "probe_statuses": snapshot.probe_statuses,
        "probe_messages": snapshot.probe_messages,
    }


def handle_doctor_history(args: dict) -> list[dict[str, Any]]:
    doc = _get_doctor()
    limit = int(args.get("limit", 20))
    snapshots = doc.get_history(limit=limit)
    return [
        {
            "timestamp": s.timestamp,
            "overall_status": s.overall_status,
            "transition": s.transition,
            "changed_probes": s.changed_probes,
        }
        for s in snapshots
    ]


def handle_doctor_trend(args: dict) -> dict[str, Any]:
    doc = _get_doctor()
    hours = int(args.get("hours", 24))
    return doc.get_trend_summary(hours=hours)


def handle_doctor_probes(args: dict) -> dict[str, Any]:
    doc = _get_doctor()
    names = args.get("names", [])
    snapshot = doc.check()
    result = {}
    for name in names:
        status = snapshot.probe_statuses.get(name)
        message = snapshot.probe_messages.get(name)
        if status is None:
            result[name] = {"status": "unknown", "message": f"No probe named '{name}'"}
        else:
            result[name] = {"status": status, "message": message or ""}
    return result


def handle_tool(name: str, arguments: dict) -> Any:
    if name == "doctor_check":
        return handle_doctor_check(arguments)
    if name == "doctor_history":
        return handle_doctor_history(arguments)
    if name == "doctor_trend":
        return handle_doctor_trend(arguments)
    if name == "doctor_probes":
        return handle_doctor_probes(arguments)
    raise ValueError(f"Unknown tool: {name}")


# ---------------------------------------------------------------------------
# JSON-RPC plumbing (matches existing MCP server pattern in this repo)
# ---------------------------------------------------------------------------

def _rpc_result(id_: Any, result: Any) -> dict:
    return {"jsonrpc": "2.0", "id": id_, "result": result}


def _rpc_error(id_: Any, code: int, message: str) -> dict:
    return {"jsonrpc": "2.0", "id": id_, "error": {"code": code, "message": message}}


def handle_request(request: dict[str, Any]) -> dict[str, Any] | None:
    method = request.get("method", "")
    id_ = request.get("id")
    params = request.get("params", {})

    if method == "initialize":
        return _rpc_result(id_, {
            "protocolVersion": PROTOCOL_VERSION,
            "capabilities": {"tools": {}},
            "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
        })
    if method == "tools/list":
        return _rpc_result(id_, {"tools": MCP_TOOLS})
    if method == "tools/call":
        tool_name = params.get("name", "")
        arguments = params.get("arguments", {})
        try:
            result = handle_tool(tool_name, arguments)
            return _rpc_result(id_, {
                "content": [{"type": "text", "text": json.dumps(result, indent=2)}],
            })
        except Exception as e:
            logger.exception("Tool call failed: %s", tool_name)
            return _rpc_result(id_, {
                "content": [{"type": "text", "text": json.dumps({"error": str(e)})}],
                "isError": True,
            })
    if method in ("notifications/initialized", "notifications/cancelled"):
        return None
    if method == "ping":
        return _rpc_result(id_, {})
    return _rpc_error(id_, -32601, f"Method not found: {method}")


def main() -> None:  # pragma: no cover
    logging.basicConfig(level=logging.WARNING, stream=sys.stderr)
    logger.info("Starting %s v%s", SERVER_NAME, SERVER_VERSION)
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            request = json.loads(line)
        except json.JSONDecodeError:
            sys.stdout.write(json.dumps(_rpc_error(None, -32700, "Parse error")) + "\n")
            sys.stdout.flush()
            continue
        response = handle_request(request)
        if response is not None:
            sys.stdout.write(json.dumps(response) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":  # pragma: no cover
    main()
