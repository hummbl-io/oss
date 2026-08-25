#!/usr/bin/env python3
"""MCP Server for Working Memory (ephemeral mid-session state).

Exposes the WorkingMemoryStore as MCP tools via stdio JSON-RPC 2.0.
Provides get, put, list, delete, promote-to-ledger, and stats operations
for multi-agent ephemeral coordination state with TTL-based expiry.

Zero third-party dependencies. Uses only Python stdlib + hummbl_cognition.
"""
from __future__ import annotations

import json
import sys
import traceback
from typing import Any

SERVER_NAME = "working-memory"
SERVER_VERSION = "0.1.0"

from hummbl_cognition.working_memory import WorkingMemoryStore

store = WorkingMemoryStore()

# ---------------------------------------------------------------------------
# Tool definitions
# ---------------------------------------------------------------------------
_TOOLS = [
    {
        "name": "memory_get",
        "description": "Retrieve a working memory item by key. Keys are formatted as 'agent:topic' (e.g., 'claude-code:hypothesis.1'). Returns null if not found or expired.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "key": {"type": "string", "description": "Namespaced key (agent:topic)"},
            },
            "required": ["key"],
        },
    },
    {
        "name": "memory_put",
        "description": "Store or update a working memory item with TTL-based expiry. Key must be 'agent:topic' format where agent prefix matches the agent parameter. Max TTL 86400s (24h).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "key": {"type": "string", "description": "Namespaced key (agent:topic)"},
                "value": {"description": "JSON-serializable value to store"},
                "agent": {"type": "string", "description": "Agent identifier (must match key prefix)"},
                "ttl_seconds": {"type": "integer", "description": "Time-to-live in seconds (default: 3600, max: 86400)", "default": 3600},
                "metadata": {"type": "object", "description": "Optional metadata dict"},
            },
            "required": ["key", "value", "agent"],
        },
    },
    {
        "name": "memory_list",
        "description": "List all non-expired working memory items, optionally filtered by agent.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "agent": {"type": "string", "description": "Filter by agent (optional)"},
            },
        },
    },
    {
        "name": "memory_delete",
        "description": "Delete a working memory item. Only the owning agent can delete.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "key": {"type": "string", "description": "Key to delete"},
                "agent": {"type": "string", "description": "Agent requesting deletion (must own the item)"},
            },
            "required": ["key", "agent"],
        },
    },
    {
        "name": "memory_promote",
        "description": "Promote a working memory item to the permanent cognitive ledger. Returns a dict suitable for constructing a LedgerEntry.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "key": {"type": "string", "description": "Key to promote"},
                "agent": {"type": "string", "description": "Agent requesting promotion (must own the item)"},
            },
            "required": ["key", "agent"],
        },
    },
    {
        "name": "memory_stats",
        "description": "Return statistics about the working memory store: item count, expired count, agent breakdown, version, session ID.",
        "inputSchema": {
            "type": "object",
            "properties": {},
        },
    },
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _ok(text: str) -> dict[str, Any]:
    return {"content": [{"type": "text", "text": text}]}


def _err(msg: str) -> dict[str, Any]:
    return {"content": [{"type": "text", "text": msg}], "isError": True}


# ---------------------------------------------------------------------------
# Tool dispatch
# ---------------------------------------------------------------------------
def _handle_call(name: str, args: dict[str, Any]) -> dict[str, Any]:
    try:
        if name == "memory_get":
            key = args.get("key", "")
            if not key:
                return _err("Missing required parameter: key")
            item = store.get(key)
            if item is None:
                return _ok(json.dumps({"found": False, "key": key}))
            return _ok(json.dumps({"found": True, "item": item.to_dict()}, indent=2))

        elif name == "memory_put":
            key = args.get("key", "")
            value = args.get("value")
            agent = args.get("agent", "")
            if not key or not agent:
                return _err("Missing required parameters: key, agent")
            if value is None:
                return _err("Missing required parameter: value")
            ttl = args.get("ttl_seconds", 3600)
            metadata = args.get("metadata")
            item = store.put(
                key=key,
                value=value,
                agent=agent,
                ttl_seconds=ttl,
                metadata=metadata,
            )
            return _ok(json.dumps({"stored": True, "item": item.to_dict()}, indent=2))

        elif name == "memory_list":
            agent = args.get("agent")
            items = store.get_all(agent=agent)
            result = [item.to_dict() for item in items]
            return _ok(json.dumps({"count": len(result), "items": result}, indent=2))

        elif name == "memory_delete":
            key = args.get("key", "")
            agent = args.get("agent", "")
            if not key or not agent:
                return _err("Missing required parameters: key, agent")
            store.delete(key=key, agent=agent)
            return _ok(json.dumps({"deleted": True, "key": key}))

        elif name == "memory_promote":
            key = args.get("key", "")
            agent = args.get("agent", "")
            if not key or not agent:
                return _err("Missing required parameters: key, agent")
            result = store.promote_to_ledger(key=key, agent=agent)
            return _ok(json.dumps({"promoted": True, "ledger_entry": result}, indent=2))

        elif name == "memory_stats":
            stats = store.stats()
            return _ok(json.dumps(stats, indent=2))

        else:
            return _err(f"Unknown tool: {name}")

    except Exception as exc:
        return _err(f"Error in {name}: {exc}\n{traceback.format_exc()}")


# ---------------------------------------------------------------------------
# JSON-RPC stdio server
# ---------------------------------------------------------------------------
def serve_stdio() -> None:
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except json.JSONDecodeError:
            sys.stdout.write(
                json.dumps({
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {"code": -32700, "message": "Parse error"},
                }) + "\n"
            )
            sys.stdout.flush()
            continue

        rid = req.get("id")
        method = req.get("method", "")
        params = req.get("params") or {}

        if method == "initialize":
            result = {
                "capabilities": {"tools": {}},
                "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
            }
        elif method == "notifications/initialized":
            continue
        elif method == "tools/list":
            result = {"tools": _TOOLS}
        elif method == "tools/call":
            result = _handle_call(
                params.get("name", ""),
                params.get("arguments") or {},
            )
        else:
            sys.stdout.write(
                json.dumps({
                    "jsonrpc": "2.0",
                    "id": rid,
                    "error": {"code": -32601, "message": f"Unknown: {method}"},
                }) + "\n"
            )
            sys.stdout.flush()
            continue

        if rid is not None:
            sys.stdout.write(
                json.dumps({"jsonrpc": "2.0", "id": rid, "result": result}) + "\n"
            )
            sys.stdout.flush()


if __name__ == "__main__":
    serve_stdio()
