#!/usr/bin/env python3
"""
Bus Bridge Server - HTTP endpoint for cross-machine bus coordination.

Receives bus messages via HTTP POST and appends to local coordination bus.
Secure by default: binds to Tailscale interface only.
"""

from __future__ import annotations

import argparse
import contextlib
import datetime as dt
import hashlib
import hmac
import json
import logging
import os
import re
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import TypedDict

from .bus_writer import (
    BusWriteResult,
    _cross_process_lock,
    _fsync_parent_directory,
    _msvcrt_path_lock,
    _resolve_bus_path,
    _sanitize_correlation_id,
    fcntl,
    msvcrt,
    post_message,
)
from .replay_ledger import (
    REMOTE_WRITE_REQUEST_SCHEMA,
    has_complete_remote_write_receipt,
    lookup_request,
    record_request,
    request_guard,
)

logger = logging.getLogger(__name__)

# Keep the bridge's pre-read request limit aligned with the Open Brain server.
MAX_REQUEST_BODY = 1_048_576

# A client timestamp is optional for compatibility with legacy bridge callers.
# When present, it must be close enough to bridge time to prevent backdated or
# future-dated records from bypassing the signed-message freshness boundary.
MAX_CLIENT_TIMESTAMP_SKEW_SECONDS = 300

class RestrictedSenderPolicy(TypedDict):
    """Static authorization envelope for one protected workload identity."""

    recipients: frozenset[str]
    types: frozenset[str]
    operationally_disabled_types: frozenset[str]
    message_prefix: str
    origin_machine: str
    origin_surface: str


_RESTRICTED_SENDER_POLICIES: dict[str, RestrictedSenderPolicy] = {
    "grok-bot": {
        "recipients": frozenset({"codex", "all"}),
        "types": frozenset(
            {
                "ACK", "BLOCKED", "HANDOFF", "MILESTONE", "PROPOSAL",
                "QUESTION", "SITREP", "SKILL_INVOKE", "STATUS",
                "WIP_END", "WIP_START",
            }
        ),
        "operationally_disabled_types": frozenset(),
        "message_prefix": "host=unknown surface=cursor-grok-bot lane=",
        "origin_machine": "unknown",
        "origin_surface": "cursor-grok-bot",
    },
    "grok-build": {
        "recipients": frozenset({"codex", "all"}),
        "types": frozenset(
            {
                "ACK",
                "BLOCKED",
                "DECISION",
                "DIRECTIVE",
                "PROPOSAL",
                "QUESTION",
                "SITREP",
                "STATUS",
                "WIP_END",
                "WIP_START",
            }
        ),
        "operationally_disabled_types": frozenset({"DECISION", "DIRECTIVE"}),
        "message_prefix": "host=anvil surface=terminal-grok-build lane=",
        "origin_machine": "anvil",
        "origin_surface": "terminal-grok-build",
    },
}
_REQUEST_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{7,127}$")
_LANE_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/-]*$")
_REMOTE_WRITE_FIELDS = frozenset(
    {
        "from",
        "sender",
        "to",
        "type",
        "message",
        "request_id",
        "correlation_id",
        "origin_machine",
        "origin_surface",
        "timestamp",
        "principal_proof",
        "bus_path",
    }
)


class SenderBindingConfigurationError(RuntimeError):
    """The configured sender-binding control is unavailable or ambiguous."""


class SenderAuthorizationError(PermissionError):
    """An authenticated client attempted an unauthorized sender operation."""


class IdempotencyClaimError(RuntimeError):
    """A durable write-ahead request claim could not be persisted."""


def _strict_json_object(raw: str, *, label: str) -> dict[str, object]:
    """Parse a JSON object while rejecting duplicate keys at every level."""

    def reject_duplicate_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
        parsed: dict[str, object] = {}
        for key, value in pairs:
            if key in parsed:
                raise ValueError(f"{label} contains duplicate key {key!r}")
            parsed[key] = value
        return parsed

    parsed = json.loads(raw, object_pairs_hook=reject_duplicate_keys)
    if not isinstance(parsed, dict):
        raise ValueError(f"{label} must contain a JSON object")
    return parsed


def _validate_unique_token_map(
    mapping: dict[str, object],
    *,
    label: str,
) -> dict[str, str]:
    """Validate an exact identity-to-token map with unique token values."""
    validated: dict[str, str] = {}
    token_owners: dict[str, str] = {}
    for identity, token in mapping.items():
        if not isinstance(identity, str) or not identity or identity.strip() != identity:
            raise ValueError(f"{label} contains a non-canonical identity key")
        if not isinstance(token, str) or not token or token.strip() != token:
            raise ValueError(f"{label} contains an invalid token for {identity!r}")
        previous = token_owners.get(token)
        if previous is not None:
            raise ValueError(
                f"{label} maps one token to multiple identities: "
                f"{previous!r}, {identity!r}"
            )
        token_owners[token] = identity
        validated[identity] = token
    if not validated:
        raise ValueError(f"{label} must not be empty")
    return validated


def _restricted_sender_target(value: object) -> str | None:
    """Return the protected canonical targeted by an exact name or variant."""
    if not isinstance(value, str):
        return None
    stripped = value.strip()
    base = stripped.split("(", 1)[0].strip()
    normalized = re.sub(r"[\s_]+", "-", base).casefold()
    return normalized if normalized in _RESTRICTED_SENDER_POLICIES else None


def _resolve_effective_sender(
    *,
    sender_fields: list[tuple[str, object]],
    bound_sender: str | None,
    authenticated_client_id: str | None,
    sender_binding_configured: bool,
) -> tuple[object, bool]:
    """Resolve legacy senders and enforce exact binding for protected senders."""
    declared = next((value for _, value in sender_fields if value), None)
    targets = {
        target
        for target in (
            *(_restricted_sender_target(value) for _, value in sender_fields),
            _restricted_sender_target(bound_sender),
            _restricted_sender_target(authenticated_client_id),
        )
        if target is not None
    }
    if not targets:
        return (bound_sender if bound_sender is not None else declared), False
    if len(targets) != 1:
        raise SenderAuthorizationError("ambiguous restricted sender identity")

    target = next(iter(targets))
    if len(sender_fields) != 1 or sender_fields[0][1] != target:
        raise SenderAuthorizationError(
            f"restricted sender must be declared exactly once as {target!r}"
        )
    if not sender_binding_configured:
        raise SenderBindingConfigurationError(
            "restricted sender binding map is not configured"
        )
    if bound_sender != target:
        raise SenderAuthorizationError(
            f"authenticated credential is not bound to {target!r}"
        )
    if authenticated_client_id != target:
        raise SenderAuthorizationError(
            f"bridge credential client ID is not exactly {target!r}"
        )
    return target, True


def _validate_restricted_request(
    *,
    sender: str,
    recipient: object,
    msg_type: object,
    message: object,
    request_id: object,
    correlation_id: object,
    origin_machine: object,
    origin_surface: object,
) -> None:
    """Apply the exact write envelope for a protected sender."""
    policy = _RESTRICTED_SENDER_POLICIES[sender]
    if msg_type in policy["operationally_disabled_types"]:
        raise SenderAuthorizationError(
            f"{sender} type={msg_type} is operationally disabled"
        )
    if msg_type not in policy["types"]:
        allowed = sorted(policy["types"])
        if len(allowed) == 1:
            raise SenderAuthorizationError(
                f"{sender} may post only type={allowed[0]}"
            )
        raise SenderAuthorizationError(
            f"{sender} may post only types {', '.join(allowed)}"
        )
    if recipient not in policy["recipients"]:
        raise SenderAuthorizationError(
            f"{sender} may post only to codex or all"
        )
    if not isinstance(request_id, str) or not _REQUEST_ID_RE.fullmatch(request_id):
        raise SenderAuthorizationError(
            f"{sender} requires a canonical request_id"
        )
    if correlation_id is not None:
        raise SenderAuthorizationError(
            f"{sender} does not accept correlation_id; include correlation "
            "inside the exact policy-approved message if required"
        )
    if not isinstance(message, str):
        raise SenderAuthorizationError(f"{sender} message must be a string")
    if origin_machine != policy["origin_machine"]:
        raise SenderAuthorizationError(
            f"{sender} requires origin_machine={policy['origin_machine']}"
        )
    if origin_surface != policy["origin_surface"]:
        raise SenderAuthorizationError(
            f"{sender} requires origin_surface={policy['origin_surface']}"
        )
    prefix = str(policy["message_prefix"])
    if not message.startswith(prefix):
        raise SenderAuthorizationError(
            f"{sender} message must begin with {prefix!r}"
        )
    lane_and_rest = message[len(prefix):]
    lane = lane_and_rest.split(maxsplit=1)[0] if lane_and_rest else ""
    if not lane or not _LANE_RE.fullmatch(lane):
        raise SenderAuthorizationError(f"{sender} requires a canonical lane value")
    for field in ("host", "surface", "lane"):
        if len(re.findall(rf"(?<!\S){field}=[^\s]+(?=\s|$)", message)) != 1:
            raise SenderAuthorizationError(
                f"{sender} requires exactly one {field} provenance field"
            )


