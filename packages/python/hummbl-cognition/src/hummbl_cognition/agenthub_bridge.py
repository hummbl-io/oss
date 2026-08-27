"""AgentHub Bridge -- bidirectional sync between hummbl-cognition coordination bus
and Karpathy's AgentHub (github.com/karpathy/agenthub).

AgentHub is a Go binary + SQLite providing bare git repos + channel-based
message boards for AI agent coordination. This bridge maps between our
append-only TSV bus and AgentHub's HTTP API.

Status: READY TO ACTIVATE. Bridge is fully implemented and tested (49 tests).
Activation requires: a running agenthub binary + AGENTHUB_API_KEY env var.

Usage:
    python -m hummbl_cognition.agenthub_bridge sync --channel general --direction both
    python -m hummbl_cognition.agenthub_bridge sync --channel general --direction pull
    python -m hummbl_cognition.agenthub_bridge sync --channel general --direction push
    python -m hummbl_cognition.agenthub_bridge status

Environment:
    AGENTHUB_URL       Base URL of AgentHub server (default: http://localhost:8080)
    AGENTHUB_API_KEY   Agent API key for authentication (required)
    AGENTHUB_AGENT_ID  Agent identity on AgentHub (default: hummbl-cognition)

API Reference (karpathy/agenthub):
    GET  /api/channels                   List all channels
    POST /api/channels                   Create channel {name, description}
    GET  /api/channels/{name}/posts      List posts (supports ?since_id=N pagination)
    POST /api/channels/{name}/posts      Create post {content, parent_id?}
    GET  /api/posts/{id}                 Get single post
    GET  /api/posts/{id}/replies         Get replies to a post
    Auth: Authorization: Bearer <api_key>
"""

from __future__ import annotations

import argparse
import contextlib
import json
import logging
import os
import ssl
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Defaults
DEFAULT_AGENTHUB_URL = "http://localhost:8080"
DEFAULT_AGENT_ID = "hummbl-cognition"
DEFAULT_BUS_PATH = "_state/coordination/messages.tsv"
DEFAULT_STATE_FILE = "_state/cognition/agenthub_bridge_state.json"

# Bus TSV columns (0-indexed)
BUS_COLUMNS = ("timestamp", "from", "to", "type", "message")
BUS_SEPARATOR = "\t"


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------


@dataclass
class AgentHubPost:
    """A message from AgentHub's message board."""

    id: int
    channel_id: int
    agent_id: str
    content: str
    created_at: str
    parent_id: int | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AgentHubPost:
        return cls(
            id=data["id"],
            channel_id=data.get("channel_id", 0),
            agent_id=data.get("agent_id", "unknown"),
            content=data.get("content", ""),
            created_at=data.get("created_at", ""),
            parent_id=data.get("parent_id"),
        )


try:
    from hummbl_bus.bus_writer import escape_message, unescape_message
except ImportError:

    def escape_message(msg: str) -> str:  # type: ignore[misc]
        return msg.replace("\\", "\\\\").replace("\t", "\\t").replace("\n", "\\n")

    def unescape_message(msg: str) -> str:  # type: ignore[misc]
        return msg.replace("\\n", "\n").replace("\\t", "\t").replace("\\\\", "\\")


@dataclass
class BusMessage:
    """A message from our coordination bus (TSV row)."""

    timestamp: str
    sender: str
    recipient: str
    msg_type: str
    message: str

    def to_tsv_line(self) -> str:
        """Encode as a TSV line (no trailing newline)."""
        safe_msg = escape_message(self.message)
        return BUS_SEPARATOR.join(
            [
                self.timestamp,
                self.sender,
                self.recipient,
                self.msg_type,
                safe_msg,
            ]
        )

    @classmethod
    def from_tsv_line(cls, line: str) -> BusMessage | None:
        """Parse a TSV line into a BusMessage. Returns None on parse failure."""
        parts = line.rstrip("\n").split(BUS_SEPARATOR)
        if len(parts) < 5:
            return None
        # TSV format is strictly 5 columns. Content is in the 5th column.
        return cls(
            timestamp=parts[0],
            sender=parts[1],
            recipient=parts[2],
            msg_type=parts[3],
            message=unescape_message(parts[4]),
        )

    def to_agenthub_content(self) -> str:
        """Format bus message as AgentHub post content.

        Uses a structured prefix so the bridge can distinguish bridged
        messages from native AgentHub posts on pull.
        """
        return (
            f"[BUS:{self.msg_type}] from={self.sender} to={self.recipient} "
            f"ts={self.timestamp}\n{self.message}"
        )


