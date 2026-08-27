#!/usr/bin/env python3
"""MCP Server for Cognitive State (shared multi-agent coordination state).

Exposes read_state, update_agent_status, claim_file, release_file, and flags
operations as MCP tools via stdio JSON-RPC 2.0. Atomic writes with optimistic
concurrency control.

Zero third-party dependencies. Uses only Python stdlib + hummbl_cognition.
"""

from __future__ import annotations

import json
import sys
import traceback
from typing import Any

SERVER_NAME = "cognitive-state"
SERVER_VERSION = "0.1.0"

from hummbl_cognition.state_manager import (
    claim_file,
    read_state,
    release_file,
    update_agent_status,
    write_state,
)

# ---------------------------------------------------------------------------
# Tool definitions
# ---------------------------------------------------------------------------
_TOOLS = [
    {
        "name": "state_read",
        "description": "Read the current shared cognitive state. Returns version, active agents, claimed files, decisions, sprint, and flags as JSON.",
        "inputSchema": {
            "type": "object",
            "properties": {},
        },
    },
    {
        "name": "state_update_agent",
        "description": "Update a specific agent's status in the shared state. Creates the agent entry if it doesn't exist.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "agent_id": {
                    "type": "string",
                    "description": "Agent identifier (e.g., 'claude-code', 'codex')",
                },
                "status": {
                    "type": "string",
                    "description": "Agent status (e.g., 'active', 'idle', 'blocked')",
                },
                "vendor": {"type": "string", "description": "Agent vendor (optional)"},
                "model": {"type": "string", "description": "Agent model (optional)"},
            },
            "required": ["agent_id", "status"],
        },
    },
    {
        "name": "state_claim_file",
        "description": "Claim exclusive access to a file. Prevents other agents from modifying it concurrently. Fails if already claimed by a different agent.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path to claim"},
                "agent_id": {
                    "type": "string",
                    "description": "Agent claiming the file",
                },
                "purpose": {
                    "type": "string",
                    "description": "Why the file is being claimed (optional)",
                    "default": "",
                },
            },
            "required": ["path", "agent_id"],
        },
    },
    {
        "name": "state_release_file",
        "description": "Release exclusive file access. Only the claiming agent can release (or use agent_id='*' to force).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path to release"},
                "agent_id": {
                    "type": "string",
                    "description": "Agent releasing the file",
                },
            },
            "required": ["path", "agent_id"],
        },
    },
    {
        "name": "state_flags",
        "description": "Read or set flags in the shared state. If value is omitted, returns the current value of the flag. If value is provided, sets the flag.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "flag": {"type": "string", "description": "Flag name"},
                "value": {
                    "description": "Value to set (omit to read). Any JSON-serializable value."
                },
                "agent_id": {
                    "type": "string",
                    "description": "Agent setting the flag (required for writes)",
                },
            },
            "required": ["flag"],
        },
    },
    {
        "name": "state_summary",
        "description": "Human-readable summary of the cognitive state: version, agent count, claimed files, active flags.",
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
        if name == "state_read":
            state = read_state()
            return _ok(json.dumps(state.to_dict(), indent=2))

        elif name == "state_update_agent":
            agent_id = args.get("agent_id", "")
            status = args.get("status", "")
            if not agent_id or not status:
                return _err("Missing required parameters: agent_id, status")
            kwargs: dict[str, Any] = {}
            if "vendor" in args:
                kwargs["vendor"] = args["vendor"]
            if "model" in args:
                kwargs["model"] = args["model"]
            state = update_agent_status(agent_id, status, **kwargs)
            return _ok(
                json.dumps(
                    {
                        "updated": True,
                        "agent_id": agent_id,
                        "status": status,
                        "version": state.version,
                    },
                    indent=2,
                )
            )

        elif name == "state_claim_file":
            path = args.get("path", "")
            agent_id = args.get("agent_id", "")
            if not path or not agent_id:
                return _err("Missing required parameters: path, agent_id")
            purpose = args.get("purpose", "")
            state = claim_file(path, agent_id, purpose=purpose)
            return _ok(
                json.dumps(
                    {
                        "claimed": True,
                        "path": path,
                        "agent_id": agent_id,
                        "version": state.version,
                    },
                    indent=2,
                )
            )

        elif name == "state_release_file":
            path = args.get("path", "")
            agent_id = args.get("agent_id", "")
            if not path or not agent_id:
                return _err("Missing required parameters: path, agent_id")
            state = release_file(path, agent_id)
            return _ok(
                json.dumps(
                    {
                        "released": True,
                        "path": path,
                        "agent_id": agent_id,
                        "version": state.version,
                    },
                    indent=2,
                )
            )

        elif name == "state_flags":
            flag = args.get("flag", "")
            if not flag:
                return _err("Missing required parameter: flag")

            if "value" not in args:
                # Read mode
                state = read_state()
                current = state.flags.get(flag)
                return _ok(
                    json.dumps(
                        {
                            "flag": flag,
                            "value": current,
                            "exists": flag in state.flags,
                        },
                        indent=2,
                    )
                )
            else:
                # Write mode
                agent_id = args.get("agent_id", "")
                if not agent_id:
                    return _err(
                        "Missing required parameter: agent_id (required for setting flags)"
                    )
                value = args["value"]
                state = read_state()
                state.flags[flag] = value
                state.increment_version(agent_id)
                write_state(state, expected_version=state.version - 1)
                return _ok(
                    json.dumps(
                        {
                            "flag": flag,
                            "value": value,
                            "set": True,
                            "version": state.version,
                        },
                        indent=2,
                    )
                )

        elif name == "state_summary":
            state = read_state()
            agents = list(state.active_agents.keys())
            claims = {
                path: info.get("agent", "unknown")
                for path, info in state.claimed_files.items()
            }
            flags = list(state.flags.keys())
            summary_lines = [
                f"Version: {state.version}",
                f"Updated: {state.updated_at or 'never'} by {state.updated_by or 'nobody'}",
                f"Active agents ({len(agents)}): {', '.join(agents) if agents else 'none'}",
                f"Claimed files ({len(claims)}): {json.dumps(claims) if claims else 'none'}",
                f"Active decisions: {len(state.active_decisions)}",
                f"Sprint: {json.dumps(state.sprint) if state.sprint else 'not set'}",
                f"Flags ({len(flags)}): {', '.join(flags) if flags else 'none'}",
            ]
            return _ok("\n".join(summary_lines))

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
                json.dumps(
                    {
                        "jsonrpc": "2.0",
                        "id": None,
                        "error": {"code": -32700, "message": "Parse error"},
                    }
                )
                + "\n"
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
                json.dumps(
                    {
                        "jsonrpc": "2.0",
                        "id": rid,
                        "error": {"code": -32601, "message": f"Unknown: {method}"},
                    }
                )
                + "\n"
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
