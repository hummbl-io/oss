"""Persistent replay ledger for remote bus writes and seed/import operations.

Promoted from hummbl-governance/bus/replay_ledger.py 2026-08-15. Default path
updated from hummbl_governance to hummbl_bus. Locking uses the cross-process
sibling-file pattern from #1915.
"""

from __future__ import annotations

import contextlib
import json
import os
import re
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Iterator

from hummbl_bus.bus_writer import (
    _cross_process_lock,
    _fsync_parent_directory,
    _msvcrt_path_lock,
    _normalize_timestamp,
    _resolve_common_repo_root,
    _resolve_repo_root,
    _validate_bus_path,
    fcntl,
    msvcrt,
)

DEFAULT_REPLAY_LEDGER_PATH = "hummbl_bus/_state/coordination/replay_ledger.jsonl"
REMOTE_WRITE_REQUEST_SCHEMA = "hummbl_bus.remote_write.v2"
_VERIFIED_PRINCIPAL_SCHEMA = "hummbl_bus.verified_principal.v1"
_AUTHORITY_FIELDS = frozenset(
    {
        "schema",
        "principal",
        "key_id",
        "key_sha256",
        "request_id",
        "sender",
        "recipient",
        "type",
        "message_sha256",
        "nonce_sha256",
        "audience",
        "bus_id",
        "issued_at",
        "expires_at",
        "proof_sha256",
    }
)
_REMOTE_WRITE_LINKAGE_FIELDS = frozenset(
    {
        "bus_path",
        "written_timestamp",
        "request_sha256",
        "message_sha256",
        "authorized_content_sha256",
        "persisted_message_sha256",
        "row_sha256",
    }
)


def _validated_authority_receipt(
    authority: Mapping[str, object],
    *,
    request_id: str,
    sender: str,
    recipient: str,
    msg_type: str,
) -> dict[str, object]:
    """Validate verifier-derived attribution before it enters the ledger."""
    receipt = dict(authority)
    if set(receipt) != _AUTHORITY_FIELDS:
        raise ValueError("authority receipt fields do not match the v1 contract")
    expected = {
        "schema": _VERIFIED_PRINCIPAL_SCHEMA,
        "request_id": request_id,
        "sender": sender,
        "recipient": recipient,
        "type": msg_type.strip().upper(),
    }
    for field, value in expected.items():
        if receipt[field] != value:
            raise ValueError(f"authority receipt {field} does not match request")
    for field in ("principal", "key_id", "audience", "bus_id"):
        if not isinstance(receipt[field], str) or not str(receipt[field]).strip():
            raise ValueError(f"authority receipt {field} is invalid")
    for field in ("key_sha256", "message_sha256", "nonce_sha256", "proof_sha256"):
        if not isinstance(receipt[field], str) or not re.fullmatch(
            r"[0-9a-f]{64}", str(receipt[field])
        ):
            raise ValueError(f"authority receipt {field} is invalid")
    for field in ("issued_at", "expires_at"):
        if isinstance(receipt[field], bool) or not isinstance(receipt[field], int):
            raise ValueError(f"authority receipt {field} is invalid")
    return receipt


def has_complete_remote_write_receipt(
    record: Mapping[str, object],
    *,
    expected_request_sha256: str | None = None,
    expected_message_sha256: str | None = None,
    require_authority: bool = False,
) -> bool:
    """Return whether a v2 accepted receipt has exact append linkage."""
    if record.get("operation") != "remote_write":
        return False
    if record.get("state", "accepted") != "accepted":
        return False
    if record.get("request_schema") != REMOTE_WRITE_REQUEST_SCHEMA:
        return False
    if any(field not in record for field in _REMOTE_WRITE_LINKAGE_FIELDS):
        return False

    for field in (
        "request_sha256",
        "message_sha256",
        "authorized_content_sha256",
        "persisted_message_sha256",
        "row_sha256",
    ):
        value = record.get(field)
        if not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{64}", value):
            return False

    if expected_request_sha256 is not None and (
        record.get("request_sha256") != expected_request_sha256
    ):
        return False
    if expected_message_sha256 is not None and (
        record.get("message_sha256") != expected_message_sha256
    ):
        return False
    if record.get("authorized_content_sha256") != record.get("message_sha256"):
        return False
    if not isinstance(record.get("bus_path"), str) or not str(
        record.get("bus_path")
    ).strip():
        return False

    written_timestamp = record.get("written_timestamp")
    if not isinstance(written_timestamp, str):
        return False
    try:
        parsed_timestamp = datetime.strptime(
            written_timestamp,
            "%Y-%m-%dT%H:%M:%SZ",
        )
    except ValueError:
        return False
    if parsed_timestamp.strftime("%Y-%m-%dT%H:%M:%SZ") != written_timestamp:
        return False

    if require_authority:
        authority = record.get("authority")
        if not isinstance(authority, Mapping):
            return False
        try:
            validated = _validated_authority_receipt(
                authority,
                request_id=str(record.get("request_id", "")),
                sender=str(record.get("sender", "")),
                recipient=str(record.get("recipient", "")),
                msg_type=str(record.get("type", "")),
            )
        except (KeyError, TypeError, ValueError):
            return False
        if validated.get("message_sha256") != record.get("message_sha256"):
            return False

    return True


