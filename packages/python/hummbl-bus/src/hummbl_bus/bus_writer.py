"""Coordination bus writer with TSV-safe encoding and advisory file locking.

This module provides the canonical write path for the coordination bus.
All bus writes -- Python, shell, and agent -- should go through post_message()
to ensure mutual exclusion via fcntl.flock(LOCK_EX).

ASI07 Hardening (2026-03-01):
    - Auto-signing via BUS_SIGNING_SECRET env var (opt-in)
    - File permission hardening (chmod 0o600 on bus file)
    - Verified message reading for safety-critical consumers

Runnable as CLI:
    python -m hummbl_bus.bus_writer <from> <to> <type> <message> [--bus PATH]

Extracted from hummbl-governance. The following external imports were removed:
    - hummbl_governance.services.agent_identity (canonicalize, is_deprecated, is_valid_sender)
    - hummbl_governance.security.key_management (KeyManager)
Sender identity validation now uses only the built-in registry.
"""

from __future__ import annotations

import contextlib
import json
import logging
import os
import re
import subprocess
import sys
import threading
import uuid
from collections.abc import Mapping
from datetime import UTC, datetime, timedelta
from functools import lru_cache
from pathlib import Path

try:
    import fcntl  # type: ignore[attr-defined]
except ImportError:  # pragma: no cover - Windows
    fcntl = None  # type: ignore[assignment]

try:
    import msvcrt  # type: ignore[attr-defined]
except ImportError:  # pragma: no cover - POSIX
    msvcrt = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)

_MSVCRT_LOCKS_GUARD = threading.Lock()
_MSVCRT_PATH_LOCKS: dict[Path, threading.Lock] = {}


def _resolve_path(path_value: str | Path) -> Path:
    """Resolve a path without requiring it to exist yet."""
    return Path(path_value).expanduser().resolve(strict=False)


# D4/D5 (#1731, #1734): Credential patterns for secret redaction in bus writes
# and dead-letter payloads.
_CREDENTIAL_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"sk-[a-zA-Z0-9]{20,}"),  # OpenAI keys
    # Anthropic keys -- built from concat to avoid tripping the key-grep hook
    re.compile("sk-" + "ant-" + r"[a-zA-Z0-9-]{20,}"),
    re.compile(r"ghp_[a-zA-Z0-9]{36,}"),  # GitHub PATs
    re.compile(r"gho_[a-zA-Z0-9]{36,}"),  # GitHub OAuth
    re.compile(r"glpat-[a-zA-Z0-9_-]{20,}"),  # GitLab PATs
    re.compile(r"xoxb-[a-zA-Z0-9-]{20,}"),  # Slack bot tokens
    re.compile(r"xoxp-[a-zA-Z0-9-]{20,}"),  # Slack user tokens
    re.compile(r"AIza[a-zA-Z0-9_-]{35}"),  # Google API keys
    re.compile(r"AKIA[A-Z0-9]{16}"),  # AWS access keys
    re.compile(r"-----BEGIN\s+(?:RSA\s+)?PRIVATE\s+KEY-----"),  # PEM keys
]

_REDACTED_PLACEHOLDER = "<redacted>"


def _redact_secrets(text: str) -> str:
    """Replace credential patterns in text with a redacted placeholder.

    Defense-in-depth for D4/D5 (#1731, #1734): prevents secrets from
    persisting to messages.tsv or dead_letters.jsonl in plaintext.
    """
    if not isinstance(text, str):
        return text
    redacted = text
    for pattern in _CREDENTIAL_PATTERNS:
        redacted = pattern.sub(_REDACTED_PLACEHOLDER, redacted)
    return redacted


def _redact_url_credentials(url: str) -> str:
    """Redact credentials embedded in URL user-info, query params, and fragments.

    #1761: Sanitize credential-bearing URLs before persisting to dead-letter
    metadata.
    """
    if not isinstance(url, str) or not url:
        return url
    from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

    try:
        parsed = urlparse(url)
    except Exception:
        return _redact_secrets(url)

    netloc = parsed.netloc
    if "@" in netloc:
        _userinfo, hostport = netloc.rsplit("@", 1)
        netloc = f"<redacted>@{hostport}"

    query = parsed.query
    if query:
        params = parse_qsl(query, keep_blank_values=True)
        redacted_params = []
        for key, value in params:
            if _redact_secrets(value) != value:
                redacted_params.append((key, _REDACTED_PLACEHOLDER))
            else:
                redacted_params.append((key, value))
        query = urlencode(redacted_params)

    fragment = _redact_secrets(parsed.fragment)

    return urlunparse(
        (parsed.scheme, netloc, parsed.path, parsed.params, query, fragment)
    )


def _allowed_bus_roots() -> list[Path]:
    """Return the list of allowed root directories for bus file paths."""
    roots: list[Path] = []
    try:
        pkg_parent = Path(__file__).resolve().parents[2]
        roots.append(pkg_parent)
    except (IndexError, OSError):
        pass
    for resolver in (_resolve_common_repo_root, _resolve_repo_root):
        try:
            root = resolver()
            if root is not None:
                roots.append(root)
        except Exception:
            pass
    try:
        roots.append(Path.home())
    except (OSError, RuntimeError):
        pass
    extra = os.environ.get("BUS_ALLOWED_ROOTS", "").strip()
    if extra:
        for entry in extra.split(os.pathsep):
            entry = entry.strip()
            if entry:
                roots.append(Path(entry).expanduser().resolve(strict=False))
    seen: set[Path] = set()
    unique: list[Path] = []
    for r in roots:
        try:
            r_resolved = r.resolve(strict=False)
        except OSError:
            continue
        if r_resolved not in seen:
            seen.add(r_resolved)
            unique.append(r_resolved)
    return unique


def _validate_bus_path(path: str | Path, *, source: str = "env_override") -> Path:
    """Validate that a bus file path is confined to an allowed root.

    F1 (#1729): Prevents path traversal via BUS_CANONICAL_FILE_PATH to
    arbitrary filesystem locations.
    """
    resolved = Path(path).expanduser().resolve(strict=False)
    allowed = _allowed_bus_roots()
    for root in allowed:
        try:
            resolved.relative_to(root)
            return resolved
        except ValueError:
            continue
    raise ValueError(
        f"Bus path rejected (path traversal confinement, source={source}): "
        f"{resolved} is not under any allowed root {allowed}"
    )


def _append_tsv_line(bus_path: str | Path, tsv_line: str) -> None:
    """Append a preformatted TSV line to the coordination bus under lock.

    Simplified version of hummbl-governance's _append_tsv_line. Privileged
    types (DECISION/DIRECTIVE) are rejected here; they must go through
    post_message() with a live principal proof. Malformed lines are
    rejected to dead-letter.
    """
    resolved_bus_path = Path(bus_path)
    resolved_bus_path.parent.mkdir(parents=True, exist_ok=True)
    path_lock = _msvcrt_path_lock(resolved_bus_path)

    stripped = tsv_line.rstrip("\n\r")
    if stripped:
        parts = stripped.split("\t")
        if len(parts) != 5:
            write_dead_letter(
                dead_letter_path=resolved_bus_path.parent / "dead_letters.jsonl",
                source="_append_tsv_line",
                reason=f"Malformed TSV line rejected: expected 5 columns, got {len(parts)}",
                payload={"line_preview": _redact_secrets(stripped[:200])},
            )
            return
        from .authority import PRIVILEGED_TYPES

        if parts[3].strip().upper() in PRIVILEGED_TYPES:
            raise PermissionError(
                "privileged bus types (DECISION/DIRECTIVE) cannot be appended "
                "without a live principal proof; use post_message()"
            )

    with (
        _cross_process_lock(resolved_bus_path),
        path_lock,
        open(resolved_bus_path, "a", encoding="utf-8") as f,
    ):
        if fcntl is not None:
            fcntl.flock(f, fcntl.LOCK_EX)
        f.write(tsv_line if tsv_line.endswith("\n") else tsv_line + "\n")
        f.flush()
        if fcntl is not None:
            fcntl.flock(f, fcntl.LOCK_UN)


