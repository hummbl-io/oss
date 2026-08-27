#!/usr/bin/env python3
# Copyright 2024-2026 HUMMBL, LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# SPDX-License-Identifier: Apache-2.0

"""MCP Server for HITL Approvals.

Exposes the ApprovalManager primitive as MCP tools via stdio JSON-RPC,
enabling any MCP-compatible AI agent to request, check, approve, and deny
human-in-the-loop approval requests.

Zero third-party dependencies. Uses only Python stdlib + hummbl_governance.

Usage:
    python3 mcp_approval.py

Configure in Claude Code settings.json:
    {
      "mcpServers": {
        "hummbl-approvals": {
          "command": "python3",
          "args": ["path/to/mcp_approval.py"],
          "env": {
            "GOVERNANCE_STATE_DIR": "/path/to/state",
            "APPROVAL_WEBHOOK_URL": "https://hooks.slack.com/...",
            "APPROVAL_SLACK_WEBHOOK_URL": "https://hooks.slack.com/T/B/X"
          }
        }
      }
    }

Environment variables:
    GOVERNANCE_STATE_DIR       - State persistence directory (default: /tmp/governance)
    APPROVAL_WEBHOOK_URL       - Generic webhook URL for notifications
    APPROVAL_SLACK_WEBHOOK_URL - Slack incoming webhook URL
    APPROVAL_EMAIL_HOST        - SMTP host for email notifications
    APPROVAL_EMAIL_PORT        - SMTP port (default: 587)
    APPROVAL_EMAIL_FROM        - Sender email address
    APPROVAL_EMAIL_TO          - Recipient email address
    APPROVAL_EMAIL_USERNAME    - SMTP username (optional)
    APPROVAL_EMAIL_PASSWORD    - SMTP password (optional)
"""

import json
import os
import sys
import tempfile
from pathlib import Path

from hummbl_governance import ApprovalManager, RiskLevel

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
STATE_DIR = os.environ.get("GOVERNANCE_STATE_DIR", os.path.join(tempfile.gettempdir(), "governance"))  # nosec B108
SERVER_NAME = "hummbl-approvals"
SERVER_VERSION = "0.1.0"
PROTOCOL_VERSION = "2024-11-05"

# ---------------------------------------------------------------------------
# Singleton ApprovalManager (lazy init)
# ---------------------------------------------------------------------------
_manager: ApprovalManager | None = None


def _get_manager() -> ApprovalManager:
    global _manager
    if _manager is None:
        email_config = None
        email_host = os.environ.get("APPROVAL_EMAIL_HOST")
        if email_host:
            email_config = {
                "host": email_host,
                "port": int(os.environ.get("APPROVAL_EMAIL_PORT", "587")),
                "from": os.environ.get("APPROVAL_EMAIL_FROM", ""),
                "to": os.environ.get("APPROVAL_EMAIL_TO", ""),
                "username": os.environ.get("APPROVAL_EMAIL_USERNAME"),
                "password": os.environ.get("APPROVAL_EMAIL_PASSWORD"),
                "use_tls": os.environ.get("APPROVAL_EMAIL_USE_TLS", "1") == "1",
            }
        _manager = ApprovalManager(
            state_dir=Path(STATE_DIR),
            webhook_url=os.environ.get("APPROVAL_WEBHOOK_URL"),
            slack_webhook_url=os.environ.get("APPROVAL_SLACK_WEBHOOK_URL"),
            email_config=email_config,
            auto_expire_interval=30,
        )
    return _manager