def _request_fingerprint(
    *,
    request_id: str,
    client_id: str,
    sender: str,
    recipient: str,
    msg_type: str,
    message: str,
    timestamp: str | None,
    correlation_id: str | None,
    origin_machine: str | None,
    origin_surface: str | None = None,
) -> tuple[str, str]:
    """Hash the complete canonical non-secret remote-write request."""
    canonical = {
        "schema": REMOTE_WRITE_REQUEST_SCHEMA,
        "request_id": request_id,
        "operation": "remote_write",
        "client_id": client_id,
        "sender": sender,
        "recipient": recipient,
        "type": msg_type,
        "message": message,
        "timestamp": timestamp,
        "correlation_id": correlation_id,
        "origin_machine": origin_machine,
        "origin_surface": origin_surface,
    }
    encoded = json.dumps(
        canonical,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest(), hashlib.sha256(
        message.encode("utf-8")
    ).hexdigest()


def _legacy_request_fingerprint(
    *,
    request_id: str,
    client_id: str,
    sender: str,
    recipient: str,
    msg_type: str,
    message: str,
    timestamp: str | None,
    correlation_id: str | None,
    origin_machine: str | None,
) -> str:
    """Reproduce v1 fingerprints solely for safe historical retry matching."""
    canonical = {
        "schema": "hummbl_bus.remote_write.v1",
        "request_id": request_id,
        "operation": "remote_write",
        "client_id": client_id,
        "sender": sender,
        "recipient": recipient,
        "type": msg_type,
        "message": message,
        "timestamp": timestamp,
        "correlation_id": correlation_id,
        "origin_machine": origin_machine,
    }
    encoded = json.dumps(
        canonical,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _validate_client_timestamp(
    value: object,
    *,
    enforce_freshness: bool = True,
) -> str | None:
    """Validate an optional canonical UTC timestamp and preserve it exactly."""
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError("timestamp must be a canonical UTC string")

    try:
        parsed = dt.datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(
            tzinfo=dt.timezone.utc
        )
    except ValueError as exc:
        raise ValueError(
            "timestamp must use canonical UTC format YYYY-MM-DDTHH:MM:SSZ"
        ) from exc
    if parsed.strftime("%Y-%m-%dT%H:%M:%SZ") != value:
        raise ValueError(
            "timestamp must use canonical UTC format YYYY-MM-DDTHH:MM:SSZ"
        )

    if enforce_freshness:
        now = dt.datetime.now(dt.timezone.utc)
        skew_seconds = abs((now - parsed).total_seconds())
        if skew_seconds > MAX_CLIENT_TIMESTAMP_SKEW_SECONDS:
            raise ValueError(
                f"timestamp exceeds {MAX_CLIENT_TIMESTAMP_SKEW_SECONDS}s freshness window"
            )
    return value


def _load_bridge_credentials() -> dict[str, str]:
    """Load rotatable client credentials from env or an external file.

    A JSON token file maps client IDs to bearer tokens. A plaintext file or
    BUS_BRIDGE_TOKEN remains supported as the single-client ``default`` form.
    """
    env_token = os.environ.get("BUS_BRIDGE_TOKEN", "").strip()
    if env_token:
        return {"default": env_token}

    token_file = os.environ.get("BUS_BRIDGE_TOKEN_FILE", "").strip()
    if not token_file:
        return {}

    try:
        raw = Path(token_file).read_text(encoding="utf-8").strip()
    except (OSError, UnicodeDecodeError):
        logger.exception("Failed to read BUS_BRIDGE_TOKEN_FILE")
        return {}

    if not raw:
        return {}
    try:
        parsed = _strict_json_object(raw, label="BUS_BRIDGE_TOKEN_FILE")
    except json.JSONDecodeError:
        if raw.lstrip().startswith(("{", "[")):
            logger.error("BUS_BRIDGE_TOKEN_FILE contains malformed JSON")
            return {}
        return {"default": raw}
    except ValueError as exc:
        logger.error("Invalid BUS_BRIDGE_TOKEN_FILE: %s", exc)
        return {}
    try:
        return _validate_unique_token_map(
            parsed,
            label="BUS_BRIDGE_TOKEN_FILE",
        )
    except ValueError as exc:
        logger.error("Invalid BUS_BRIDGE_TOKEN_FILE: %s", exc)
        return {}


def _load_bridge_token() -> str | None:
    """Compatibility helper returning the single configured token, if any."""
    credentials = _load_bridge_credentials()
    return credentials.get("default") if len(credentials) == 1 else None


def _get_package_version() -> str:
    """Return the installed hummbl-bus package version."""
    try:
        from importlib.metadata import version
        return version("hummbl-bus")
    except Exception:
        return "unknown"


def _load_sender_tokens() -> dict[str, str] | None:
    """Load per-agent token mapping for sender binding (AAR 20260818, Rec 1).

    Returns a dict mapping token -> sender_name, or None if not configured.
    A configured-but-invalid map raises ``SenderBindingConfigurationError``;
    it never silently falls back to a caller-selected sender.

    When configured (BUS_SENDER_TOKENS_FILE env var), the server binds the
    authenticated Bearer token to a specific sender identity, overriding the
    client-supplied 'from' field. This prevents sender spoofing: a client with
    agent X's token cannot post as agent Y, even if both know the token format.

    File format (JSON): {"devin": "token-devin-abc123", "codex": "token-codex-xyz", ...}
    The mapping is inverted on load: {token -> sender}.

    When not configured (None), legacy non-restricted senders retain the
    caller-supplied ``from`` behavior. Restricted senders still fail closed.
    """
    tokens_file = os.environ.get("BUS_SENDER_TOKENS_FILE", "").strip()
    if not tokens_file:
        return None
    try:
        raw = Path(tokens_file).read_text(encoding="utf-8").strip()
    except (OSError, UnicodeDecodeError) as exc:
        raise SenderBindingConfigurationError(
            "BUS_SENDER_TOKENS_FILE is unreadable"
        ) from exc
    if not raw:
        raise SenderBindingConfigurationError("BUS_SENDER_TOKENS_FILE is empty")
    try:
        parsed = _strict_json_object(raw, label="BUS_SENDER_TOKENS_FILE")
        mapping = _validate_unique_token_map(
            parsed,
            label="BUS_SENDER_TOKENS_FILE",
        )
    except (json.JSONDecodeError, ValueError) as exc:
        raise SenderBindingConfigurationError(str(exc)) from exc

    for sender in mapping:
        protected_target = _restricted_sender_target(sender)
        if protected_target is not None and sender != protected_target:
            raise SenderBindingConfigurationError(
                f"restricted sender key must be exactly {protected_target!r}"
            )
    return {token: sender for sender, token in mapping.items()}


def _resolve_auth_log_path() -> Path:
    """Resolve the path for the bridge auth event log (append-only JSONL).

    Honors BUS_AUTH_EVENT_LOG env override; otherwise sits next to the bus TSV
    under _state/bus/auth_events.jsonl. The directory is created on demand.
    """
    override = os.environ.get("BUS_AUTH_EVENT_LOG", "").strip()
    if override:
        return Path(override)
    bus_path = _resolve_bus_path(None)
    return bus_path.parent.parent / "bus" / "auth_events.jsonl"


def _record_auth_event(
    *,
    outcome: str,
    client_ip: str,
    sender: str | None = None,
    reason: str | None = None,
    recipient: str | None = None,
    msg_type: str | None = None,
    request_id: str | None = None,
    correlation_id: str | None = None,
    origin_machine: str | None = None,
    origin_surface: str | None = None,
    bus_path: str | None = None,
    operation: str | None = None,
    client_id: str | None = None,
    request_schema: str | None = None,
    request_sha256: str | None = None,
    message_sha256: str | None = None,
    written_timestamp: str | None = None,
    authorized_content_sha256: str | None = None,
    persisted_message_sha256: str | None = None,
    row_sha256: str | None = None,
    authority: dict[str, object] | None = None,
) -> bool:
    """Append-only auth event log. Never writes the token itself.

    outcome: "success" | "failure" | "no_auth" | "accepted" | "duplicate"
        | "rejected"
    """
    try:
        log_path = _resolve_auth_log_path()
        log_path.parent.mkdir(parents=True, exist_ok=True)
        event = {
            "ts": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "outcome": outcome,
            "client_ip": client_ip,
        }
        if sender:
            event["sender"] = sender
        if recipient:
            event["recipient"] = recipient
        if msg_type:
            event["msg_type"] = msg_type
        if request_id:
            event["request_id"] = request_id
        if correlation_id:
            event["correlation_id"] = correlation_id
        if origin_machine:
            event["origin_machine"] = origin_machine
        if origin_surface:
            event["origin_surface"] = origin_surface
        if bus_path:
            event["bus_path"] = bus_path
        if operation:
            event["operation"] = operation
        if client_id:
            event["client_id"] = client_id
        if request_schema:
            event["request_schema"] = request_schema
        if request_sha256:
            event["request_sha256"] = request_sha256
        if message_sha256:
            event["message_sha256"] = message_sha256
        if written_timestamp:
            event["written_timestamp"] = written_timestamp
        if authorized_content_sha256:
            event["authorized_content_sha256"] = authorized_content_sha256
        if persisted_message_sha256:
            event["persisted_message_sha256"] = persisted_message_sha256
        if row_sha256:
            event["row_sha256"] = row_sha256
        if authority is not None:
            event["authority"] = authority
        if reason:
            event["reason"] = reason
        is_new_file = not log_path.exists()
        path_lock = (
            _msvcrt_path_lock(log_path)
            if msvcrt is not None
            else contextlib.nullcontext()
        )
        with path_lock, _cross_process_lock(log_path), open(
            log_path, "a", encoding="utf-8"
        ) as f:
            if fcntl is not None:
                fcntl.flock(f, fcntl.LOCK_EX)
            f.write(json.dumps(event) + "\n")
            f.flush()
            os.fsync(f.fileno())
            if fcntl is not None:
                fcntl.flock(f, fcntl.LOCK_UN)
        if is_new_file:
            _fsync_parent_directory(log_path)
        return True
    except Exception:
        # Auth-log failure must never break the auth path itself.
        logger.exception("Failed to write bridge auth event")
        return False


def _lookup_auth_event_request(request_id: str) -> dict[str, object] | None:
    """Return an accepted request receipt from auth_events.jsonl, if present.

    The auth log is a secondary receipt for the narrow case where the bus row
    has landed but replay_ledger.jsonl is unavailable before record_request()
    can persist the primary idempotence record.
    """
    try:
        log_path = _resolve_auth_log_path()
        if not log_path.exists():
            return None

        found: dict[str, object] | None = None
        with open(log_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if event.get("request_id") != request_id:
                    continue
                if event.get("outcome") != "accepted":
                    continue

                record: dict[str, object] = {
                    "request_id": request_id,
                    "operation": "remote_write",
                    "accepted_at": event.get("ts"),
                    "receipt_source": "auth_events",
                    "auth_outcome": event.get("outcome"),
                }
                if event.get("sender"):
                    record["sender"] = event["sender"]
                if event.get("client_id"):
                    record["client_id"] = event["client_id"]
                if event.get("recipient"):
                    record["recipient"] = event["recipient"]
                if event.get("msg_type"):
                    record["type"] = event["msg_type"]
                if event.get("origin_machine"):
                    record["origin_machine"] = event["origin_machine"]
                if event.get("origin_surface"):
                    record["origin_surface"] = event["origin_surface"]
                if event.get("correlation_id"):
                    record["correlation_id"] = event["correlation_id"]
                if event.get("bus_path"):
                    record["bus_path"] = event["bus_path"]
                if event.get("reason"):
                    record["reason"] = event["reason"]
                if event.get("request_schema"):
                    record["request_schema"] = event["request_schema"]
                if event.get("request_sha256"):
                    record["request_sha256"] = event["request_sha256"]
                if event.get("message_sha256"):
                    record["message_sha256"] = event["message_sha256"]
                if event.get("written_timestamp"):
                    record["written_timestamp"] = event["written_timestamp"]
                if event.get("authorized_content_sha256"):
                    record["authorized_content_sha256"] = event[
                        "authorized_content_sha256"
                    ]
                if event.get("persisted_message_sha256"):
                    record["persisted_message_sha256"] = event[
                        "persisted_message_sha256"
                    ]
                if event.get("row_sha256"):
                    record["row_sha256"] = event["row_sha256"]
                if event.get("authority"):
                    record["authority"] = event["authority"]
                found = record
        return found
    except Exception:
        logger.exception("Failed to read bridge auth receipt")
        return None


MAX_TAIL_LINES = 10000  # DoS protection: cap on /bus/tail?n= and /bus/search?n=

# Module-level cache for /bus/status line counts, keyed by bus file path.
# Stores (mtime_ns, line_count) tuples. Invalidated when the file's mtime
# changes. This avoids O(n) full-file scans on every status poll when the
# bus is idle (the common case — agents poll status every few minutes).
_SERVE_BUS_STATUS_CACHE: dict[str, tuple[int, int]] = {}

# Maximum number of messages accepted in a single /bus/batch request.
MAX_BATCH_MESSAGES = 50


class BusBridgeHandler(BaseHTTPRequestHandler):
    """HTTP handler for receiving remote bus messages."""

    def log_message(self, format: str, *args: object) -> None:
        """Suppress default logging - be quiet."""
        pass

    def _client_ip(self) -> str:
        try:
            return self.client_address[0]
        except Exception:
            return "?"

    def _check_post_auth(self, operation: str = "protected") -> tuple[bool, str | None]:
        """Default-deny protected operations; only /health is unauthenticated.

        Uses hmac.compare_digest for constant-time comparison to prevent
        timing-attack token recovery from co-tenant tailnet observers.

        Returns (authenticated, bound_sender). When per-agent sender tokens
        are configured (BUS_SENDER_TOKENS_FILE), bound_sender is the agent
        identity mapped from the presented token. The caller MUST use
        bound_sender instead of the client-supplied 'from' field ΓÇö this
        prevents sender spoofing (AAR 20260818, Rec 1).

        When sender tokens are not configured, bound_sender is None for legacy
        senders. Restricted senders are rejected later by their write policy.
        A configured-but-invalid sender map rejects the protected operation
        with HTTP 503 instead of falling back to caller-selected identity.
        """
        credentials = _load_bridge_credentials()
        client_id = self.headers.get("X-Bridge-Client-ID", "").strip() or None
        auth_header = self.headers.get("Authorization", "")
        supplied = auth_header.removeprefix("Bearer ").strip()
        matched_id = None
        for candidate_id, token in credentials.items():
            if hmac.compare_digest(supplied, token):
                if client_id is None or client_id == candidate_id:
                    matched_id = candidate_id
                    break
        if matched_id is None:
            status = 503 if not credentials else 401
            _record_auth_event(outcome="failure", client_ip=self._client_ip(),
                               reason=("auth_not_configured" if not credentials else "401_invalid_token"),
                               operation=operation, client_id=client_id)
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Bridge authentication required"}).encode())
            return False, None

        # Sender binding (AAR 20260818, Rec 1): when per-agent sender tokens
        # are configured, map the presented token to a bound sender identity.
        bound_sender = None
        try:
            sender_tokens = _load_sender_tokens()
        except SenderBindingConfigurationError as exc:
            _record_auth_event(
                outcome="failure",
                client_ip=self._client_ip(),
                reason="sender_binding_configuration_error",
                operation=operation,
                client_id=matched_id,
            )
            self._json_response(
                {
                    "error": "Sender binding configuration unavailable",
                    "code": "sender_binding_configuration_error",
                },
                status=503,
            )
            logger.error("Sender binding configuration unavailable: %s", exc)
            return False, None
        if sender_tokens is not None:
            for token, sender in sender_tokens.items():
                if hmac.compare_digest(supplied, token):
                    bound_sender = sender
                    break

        self._authenticated_client_id = matched_id
        self._sender_binding_configured = sender_tokens is not None
        self._authenticated_with_bearer = auth_header.startswith("Bearer ")
        _record_auth_event(
            outcome="success",
            client_ip=self._client_ip(),
            operation=operation,
            client_id=matched_id,
        )

        return True, bound_sender

    def do_POST(self) -> None:
        """Handle incoming bus message."""
        if self.path not in ('/bus', '/api/bus/send', '/bus/post', '/bus/batch'):
            self.send_error(404, "Not found")
            return

        authenticated, bound_sender = self._check_post_auth("write")
        if not authenticated:
            return

        # Batch endpoint: accept an array of messages in one request,
        # applying a single auth check per batch. This eliminates the
        # 5-second-per-post rate-limit wait when an orchestrator needs
        # to post multiple receipts/status messages at once.
        if self.path == '/bus/batch':
            self._handle_batch_post(bound_sender)
            return

        try:
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length < 0:
                raise ValueError("Content-Length must not be negative")
            if content_length > MAX_REQUEST_BODY:
                self.send_error(413, "Payload too large")
                return
            body = self.rfile.read(content_length).decode('utf-8')
            data = _strict_json_object(body, label="request body")
            unexpected_fields = set(data).difference(_REMOTE_WRITE_FIELDS)
            if unexpected_fields:
                names = ", ".join(sorted(unexpected_fields))
                raise ValueError(f"request body contains unknown fields: {names}")

            # Accept both legacy naming conventions, but retain which fields
            # were present. Protected identities must be declared exactly once
            # so ``from``/``sender`` ambiguity cannot weaken token binding.
            sender_fields = [
                (field, data[field])
                for field in ("from", "sender")
                if field in data
            ]
            to_agent = data.get('to', 'all')
            msg_type = data.get('type', 'STATUS')
            message = data.get('message')
            request_id = data.get('request_id')
            correlation_id = data.get('correlation_id')
            origin_machine = data.get('origin_machine')
            origin_surface = data.get('origin_surface')
            principal_proof = data.get('principal_proof')
            # proposal_id: optional threading field for PROPOSAL/ACK/DECISION
            # correlation. Added 2026-09-02 per bus corpus analysis finding
            # (85% orphan proposals). See PROPOSAL on bus 2026-09-02.
            proposal_id = data.get('proposal_id')

            try:
                from_agent, restricted_sender = _resolve_effective_sender(
                    sender_fields=sender_fields,
                    bound_sender=bound_sender,
                    authenticated_client_id=getattr(
                        self, "_authenticated_client_id", None
                    ),
                    sender_binding_configured=bool(
                        getattr(self, "_sender_binding_configured", False)
                    ),
                )
            except SenderBindingConfigurationError as exc:
                _record_auth_event(
                    outcome="rejected",
                    client_ip=self._client_ip(),
                    reason="restricted_sender_binding_unavailable",
                    request_id=str(request_id) if request_id else None,
                    client_id=getattr(self, "_authenticated_client_id", None),
                )
                self._json_response(
                    {
                        "error": str(exc),
                        "code": "restricted_sender_binding_unavailable",
                    },
                    status=503,
                )
                return
            except SenderAuthorizationError as exc:
                _record_auth_event(
                    outcome="rejected",
                    client_ip=self._client_ip(),
                    reason="restricted_sender_binding_denied",
                    request_id=str(request_id) if request_id else None,
                    client_id=getattr(self, "_authenticated_client_id", None),
                )
                self._json_response(
                    {
                        "error": str(exc),
                        "code": "restricted_sender_binding_denied",
                    },
                    status=403,
                )
                return

            if restricted_sender and not bool(
                getattr(self, "_authenticated_with_bearer", False)
            ):
                _record_auth_event(
                    outcome="rejected",
                    client_ip=self._client_ip(),
                    sender=str(from_agent),
                    request_id=str(request_id) if request_id else None,
                    reason="restricted_sender_bearer_required",
                    client_id=getattr(self, "_authenticated_client_id", None),
                )
                self._json_response(
                    {
                        "error": "restricted sender requires Bearer authentication",
                        "code": "restricted_sender_binding_denied",
                    },
                    status=403,
                )
                return

            if not isinstance(from_agent, str) or not from_agent.strip():
                raise ValueError("Missing required field: 'from' or 'sender'")
            if not isinstance(to_agent, str) or not to_agent.strip():
                raise ValueError("'to' must be a non-empty string")
            if not isinstance(msg_type, str) or not msg_type.strip():
                raise ValueError("'type' must be a non-empty string")
            if not isinstance(message, str) or not message:
                raise ValueError("Missing required field: 'message'")
            if correlation_id is not None and not isinstance(correlation_id, str):
                raise ValueError("'correlation_id' must be a string")
            if origin_machine is not None and not isinstance(origin_machine, str):
                raise ValueError("'origin_machine' must be a string")
            if origin_surface is not None and not isinstance(origin_surface, str):
                raise ValueError("'origin_surface' must be a string")

            from .authority import PRIVILEGED_TYPES

            is_privileged = msg_type.strip().upper() in PRIVILEGED_TYPES
            if restricted_sender and correlation_id is not None:
                _record_auth_event(
                    outcome="rejected",
                    client_ip=self._client_ip(),
                    sender=from_agent,
                    recipient=to_agent,
                    msg_type=msg_type,
                    request_id=str(request_id) if request_id else None,
                    origin_machine=origin_machine,
                    origin_surface=origin_surface,
                    reason="restricted_sender_correlation_metadata_denied",
                    client_id=getattr(self, "_authenticated_client_id", None),
                )
                self._json_response(
                    {
                        "error": (
                            f"{from_agent} does not accept correlation_id; "
                            "include correlation inside the exact "
                            "policy-approved message if required"
                        ),
                        "code": "restricted_sender_acl_denied",
                    },
                    status=403,
                )
                return
            if is_privileged and correlation_id is not None:
                _record_auth_event(
                    outcome="rejected",
                    client_ip=self._client_ip(),
                    sender=from_agent,
                    recipient=to_agent,
                    msg_type=msg_type,
                    request_id=str(request_id) if request_id else None,
                    origin_machine=origin_machine,
                    origin_surface=origin_surface,
                    reason="privileged_correlation_metadata_denied",
                    client_id=getattr(self, "_authenticated_client_id", None),
                )
                self._json_response(
                    {
                        "error": (
                            "privileged correlation_id must be inside the "
                            "signed message content"
                        ),
                        "code": "privileged_correlation_metadata_denied",
                    },
                    status=403,
                )
                return
            correlation_text = (
                None
                if correlation_id is None
                else _sanitize_correlation_id(correlation_id)
            )

            try:
                timestamp = _validate_client_timestamp(
                    data.get('timestamp'),
                    enforce_freshness=False,
                )
            except ValueError:
                _record_auth_event(
                    outcome="rejected",
                    client_ip=self._client_ip(),
                    sender=str(from_agent) if from_agent else None,
                    recipient=str(to_agent),
                    msg_type=str(msg_type),
                    request_id=str(request_id) if request_id else None,
                    correlation_id=correlation_text,
                    origin_machine=str(origin_machine) if origin_machine else None,
                    reason="invalid_or_stale_client_timestamp",
                )
                raise

            if data.get("bus_path"):
                _record_auth_event(
                    outcome="rejected",
                    client_ip=self._client_ip(),
                    sender=str(from_agent),
                    recipient=str(to_agent),
                    msg_type=str(msg_type),
                    request_id=str(request_id) if request_id else None,
                    correlation_id=correlation_text,
                    origin_machine=str(origin_machine) if origin_machine else None,
                    reason="client-supplied bus_path is not accepted",
                )
                self.send_error(400, "Client-supplied bus_path is not accepted")
                return

            explicit_request_id = bool(request_id)
            if restricted_sender and (
                not isinstance(request_id, str)
                or not _REQUEST_ID_RE.fullmatch(request_id)
            ):
                _record_auth_event(
                    outcome="rejected",
                    client_ip=self._client_ip(),
                    sender=from_agent,
                    recipient=to_agent,
                    msg_type=msg_type,
                    request_id=str(request_id) if request_id else None,
                    reason="restricted_sender_request_id_required",
                    client_id=getattr(self, "_authenticated_client_id", None),
                )
                self._json_response(
                    {
                        "error": f"{from_agent} requires a canonical request_id",
                        "code": "restricted_sender_acl_denied",
                    },
                    status=403,
                )
                return

            payload_dedup = False
            request_id_text = str(request_id) if explicit_request_id else None
            if request_id_text is None and not is_privileged:
                payload_hash = hashlib.sha256(
                    f"{from_agent}|{to_agent}|{msg_type}|{message}".encode("utf-8")
                ).hexdigest()[:16]
                request_id_text = f"payload:{payload_hash}"
                payload_dedup = True

            origin_text = str(origin_machine) if origin_machine else None
            surface_text = str(origin_surface) if origin_surface else None
            request_sha256 = None
            legacy_request_sha256 = None
            message_sha256 = None
            if request_id_text is not None:
                request_sha256, message_sha256 = _request_fingerprint(
                    request_id=request_id_text,
                    client_id=str(
                        getattr(self, "_authenticated_client_id", "unknown")
                    ),
                    sender=from_agent,
                    recipient=to_agent,
                    msg_type=msg_type,
                    message=message,
                    timestamp=timestamp,
                    correlation_id=correlation_text,
                    origin_machine=origin_text,
                    origin_surface=surface_text,
                )
                legacy_request_sha256 = _legacy_request_fingerprint(
                    request_id=request_id_text,
                    client_id=str(
                        getattr(self, "_authenticated_client_id", "unknown")
                    ),
                    sender=from_agent,
                    recipient=to_agent,
                    msg_type=msg_type,
                    message=message,
                    timestamp=timestamp,
                    correlation_id=correlation_text,
                    origin_machine=origin_text,
                )

            guard = (
                request_guard(request_id_text)
                if request_id_text is not None
                else contextlib.nullcontext()
            )
            with guard:
                existing = None
                if request_id_text is not None:
                    try:
                        existing = lookup_request(request_id_text)
                    except Exception:
                        logger.exception(
                            "Failed to read bridge replay receipt for request_id=%s",
                            request_id_text,
                        )
                    if explicit_request_id and (
                        existing is None
                        or (
                            isinstance(existing, dict)
                            and existing.get("state") == "pending"
                        )
                    ):
                        auth_existing = _lookup_auth_event_request(request_id_text)
                        if auth_existing is not None:
                            existing = auth_existing

                duplicate = False
                conflict_code = None
                if isinstance(existing, dict):
                    prior_state = existing.get("state", "accepted")
                    prior_schema = existing.get("request_schema")
                    prior_sha256 = existing.get("request_sha256")
                    request_matches = bool(
                        (
                            prior_schema == REMOTE_WRITE_REQUEST_SCHEMA
                            and prior_sha256 == request_sha256
                        )
                        or (
                            prior_schema == "hummbl_bus.remote_write.v1"
                            and prior_sha256 == legacy_request_sha256
                        )
                    )
                    receipt_durable = has_complete_remote_write_receipt(
                        existing,
                        expected_request_sha256=request_sha256,
                        expected_message_sha256=message_sha256,
                        require_authority=is_privileged,
                    )
                    if prior_state == "pending":
                        if request_matches:
                            conflict_code = "idempotency_reconciliation_required"
                        else:
                            conflict_code = "idempotency_key_conflict"
                    elif payload_dedup:
                        accepted_str = existing.get("accepted_at", "")
                        if accepted_str:
                            try:
                                accepted_dt = dt.datetime.fromisoformat(
                                    str(accepted_str).replace("Z", "+00:00")
                                )
                                dedup_window = int(
                                    os.environ.get(
                                        "BUS_DEDUP_WINDOW_SECONDS", "60"
                                    )
                                )
                                within_window = (
                                    time.time() - accepted_dt.timestamp()
                                    < dedup_window
                                )
                                if within_window:
                                    if receipt_durable:
                                        duplicate = True
                                    else:
                                        conflict_code = (
                                            "idempotency_reconciliation_required"
                                        )
                            except (ValueError, TypeError):
                                pass
                    else:
                        if prior_schema or prior_sha256:
                            if request_matches:
                                if receipt_durable:
                                    duplicate = True
                                else:
                                    conflict_code = (
                                        "idempotency_reconciliation_required"
                                    )
                            else:
                                conflict_code = "idempotency_key_conflict"
                        else:
                            conflict_code = "idempotency_record_unverifiable"

                if conflict_code is not None:
                    _record_auth_event(
                        outcome="rejected",
                        client_ip=self._client_ip(),
                        sender=from_agent,
                        recipient=to_agent,
                        msg_type=msg_type,
                        request_id=request_id_text,
                        correlation_id=correlation_text,
                        origin_machine=origin_text,
                        origin_surface=surface_text,
                        reason=conflict_code,
                        client_id=getattr(self, "_authenticated_client_id", None),
                        request_schema=REMOTE_WRITE_REQUEST_SCHEMA,
                        request_sha256=request_sha256,
                        message_sha256=message_sha256,
                    )
                    self._json_response(
                        {
                            "error": (
                                "request acceptance requires reconciliation"
                                if conflict_code
                                == "idempotency_reconciliation_required"
                                else "request_id is already bound to another request"
                            ),
                            "code": conflict_code,
                            "duplicate": False,
                            "request_id": request_id_text,
                            "receipt_durable": False,
                        },
                        status=409,
                    )
                    return

                if duplicate:
                    _record_auth_event(
                        outcome="duplicate",
                        client_ip=self._client_ip(),
                        sender=from_agent,
                        recipient=to_agent,
                        msg_type=msg_type,
                        request_id=request_id_text,
                        correlation_id=correlation_text,
                        origin_machine=origin_text,
                        origin_surface=surface_text,
                        client_id=getattr(self, "_authenticated_client_id", None),
                        request_schema=REMOTE_WRITE_REQUEST_SCHEMA,
                        request_sha256=request_sha256,
                        message_sha256=message_sha256,
                    )
                    self._json_response(
                        {
                            "status": "ok",
                            "duplicate": True,
                            "request_id": request_id_text,
                            "record": existing,
                            "receipt_durable": True,
                        }
                    )
                    return

                # BLOCKED-specific dedup: longer window (6h) for chronic blockers.
                # Added 2026-09-02 per bus corpus analysis: 1,662 BLOCKED messages,
                # 60.6% never resolve; top chronic blockers reposted dozens of times
                # (GiteaActRunner 140, GPG signing 82, push-pull-loop 52).
                # The existing payload dedup (60s) is too short for BLOCKED — the
                # same failure recurs hours later. This check is separate from the
                # payload dedup above and only applies to BLOCKED type.
                # Configurable via BUS_BLOCKED_DEDUP_WINDOW_SECONDS (default 21600=6h).
                if str(msg_type).upper() == "BLOCKED" and not duplicate:
                    blocked_dedup_window = int(
                        os.environ.get("BUS_BLOCKED_DEDUP_WINDOW_SECONDS", "21600")
                    )
                    blocked_hash = hashlib.sha256(
                        f"{from_agent}|{to_agent}|{msg_type}|{message}".encode("utf-8")
                    ).hexdigest()[:16]
                    blocked_dedup_key = f"blocked_dedup:{blocked_hash}"
                    try:
                        blocked_existing = lookup_request(blocked_dedup_key)
                        if isinstance(blocked_existing, dict):
                            blocked_accepted = blocked_existing.get("accepted_at", "")
                            if blocked_accepted:
                                blocked_dt = dt.datetime.fromisoformat(
                                    str(blocked_accepted).replace("Z", "+00:00")
                                )
                                if time.time() - blocked_dt.timestamp() < blocked_dedup_window:
                                    _record_auth_event(
                                        outcome="duplicate",
                                        client_ip=self._client_ip(),
                                        sender=from_agent,
                                        recipient=to_agent,
                                        msg_type=msg_type,
                                        request_id=request_id_text,
                                        correlation_id=correlation_text,
                                        origin_machine=origin_text,
                                        client_id=getattr(self, "_authenticated_client_id", None),
                                        request_schema=REMOTE_WRITE_REQUEST_SCHEMA,
                                        request_sha256=request_sha256,
                                        message_sha256=message_sha256,
                                        reason="blocked_dedup",
                                    )
                                    self._json_response(
                                        {
                                            "status": "ok",
                                            "duplicate": True,
                                            "dedup_reason": "blocked_dedup",
                                            "dedup_window_seconds": blocked_dedup_window,
                                            "request_id": request_id_text,
                                        },
                                        status=409,
                                    )
                                    return
                    except Exception:
                        logger.exception(
                            "Failed to check BLOCKED dedup for hash=%s",
                            blocked_hash,
                        )

                try:
                    _validate_client_timestamp(timestamp)
                except ValueError:
                    _record_auth_event(
                        outcome="rejected",
                        client_ip=self._client_ip(),
                        sender=from_agent,
                        recipient=to_agent,
                        msg_type=msg_type,
                        request_id=request_id_text,
                        correlation_id=correlation_text,
                        origin_machine=origin_text,
                        origin_surface=surface_text,
                        reason="invalid_or_stale_client_timestamp",
                        client_id=getattr(self, "_authenticated_client_id", None),
                        request_schema=REMOTE_WRITE_REQUEST_SCHEMA,
                        request_sha256=request_sha256,
                        message_sha256=message_sha256,
                    )
                    raise

                if restricted_sender:
                    try:
                        _validate_restricted_request(
                            sender=from_agent,
                            recipient=to_agent,
                            msg_type=msg_type,
                            message=message,
                            request_id=request_id_text,
                            correlation_id=correlation_id,
                            origin_machine=origin_text,
                            origin_surface=surface_text,
                        )
                    except SenderAuthorizationError as exc:
                        _record_auth_event(
                            outcome="rejected",
                            client_ip=self._client_ip(),
                            sender=from_agent,
                            recipient=to_agent,
                            msg_type=msg_type,
                            request_id=request_id_text,
                            correlation_id=correlation_text,
                            origin_machine=origin_text,
                            origin_surface=surface_text,
                            reason="restricted_sender_acl_denied",
                            client_id=getattr(
                                self, "_authenticated_client_id", None
                            ),
                            request_schema=REMOTE_WRITE_REQUEST_SCHEMA,
                            request_sha256=request_sha256,
                            message_sha256=message_sha256,
                        )
                        self._json_response(
                            {
                                "error": str(exc),
                                "code": "restricted_sender_acl_denied",
                            },
                            status=403,
                        )
                        return

                # Append to the bridge's configured canonical bus while the
                # request guard is held, then durably bind the receipt.
                bus_path = _resolve_bus_path(None)
                recipient_policy = (
                    set(_RESTRICTED_SENDER_POLICIES[from_agent]["recipients"])
                    if restricted_sender
                    else None
                )
                sender_policy = {from_agent} if restricted_sender else None
                claimed_at = dt.datetime.now(dt.timezone.utc).strftime(
                    "%Y-%m-%dT%H:%M:%SZ"
                )

                def persist_pending_claim(
                    verified_principal: object | None = None,
                ) -> None:
                    authority = None
                    if verified_principal is not None:
                        from .authority import (
                            VerifiedPrincipal,
                            verified_principal_receipt,
                        )

                        if not isinstance(verified_principal, VerifiedPrincipal):
                            raise TypeError(
                                "privileged claim requires a verified principal"
                            )
                        authority = verified_principal_receipt(verified_principal)
                    try:
                        record_request(
                            request_id=request_id_text,
                            operation="remote_write",
                            state="pending",
                            client_id=str(
                                getattr(
                                    self,
                                    "_authenticated_client_id",
                                    "unknown",
                                )
                            ),
                            sender=from_agent,
                            recipient=to_agent,
                            msg_type=msg_type,
                            origin_machine=origin_text,
                            origin_surface=surface_text,
                            correlation_id=correlation_text,
                            accepted_at=claimed_at,
                            bus_path=str(bus_path),
                            request_schema=REMOTE_WRITE_REQUEST_SCHEMA,
                            request_sha256=request_sha256,
                            message_sha256=message_sha256,
                            client_timestamp=timestamp,
                            authority=authority,
                        )
                    except Exception as exc:
                        raise IdempotencyClaimError(
                            "idempotency claim unavailable"
                        ) from exc

                if request_id_text is not None and not is_privileged:
                    try:
                        persist_pending_claim()
                    except IdempotencyClaimError:
                        _record_auth_event(
                            outcome="rejected",
                            client_ip=self._client_ip(),
                            sender=from_agent,
                            recipient=to_agent,
                            msg_type=msg_type,
                            request_id=request_id_text,
                            correlation_id=correlation_text,
                            origin_machine=origin_text,
                            origin_surface=surface_text,
                            reason="idempotency_claim_unavailable",
                            client_id=getattr(
                                self, "_authenticated_client_id", None
                            ),
                            request_schema=REMOTE_WRITE_REQUEST_SCHEMA,
                            request_sha256=request_sha256,
                            message_sha256=message_sha256,
                        )
                        logger.exception(
                            "Failed to persist request claim for request_id=%s",
                            request_id_text,
                        )
                        self._json_response(
                            {
                                "error": "idempotency claim unavailable",
                                "code": "idempotency_claim_unavailable",
                            },
                            status=503,
                        )
                        return
                try:
                    write_result = post_message(
                        bus_path=bus_path,
                        from_id=from_agent,
                        to_id=to_agent,
                        msg_type=msg_type,
                        message=message,
                        timestamp=timestamp,
                        # Correlation is bound into the request fingerprint and
                        # durable receipts below. The bridge must not mutate the
                        # authorized content after hashing the submitted body.
                        correlation_id=None,
                        validate_sender_identity=True,
                        enforce_sender_identity=True,
                        known_agent_ids=sender_policy,
                        validate_recipient_identity=restricted_sender,
                        enforce_recipient_identity=restricted_sender,
                        known_recipient_ids=recipient_policy,
                        validate_message_type=True,
                        enforce_message_type=True,
                        validate_host_presence=True,
                        enforce_host_presence=True,
                        request_id=request_id_text,
                        principal_proof=principal_proof,
                        before_privileged_append=(
                            persist_pending_claim
                            if request_id_text is not None and is_privileged
                            else None
                        ),
                    )
                    if not isinstance(write_result, BusWriteResult):
                        raise RuntimeError(
                            "canonical writer did not return row linkage"
                        )
                    authority_receipt = None
                    if is_privileged:
                        from .authority import (
                            VerifiedPrincipal,
                            verified_principal_receipt,
                        )

                        if not isinstance(
                            write_result.verified_principal,
                            VerifiedPrincipal,
                        ):
                            raise RuntimeError(
                                "privileged writer omitted verified principal linkage"
                            )
                        authority_receipt = verified_principal_receipt(
                            write_result.verified_principal
                        )
                except IdempotencyClaimError:
                    _record_auth_event(
                        outcome="rejected",
                        client_ip=self._client_ip(),
                        sender=from_agent,
                        recipient=to_agent,
                        msg_type=msg_type,
                        request_id=request_id_text,
                        correlation_id=correlation_text,
                        origin_machine=origin_text,
                        origin_surface=surface_text,
                        reason="idempotency_claim_unavailable",
                        client_id=getattr(self, "_authenticated_client_id", None),
                        request_schema=REMOTE_WRITE_REQUEST_SCHEMA,
                        request_sha256=request_sha256,
                        message_sha256=message_sha256,
                    )
                    logger.exception(
                        "Failed to persist privileged request claim for "
                        "request_id=%s",
                        request_id_text,
                    )
                    self._json_response(
                        {
                            "error": "idempotency claim unavailable",
                            "code": "idempotency_claim_unavailable",
                        },
                        status=503,
                    )
                    return
                except (PermissionError, ValueError):
                    _record_auth_event(
                        outcome="rejected",
                        client_ip=self._client_ip(),
                        sender=from_agent,
                        recipient=to_agent,
                        msg_type=msg_type,
                        request_id=request_id_text,
                        correlation_id=correlation_text,
                        origin_machine=origin_text,
                        origin_surface=surface_text,
                        reason="final_writer_rejected",
                        client_id=getattr(self, "_authenticated_client_id", None),
                        request_schema=REMOTE_WRITE_REQUEST_SCHEMA,
                        request_sha256=request_sha256,
                        message_sha256=message_sha256,
                    )
                    raise
                except Exception:
                    _record_auth_event(
                        outcome="failure",
                        client_ip=self._client_ip(),
                        sender=from_agent,
                        recipient=to_agent,
                        msg_type=msg_type,
                        request_id=request_id_text,
                        correlation_id=correlation_text,
                        origin_machine=origin_text,
                        origin_surface=surface_text,
                        reason="bus_write_outcome_ambiguous",
                        client_id=getattr(self, "_authenticated_client_id", None),
                        request_schema=REMOTE_WRITE_REQUEST_SCHEMA,
                        request_sha256=request_sha256,
                        message_sha256=message_sha256,
                    )
                    raise

                record = None
                receipt_error = None
                accepted_at = dt.datetime.now(dt.timezone.utc).strftime(
                    "%Y-%m-%dT%H:%M:%SZ"
                )
                if request_id_text is not None:
                    try:
                        record = record_request(
                            request_id=request_id_text,
                            operation="remote_write",
                            state="accepted",
                            client_id=str(
                                getattr(
                                    self,
                                    "_authenticated_client_id",
                                    "unknown",
                                )
                            ),
                            sender=from_agent,
                            recipient=to_agent,
                            msg_type=msg_type,
                            origin_machine=origin_text,
                            origin_surface=surface_text,
                            correlation_id=correlation_text,
                            accepted_at=accepted_at,
                            bus_path=str(bus_path),
                            request_schema=REMOTE_WRITE_REQUEST_SCHEMA,
                            request_sha256=request_sha256,
                            message_sha256=message_sha256,
                            client_timestamp=timestamp,
                            written_timestamp=write_result.timestamp,
                            authorized_content_sha256=(
                                write_result.authorized_content_sha256
                            ),
                            persisted_message_sha256=(
                                write_result.persisted_message_sha256
                            ),
                            row_sha256=write_result.row_sha256,
                            authority=authority_receipt,
                        )
                    except Exception as exc:
                        receipt_error = f"{type(exc).__name__}: {exc}"
                        logger.exception(
                            "Failed to record bridge replay receipt for request_id=%s",
                            request_id_text,
                        )

                # Record BLOCKED dedup key so future BLOCKED duplicates within
                # the window are rejected. Added 2026-09-02.
                if str(msg_type).upper() == "BLOCKED":
                    try:
                        blocked_hash = hashlib.sha256(
                            f"{from_agent}|{to_agent}|{msg_type}|{message}".encode("utf-8")
                        ).hexdigest()[:16]
                        blocked_dedup_key = f"blocked_dedup:{blocked_hash}"
                        record_request(
                            request_id=blocked_dedup_key,
                            operation="remote_write",
                            state="accepted",
                            client_id=str(
                                getattr(
                                    self,
                                    "_authenticated_client_id",
                                    "unknown",
                                )
                            ),
                            sender=from_agent,
                            recipient=to_agent,
                            msg_type=msg_type,
                            origin_machine=origin_text,
                            correlation_id=correlation_text,
                            accepted_at=accepted_at,
                            bus_path=str(bus_path),
                            request_schema=REMOTE_WRITE_REQUEST_SCHEMA,
                            request_sha256=request_sha256,
                            message_sha256=message_sha256,
                            client_timestamp=timestamp,
                        )
                    except Exception:
                        logger.exception(
                            "Failed to record BLOCKED dedup key for hash=%s",
                            blocked_hash,
                        )

                auth_recorded = _record_auth_event(
                    outcome="accepted",
                    client_ip=self._client_ip(),
                    sender=from_agent,
                    recipient=to_agent,
                    msg_type=msg_type,
                    request_id=request_id_text,
                    correlation_id=correlation_text,
                    origin_machine=origin_text,
                    origin_surface=surface_text,
                    bus_path=str(bus_path),
                    operation="remote_write",
                    reason=(
                        f"replay_receipt_error: {receipt_error}"
                        if receipt_error
                        else None
                    ),
                    client_id=getattr(self, "_authenticated_client_id", None),
                    request_schema=(
                        REMOTE_WRITE_REQUEST_SCHEMA
                        if request_id_text is not None
                        else None
                    ),
                    request_sha256=request_sha256,
                    message_sha256=message_sha256,
                    written_timestamp=write_result.timestamp,
                    authorized_content_sha256=(
                        write_result.authorized_content_sha256
                    ),
                    persisted_message_sha256=(
                        write_result.persisted_message_sha256
                    ),
                    row_sha256=write_result.row_sha256,
                    authority=authority_receipt,
                )

                primary_receipt_durable = isinstance(record, dict) and (
                    has_complete_remote_write_receipt(
                        record,
                        expected_request_sha256=request_sha256,
                        expected_message_sha256=message_sha256,
                        require_authority=is_privileged,
                    )
                )
                auth_receipt: dict[str, object] = {
                    "request_id": request_id_text,
                    "operation": "remote_write",
                    "state": "accepted",
                    "sender": from_agent,
                    "recipient": to_agent,
                    "type": msg_type,
                    "accepted_at": accepted_at,
                    "bus_path": str(bus_path),
                    "request_schema": REMOTE_WRITE_REQUEST_SCHEMA,
                    "request_sha256": request_sha256,
                    "message_sha256": message_sha256,
                    "written_timestamp": write_result.timestamp,
                    "authorized_content_sha256": (
                        write_result.authorized_content_sha256
                    ),
                    "persisted_message_sha256": (
                        write_result.persisted_message_sha256
                    ),
                    "row_sha256": write_result.row_sha256,
                }
                if authority_receipt is not None:
                    auth_receipt["authority"] = authority_receipt
                auth_receipt_durable = bool(auth_recorded) and (
                    has_complete_remote_write_receipt(
                        auth_receipt,
                        expected_request_sha256=request_sha256,
                        expected_message_sha256=message_sha256,
                        require_authority=is_privileged,
                    )
                )

                response = {
                    "status": "ok",
                    "duplicate": False,
                    "request_id": request_id_text,
                    "accepted_at": accepted_at,
                    "record": record,
                    "auth_recorded": auth_recorded,
                    "receipt_durable": (
                        primary_receipt_durable or auth_receipt_durable
                    ),
                }
                if proposal_id is not None:
                    response["proposal_id"] = proposal_id
                if receipt_error:
                    response["receipt_error"] = receipt_error
                self._json_response(response)

        except json.JSONDecodeError:
            self._json_response({"error": "Invalid JSON"}, status=400)
        except ValueError as e:
            self._json_response({"error": str(e)}, status=400)
        except PermissionError as e:
            self._json_response({"error": str(e)}, status=403)
        except Exception as e:
            self._json_response({"error": str(e)}, status=500)

    def _handle_batch_post(self, bound_sender: str | None) -> None:
        """Handle /bus/batch — post multiple messages in one request.

        Accepts a JSON array of message objects, each with the same fields
        as a single /bus POST (from, to, type, message, request_id, etc.).
        Applies a single auth check for the batch, then validates and writes
        each message individually. Returns an array of per-message results.

        This eliminates the 5-second-per-post rate-limit wait when an
        orchestrator needs to post multiple receipts at once (e.g., 5
        subagents completing simultaneously).
        """
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length > MAX_REQUEST_BODY * 4:  # Allow larger batch payloads
                self.send_error(413, "Payload too large")
                return
            body = self.rfile.read(content_length).decode('utf-8')
            data = json.loads(body)

            if isinstance(data, dict) and "messages" in data:
                messages = data["messages"]
            elif isinstance(data, list):
                messages = data
            else:
                self._json_response(
                    {"error": "Expected a JSON array or {\"messages\": [...]}"},
                    status=400,
                )
                return

            if not isinstance(messages, list):
                self._json_response({"error": "messages must be an array"}, status=400)
                return

            if len(messages) > MAX_BATCH_MESSAGES:
                self._json_response(
                    {"error": f"Batch exceeds max of {MAX_BATCH_MESSAGES} messages"},
                    status=413,
                )
                return

            if not messages:
                self._json_response({"error": "Empty batch"}, status=400)
                return

            results: list[dict[str, object]] = []
            success_count = 0
            error_count = 0

            for i, msg_data in enumerate(messages):
                if not isinstance(msg_data, dict):
                    results.append({"index": i, "status": "error", "error": "not a JSON object"})
                    error_count += 1
                    continue

                # Reuse the same field extraction as single-post
                sender_fields = [
                    (field, msg_data[field])
                    for field in ("from", "sender")
                    if field in msg_data
                ]
                to_agent = msg_data.get('to', 'all')
                msg_type = msg_data.get('type', 'STATUS')
                message = msg_data.get('message')
                request_id = msg_data.get('request_id')
                correlation_id = msg_data.get('correlation_id')
                origin_machine = msg_data.get('origin_machine')
                principal_proof = msg_data.get('principal_proof')

                try:
                    from_agent, restricted_sender = _resolve_effective_sender(
                        sender_fields=sender_fields,
                        bound_sender=bound_sender,
                        authenticated_client_id=getattr(
                            self, "_authenticated_client_id", None
                        ),
                        sender_binding_configured=bool(
                            getattr(self, "_sender_binding_configured", False)
                        ),
                    )
                except Exception as exc:
                    results.append({"index": i, "status": "error", "error": str(exc)})
                    error_count += 1
                    continue

                if not message:
                    results.append({"index": i, "status": "error", "error": "missing message"})
                    error_count += 1
                    continue

                timestamp = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
                request_id_text = str(request_id) if request_id else f"batch-{i}-{int(time.time())}"
                correlation_text = str(correlation_id) if correlation_id else ""

                try:
                    bus_path = _resolve_bus_path(None)
                    post_message(
                        bus_path=bus_path,
                        from_id=from_agent,
                        to_id=to_agent,
                        msg_type=msg_type,
                        message=message,
                        timestamp=timestamp,
                        correlation_id=correlation_text,
                        validate_sender_identity=True,
                        enforce_sender_identity=True,
                        known_agent_ids=None,
                        validate_recipient_identity=False,
                        enforce_recipient_identity=False,
                        known_recipient_ids=None,
                        validate_message_type=True,
                        enforce_message_type=True,
                        validate_host_presence=True,
                        enforce_host_presence=True,
                        request_id=request_id_text,
                        principal_proof=principal_proof,
                    )
                    results.append({
                        "index": i,
                        "status": "ok",
                        "request_id": request_id_text,
                        "accepted_at": timestamp,
                    })
                    success_count += 1
                except (PermissionError, ValueError) as exc:
                    results.append({"index": i, "status": "error", "error": str(exc)})
                    error_count += 1
                except Exception as exc:
                    logger.exception("Batch post item %d failed", i)
                    results.append({"index": i, "status": "error", "error": str(exc)})
                    error_count += 1

            self._json_response({
                "status": "ok" if error_count == 0 else "partial",
                "success_count": success_count,
                "error_count": error_count,
                "results": results,
            })

        except json.JSONDecodeError:
            self._json_response({"error": "Invalid JSON"}, status=400)
        except Exception as e:
            self._json_response({"error": str(e)}, status=500)

    def do_GET(self):
        """Handle GET requests: health, tail, search."""
        from urllib.parse import parse_qs, urlparse

        parsed = urlparse(self.path)
        path = parsed.path
        params = parse_qs(parsed.query)

        # Preserve deterministic input validation for read endpoints even when
        # bridge authentication is unavailable. This keeps malformed requests
        # distinct from otherwise valid unauthenticated requests.
        n: int | None = None
        if path in {'/bus/tail', '/bus/search'}:
            default_n = '50' if path == '/bus/tail' else '200'
            try:
                n = min(int(params.get('n', [default_n])[0]), MAX_TAIL_LINES)
            except (ValueError, IndexError):
                self.send_error(400, "Invalid 'n' parameter")
                return
            if n < 0:
                n = 0

        if path != '/health':
            authenticated, _ = self._check_post_auth("read")
            if not authenticated:
                return

        if path == '/health':
            self._json_response({
                "status": "up",
                "service": "bus-bridge",
                "version": _get_package_version(),
                "auth_enabled": bool(_load_bridge_credentials()),
                "unauthenticated_operations": ["health"],
            })

        elif path == '/bus/status':
            self._serve_bus_status()

        elif path == '/bus/tail':
            assert n is not None
            date = params.get('date', [None])[0]
            self._serve_bus_lines(n=n, date=date)

        elif path == '/bus/search':
            pattern = params.get('q', [None])[0]
            if not pattern:
                self.send_error(400, "Missing required param: q")
                return
            assert n is not None
            self._serve_bus_lines(n=n, pattern=pattern)

        else:
            self.send_error(404, "Not found")

    def _json_response(self, data: dict[str, object], status: int = 200) -> None:
        """Send a JSON response."""
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def _serve_bus_status(self):
        """Return bus line count and last write timestamp.

        Uses an mtime-based line-count cache to avoid O(n) full-file scans
        on every status request. The cache is invalidated when the file's
        mtime changes.
        """
        try:
            bus_path = _resolve_bus_path(None)
            if not bus_path.exists():
                self._json_response(
                    {"status": "no_bus", "line_count": 0, "last_write": None}
                )
                return

            stat = bus_path.stat()
            last_write = dt.datetime.fromtimestamp(
                stat.st_mtime, dt.timezone.utc
            ).strftime(
                "%Y-%m-%dT%H:%M:%SZ"
            )

            # Mtime-based cache: only count lines when the file has changed
            # since the last status request. This avoids O(n) scans on every
            # poll when the bus is idle (the common case).
            cache_key = str(bus_path)
            cached = _SERVE_BUS_STATUS_CACHE.get(cache_key)
            if cached and cached[0] == stat.st_mtime_ns:
                line_count = cached[1]
            else:
                with open(bus_path, "r", encoding="utf-8") as f:
                    line_count = sum(1 for _ in f)
                _SERVE_BUS_STATUS_CACHE[cache_key] = (stat.st_mtime_ns, line_count)

            self._json_response(
                {
                    "status": "ok",
                    "line_count": line_count,
                    "last_write": last_write,
                    "bus_path": str(bus_path),
                }
            )
        except Exception as e:
            self._json_response({"status": "error", "error": str(e)}, 500)

    def _serve_bus_lines(
        self, n: int = 50, date: str | None = None, pattern: str | None = None
    ) -> None:
        """Read and filter bus lines, return as JSON.

        Optimization: when no date or pattern filter is active (plain tail),
        use collections.deque(maxlen=n) to read only the last n lines instead
        of loading the entire file into memory. This is O(n) in the number of
        returned lines rather than O(total_bus_size).
        """
        from collections import deque

        try:
            bus_path = _resolve_bus_path(None)
            if not bus_path.exists():
                self._json_response({"error": "Bus file not found"}, 404)
                return

            # Fast path: plain tail (no date/pattern filter) — use deque to
            # avoid loading the full file. This is the common case for
            # /bus/tail?n=50.
            if not date and not pattern:
                with open(bus_path, "r", encoding="utf-8") as f:
                    tail_lines = deque(f, maxlen=n)
                lines = list(tail_lines)
            else:
                # Filtered path: must scan the file for matches.
                # For pattern search, scan in reverse and early-terminate
                # once we have n matches (most bus searches want recent).
                if pattern and not date:
                    pat_lower = pattern.lower()
                    matched: list[str] = []
                    with open(bus_path, "r", encoding="utf-8") as f:
                        for line in f:
                            if pat_lower in line.lower():
                                matched.append(line)
                    lines = matched[-n:]
                else:
                    # Date-filtered path: full scan (dates are prefix-sorted
                    # but we don't know the range boundaries without an index)
                    with open(bus_path, "r", encoding="utf-8") as f:
                        lines = f.readlines()
                    if date:
                        lines = [line for line in lines if line.startswith(date)]
                    if pattern:
                        pat_lower = pattern.lower()
                        lines = [line for line in lines if pat_lower in line.lower()]
                    lines = lines[-n:]

            messages = []
            for line in lines:
                line = line.rstrip('\n')
                if not line or line.startswith('timestamp_utc'):
                    continue
                parts = line.split('\t', 4)
                if len(parts) >= 5:
                    messages.append({
                        "timestamp": parts[0],
                        "from": parts[1],
                        "to": parts[2],
                        "type": parts[3],
                        "message": parts[4],
                    })

            self._json_response({"count": len(messages), "messages": messages})

        except Exception as e:
            self._json_response({"error": str(e)}, status=500)


def get_tailscale_ip() -> str | None:
    """Get the Tailscale IP (100.x.x.x)."""
    import subprocess

    try:
        # Try to get from tailscale status
        result = subprocess.run(
            ['tailscale', 'ip', '-4'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            return result.stdout.strip().split('\n')[0]
    except (subprocess.SubprocessError, FileNotFoundError):
        pass

    # Fallback: try to find 100.x interface (cross-platform)
    try:
        import sys as _sys
        if _sys.platform == 'win32':
            # Windows: use ipconfig and parse IPv4 lines
            result = subprocess.run(
                ['ipconfig'], capture_output=True, text=True, timeout=5
            )
            for line in result.stdout.split('\n'):
                line = line.strip()
                if line.startswith('IPv4 Address') and '100.' in line:
                    # "IPv4 Address. . . . . . . . . . . : 100.109.69.16"
                    ip = line.split(':')[-1].strip()
                    if ip.startswith('100.'):
                        return ip
        else:
            # Unix/macOS: use ifconfig
            for line in subprocess.run(
                ['ifconfig'], capture_output=True, text=True, timeout=5
            ).stdout.split('\n'):
                if 'inet 100.' in line:
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if part == 'inet' and i + 1 < len(parts):
                            ip = parts[i + 1]
                            if ip.startswith('100.'):
                                return ip
    except Exception:
        logger.exception("Failed to detect Tailscale IP")

    return None


def run_server(port: int = 18790, bind_all: bool = False) -> None:
    """Run the bridge server."""
    if bind_all:
        host = '0.0.0.0'
    else:
        # Bind to Tailscale interface only for security
        tailscale_ip = get_tailscale_ip()
        if tailscale_ip:
            host = tailscale_ip
            print(f"Binding to Tailscale interface: {host}")
        else:
            host = '127.0.0.1'
            print("Warning: No Tailscale IP found, binding to localhost only")

    credentials = _load_bridge_credentials()
    server = ThreadingHTTPServer((host, port), BusBridgeHandler)
    # daemon_threads ensures workers exit cleanly when server.shutdown() is called.
    server.daemon_threads = True
    print(f"Bus Bridge Server running on http://{host}:{port}")
    print("Endpoints: POST /bus, POST /bus/batch, GET /health, GET /bus/status, GET /bus/tail, GET /bus/search")
    if credentials:
        print("Auth: POST endpoints require Authorization: Bearer <BUS_BRIDGE_TOKEN>")
    else:
        print("Auth: FAIL-CLOSED ΓÇö configure BUS_BRIDGE_TOKEN or BUS_BRIDGE_TOKEN_FILE")
    print("Press Ctrl+C to stop")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
        server.shutdown()


if __name__ == '__main__':  # pragma: no cover
    parser = argparse.ArgumentParser(description='Bus Bridge Server for cross-machine coordination')
    parser.add_argument('--port', '-p', type=int, default=18790, help='Port to listen on (default: 18790)')
    parser.add_argument('--bind-all', '-a', action='store_true', help='Bind to all interfaces (default: Tailscale only)')

    args = parser.parse_args()
    run_server(port=args.port, bind_all=args.bind_all)
