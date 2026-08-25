"""Oldest-first replay worker for outbound bus spool records.

Promoted from hummbl-governance/bus/replay_worker.py 2026-08-15.
"""

from __future__ import annotations

from pathlib import Path

from hummbl_bus.bridge_client import DEFAULT_PORT, post_to_remote_bus_result
from hummbl_bus.spool import (
    list_spool_records,
    load_spool_record,
    mark_spool_attempt,
    move_spool_record_to_dead_letter,
    remove_spool_record,
)


def replay_next_record(
    host: str,
    *,
    port: int = DEFAULT_PORT,
    spool_dir: str | Path | None = None,
    dead_letter_path: str | Path | None = None,
    post_func=post_to_remote_bus_result,
) -> dict[str, object]:
    """Replay the oldest queued outbound record once.

    Returns a summary dict with:
    - status: empty, replayed, duplicate, deferred, dead_lettered
    - path: spool record path if applicable
    - attempts: updated attempt count for deferred records
    """
    paths = list_spool_records(spool_dir)
    if not paths:
        return {"status": "empty"}

    target = paths[0]
    record = load_spool_record(target)
    from hummbl_bus.authority import PRIVILEGED_TYPES

    if str(record.get("type", "")).strip().upper() in PRIVILEGED_TYPES:
        if dead_letter_path is None:
            raise ValueError(
                "dead_letter_path is required to quarantine privileged spool records"
            )
        move_spool_record_to_dead_letter(
            target,
            reason="privileged records cannot be replayed; fresh authenticated proof required",
            dead_letter_path=dead_letter_path,
        )
        return {
            "status": "dead_lettered",
            "path": str(target),
            "request_id": record.get("request_id"),
        }
    result = post_func(
        host,
        record["sender"],
        record["recipient"],
        record["type"],
        record["message"],
        request_id=record.get("request_id"),
        correlation_id=record.get("correlation_id"),
        origin_machine=record.get("origin_machine"),
        port=port,
    )

    if result.get("ok"):
        remove_spool_record(target)
        return {
            "status": "duplicate" if result.get("duplicate") else "replayed",
            "path": str(target),
            "request_id": record.get("request_id"),
        }

    if result.get("permanent_error"):
        if dead_letter_path is None:
            raise ValueError(
                "dead_letter_path is required for permanent replay failures"
            )
        move_spool_record_to_dead_letter(
            target,
            reason=f"permanent replay failure: {result.get('status_code')} {result.get('error', '')}".strip(),
            dead_letter_path=dead_letter_path,
        )
        return {
            "status": "dead_lettered",
            "path": str(target),
            "request_id": record.get("request_id"),
        }

    updated = mark_spool_attempt(target)
    return {
        "status": "deferred",
        "path": str(target),
        "request_id": record.get("request_id"),
        "attempts": updated.get("attempt_count"),
    }
