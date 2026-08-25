"""Dispatcher pod receipt — structured claim/release lifecycle for dispatch pods.

Each dispatch pod operation (claim, launch, writeback, release) generates a
receipt that is appended to an append-only JSONL log. Receipts are linked via
parent_receipt_hash, creating a tamper-evident chain per pod.

Schema: hummbl_cognition/schemas/dispatcher_pod_receipt.schema.json
Log:     _state/cognition/dispatcher_pod_receipts.jsonl (append-only JSONL)

Design:
  - Pure stdlib (uuid, json, os, hashlib, datetime, pathlib, argparse)
  - Append-only JSONL with platform-appropriate advisory locking
  - CLI: python -m hummbl_cognition.dispatcher_pod_receipt claim --pod-id ... --agent ...
  - Chain validation: verify parent_receipt_hash links and content_hash integrity

Reference: ADR-FM-021 (Dispatcher TDPS Foundation)
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import threading
import uuid
from dataclasses import dataclass, field
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

_SCHEMA_PATH = Path(__file__).parent / "schemas" / "dispatcher_pod_receipt.schema.json"
_DEFAULT_LOG = Path("_state/cognition/dispatcher_pod_receipts.jsonl")
_THREAD_WRITE_LOCK = threading.Lock()

VALID_OPERATIONS = {"claim", "release", "policy_block", "setup_failure", "launch", "writeback"}
VALID_STATUSES = {"complete", "partial", "failed", "blocked"}


@dataclass(frozen=True, slots=True)
class PodReceipt:
    """Immutable dispatcher pod receipt."""
    receipt_id: str
    pod_id: str
    operation: str
    agent: str
    correlation_id: str
    timestamp: str
    content_hash: str
    parent_receipt_hash: str | None = None
    lane_id: str | None = None
    tracker_id: str | None = None
    issue_id: str | None = None
    worktree_path: str | None = None
    worktree_head: str | None = None
    runtime: str | None = None
    process_id: int | None = None
    agent_evidence_ref: str | None = None
    status: str | None = None
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dict for JSON output."""
        d: dict[str, Any] = {
            "receipt_id": self.receipt_id,
            "pod_id": self.pod_id,
            "operation": self.operation,
            "agent": self.agent,
            "correlation_id": self.correlation_id,
            "timestamp": self.timestamp,
            "content_hash": self.content_hash,
            "parent_receipt_hash": self.parent_receipt_hash,
            "lane_id": self.lane_id,
            "tracker_id": self.tracker_id,
            "issue_id": self.issue_id,
            "worktree_path": self.worktree_path,
            "worktree_head": self.worktree_head,
            "runtime": self.runtime,
            "process_id": self.process_id,
            "agent_evidence_ref": self.agent_evidence_ref,
            "status": self.status,
            "notes": self.notes,
        }
        return d


def _canonical_json(data: dict[str, Any]) -> str:
    """Produce canonical JSON for hashing (sorted keys, no whitespace)."""
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _content_hash(receipt: dict[str, Any]) -> str:
    """Compute SHA-256 of the canonical receipt (excluding the hash field)."""
    stripped = {k: v for k, v in receipt.items() if k != "content_hash"}
    return hashlib.sha256(_canonical_json(stripped).encode("utf-8")).hexdigest()