@dataclass
class SyncState:
    """Persistent state for duplicate-free sync."""

    # Last AgentHub post ID we pulled (for pull direction)
    last_pulled_post_id: int = 0
    # Last bus line number we pushed (for push direction)
    last_pushed_bus_line: int = 0
    # Set of AgentHub post IDs we created (to avoid re-pulling our own posts)
    pushed_post_ids: list[int] = field(default_factory=list)
    # Channel name we're syncing
    channel: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SyncState:
        return cls(
            last_pulled_post_id=data.get("last_pulled_post_id", 0),
            last_pushed_bus_line=data.get("last_pushed_bus_line", 0),
            pushed_post_ids=data.get("pushed_post_ids", []),
            channel=data.get("channel", ""),
        )


# ---------------------------------------------------------------------------
# AgentHub HTTP client (stdlib only, urllib)
# ---------------------------------------------------------------------------


class AgentHubClient:
    """Minimal HTTP client for AgentHub's board API."""

    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        agent_id: str | None = None,
        timeout: int = 30,
    ):
        self.base_url = (
            base_url or os.environ.get("AGENTHUB_URL", DEFAULT_AGENTHUB_URL)
        ).rstrip("/")
        self.api_key = api_key or os.environ.get("AGENTHUB_API_KEY", "")
        self.agent_id = agent_id or os.environ.get(
            "AGENTHUB_AGENT_ID", DEFAULT_AGENT_ID
        )
        self.timeout = timeout

        if not self.api_key:
            raise ValueError(
                "AGENTHUB_API_KEY environment variable is required. "
                "Register an agent via POST /api/admin/agents or /api/register."
            )

    def _request(
        self,
        method: str,
        path: str,
        body: dict[str, Any] | None = None,
    ) -> dict[str, Any] | list[Any]:
        """Make an authenticated HTTP request to AgentHub.

        Returns parsed JSON response.
        Raises AgentHubError on HTTP or parse failures.
        """
        url = f"{self.base_url}{path}"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        data = None
        if body is not None:
            data = json.dumps(body).encode("utf-8")

        req = urllib.request.Request(url, data=data, headers=headers, method=method)

        try:
            # TLS: AgentHub defaults to HTTP (localhost), but supports HTTPS.
            # ssl.create_default_context() is the correct approach for HTTPS.
            ctx = None
            if url.startswith("https://"):
                ctx = ssl.create_default_context()

            with urllib.request.urlopen(req, timeout=self.timeout, context=ctx) as resp:
                resp_body = resp.read().decode("utf-8")
                if not resp_body:
                    return {}
                return json.loads(resp_body)
        except urllib.error.HTTPError as e:
            body_text = ""
            with contextlib.suppress(Exception):
                body_text = e.read().decode("utf-8")
            raise AgentHubError(f"HTTP {e.code} {method} {path}: {body_text}") from e
        except urllib.error.URLError as e:
            raise AgentHubError(f"Connection error {method} {path}: {e.reason}") from e

    # -- Channel operations --

    def list_channels(self) -> list[dict[str, Any]]:
        """GET /api/channels -- list all channels."""
        # Handles both bare list response and {"channels": [...]} envelope.
        result = self._request("GET", "/api/channels")
        if isinstance(result, list):
            return result
        return result.get("channels", [])

    def create_channel(self, name: str, description: str = "") -> dict[str, Any]:
        """POST /api/channels -- create a new channel.

        Channel names must match: ^[a-z0-9][a-z0-9_-]{0,30}$
        """
        result = self._request(
            "POST",
            "/api/channels",
            {
                "name": name,
                "description": description,
            },
        )
        return result if isinstance(result, dict) else {}

    def ensure_channel(self, name: str, description: str = "") -> None:
        """Create channel if it doesn't exist, ignore 409 Conflict."""
        try:
            self.create_channel(name, description)
            logger.info("Created AgentHub channel: %s", name)
        except AgentHubError as e:
            if "409" in str(e):
                logger.debug("Channel %s already exists", name)
            else:
                raise

    # -- Post operations --

    def list_posts(
        self,
        channel: str,
        since_id: int = 0,
    ) -> list[AgentHubPost]:
        """GET /api/channels/{name}/posts -- list posts in a channel.

        Uses since_id for pagination to only fetch new posts.
        """
        # Pagination: uses ?since_id=N per API reference in module docstring.
        path = f"/api/channels/{urllib.parse.quote(channel)}/posts"
        if since_id > 0:
            path += f"?since_id={since_id}"

        result = self._request("GET", path)
        posts_data = result if isinstance(result, list) else result.get("posts", [])
        return [AgentHubPost.from_dict(p) for p in posts_data]

    def create_post(
        self,
        channel: str,
        content: str,
        parent_id: int | None = None,
    ) -> AgentHubPost:
        """POST /api/channels/{name}/posts -- create a post.

        Content is capped at 32KB by AgentHub server.
        """
        body: dict[str, Any] = {"content": content}
        if parent_id is not None:
            body["parent_id"] = parent_id

        path = f"/api/channels/{urllib.parse.quote(channel)}/posts"
        result = self._request("POST", path, body)
        return AgentHubPost.from_dict(result if isinstance(result, dict) else {})


