#!/usr/bin/env python3
"""MCP Server for the Coordination Bus.

Exposes the append-only TSV coordination bus as MCP tools.
Read messages, post messages, search, analytics, and replay.

Zero third-party dependencies. Uses only Python stdlib + bus_writer.

Tools:
    bus_read         - Read recent bus messages (optionally filtered)
    bus_post         - Post a message to the coordination bus
    bus_search       - Search messages by content, agent, or type
    bus_stats        - Message count, agent activity, type breakdown
    bus_agents       - List all agents with message counts and last activity
"""

import csv
import json
import logging
import os
import sys
import traceback
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

logger = logging.getLogger(__name__)

SERVER_NAME = "coordination-bus"
SERVER_VERSION = "0.1.0"
PROTOCOL_VERSION = "2024-11-05"

BUS_FILE = Path(
    os.environ.get(
        "BUS_FILE",
        Path(__file__).resolve().parent.parent
        / "_state"
        / "coordination"
        / "messages.tsv",
    )
)


# ---------------------------------------------------------------------------
# Bus operations
# ---------------------------------------------------------------------------
def read_bus(
    limit: int = 50,
    agent: str | None = None,
    msg_type: str | None = None,
    since: str | None = None,
) -> list[dict[str, str]]:
    """Read messages from the TSV bus, newest first."""
    limit = max(limit, 0)
    if not BUS_FILE.exists():
        return []
    rows = []
    try:
        with open(BUS_FILE, "r", encoding="utf-8") as f:
            reader = csv.reader(f, delimiter="\t")
            for row in reader:
                if len(row) < 5:
                    continue
                ts, frm, to, mtype, msg = (
                    row[0],
                    row[1],
                    row[2],
                    row[3],
                    row[4] if len(row) > 4 else "",
                )
                if agent and agent.lower() not in frm.lower():
                    continue
                if msg_type and msg_type.upper() != mtype.upper():
                    continue
                if since and ts < since:
                    continue
                rows.append(
                    {
                        "timestamp": ts,
                        "from": frm,
                        "to": to,
                        "type": mtype,
                        "message": msg[:500],
                    }
                )
    except OSError as e:
        logger.error("read_bus: failed to read bus file %s: %s", BUS_FILE, e)
        return []
    return rows[-limit:] if limit > 0 else []


def search_bus(query: str, limit: int = 20) -> list[dict[str, str]]:
    """Search bus messages by content."""
    limit = max(limit, 0)
    query_lower = query.lower()
    results = []
    if not BUS_FILE.exists():
        return results
    try:
        with open(BUS_FILE, "r", encoding="utf-8") as f:
            reader = csv.reader(f, delimiter="\t")
            for row in reader:
                if len(row) < 5:
                    continue
                combined = "\t".join(row).lower()
                if query_lower in combined:
                    results.append(
                        {
                            "timestamp": row[0],
                            "from": row[1],
                            "to": row[2],
                            "type": row[3],
                            "message": row[4][:500] if len(row) > 4 else "",
                        }
                    )
    except OSError as e:
        logger.error("search_bus: failed to read bus file %s: %s", BUS_FILE, e)
        return results
    return results[-limit:] if limit > 0 else []


def bus_stats() -> dict[str, object]:
    """Aggregate bus statistics."""
    if not BUS_FILE.exists():
        return {"error": "Bus file not found"}
    agents: Counter[str] = Counter()
    types: Counter[str] = Counter()
    total = 0
    first_ts: str | None = None
    last_ts: str | None = None
    try:
        with open(BUS_FILE, "r", encoding="utf-8") as f:
            reader = csv.reader(f, delimiter="\t")
            for row in reader:
                if len(row) < 5:
                    continue
                total += 1
                agents[row[1]] += 1
                types[row[3]] += 1
                if first_ts is None:
                    first_ts = row[0]
                last_ts = row[0]
    except OSError as e:
        logger.error("bus_stats: failed to read bus file %s: %s", BUS_FILE, e)
        return {"error": f"Bus file unreadable: {e}"}
    return {
        "total_messages": total,
        "date_range": {"first": first_ts, "last": last_ts},
        "agents": dict(agents.most_common(20)),
        "types": dict(types.most_common()),
    }