def _utc_now() -> str:
    """Return ISO 8601 UTC timestamp with Z suffix."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def _validate_receipt_structure(receipt: dict[str, Any]) -> list[str]:
    """Validate receipt against required fields and constraints. Returns error list."""
    errors: list[str] = []

    required = {"receipt_id", "pod_id", "operation", "agent", "correlation_id",
                "timestamp", "content_hash"}
    for field_name in required:
        if field_name not in receipt:
            errors.append(f"Missing required field: {field_name}")

    if "operation" in receipt and receipt["operation"] not in VALID_OPERATIONS:
        errors.append(f"Invalid operation: {receipt['operation']}")

    if "status" in receipt and receipt["status"] is not None:
        if receipt["status"] not in VALID_STATUSES:
            errors.append(f"Invalid status: {receipt['status']}")

    if "pod_id" in receipt and not receipt["pod_id"].startswith("pod-"):
        errors.append(f"pod_id must start with 'pod-': {receipt.get('pod_id')}")

    if "content_hash" in receipt:
        expected = _content_hash(receipt)
        if receipt["content_hash"] != expected:
            errors.append(f"content_hash mismatch: expected {expected}, got {receipt['content_hash']}")

    return errors


def create_claim_receipt(
    pod_id: str,
    agent: str,
    correlation_id: str,
    lane_id: str | None = None,
    tracker_id: str | None = None,
    issue_id: str | None = None,
    notes: str = "",
) -> PodReceipt:
    """Create a claim receipt — the first receipt in a pod's chain.

    The claim receipt has no parent_receipt_hash (it starts the chain).
    """
    receipt_id = str(uuid.uuid4())
    timestamp = _utc_now()

    receipt_dict: dict[str, Any] = {
        "receipt_id": receipt_id,
        "pod_id": pod_id,
        "operation": "claim",
        "agent": agent,
        "correlation_id": correlation_id,
        "timestamp": timestamp,
        "parent_receipt_hash": None,
        "lane_id": lane_id,
        "tracker_id": tracker_id,
        "issue_id": issue_id,
        "worktree_path": None,
        "worktree_head": None,
        "runtime": None,
        "process_id": None,
        "agent_evidence_ref": None,
        "status": None,
        "notes": notes,
    }
    receipt_dict["content_hash"] = _content_hash(receipt_dict)

    return PodReceipt(
        receipt_id=receipt_id,
        pod_id=pod_id,
        operation="claim",
        agent=agent,
        correlation_id=correlation_id,
        timestamp=timestamp,
        content_hash=receipt_dict["content_hash"],
        parent_receipt_hash=None,
        lane_id=lane_id,
        tracker_id=tracker_id,
        issue_id=issue_id,
        notes=notes,
    )


def create_receipt(
    pod_id: str,
    operation: str,
    agent: str,
    correlation_id: str,
    parent_receipt_hash: str,
    lane_id: str | None = None,
    tracker_id: str | None = None,
    issue_id: str | None = None,
    worktree_path: str | None = None,
    worktree_head: str | None = None,
    runtime: str | None = None,
    process_id: int | None = None,
    agent_evidence_ref: str | None = None,
    status: str | None = None,
    notes: str = "",
) -> PodReceipt:
    """Create a non-claim receipt (launch, writeback, release, etc.).

    All non-claim receipts must have a parent_receipt_hash linking to the
    previous receipt in the pod's chain.
    """
    if operation == "claim":
        raise ValueError("Use create_claim_receipt() for claim operations")

    receipt_id = str(uuid.uuid4())
    timestamp = _utc_now()

    receipt_dict: dict[str, Any] = {
        "receipt_id": receipt_id,
        "pod_id": pod_id,
        "operation": operation,
        "agent": agent,
        "correlation_id": correlation_id,
        "timestamp": timestamp,
        "parent_receipt_hash": parent_receipt_hash,
        "lane_id": lane_id,
        "tracker_id": tracker_id,
        "issue_id": issue_id,
        "worktree_path": worktree_path,
        "worktree_head": worktree_head,
        "runtime": runtime,
        "process_id": process_id,
        "agent_evidence_ref": agent_evidence_ref,
        "status": status,
        "notes": notes,
    }
    receipt_dict["content_hash"] = _content_hash(receipt_dict)

    return PodReceipt(
        receipt_id=receipt_id,
        pod_id=pod_id,
        operation=operation,
        agent=agent,
        correlation_id=correlation_id,
        timestamp=timestamp,
        content_hash=receipt_dict["content_hash"],
        parent_receipt_hash=parent_receipt_hash,
        lane_id=lane_id,
        tracker_id=tracker_id,
        issue_id=issue_id,
        worktree_path=worktree_path,
        worktree_head=worktree_head,
        runtime=runtime,
        process_id=process_id,
        agent_evidence_ref=agent_evidence_ref,
        status=status,
        notes=notes,
    )


def append_receipt(
    receipt: PodReceipt,
    log_path: Path | None = None,
) -> Path:
    """Append a receipt to the JSONL log with advisory locking.

    Returns the path to the log file written to.
    """
    if log_path is None:
        log_path = _DEFAULT_LOG

    log_path = Path(log_path)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    line = json.dumps(receipt.to_dict(), separators=(",", ":"), ensure_ascii=False)

    with _THREAD_WRITE_LOCK:
        with open(log_path, "a", encoding="utf-8") as f:
            if fcntl is not None:
                try:
                    fcntl.flock(f.fileno(), fcntl.LOCK_EX)
                except OSError:
                    pass
            elif msvcrt is not None:
                try:
                    msvcrt.locking(f.fileno(), msvcrt.LK_LOCK, 1)
                except OSError:
                    pass
            f.write(line + "\n")

    logger.info("Appended pod receipt %s for pod %s (%s)", receipt.receipt_id, receipt.pod_id, receipt.operation)
    return log_path


def read_receipts(log_path: Path | None = None) -> list[dict[str, Any]]:
    """Read all receipts from the JSONL log."""
    if log_path is None:
        log_path = _DEFAULT_LOG
    log_path = Path(log_path)

    if not log_path.exists():
        return []

    receipts: list[dict[str, Any]] = []
    with open(log_path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                receipt = json.loads(line)
                receipts.append(receipt)
            except json.JSONDecodeError as e:
                logger.warning("Invalid JSON at line %d in %s: %s", line_num, log_path, e)
    return receipts


def get_pod_chain(pod_id: str, log_path: Path | None = None) -> list[dict[str, Any]]:
    """Get all receipts for a specific pod, ordered by chain."""
    all_receipts = read_receipts(log_path)
    pod_receipts = [r for r in all_receipts if r.get("pod_id") == pod_id]

    # Sort by chain: claim first, then follow parent_receipt_hash links
    if not pod_receipts:
        return []

    # Find the claim (no parent_receipt_hash)
    claim = None
    for r in pod_receipts:
        if r.get("parent_receipt_hash") is None:
            claim = r
            break

    if claim is None:
        # No claim found — return in timestamp order
        pod_receipts.sort(key=lambda r: r.get("timestamp", ""))
        return pod_receipts

    # Build chain by following parent_receipt_hash
    chain = [claim]
    by_hash = {r.get("content_hash"): r for r in pod_receipts if r.get("content_hash")}
    current_hash = claim.get("content_hash")

    while current_hash:
        next_receipt = None
        for r in pod_receipts:
            if r.get("parent_receipt_hash") == current_hash:
                next_receipt = r
                break
        if next_receipt is None:
            break
        chain.append(next_receipt)
        current_hash = next_receipt.get("content_hash")

    return chain


def validate_chain(pod_id: str, log_path: Path | None = None) -> list[str]:
    """Validate the receipt chain for a pod. Returns list of errors."""
    chain = get_pod_chain(pod_id, log_path)
    if not chain:
        return [f"No receipts found for pod {pod_id}"]

    errors: list[str] = []

    # First receipt must be a claim with no parent
    if chain[0].get("operation") != "claim":
        errors.append("First receipt in chain must be a 'claim' operation")
    if chain[0].get("parent_receipt_hash") is not None:
        errors.append("Claim receipt must have null parent_receipt_hash")

    # Validate each receipt's structure and hash
    for i, receipt in enumerate(chain):
        struct_errors = _validate_receipt_structure(receipt)
        errors.extend(f"Receipt {i}: {e}" for e in struct_errors)

        # Verify chain linkage (except for claim)
        if i > 0:
            expected_parent = chain[i - 1].get("content_hash")
            actual_parent = receipt.get("parent_receipt_hash")
            if actual_parent != expected_parent:
                errors.append(
                    f"Receipt {i}: parent_receipt_hash mismatch: "
                    f"expected {expected_parent}, got {actual_parent}"
                )

    return errors


def is_pod_claimed(pod_id: str, log_path: Path | None = None) -> bool:
    """Check if a pod is currently claimed (claimed but not released)."""
    chain = get_pod_chain(pod_id, log_path)
    if not chain:
        return False

    has_claim = any(r.get("operation") == "claim" for r in chain)
    has_release = any(r.get("operation") == "release" for r in chain)
    return has_claim and not has_release


# --- CLI ---

def _cli() -> None:
    """CLI entry point for dispatcher pod receipt operations."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Dispatcher pod receipt — claim/release lifecycle"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # claim
    claim_p = sub.add_parser("claim", help="Create and append a claim receipt")
    claim_p.add_argument("--pod-id", required=True, help="Pod ID (e.g., pod-issueops-abc123)")
    claim_p.add_argument("--agent", required=True, help="Agent identity")
    claim_p.add_argument("--correlation-id", required=True, help="Correlation ID")
    claim_p.add_argument("--lane-id", help="Lane ID")
    claim_p.add_argument("--tracker-id", help="Tracker ID")
    claim_p.add_argument("--issue-id", help="Issue ID")
    claim_p.add_argument("--notes", default="", help="Notes")
    claim_p.add_argument("--log-path", help="Custom log path")

    # release
    release_p = sub.add_parser("release", help="Create and append a release receipt")
    release_p.add_argument("--pod-id", required=True, help="Pod ID")
    release_p.add_argument("--agent", required=True, help="Agent identity")
    release_p.add_argument("--correlation-id", required=True, help="Correlation ID")
    release_p.add_argument("--status", choices=list(VALID_STATUSES), help="Final status")
    release_p.add_argument("--notes", default="", help="Notes")
    release_p.add_argument("--log-path", help="Custom log path")

    # validate
    validate_p = sub.add_parser("validate", help="Validate a pod's receipt chain")
    validate_p.add_argument("--pod-id", required=True, help="Pod ID to validate")
    validate_p.add_argument("--log-path", help="Custom log path")

    # chain
    chain_p = sub.add_parser("chain", help="Show a pod's receipt chain")
    chain_p.add_argument("--pod-id", required=True, help="Pod ID")
    chain_p.add_argument("--log-path", help="Custom log path")

    # status
    status_p = sub.add_parser("status", help="Check if a pod is claimed")
    status_p.add_argument("--pod-id", required=True, help="Pod ID")
    status_p.add_argument("--log-path", help="Custom log path")

    args = parser.parse_args()
    log_path = Path(args.log_path) if args.log_path else None

    if args.command == "claim":
        receipt = create_claim_receipt(
            pod_id=args.pod_id,
            agent=args.agent,
            correlation_id=args.correlation_id,
            lane_id=args.lane_id,
            tracker_id=args.tracker_id,
            issue_id=args.issue_id,
            notes=args.notes,
        )
        path = append_receipt(receipt, log_path)
        print(json.dumps({"receipt_id": receipt.receipt_id, "content_hash": receipt.content_hash, "log_path": str(path)}, indent=2))

    elif args.command == "release":
        chain = get_pod_chain(args.pod_id, log_path)
        if not chain:
            print(f"Error: No receipts found for pod {args.pod_id}")
            raise SystemExit(1)
        parent_hash = chain[-1].get("content_hash")
        receipt = create_receipt(
            pod_id=args.pod_id,
            operation="release",
            agent=args.agent,
            correlation_id=args.correlation_id,
            parent_receipt_hash=parent_hash,
            status=args.status,
            notes=args.notes,
        )
        path = append_receipt(receipt, log_path)
        print(json.dumps({"receipt_id": receipt.receipt_id, "content_hash": receipt.content_hash, "log_path": str(path)}, indent=2))

    elif args.command == "validate":
        errors = validate_chain(args.pod_id, log_path)
        if errors:
            print(f"INVALID: {len(errors)} errors found:")
            for e in errors:
                print(f"  - {e}")
            raise SystemExit(1)
        else:
            print(f"VALID: Chain for pod {args.pod_id} is intact")

    elif args.command == "chain":
        chain = get_pod_chain(args.pod_id, log_path)
        if not chain:
            print(f"No receipts found for pod {args.pod_id}")
        else:
            for i, r in enumerate(chain):
                print(f"[{i}] {r.get('operation')} @ {r.get('timestamp')}")
                print(f"    receipt_id: {r.get('receipt_id')}")
                print(f"    content_hash: {r.get('content_hash')}")
                if r.get("parent_receipt_hash"):
                    print(f"    parent: {r.get('parent_receipt_hash')}")
                if r.get("status"):
                    print(f"    status: {r.get('status')}")

    elif args.command == "status":
        claimed = is_pod_claimed(args.pod_id, log_path)
        print(f"Pod {args.pod_id}: {'CLAIMED' if claimed else 'NOT CLAIMED'}")


if __name__ == "__main__":
    _cli()
