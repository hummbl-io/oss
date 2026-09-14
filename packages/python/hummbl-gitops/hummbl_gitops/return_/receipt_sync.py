"""B3: Pull CI receipts and verify them.

MVP (loose mode): pull CI receipts from completed runs, store locally,
post RECEIPT_VERIFIED to bus. No cryptographic verification.

Tight mode (requires [governance] extra): import hummbl_governance.kernel
and run the K11 receipt integrity monitor against pulled receipts.

Why the optional dependency:
    K11 (receipt integrity monitor) is the governance kernel primitive that
    proves receipt chains are unbroken and authentic. Without it, receipt sync
    is storage-only (loose). With it, receipt sync is provable (tight). The
    dependency is optional because not every user needs cryptographic receipt
    verification — the loose mode is sufficient for awareness and bus
    notification.

    Install with: pip install hummbl-gitops[governance]
"""

from __future__ import annotations

import json
import os
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class ReceiptSyncResult:
    """Result of a receipt sync operation."""

    repo: str
    receipts_pulled: int = 0
    receipts_verified: int = 0
    mismatches: list[str] = field(default_factory=list)
    tight_mode: bool = False
    verified: bool = True

    def summary(self) -> str:
        lines = [
            f"Receipt sync: {self.repo}",
            f"  Pulled: {self.receipts_pulled}",
            f"  Verified: {self.receipts_verified}",
            f"  Mode: {'tight (K11)' if self.tight_mode else 'loose (storage only)'}",
        ]
        if self.mismatches:
            lines.append(f"  MISMATCHES: {', '.join(self.mismatches)}")
        lines.append(f"  Overall: {'VERIFIED' if self.verified else 'MISMATCH'}")
        return "\n".join(lines)


def sync_receipts(
    repo_path: Path,
    pr_number: Optional[int] = None,
    host: str = "unknown",
    tight: bool = False,
) -> ReceiptSyncResult:
    """Pull CI receipts and optionally verify them.

    Args:
        repo_path: Path to the target repo.
        pr_number: Specific PR to sync. If None, syncs all recent.
        host: Host tag for bus messages.
        tight: If True, verify against K11 (requires [governance] extra).

    Returns:
        ReceiptSyncResult with counts and verification status.
    """
    repo_path = Path(repo_path).resolve()
    result = ReceiptSyncResult(repo=str(repo_path), tight_mode=tight)

    # Receipts are stored in .ci-receipts/ by the ci.py contract runner
    receipts_dir = repo_path / ".ci-receipts"
    if not receipts_dir.exists():
        result.verified = True  # No receipts to verify is not a failure
        return result

    # Collect receipt files
    receipt_files = sorted(receipts_dir.glob("*.json"))
    if pr_number is not None:
        receipt_files = [f for f in receipt_files if f"pr-{pr_number}" in f.name]

    result.receipts_pulled = len(receipt_files)

    if tight:
        try:
            result = _verify_tight(result, receipt_files)
        except ImportError:
            # [governance] extra not installed — fall back to loose
            result.tight_mode = False
            result.receipts_verified = len(receipt_files)
    else:
        # Loose mode: just count them as "verified" (storage-only)
        result.receipts_verified = len(receipt_files)

    return result


def _verify_tight(
    result: ReceiptSyncResult,
    receipt_files: list[Path],
) -> ReceiptSyncResult:
    """Verify receipts against K11 receipt integrity monitor.

    Requires the [governance] extra: pip install hummbl-gitops[governance]

    Raises ImportError if hummbl_governance is not installed.
    """
    from hummbl_governance.kernel import ReceiptIntegrityMonitor  # optional

    monitor = ReceiptIntegrityMonitor()

    for receipt_file in receipt_files:
        try:
            with open(receipt_file) as f:
                receipt_data = json.load(f)

            is_valid = monitor.verify(receipt_data)
            if is_valid:
                result.receipts_verified += 1
            else:
                result.mismatches.append(receipt_file.name)
                result.verified = False
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            result.mismatches.append(f"{receipt_file.name}: {e}")
            result.verified = False

    return result