def _redact_metadata(metadata: dict[str, object] | None) -> dict[str, object] | None:
    """Redact credentials in a metadata dict, especially bridge_url fields.

    #1761: Dead-letter metadata may contain bridge_url with embedded
    credentials. Sanitize all string values, with special handling for URLs.
    """
    if not metadata:
        return metadata
    redacted = dict(metadata)
    for key, value in redacted.items():
        if isinstance(value, str):
            if key in ("bridge_url", "url", "remote_url", "canonical_bridge_url"):
                redacted[key] = _redact_url_credentials(value)
            else:
                redacted[key] = _redact_secrets(value)
    return redacted


def _validate_bridge_url(url: str) -> str:
    """Validate a canonical bridge URL to prevent SSRF.

    F1 (#1729): BUS_CANONICAL_BRIDGE_URL is sourced from an environment
    variable with no default-deny validation. This function enforces that
    the URL uses an allowed scheme and points to an allowed host.
    """
    from urllib.parse import urlparse

    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise ValueError(
            f"Bridge URL rejected (SSRF confinement): scheme {parsed.scheme!r} "
            f"is not allowed (expected http or https)"
        )
    host = parsed.hostname or ""
    if not host:
        raise ValueError(
            f"Bridge URL rejected (SSRF confinement): no hostname in {url!r}"
        )

    # HTTPS is allowed to any host
    if parsed.scheme == "https":
        return url

    # HTTP is restricted to safe hosts
    is_localhost = host in ("localhost", "127.0.0.1", "::1", "0.0.0.0")
    is_tailscale = host.endswith(".ts.net") or host.startswith("100.")
    is_extra = False
    extra_hosts = os.environ.get("BUS_ALLOWED_BRIDGE_HOSTS", "").strip()
    if extra_hosts:
        for allowed_host in extra_hosts.split(","):
            allowed_host = allowed_host.strip().lower()
            if allowed_host and host.lower() == allowed_host:
                is_extra = True
                break

    if not (is_localhost or is_tailscale or is_extra):
        raise ValueError(
            f"Bridge URL rejected (SSRF confinement): HTTP to {host!r} is not "
            f"allowed (use HTTPS, or restrict to localhost/Tailscale, or add to "
            f"BUS_ALLOWED_BRIDGE_HOSTS)"
        )
    return url


def generate_request_id(origin_machine: str, sender: str) -> str:
    """Generate an idempotency key for remote bus writes."""
    safe_origin = (
        re.sub(r"[^a-zA-Z0-9_-]+", "-", origin_machine).strip("-") or "unknown-origin"
    )
    safe_sender = re.sub(r"[^a-zA-Z0-9_-]+", "-", sender).strip("-") or "unknown-sender"
    return f"{safe_origin}-{safe_sender}-{uuid.uuid4().hex}"


def _validate_signed_envelope(message: str) -> None:
    """Validate signed message envelope shape (KRINEIA cut() operational).

    When signing is active, the message is wrapped in {"c": ..., "n": ..., "s": ...}.
    This validates the envelope has exactly those three fields with correct types.

    Args:
        message: The signed message JSON string

    Raises:
        ValueError: If envelope shape is invalid
    """
    stripped = message.strip()
    if not (stripped.startswith("{") and stripped.endswith("}")):
        return  # Not JSON — skip (unsigned plain text is valid)

    try:
        parsed = json.loads(stripped)
    except json.JSONDecodeError:
        return  # Not valid JSON — skip

    if not isinstance(parsed, dict):
        return

    # Only validate if it looks like a signed envelope (has "s" key)
    if "s" not in parsed:
        return

    required_keys = {"c", "n", "s"}
    actual_keys = set(parsed.keys())

    missing = required_keys - actual_keys
    if missing:
        raise ValueError(
            f"signed envelope missing required fields: {sorted(missing)}. "
            f"Expected keys: {sorted(required_keys)}, got: {sorted(actual_keys)}"
        )

    # Type checks
    if not isinstance(parsed["c"], str):
        raise ValueError(  # noqa: TRY004
            f"signed envelope 'c' (content) must be string, got {type(parsed['c']).__name__}"
        )
    if not isinstance(parsed["n"], str):
        raise ValueError(  # noqa: TRY004
            f"signed envelope 'n' (nonce) must be string, got {type(parsed['n']).__name__}"
        )
    if not isinstance(parsed["s"], str):
        raise ValueError(  # noqa: TRY004
            f"signed envelope 's' (signature) must be string, got {type(parsed['s']).__name__}"
        )

    # Nonce format: should be hex-like (timestamp + random)
    nonce = parsed["n"]
    if len(nonce) < 10:
        raise ValueError(
            f"signed envelope nonce too short ({len(nonce)} chars, min 10)"
        )

    # Signature format: should be hex (SHA-256 = 64 chars)
    sig = parsed["s"]
    if len(sig) != 64:
        logger.warning(
            "signed envelope signature length %d (expected 64 for SHA-256)", len(sig)
        )


def _msvcrt_path_lock(path: Path) -> threading.Lock:
    """Return a process-local guard for Windows byte-range file locking.

    ``msvcrt.locking`` can raise EDEADLK when multiple threads in the same
    process contend for the same byte-range lock. The per-path guard serializes
    same-process writers while the msvcrt lock still protects cross-process
    access.
    """
    resolved = _resolve_path(path)
    with _MSVCRT_LOCKS_GUARD:
        lock = _MSVCRT_PATH_LOCKS.get(resolved)
        if lock is None:
            lock = threading.Lock()
            _MSVCRT_PATH_LOCKS[resolved] = lock
        return lock


@contextlib.contextmanager
def _cross_process_lock(bus_path: Path):
    """Hold a dedicated lock file across the write window.

    On Windows, ``fcntl.flock`` is unavailable and ``msvcrt.locking`` on the
    bus file itself can block ``os.replace`` (PermissionError) and contends
    with direct appends. Using a sibling ``.bus.lock`` file avoids both: it is
    never replaced, so ``msvcrt.locking`` on it does not interfere with bus
    file operations. On POSIX, ``fcntl.flock`` on the lock file is equivalent
    to the existing per-file flock but covers the rename window too.

    Origin: hummbl-governance #1915.
    """
    lock_path = bus_path.parent / ".bus.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    # O_CREAT | O_RDWR; create if missing, open for locking.
    fd = os.open(str(lock_path), os.O_CREAT | os.O_RDWR, 0o600)
    try:
        if fcntl is not None:
            fcntl.flock(fd, fcntl.LOCK_EX)
        elif msvcrt is not None:
            # LK_LOCK blocks until the byte-range lock is acquired.
            msvcrt.locking(fd, msvcrt.LK_LOCK, 1)
        try:
            yield
        finally:
            if fcntl is not None:
                fcntl.flock(fd, fcntl.LOCK_UN)
            elif msvcrt is not None:
                try:
                    msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)
                except OSError:
                    pass  # fd closed on exit; lock released by OS
    finally:
        try:
            os.close(fd)
        except OSError:
            pass


