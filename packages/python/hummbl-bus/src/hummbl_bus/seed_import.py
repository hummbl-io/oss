"""Idempotent seed/import tooling for migrating historical coordination bus rows.

Promoted from hummbl-governance/bus/seed_import.py 2026-08-15. Schema and
quarantine labels updated from hummbl_governance to hummbl_bus.
"""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path

from hummbl_bus.authority import PRIVILEGED_TYPES
from hummbl_bus.bus_writer import (
    DEFAULT_BUS_PATH,
    _append_tsv_line,
    _msvcrt_path_lock,
    _resolve_path,
    fcntl,
    msvcrt,
)
from hummbl_bus.replay_ledger import (
    lookup_request,
    record_request,
    resolve_replay_ledger_path,
)


def seed_request_id(tsv_line: str) -> str:
    """Return a deterministic request ID for a historical bus row."""
    normalized = tsv_line.rstrip("\n").encode("utf-8")
    digest = hashlib.sha256(normalized).hexdigest()
    return f"seed-{digest}"


def _append_quarantine(path: Path, record: dict[str, object]) -> None:
    """Append one evidence-preserving quarantine record under a file lock."""
    path.parent.mkdir(parents=True, exist_ok=True)
    guard = _msvcrt_path_lock(path) if msvcrt is not None else contextlib.nullcontext()
    with guard, open(path, "a", encoding="utf-8") as handle:
        if fcntl is not None:
            fcntl.flock(handle, fcntl.LOCK_EX)
        try:
            handle.write(json.dumps(record, separators=(",", ":"), sort_keys=True))
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        finally:
            if fcntl is not None:
                fcntl.flock(handle, fcntl.LOCK_UN)


def _iter_seed_rows(source_path: str | Path):
    """Yield importable bus rows from a TSV file, skipping headers and blanks."""
    with open(source_path, encoding="utf-8") as handle:
        for line_number, raw_line in enumerate(handle, start=1):
            stripped = raw_line.rstrip("\n")
            if not stripped:
                continue
            if (
                line_number == 1
                and stripped == "timestamp_utc\tfrom\tto\ttype\tmessage"
            ):
                continue
            if line_number == 1 and stripped == "timestamp\tfrom\tto\ttype\tmessage":
                continue

            parts = stripped.split("\t")
            if len(parts) != 5:
                if line_number != 2:
                    print(f"Warning: Skipping malformed row at line {line_number}")
                continue
            yield line_number, stripped + "\n", parts


def import_bus_history(
    *,
    source_path: str | Path,
    dest_bus_path: str | Path | None = None,
    ledger_path: str | Path | None = None,
    dry_run: bool = False,
    origin_machine: str = "seed-import",
    quarantine_path: str | Path | None = None,
) -> dict[str, object]:
    """Seed historical bus rows into a canonical bus with idempotent replay ledgering."""
    source = _resolve_path(source_path)
    if not source.exists():
        raise FileNotFoundError(source)

    destination = _resolve_path(dest_bus_path or DEFAULT_BUS_PATH)
    ledger = resolve_replay_ledger_path(ledger_path)
    quarantine = _resolve_path(
        quarantine_path or destination.parent / "privileged_import_quarantine.jsonl"
    )
    source_sha256 = hashlib.sha256(source.read_bytes()).hexdigest()

    rows_seen = 0
    rows_imported = 0
    rows_duplicate = 0
    rows_quarantined = 0

    imported_at = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")

    print(f"[*] Starting import from {source}...", file=sys.stderr)
    for line_num, tsv_line, parts in _iter_seed_rows(source):
        rows_seen += 1

        if rows_seen % 1000 == 0:
            print(f"[*] Processed {rows_seen} rows...", file=sys.stderr)
            sys.stderr.flush()

        request_id = seed_request_id(tsv_line)
        if parts[3].strip().upper() in PRIVILEGED_TYPES:
            rows_quarantined += 1
            if not dry_run:
                _append_quarantine(
                    quarantine,
                    {
                        "schema": "hummbl_bus.import_quarantine.v1",
                        "source_path": str(source),
                        "source_sha256": source_sha256,
                        "line_number": line_num,
                        "row_sha256": hashlib.sha256(
                            tsv_line.rstrip("\n").encode("utf-8")
                        ).hexdigest(),
                        "sender": parts[1],
                        "type": parts[3],
                        "reason": "historical privileged row lacks authenticated principal proof",
                        "reconciliation_status": "open",
                        "quarantined_at": imported_at,
                    },
                )
            continue
        if lookup_request(request_id, ledger_path=ledger) is not None:
            rows_duplicate += 1
            continue

        if not dry_run:
            _append_tsv_line(destination, tsv_line)
            record_request(
                request_id=request_id,
                operation="seed_import",
                sender=parts[1],
                recipient=parts[2],
                msg_type=parts[3],
                origin_machine=origin_machine,
                accepted_at=imported_at,
                bus_path=str(destination),
                ledger_path=ledger,
            )

        rows_imported += 1

    return {
        "source_path": str(source),
        "dest_bus_path": str(destination),
        "ledger_path": str(ledger),
        "dry_run": dry_run,
        "rows_seen": rows_seen,
        "rows_imported": rows_imported,
        "rows_duplicate": rows_duplicate,
        "rows_quarantined": rows_quarantined,
        "quarantine_path": str(quarantine),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Seed historical coordination bus rows into the canonical bus."
    )
    parser.add_argument("--source", required=True, help="Source messages.tsv to import")
    parser.add_argument(
        "--dest",
        default=None,
        help="Destination canonical messages.tsv path. Defaults to the local canonical bus path.",
    )
    parser.add_argument(
        "--ledger",
        default=None,
        help="Replay ledger path override. Defaults to BUS_REPLAY_LEDGER_PATH or the repo ledger path.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate and count rows without appending or recording replay-ledger entries.",
    )
    args = parser.parse_args(argv)

    summary = import_bus_history(
        source_path=args.source,
        dest_bus_path=args.dest,
        ledger_path=args.ledger,
        dry_run=args.dry_run,
    )
    print(summary)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
