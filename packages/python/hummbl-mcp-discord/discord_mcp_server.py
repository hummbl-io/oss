#!/usr/bin/env python3
import json
import os
import sys
import traceback
import urllib.request
import urllib.error

SERVER_NAME = "discord"
SERVER_VERSION = "0.1.0"
PROTOCOL_VERSION = "2024-11-05"


def discord_api_request(endpoint: str, method: str = "GET", data: dict = None) -> dict:
    token = os.environ.get("DISCORD_BOT_TOKEN")
    if not token:
        raise ValueError("DISCORD_BOT_TOKEN environment variable is required.")

    url = f"https://discord.com/api/v10{endpoint}"
    req = urllib.request.Request(url, method=method)
    req.add_header("Authorization", f"Bot {token}")
    req.add_header("User-Agent", "HummblMCP/1.0")

    if data is not None:
        req.add_header("Content-Type", "application/json")
        req.data = json.dumps(data).encode("utf-8")

    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8")
        raise RuntimeError(f"Discord API Error {e.code}: {error_body}")
    except Exception as e:
        raise RuntimeError(f"Request failed: {str(e)}")


def tool_discord_channel_summarize(args: dict) -> dict:
    channel_id = args.get("channel_id")
    limit = args.get("limit", 50)

    if not channel_id:
        raise ValueError("channel_id is required")

    messages = discord_api_request(f"/channels/{channel_id}/messages?limit={limit}")

    formatted_messages = []
    for msg in reversed(messages):
        author = msg.get("author", {}).get("username", "Unknown")
        content = msg.get("content", "")
        formatted_messages.append(f"[{author}]: {content}")

    return {
        "content": [
            {
                "type": "text",
                "text": "\n".join(formatted_messages) or "No messages found.",
            }
        ]
    }


def tool_discord_draft_reply(args: dict) -> dict:
    channel_id = args.get("channel_id")
    message = args.get("message")

    if not channel_id or not message:
        raise ValueError("channel_id and message are required")

    # In a true RSI loop, this might post to a dedicated #drafts channel,
    # or just post directly if authorized. For now, we post directly as the bot.
    result = discord_api_request(
        f"/channels/{channel_id}/messages", method="POST", data={"content": message}
    )

    return {
        "content": [
            {
                "type": "text",
                "text": f"Successfully drafted/posted message with ID: {result.get('id')}",
            }
        ]
    }


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
                        "name": "discord_channel_summarize",
                        "description": "Fetch recent messages from a Discord channel for triage/summarization.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "channel_id": {
                                    "type": "string",
                                    "description": "The Discord channel ID",
                                },
                                "limit": {
                                    "type": "integer",
                                    "description": "Number of messages to fetch (default 50)",
                                },
                            },
                            "required": ["channel_id"],
                        },
                    },
                    {
                        "name": "discord_draft_reply",
                        "description": "Draft or post a reply to a Discord channel.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "channel_id": {
                                    "type": "string",
                                    "description": "The Discord channel ID to post to",
                                },
                                "message": {
                                    "type": "string",
                                    "description": "The message content to draft/post",
                                },
                            },
                            "required": ["channel_id", "message"],
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
            if tool_name == "discord_channel_summarize":
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": tool_discord_channel_summarize(args),
                }
            elif tool_name == "discord_draft_reply":
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": tool_discord_draft_reply(args),
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
