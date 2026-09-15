#!/usr/bin/env python3
"""MCP Server for Proton Services.

Exposes Proton Mail, Drive, Calendar, and Meet capabilities as MCP tools via stdio JSON-RPC.
This package integrates with Proton Bridge (for Mail) and other potential local/API methods
for Drive, Calendar, and Meet.

Usage:
    python3 proton_mcp_server.py

Configure in Antigravity or Gemini config (`mcp_config.json`):
    {
      "mcpServers": {
        "proton": {
          "command": "hummbl-mcp-proton"
        }
      }
    }
"""

import json
import sys
import traceback
import os
import imaplib
import smtplib
import subprocess
from email.message import EmailMessage
from email import policy
from email.parser import BytesParser

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
SERVER_NAME = "proton"
SERVER_VERSION = "0.1.0"
PROTOCOL_VERSION = "2024-11-05"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def get_imap_client():
    host = os.environ.get("PROTON_IMAP_HOST", "127.0.0.1")
    port = int(os.environ.get("PROTON_IMAP_PORT", "1143"))
    user = os.environ.get("PROTON_USER")
    pwd = os.environ.get("PROTON_PASS")

    if not user or not pwd:
        raise ValueError(
            "PROTON_USER and PROTON_PASS environment variables are required."
        )

    if port == 993:
        client = imaplib.IMAP4_SSL(host, port)
    else:
        client = imaplib.IMAP4(host, port)
        client.starttls()

    client.login(user, pwd)
    return client


def get_smtp_client():
    host = os.environ.get("PROTON_SMTP_HOST", "127.0.0.1")
    port = int(os.environ.get("PROTON_SMTP_PORT", "1025"))
    user = os.environ.get("PROTON_USER")
    pwd = os.environ.get("PROTON_PASS")

    if not user or not pwd:
        raise ValueError(
            "PROTON_USER and PROTON_PASS environment variables are required."
        )

    if port == 465:
        client = smtplib.SMTP_SSL(host, port)
    else:
        client = smtplib.SMTP(host, port)
        client.starttls()

    client.login(user, pwd)
    return client


# ---------------------------------------------------------------------------
# Tool Implementations
# ---------------------------------------------------------------------------
def tool_proton_mail_search(arguments):
    """Search Proton Mail via IMAP (Proton Bridge)."""
    query = arguments.get("query", "ALL")
    limit = int(arguments.get("limit", 10))

    try:
        client = get_imap_client()
        client.select("INBOX")
        status, messages = client.search(None, query.encode("utf-8"))

        if status != "OK":
            return {"error": "IMAP search failed", "status": status}

        msg_nums = messages[0].split()
        msg_nums = msg_nums[-limit:]  # get the latest 'limit' messages

        results = []
        for num in reversed(msg_nums):
            res, msg_data = client.fetch(num, "(RFC822)")
            if res != "OK":
                continue

            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = BytesParser(policy=policy.default).parsebytes(
                        response_part[1]
                    )
                    subject = msg.get("subject", "")
                    from_ = msg.get("from", "")
                    date = msg.get("date", "")

                    # Extract plain text body
                    body = ""
                    if msg.is_multipart():
                        for part in msg.walk():
                            if part.get_content_type() == "text/plain":
                                content = part.get_content()
                                if content:
                                    body += content
                    else:
                        body = msg.get_content()

                    results.append(
                        {
                            "id": num.decode(),
                            "subject": subject,
                            "from": from_,
                            "date": date,
                            "body_snippet": body[:500]
                            + ("..." if len(body) > 500 else ""),
                        }
                    )

        client.logout()
        return {"messages": results, "count": len(results)}
    except Exception as e:
        return {"error": str(e), "traceback": traceback.format_exc()}


def tool_proton_mail_send(arguments):
    """Send Proton Mail via SMTP (Proton Bridge)."""
    to_addr = arguments.get("to")
    subject = arguments.get("subject")
    body = arguments.get("body")

    if not all([to_addr, subject, body]):
        return {"error": "Missing required fields: to, subject, body"}

    try:
        msg = EmailMessage()
        msg.set_content(body)
        msg["Subject"] = subject
        msg["From"] = os.environ.get("PROTON_USER")
        msg["To"] = to_addr

        client = get_smtp_client()
        client.send_message(msg)
        client.quit()

        return {"status": "success", "message": f"Email sent to {to_addr}"}
    except Exception as e:
        return {"error": str(e), "traceback": traceback.format_exc()}