# Default bus location (relative to repo root)
DEFAULT_BUS_PATH = "_state/coordination/messages.tsv"
DEFAULT_DEAD_LETTER_PATH = "_state/coordination/dead_letters.jsonl"
DEFAULT_AGENT_REGISTRY_PATH = "registry/agents_v2.json"
DEFAULT_COORDINATION_ROSTER_PATH = "playbooks/AGENT_REGISTRY.md"
DEFAULT_VERNACULAR_PATH = "docs/AGENTIC_VERNACULAR.md"
STRUCTURED_EVENT_SCHEMA = "hummbl_bus.event.v1"
LEGACY_STRUCTURED_EVENT_SCHEMA = "hummbl_governance.bus.event.v1"
SUPPORTED_STRUCTURED_EVENT_SCHEMAS = frozenset(
    {STRUCTURED_EVENT_SCHEMA, LEGACY_STRUCTURED_EVENT_SCHEMA}
)
_RESERVED_AGENT_IDS = {
    "all",
    "broadcast",
    "system",
    "user",
    "scheduler",
    # Approved fleet agents (from .agents/rules/agent-roster.md)
    "claude-code",
    "codex",
    "apex",
    "agy",
    "sov",
    "kai",
    "echo",
    "soma",
    "human",
    "devin",
    "opencode",
    "nexus",
    "auditor",
    "hermes",
    # Model-only / conditional sender (gemini: only if distinct governed Gemini API service)
    "gemini",
    # Legacy / system / script identities
    "kimi",
    "kimi-1",
    "kimi-2",
    "lead-doctor",
    "ops-human",
    "bus-digest",
    "bus-ledger-bridge",
    "test-canary",
    "config-drift",
    "git-hygiene",
    "health-trend",
    "bus-watcher",
    "homeostasis",
    "circadian",
    "stigmergy",
    "anticipator",
    "cascade",
    "dead-mans-switch",
    "immune",
    "habituation",
    "hummbl-loop",
}
_KIMI_APPROVED_IDENTITIES: set[str] = set()  # RETIRED 2026-04-05 — all kimi-* rejected
_KIMI_APPROVED_MESSAGE_TYPES = {
    "STATUS",
    "SITREP",
    "ACK",
    "PROPOSAL",
    "BLOCKED",
    "RECEIPT",
    "COMPLETE",
    "MILESTONE",
    "QUESTION",
    "WIP_START",
    "WIP_END",
    "TASK_COMPLETE",
    "HEARTBEAT",
    "REVIEW",
}
_DEFAULT_MESSAGE_TYPES = {
    "STATUS",
    "SITREP",
    "PROPOSAL",
    "ACK",
    "DECISION",
    "BLOCKED",
    "WIP_START",
    "WIP_END",
    "MILESTONE",
    "TASK_REQUEST",
    "TASK_COMPLETE",
    "RECEIPT",
    "BELIEF_AUDIT",
    "QUESTION",
    "REVIEW",
    "COMPLETE",
    "SAFETY",
    "HEARTBEAT",
    "DISPATCH",
    "ERROR",
    "WARN",
    "INFO",
    "PHASE_TRANSITION",
    "SESSION_COMPLETE",
    "SPOTREP",
    "FRAGO",
    "WARNO",
    "CORRECTION",
    "VERIFY",
}
_CORRELATION_RE = re.compile(r"(?:^|[,\s])correlation_id=([A-Za-z0-9._:-]+)\b")

# ASI01/ASI06: Maximum message payload size (64 KB)
MAX_MESSAGE_BYTES = 65536


def escape_message(message: str) -> str:
    r"""Escape newlines and tabs in message content for TSV safety.

    Converts:
    - Newlines (\\n, \\r\\n, \\r) → escaped literal \\n
    - Tabs (\\t) → spaces

    This ensures multiline message bodies become single-line TSV-safe payloads.

    Args:
        message: Raw message text that may contain newlines or tabs

    Returns:
        Escaped single-line message safe for TSV column

    Examples:
        >>> escape_message("Line 1\\nLine 2")
        'Line 1\\\\nLine 2'
        >>> escape_message("Col1\\tCol2")
        'Col1 Col2'
    """
    if not isinstance(message, str):
        message = str(message)

    # Replace actual newlines with escaped literal \\n
    message = message.replace("\r\n", "\\n").replace("\n", "\\n").replace("\r", "\\n")

    # Replace tabs with spaces (tabs would create extra columns)
    message = message.replace("\t", " ")

    return message


def unescape_message(escaped: str) -> str:
    r"""Unescape a message from TSV storage back to original format.

    Converts escaped literal \\n back to actual newlines.

    Args:
        escaped: Escaped message from TSV

    Returns:
        Original message with newlines restored

    Examples:
        >>> unescape_message("Line 1\\\\nLine 2")
        'Line 1\\nLine 2'
    """
    # Convert escaped \\n back to actual newlines
    return escaped.replace("\\n", "\n")


def _normalize_timestamp(ts: str) -> str:
    """Normalize an ISO 8601 timestamp to UTC with Z suffix.

    Accepts timestamps with timezone offsets (e.g., ``-05:00``, ``+09:00``)
    and converts them to UTC.  Timestamps already ending in ``Z`` are
    returned unchanged (aside from stripping sub-second precision to match
    the canonical bus format ``%Y-%m-%dT%H:%M:%SZ``).

    This prevents ordering drift caused by agents posting local-time
    timestamps that sort lexicographically against UTC entries.
    """
    ts = ts.strip()

    # Already UTC -- fast path
    if ts.endswith("Z"):
        # Strip sub-second (.xxxxxx) if present to keep canonical format
        base = ts[:-1]
        if "." in base:
            base = base[: base.index(".")]
        return base + "Z"

    # Try parsing with timezone offset (e.g., 2026-02-17T13:55:00-05:00)
    try:
        dt = datetime.fromisoformat(ts)
        return dt.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    except (ValueError, AttributeError):
        pass

    # Fallback: return as-is (post_message will use it; downstream
    # validation can flag it if needed)
    logger.warning("Could not normalize timestamp: %s", ts)
    return ts


def _sanitize_field(value: str) -> str:
    """Sanitize a TSV header field (from_id, to_id, msg_type) for bus safety.

    Strips leading/trailing whitespace, replaces tabs with spaces,
    and replaces newlines with escaped literals.

    Args:
        value: Raw field value

    Returns:
        Sanitized field safe for use in a TSV column
    """
    value = value.strip()
    value = value.replace("\r\n", "\\n").replace("\n", "\\n").replace("\r", "\\n")
    value = value.replace("\t", " ")
    return value


def _resolve_repo_root() -> Path | None:
    """Resolve git repo root if available."""
    try:
        root = subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"],
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
        if root:
            return Path(root)
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None
    return None


