"""Kill Switch MCP Server -- expose emergency halt state via JSON-RPC.

Safety-critical MCP server. Agents query this to check if their task
is allowed before executing. READ-ONLY by default — engage/disengage
requires explicit tool call with confirmation.

Stdlib-only. No third-party dependencies.

Usage:
    python -m hummbl_mcp.mcp_kill_switch
"""

from __future__ import annotations

import json
import logging
import sys
from typing import Any

try:
    from hummbl_governance.kill_switch import (
        get_kill_switch_core,
    )
except ImportError:
    pass

logger = logging.getLogger(__name__)

SERVER_NAME = "kill-switch"
SERVER_VERSION = "0.1.0"
PROTOCOL_VERSION = "2024-11-05"

MCP_TOOLS: list[dict[str, Any]] = [
    {
        "name": "ks_status",
        "description": "Get current kill switch state (mode, engaged, critical tasks)",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "ks_check_task",
        "description": "Check if a specific task is allowed under current kill switch state",
        "inputSchema": {
            "type": "object",
            "properties": {
                "task_name": {
                    "type": "string",
                    "description": "Task name to check (e.g. 'briefing_generation', 'safety_monitoring')",
                },
            },
            "required": ["task_name"],
        },
    },
    {
        "name": "ks_history",
        "description": "Get recent kill switch state transitions",
        "inputSchema": {
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "description": "Max events to return (default 10)"},
            },
        },
    },
]


def handle_ks_status() -> dict[str, Any]:
    """Get current kill switch state."""
    ks = get_kill_switch_core()
    status = ks.get_status()
    return {
        "mode": status.get("mode", "UNKNOWN"),
        "engaged": status.get("engaged", False),
        "critical_tasks": sorted(ks.CRITICAL_TASKS) if hasattr(ks, "CRITICAL_TASKS") else [],
        "state_file": str(ks._state_file) if hasattr(ks, "_state_file") else None,
    }


def handle_ks_check_task(task_name: str) -> dict[str, Any]:
    """Check if a task is allowed."""
    ks = get_kill_switch_core()
    result = ks.check_task_allowed(task_name)
    return {
        "task": task_name,
        "allowed": result.get("allowed", False),
        "action": result.get("action", "unknown"),
        "reason": result.get("reason", result.get("note", "")),
    }


def handle_ks_history(limit: int = 10) -> dict[str, Any]:
    """Get recent state transitions."""
    ks = get_kill_switch_core()
    events = []
    if hasattr(ks, "_event_history"):
        for event in ks._event_history[-limit:]:
            events.append({
                "mode": str(event.mode) if hasattr(event, "mode") else str(event),
                "timestamp": str(event.timestamp) if hasattr(event, "timestamp") else None,
            })
    return {"events": events, "count": len(events)}


def handle_tool(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    if name == "ks_status":
        return handle_ks_status()
    elif name == "ks_check_task":
        return handle_ks_check_task(arguments["task_name"])
    elif name == "ks_history":
        return handle_ks_history(arguments.get("limit", 10))
    return {"error": f"Unknown tool: {name}"}


def _rpc_result(id_: Any, result: Any) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": id_, "result": result}


def _rpc_error(id_: Any, code: int, message: str) -> dict[str, Any]:
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
    if method == "notifications/initialized":
        return None
    if method == "ping":
        return _rpc_result(id_, {})
    return _rpc_error(id_, -32601, f"Method not found: {method}")


def main() -> None:  # pragma: no cover
    logging.basicConfig(level=logging.INFO, stream=sys.stderr)
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