# ---------------------------------------------------------------------------
# Tool definitions
# ---------------------------------------------------------------------------
TOOLS = [
    {
        "name": "approval_request",
        "description": (
            "Request human approval for an agent action. Creates a PENDING request "
            "and notifies reviewers via configured channels (webhook, Slack, email). "
            "Returns the request_id for polling with approval_check_status."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "agent_id": {"type": "string", "description": "Agent requesting approval"},
                "action": {"type": "string", "description": "Action/tool name requiring approval"},
                "action_args": {"type": "string", "description": "Human-readable argument summary (redacted)"},
                "risk_level": {
                    "type": "string",
                    "enum": ["LOW", "MEDIUM", "HIGH", "CRITICAL"],
                    "description": "Risk classification",
                },
                "justification": {"type": "string", "description": "Why this action is needed"},
                "timeout_seconds": {
                    "type": "number",
                    "description": "Seconds before auto-expiry (default: no expiry)",
                },
                "task_id": {"type": "string", "description": "Optional task identifier"},
            },
            "required": ["agent_id", "action", "risk_level", "justification"],
        },
    },
    {
        "name": "approval_check_status",
        "description": "Check the status of an approval request. Auto-expires stale requests.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "request_id": {"type": "string", "description": "Approval request ID"},
            },
            "required": ["request_id"],
        },
    },
    {
        "name": "approval_approve",
        "description": "Approve a pending approval request. Requires reviewer identity.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "request_id": {"type": "string", "description": "Approval request ID"},
                "decided_by": {"type": "string", "description": "Reviewer identity"},
                "reason": {"type": "string", "description": "Reason for approval"},
            },
            "required": ["request_id", "decided_by"],
        },
    },
    {
        "name": "approval_deny",
        "description": "Deny a pending approval request. Requires reviewer identity.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "request_id": {"type": "string", "description": "Approval request ID"},
                "decided_by": {"type": "string", "description": "Reviewer identity"},
                "reason": {"type": "string", "description": "Reason for denial"},
            },
            "required": ["request_id", "decided_by"],
        },
    },
    {
        "name": "approval_cancel",
        "description": "Cancel a pending approval request (typically called by the requesting agent).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "request_id": {"type": "string", "description": "Approval request ID"},
                "decided_by": {"type": "string", "description": "Who is cancelling"},
                "reason": {"type": "string", "description": "Reason for cancellation"},
            },
            "required": ["request_id", "decided_by"],
        },
    },
    {
        "name": "approval_list_pending",
        "description": "List all pending approval requests awaiting human decision.",
        "inputSchema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "approval_list_all",
        "description": "List all approval requests (newest first).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "description": "Max results (default: 20)", "default": 20},
            },
            "required": [],
        },
    },
    {
        "name": "approval_stats",
        "description": "Get aggregate approval statistics: counts by status and risk level.",
        "inputSchema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "approval_gate",
        "description": (
            "One-call gate: if risk_level is below threshold, auto-approves. "
            "Otherwise creates a request and blocks until a decision is reached "
            "or timeout expires. Returns {allowed, status, request_id, reason}."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "agent_id": {"type": "string", "description": "Agent requesting the action"},
                "action": {"type": "string", "description": "Action/tool name"},
                "action_args": {"type": "string", "description": "Argument summary"},
                "risk_level": {
                    "type": "string",
                    "enum": ["LOW", "MEDIUM", "HIGH", "CRITICAL"],
                    "description": "Risk classification",
                },
                "justification": {"type": "string", "description": "Why this action is needed"},
                "threshold": {
                    "type": "string",
                    "enum": ["LOW", "MEDIUM", "HIGH", "CRITICAL"],
                    "description": "Risk level at/above which approval is required (default: MEDIUM)",
                    "default": "MEDIUM",
                },
                "timeout_seconds": {
                    "type": "number",
                    "description": "How long to wait for a decision (default: 300)",
                    "default": 300,
                },
            },
            "required": ["agent_id", "action", "risk_level", "justification"],
        },
    },
    {
        "name": "approval_expire_stale",
        "description": "Manually trigger expiration of all stale (timed-out) pending requests.",
        "inputSchema": {"type": "object", "properties": {}, "required": []},
    },
]


