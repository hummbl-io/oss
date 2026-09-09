#!/usr/bin/env python3
import json
import sys
import traceback
from state import GovernanceState
from dataclasses import asdict

SERVER_NAME = "omnichannel-governance-gate"
SERVER_VERSION = "0.1.0"
PROTOCOL_VERSION = "2024-11-05"

gov_state = GovernanceState()


def tool_draft_message(args: dict) -> dict:
    target = args.get("target")
    content = args.get("content")
    urgency = args.get("urgency", "normal")

    if not target or not content:
        raise ValueError("target and content are required")

    msg = gov_state.create_draft(target, urgency, content)

    return {
        "content": [
            {
                "type": "text",
                "text": f"Successfully queued draft {msg.id}. Awaiting human operator approval.",
            }
        ]
    }


def tool_broadcast_urgent(args: dict) -> dict:
    content = args.get("content")
    if not content:
        raise ValueError("content is required")

    # An urgent broadcast typically goes to the public feed or all priority channels
    msg = gov_state.create_draft("public_feed", "critical", content)

    return {
        "content": [
            {
                "type": "text",
                "text": f"CRITICAL: Queued broadcast draft {msg.id}. Human operator must explicitly authorize this dispatch.",
            }
        ]
    }


def tool_list_pending_drafts(args: dict) -> dict:
    drafts = gov_state.list_pending_drafts()
    if not drafts:
        return {"content": [{"type": "text", "text": "No pending drafts."}]}

    results = [asdict(d) for d in drafts]
    return {"content": [{"type": "text", "text": json.dumps(results, indent=2)}]}


def handle_request(request: dict) -> dict:
    req_id = request.get("id")
    method = request.get("method")

    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": {"tools": {}},
                "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
            },
        }
    elif method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "tools": [
                    {
                        "name": "omni_draft_message",
                        "description": "Enqueue a message draft for human operator approval. Does NOT send the message.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "target": {
                                    "type": "string",
                                    "description": "The logical recipient (e.g., '+1234567890', 'team_channel')",
                                },
                                "content": {
                                    "type": "string",
                                    "description": "The message body",
                                },
                                "urgency": {
                                    "type": "string",
                                    "enum": ["low", "normal", "high"],
                                    "description": "Urgency level",
                                },
                            },
                            "required": ["target", "content"],
                        },
                    },
                    {
                        "name": "omni_broadcast_urgent",
                        "description": "Enqueue a critical public broadcast draft. Will halt and alert human operator for approval.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "content": {
                                    "type": "string",
                                    "description": "The critical broadcast body",
                                }
                            },
                            "required": ["content"],
                        },
                    },
                    {
                        "name": "omni_list_pending_drafts",
                        "description": "List all messages currently trapped in the draft state waiting for approval.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {},
                            "required": [],
                        },
                    },
                ]
            },
        }
    elif method == "tools/call":
        params = request.get("params", {})
        tool_name = params.get("name")
        args = params.get("arguments", {})

        try:
            if tool_name == "omni_draft_message":
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": tool_draft_message(args),
                }
            elif tool_name == "omni_broadcast_urgent":
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": tool_broadcast_urgent(args),
                }
            elif tool_name == "omni_list_pending_drafts":
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": tool_list_pending_drafts(args),
                }
            else:
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {
                        "code": -32601,
                        "message": f"Tool not found: {tool_name}",
                    },
                }
        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(
                                {"error": str(e), "traceback": traceback.format_exc()}
                            ),
                        }
                    ]
                },
            }

    return {
        "jsonrpc": "2.0",
        "id": req_id,
        "error": {"code": -32601, "message": f"Method not found: {method}"},
    }


def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
            res = handle_request(req)
            sys.stdout.write(json.dumps(res) + "\\n")
            sys.stdout.flush()
        except Exception:
            pass


if __name__ == "__main__":
    main()
