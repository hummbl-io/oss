"""IssueOps run receipt — structured record of each IssueOps execution.

The IssueOps system generates GitHub issues from audit findings but did not
previously record a structured receipt for each run. This module provides the
canonical create/validate/append path so every run is durably logged with
what was generated, when, and with what evidence.

Schema: hummbl_cognition/schemas/issueops_run_receipt.schema.json
Log:     _state/cognition/issueops_receipts.jsonl (append-only JSONL)

Design:
  - Pure stdlib (uuid, json, os, hashlib, datetime, pathlib, argparse)
  - Append-only JSONL with platform-appropriate advisory locking
  - CLI: python -m hummbl_cognition.issueops_receipt create --source ... --agent ...
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    import fcntl  # type: ignore[attr-defined]
except ImportError:  # pragma: no cover - exercised on Windows
    fcntl = None

try:
    import msvcrt  # type: ignore[attr-defined]
except ImportError:  # pragma: no cover - exercised on POSIX
    msvcrt = None

logger = logging.getLogger(__name__)

__all__ = [
    "IssueOpsReceiptError",
    "create_receipt",
    "validate_receipt",
    "append_receipt",
    "read_receipts",
    "DEFAULT_RECEIPT_LOG_PATH",
    "VALID_SOURCES",
    "VALID_SEVERITIES",
    "SCHEMA_PATH",
]

# Default log location (relative to repo root)
DEFAULT_RECEIPT_LOG_PATH = "_state/cognition/issueops_receipts.jsonl"

SCHEMA_PATH = (
    Path(__file__).resolve().parent
    / "schemas"
    / "issueops_run_receipt.schema.json"
)

VALID_SOURCES = frozenset(
    {"chatgpt-connector", "arbiter-audit", "manual", "scheduled", "webhook"}
)
VALID_SEVERITIES = frozenset({"low", "medium", "high", "critical"})

_THREAD_WRITE_LOCK = threading.Lock()
_WINDOWS_LOCK_SPAN = 0x7FFFFFFF


class IssueOpsReceiptError(ValueError):
    """Raised when a receipt fails validation or construction."""


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _utc_now() -> str:
    """Return current UTC timestamp in ISO 8601 Z format."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _new_run_id() -> str:
    """Generate a unique run id: issueops-<uuid4>."""
    return f"issueops-{uuid.uuid4()}"


def _lock_file(file_obj) -> None:
    """Acquire an exclusive advisory lock for the current file object."""
    if fcntl is not None:
        fcntl.flock(file_obj, fcntl.LOCK_EX)
        return
    if msvcrt is not None:
        file_obj.flush()
        file_obj.seek(0)
        msvcrt.locking(file_obj.fileno(), msvcrt.LK_LOCK, _WINDOWS_LOCK_SPAN)
        return
    logger.warning("No advisory file locking backend available; proceeding unlocked")


def _unlock_file(file_obj) -> None:
    """Release the advisory lock for the current file object."""
    if fcntl is not None:
        fcntl.flock(file_obj, fcntl.LOCK_UN)
        return
    if msvcrt is not None:
        file_obj.flush()
        file_obj.seek(0)
        msvcrt.locking(file_obj.fileno(), msvcrt.LK_UNLCK, _WINDOWS_LOCK_SPAN)
        return


def _resolve_log_path(override: str | Path | None = None) -> Path:
    """Resolve the receipt log file path.

    Priority: explicit override > ISSUEOPS_RECEIPT_LOG env > git root default.
    """
    if override:
        return Path(override)

    env_path = os.environ.get("ISSUEOPS_RECEIPT_LOG")
    if env_path:
        return Path(env_path)

    try:
        import subprocess

        root = subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"],
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=5,
        ).strip()
        if root:
            return Path(root) / DEFAULT_RECEIPT_LOG_PATH
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        pass

    return Path(DEFAULT_RECEIPT_LOG_PATH)