# ---------------------------------------------------------------------------
# Tool handlers
# ---------------------------------------------------------------------------
def _handle_request(args: dict) -> dict:
    mgr = _get_manager()
    risk = RiskLevel[args["risk_level"]]
    metadata = {}
    if args.get("task_id"):
        metadata["task_id"] = args["task_id"]
    req = mgr.request_approval(
        agent_id=args["agent_id"],
        action=args["action"],
        action_args=args.get("action_args", ""),
        risk_level=risk,
        justification=args["justification"],
        timeout_seconds=args.get("timeout_seconds"),
        metadata=metadata if metadata else None,
    )
    return req.to_dict()


def _handle_check_status(args: dict) -> dict:
    mgr = _get_manager()
    return mgr.check_status(args["request_id"])


def _handle_approve(args: dict) -> dict:
    mgr = _get_manager()
    req = mgr.approve(args["request_id"], decided_by=args["decided_by"], reason=args.get("reason"))
    return req.to_dict()


def _handle_deny(args: dict) -> dict:
    mgr = _get_manager()
    req = mgr.deny(args["request_id"], decided_by=args["decided_by"], reason=args.get("reason"))
    return req.to_dict()


def _handle_cancel(args: dict) -> dict:
    mgr = _get_manager()
    req = mgr.cancel(args["request_id"], decided_by=args["decided_by"], reason=args.get("reason"))
    return req.to_dict()


def _handle_list_pending(args: dict) -> dict:
    mgr = _get_manager()
    return {"pending": mgr.list_pending()}


def _handle_list_all(args: dict) -> dict:
    mgr = _get_manager()
    return {"requests": mgr.list_all(limit=args.get("limit", 20))}


def _handle_stats(args: dict) -> dict:
    mgr = _get_manager()
    return mgr.get_stats()


def _handle_gate(args: dict) -> dict:
    mgr = _get_manager()
    risk = RiskLevel[args["risk_level"]]
    threshold = RiskLevel[args.get("threshold", "MEDIUM")]
    return mgr.gate(
        agent_id=args["agent_id"],
        action=args["action"],
        action_args=args.get("action_args", ""),
        risk_level=risk,
        justification=args["justification"],
        threshold=threshold,
        timeout_seconds=args.get("timeout_seconds", 300),
    )


def _handle_expire_stale(args: dict) -> dict:
    mgr = _get_manager()
    count = mgr.expire_stale()
    return {"expired_count": count}


_TOOL_HANDLERS = {
    "approval_request": _handle_request,
    "approval_check_status": _handle_check_status,
    "approval_approve": _handle_approve,
    "approval_deny": _handle_deny,
    "approval_cancel": _handle_cancel,
    "approval_list_pending": _handle_list_pending,
    "approval_list_all": _handle_list_all,
    "approval_stats": _handle_stats,
    "approval_gate": _handle_gate,
    "approval_expire_stale": _handle_expire_stale,
}


def handle_tool(name: str, arguments: dict) -> dict:
    handler = _TOOL_HANDLERS.get(name)
    if handler is None:
        return {"error": f"Unknown tool: {name}"}
    try:
        return handler(arguments)
    except Exception as e:
        return {"error": str(e), "error_type": type(e).__name__}


# ---------------------------------------------------------------------------
# JSON-RPC protocol
# ---------------------------------------------------------------------------
def send_response(msg_id, result):
    response = {"jsonrpc": "2.0", "id": msg_id, "result": result}
    sys.stdout.write(json.dumps(response) + "\n")
    sys.stdout.flush()


def send_error(msg_id, code, message):
    response = {"jsonrpc": "2.0", "id": msg_id, "error": {"code": code, "message": message}}
    sys.stdout.write(json.dumps(response) + "\n")
    sys.stdout.flush()


def main():
    """Main stdio JSON-RPC loop implementing MCP protocol."""
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
                        "content": [{"type": "text", "text": json.dumps(result, indent=2, default=str)}],
                    },
                )
            elif method == "ping":
                send_response(msg_id, {})
            else:
                send_error(msg_id, -32601, f"Method not found: {method}")
        except Exception as e:
            send_error(msg_id, -32603, f"Internal error: {e}")


if __name__ == "__main__":
    main()