class AgentHubError(Exception):
    """Error communicating with AgentHub."""


# ---------------------------------------------------------------------------
# Bus I/O helpers
# ---------------------------------------------------------------------------


def _resolve_bus_path(bus_path: str | None = None) -> Path:
    """Resolve bus path from override, env, or package-relative location."""
    import subprocess as sp

    rel = bus_path or DEFAULT_BUS_PATH

    # BUS_CANONICAL_FILE_PATH: canonical override
    canonical = os.environ.get("BUS_CANONICAL_FILE_PATH", "").strip()
    if canonical and not bus_path:
        return Path(canonical)

    # Package-relative: always correct regardless of repo dir name.
    pkg_parent = Path(__file__).resolve().parents[2]
    pkg_bus = pkg_parent / rel
    if pkg_bus.parent.exists():
        return pkg_bus

    # Fallback: git toplevel + relative path.
    try:
        root = sp.check_output(
            ["git", "rev-parse", "--show-toplevel"],
            stderr=sp.DEVNULL,
            text=True,
            timeout=5,
        ).strip()
        if root:
            return Path(root) / rel
    except (sp.CalledProcessError, FileNotFoundError, sp.TimeoutExpired):
        pass
    return Path(rel)


def read_bus_lines(bus_path: Path) -> list[str]:
    """Read all lines from the coordination bus TSV."""
    if not bus_path.exists():
        return []
    return bus_path.read_text(encoding="utf-8").splitlines()


def append_bus_message(msg: BusMessage, bus_path: Path) -> None:
    """Append a message to the coordination bus using bus_writer if available.

    Falls back to direct file append with fcntl locking.
    """
    try:
        from hummbl_bus.bus_writer import post_message

        post_message(
            from_id=msg.sender,
            to_id=msg.recipient,
            msg_type=msg.msg_type,
            message=msg.message,
            bus_path=str(bus_path),
        )
    except ImportError as e:
        logger.warning("bus_writer unavailable, using direct append: %s", e)
        from hummbl_cognition._filelock import lock_file, unlock_file

        line = msg.to_tsv_line() + "\n"
        bus_path.parent.mkdir(parents=True, exist_ok=True)
        with open(bus_path, "a", encoding="utf-8") as f:
            lock_file(f)
            try:
                f.write(line)
            finally:
                unlock_file(f)


# ---------------------------------------------------------------------------
# Sync state persistence
# ---------------------------------------------------------------------------


def _resolve_state_path(state_path: str | None = None) -> Path:
    """Resolve state file path."""
    import subprocess as sp

    rel = state_path or DEFAULT_STATE_FILE
    try:
        root = sp.check_output(
            ["git", "rev-parse", "--show-toplevel"],
            stderr=sp.DEVNULL,
            text=True,
            timeout=5,
        ).strip()
        if root:
            return Path(root) / rel
    except (sp.CalledProcessError, FileNotFoundError, sp.TimeoutExpired):
        pass
    return Path(rel)


def load_sync_state(state_path: Path) -> SyncState:
    """Load sync state from disk."""
    if not state_path.exists():
        return SyncState()
    try:
        data = json.loads(state_path.read_text(encoding="utf-8"))
        return SyncState.from_dict(data)
    except (json.JSONDecodeError, KeyError) as e:
        logger.warning("Corrupt sync state, starting fresh: %s", e)
        return SyncState()


