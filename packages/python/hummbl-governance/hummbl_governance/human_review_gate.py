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

"""Human Review Gate (P53) — GDPR Art. 22(3) mandatory pre-decision checkpoint.

Provides a governance primitive that pauses agent execution at any point where
a solely-automated decision with legal or similarly significant effects would
otherwise occur, presents the proposed decision to a named human reviewer, and
only permits the agent to proceed on an explicit APPROVED outcome.

Legal basis
-----------
- GDPR Art. 22(3): right to obtain human intervention, express point of view,
  and contest decisions based solely on automated processing.
- GDPR Art. 22(1): a decision is "solely automated" unless meaningful human
  involvement occurred.  This gate provides that involvement.
- AI Act Art. 14: effective human oversight for high-risk AI systems — human
  overseers must be able to monitor, interpret, and override.
- EDPB WP251rev.01: token "rubber-stamp" review does not satisfy Art. 22.
  The reviewer must have authority to override and must exercise it.

Design decisions
----------------
- Wraps ApprovalManager (P37) for persistence, notifications, and expiry.
  HumanReviewGate is a GDPR-specific façade that adds: data-subject linkage,
  Art. 22 statutory mode, solely_automated chain-break semantics, and
  DSAR-searchable JSONL receipts.
- reviewer_id is an opaque string (owner decision Q1 — no P6 dependency).
- Timeout resolves as DENIED, not APPROVED (silence ≠ consent under GDPR).
- Art22Mode.NONE is prohibited — gate raises immediately rather than proceeding
  without a valid Art. 22 exception.
- Receipts are persisted to a JSONL store (one entry per gate event) so that
  DSARHandler (P55) can search by data_subject_id.

Usage
-----
::

    from hummbl_governance import ApprovalManager, HumanReviewGate, Art22Mode

    mgr = ApprovalManager(webhook_url="https://hooks.example.com/review")
    gate = HumanReviewGate(approval_manager=mgr,
                           store_path=Path("/var/governance/gate_receipts.jsonl"))

    receipt = gate.request_review(
        agent_id="credit-scorer-v2",
        data_subject_id="subj-pseudonym-7f3a",
        decision_summary="Deny credit application: score 420 < threshold 550",
        decision_payload={"score": 420, "threshold": 550, "action": "deny"},
        art22_mode=Art22Mode.CONTRACT,
        timeout_seconds=86_400,
    )

    # Blocking wait (synchronous agent loop):
    final = gate.wait_for_gate(receipt.gate_id, timeout=86_400.0)
    if final.outcome != "APPROVED":
        raise RuntimeError("Decision blocked by human reviewer")

    # Poll-based (MCP / async):
    status = gate.check_gate(receipt.gate_id)
    if status.outcome == "APPROVED":
        proceed()

Stdlib-only. Zero third-party dependencies.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import threading
import time
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Literal

from hummbl_governance._types import RiskLevel
from hummbl_governance.approval import ApprovalManager, ApprovalStatus

logger = logging.getLogger(__name__)

# HMAC key for receipt signing — same convention as other primitives.
_RECEIPT_KEY = b"hummbl-governance-receipt-key-v1"

# Default gate timeout: 24 hours.
_DEFAULT_TIMEOUT_SECONDS = 86_400


# ---------------------------------------------------------------------------
# Enums / types
# ---------------------------------------------------------------------------

class Art22Mode:
    """GDPR Article 22(2) exception modes.

    Art22Mode controls which statutory exception permits the solely-automated
    decision to proceed.  NONE indicates no valid exception — the gate will
    raise Art22ModeError immediately.

    Values map directly to GDPR Art. 22(2) sub-paragraphs:
        CONTRACT — Art. 22(2)(a): necessary for contract performance.
        LAW      — Art. 22(2)(b): authorised by Union/Member State law.
        CONSENT  — Art. 22(2)(c): based on explicit consent.
        NONE     — prohibited; gate raises immediately.
    """
    CONTRACT = "contract"   # Art. 22(2)(a)
    LAW      = "law"        # Art. 22(2)(b)
    CONSENT  = "consent"    # Art. 22(2)(c)
    NONE     = "none"       # Prohibited — gate raises immediately

    _VALID = {CONTRACT, LAW, CONSENT, NONE}

    @classmethod
    def validate(cls, mode: str) -> str:
        if mode not in cls._VALID:
            raise ValueError(
                f"Unknown Art22Mode {mode!r}. "
                f"Must be one of: {sorted(cls._VALID)}"
            )
        if mode == cls.NONE:
            raise Art22ModeError(
                "Art22Mode.NONE indicates no valid Art. 22(2) exception. "
                "The gate cannot proceed without a lawful basis. "
                "Provide CONTRACT, LAW, or CONSENT."
            )
        return mode


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------

class HumanReviewGateError(Exception):
    """Base exception for HumanReviewGate failures."""


class Art22ModeError(HumanReviewGateError):
    """Raised when Art22Mode.NONE is supplied — no lawful basis exists."""


class GateNotFoundError(HumanReviewGateError):
    """Raised when a gate_id is not found in the store."""
    def __init__(self, gate_id: str):
        self.gate_id = gate_id
        super().__init__(f"Gate not found: {gate_id}")


class GateAlreadyDecidedError(HumanReviewGateError):
    """Raised when a decision is attempted on an already-terminal gate."""
    def __init__(self, gate_id: str, current_outcome: str):
        self.gate_id = gate_id
        self.current_outcome = current_outcome
        super().__init__(
            f"Gate {gate_id} already decided ({current_outcome})"
        )


# ---------------------------------------------------------------------------
# Receipt dataclass
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class HumanReviewGateReceipt:
    """Signed record of a human review gate event.

    Persisted to the JSONL store on every state transition.  DSAR-searchable
    by data_subject_id.  The solely_automated field implements the Art. 22
    chain-break: it is set to False only when outcome == APPROVED, confirming
    that a human genuinely intervened.

    Attributes:
        gate_id: Unique gate identifier (UUID4).
        approval_request_id: Underlying ApprovalManager request_id.
        agent_id: Agent that requested the review.
        data_subject_id: Pseudonymised reference to the affected data subject.
            Used by DSARHandler (P55) to search gate receipts.
        decision_summary: Human-readable summary of the proposed decision.
        art22_mode: Art. 22(2) exception in effect (CONTRACT/LAW/CONSENT).
        reviewer_id: Identity of the reviewer (opaque string; org-supplied).
            None until a reviewer has decided.
        outcome: Gate outcome — PENDING, APPROVED, DENIED, or TIMEOUT.
        solely_automated: True if the decision was solely automated (no human
            genuinely intervened).  Set to False only on APPROVED.
        reviewer_notes: Free-text notes from the reviewer.
        timestamp_requested: ISO timestamp when gate was opened.
        timestamp_decided: ISO timestamp when reviewer decided (or timeout).
        receipt_hmac: HMAC-SHA256 over canonical gate fields.
    """
    gate_id: str
    approval_request_id: str
    agent_id: str
    data_subject_id: str
    decision_summary: str
    art22_mode: str
    reviewer_id: str | None
    outcome: str   # PENDING | APPROVED | DENIED | TIMEOUT
    solely_automated: bool
    reviewer_notes: str
    timestamp_requested: str
    timestamp_decided: str | None
    receipt_hmac: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "gate_id": self.gate_id,
            "approval_request_id": self.approval_request_id,
            "agent_id": self.agent_id,
            "data_subject_id": self.data_subject_id,
            "decision_summary": self.decision_summary,
            "art22_mode": self.art22_mode,
            "reviewer_id": self.reviewer_id,
            "outcome": self.outcome,
            "solely_automated": self.solely_automated,
            "reviewer_notes": self.reviewer_notes,
            "timestamp_requested": self.timestamp_requested,
            "timestamp_decided": self.timestamp_decided,
            "receipt_hmac": self.receipt_hmac,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "HumanReviewGateReceipt":
        return cls(
            gate_id=data["gate_id"],
            approval_request_id=data["approval_request_id"],
            agent_id=data["agent_id"],
            data_subject_id=data["data_subject_id"],
            decision_summary=data["decision_summary"],
            art22_mode=data["art22_mode"],
            reviewer_id=data.get("reviewer_id"),
            outcome=data["outcome"],
            solely_automated=data["solely_automated"],
            reviewer_notes=data.get("reviewer_notes", ""),
            timestamp_requested=data["timestamp_requested"],
            timestamp_decided=data.get("timestamp_decided"),
            receipt_hmac=data["receipt_hmac"],
        )


# ---------------------------------------------------------------------------
# HMAC helper
# ---------------------------------------------------------------------------

def _sign_gate(gate_id: str, outcome: str, timestamp: str) -> str:
    """Compute HMAC-SHA256 over canonical gate fields."""
    msg = f"{gate_id}:{outcome}:{timestamp}".encode()
    return hmac.new(_RECEIPT_KEY, msg, hashlib.sha256).hexdigest()


# ---------------------------------------------------------------------------
# HumanReviewGate
# ---------------------------------------------------------------------------

class HumanReviewGate:
    """GDPR Art. 22(3) mandatory pre-decision human review checkpoint (P53).

    Wraps ApprovalManager (P37) and adds GDPR-specific semantics:
    - data_subject_id linkage for DSAR search (P55).
    - Art. 22(2) mode declaration (CONTRACT/LAW/CONSENT).
    - solely_automated chain-break: False only on APPROVED.
    - Timeout resolves as DENIED — silence is not consent.
    - All state transitions persisted to a JSONL store.

    Args:
        approval_manager: ApprovalManager instance (P37) for HITL workflow.
        store_path: Path to JSONL file for gate receipts.  Created if absent.
            DSARHandler (P55) reads this file to compile Art. 15 responses.
        audit_log: Optional AuditLog for governance event emission.
        hmac_key: Override HMAC key (bytes).  Defaults to package key.
    """

    def __init__(
        self,
        approval_manager: ApprovalManager,
        store_path: Path | None = None,
        audit_log: Any | None = None,
        hmac_key: bytes = _RECEIPT_KEY,
    ) -> None:
        self._mgr = approval_manager
        self._store_path = store_path
        self._audit_log = audit_log
        self._hmac_key = hmac_key
        self._lock = threading.RLock()
        self._in_memory: dict[str, HumanReviewGateReceipt] = {}

        if store_path is not None:
            store_path.parent.mkdir(parents=True, exist_ok=True)
            self._load_store()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def request_review(
        self,
        agent_id: str,
        data_subject_id: str,
        decision_summary: str,
        decision_payload: dict[str, Any],
        art22_mode: str,
        risk_level: RiskLevel = RiskLevel.HIGH,
        timeout_seconds: float = _DEFAULT_TIMEOUT_SECONDS,
        reviewer_notes: str = "",
    ) -> HumanReviewGateReceipt:
        """Open a new human review gate for a proposed automated decision.

        The calling agent MUST NOT execute the proposed decision until
        wait_for_gate() or check_gate() returns outcome == 'APPROVED'.

        Args:
            agent_id: ID of the agent proposing the decision.
            data_subject_id: Pseudonymised reference to the affected subject.
                Used by DSARHandler for Art. 15 access request compilation.
            decision_summary: Human-readable description of the decision.
            decision_payload: Serialisable dict of the proposed decision data.
            art22_mode: Art. 22(2) exception in effect.  Art22Mode.NONE raises.
            risk_level: Risk tier for ApprovalManager routing.
            timeout_seconds: Seconds before the gate auto-closes as DENIED.
            reviewer_notes: Pre-populated notes for the reviewer (optional).

        Returns:
            HumanReviewGateReceipt with outcome='PENDING'.

        Raises:
            Art22ModeError: If art22_mode is Art22Mode.NONE.
            ValueError: If art22_mode is not a recognised value.
        """
        Art22Mode.validate(art22_mode)

        now = datetime.now(timezone.utc).isoformat()
        gate_id = str(uuid.uuid4())

        # Delegate HITL machinery to ApprovalManager (P37).
        approval_req = self._mgr.request_approval(
            agent_id=agent_id,
            action="human_review_gate",
            action_args=decision_summary[:500],
            risk_level=risk_level,
            justification=(
                f"GDPR Art. 22(3) gate | mode={art22_mode} | "
                f"subject={data_subject_id} | {decision_summary[:200]}"
            ),
            timeout_seconds=timeout_seconds,
            metadata={
                "gate_id": gate_id,
                "data_subject_id": data_subject_id,
                "art22_mode": art22_mode,
                "decision_payload": json.dumps(decision_payload,
                                               separators=(",", ":")),
            },
        )

        receipt = HumanReviewGateReceipt(
            gate_id=gate_id,
            approval_request_id=approval_req.request_id,
            agent_id=agent_id,
            data_subject_id=data_subject_id,
            decision_summary=decision_summary,
            art22_mode=art22_mode,
            reviewer_id=None,
            outcome="PENDING",
            solely_automated=True,  # True until a human actually approves
            reviewer_notes=reviewer_notes,
            timestamp_requested=now,
            timestamp_decided=None,
            receipt_hmac=_sign_gate(gate_id, "PENDING", now),
        )

        with self._lock:
            self._in_memory[gate_id] = receipt
            self._persist(receipt)

        self._emit_audit("gate_opened", receipt)
        logger.info("HumanReviewGate opened gate_id=%s agent=%s subject=%s",
                    gate_id, agent_id, data_subject_id)
        return receipt

    def check_gate(self, gate_id: str) -> HumanReviewGateReceipt:
        """Non-blocking status check for a gate.

        Also resolves expired ApprovalManager requests to TIMEOUT/DENIED.

        Args:
            gate_id: Gate identifier from request_review().

        Returns:
            Current HumanReviewGateReceipt.

        Raises:
            GateNotFoundError: If gate_id is unknown.
        """
        with self._lock:
            receipt = self._in_memory.get(gate_id)
            if receipt is None:
                raise GateNotFoundError(gate_id)
            if receipt.outcome != "PENDING":
                return receipt

        # Sync with ApprovalManager state.
        status = self._mgr.check_status(receipt.approval_request_id)
        ap_status = status.get("status", "PENDING")

        if ap_status == "APPROVED":
            return self._finalise(gate_id, "APPROVED", None, "")
        if ap_status in ("DENIED", "CANCELLED"):
            return self._finalise(gate_id, "DENIED", None, "")
        if ap_status == "EXPIRED":
            return self._finalise(gate_id, "TIMEOUT", None, "")

        return receipt

    def wait_for_gate(
        self,
        gate_id: str,
        timeout: float = _DEFAULT_TIMEOUT_SECONDS,
        poll_interval: float = 1.0,
    ) -> HumanReviewGateReceipt:
        """Block until the gate reaches a terminal outcome or timeout.

        IMPORTANT: timeout here resolves as DENIED, not APPROVED.
        Silence is not consent under GDPR Art. 22.

        Args:
            gate_id: Gate identifier from request_review().
            timeout: Maximum seconds to wait before returning TIMEOUT/DENIED.
            poll_interval: Seconds between ApprovalManager polls.

        Returns:
            Terminal HumanReviewGateReceipt (APPROVED, DENIED, or TIMEOUT).
        """
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            receipt = self.check_gate(gate_id)
            if receipt.outcome != "PENDING":
                return receipt
            time.sleep(poll_interval)

        # Timeout — resolve as DENIED.
        return self._finalise(gate_id, "TIMEOUT", None, "")

    def record_reviewer_decision(
        self,
        gate_id: str,
        reviewer_id: str,
        outcome: Literal["APPROVED", "DENIED"],
        reviewer_notes: str = "",
    ) -> HumanReviewGateReceipt:
        """Record a human reviewer's explicit decision.

        For use by reviewer-facing UIs or webhook handlers that need to
        drive the gate directly rather than via ApprovalManager polling.

        Args:
            gate_id: Gate identifier from request_review().
            reviewer_id: Opaque reviewer identity (org-supplied string).
            outcome: 'APPROVED' or 'DENIED'.
            reviewer_notes: Reviewer's free-text rationale.

        Returns:
            Updated HumanReviewGateReceipt with sole_automated=False if APPROVED.

        Raises:
            GateNotFoundError: If gate_id is unknown.
            GateAlreadyDecidedError: If gate already has a terminal outcome.
            ValueError: If outcome is not APPROVED or DENIED.
        """
        if outcome not in ("APPROVED", "DENIED"):
            raise ValueError(
                f"outcome must be 'APPROVED' or 'DENIED', got {outcome!r}"
            )

        with self._lock:
            current = self._in_memory.get(gate_id)
            if current is None:
                raise GateNotFoundError(gate_id)
            if current.outcome != "PENDING":
                raise GateAlreadyDecidedError(gate_id, current.outcome)

        # Mirror decision into ApprovalManager.
        try:
            if outcome == "APPROVED":
                self._mgr.approve(
                    current.approval_request_id,
                    decided_by=reviewer_id,
                    reason=reviewer_notes or "Approved by reviewer",
                )
            else:
                self._mgr.deny(
                    current.approval_request_id,
                    decided_by=reviewer_id,
                    reason=reviewer_notes or "Denied by reviewer",
                )
        except Exception as exc:
            # Log but don't block — gate state is source of truth.
            logger.warning("ApprovalManager sync failed for gate %s: %s",
                           gate_id, exc)

        return self._finalise(gate_id, outcome, reviewer_id, reviewer_notes)

    def list_by_subject(
        self, data_subject_id: str
    ) -> list[HumanReviewGateReceipt]:
        """Return all gate receipts for a given data subject.

        Used by DSARHandler (P55) to compile Art. 15 access responses.

        Args:
            data_subject_id: Pseudonymised subject reference.

        Returns:
            List of matching receipts (may be empty).
        """
        with self._lock:
            return [
                r for r in self._in_memory.values()
                if r.data_subject_id == data_subject_id
            ]

    def list_pending(self) -> list[HumanReviewGateReceipt]:
        """Return all currently pending gates."""
        with self._lock:
            return [r for r in self._in_memory.values()
                    if r.outcome == "PENDING"]

    def get(self, gate_id: str) -> HumanReviewGateReceipt:
        """Retrieve a gate receipt by gate_id.

        Raises:
            GateNotFoundError: If gate_id is unknown.
        """
        with self._lock:
            receipt = self._in_memory.get(gate_id)
        if receipt is None:
            raise GateNotFoundError(gate_id)
        return receipt

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _finalise(
        self,
        gate_id: str,
        outcome: str,
        reviewer_id: str | None,
        reviewer_notes: str,
    ) -> HumanReviewGateReceipt:
        """Create and persist a terminal receipt for a gate."""
        now = datetime.now(timezone.utc).isoformat()
        with self._lock:
            current = self._in_memory.get(gate_id)
            if current is None:
                raise GateNotFoundError(gate_id)
            if current.outcome != "PENDING":
                # Already decided — return existing receipt idempotently.
                return current

            # solely_automated is False only when a human explicitly approved.
            solely_automated = outcome != "APPROVED"

            updated = HumanReviewGateReceipt(
                gate_id=gate_id,
                approval_request_id=current.approval_request_id,
                agent_id=current.agent_id,
                data_subject_id=current.data_subject_id,
                decision_summary=current.decision_summary,
                art22_mode=current.art22_mode,
                reviewer_id=reviewer_id,
                outcome=outcome,
                solely_automated=solely_automated,
                reviewer_notes=reviewer_notes,
                timestamp_requested=current.timestamp_requested,
                timestamp_decided=now,
                receipt_hmac=self._sign(gate_id, outcome, now),
            )
            self._in_memory[gate_id] = updated
            self._persist(updated)

        self._emit_audit(f"gate_{outcome.lower()}", updated)
        logger.info("HumanReviewGate %s gate_id=%s reviewer=%s",
                    outcome, gate_id, reviewer_id)
        return updated

    def _sign(self, gate_id: str, outcome: str, timestamp: str) -> str:
        msg = f"{gate_id}:{outcome}:{timestamp}".encode()
        return hmac.new(self._hmac_key, msg, hashlib.sha256).hexdigest()

    def _persist(self, receipt: HumanReviewGateReceipt) -> None:
        """Append receipt to the JSONL store (if configured)."""
        if self._store_path is None:
            return
        line = json.dumps(receipt.to_dict(), separators=(",", ":")) + "\n"
        try:
            with open(self._store_path, "a", encoding="utf-8") as fh:
                fh.write(line)
        except OSError as exc:
            logger.error("HumanReviewGate store write failed: %s", exc)

    def _load_store(self) -> None:
        """Populate in-memory state from the JSONL store."""
        if self._store_path is None or not self._store_path.exists():
            return
        try:
            with open(self._store_path, encoding="utf-8") as fh:
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                        receipt = HumanReviewGateReceipt.from_dict(data)
                        # Keep only the latest state per gate_id.
                        self._in_memory[receipt.gate_id] = receipt
                    except (json.JSONDecodeError, KeyError) as exc:
                        logger.warning("Skipping malformed gate record: %s", exc)
        except OSError as exc:
            logger.warning("Could not load gate store %s: %s",
                           self._store_path, exc)

    def _emit_audit(
        self, event_type: str, receipt: HumanReviewGateReceipt
    ) -> None:
        """Emit a governance event to AuditLog if configured."""
        if self._audit_log is None:
            return
        try:
            self._audit_log.append(
                intent_id=receipt.gate_id,
                task_id=receipt.approval_request_id,
                tuple_type="EVIDENCE",
                tuple_data={
                    "event_type": f"human_review_gate.{event_type}",
                    "gate_id": receipt.gate_id,
                    "data_subject_id": receipt.data_subject_id,
                    "art22_mode": receipt.art22_mode,
                    "outcome": receipt.outcome,
                    "solely_automated": receipt.solely_automated,
                },
                signature=receipt.receipt_hmac,
            )
        except Exception as exc:
            logger.warning("AuditLog emit failed for gate %s: %s",
                           receipt.gate_id, exc)


__all__ = [
    "Art22Mode",
    "Art22ModeError",
    "GateAlreadyDecidedError",
    "GateNotFoundError",
    "HumanReviewGate",
    "HumanReviewGateError",
    "HumanReviewGateReceipt",
]
