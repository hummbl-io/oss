"""Persistent replay ledger for remote bus writes and seed/import operations.

Promoted from hummbl-governance/bus/replay_ledger.py 2026-08-15. Default path
updated from hummbl_governance to hummbl_bus. Locking uses the cross-process
sibling-file pattern from #1915.
"""

from __future__ import annotations

import contextlib
import json
import os
from datetime import UTC, datetime
from pathlib import Path

from hummbl_bus.bus_writer import (
    _cross_process_lock,
    _msvcrt_path_lock,
    _normalize_timestamp,
    _resolve_common_repo_root,
    _resolve_repo_root,
    _validate_bus_path,
    fcntl,
    msvcrt,
)

DEFAULT_REPLAY_LEDGER_PATH = "hummbl_bus/_state/coordination/replay_ledger.jsonl"


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
    """Return a previously accepted request record, if present."""
    path = resolve_replay_ledger_path(ledger_path)
    if not path.exists():
        return None

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
                return record
    return None


def record_request(
    *,
    request_id: str,
    operation: str,
    sender: str,
    recipient: str,
    msg_type: str,
    origin_machine: str | None = None,
    correlation_id: str | None = None,
    accepted_at: str | None = None,
    bus_path: str | None = None,
    ledger_path: str | Path | None = None,
) -> dict[str, object]:
    """Append a request acceptance record to the replay ledger."""
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
    if origin_machine:
        record["origin_machine"] = origin_machine
    if correlation_id:
        record["correlation_id"] = correlation_id
    if bus_path:
        record["bus_path"] = bus_path

    line = json.dumps(record, separators=(",", ":"), sort_keys=True) + "\n"
    path_lock = (
        _msvcrt_path_lock(path) if msvcrt is not None else contextlib.nullcontext()
    )
    with _cross_process_lock(path), path_lock, open(path, "a", encoding="utf-8") as f:
        if fcntl is not None:
            fcntl.flock(f, fcntl.LOCK_EX)
        f.write(line)
        f.flush()
        if fcntl is not None:
            fcntl.flock(f, fcntl.LOCK_UN)
    return record
