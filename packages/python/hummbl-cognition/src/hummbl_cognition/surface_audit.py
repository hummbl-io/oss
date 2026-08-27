"""Governance surface audit log — records GitHub surface actions with authority.

Every agentic action on a GitHub surface (create issue, comment, close, merge, etc.)
generates a receipt that is appended to an append-only JSONL log. This provides
a tamper-evident audit trail of all agent interactions with GitHub.

Schema: hummbl_cognition/schemas/surface_audit_receipt.schema.json
Log:     _state/cognition/surface_audit_receipts.jsonl (append-only JSONL)

Design:
  - Pure stdlib (uuid, json, os, hashlib, datetime, pathlib, argparse)
  - Append-only JSONL with platform-appropriate advisory locking
  - CLI: python -m hummbl_cognition.surface_audit record --surface-id ... --actor ...

Reference: GITHUB_SURFACE_MAP_DOCTRINE.md (receipt fields)
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import threading
import uuid
from pathlib import Path
from typing import Any

from hummbl_cognition._timeutils import utc_now_micros as _utc_now

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
    "SurfaceAuditError",
    "record_action",
    "validate_receipt",
    "append_receipt",
    "read_receipts",
    "DEFAULT_LOG_PATH",
    "VALID_SURFACES",
    "VALID_AUTHORITY_LEVELS",
    "VALID_RESULTS",
]

DEFAULT_LOG_PATH = "_state/cognition/surface_audit_receipts.jsonl"

VALID_SURFACES = [
    "code-ui",
    "issues-ui",
    "prs-ui",
    "actions-ui",
    "projects-ui",
    "security-ui",
    "insights-ui",
    "settings-ui",
    "gh-cli",
    "api",
    "tui",
    "ide",
]

VALID_AUTHORITY_LEVELS = [
    "operator-only",
    "steward",
    "trusted",
    "active",
    "probationary",
    "candidate",
]

VALID_RESULTS = ["success", "failure", "denied", "error"]


class SurfaceAuditError(Exception):
    """Raised when surface audit receipt operations fail."""


def _generate_action_id() -> str:
    return f"surf-{uuid.uuid4().hex[:12]}"


def _compute_content_hash(data: dict[str, Any]) -> str:
    canonical = json.dumps(data, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def record_action(
    surface_id: str,
    actor: str,
    authority_level: str,
    action: str,
    result: str,
    evidence_ref: str = "",
    repo: str = "",
    issue_number: int | None = None,
    pr_number: int | None = None,
    notes: str = "",
) -> dict[str, Any]:
    """Create a surface audit receipt (does not append to log)."""
    if surface_id not in VALID_SURFACES:
        raise SurfaceAuditError(
            f"invalid surface_id: {surface_id}; must be one of {VALID_SURFACES}"
        )
    if authority_level not in VALID_AUTHORITY_LEVELS:
        raise SurfaceAuditError(
            f"invalid authority_level: {authority_level}; must be one of {VALID_AUTHORITY_LEVELS}"
        )
    if result not in VALID_RESULTS:
        raise SurfaceAuditError(
            f"invalid result: {result}; must be one of {VALID_RESULTS}"
        )
    if not actor:
        raise SurfaceAuditError("actor must not be empty")
    if not action:
        raise SurfaceAuditError("action must not be empty")

    receipt: dict[str, Any] = {
        "action_id": _generate_action_id(),
        "timestamp": _utc_now(),
        "surface_id": surface_id,
        "actor": actor,
        "authority_level": authority_level,
        "action": action,
        "result": result,
        "evidence_ref": evidence_ref,
        "repo": repo,
        "notes": notes,
    }
    if issue_number is not None:
        receipt["issue_number"] = issue_number
    if pr_number is not None:
        receipt["pr_number"] = pr_number

    receipt["content_hash"] = _compute_content_hash(
        {k: v for k, v in receipt.items() if k != "content_hash"}
    )
    return receipt


def validate_receipt(receipt: dict[str, Any]) -> bool:
    """Validate a surface audit receipt has all required fields."""
    required = [
        "action_id",
        "timestamp",
        "surface_id",
        "actor",
        "authority_level",
        "action",
        "result",
    ]
    for field_name in required:
        if field_name not in receipt:
            raise SurfaceAuditError(f"missing required field: {field_name}")
    if receipt["surface_id"] not in VALID_SURFACES:
        raise SurfaceAuditError(f"invalid surface_id: {receipt['surface_id']}")
    if receipt["authority_level"] not in VALID_AUTHORITY_LEVELS:
        raise SurfaceAuditError(
            f"invalid authority_level: {receipt['authority_level']}"
        )
    if receipt["result"] not in VALID_RESULTS:
        raise SurfaceAuditError(f"invalid result: {receipt['result']}")
    return True


def append_receipt(
    receipt: dict[str, Any],
    log_path: str | Path = DEFAULT_LOG_PATH,
) -> Path:
    """Append a receipt to the JSONL log with file locking."""
    validate_receipt(receipt)
    path = Path(log_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    line = json.dumps(receipt, sort_keys=True, separators=(",", ":")) + "\n"

    lock = threading.Lock()
    with lock:
        with open(path, "a", encoding="utf-8") as f:
            if fcntl is not None:
                fcntl.flock(f.fileno(), fcntl.LOCK_EX)
            try:
                f.write(line)
                f.flush()
                os.fsync(f.fileno())
            finally:
                if fcntl is not None:
                    fcntl.flock(f.fileno(), fcntl.LOCK_UN)

    logger.info("surface audit receipt appended: %s → %s", receipt["action_id"], path)
    return path


def read_receipts(
    log_path: str | Path = DEFAULT_LOG_PATH,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """Read recent receipts from the JSONL log (newest first)."""
    path = Path(log_path)
    if not path.exists():
        return []

    receipts: list[dict[str, Any]] = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                receipts.append(json.loads(line))
            except json.JSONDecodeError as e:
                logger.warning("corrupt receipt line: %s", e)
                continue

    receipts.reverse()
    return receipts[:limit]