def save_sync_state(state: SyncState, state_path: Path) -> None:
    """Save sync state to disk."""
    state_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = state_path.with_suffix(".tmp")
    tmp.write_text(json.dumps(state.to_dict(), indent=2) + "\n", encoding="utf-8")
    tmp.replace(state_path)


# ---------------------------------------------------------------------------
# Message format mapping
# ---------------------------------------------------------------------------

# Prefix used in AgentHub posts to identify bridged bus messages
_BUS_PREFIX = "[BUS:"

# Valid bus message types (subset -- bridge accepts any but tags known ones)
_KNOWN_BUS_TYPES = {
    "PROPOSAL",
    "ACK",
    "STATUS",
    "SITREP",
    "BLOCKED",
    "DECISION",
    "QUESTION",
    "MILESTONE",
    "RECEIPT",
    "COMPLETE",
    "WIP_START",
    "WIP_END",
    "TASK_COMPLETE",
    "HEARTBEAT",
}


def bus_message_to_post_content(msg: BusMessage) -> str:
    """Convert a bus message to AgentHub post content."""
    return msg.to_agenthub_content()


def post_to_bus_message(post: AgentHubPost) -> BusMessage | None:
    """Convert an AgentHub post to a bus message.

    If the post was originally bridged FROM the bus (has [BUS:...] prefix),
    returns None to avoid echo loops.

    Native AgentHub posts are mapped to STATUS messages from the agent.
    """
    content = post.content

    # Skip posts that originated from our bus (bridged posts)
    if content.startswith(_BUS_PREFIX):
        return None

    # Map native AgentHub post to bus message
    # AgentHub uses SQLite CURRENT_TIMESTAMP: "YYYY-MM-DD HH:MM:SS" (no Z suffix).
    # Normalize to ISO 8601 with Z suffix for bus compatibility.
    try:
        ts = post.created_at
        # Normalize to UTC Z suffix if possible
        if ts and not ts.endswith("Z"):
            # Try parsing and reformatting
            for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"):
                try:
                    dt = datetime.strptime(ts, fmt).replace(tzinfo=timezone.utc)
                    ts = dt.strftime("%Y-%m-%dT%H:%M:%SZ")
                    break
                except ValueError:
                    continue
    except Exception:
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    sender = f"agenthub:{post.agent_id}"
    return BusMessage(
        timestamp=ts,
        sender=sender,
        recipient="all",
        msg_type="STATUS",
        message=f"[agenthub] {content[:4000]}",
    )


# ---------------------------------------------------------------------------
# Sync engine
# ---------------------------------------------------------------------------


def pull_from_agenthub(
    client: AgentHubClient,
    channel: str,
    bus_path: Path,
    state: SyncState,
    dry_run: bool = False,
) -> int:
    """Pull new posts from AgentHub and append to bus. Returns count of new messages."""
    posts = client.list_posts(channel, since_id=state.last_pulled_post_id)
    count = 0

    for post in posts:
        # Skip posts we pushed ourselves
        if post.id in state.pushed_post_ids:
            logger.debug("Skipping own post %d", post.id)
            if post.id > state.last_pulled_post_id:
                state.last_pulled_post_id = post.id
            continue

        msg = post_to_bus_message(post)
        if msg is None:
            # Bridged post -- skip to avoid echo
            logger.debug("Skipping bridged post %d", post.id)
            if post.id > state.last_pulled_post_id:
                state.last_pulled_post_id = post.id
            continue

        if dry_run:
            logger.info("[dry-run] Would append to bus: %s", msg.to_tsv_line())
        else:
            append_bus_message(msg, bus_path)
            logger.info("Pulled post %d -> bus: %s", post.id, msg.msg_type)

        count += 1
        if post.id > state.last_pulled_post_id:
            state.last_pulled_post_id = post.id

    return count


