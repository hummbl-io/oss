"""Discord cross-guild bridge tools for HUMMBL MCP.

Lets agents (Soma, Echo, Dan's agents) read and post across multiple Discord
guilds through a single shared bot application ("HUMMBL MCP" Discord app).

Transport: Discord REST API (https://discord.com/api/v10) via stdlib urllib.
Auth: Bot token from HUMMBL_MCP_DISCORD_TOKEN env var.

Tools v1 (REST-only, no WebSocket — request/response only):
  - bridge_list_guilds        GET /users/@me/guilds
  - bridge_list_channels      GET /guilds/{guild_id}/channels
  - bridge_post_message       POST /channels/{channel_id}/messages
  - bridge_read_recent        GET /channels/{channel_id}/messages
  - bridge_edit_message       PATCH /channels/{channel_id}/messages/{msg_id}
  - bridge_delete_message     DELETE /channels/{channel_id}/messages/{msg_id}
  - bridge_add_reaction       PUT /channels/.../reactions/{emoji}/@me
  - bridge_get_user           GET /users/{user_id}

Rate limits: Discord enforces per-route limits. On 429, we raise a
JsonRpcError with the retry-after value so the caller can back off.
Heavier rate-limit middleware is deferred to v2.

Stdlib-only (urllib + json).
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any

from hummbl_mcp.protocol import JsonRpcError, TOOL_EXECUTION_ERROR, ToolDefinition


DISCORD_API_BASE = os.environ.get("DISCORD_API_BASE", "https://discord.com/api/v10")
USER_AGENT = "HummblMCP/0.1 (https://github.com/hummbl-io/hummbl-mcp, 0.1.0)"
REQUEST_TIMEOUT = int(os.environ.get("DISCORD_REQUEST_TIMEOUT", "15"))


class DiscordAPIError(JsonRpcError):
    """Discord-specific API error, carries HTTP status + retry-after on 429."""


def _get_token() -> str:
    token = os.environ.get("HUMMBL_MCP_DISCORD_TOKEN", "")
    if not token:
        raise JsonRpcError(
            TOOL_EXECUTION_ERROR,
            "HUMMBL_MCP_DISCORD_TOKEN not set — bridge tools require the bot token",
        )
    return token


def _discord_request(method: str, path: str, body: dict[str, Any] | None = None) -> Any:
    """Make an authenticated Discord REST call. Returns parsed JSON or None.

    On non-2xx, raises DiscordAPIError with HTTP status + any retry-after.
    """
    token = _get_token()
    url = f"{DISCORD_API_BASE}{path}"
    headers = {
        "Authorization": f"Bot {token}",
        "User-Agent": USER_AGENT,
        "Accept": "application/json",
    }
    data = None
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"

    req = urllib.request.Request(url=url, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
            raw = resp.read()
            if not raw:
                return None
            return json.loads(raw.decode("utf-8"))
    except urllib.error.HTTPError as e:
        status = e.code
        body_raw = b""
        try:
            body_raw = e.read() or b""
        except Exception:  # noqa: BLE001
            pass
        body_text = body_raw.decode("utf-8", errors="replace")[:500]
        retry_after = None
        if status == 429:
            # Discord sends retry-after in the body as JSON
            try:
                j = json.loads(body_text)
                retry_after = j.get("retry_after")
            except Exception:  # noqa: BLE001
                pass
        raise DiscordAPIError(
            TOOL_EXECUTION_ERROR,
            f"Discord API {status}: {body_text}",
            data={"status": status, "retry_after": retry_after, "path": path},
        ) from e
    except urllib.error.URLError as e:
        raise JsonRpcError(
            TOOL_EXECUTION_ERROR,
            f"Discord API network error: {e.reason}",
            data={"path": path},
        ) from e


# ---------------------------------------------------------------------------
# Tool handlers
# ---------------------------------------------------------------------------

def bridge_list_guilds(params: dict[str, Any]) -> Any:
    """List all Discord guilds (servers) the bot is a member of."""
    return _discord_request("GET", "/users/@me/guilds")


def bridge_list_channels(params: dict[str, Any]) -> Any:
    """List all channels in a guild."""
    guild_id = params["guild_id"]
    return _discord_request("GET", f"/guilds/{guild_id}/channels")


def bridge_post_message(params: dict[str, Any]) -> Any:
    """Post a message to a channel. Content <= 2000 chars per Discord limit."""
    channel_id = params["channel_id"]
    content = params["content"]
    if len(content) > 2000:
        raise JsonRpcError(
            TOOL_EXECUTION_ERROR,
            f"content exceeds Discord 2000-char limit ({len(content)} chars)",
        )
    body: dict[str, Any] = {"content": content}
    if params.get("reply_to_message_id"):
        body["message_reference"] = {"message_id": params["reply_to_message_id"]}
    return _discord_request("POST", f"/channels/{channel_id}/messages", body)


def bridge_read_recent(params: dict[str, Any]) -> Any:
    """Read recent messages from a channel. limit 1-100, default 50."""
    channel_id = params["channel_id"]
    limit = max(1, min(int(params.get("limit", 50)), 100))
    path = f"/channels/{channel_id}/messages?limit={limit}"
    if params.get("before_message_id"):
        path += f"&before={urllib.parse.quote(str(params['before_message_id']))}"
    return _discord_request("GET", path)


def bridge_edit_message(params: dict[str, Any]) -> Any:
    """Edit a message the bot authored."""
    channel_id = params["channel_id"]
    message_id = params["message_id"]
    content = params["content"]
    if len(content) > 2000:
        raise JsonRpcError(
            TOOL_EXECUTION_ERROR,
            f"content exceeds Discord 2000-char limit ({len(content)} chars)",
        )
    return _discord_request(
        "PATCH", f"/channels/{channel_id}/messages/{message_id}", {"content": content}
    )


def bridge_delete_message(params: dict[str, Any]) -> Any:
    """Delete a message (bot-authored, or anyone's if the bot has Manage Messages)."""
    channel_id = params["channel_id"]
    message_id = params["message_id"]
    _discord_request("DELETE", f"/channels/{channel_id}/messages/{message_id}")
    return {"deleted": True, "channel_id": channel_id, "message_id": message_id}


def bridge_add_reaction(params: dict[str, Any]) -> Any:
    """Add an emoji reaction. For unicode emoji, pass the literal char (e.g. '👍').
    For custom emoji, pass 'name:id' form."""
    channel_id = params["channel_id"]
    message_id = params["message_id"]
    emoji = urllib.parse.quote(params["emoji"])
    _discord_request(
        "PUT", f"/channels/{channel_id}/messages/{message_id}/reactions/{emoji}/@me"
    )
    return {"reacted": True}


def bridge_get_user(params: dict[str, Any]) -> Any:
    """Resolve a Discord user ID to profile info."""
    user_id = params["user_id"]
    return _discord_request("GET", f"/users/{user_id}")


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

@dataclass
class BridgeTool:
    name: str
    description: str
    handler: Any
    input_schema: dict[str, Any]


BRIDGE_TOOLS: list[BridgeTool] = [
    BridgeTool(
        name="bridge_list_guilds",
        description="List all Discord servers the HUMMBL MCP bot is a member of.",
        handler=bridge_list_guilds,
        input_schema={"type": "object", "properties": {}},
    ),
    BridgeTool(
        name="bridge_list_channels",
        description="List all channels in a Discord guild (server) by guild id.",
        handler=bridge_list_channels,
        input_schema={
            "type": "object",
            "properties": {"guild_id": {"type": "string"}},
            "required": ["guild_id"],
        },
    ),
    BridgeTool(
        name="bridge_post_message",
        description="Post a message to a Discord channel. Content <= 2000 chars. Optional reply_to_message_id for threaded reply.",
        handler=bridge_post_message,
        input_schema={
            "type": "object",
            "properties": {
                "channel_id": {"type": "string"},
                "content": {"type": "string"},
                "reply_to_message_id": {"type": "string"},
            },
            "required": ["channel_id", "content"],
        },
    ),
    BridgeTool(
        name="bridge_read_recent",
        description="Read recent messages from a Discord channel (1-100, default 50).",
        handler=bridge_read_recent,
        input_schema={
            "type": "object",
            "properties": {
                "channel_id": {"type": "string"},
                "limit": {"type": "integer", "minimum": 1, "maximum": 100},
                "before_message_id": {"type": "string"},
            },
            "required": ["channel_id"],
        },
    ),
    BridgeTool(
        name="bridge_edit_message",
        description="Edit a bot-authored Discord message.",
        handler=bridge_edit_message,
        input_schema={
            "type": "object",
            "properties": {
                "channel_id": {"type": "string"},
                "message_id": {"type": "string"},
                "content": {"type": "string"},
            },
            "required": ["channel_id", "message_id", "content"],
        },
    ),
    BridgeTool(
        name="bridge_delete_message",
        description="Delete a Discord message (bot-authored, or any if bot has Manage Messages).",
        handler=bridge_delete_message,
        input_schema={
            "type": "object",
            "properties": {
                "channel_id": {"type": "string"},
                "message_id": {"type": "string"},
            },
            "required": ["channel_id", "message_id"],
        },
    ),
    BridgeTool(
        name="bridge_add_reaction",
        description="Add an emoji reaction to a Discord message. Unicode emoji as literal; custom as 'name:id'.",
        handler=bridge_add_reaction,
        input_schema={
            "type": "object",
            "properties": {
                "channel_id": {"type": "string"},
                "message_id": {"type": "string"},
                "emoji": {"type": "string"},
            },
            "required": ["channel_id", "message_id", "emoji"],
        },
    ),
    BridgeTool(
        name="bridge_get_user",
        description="Resolve a Discord user id to profile info.",
        handler=bridge_get_user,
        input_schema={
            "type": "object",
            "properties": {"user_id": {"type": "string"}},
            "required": ["user_id"],
        },
    ),
]


def get_tool_definitions() -> list[ToolDefinition]:
    return [
        ToolDefinition(name=t.name, description=t.description, input_schema=t.input_schema)
        for t in BRIDGE_TOOLS
    ]


def get_handlers() -> dict[str, Any]:
    return {t.name: t.handler for t in BRIDGE_TOOLS}