def bus_agents_list() -> dict[str, object]:
    """List agents with activity stats."""
    if not BUS_FILE.exists():
        return {"error": "Bus file not found"}
    agent_data: dict[str, dict[str, object]] = {}
    try:
        with open(BUS_FILE, "r", encoding="utf-8") as f:
            reader = csv.reader(f, delimiter="\t")
            for row in reader:
                if len(row) < 5:
                    continue
                frm = row[1]
                if frm not in agent_data:
                    agent_data[frm] = {
                        "count": 0,
                        "first_seen": row[0],
                        "last_seen": row[0],
                        "types": Counter(),
                    }
                agent_data[frm]["count"] += 1
                agent_data[frm]["last_seen"] = row[0]
                agent_data[frm]["types"][row[3]] += 1
    except OSError as e:
        logger.error("bus_agents_list: failed to read bus file %s: %s", BUS_FILE, e)
        return {"error": f"Bus file unreadable: {e}"}
    return {
        "agents": [
            {
                "name": name,
                "messages": data["count"],
                "first_seen": data["first_seen"],
                "last_seen": data["last_seen"],
                "top_types": dict(data["types"].most_common(3)),
            }
            for name, data in sorted(agent_data.items(), key=lambda x: -x[1]["count"])
        ]
    }


# ---------------------------------------------------------------------------
# Tool definitions
# ---------------------------------------------------------------------------
TOOLS = [
    {
        "name": "bus_read",
        "description": "Read recent coordination bus messages. Optionally filter by agent or message type.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": "Max messages (default: 30)",
                    "default": 30,
                },
                "agent": {
                    "type": "string",
                    "description": "Filter by sender agent name (partial match)",
                },
                "type": {
                    "type": "string",
                    "description": "Filter by message type (STATUS, SITREP, PROPOSAL, etc.)",
                },
                "since": {
                    "type": "string",
                    "description": "Only messages after this ISO timestamp",
                },
            },
            "required": [],
        },
    },
    {
        "name": "bus_post",
        "description": "Post a message to the coordination bus. Uses bus_writer for flock-safe append.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "from_agent": {
                    "type": "string",
                    "description": "Sender identity (default: mcp-client)",
                    "default": "mcp-client",
                },
                "to": {
                    "type": "string",
                    "description": "Recipient (agent name or 'all')",
                    "default": "all",
                },
                "type": {
                    "type": "string",
                    "enum": [
                        "STATUS",
                        "SITREP",
                        "PROPOSAL",
                        "ACK",
                        "BLOCKED",
                        "DECISION",
                        "QUESTION",
                        "MILESTONE",
                    ],
                    "description": "Message type",
                },
                "message": {"type": "string", "description": "Message content"},
            },
            "required": ["type", "message"],
        },
    },
    {
        "name": "bus_search",
        "description": "Search bus messages by text content across all fields.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search text"},
                "limit": {
                    "type": "integer",
                    "description": "Max results (default: 20)",
                    "default": 20,
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "bus_stats",
        "description": "Get bus statistics: total messages, date range, top agents, message type breakdown.",
        "inputSchema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "bus_agents",
        "description": "List all agents that have posted to the bus with message counts, first/last seen, and top message types.",
        "inputSchema": {"type": "object", "properties": {}, "required": []},
    },
]