def resolve_replay_ledger_path(path_override: str | Path | None = None) -> Path:
    """Resolve the replay ledger path."""
    if path_override is not None:
        return Path(path_override)

    env_override = os.environ.get("BUS_REPLAY_LEDGER_PATH")
    if env_override:
        # F1 (#1729): Validate env-overridden path is confined to an allowed root.
        return _validate_bus_path(env_override, source="BUS_REPLAY_LEDGER_PATH")

    root = _resolve_common_repo_root() or _resolve_repo_root()
    if root is not None:
        return root / DEFAULT_REPLAY_LEDGER_PATH

    return Path(DEFAULT_REPLAY_LEDGER_PATH)


def lookup_request(
    request_id: str,
    *,
    ledger_path: str | Path | None = None,
) -> dict[str, object] | None:
    """Return the latest accepted request record, if present."""
    path = resolve_replay_ledger_path(ledger_path)
    if not path.exists():
        return None

    found: dict[str, object] | None = None
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            if record.get("request_id") == request_id:
                found = record
    return found


@contextlib.contextmanager
def request_guard(
    request_id: str,
    *,
    ledger_path: str | Path | None = None,
) -> Iterator[None]:
    """Serialize replay lookup, bus append, and receipt persistence.

    The bridge is served by ``ThreadingHTTPServer`` and may also be started in
    more than one process against the same state directory.  A lookup followed
    by a bus append and a later receipt write is otherwise racy: two requests
    with the same idempotency key can both append before either receipt lands.

    The guard intentionally serializes all remote-write request IDs. Bus
    throughput is low, and one shared lock keeps the cross-platform locking
    behavior simple and auditable. The request ID is validated here but is
    never used as a filesystem path component.
    """
    if not isinstance(request_id, str) or not request_id.strip():
        raise ValueError("request_id must be a non-empty string")

    ledger = resolve_replay_ledger_path(ledger_path)
    guard_target = ledger.parent / ".request-guard" / "remote-write"
    guard_target.parent.mkdir(parents=True, exist_ok=True)
    local_guard = (
        _msvcrt_path_lock(guard_target)
        if msvcrt is not None
        else contextlib.nullcontext()
    )
    with local_guard, _cross_process_lock(guard_target):
        yield


def record_request(
    *,
    request_id: str,
    operation: str,
    sender: str,
    recipient: str,
    msg_type: str,
    state: str | None = None,
    client_id: str | None = None,
    origin_machine: str | None = None,
    origin_surface: str | None = None,
    correlation_id: str | None = None,
    accepted_at: str | None = None,
    bus_path: str | None = None,
    request_schema: str | None = None,
    request_sha256: str | None = None,
    message_sha256: str | None = None,
    client_timestamp: str | None = None,
    written_timestamp: str | None = None,
    authorized_content_sha256: str | None = None,
    persisted_message_sha256: str | None = None,
    row_sha256: str | None = None,
    authority: Mapping[str, object] | None = None,
    ledger_path: str | Path | None = None,
) -> dict[str, object]:
    """Append a durable request state record to the replay ledger."""
    path = resolve_replay_ledger_path(ledger_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    if accepted_at is None:
        accepted_at = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    else:
        accepted_at = _normalize_timestamp(accepted_at)

    record: dict[str, object] = {
        "request_id": request_id,
        "operation": operation,
        "sender": sender,
        "recipient": recipient,
        "type": msg_type,
        "accepted_at": accepted_at,
    }
    if state is not None:
        if state not in {"pending", "accepted"}:
            raise ValueError("state must be 'pending' or 'accepted'")
        record["state"] = state
    if client_id:
        record["client_id"] = client_id
    if origin_machine:
        record["origin_machine"] = origin_machine
    if origin_surface:
        record["origin_surface"] = origin_surface
    if correlation_id:
        record["correlation_id"] = correlation_id
    if bus_path:
        record["bus_path"] = bus_path
    if request_schema:
        record["request_schema"] = request_schema
    if request_sha256:
        record["request_sha256"] = request_sha256
    if message_sha256:
        record["message_sha256"] = message_sha256
    if client_timestamp:
        record["client_timestamp"] = client_timestamp
    if written_timestamp:
        record["written_timestamp"] = written_timestamp
    for field, value in (
        ("authorized_content_sha256", authorized_content_sha256),
        ("persisted_message_sha256", persisted_message_sha256),
        ("row_sha256", row_sha256),
    ):
        if value is not None:
            if not re.fullmatch(r"[0-9a-f]{64}", value):
                raise ValueError(f"{field} must be canonical SHA-256")
            record[field] = value
    if authority is not None:
        record["authority"] = _validated_authority_receipt(
            authority,
            request_id=request_id,
            sender=sender,
            recipient=recipient,
            msg_type=msg_type,
        )

    if (
        operation == "remote_write"
        and state == "accepted"
        and request_schema == REMOTE_WRITE_REQUEST_SCHEMA
        and not has_complete_remote_write_receipt(
            record,
            require_authority=msg_type.strip().upper()
            in {"DECISION", "DIRECTIVE"},
        )
    ):
        raise ValueError(
            "accepted v2 remote_write requires complete append linkage"
        )

    line = json.dumps(record, separators=(",", ":"), sort_keys=True) + "\n"
    is_new_file = not path.exists()
    path_lock = (
        _msvcrt_path_lock(path) if msvcrt is not None else contextlib.nullcontext()
    )
    with path_lock, _cross_process_lock(path), open(path, "a", encoding="utf-8") as f:
        if fcntl is not None:
            fcntl.flock(f, fcntl.LOCK_EX)
        f.write(line)
        f.flush()
        os.fsync(f.fileno())
        if fcntl is not None:
            fcntl.flock(f, fcntl.LOCK_UN)
    if is_new_file:
        _fsync_parent_directory(path)
    return record
