"""Client-side outbound spool for remote bus writes.

Promoted from hummbl-governance/bus/spool.py 2026-08-15. Schema and default
paths updated from hummbl_governance to hummbl_bus.
"""

from __future__ import annotations

import json
import os
import tempfile
from datetime import UTC, datetime
from pathlib import Path

from hummbl_bus.bus_writer import (
    _normalize_timestamp,
    _redact_url_credentials,
    _resolve_common_repo_root,
    _resolve_repo_root,
    _validate_bus_path,
    write_dead_letter,
)

DEFAULT_SPOOL_DIR = "hummbl_bus/_state/coordination/spool/outbound"


def resolve_spool_dir(path_override: str | Path | None = None) -> Path:
    """Resolve the outbound spool directory."""
    if path_override is not None:
        return Path(path_override)

    env_override = os.environ.get("BUS_SPOOL_DIR")
    if env_override:
        # F1 (#1729): Validate env-overridden path is confined to an allowed root.
        return _validate_bus_path(env_override, source="BUS_SPOOL_DIR")

    root = _resolve_common_repo_root() or _resolve_repo_root()
    if root is not None:
        return root / DEFAULT_SPOOL_DIR

    return Path(DEFAULT_SPOOL_DIR)


def _now_utc() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _spool_filename(created_at: str, request_id: str) -> str:
    safe_created = created_at.replace(":", "").replace("-", "")
    safe_created = safe_created.replace("T", "T").replace("Z", "Z")
    safe_request = request_id.replace("/", "_")
    return f"{safe_created}--{safe_request}.json"


def enqueue_outbound_record(
    *,
    sender: str,
    recipient: str,
    msg_type: str,
    message: str,
    request_id: str,
    correlation_id: str | None = None,
    origin_machine: str | None = None,
    bridge_url: str | None = None,
    spool_dir: str | Path | None = None,
    created_at: str | None = None,
) -> Path:
    """Persist one outbound record to the local spool."""
    from hummbl_bus.authority import PRIVILEGED_TYPES

    if msg_type.strip().upper() in PRIVILEGED_TYPES:
        raise PermissionError(
            "privileged bus messages require live authenticated delivery and cannot be spooled"
        )
    target_dir = resolve_spool_dir(spool_dir)
    target_dir.mkdir(parents=True, exist_ok=True)

    created = _now_utc() if created_at is None else _normalize_timestamp(created_at)
    record: dict[str, object] = {
        "schema": "hummbl_bus.spool.v1",
        "request_id": request_id,
        "sender": sender,
        "recipient": recipient,
        "type": msg_type,
        "message": message,
        "created_at": created,
        "last_attempt_at": None,
        "attempt_count": 0,
    }
    if correlation_id:
        record["correlation_id"] = correlation_id
    if origin_machine:
        record["origin_machine"] = origin_machine
    if bridge_url:
        # #1761: Redact credentials in bridge_url before persisting to spool
        record["bridge_url"] = _redact_url_credentials(bridge_url)

    filename = _spool_filename(created, request_id)
    final_path = target_dir / filename

    with tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        dir=target_dir,
        prefix=".tmp-",
        suffix=".json",
        delete=False,
    ) as tmp:
        json.dump(record, tmp, separators=(",", ":"), sort_keys=True)
        tmp.write("\n")
        tmp_path = Path(tmp.name)

    tmp_path.replace(final_path)
    return final_path


def load_spool_record(path: str | Path) -> dict[str, object]:
    """Load one spooled outbound record.

    Raises:
        FileNotFoundError: If the spool file does not exist.
        json.JSONDecodeError: If the file content is not valid JSON.
    """
    raw = Path(path).read_text(encoding="utf-8")
    return json.loads(raw)


def save_spool_record(path: str | Path, record: dict[str, object]) -> None:
    """Persist an updated spool record atomically."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        dir=target.parent,
        prefix=".tmp-",
        suffix=".json",
        delete=False,
    ) as tmp:
        json.dump(record, tmp, separators=(",", ":"), sort_keys=True)
        tmp.write("\n")
        tmp_path = Path(tmp.name)
    tmp_path.replace(target)


def mark_spool_attempt(
    path: str | Path,
    *,
    attempted_at: str | None = None,
) -> dict[str, object]:
    """Increment attempt count and persist latest attempt timestamp."""
    record = load_spool_record(path)
    count = int(record.get("attempt_count", 0))  # type: ignore[call-overload]
    record["attempt_count"] = count + 1
    record["last_attempt_at"] = (
        _now_utc() if attempted_at is None else _normalize_timestamp(attempted_at)
    )
    save_spool_record(path, record)
    return record


def list_spool_records(spool_dir: str | Path | None = None) -> list[Path]:
    """List spooled records oldest-first."""
    target_dir = resolve_spool_dir(spool_dir)
    if not target_dir.exists():
        return []
    return sorted(p for p in target_dir.glob("*.json") if p.is_file())


def remove_spool_record(path: str | Path) -> None:
    """Delete a spool record if present."""
    target = Path(path)
    if target.exists():
        target.unlink()


def move_spool_record_to_dead_letter(
    path: str | Path,
    *,
    reason: str,
    dead_letter_path: str | Path,
    source: str = "replay_worker",
) -> None:
    """Write a dead-letter entry for a spool record and remove it."""
    record = load_spool_record(path)
    write_dead_letter(
        dead_letter_path=dead_letter_path,
        source=source,
        reason=reason,
        payload=record,
    )
    remove_spool_record(path)