def tool_proton_drive_list(arguments):
    """List files in Proton Drive via official CLI."""
    path = arguments.get("path", "/")

    try:
        result = subprocess.run(
            ["proton-drive", "list", path, "--json"],
            capture_output=True,
            text=True,
            check=True,
        )
        data = json.loads(result.stdout)
        return {"status": "success", "files": data}
    except FileNotFoundError:
        return {"error": "proton-drive CLI not found on PATH. Install it first."}
    except subprocess.CalledProcessError as e:
        return {"error": "Proton Drive CLI error", "stderr": e.stderr}
    except json.JSONDecodeError:
        return {
            "error": "Failed to parse JSON from proton-drive CLI",
            "stdout": result.stdout,
        }
    except Exception as e:
        return {"error": str(e), "traceback": traceback.format_exc()}


def tool_proton_calendar_events(arguments):
    """List events in Proton Calendar via proton-calendar-cli."""
    days = int(arguments.get("days", 7))

    try:
        result = subprocess.run(
            ["proton-calendar-cli", "list", "--days", str(days), "--json"],
            capture_output=True,
            text=True,
            check=True,
        )
        data = json.loads(result.stdout)
        return {"status": "success", "events": data}
    except FileNotFoundError:
        return {"error": "proton-calendar-cli not found on PATH. Install it first."}
    except subprocess.CalledProcessError as e:
        return {"error": "Proton Calendar CLI error", "stderr": e.stderr}
    except json.JSONDecodeError:
        return {
            "error": "Failed to parse JSON from proton-calendar-cli",
            "stdout": result.stdout,
        }
    except Exception as e:
        return {"error": str(e), "traceback": traceback.format_exc()}


# ---------------------------------------------------------------------------
# MCP Tool Definitions
# ---------------------------------------------------------------------------
TOOLS = [
    {
        "name": "proton_mail_search",
        "description": "Search for emails in Proton Mail (requires Proton Mail Bridge running).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "IMAP search query"},
                "limit": {
                    "type": "integer",
                    "description": "Max results to return",
                    "default": 10,
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "proton_mail_send",
        "description": "Send an email via Proton Mail.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "to": {"type": "string"},
                "subject": {"type": "string"},
                "body": {"type": "string"},
            },
            "required": ["to", "subject", "body"],
        },
    },
    {
        "name": "proton_drive_list",
        "description": "List files and folders in Proton Drive.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Folder path to list",
                    "default": "/",
                }
            },
        },
    },
    {
        "name": "proton_calendar_events",
        "description": "Retrieve events from Proton Calendar.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "days": {
                    "type": "integer",
                    "description": "Number of days ahead to fetch",
                    "default": 7,
                }
            },
        },
    },
]

# Tool dispatch map
TOOL_HANDLERS = {
    "proton_mail_search": tool_proton_mail_search,
    "proton_mail_send": tool_proton_mail_send,
    "proton_drive_list": tool_proton_drive_list,
    "proton_calendar_events": tool_proton_calendar_events,
}


# ---------------------------------------------------------------------------
# JSON-RPC protocol
# ---------------------------------------------------------------------------
def send_response(msg_id, result):
    """Send a JSON-RPC response to stdout."""
    response = {"jsonrpc": "2.0", "id": msg_id, "result": result}
    out = json.dumps(response)
    sys.stdout.write(out + "\\n")
    sys.stdout.flush()


def send_error(msg_id, code, message):
    """Send a JSON-RPC error to stdout."""
    response = {
        "jsonrpc": "2.0",
        "id": msg_id,
        "error": {"code": code, "message": message},
    }
    out = json.dumps(response)
    sys.stdout.write(out + "\\n")
    sys.stdout.flush()


def _handle_initialize(msg_id):
    """Handle MCP initialize request."""
    send_response(
        msg_id,
        {
            "protocolVersion": PROTOCOL_VERSION,
            "capabilities": {"tools": {}},
            "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
        },
    )


def _handle_tools_call(msg_id, params):
    """Handle MCP tools/call request."""
    tool_name = params.get("name", "")
    arguments = params.get("arguments", {})
    handler = TOOL_HANDLERS.get(tool_name)
    result = handler(arguments) if handler else {"error": f"Unknown tool: {tool_name}"}
    send_response(
        msg_id,
        {
            "content": [
                {"type": "text", "text": json.dumps(result, indent=2, default=str)}
            ],
        },
    )


# Method dispatch table
_METHOD_HANDLERS = {
    "initialize": lambda msg_id, _params: _handle_initialize(msg_id),
    "notifications/initialized": lambda _msg_id, _params: None,
    "tools/list": lambda msg_id, _params: send_response(msg_id, {"tools": TOOLS}),
    "tools/call": lambda msg_id, params: _handle_tools_call(msg_id, params),
    "ping": lambda msg_id, _params: send_response(msg_id, {}),
}


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
            handler = _METHOD_HANDLERS.get(method)
            if handler:
                handler(msg_id, params)
            else:
                send_error(msg_id, -32601, f"Method not found: {method}")
        except Exception as e:
            send_error(
                msg_id,
                -32603,
                f"Internal error: {e}\\n{traceback.format_exc()}",
            )


if __name__ == "__main__":
    main()
