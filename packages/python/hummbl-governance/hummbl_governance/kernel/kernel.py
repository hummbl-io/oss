# Copyright 2024-2026 HUMMBL, LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# SPDX-License-Identifier: Apache-2.0

"""Kernel — Main orchestrator for all seven engines.

The Kernel is the operating system of the fleet. It guarantees
invariants K1-K11 through seven specialized engines plus K9-K11
enforcement via rollback, recovery, and integrity primitives.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

from .authority_engine import AuthorityCheck, AuthorityEngine
from .doctrine_engine import DoctrineEngine
from .evidence_engine import EvidenceEngine
from .identity_engine import IdentityEngine
from .invariants import KernelInvariant, KernelPanic
from .law_engine import LawEngine
from .receipt_engine import Receipt, ReceiptEngine
from .receipt_integrity_monitor import raise_on_integrity_violation
from .recovery_verifier import raise_on_recovery_violation
from .rollback import raise_on_rollback_violation
from .schedule_engine import ScheduleEngine
from .sequence_engine import SequenceEngine

# Best-effort corpus adapter import
try:
    from ..corpus_adapter import CorpusAdapter
except ImportError:
    CorpusAdapter = None  # type: ignore[misc,assignment]

logger = logging.getLogger(__name__)

def _default_state_dir() -> Path:
    """Return the default Kernel state directory.

    Resolution order:
    1. HUMMBL_KERNEL_STATE_DIR environment variable
    2. XDG_DATA_HOME/hummbl-governance/kernel (Unix)
    3. ~/.local/share/hummbl-governance/kernel (fallback)
    """
    if env_dir := os.environ.get("HUMMBL_KERNEL_STATE_DIR"):
        return Path(env_dir)
    xdg = os.environ.get("XDG_DATA_HOME")
    if xdg:
        return Path(xdg) / "hummbl-governance" / "kernel"
    return Path.home() / ".local" / "share" / "hummbl-governance" / "kernel"


DEFAULT_STATE_DIR = _default_state_dir()


class Kernel:
    """The Governance Kernel for multi-agent AI systems.

    Usage:
        kernel = Kernel.boot()
        receipt = kernel.receipt.create(agent_id="devin", action_type="STATUS")
        violations = kernel.law.evaluate(receipt.__dict__)
        kernel.receipt.store(receipt)
    """

    def __init__(self, state_dir: Path | None = None) -> None:
        self.state_dir = state_dir or DEFAULT_STATE_DIR
        self.state_dir.mkdir(parents=True, exist_ok=True)

        # Wire corpus adapter if HUMMBL_CORPUS_DIR is set
        corpus_dir = os.environ.get("HUMMBL_CORPUS_DIR")
        corpus_adapter = None
        if corpus_dir and CorpusAdapter is not None:
            try:
                corpus_adapter = CorpusAdapter(
                    corpus_dir=Path(corpus_dir),
                    state_dir=self.state_dir,
                )
            except Exception:
                logger.warning(
                    "Failed to initialize CorpusAdapter for dir %s; continuing without corpus ingestion",
                    corpus_dir,
                    exc_info=True,
                )

        # Initialize all seven engines + doctrine
        self.receipt = ReceiptEngine(self.state_dir, corpus_adapter=corpus_adapter)
        self.law = LawEngine()
        self.identity = IdentityEngine(self.state_dir)
        self.sequence = SequenceEngine(self.state_dir)
        self.evidence = EvidenceEngine()
        self.authority = AuthorityEngine(self.state_dir)
        self.schedule = ScheduleEngine(self.state_dir)
        self.doctrine = DoctrineEngine(self.state_dir)

        self.booted = False
        self.boot_receipt_id: str = ""

    @classmethod
    def boot(cls, state_dir: Path | None = None) -> "Kernel":
        """Boot the Kernel through its 8-phase sequence.

        Returns an initialized and validated Kernel instance.
        Raises KernelPanic if any phase fails.
        """
        kernel = cls(state_dir)
        kernel._boot_sequence()
        return kernel

    def _boot_sequence(self) -> None:
        """Execute the 7-phase Kernel boot sequence."""
        logger.info("KERNEL BOOT: Phase 0 — Hardware/OS check")
        # Phase 0: Basic system check
        if not os.access(self.state_dir, os.W_OK):
            raise KernelPanic(
                KernelInvariant.RECEIPT,
                f"State directory not writable: {self.state_dir}",
            )

        logger.info("KERNEL BOOT: Phase 1 — Identity bootstrap")
        # Phase 1: Verify identity registry
        if not self.identity.registry_file.exists():
            logger.warning("Identity registry not found; creating empty registry")
            self.identity.registry_file.touch()

        logger.info("KERNEL BOOT: Phase 2 — Law bootstrap")
        # Phase 2: Verify scaling law atlas
        if not self.law.laws:
            logger.warning("Scaling Law Atlas not found; operating in degraded mode")

        logger.info("KERNEL BOOT: Phase 3 — Receipt engine init")
        # Phase 3: Verify receipt storage
        self.receipt.receipts_dir.mkdir(parents=True, exist_ok=True)

        logger.info("KERNEL BOOT: Phase 4 — Role registration")
        # Phase 4: Load active roles from identity engine
        for agent_id, identity in self.identity._identities.items():
            for role_id in identity.active_roles:
                logger.info(f"  Registered role {role_id} for {agent_id}")

        logger.info("KERNEL BOOT: Phase 5 — Bus init")
        # Phase 5: Verify bus connectivity (simplified)
        # In full implementation, verify TSV integrity and bridge

        logger.info("KERNEL BOOT: Phase 6 — Loop start")
        # Phase 6: Register default schedules
        # Officer roles will register their own loops

        logger.info("KERNEL BOOT: Phase 7 — Doctrine bootstrap")
        # Phase 7: Verify doctrine engine and promotion graph
        self.doctrine.doctrine_dir.mkdir(parents=True, exist_ok=True)
        logger.info(
            "  Doctrine promotion graph: %s stages, %s valid edges",
            len(self.doctrine._valid_promotions),
            sum(len(v) for v in self.doctrine._valid_promotions.values()),
        )

        logger.info("KERNEL BOOT: Phase 8 — Handoff")
        # Phase 8: Post KERNEL_BOOT receipt
        seq_id = self.sequence.next("kernel")
        receipt = self.receipt.create(
            agent_id="kernel",
            action_type="KERNEL_BOOT",
            payload={
                "phase": 8,
                "laws_loaded": len(self.law.laws),
                "doctrine_stages": len(self.doctrine._valid_promotions),
                "identities_loaded": len(self.identity._identities),
                "schedules_loaded": len(self.schedule._schedules),
            },
            law_checks=["SL-07"],
            sequence_id=seq_id,
        )
        self.boot_receipt_id = self.receipt.store(receipt)
        self.booted = True

        logger.info(f"KERNEL BOOT COMPLETE: receipt={self.boot_receipt_id}")

    def health(self) -> dict[str, Any]:
        """Return Kernel health status."""
        if not self.booted:
            return {"status": "NOT_BOOTED", "healthy": False}

        engine_health = {
            "receipt_engine": True,
            "law_engine": True,  # Engine healthy even if atlas empty (degraded mode)
            "identity_engine": self.identity.registry_file.exists(),
            "sequence_engine": self.sequence.counters_file.exists(),
            "evidence_engine": True,
            "authority_engine": True,  # Engine healthy even if no exercises yet
            "schedule_engine": True,  # Engine healthy even if no schedules yet
        }

        all_healthy = all(engine_health.values())

        return {
            "status": "HEALTHY" if all_healthy else "DEGRADED",
            "healthy": all_healthy,
            "booted": self.booted,
            "boot_receipt_id": self.boot_receipt_id,
            "engines": engine_health,
            "laws_loaded": len(self.law.laws),
            "identities_loaded": len(self.identity._identities),
            "schedules_active": len(self.schedule._schedules),
        }

    def create_receipt(
        self,
        agent_id: str,
        action_type: str,
        payload: dict[str, Any] | None = None,
        law_checks: list[str] | None = None,
        evidence_grade: str = "UNGRADED",
    ) -> Receipt:
        """Create a receipt with automatic sequence_id assignment.

        This is the primary syscall for agent actions.
        """
        if not self.booted:
            raise KernelPanic(
                KernelInvariant.RECEIPT,
                "Kernel not booted; cannot create receipts",
            )

        # K4: Assign sequence_id
        seq_id = self.sequence.next(agent_id)

        # K1: Get previous receipt hash for chain
        last_receipt = self.receipt.last_for_agent(agent_id)
        prev_hash = last_receipt.compute_hash() if last_receipt else ""

        # K5: Grade evidence if claims present
        grade = evidence_grade
        if grade == "UNGRADED" and payload and payload.get("claims"):
            acceptable, reasons = self.evidence.validate_receipt_claims(payload)
            grade = "A" if acceptable else "C"

        receipt = self.receipt.create(
            agent_id=agent_id,
            action_type=action_type,
            payload=payload or {},
            law_checks=law_checks or [],
            evidence_grade=grade,
            prev_receipt_hash=prev_hash,
            sequence_id=seq_id,
        )
        return receipt

    def store_receipt(self, receipt: Receipt) -> str:
        """Store a receipt and evaluate against laws."""
        # K2: Evaluate against laws
        violations = self.law.evaluate(receipt.__dict__)
        if violations:
            logger.warning(
                f"Receipt {receipt.receipt_id} has {len(violations)} law violations"
            )

        receipt_id = self.receipt.store(receipt)

        # Update identity last_receipt_time
        identity = self.identity.resolve(receipt.agent_id)
        if identity:
            identity.last_receipt_time = receipt.timestamp
            self.identity._save_identities()

        return receipt_id

    def check_authority(
        self,
        agent_id: str,
        role_id: str,
        authority: str,
        context: dict[str, Any] | None = None,
    ) -> AuthorityCheck:
        """Check if an agent can exercise an authority."""
        check = self.authority.check(
            agent_id=agent_id,
            role_id=role_id,
            authority=authority,
            context=context or {},
        )
        return check

    def exercise_authority(
        self,
        agent_id: str,
        role_id: str,
        authority: str,
        context: dict[str, Any] | None = None,
    ) -> AuthorityCheck:
        """Exercise an authority with full logging."""
        check = self.check_authority(agent_id, role_id, authority, context)

        # Create receipt for the authority exercise
        receipt = self.create_receipt(
            agent_id=agent_id,
            action_type="AUTHORITY_EXERCISE",
            payload={
                "role_id": role_id,
                "authority": authority,
                "permitted": check.permitted,
                "context": context or {},
            },
            law_checks=["SL-07"],
        )
        receipt_id = self.store_receipt(receipt)

        # Log to authority engine
        self.authority.log_exercise(
            agent_id=agent_id,
            role_id=role_id,
            authority=authority,
            check=check,
            receipt_id=receipt_id,
        )

        return check

    # ── K9-K11 Enforcement ─────────────────────────────────────

    def validate_rollback(self, declaration: dict[str, Any]) -> None:
        """Validate a rollback declaration with K9 enforcement.

        Calls raise_on_rollback_violation() which raises KernelPanic(K9)
        if the declaration fails schema or reversibility validation.

        Args:
            declaration: Rollback declaration dict conforming to
                rollback.schema.json.

        Raises:
            KernelPanic: With invariant=K9 if the declaration is invalid.
        """
        raise_on_rollback_violation(declaration)

    def validate_recovery(self, verification: dict[str, Any]) -> None:
        """Validate a recovery verification record with K10 enforcement.

        Calls raise_on_recovery_violation() which raises KernelPanic(K10)
        if the verification fails schema, root-cause, or operator-approval
        validation.

        Args:
            verification: Recovery verification dict conforming to
                recovery_verifier.schema.json.

        Raises:
            KernelPanic: With invariant=K10 if the verification is invalid.
        """
        raise_on_recovery_violation(verification)

    def check_receipt_integrity(self, agent_id: str) -> dict[str, Any]:
        """Check receipt integrity for an agent with K11 enforcement.

        Loads the agent's receipts from the receipt store and runs
        raise_on_integrity_violation(). Only sequence gaps (K4) and
        hash-chain breaks (K1) raise KernelPanic; timestamp-only
        anomalies are reported as warnings in the returned report.

        Args:
            agent_id: ID of the agent whose receipts are being checked.

        Returns:
            Monitor report dict (if no KernelPanic was raised).

        Raises:
            KernelPanic: With invariant=K11 if sequence gaps or
                hash-chain breaks are detected.
        """
        receipt_file = self.receipt.receipts_dir / f"{agent_id}.jsonl"
        if not receipt_file.exists():
            return {
                "agent_id": agent_id,
                "check_results": {
                    "sequence_check": {"passed": True, "gaps": []},
                    "hash_chain_check": {
                        "passed": True,
                        "chains_verified": 0,
                        "broken_links": [],
                    },
                    "timestamp_check": {
                        "passed": True,
                        "anomalies": [],
                    },
                },
                "panic_triggered": False,
                "panic_details": None,
                "receipt": {"receipt_hash": ""},
            }

        import hashlib
        import json

        receipts: list[dict[str, Any]] = []
        with open(receipt_file, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    receipt_dict = json.loads(line)
                    # Stored receipts don't have a receipt_hash field;
                    # compute it from the canonical form (excluding signature)
                    # so the integrity monitor can verify the hash chain.
                    canonical = dict(receipt_dict)
                    canonical.pop("signature", None)
                    canonical_str = json.dumps(canonical, sort_keys=True, separators=(",", ":"))
                    receipt_dict["receipt_hash"] = hashlib.sha256(
                        canonical_str.encode("utf-8")
                    ).hexdigest()
                    receipts.append(receipt_dict)

        # Adjust for 1-based sequence IDs: SequenceEngine starts at 1,
        # but the integrity monitor's check_sequence expects 0-based.
        # If the first receipt has sequence_id=1, shift all by -1.
        if receipts and receipts[0].get("sequence_id") == 1:
            for r in receipts:
                r["sequence_id"] = r.get("sequence_id", 0) - 1

        return raise_on_integrity_violation(receipts, agent_id)

    def validate_doctrine_amendment(self, amendment: dict[str, Any]) -> None:
        """Validate a doctrine amendment with D7 enforcement.

        Wraps DoctrineEngine.assert_invariant_change_gated() to enforce
        D7 (DOCTRINE_AMENDMENT): no invariant or doctrine amendment may
        take effect without operator approval, evidence, and a recorded
        receipt. Ungated amendments raise KernelPanic.

        Args:
            amendment: A doctrine amendment record dict conforming to
                doctrine_amendment.schema.json. Must have
                authority.operator_approval=True, a non-empty approver_id,
                at least one evidence reference, and a receipt with
                receipt_hash.

        Raises:
            KernelPanic: With invariant=K8 (DOCTRINE) if the amendment
                is ungated or missing required fields.
        """
        self.doctrine.assert_invariant_change_gated(amendment)