def push_to_agenthub(
    client: AgentHubClient,
    channel: str,
    bus_path: Path,
    state: SyncState,
    dry_run: bool = False,
) -> int:
    """Push new bus messages to AgentHub. Returns count of posted messages."""
    lines = read_bus_lines(bus_path)
    start = state.last_pushed_bus_line
    count = 0

    for i, line in enumerate(lines):
        if i < start:
            continue

        msg = BusMessage.from_tsv_line(line)
        if msg is None:
            continue

        # Skip messages that came from AgentHub (avoid echo)
        if msg.sender.startswith("agenthub:"):
            state.last_pushed_bus_line = i + 1
            continue

        content = bus_message_to_post_content(msg)

        if dry_run:
            logger.info("[dry-run] Would post to AgentHub: %s", content[:120])
        else:
            try:
                post = client.create_post(channel, content)
                state.pushed_post_ids.append(post.id)
                # Cap pushed_post_ids to last 1000 to avoid unbounded growth
                if len(state.pushed_post_ids) > 1000:
                    state.pushed_post_ids = state.pushed_post_ids[-500:]
                logger.info(
                    "Pushed bus line %d -> post %d: %s",
                    i,
                    post.id,
                    msg.msg_type,
                )
            except AgentHubError as e:
                logger.error("Failed to push bus line %d: %s", i, e)
                # Don't advance past failures -- retry next run
                break

        count += 1
        state.last_pushed_bus_line = i + 1

    return count


def sync(
    channel: str,
    direction: str = "both",
    bus_path: str | None = None,
    state_path: str | None = None,
    base_url: str | None = None,
    api_key: str | None = None,
    dry_run: bool = False,
) -> dict[str, int]:
    """Run a sync cycle. Returns {pulled: N, pushed: N}.

    direction: 'pull', 'push', or 'both'
    """
    resolved_bus = _resolve_bus_path(bus_path)
    resolved_state = _resolve_state_path(state_path)

    client = AgentHubClient(base_url=base_url, api_key=api_key)
    state = load_sync_state(resolved_state)
    state.channel = channel

    # Ensure channel exists before syncing
    if not dry_run:
        client.ensure_channel(
            channel,
            description="HUMMBL coordination bus bridge",
        )

    pulled = 0
    pushed = 0

    if direction in ("pull", "both"):
        pulled = pull_from_agenthub(
            client, channel, resolved_bus, state, dry_run=dry_run
        )

    if direction in ("push", "both"):
        pushed = push_to_agenthub(client, channel, resolved_bus, state, dry_run=dry_run)

    if not dry_run:
        save_sync_state(state, resolved_state)

    return {"pulled": pulled, "pushed": pushed}


def show_status(state_path: str | None = None) -> int:
    """Print current bridge state."""
    resolved = _resolve_state_path(state_path)
    state = load_sync_state(resolved)

    print(f"State file: {resolved}")
    print(f"Channel: {state.channel or '(not set)'}")
    print(f"Last pulled post ID: {state.last_pulled_post_id}")
    print(f"Last pushed bus line: {state.last_pushed_bus_line}")
    print(f"Pushed post IDs tracked: {len(state.pushed_post_ids)}")

    return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m hummbl_cognition.agenthub_bridge",
        description="AgentHub Bridge -- sync coordination bus with AgentHub",
    )
    parser.add_argument(
        "--bus",
        help="Override bus TSV path",
    )
    parser.add_argument(
        "--state",
        help="Override sync state file path",
    )
    parser.add_argument(
        "--url",
        help="AgentHub base URL (or AGENTHUB_URL env var)",
    )
    parser.add_argument(
        "--api-key",
        help="AgentHub API key (or AGENTHUB_API_KEY env var)",
    )

    sub = parser.add_subparsers(dest="command", help="Commands")

    p_sync = sub.add_parser("sync", help="Sync messages between bus and AgentHub")
    p_sync.add_argument(
        "--channel",
        required=True,
        help="AgentHub channel name to sync with",
    )
    p_sync.add_argument(
        "--direction",
        choices=["pull", "push", "both"],
        default="both",
        help="Sync direction (default: both)",
    )
    p_sync.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would happen without making changes",
    )

    sub.add_parser("status", help="Show current bridge sync state")

    return parser


def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )

    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        return 2

    if args.command == "status":
        return show_status(state_path=args.state)

    if args.command == "sync":
        try:
            result = sync(
                channel=args.channel,
                direction=args.direction,
                bus_path=args.bus,
                state_path=args.state,
                base_url=args.url,
                api_key=args.api_key,
                dry_run=args.dry_run,
            )
        except (AgentHubError, ValueError) as e:
            print(f"ERROR: {e}", file=sys.stderr)
            return 1

        prefix = "[dry-run] " if args.dry_run else ""
        print(f"{prefix}Pulled: {result['pulled']}, Pushed: {result['pushed']}")
        return 0

    parser.print_help()
    return 2


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
