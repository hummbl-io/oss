"""Spark Gateway MCP Server.

Exposes a curated, read-only subset of HUMMBL capabilities to Spark.
Strictly blocks kill-switch and governance-bus access.
"""

from __future__ import annotations

import json
import logging
import sys
from typing import Any

from hummbl_mcp._auth import verify_token
from hummbl_mcp._constants import MCP_PROTOCOL_VERSION

logger = logging.getLogger(__name__)

SERVER_NAME = "spark-gateway"
SERVER_VERSION = "0.1.0"
PROTOCOL_VERSION = MCP_PROTOCOL_VERSION

MCP_TOOLS: list[dict[str, Any]] = [
    {
        "name": "gateway_status",
        "description": "Check Gateway connection status",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "fleet_health_summary",
        "description": "Get read-only fleet health summary",
        "inputSchema": {"type": "object", "properties": {}},
    }
]

# We will require initialization to pass an auth token in params.
is_authenticated = False

def handle_gateway_status() -> dict[str, Any]:
    return {"status": "connected", "mode": "read-only"}

def handle_fleet_health_summary() -> dict[str, Any]:
    try:
        from hummbl_mcp.mcp_fleet_health import MCPFleetMonitor

        status = MCPFleetMonitor.from_state().get_fleet_status()
        return {
            "status": status.fleet_status,
            "source": "mcp_fleet_health",
            "summary": status.summary,
            "score": status.score,
            "server_count": status.server_count,
            "healthy_count": status.healthy_count,
            "degraded_count": status.degraded_count,
            "unhealthy_count": status.unhealthy_count,
            "disabled_count": status.disabled_count,
        }
    except Exception as e:
        logger.warning("Fleet health summary unavailable: %s", e)
        return {
            "status": "unknown",
            "source": "mcp_fleet_health",
            "error": "Fleet health summary unavailable",
        }

def handle_tool(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    if not is_authenticated:
        return {"error": "Unauthorized. Call initialize with valid token."}

    if name == "gateway_status":
        return handle_gateway_status()
    elif name == "fleet_health_summary":
        return handle_fleet_health_summary()

    return {"error": f"Unknown tool: {name}"}

def _rpc_result(id_: Any, result: Any) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": id_, "result": result}

def _rpc_error(id_: Any, code: int, message: str) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": id_, "error": {"code": code, "message": message}}

def handle_request(request: dict[str, Any]) -> dict[str, Any] | None:
    global is_authenticated
    method = request.get("method", "")
    id_ = request.get("id")
    params = request.get("params", {})

    if method == "initialize":
        # Check auth in initialization params (custom extension for Gateway)
        token = params.get("clientInfo", {}).get("token", "")
        try:
            verify_token(token)
            is_authenticated = True
        except Exception as e:
            return _rpc_error(id_, -32000, f"Authentication failed: {e}")

        return _rpc_result(id_, {
            "protocolVersion": PROTOCOL_VERSION,
            "capabilities": {"tools": {}},
            "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
        })

    if not is_authenticated and method != "ping":
        return _rpc_error(id_, -32000, "Not authenticated")

    if method == "tools/list":
        return _rpc_result(id_, {"tools": MCP_TOOLS})

    if method == "tools/call":
        tool_name = params.get("name", "")
        arguments = params.get("arguments", {})

        # Hard-block sensitive tools
        if tool_name in ["ks_status", "ks_check_task", "cost_check"]:
            return _rpc_result(id_, {
                "content": [{"type": "text", "text": json.dumps({"error": "Blocked by Gateway Policy"})}],
                "isError": True,
            })

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
