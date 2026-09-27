"""Discord DM/channel poller — Bot API -> envelopes.

Polls one or more channel IDs for messages after a watermark. A DM to
the bot is just a channel the user shares with it — same endpoint.

Message-id anchor: Discord snowflake ``message.id`` is globally unique
and monotonic — perfect dedup + watermark key.
"""

from __future__ import annotations

import json
import logging
import time
import urllib.request

from .envelope import InboundEnvelope

log = logging.getLogger("bus-ingress-discord")

_API = "https://discord.com/api/v10"


def fetch_messages(
    token: str, channel_id: str, *, after: str | None = None, limit: int = 25
) -> list[dict]:
    url = f"{_API}/channels/{channel_id}/messages?limit={limit}"
    if after:
        url += f"&after={after}"
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bot {token}",
            "User-Agent": "hummbl-bus-ingress (poll)",
        },
    )
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read())


def msg_to_envelope(msg: dict, *, bot_id: str = "") -> InboundEnvelope | None:
    author = msg.get("author", {})
    if bot_id and author.get("id") == bot_id:
        return None  # our own messages
    content = (msg.get("content") or "").strip()
    if not content:
        return None  # attachment-only / embed messages
    return InboundEnvelope(
        channel="discord",
        channel_msg_id=msg.get("id", ""),
        # Immutable snowflake ID, not username (usernames are editable).
        sender_addr=str(author.get("id") or author.get("username") or "unknown"),
        received_at=msg.get("timestamp", "1970-01-01T00:00:00Z"),
        body=content,
        meta={
            "guild": msg.get("guild_id"),
            "channel": msg.get("channel_id"),
            "username": author.get("username"),
        },
    )


def run_poller(
    token: str,
    channel_ids: list[str],
    normalizer,
    *,
    bot_id: str = "",
    poll_seconds: int = 15,
    watermark_path: str | None = None,
) -> None:
    """Watermark-persistent poll loop over N channels."""
    watermarks = _load_watermarks(watermark_path)
    while True:
        for cid in channel_ids:
            try:
                for msg in fetch_messages(token, cid, after=watermarks.get(cid)):
                    env = msg_to_envelope(msg, bot_id=bot_id)
                    if env is not None:
                        result = normalizer.handle(env)
                        log.info("discord %s -> %s", env.channel_msg_id, result.status)
                    watermarks[cid] = msg["id"]
                _save_watermarks(watermark_path, watermarks)
            except Exception as e:
                log.warning("discord poll %s failed: %s", cid, e)
        time.sleep(poll_seconds)


def _load_watermarks(path: str | None) -> dict:
    if path:
        try:
            return json.loads(open(path).read())
        except Exception:
            return {}
    return {}


def _save_watermarks(path: str | None, w: dict) -> None:
    if path:
        try:
            with open(path, "w") as f:
                json.dump(w, f)
        except Exception as e:
            log.warning("watermark save failed: %s", e)
