#!/usr/bin/env python3
import json
import os
import subprocess
import sys
import traceback

SERVER_NAME = "hummbl-mcp-signal"
SERVER_VERSION = "0.1.0"
PROTOCOL_VERSION = "2024-11-05"


def get_signal_config() -> tuple[str, str]:
    config_dir = os.environ.get("SIGNAL_CONFIG_DIR")
    account = os.environ.get("SIGNAL_ACCOUNT")

    if not config_dir or not account:
        raise ValueError(
            "SIGNAL_CONFIG_DIR and SIGNAL_ACCOUNT environment variables are required."
        )
    return config_dir, account


def run_signal_cli(args: list[str]) -> str:
    config_dir, account = get_signal_config()
    cmd = ["signal-cli", "--config", config_dir, "-u", account, "-o", "json"] + args

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except FileNotFoundError:
        raise RuntimeError("signal-cli not found on PATH. Install it first.")
    except subprocess.CalledProcessError as e:
        raise RuntimeError(
            f"signal-cli error (code {e.returncode}): {e.stderr.strip()}"
        )


def tool_signal_send_message(args: dict) -> dict:
    target = args.get("target")
    content = args.get("content")

    if not target or not content:
        raise ValueError("target and content are required")

    # Send message: signal-cli send -m "message" recipient
    run_signal_cli(["send", "-m", content, target])

    return {
        "content": [{"type": "text", "text": f"Successfully sent message to {target}"}]
    }


def tool_signal_receive_messages(args: dict) -> dict:
    # Receive messages: signal-cli receive
    # This pulls pending messages and clears them from the server queue for this device
    output = run_signal_cli(["receive"])

    return {"content": [{"type": "text", "text": output or "No new messages."}]}


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
                        "name": "signal_send_message",
                        "description": "Send a secure message via Signal to a specific recipient (phone number).",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "target": {
                                    "type": "string",
                                    "description": "The recipient's phone number (e.g. +1234567890)",
                                },
                                "content": {
                                    "type": "string",
                                    "description": "The message text to send",
                                },
                            },
                            "required": ["target", "content"],
                        },
                    },
                    {
                        "name": "signal_receive_messages",
                        "description": "Pull recent unread messages from Signal for this device link.",
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
            if tool_name == "signal_send_message":
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": tool_signal_send_message(args),
                }
            elif tool_name == "signal_receive_messages":
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": tool_signal_receive_messages(args),
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
            sys.stdout.write(json.dumps(res) + "\n")
            sys.stdout.flush()
        except Exception:
            pass


if __name__ == "__main__":
    main()
