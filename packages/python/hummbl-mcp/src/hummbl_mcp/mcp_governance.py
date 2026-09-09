"""Governance Bus MCP Server -- expose IDP audit log via JSON-RPC.

Compliance-critical MCP server. Provides query access to the append-only
JSONL governance audit log (delegation tokens, scope verification, etc).

Stdlib-only. No third-party dependencies.

Usage:
    python -m hummbl_mcp.mcp_governance
"""

from __future__ import annotations

import json
import logging
import sys
from typing import Any

from hummbl_mcp._governance_bus import (
    _is_idp_enabled,
    get_governance_bus,
)

logger = logging.getLogger(__name__)

SERVER_NAME = "governance-bus"
SERVER_VERSION = "0.2.0"
PROTOCOL_VERSION = "2024-11-05"

# Tuple types expected to appear in a complete delegation chain
_CHAIN_TUPLE_TYPES = ("CONTRACT", "DCTX", "EVIDENCE")

MCP_TOOLS: list[dict[str, Any]] = [
    {
        "name": "gov_query",
        "description": "Query governance audit entries by intent_id (omit to scan all)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "intent": {"type": "string", "description": "Filter by intent_id (exact match)"},
                "limit": {"type": "integer", "description": "Max entries (default 20)"},
            },
        },
    },
    {
        "name": "gov_stats",
        "description": "Get governance bus statistics (entry count, tuple type breakdown, IDP enabled flag)",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "gov_recent",
        "description": "Get the N most recent governance entries (ordered by timestamp desc)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "description": "Number of entries (default 10, minimum 1)"},
            },
        },
    },
    {
        "name": "gov_trace_contract",
        "description": (
            "Trace a delegation chain by contract_id. Returns linked entries grouped "
            "by tuple_type; 'complete' is true only when CONTRACT, DCTX, and EVIDENCE "
            "are all present."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "contract_id": {"type": "string", "description": "Contract ID to trace"},
            },
            "required": ["contract_id"],
        },
    },
]


def _all_entries(gb: Any) -> list[Any]:
    """Materialize gb.query_all() to a list (gated by ENABLE_IDP).

    Returns [] when IDP is disabled, since query_all() yields nothing.
    """
    return list(gb.query_all())


def handle_gov_query(intent: str | None = None, limit: int = 20) -> dict[str, Any]:
    try:
        limit = max(1, int(limit))
    except (TypeError, ValueError):
        limit = 20
    gb = get_governance_bus()
    try:
        if intent:
            entries = list(gb.query_by_intent(intent))
        else:
            entries = _all_entries(gb)
        entries = entries[:limit]
        return {
            "entries": [_entry_to_dict(e) for e in entries],
            "count": len(entries),
            "filter": intent,
        }
    except Exception as e:
        return {"entries": [], "count": 0, "error": str(e)}


def handle_gov_stats() -> dict[str, Any]:
    gb = get_governance_bus()
    try:
        all_entries = _all_entries(gb)
        types: dict[str, int] = {}
        for entry in all_entries:
            t = _get_field(entry, "tuple_type") or "unknown"
            types[t] = types.get(t, 0) + 1
        return {
            "total_entries": len(all_entries),
            "tuple_types": types,
            "enabled": _is_idp_enabled(),
        }
    except Exception as e:
        return {"total_entries": 0, "error": str(e)}


def handle_gov_recent(limit: int = 10) -> dict[str, Any]:
    try:
        limit = max(1, int(limit))
    except (TypeError, ValueError):
        limit = 10
    gb = get_governance_bus()
    try:
        entries = _all_entries(gb)
        # Sort by timestamp desc; entries lacking timestamp sink to the end.
        entries.sort(key=lambda e: _get_field(e, "timestamp") or "", reverse=True)
        recent = entries[:limit]
        return {"entries": [_entry_to_dict(e) for e in recent], "count": len(recent)}
    except Exception as e:
        return {"entries": [], "count": 0, "error": str(e)}


def handle_gov_trace_contract(contract_id: str) -> dict[str, Any]:
    gb = get_governance_bus()
    try:
        chain = list(gb.query_by_contract(contract_id))
        chain.sort(key=lambda e: _get_field(e, "timestamp") or "")
        present_types = {_get_field(e, "tuple_type") for e in chain}
        missing = [t for t in _CHAIN_TUPLE_TYPES if t not in present_types]
        return {
            "contract_id": contract_id,
            "chain_length": len(chain),
            "entries": [_entry_to_dict(e) for e in chain],
            "tuple_types_present": sorted(t for t in present_types if t),
            "missing_tuple_types": missing,
            "complete": len(missing) == 0 and len(chain) > 0,
        }
    except Exception as e:
        return {"contract_id": contract_id, "chain_length": 0, "error": str(e)}


def _entry_to_dict(entry: Any) -> dict[str, Any]:
    if isinstance(entry, dict):
        return entry
    if hasattr(entry, "__dict__"):
        return {k: str(v) for k, v in entry.__dict__.items() if not k.startswith("_")}
    return {"raw": str(entry)}


def _get_field(entry: Any, field: str) -> str:
    if isinstance(entry, dict):
        return entry.get(field, "")
    return getattr(entry, field, "")


def handle_tool(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    if name == "gov_query":
        return handle_gov_query(arguments.get("intent"), arguments.get("limit", 20))
    elif name == "gov_stats":
        return handle_gov_stats()
    elif name == "gov_recent":
        return handle_gov_recent(arguments.get("limit", 10))
    elif name == "gov_trace_contract" or name == "gov_verify_chain":
        # gov_verify_chain retained as alias for backwards compatibility.
        return handle_gov_trace_contract(arguments["contract_id"])
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
                "content": [{"type": "text", "text": json.dumps(result, indent=2, default=str)}],
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
            sys.stdout.write(json.dumps(response, default=str) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":  # pragma: no cover
    main()