def _load_schema() -> dict[str, Any]:
    """Load the IssueOps run receipt JSON schema from disk."""
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def _canonical_json(obj: dict[str, Any]) -> str:
    """Serialize dict to canonical JSON (sorted keys, compact)."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))


def _content_hash(receipt: dict[str, Any]) -> str:
    """Compute SHA-256 of the canonical receipt (excluding the hash field)."""
    stripped = {k: v for k, v in receipt.items() if k != "content_hash"}
    return hashlib.sha256(_canonical_json(stripped).encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


def validate_receipt(
    receipt: dict[str, Any],
    schema: dict[str, Any] | None = None,
) -> tuple[bool, list[str]]:
    """Validate a receipt dict against the IssueOps run receipt schema.

    Returns (is_valid, errors). Uses the stdlib-only hummbl_governance
    SchemaValidator when available, falling back to inline structural checks.
    """
    if schema is None:
        schema = _load_schema()

    # Prefer the canonical stdlib validator from hummbl_governance
    try:
        from hummbl_cognition.schema_validator import validate as _validate

        errors = _validate(receipt, schema)
        return len(errors) == 0, errors
    except Exception:  # pragma: no cover - fallback path
        pass

    # Inline fallback validation (stdlib only)
    errors: list[str] = []
    required = schema.get("required", [])
    for field in required:
        if field not in receipt or receipt[field] is None:
            errors.append(f"missing required field: {field}")

    if errors:
        return False, errors

    # Type checks
    props = schema.get("properties", {})
    type_map = {
        "run_id": str,
        "timestamp": str,
        "source": str,
        "total_issues_processed": int,
        "agent": str,
        "evidence_refs": list,
        "issues_created": list,
        "issues_closed": list,
        "issues_commented": list,
    }
    for field, expected in type_map.items():
        if field in receipt and receipt[field] is not None:
            if not isinstance(receipt[field], expected):
                errors.append(
                    f"{field}: expected {expected.__name__}, got "
                    f"{type(receipt[field]).__name__}"
                )

    if receipt.get("source") and receipt["source"] not in VALID_SOURCES:
        errors.append(
            f"source: {receipt['source']!r} not in {sorted(VALID_SOURCES)}"
        )

    if receipt.get("total_issues_processed") is not None:
        tip = receipt["total_issues_processed"]
        if tip < 0:
            errors.append("total_issues_processed must be >= 0")

    # issues_created sub-objects
    for i, item in enumerate(receipt.get("issues_created", [])):
        if not isinstance(item, dict):
            errors.append(f"issues_created[{i}]: expected object")
            continue
        for sub in ("repo", "number", "title", "category", "severity"):
            if sub not in item:
                errors.append(f"issues_created[{i}]: missing {sub}")
        sev = item.get("severity")
        if sev and sev not in VALID_SEVERITIES:
            errors.append(
                f"issues_created[{i}].severity: {sev!r} not in "
                f"{sorted(VALID_SEVERITIES)}"
            )

    # issues_closed sub-objects
    for i, item in enumerate(receipt.get("issues_closed", [])):
        if not isinstance(item, dict):
            errors.append(f"issues_closed[{i}]: expected object")
            continue
        for sub in ("repo", "number", "reason"):
            if sub not in item:
                errors.append(f"issues_closed[{i}]: missing {sub}")

    # issues_commented sub-objects
    for i, item in enumerate(receipt.get("issues_commented", [])):
        if not isinstance(item, dict):
            errors.append(f"issues_commented[{i}]: expected object")
            continue
        for sub in ("repo", "number"):
            if sub not in item:
                errors.append(f"issues_commented[{i}]: missing {sub}")

    return len(errors) == 0, errors


# ---------------------------------------------------------------------------
# Receipt construction
# ---------------------------------------------------------------------------


def create_receipt(
    *,
    source: str,
    agent: str,
    issues_created: list[dict[str, Any]] | None = None,
    issues_closed: list[dict[str, Any]] | None = None,
    issues_commented: list[dict[str, Any]] | None = None,
    evidence_refs: list[str] | None = None,
    run_id: str | None = None,
    timestamp: str | None = None,
    notes: str | None = None,
    skipped_duplicate_candidates: list[dict[str, Any]] | None = None,
    read_only_candidates: list[dict[str, Any]] | None = None,
    access_limits: list[dict[str, Any]] | None = None,
    write_boundary: list[str] | None = None,
    quality_scores: dict[str, Any] | None = None,
    run_disposition: str | None = None,
    backpressure_notes: str | None = None,
) -> dict[str, Any]:
    """Construct and validate an IssueOps run receipt.

    Args:
        source: Origin of the run (one of VALID_SOURCES).
        agent: Canonical agent identity that ran the IssueOps.
        issues_created: List of {repo, number, title, category, severity}.
        issues_closed: List of {repo, number, reason}.
        issues_commented: List of {repo, number}.
        evidence_refs: List of links to audit reports / bus receipts.
        run_id: Optional explicit run id (auto-generated if omitted).
        timestamp: Optional explicit ISO 8601 timestamp (auto if omitted).
        notes: Optional free-form notes.
        skipped_duplicate_candidates: Candidates skipped as duplicates.
        read_only_candidates: Candidates outside the write boundary.
        access_limits: Access-limit decisions encountered.
        write_boundary: List of repos where issue creation is authorized.
        quality_scores: Quality score summary for created issues.
        run_disposition: Overall disposition (created, no-op, etc.).
        backpressure_notes: Notes about throttling applied.

    Returns:
        A validated receipt dict (with content_hash appended).

    Raises:
        IssueOpsReceiptError: if validation fails.
    """
    if not source or source not in VALID_SOURCES:
        raise IssueOpsReceiptError(
            f"source must be one of {sorted(VALID_SOURCES)}, got {source!r}"
        )
    if not agent or not agent.strip():
        raise IssueOpsReceiptError("agent must be a non-empty string")

    created = list(issues_created or [])
    closed = list(issues_closed or [])
    commented = list(issues_commented or [])
    evidence = list(evidence_refs or [])

    # Compute total issues processed (deduplicated by (repo, number))
    seen: set[tuple[str, int]] = set()
    for item in created:
        seen.add((item["repo"], item["number"]))
    for item in closed:
        seen.add((item["repo"], item["number"]))
    for item in commented:
        seen.add((item["repo"], item["number"]))
    total = len(seen)

    receipt: dict[str, Any] = {
        "run_id": run_id or _new_run_id(),
        "timestamp": timestamp or _utc_now(),
        "source": source,
        "issues_created": created,
        "issues_closed": closed,
        "issues_commented": commented,
        "total_issues_processed": total,
        "agent": agent,
        "evidence_refs": evidence,
    }
    if notes:
        receipt["notes"] = notes
    if skipped_duplicate_candidates:
        receipt["skipped_duplicate_candidates"] = list(skipped_duplicate_candidates)
    if read_only_candidates:
        receipt["read_only_candidates"] = list(read_only_candidates)
    if access_limits:
        receipt["access_limits"] = list(access_limits)
    if write_boundary:
        receipt["write_boundary"] = list(write_boundary)
    if quality_scores:
        receipt["quality_scores"] = dict(quality_scores)
    if run_disposition:
        receipt["run_disposition"] = run_disposition
    if backpressure_notes:
        receipt["backpressure_notes"] = backpressure_notes

    # Validate before hashing
    is_valid, errors = validate_receipt(receipt)
    if not is_valid:
        raise IssueOpsReceiptError(
            "receipt failed validation: " + "; ".join(errors)
        )

    # Append content hash for tamper detection
    receipt["content_hash"] = _content_hash(receipt)
    return receipt


# ---------------------------------------------------------------------------
# Append-only JSONL persistence
# ---------------------------------------------------------------------------


def append_receipt(
    receipt: dict[str, Any],
    log_path: str | Path | None = None,
) -> Path:
    """Append a validated receipt to the JSONL log.

    Creates parent directories as needed. Uses platform-appropriate advisory
    locking for mutual exclusion across processes.

    Returns the resolved path that was written to.
    """
    is_valid, errors = validate_receipt(receipt)
    if not is_valid:
        raise IssueOpsReceiptError(
            "cannot append invalid receipt: " + "; ".join(errors)
        )

    path = _resolve_log_path(log_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    line = json.dumps(receipt, sort_keys=True, separators=(",", ":"))

    with _THREAD_WRITE_LOCK:
        with open(path, "a", encoding="utf-8") as fh:
            _lock_file(fh)
            try:
                fh.write(line + "\n")
                fh.flush()
                os.fsync(fh.fileno())
            finally:
                _unlock_file(fh)

    return path


def read_receipts(
    log_path: str | Path | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    """Read receipts from the JSONL log (most recent first).

    Args:
        log_path: Override for the log file path.
        limit: Maximum number of receipts to return.

    Returns:
        List of receipt dicts, newest first.
    """
    path = _resolve_log_path(log_path)
    if not path.exists():
        return []

    receipts: list[dict[str, Any]] = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                receipts.append(json.loads(line))
            except json.JSONDecodeError as exc:
                logger.warning("skipping unparseable receipt line: %s", exc)

    receipts.reverse()  # newest first
    return receipts[:limit]


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _build_parser() -> "argparse.ArgumentParser":  # type: ignore[name-defined]
    import argparse

    parser = argparse.ArgumentParser(
        prog="python -m hummbl_cognition.issueops_receipt",
        description="IssueOps run receipt writer — record structured run receipts",
    )
    parser.add_argument(
        "--log",
        help="Override receipt log file path",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # create
    p_create = subparsers.add_parser(
        "create", help="Create and append a new IssueOps run receipt"
    )
    p_create.add_argument(
        "--source",
        required=True,
        choices=sorted(VALID_SOURCES),
        help="Origin of the run",
    )
    p_create.add_argument(
        "--agent",
        required=True,
        help="Canonical agent identity that ran the IssueOps",
    )
    p_create.add_argument(
        "--issues-created",
        help="JSON array of {repo, number, title, category, severity}",
    )
    p_create.add_argument(
        "--issues-closed",
        help="JSON array of {repo, number, reason}",
    )
    p_create.add_argument(
        "--issues-commented",
        help="JSON array of {repo, number}",
    )
    p_create.add_argument(
        "--evidence-refs",
        nargs="*",
        default=[],
        help="Links to audit reports / bus receipts",
    )
    p_create.add_argument("--notes", help="Optional free-form notes")
    p_create.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the receipt without appending to the log",
    )

    # list
    p_list = subparsers.add_parser("list", help="List recent receipts")
    p_list.add_argument("--limit", type=int, default=20, help="Max receipts")

    # validate
    p_validate = subparsers.add_parser(
        "validate", help="Validate all receipts in the log"
    )

    return parser


def _parse_json_array(raw: str | None, field_name: str) -> list[dict[str, Any]]:
    """Parse a JSON array argument, returning [] for None."""
    if not raw:
        return []
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise IssueOpsReceiptError(
            f"{field_name}: invalid JSON: {exc}"
        ) from exc
    if not isinstance(parsed, list):
        raise IssueOpsReceiptError(f"{field_name}: expected JSON array")
    return parsed


def cmd_create(args: "argparse.Namespace") -> int:  # type: ignore[name-defined]
    """Create and append a new IssueOps run receipt."""
    try:
        receipt = create_receipt(
            source=args.source,
            agent=args.agent,
            issues_created=_parse_json_array(args.issues_created, "--issues-created"),
            issues_closed=_parse_json_array(args.issues_closed, "--issues-closed"),
            issues_commented=_parse_json_array(
                args.issues_commented, "--issues-commented"
            ),
            evidence_refs=args.evidence_refs,
            notes=args.notes,
        )
    except IssueOpsReceiptError as exc:
        print(f"ERROR: {exc}", file=__import__("sys").stderr)
        return 1

    if args.dry_run:
        print(json.dumps(receipt, indent=2))
        return 0

    try:
        path = append_receipt(receipt, log_path=args.log)
    except (IssueOpsReceiptError, OSError) as exc:
        print(f"ERROR: {exc}", file=__import__("sys").stderr)
        return 1

    print(
        f"Appended receipt {receipt['run_id']} "
        f"({receipt['total_issues_processed']} issues) -> {path}"
    )
    return 0


def cmd_list(args: "argparse.Namespace") -> int:  # type: ignore[name-defined]
    """List recent receipts."""
    import sys

    receipts = read_receipts(log_path=args.log, limit=args.limit)
    if not receipts:
        print("No receipts found.")
        return 0

    for r in receipts:
        print(
            f"[{r.get('timestamp', '?')}] {r.get('run_id', '?')} "
            f"source={r.get('source', '?')} agent={r.get('agent', '?')} "
            f"processed={r.get('total_issues_processed', 0)}"
        )
    print(f"\n--- {len(receipts)} receipts ---")
    return 0


def cmd_validate(args: "argparse.Namespace") -> int:  # type: ignore[name-defined]
    """Validate all receipts in the log."""
    import sys

    path = _resolve_log_path(args.log)
    if not path.exists():
        print(f"No receipt log found at: {path}")
        return 0

    total = 0
    valid = 0
    errors_count = 0
    with open(path, encoding="utf-8") as fh:
        for line_num, raw_line in enumerate(fh, 1):
            raw_line = raw_line.strip()
            if not raw_line:
                continue
            total += 1
            try:
                receipt = json.loads(raw_line)
            except json.JSONDecodeError as exc:
                print(f"  line {line_num}: parse error: {exc}", file=sys.stderr)
                errors_count += 1
                continue

            is_valid, errors = validate_receipt(receipt)
            if is_valid:
                valid += 1
            else:
                errors_count += 1
                for err in errors:
                    print(f"  line {line_num}: {err}", file=sys.stderr)

    print(f"Validation: {valid} valid, {errors_count} errors, {total} total")
    return 1 if errors_count else 0


def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "create":
        return cmd_create(args)
    if args.command == "list":
        return cmd_list(args)
    if args.command == "validate":
        return cmd_validate(args)

    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