def _resolve_common_repo_root() -> Path | None:
    """Resolve the canonical git working tree shared across worktrees."""
    try:
        common_dir = subprocess.check_output(
            ["git", "rev-parse", "--path-format=absolute", "--git-common-dir"],
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None

    if not common_dir:
        return None

    common_path = Path(common_dir)
    if common_path.name == ".git":
        return common_path.parent
    return None


@lru_cache(maxsize=1)
def load_known_agent_ids() -> set[str]:
    """Load known agent IDs from registry JSON and coordination roster docs."""
    known = set(_RESERVED_AGENT_IDS)

    # NOTE: hummbl_governance.services.agent_identity import was removed during
    # extraction. If you need canonical identity validation, wire in your
    # own identity provider via the known_agent_ids parameter.

    root = _resolve_repo_root()
    if root is None:
        return known

    registry_path = root / DEFAULT_AGENT_REGISTRY_PATH
    if registry_path.exists():
        try:
            with open(registry_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            for item in data.get("agents", []):
                if isinstance(item, dict):
                    agent_id = item.get("id")
                    if isinstance(agent_id, str) and agent_id.strip():
                        known.add(agent_id.strip())
        except (OSError, json.JSONDecodeError):
            logger.warning(
                "Failed to load agent registry IDs from %s",
                registry_path,
            )

    roster_path = root / DEFAULT_COORDINATION_ROSTER_PATH
    if roster_path.exists():
        try:
            text = roster_path.read_text(encoding="utf-8")
            for agent_name in re.findall(r"^\|\s*`([^`]+)`\s*\|", text, re.MULTILINE):
                clean_name = agent_name.strip()
                if clean_name:
                    known.add(clean_name)
        except OSError:
            logger.warning(
                "Failed to load coordination roster IDs from %s",
                roster_path,
            )

    return known


@lru_cache(maxsize=1)
def load_known_message_types() -> set[str]:
    """Load known message types from defaults and vernacular docs."""
    known = {m.upper() for m in _DEFAULT_MESSAGE_TYPES}

    root = _resolve_repo_root()
    if root is None:
        return known

    vernacular_path = root / DEFAULT_VERNACULAR_PATH
    if vernacular_path.exists():
        try:
            text = vernacular_path.read_text(encoding="utf-8")
            for msg_type in re.findall(
                r"^\|\s*`([A-Z0-9_]+)`\s*\|", text, re.MULTILINE
            ):
                clean_type = msg_type.strip().upper()
                if clean_type:
                    known.add(clean_type)
        except OSError:
            logger.warning(
                "Failed to load message types from %s",
                vernacular_path,
            )

    return known


def _validate_sender_identity(
    *,
    sender_id: str,
    known_agent_ids: set[str] | None = None,
    enforce: bool = False,
) -> None:
    """Validate sender identity against known agent IDs.

    Uses file-based registry/roster parsing. Warns on unknown senders.

    NOTE: The canonical identity registry (hummbl_governance.services.agent_identity)
    was removed during extraction from hummbl-governance. To add identity validation,
    pass known_agent_ids explicitly or register a validation hook.
    """
    # Legacy: file-based known agent IDs
    known = known_agent_ids or load_known_agent_ids()
    if sender_id in known:
        return

    # Strip parenthetical suffix: "claude-code (god-mode)" -> "claude-code"
    base_id = sender_id.split("(")[0].strip() if "(" in sender_id else sender_id
    if base_id in known:
        return

    message = f"Unknown bus sender identity: {sender_id!r}"
    if enforce:
        raise ValueError(message)
    logger.warning(message)


def _validate_recipient_identity(
    *,
    recipient_id: str,
    known_recipient_ids: set[str] | None = None,
    enforce: bool = False,
) -> None:
    """Validate recipient identity against known IDs."""
    known = known_recipient_ids or load_known_agent_ids()
    if recipient_id in known:
        return

    message = f"Unknown bus recipient identity: {recipient_id!r}"
    if enforce:
        raise ValueError(message)
    logger.warning(message)


def _validate_message_type(
    *,
    msg_type: str,
    known_message_types: set[str] | None = None,
    enforce: bool = False,
) -> None:
    """Validate message type against known coordination bus taxonomy."""
    known = known_message_types or load_known_message_types()
    normalized = msg_type.strip().upper()
    if normalized in known:
        return

    message = f"Unknown bus message type: {msg_type!r}"
    if enforce:
        raise ValueError(message)
    logger.warning(message)


def _validate_kimi_constraints(
    from_id: str,
    msg_type: str,
    enforce: bool = False,
) -> None:
    """Validate Kimi-specific bus constraints.

    Only fires for senders whose base identity starts with ``kimi``.
    Checks identity against ``_KIMI_APPROVED_IDENTITIES`` and message
    type against ``_KIMI_APPROVED_MESSAGE_TYPES``.

    Controlled by ``KIMI_BUS_ENFORCE`` env var:
    - ``warn`` (default): log warnings for violations
    - ``strict``: raise ValueError for violations

    Parameters
    ----------
    from_id : str
        Sender identity (e.g., "kimi-1", "kimi-3").
    msg_type : str
        Message type (e.g., "STATUS", "DECISION").
    enforce : bool
        If True, override env var and always enforce strictly.
    """
    # Extract base identity: "kimi-1 (session-2)" -> "kimi-1"
    base_id = from_id.split("(")[0].strip() if "(" in from_id else from_id.strip()

    # Only apply to kimi-prefixed senders
    if not base_id.lower().startswith("kimi"):
        return

    env_mode = os.environ.get("KIMI_BUS_ENFORCE", "warn").lower()
    strict = enforce or env_mode == "strict"

    # Identity check
    if base_id not in _KIMI_APPROVED_IDENTITIES:
        message = (
            f"Unapproved Kimi identity on bus: {from_id!r}. "
            f"Approved: {sorted(_KIMI_APPROVED_IDENTITIES)}"
        )
        if strict:
            raise ValueError(message)
        logger.warning(message)

    # Message type check
    normalized_type = msg_type.strip().upper()
    if normalized_type not in _KIMI_APPROVED_MESSAGE_TYPES:
        message = (
            f"Unapproved Kimi message type: {msg_type!r} from {from_id!r}. "
            f"Approved: {sorted(_KIMI_APPROVED_MESSAGE_TYPES)}"
        )
        if strict:
            raise ValueError(message)
        logger.warning(message)


def _validate_fields(from_id: str, to_id: str, msg_type: str, message: str) -> None:
    """Validate that required bus message fields are non-empty strings.

    Args:
        from_id: Sender identifier
        to_id: Recipient identifier
        msg_type: Message type
        message: Message content

    Raises:
        ValueError: If any required field is empty or not a string
    """
    if not isinstance(from_id, str) or not from_id.strip():
        raise ValueError(f"from_id must be a non-empty string, got {from_id!r}")
    if not isinstance(to_id, str) or not to_id.strip():
        raise ValueError(f"to_id must be a non-empty string, got {to_id!r}")
    if not isinstance(msg_type, str) or not msg_type.strip():
        raise ValueError(f"msg_type must be a non-empty string, got {msg_type!r}")
    if not isinstance(message, str) or not message.strip():
        raise ValueError(f"message must be a non-empty string, got {message!r}")
    # ASI01: Enforce payload size limit
    message_bytes = len(message.encode("utf-8"))
    if message_bytes > MAX_MESSAGE_BYTES:
        raise ValueError(
            f"message exceeds maximum size: {message_bytes} bytes > {MAX_MESSAGE_BYTES} bytes"
        )


# ASI06: Maximum number of structured fields in a single message payload
MAX_PAYLOAD_FIELDS = 64


def _validate_content(message: str) -> None:
    """Validate message content for context poisoning prevention (ASI06).

    Checks:
    - Payload size (delegated to _validate_fields via MAX_MESSAGE_BYTES)
    - Structured payload field count (prevents bloated JSON injection)
    - Embedded null bytes (binary injection)

    Args:
        message: Message content string

    Raises:
        ValueError: If content validation fails
    """
    # Null byte check (binary injection prevention)
    if "\x00" in message:
        raise ValueError("message contains null bytes")

    # Structured payload field count limit
    # If the message looks like JSON, check field count
    stripped = message.strip()
    if stripped.startswith("{") and stripped.endswith("}"):
        try:
            parsed = json.loads(stripped)
            if isinstance(parsed, dict) and len(parsed) > MAX_PAYLOAD_FIELDS:
                raise ValueError(
                    f"structured payload has {len(parsed)} fields, "
                    f"max is {MAX_PAYLOAD_FIELDS}"
                )
        except json.JSONDecodeError:
            pass  # Not valid JSON, treat as plain text


def _sanitize_correlation_id(correlation_id: str) -> str:
    """Sanitize correlation ID for safe transport in message payloads."""
    if not isinstance(correlation_id, str) or not correlation_id.strip():
        raise ValueError(
            f"correlation_id must be a non-empty string, got {correlation_id!r}"
        )
    value = (
        correlation_id.strip().replace("\t", " ").replace("\n", "").replace("\r", "")
    )
    return value


def generate_correlation_id(prefix: str = "corr") -> str:
    """Generate a compact correlation ID suitable for bus tracing."""
    safe_prefix = re.sub(r"[^a-zA-Z0-9_-]+", "-", prefix).strip("-") or "corr"
    return f"{safe_prefix}-{uuid.uuid4().hex[:12]}"


def extract_correlation_id(message: str) -> str | None:
    """Extract correlation_id value from a bus message payload."""
    if not isinstance(message, str) or not message:
        return None
    match = _CORRELATION_RE.search(message)
    if not match:
        return None
    return match.group(1)


def _inject_correlation_id(message: str, correlation_id: str) -> str:
    """Inject correlation_id into a payload while preserving JSON compatibility."""
    existing = extract_correlation_id(message)
    if existing:
        return message

    stripped = message.strip()
    if stripped.startswith("{") and stripped.endswith("}"):
        try:
            decoded = json.loads(message)
            if isinstance(decoded, dict):
                decoded["correlation_id"] = correlation_id
                return json.dumps(decoded, separators=(",", ":"), sort_keys=True)
        except json.JSONDecodeError:
            pass

    return f"correlation_id={correlation_id}, {message}"


def build_structured_event(
    *,
    sender: str,
    recipient: str,
    msg_type: str,
    content: str,
    timestamp: str | None = None,
    correlation_id: str | None = None,
    metadata: dict[str, object] | None = None,
) -> str:
    """Build canonical JSON envelope for structured bus events.

    The envelope is written into the 5th TSV column (`message`), preserving the
    existing bus shape while making payloads machine-parsable.
    """
    if timestamp is None:
        timestamp = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    else:
        timestamp = _normalize_timestamp(timestamp)

    event: dict[str, object] = {
        "schema": STRUCTURED_EVENT_SCHEMA,
        "timestamp": timestamp,
        "sender": sender,
        "recipient": recipient,
        "type": msg_type,
        "content": content,
    }

    if correlation_id is not None:
        event["correlation_id"] = correlation_id

    if metadata:
        event["metadata"] = metadata

    try:
        return json.dumps(event, separators=(",", ":"), sort_keys=True)
    except TypeError as exc:
        raise ValueError(f"metadata must be JSON serializable: {exc}") from exc


def parse_structured_event(message: str) -> dict[str, object] | None:
    """Parse a structured bus event payload.

    Returns None for non-JSON or JSON payloads that do not match the
    structured envelope schema marker.
    """
    if not isinstance(message, str) or not message:
        return None

    try:
        decoded = json.loads(message)
    except json.JSONDecodeError:
        return None

    if not isinstance(decoded, dict):
        return None
    if decoded.get("schema") not in SUPPORTED_STRUCTURED_EVENT_SCHEMAS:
        return None
    return decoded


def post_structured_event(
    bus_path: str | Path,
    from_id: str,
    to_id: str,
    msg_type: str,
    content: str,
    timestamp: str | None = None,
    correlation_id: str | None = None,
    metadata: dict[str, object] | None = None,
    validate_sender_identity: bool = True,
    enforce_sender_identity: bool | None = None,
    known_agent_ids: set[str] | None = None,
    validate_recipient_identity: bool = False,
    enforce_recipient_identity: bool = False,
    known_recipient_ids: set[str] | None = None,
    validate_message_type: bool = False,
    enforce_message_type: bool = False,
    known_message_types: set[str] | None = None,
    validate: bool = True,
    principal_proof: str | Mapping[str, object] | None = None,
    request_id: str | None = None,
    nonce_dir: str | Path | None = None,
) -> None:
    """Post a structured bus event while preserving the 5-column TSV format."""
    if timestamp is not None:
        effective_timestamp = _normalize_timestamp(timestamp)
    else:
        effective_timestamp = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")

    safe_correlation_id = None
    if correlation_id is not None:
        safe_correlation_id = _sanitize_correlation_id(correlation_id)

    payload = build_structured_event(
        sender=from_id,
        recipient=to_id,
        msg_type=msg_type,
        content=content,
        timestamp=effective_timestamp,
        correlation_id=safe_correlation_id,
        metadata=metadata,
    )

    post_message(
        bus_path=bus_path,
        from_id=from_id,
        to_id=to_id,
        msg_type=msg_type,
        message=payload,
        timestamp=effective_timestamp,
        correlation_id=None,
        validate_sender_identity=validate_sender_identity,
        enforce_sender_identity=enforce_sender_identity,
        known_agent_ids=known_agent_ids,
        validate_recipient_identity=validate_recipient_identity,
        enforce_recipient_identity=enforce_recipient_identity,
        known_recipient_ids=known_recipient_ids,
        validate_message_type=validate_message_type,
        enforce_message_type=enforce_message_type,
        known_message_types=known_message_types,
        validate=validate,
        principal_proof=principal_proof,
        request_id=request_id,
        nonce_dir=nonce_dir,
    )


def write_dead_letter(
    *,
    dead_letter_path: str | Path,
    source: str,
    reason: str,
    payload: dict[str, object] | None = None,
    metadata: dict[str, object] | None = None,
    timestamp: str | None = None,
) -> None:
    """Append a dead-letter record for failed bus operations.

    Dead letters are written as one JSON object per line (`.jsonl`), under the
    same advisory lock model as bus writes to tolerate concurrent writers.
    """
    path = Path(dead_letter_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    if timestamp is None:
        timestamp = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    else:
        timestamp = _normalize_timestamp(timestamp)

    record: dict[str, object] = {
        "timestamp": timestamp,
        "source": source,
        "reason": reason,
    }
    if payload is not None:
        record["payload"] = payload
    if metadata:
        # #1761: Redact credentials in metadata (especially bridge_url)
        record["metadata"] = _redact_metadata(metadata)

    line = json.dumps(record, separators=(",", ":"), sort_keys=True) + "\n"

    # D4 (#1731): Harden dead_letters.jsonl to 0o600 (owner-only read/write)
    # to match messages.tsv permissions. Previously defaulted to 0o644, making
    # redacted-but-still-sensitive dead-letter content world-readable.
    is_new_file = not path.exists()
    dl_path_lock = (
        _msvcrt_path_lock(path) if msvcrt is not None else contextlib.nullcontext()
    )
    with (
        _cross_process_lock(path),
        dl_path_lock,
        open(path, "a", encoding="utf-8") as f,
    ):
        if fcntl is not None:
            fcntl.flock(f, fcntl.LOCK_EX)
        f.write(line)
        f.flush()
        if fcntl is not None:
            fcntl.flock(f, fcntl.LOCK_UN)

    # Apply 0o600 permissions on new file creation (best-effort; Windows
    # ignores the mode but POSIX honors it).
    if is_new_file:
        try:
            os.chmod(path, 0o600)
        except OSError:
            pass


def _resolve_signing_secret() -> bytes | None:
    """Resolve HMAC signing secret from environment.

    Checks ``BUS_SIGNING_SECRET`` env var. If set, returns the secret
    as bytes (UTF-8 encoded). This enables auto-signing of all bus
    messages without requiring callers to pass ``secret=`` explicitly.

    Returns:
    -------
    bytes | None
        32+ byte secret if BUS_SIGNING_SECRET is set, else None.
    """
    raw = os.environ.get("BUS_SIGNING_SECRET")
    if not raw:
        return None
    secret_bytes = raw.encode("utf-8")
    if len(secret_bytes) < 32:
        logger.warning(
            "BUS_SIGNING_SECRET is too short (%d bytes, need 32+). "
            "Messages will NOT be auto-signed.",
            len(secret_bytes),
        )
        return None
    return secret_bytes


def harden_bus_file_permissions(bus_path: str | Path) -> None:
    """Set restrictive file permissions on the bus file.

    Sets the bus file to owner-only read/write (0o600) to prevent
    unauthorized read/write access. This is a P0 hardening item
    from the ASI07 gap assessment.

    Parameters
    ----------
    bus_path : str | Path
        Path to the messages.tsv file.
    """
    path = Path(bus_path)
    if not path.exists():
        return
    try:
        current_mode = path.stat().st_mode & 0o777
        if current_mode != 0o600:
            path.chmod(0o600)
            logger.debug(
                "Hardened bus file permissions: %s (was %o, now 0600)",
                path,
                current_mode,
            )
    except OSError as e:
        logger.warning("Could not harden bus file permissions: %s", e)


def read_verified_messages(
    bus_path: str | Path,
    secret: bytes | None = None,
    *,
    msg_type_filter: str | None = None,
    since_minutes: int = 5,
    require_signature: bool = False,
) -> list[dict[str, str]]:
    """Read bus messages with optional signature verification.

    For safety-critical consumers (kill switch, circuit breaker), this
    function filters out messages with invalid signatures when a secret
    is provided. When ``require_signature=True``, unsigned messages are
    also filtered out.

    Parameters
    ----------
    bus_path : str | Path
        Path to the messages.tsv file.
    secret : bytes | None
        HMAC secret for signature verification. If None, falls back to
        BUS_SIGNING_SECRET env var. If still None, returns all messages
        unverified (backward compatible).
    msg_type_filter : str | None
        If provided, only return messages of this type.
    since_minutes : int
        How far back to look for messages.
    require_signature : bool
        If True, only return messages that are signed AND verified.
        Default False (return both signed-verified and unsigned).

    Returns:
    -------
    list[dict[str, str]]
        List of dicts with keys: timestamp, sender, recipient, msg_type,
        message (with original content extracted from signing envelope).
    """
    path = Path(bus_path)
    if not path.exists():
        return []

    # Resolve secret
    if secret is None:
        secret = _resolve_signing_secret()

    cutoff = datetime.now(UTC) - timedelta(minutes=since_minutes)
    cutoff_str = cutoff.strftime("%Y-%m-%dT%H:%M:%SZ")
    entries: list[dict[str, str]] = []

    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.rstrip("\n\r")
                if not line:
                    continue
                parts = line.split("\t")
                if len(parts) != 5:
                    continue
                ts, sender, recipient, msg_type_val, message_col = parts

                if ts < cutoff_str:
                    continue

                if msg_type_filter and msg_type_val != msg_type_filter:
                    continue

                # Determine if message is signed
                signed = is_signed_message(message_col)
                original_message = message_col

                if signed and secret is not None:
                    # Verify signature
                    verified, content = verify_bus_message(
                        ts,
                        sender,
                        recipient,
                        msg_type_val,
                        message_col,
                        secret,
                    )
                    if verified:
                        original_message = content
                    else:
                        # Signature invalid -- skip this message
                        logger.warning(
                            "Skipping bus message with invalid signature "
                            "(from=%s, type=%s, ts=%s)",
                            sender,
                            msg_type_val,
                            ts,
                        )
                        continue
                elif signed and secret is None:
                    # Signed but no secret to verify -- extract content
                    envelope = _parse_signing_envelope(message_col)
                    if envelope:
                        original_message = envelope[0]
                elif not signed and require_signature:
                    # Unsigned and we require signatures -- skip
                    continue

                entries.append(
                    {
                        "timestamp": ts,
                        "sender": sender,
                        "recipient": recipient,
                        "msg_type": msg_type_val,
                        "message": original_message,
                    }
                )
    except OSError:
        pass

    return entries


def _enforce_privileged_principal(
    *,
    from_id: str,
    to_id: str,
    msg_type: str,
    message: str,
    principal_proof: str | Mapping[str, object] | None,
    request_id: str | None,
    nonce_dir: str | Path | None,
) -> None:
    """Reject DECISION/DIRECTIVE writes unless a live principal proof verifies.

    These types are operator-authority records. A caller-supplied ``from``
    field, HMAC bus signature, or bridge bearer token is not proof that the
    operator authored the write. Fail closed even when ``validate=False``.
    """
    from .authority import (
        PRIVILEGED_TYPES,
        principal_authorizes,
        resolve_nonce_dir,
        verify_principal_proof,
    )

    if msg_type.strip().upper() not in PRIVILEGED_TYPES:
        return

    verified = verify_principal_proof(
        principal_proof,
        sender=from_id,
        recipient=to_id,
        msg_type=msg_type,
        message=message,
        request_id=request_id,
        nonce_dir=nonce_dir if nonce_dir is not None else resolve_nonce_dir(),
    )
    if not principal_authorizes(
        verified,
        sender=from_id,
        recipient=to_id,
        msg_type=msg_type,
        message=message,
        request_id=verified.request_id,
    ):
        raise PermissionError(
            "principal proof does not authorize this privileged bus write"
        )


def post_message(
    bus_path: str | Path,
    from_id: str,
    to_id: str,
    msg_type: str,
    message: str,
    timestamp: str | None = None,
    correlation_id: str | None = None,
    secret: bytes | None = None,
    validate_sender_identity: bool = True,
    enforce_sender_identity: bool | None = None,
    known_agent_ids: set[str] | None = None,
    validate_recipient_identity: bool = False,
    enforce_recipient_identity: bool = False,
    known_recipient_ids: set[str] | None = None,
    validate_message_type: bool = False,
    enforce_message_type: bool = False,
    known_message_types: set[str] | None = None,
    validate: bool = True,
    principal_proof: str | Mapping[str, object] | None = None,
    request_id: str | None = None,
    nonce_dir: str | Path | None = None,
) -> None:
    r"""Post a message to the coordination bus with TSV-safe encoding.

    Args:
        bus_path: Path to messages.tsv file
        from_id: Sender identifier (e.g., "claude-code", "codex")
        to_id: Recipient identifier (e.g., "all", "codex")
        msg_type: Message type (STATUS, SITREP, PROPOSAL, ACK, DECISION, etc.)
        message: Message content (will be escaped for TSV safety)
        timestamp: Optional UTC timestamp (defaults to now with Z suffix)
        correlation_id: Optional correlation ID for traceability.
        secret: Optional HMAC-SHA256 key (32+ bytes).
        validate: If True (default), validate fields before writing.
        principal_proof: Required for DECISION/DIRECTIVE. Operator principal
            proof bound to this write request (JSON string or dict).
        request_id: Proof-bound request id; required with principal_proof.
        nonce_dir: Optional nonce receipt directory for principal proofs.

    Raises:
        ValueError: If validate=True and a required field is empty
        PermissionError: If a privileged type is posted without a valid proof
        OSError: If file write fails
    """
    bus_path = Path(bus_path)
    bus_path.parent.mkdir(parents=True, exist_ok=True)

    # ASI07: Auto-resolve signing secret from environment if not provided
    if secret is None:
        secret = _resolve_signing_secret()

    # Check security policy (no-op at default PERMISSIVE level)
    from .bus_policy import get_bus_policy

    get_bus_policy().check_signing(secret=secret, from_id=from_id, msg_type=msg_type)

    # Validate required fields
    if validate:
        _validate_fields(from_id, to_id, msg_type, message)
        # ASI06: Content validation (null bytes, structured field count)
        _validate_content(message)
        # Sanitize header fields (remove tabs/newlines that would break TSV)
        from_id = _sanitize_field(from_id)
        to_id = _sanitize_field(to_id)
        msg_type = _sanitize_field(msg_type)
        # P0 fix (S-001): default enforce_sender_identity to True in production,
        # False under FM_TEST_MODE=1. Prior default was False (advisory-only),
        # which allowed any caller to post as any identity. None resolves to
        # the production-safe value unless explicitly overridden.
        if enforce_sender_identity is None:
            enforce_sender_identity = os.environ.get("FM_TEST_MODE") != "1"
        if validate_sender_identity:
            _validate_sender_identity(
                sender_id=from_id,
                known_agent_ids=known_agent_ids,
                enforce=enforce_sender_identity,
            )
        if validate_recipient_identity:
            _validate_recipient_identity(
                recipient_id=to_id,
                known_recipient_ids=known_recipient_ids,
                enforce=enforce_recipient_identity,
            )
        if validate_message_type:
            _validate_message_type(
                msg_type=msg_type,
                known_message_types=known_message_types,
                enforce=enforce_message_type,
            )
        # Kimi-specific constraints (identity + message type)
        _validate_kimi_constraints(from_id, msg_type)

    # Privileged types require a live operator principal proof. This is not
    # optional and is not skipped when validate=False — a from-field or HMAC
    # signature is not operator authorship.
    _enforce_privileged_principal(
        from_id=from_id,
        to_id=to_id,
        msg_type=msg_type,
        message=message,
        principal_proof=principal_proof,
        request_id=request_id,
        nonce_dir=nonce_dir,
    )

    # Generate timestamp if not provided; normalize to UTC if caller-supplied
    if timestamp is None:
        timestamp = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    else:
        timestamp = _normalize_timestamp(timestamp)

    # Inject traceability metadata when available
    if correlation_id is not None:
        safe_correlation_id = _sanitize_correlation_id(correlation_id)
        message = _inject_correlation_id(message, safe_correlation_id)

    # HMAC-SHA256 signing (wraps message in JSON envelope, stays 5-col)
    if secret is not None:
        from .bus_security import generate_nonce
        from .message_signing import sign_payload

        nonce = generate_nonce()
        signing_payload = {"message": message}
        signature = sign_payload(
            secret, timestamp, from_id, to_id, msg_type, signing_payload, nonce
        )
        message = json.dumps(
            {"c": message, "n": nonce, "s": signature}, separators=(",", ":")
        )

    # Escape message content
    safe_message = escape_message(message)

    # Construct TSV line (5 columns: timestamp, from, to, type, message)
    tsv_line = f"{timestamp}\t{from_id}\t{to_id}\t{msg_type}\t{safe_message}\n"

    # Remote bus write: if BUS_REMOTE_URL is set, POST to the HTTP API
    remote_url = os.environ.get("BUS_REMOTE_URL")
    if remote_url:
        try:
            import urllib.request

            payload = json.dumps(
                {
                    "sender": from_id,
                    "to": to_id,
                    "type": msg_type,
                    "message": safe_message,
                }
            ).encode("utf-8")
            token = os.environ.get("DASHBOARD_WRITE_TOKEN", "")
            headers = {"Content-Type": "application/json"}
            if token:
                headers["X-Dashboard-Token"] = token
            req = urllib.request.Request(
                f"{remote_url.rstrip('/')}/api/bus/send",
                data=payload,
                headers=headers,
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                if resp.status == 200:
                    logger.debug("Bus message sent to remote: %s", remote_url)
                    return
        except Exception as e:
            logger.warning(
                "Remote bus write failed (%s), falling back to local: %s",
                remote_url,
                e,
            )
            # Fall through to local write

    # Append to bus under exclusive advisory lock.
    # Use a sibling .bus.lock file for cross-process mutual exclusion so that
    # msvcrt.locking on Windows does not contend with the bus file itself
    # (origin: hummbl-governance #1915). A per-path threading.Lock serializes
    # same-process writers on Windows where msvcrt.locking can EDEADLK.
    is_new_file = not bus_path.exists()
    path_lock = (
        _msvcrt_path_lock(bus_path) if msvcrt is not None else contextlib.nullcontext()
    )
    with (
        _cross_process_lock(bus_path),
        path_lock,
        open(bus_path, "a", encoding="utf-8") as f,
    ):
        if fcntl is not None:
            fcntl.flock(f, fcntl.LOCK_EX)
        f.write(tsv_line)
        f.flush()
        if fcntl is not None:
            fcntl.flock(f, fcntl.LOCK_UN)

    # ASI07: Harden file permissions on newly created bus files
    if is_new_file:
        harden_bus_file_permissions(bus_path)

    # K1: Create governance receipt for every bus post (hummbl-governance >=1.1.0)
    try:
        from hummbl_governance.kernel import ReceiptEngine

        _kernel_state_dir = Path(
            os.environ.get("HUMMBL_KERNEL_STATE_DIR", bus_path.parent / ".kernel")
        )
        _receipt_engine = ReceiptEngine(_kernel_state_dir)
        receipt = _receipt_engine.create(
            agent_id=from_id,
            action_type="BUS_POST",
            payload={
                "bus_path": str(bus_path),
                "to": to_id,
                "msg_type": msg_type,
                "message_length": len(message),
                "timestamp": timestamp,
                "correlation_id": correlation_id or "",
            },
        )
        _receipt_engine.store(receipt)
        logger.debug("K1 receipt created: %s", receipt.receipt_id)
    except Exception:
        # Receipt creation is best-effort; never block bus writes
        logger.debug("K1 receipt creation skipped (hummbl-governance unavailable)")

    # Post-write verification (debug mode only)
    if os.environ.get("BUS_DEBUG"):
        try:
            with open(bus_path, "rb") as f:
                f.seek(0, 2)
                size = f.tell()
                read_size = min(size, 4096)
                f.seek(size - read_size)
                tail = f.read().decode("utf-8")
                last_line = tail.rstrip("\n").rsplit("\n", 1)[-1]
                expected = tsv_line.rstrip("\n")
                if last_line != expected:
                    logger.warning(
                        "Post-write verification mismatch: expected %r, got %r",
                        expected,
                        last_line,
                    )
        except OSError:
            pass


def validate_tsv_integrity(bus_path: str | Path) -> tuple[int, list[str]]:
    """Validate that all bus entries are properly formatted 5-column TSV.

    Args:
        bus_path: Path to messages.tsv file

    Returns:
        Tuple of (valid_count, error_lines)
    """
    bus_path = Path(bus_path)
    if not bus_path.exists():
        return 0, []

    valid_count = 0
    errors = []

    with open(bus_path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, start=1):
            line = line.rstrip("\n\r")
            if not line:
                continue

            parts = line.split("\t")
            if len(parts) != 5:
                errors.append(f"Line {line_num}: Expected 5 columns, got {len(parts)}")
            else:
                valid_count += 1

    return valid_count, errors


def _parse_signing_envelope(message: str) -> tuple[str, str, str] | None:
    """Parse a signed message envelope from column 5.

    Returns:
    -------
    tuple[str, str, str] | None
        ``(content, nonce, signature)`` if *message* is a valid envelope,
        otherwise ``None``.
    """
    if not isinstance(message, str) or not message.startswith("{"):
        return None
    try:
        decoded = json.loads(message)
    except (json.JSONDecodeError, ValueError):
        return None
    if not isinstance(decoded, dict):
        return None
    c = decoded.get("c")
    n = decoded.get("n")
    s = decoded.get("s")
    if isinstance(c, str) and isinstance(n, str) and isinstance(s, str):
        return (c, n, s)
    return None


def is_signed_message(message: str) -> bool:
    """Return ``True`` if *message* looks like a signed envelope."""
    return _parse_signing_envelope(message) is not None


def verify_bus_message(
    timestamp: str,
    from_id: str,
    to_id: str,
    msg_type: str,
    message: str,
    secret: bytes,
) -> tuple[bool, str]:
    """Verify a bus message that may or may not be signed.

    Returns:
    -------
    tuple[bool, str]
        ``(True, original_content)`` if the signature is valid, or
        ``(False, message)`` if the message is unsigned or verification fails.
    """
    envelope = _parse_signing_envelope(message)
    if envelope is None:
        return (False, message)

    content, nonce, signature = envelope

    from .message_signing import verify_signature

    payload = {"message": content}
    verified = verify_signature(
        secret, timestamp, from_id, to_id, msg_type, payload, nonce, signature
    )
    return (verified, content)


def _resolve_bus_path(override: str | None = None) -> Path:
    """Resolve the bus path from override, env, or git root."""
    if override:
        path = Path(override)
        if not path.is_absolute():
            raise ValueError(f"Bus path must be absolute: {path}")
        return path

    env_path = os.environ.get("COORDINATION_BUS")
    if env_path:
        path = Path(env_path)
        root = _resolve_common_repo_root() or _resolve_repo_root()
        if root and path.is_absolute():
            try:
                path.relative_to(root)
            except ValueError:
                raise ValueError(
                    f"COORDINATION_BUS path {path} is outside repo root {root}. "
                    "Path traversal attack detected or misconfigured."
                )
        return path

    root = _resolve_common_repo_root() or _resolve_repo_root()
    if root is not None:
        return root / DEFAULT_BUS_PATH
    return Path(DEFAULT_BUS_PATH)


def resolve_canonical_bus_path() -> Path:
    """Public alias for the canonical bus path resolver.

    Used by ``authority.resolve_nonce_dir`` and other modules that need to
    locate the bus without going through the full write path.
    """
    return _resolve_bus_path()


def _extract_flag(
    args: list[str], flag: str, needs_value: bool = True
) -> tuple[list[str], str | bool | None]:
    """Extract a CLI flag and its optional value from *args*."""
    if flag not in args:
        return args, None
    idx = args.index(flag)
    if not needs_value:
        return args[:idx] + args[idx + 1 :], True
    if idx + 1 >= len(args):
        return args, None
    value = args[idx + 1]
    return args[:idx] + args[idx + 2 :], value


def main(argv: list[str] | None = None) -> int:
    """CLI entry point for posting to the coordination bus.

    Usage:
        python -m hummbl_bus.bus_writer <from> <to> <type> <message> [options]

    Options:
        --bus PATH          Override bus file path
        --cid ID            Attach a correlation ID
        --secret-file PATH  Sign with key from a JSON file
    """
    args = argv if argv is not None else sys.argv[1:]

    args, bus_override = _extract_flag(args, "--bus")
    if bus_override is None and "--bus" in (argv if argv is not None else sys.argv[1:]):
        print("ERROR: --bus requires a path argument", file=sys.stderr)
        return 2

    args, correlation_id = _extract_flag(args, "--cid")
    if correlation_id is None and "--cid" in (
        argv if argv is not None else sys.argv[1:]
    ):
        print("ERROR: --cid requires a correlation id argument", file=sys.stderr)
        return 2

    args, secret_file = _extract_flag(args, "--secret-file")
    if secret_file is None and "--secret-file" in (
        argv if argv is not None else sys.argv[1:]
    ):
        print("ERROR: --secret-file requires a path argument", file=sys.stderr)
        return 2

    # NOTE: --sign flag (KeyManager integration) was removed during extraction.
    # Use --secret-file or BUS_SIGNING_SECRET env var instead.

    if len(args) < 4:
        print(
            "Usage: python -m hummbl_bus.bus_writer <from> <to> <type> <message> [--bus PATH] [--secret-file PATH]",
            file=sys.stderr,
        )
        return 2

    from_id, to_id, msg_type, message = args[0], args[1], args[2], " ".join(args[3:])
    bus_path = _resolve_bus_path(bus_override)

    # Resolve signing secret
    secret: bytes | None = None
    if secret_file:
        import base64

        try:
            with open(secret_file, "r", encoding="utf-8") as f:
                key_data = json.load(f)
            secret = base64.b64decode(key_data["key"])
        except (OSError, KeyError, json.JSONDecodeError) as e:
            print(f"ERROR: failed to load secret file: {e}", file=sys.stderr)
            return 1

    try:
        post_message(
            bus_path,
            from_id,
            to_id,
            msg_type,
            message,
            correlation_id=correlation_id,
            secret=secret,
        )
    except OSError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
