"""Parallel gate receipt schema and validator.

Deterministic receipt for parallel CI gates. Ensures failure attribution,
log determinism, and artifact isolation.

Key invariants:
  - Receipts are deterministic: same code + same seed = same hash
  - Failures are attributable to file/rule/line
  - Retries are only for transient failures, not deterministic ones
  - Findings are sorted by file, then line (deterministic order)
  - Environment metadata is captured for reproducibility

Related: issue #1117. This receipt primitive does not by itself satisfy that
issue's runner, join, fallback, or serial-versus-parallel trial criteria.
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime
from typing import Any

from hummbl_cognition._json_utils import canonical_json as _canonical_json
from hummbl_cognition._timeutils import utc_now as _utc_now

__all__ = [
    "ParallelGateReceiptError",
    "create_parallel_gate_receipt",
    "validate_parallel_gate_receipt",
    "compute_gate_receipt_hash",
]

VALID_STATUS = {"pass", "fail", "skipped", "error"}
VALID_SEVERITY = {"critical", "high", "medium", "low"}
VALID_BACKOFF = {"exponential", "linear", "fixed", "none"}
ALLOWED_FIELDS = {
    "gate_name", "run_id", "timestamp", "status", "duration_ms",
    "receipt_hash", "deterministic_seed", "findings", "environment",
    "timeout_ms", "retry_count", "retry_backoff",
}


class ParallelGateReceiptError(Exception):
    """Raised when parallel gate receipt validation fails."""


def compute_gate_receipt_hash(receipt: dict[str, Any]) -> str:
    """Compute deterministic SHA-256 excluding volatile timestamp/hash fields."""
    stripped = {
        k: v for k, v in receipt.items()
        if k not in {"receipt_hash", "timestamp"}
    }
    digest = hashlib.sha256(_canonical_json(stripped).encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


def _sort_findings(findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Sort findings by file, then line (deterministic order)."""
    def key(finding: dict[str, Any]) -> tuple[str, int]:
        file_value = finding.get("file")
        line_value = finding.get("line")
        return (
            file_value if isinstance(file_value, str) else "",
            line_value if isinstance(line_value, int) and not isinstance(line_value, bool) else -1,
        )

    return sorted(findings, key=key)


def _valid_timestamp(value: str) -> bool:
    if "T" not in value or not (value.endswith("Z") or re.search(r"[+-]\d\d:\d\d$", value)):
        return False
    try:
        datetime.fromisoformat(value[:-1] + "+00:00" if value.endswith("Z") else value)
        return True
    except ValueError:
        return False


def _valid_relative_path(value: Any) -> bool:
    if not isinstance(value, str) or not value.strip() or "\\" in value:
        return False
    return not value.startswith("/") and all(part != ".." for part in value.split("/"))