# ---------------------------------------------------------------------------
# Tool dispatch
# ---------------------------------------------------------------------------
def handle_tool(name: str, arguments: dict[str, object]) -> dict[str, object]:
    if name == "bus_read":
        messages = read_bus(
            limit=arguments.get("limit", 30),
            agent=arguments.get("agent"),
            msg_type=arguments.get("type"),
            since=arguments.get("since"),
        )
        return {"count": len(messages), "messages": messages}

    elif name == "bus_post":
        try:
            from .bus_writer import post_message

            post_message(
                bus_path=str(BUS_FILE),
                from_id=arguments.get("from_agent", "mcp-client"),
                to_id=arguments.get("to", "all"),
                msg_type=arguments["type"],
                message=arguments["message"],
            )
            return {
                "posted": True,
                "type": arguments["type"],
                "message": arguments["message"][:200],
            }
        except PermissionError as exc:
            return {"posted": False, "error": str(exc)}
        except ImportError:
            # Fallback: direct append with platform-appropriate locking
            try:
                import fcntl
            except ImportError:
                fcntl = None  # type: ignore[assignment]
            try:
                import msvcrt  # type: ignore[attr-defined]
            except ImportError:
                msvcrt = None  # type: ignore[assignment]

            ts = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
            frm = arguments.get("from_agent", "mcp-client")
            to = arguments.get("to", "all")
            mtype = arguments["type"]
            from .authority import PRIVILEGED_TYPES

            if str(mtype).strip().upper() in PRIVILEGED_TYPES:
                return {
                    "posted": False,
                    "error": "privileged bus write requires authenticated principal proof",
                }
            msg = arguments["message"].replace("\t", " ").replace("\n", " ")
            line = f"{ts}\t{frm}\t{to}\t{mtype}\t{msg}\n"
            BUS_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(BUS_FILE, "a", encoding="utf-8") as f:
                if fcntl is not None:
                    fcntl.flock(f, fcntl.LOCK_EX)
                elif msvcrt is not None:
                    msvcrt.locking(f.fileno(), msvcrt.LK_LOCK, 1)
                f.write(line)
                f.flush()
                if fcntl is not None:
                    fcntl.flock(f, fcntl.LOCK_UN)
                elif msvcrt is not None:
                    msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
            return {
                "posted": True,
                "type": mtype,
                "message": msg[:200],
                "method": "direct_append",
            }

    elif name == "bus_search":
        results = search_bus(arguments["query"], arguments.get("limit", 20))
        return {"query": arguments["query"], "count": len(results), "results": results}

    elif name == "bus_stats":
        return bus_stats()

    elif name == "bus_agents":
        return bus_agents_list()

    else:
        return {"error": f"Unknown tool: {name}"}


# ---------------------------------------------------------------------------
# JSON-RPC protocol
# ---------------------------------------------------------------------------
def send_response(msg_id: object, result: dict[str, object]) -> None:
    response = {"jsonrpc": "2.0", "id": msg_id, "result": result}
    sys.stdout.write(json.dumps(response) + "\n")
    sys.stdout.flush()


def send_error(msg_id: object, code: int, message: str) -> None:
    response = {
        "jsonrpc": "2.0",
        "id": msg_id,
        "error": {"code": code, "message": message},
    }
    sys.stdout.write(json.dumps(response) + "\n")
    sys.stdout.flush()


def main() -> None:
    # Force UTF-8 on stdio. On Windows, sys.stdin/sys.stdout default to the
    # system codepage (CP1252), which corrupts non-ASCII JSON-RPC payloads
    # (em-dashes, smart quotes, accented characters) via mojibake before
    # json.loads ever sees them. On POSIX this is a no-op (stdin/stdout are
    # already UTF-8). Python 3.7+ supports TextIOWrapper.reconfigure().
    if hasattr(sys.stdin, "reconfigure"):
        sys.stdin.reconfigure(encoding="utf-8")
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            continue

        msg_id = msg.get("id")
        method = msg.get("method", "")
        params = msg.get("params", {})

        try:
            if method == "initialize":
                send_response(
                    msg_id,
                    {
                        "protocolVersion": PROTOCOL_VERSION,
                        "capabilities": {"tools": {}},
                        "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
                    },
                )
            elif method == "notifications/initialized":
                pass
            elif method == "tools/list":
                send_response(msg_id, {"tools": TOOLS})
            elif method == "tools/call":
                tool_name = params.get("name", "")
                arguments = params.get("arguments", {})
                result = handle_tool(tool_name, arguments)
                send_response(
                    msg_id,
                    {
                        "content": [
                            {
                                "type": "text",
                                "text": json.dumps(result, indent=2, default=str),
                            }
                        ],
                    },
                )
            elif method == "ping":
                send_response(msg_id, {})
            else:
                send_error(msg_id, -32601, f"Method not found: {method}")
        except Exception as e:
            send_error(msg_id, -32603, f"Internal error: {e}\n{traceback.format_exc()}")


if __name__ == "__main__":
    main()