def validate_parallel_gate_receipt(receipt: dict[str, Any]) -> tuple[bool, list[str]]:
    """Validate a receipt dict against the parallel gate receipt schema."""
    errors: list[str] = []

    required = [
        "gate_name", "run_id", "timestamp", "status",
        "duration_ms", "receipt_hash", "deterministic_seed",
    ]
    for field in required:
        if field not in receipt or receipt[field] is None:
            errors.append(f"missing required field: {field}")

    unexpected = sorted(set(receipt) - ALLOWED_FIELDS)
    if unexpected:
        errors.append(f"unexpected fields: {unexpected}")

    for field in ("gate_name", "run_id", "timestamp", "status", "receipt_hash", "deterministic_seed"):
        if field in receipt and (not isinstance(receipt[field], str) or not receipt[field].strip()):
            errors.append(f"{field} must be a non-empty string")

    if errors:
        return False, errors

    status = receipt.get("status", "")
    if not isinstance(status, str) or status not in VALID_STATUS:
        errors.append(f"status: {status!r} not in {sorted(VALID_STATUS)}")
    if not _valid_timestamp(receipt["timestamp"]):
        errors.append("timestamp must be an RFC3339 date-time with a timezone")

    # Findings validation
    findings = receipt.get("findings", [])
    if not isinstance(findings, list):
        errors.append("findings must be a list")
        findings = []
    if status == "fail" and not findings:
        errors.append("status='fail' requires at least one attributable finding")
    if findings:
        if status == "pass":
            errors.append("status='pass' must not have findings")
        for i, f in enumerate(findings):
            if not isinstance(f, dict):
                errors.append(f"finding {i}: must be a dict")
                continue
            for req in ("file", "rule", "line", "severity", "message"):
                if req not in f:
                    errors.append(f"finding {i}: missing required field '{req}'")
            if not _valid_relative_path(f.get("file")):
                errors.append(f"finding {i}: file must be a non-empty relative POSIX path")
            for field in ("rule", "message"):
                if not isinstance(f.get(field), str) or not f[field].strip():
                    errors.append(f"finding {i}: {field} must be a non-empty string")
            severity = f.get("severity", "")
            if severity not in VALID_SEVERITY:
                errors.append(f"finding {i}: severity '{severity}' not in {sorted(VALID_SEVERITY)}")
            line = f.get("line", 0)
            if not isinstance(line, int) or isinstance(line, bool) or line < 1:
                errors.append(f"finding {i}: line must be a positive integer")
        sortable_findings = [f for f in findings if isinstance(f, dict)]
        if sortable_findings != _sort_findings(sortable_findings):
            errors.append("findings must be sorted by file, then line")

    # Retry validation
    retry_count = receipt.get("retry_count", 0)
    if not isinstance(retry_count, int) or isinstance(retry_count, bool) or retry_count < 0:
        errors.append("retry_count must be a non-negative integer")

    backoff = receipt.get("retry_backoff", "exponential")
    if not isinstance(backoff, str) or backoff not in VALID_BACKOFF:
        errors.append(f"retry_backoff: {backoff!r} not in {sorted(VALID_BACKOFF)}")

    # Retries on deterministic failures (status=fail) are not allowed
    if status == "fail" and retry_count > 0:
        errors.append(
            "retry_count > 0 is not allowed when status='fail' — "
            "retries are only for transient failures (status='error')"
        )

    # Deterministic seed
    seed = receipt.get("deterministic_seed", "")
    if not seed:
        errors.append("deterministic_seed must be a non-empty string (use 'none' if no randomization)")

    # Duration
    duration = receipt.get("duration_ms", 0)
    if not isinstance(duration, int) or isinstance(duration, bool) or duration < 0:
        errors.append("duration_ms must be a non-negative integer")

    environment = receipt.get("environment")
    if environment is not None:
        if not isinstance(environment, dict):
            errors.append("environment must be an object")
        else:
            unexpected_environment = sorted(
                set(environment) - {"runner", "python_version", "dependencies_hash"}
            )
            if unexpected_environment:
                errors.append(f"environment has unexpected fields: {unexpected_environment}")
            for field in ("runner", "python_version", "dependencies_hash"):
                if field in environment and not isinstance(environment[field], str):
                    errors.append(f"environment.{field} must be a string")
            dependency_hash = environment.get("dependencies_hash")
            if isinstance(dependency_hash, str) and not re.fullmatch(
                r"sha256:[a-f0-9]{64}", dependency_hash
            ):
                errors.append("environment.dependencies_hash must match sha256:<64 lowercase hex>")

    # Hash verification
    expected_hash = compute_gate_receipt_hash(receipt)
    stored_hash = receipt.get("receipt_hash", "")
    if isinstance(stored_hash, str) and not re.fullmatch(r"sha256:[a-f0-9]{64}", stored_hash):
        errors.append("receipt_hash must match sha256:<64 lowercase hex>")
    if receipt.get("receipt_hash") != expected_hash:
        errors.append("receipt_hash does not match computed hash — receipt may be tampered")

    return len(errors) == 0, errors


def create_parallel_gate_receipt(
    *,
    gate_name: str,
    run_id: str,
    status: str,
    duration_ms: int,
    deterministic_seed: str = "none",
    findings: list[dict[str, Any]] | None = None,
    environment: dict[str, Any] | None = None,
    timeout_ms: int = 300000,
    retry_count: int = 0,
    retry_backoff: str = "exponential",
    timestamp: str | None = None,
) -> dict[str, Any]:
    """Construct and validate a parallel gate receipt.

    Args:
        gate_name: Name of the gate (e.g. "security-bandit").
        run_id: Unique run identifier.
        status: Gate status (pass/fail/skipped/error).
        duration_ms: Execution duration in milliseconds.
        deterministic_seed: Seed for randomized operations ("none" if no randomization).
        findings: List of finding dicts (file, rule, line, severity, message).
        environment: Execution environment metadata.
        timeout_ms: Maximum execution time.
        retry_count: Number of retries (0 for no retry).
        retry_backoff: Backoff strategy (exponential/linear/fixed/none).
        timestamp: Optional RFC3339 completion time override for replay tests.

    Returns:
        A validated receipt dict (with receipt_hash appended).

    Raises:
        ParallelGateReceiptError: if validation fails.
    """
    receipt: dict[str, Any] = {
        "gate_name": gate_name,
        "run_id": run_id,
        "timestamp": timestamp or _utc_now(),
        "status": status,
        "duration_ms": duration_ms,
        "deterministic_seed": deterministic_seed,
        "timeout_ms": timeout_ms,
        "retry_count": retry_count,
        "retry_backoff": retry_backoff,
    }

    if findings:
        receipt["findings"] = _sort_findings(findings)
    if environment:
        receipt["environment"] = environment

    receipt["receipt_hash"] = compute_gate_receipt_hash(receipt)

    is_valid, errors = validate_parallel_gate_receipt(receipt)
    if not is_valid:
        raise ParallelGateReceiptError(
            "receipt failed validation: " + "; ".join(errors)
        )

    return receipt
