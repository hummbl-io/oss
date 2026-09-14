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

"""Internal type definitions for hummbl-governance.

Vendored from hummbl-library to eliminate the supply-chain risk of
fallback imports.  All types here are stdlib-only and frozen.

This module is not part of the public API;  consumers should import
types from the sub-modules that expose them (e.g.
``from hummbl_governance import KillSwitchMode``).
"""

from __future__ import annotations

import hashlib
import hmac
import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum, auto
from typing import Any, Literal


# ---------------------------------------------------------------------------
# Kill switch
# ---------------------------------------------------------------------------

class KillSwitchMode(Enum):
    """Kill switch engagement modes."""

    DISENGAGED = auto()
    HALT_NONCRITICAL = auto()
    HALT_ALL = auto()
    EMERGENCY = auto()


class KillSwitchReason(Enum):
    """Machine-actionable failure classification for kill switch engagement.

    Per Ashby's Law of Requisite Variety: the regulator's variety must match
    the system's variety. The kill switch's 4 modes (~3 bits) cannot
    distinguish 15+ failure classes (~4 bits) without this dimension.

    Phase 1 (this enum): machine-actionable reasons replace free-text.
    Phase 2: ``check_task_allowed`` branches on ``(mode, failure_class, is_critical)``.
    Phase 3: per-class circuit breakers consult ``failure_modes.py`` (FM1-FM30).
    """

    BUDGET = "budget"
    BUDGET_CREEP = "budget_creep"
    CAPABILITY_MISUSE = "capability_misuse"
    IDENTITY = "identity"
    DRIFT = "drift"
    INJECTION = "injection"
    EXFIL = "exfiltration"
    REGRESSION = "regression"
    DEPENDENCY = "dependency"
    LEGAL = "legal"
    OPERATOR = "operator"
    DEGRADATION = "degradation"
    TAMPER = "tamper"
    RUNAWAY = "runaway"
    KERNEL_VIOLATION = "kernel_violation"


# ---------------------------------------------------------------------------
# Circuit breaker
# ---------------------------------------------------------------------------

class CircuitBreakerState(Enum):
    """Circuit breaker states."""

    CLOSED = auto()
    OPEN = auto()
    HALF_OPEN = auto()


# ---------------------------------------------------------------------------
# Coordination bus
# ---------------------------------------------------------------------------

class PolicyLevel(Enum):
    """Security policy levels for bus message validation.

    Levels are ordered by strictness: PERMISSIVE < WARN < STRICT.
    """

    PERMISSIVE = 1  # Accept all messages, no validation
    WARN = 2  # Accept all, log warnings for unsigned
    STRICT = 3  # Reject unsigned messages

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, PolicyLevel):
            return NotImplemented
        return self.value < other.value

    def __le__(self, other: object) -> bool:
        if not isinstance(other, PolicyLevel):
            return NotImplemented
        return self.value <= other.value

    def __gt__(self, other: object) -> bool:
        if not isinstance(other, PolicyLevel):
            return NotImplemented
        return self.value > other.value

    def __ge__(self, other: object) -> bool:
        if not isinstance(other, PolicyLevel):
            return NotImplemented
        return self.value >= other.value


# ---------------------------------------------------------------------------
# HITL approvals (human-in-the-loop)
# ---------------------------------------------------------------------------

class ApprovalStatus(Enum):
    """Approval request lifecycle states."""

    PENDING = auto()
    APPROVED = auto()
    DENIED = auto()
    EXPIRED = auto()
    CANCELLED = auto()


class RiskLevel(Enum):
    """Risk classification driving approval requirements."""

    LOW = auto()
    MEDIUM = auto()
    HIGH = auto()
    CRITICAL = auto()


@dataclass
class ApprovalRequest:
    """A human-in-the-loop approval request for an agent action.

    Attributes:
        request_id: Unique identifier (UUID).
        agent_id: Agent requesting approval.
        action: Action/tool name requiring approval.
        action_args: Summary of arguments (redacted, human-readable).
        risk_level: Risk classification.
        justification: Agent's stated reason for the action.
        created_at: ISO timestamp.
        expires_at: ISO timestamp (None = no expiry).
        status: Current lifecycle state.
        decided_by: Reviewer identity (None until decided).
        decided_at: ISO timestamp of decision (None until decided).
        decision_reason: Reviewer's reason for approve/deny.
        notification_channels: List of channels notified.
        metadata: Extra context (task_id, contract_id, etc.).
    """

    request_id: str
    agent_id: str
    action: str
    action_args: str
    risk_level: RiskLevel
    justification: str
    created_at: str
    expires_at: str | None
    status: ApprovalStatus = ApprovalStatus.PENDING
    decided_by: str | None = None
    decided_at: str | None = None
    decision_reason: str | None = None
    notification_channels: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def is_terminal(self) -> bool:
        """True if the request has reached a final state."""
        return self.status in (
            ApprovalStatus.APPROVED,
            ApprovalStatus.DENIED,
            ApprovalStatus.EXPIRED,
            ApprovalStatus.CANCELLED,
        )

    @property
    def is_pending(self) -> bool:
        """True if the request is still awaiting a decision."""
        return self.status == ApprovalStatus.PENDING

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a JSON-compatible dict."""
        return {
            "request_id": self.request_id,
            "agent_id": self.agent_id,
            "action": self.action,
            "action_args": self.action_args,
            "risk_level": self.risk_level.name,
            "justification": self.justification,
            "created_at": self.created_at,
            "expires_at": self.expires_at,
            "status": self.status.name,
            "decided_by": self.decided_by,
            "decided_at": self.decided_at,
            "decision_reason": self.decision_reason,
            "notification_channels": list(self.notification_channels),
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ApprovalRequest:
        """Deserialize from a dict (inverse of to_dict)."""
        return cls(
            request_id=data["request_id"],
            agent_id=data["agent_id"],
            action=data["action"],
            action_args=data["action_args"],
            risk_level=RiskLevel[data["risk_level"]],
            justification=data["justification"],
            created_at=data["created_at"],
            expires_at=data.get("expires_at"),
            status=ApprovalStatus[data["status"]],
            decided_by=data.get("decided_by"),
            decided_at=data.get("decided_at"),
            decision_reason=data.get("decision_reason"),
            notification_channels=list(data.get("notification_channels", [])),
            metadata=dict(data.get("metadata", {})),
        )


# ---------------------------------------------------------------------------
# Audit log
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class AuditEntry:
    """Single entry in the governance audit log."""

    timestamp: str
    entry_id: str
    intent_id: str
    task_id: str
    tuple_type: str
    tuple_data: dict[str, Any]
    signature: str | None = None
    contract_id: str | None = None
    capability_token_id: str | None = None
    verification_id: str | None = None
    amendment_of: str | None = None

    def to_jsonl(self) -> str:
        """Serialize to JSONL line."""
        data: dict[str, Any] = {
            "timestamp": self.timestamp,
            "entry_id": self.entry_id,
            "intent_id": self.intent_id,
            "task_id": self.task_id,
            "tuple_type": self.tuple_type,
            "tuple_data": self.tuple_data,
            "signature": self.signature,
        }
        if self.contract_id is not None:
            data["contract_id"] = self.contract_id
        if self.capability_token_id is not None:
            data["capability_token_id"] = self.capability_token_id
        if self.verification_id is not None:
            data["verification_id"] = self.verification_id
        if self.amendment_of is not None:
            data["amendment_of"] = self.amendment_of
        return json.dumps(data, sort_keys=True, separators=(",", ":"))

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AuditEntry":
        """Deserialize from dictionary."""
        return cls(
            timestamp=data["timestamp"],
            entry_id=data["entry_id"],
            intent_id=data["intent_id"],
            task_id=data["task_id"],
            tuple_type=data["tuple_type"],
            tuple_data=data["tuple_data"],
            signature=data.get("signature"),
            contract_id=data.get("contract_id"),
            capability_token_id=data.get("capability_token_id"),
            verification_id=data.get("verification_id"),
            amendment_of=data.get("amendment_of"),
        )


# ---------------------------------------------------------------------------
# Delegation tokens
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ResourceSelector:
    """Resource selector specifying accessible resources."""

    resource_type: str
    resource_id: str = "*"
    constraints: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Caveat:
    """Caveat constraining capability use."""

    caveat_id: str
    type: Literal["TIME_BOUND", "RATE_LIMIT", "APPROVAL_REQUIRED", "AUDIT_REQUIRED"]
    parameters: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class TokenBinding:
    """Binding linking a token to a specific task and contract."""

    task_id: str
    contract_id: str


@dataclass(frozen=True)
class DelegationToken:
    """HMAC-SHA256 or Ed25519 signed delegation capability token.

    Immutable after creation (frozen dataclass). The signing_method field
    indicates which signature scheme was used ("hmac_sha256" or "ed25519")
    and is NOT part of the signed payload (to_dict()).
    """

    token_id: str
    issuer: str
    subject: str
    resource_selectors: tuple[ResourceSelector, ...] = field(default_factory=tuple)
    ops_allowed: tuple[str, ...] = field(default_factory=tuple)
    caveats: tuple[Caveat, ...] = field(default_factory=tuple)
    expiry: str | None = None
    binding: TokenBinding | None = None
    signature: str = ""
    signing_method: str = "hmac_sha256"

    def to_dict(self) -> dict[str, Any]:
        """Serialize token to dictionary (excluding signature for signing)."""
        return {
            "token_id": self.token_id,
            "issuer": self.issuer,
            "subject": self.subject,
            "resource_selectors": [
                {
                    "resource_type": r.resource_type,
                    "resource_id": r.resource_id,
                    "constraints": r.constraints,
                }
                for r in self.resource_selectors
            ],
            "ops_allowed": list(self.ops_allowed),
            "caveats": [
                {"caveat_id": c.caveat_id, "type": c.type, "parameters": c.parameters}
                for c in self.caveats
            ],
            "expiry": self.expiry,
            "binding": (
                {"task_id": self.binding.task_id, "contract_id": self.binding.contract_id}
                if self.binding
                else None
            ),
        }

    def verify_signature(self, secret: bytes) -> bool:
        """Verify HMAC-SHA256 signature matches token content."""
        canonical = json.dumps(self.to_dict(), separators=(",", ":"), sort_keys=True)
        mac = hmac.new(secret, canonical.encode("utf-8"), hashlib.sha256)
        expected = mac.hexdigest()
        return hmac.compare_digest(self.signature, expected)

    def verify_ed25519_signature(self, public_key: bytes) -> bool:
        """Verify Ed25519 signature against a public key.

        Args:
            public_key: Ed25519 public key bytes (32 bytes).

        Returns:
            True if signature is valid.

        Raises:
            ImportError: If the cryptography package is not installed.
        """
        try:
            from cryptography.hazmat.primitives.asymmetric.ed25519 import (
                Ed25519PublicKey,
            )
        except ImportError as exc:
            raise ImportError(
                "Ed25519 verification requires the 'cryptography' package. "
                "Install with: pip install hummbl-governance[primitives]"
            ) from exc
        canonical = json.dumps(self.to_dict(), separators=(",", ":"), sort_keys=True)
        try:
            pub = Ed25519PublicKey.from_public_bytes(public_key)
            pub.verify(
                bytes.fromhex(self.signature),
                canonical.encode("utf-8"),
            )
            return True
        except Exception:
            return False

    def is_expired(self) -> bool:
        """Check if token has expired."""
        if self.expiry is None:
            return False
        try:
            expiry_dt = datetime.fromisoformat(self.expiry.replace("Z", "+00:00"))
            return datetime.now(timezone.utc) > expiry_dt
        except (ValueError, TypeError):
            return True

    def validate_binding(self, task_id: str, contract_id: str, subject: str) -> bool:
        """Validate token is bound to expected task/contract/subject."""
        if self.binding is None:
            return False
        return (
            self.binding.task_id == task_id
            and self.binding.contract_id == contract_id
            and self.subject == subject
        )


# ---------------------------------------------------------------------------
# Cost governor
# ---------------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class UsageRecord:
    """A single API usage record."""

    record_id: str
    timestamp: str
    provider: str
    model: str
    tokens_in: int
    tokens_out: int
    cost: float
    meta: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        provider: str,
        model: str,
        tokens_in: int,
        tokens_out: int,
        cost: float,
        timestamp: datetime | None = None,
        meta: dict[str, Any] | None = None,
    ) -> "UsageRecord":
        """Factory method with auto-generated IDs."""
        ts = timestamp or datetime.now(timezone.utc)
        return cls(
            record_id=f"usage-{uuid.uuid4().hex[:12]}",
            timestamp=ts.isoformat().replace("+00:00", "Z"),
            provider=provider,
            model=model,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            cost=cost,
            meta=meta or {},
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "record_id": self.record_id,
            "timestamp": self.timestamp,
            "provider": self.provider,
            "model": self.model,
            "tokens_in": self.tokens_in,
            "tokens_out": self.tokens_out,
            "cost": self.cost,
            "meta": self.meta,
        }


@dataclass(frozen=True, slots=True)
class BudgetStatus:
    """Budget status report with governance decision."""

    current_spend: float
    soft_cap: float
    hard_cap: float | None
    currency: str
    threshold_percent: float
    decision: str
    rationale: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "current_spend": self.current_spend,
            "soft_cap": self.soft_cap,
            "hard_cap": self.hard_cap,
            "currency": self.currency,
            "threshold_percent": self.threshold_percent,
            "decision": self.decision,
            "rationale": self.rationale,
        }


# ---------------------------------------------------------------------------
# Contestation Handler (P54)
# ---------------------------------------------------------------------------

@dataclass
class ContestationRecord:
    """A data subject's contestation of an automated decision.
    
    Status can change, so this is a standard dataclass (not frozen).
    """
    contestation_id: str
    original_gate_id: str
    data_subject_id: str
    grounds: str
    status: str
    outcome: "str | None"
    resolution_notes: str
    deadline_iso: str
    timestamp_submitted: str
    timestamp_resolved: "str | None"
    resolver_id: "str | None"
    receipt_hmac: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "contestation_id": self.contestation_id,
            "original_gate_id": self.original_gate_id,
            "data_subject_id": self.data_subject_id,
            "grounds": self.grounds,
            "status": self.status,
            "outcome": self.outcome,
            "resolution_notes": self.resolution_notes,
            "deadline_iso": self.deadline_iso,
            "timestamp_submitted": self.timestamp_submitted,
            "timestamp_resolved": self.timestamp_resolved,
            "resolver_id": self.resolver_id,
            "receipt_hmac": self.receipt_hmac,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ContestationRecord":
        return cls(
            contestation_id=data["contestation_id"],
            original_gate_id=data["original_gate_id"],
            data_subject_id=data["data_subject_id"],
            grounds=data["grounds"],
            status=data["status"],
            outcome=data.get("outcome"),
            resolution_notes=data.get("resolution_notes", ""),
            deadline_iso=data["deadline_iso"],
            timestamp_submitted=data["timestamp_submitted"],
            timestamp_resolved=data.get("timestamp_resolved"),
            resolver_id=data.get("resolver_id"),
            receipt_hmac=data["receipt_hmac"],
        )


# ---------------------------------------------------------------------------
# DSAR Handler (P55)
# ---------------------------------------------------------------------------

@dataclass
class DSARRecord:
    """A Data Subject Access Request (Art. 15).
    
    Status can change, so this is a standard dataclass (not frozen).
    """
    dsar_id: str
    data_subject_id: str
    requester_ref: str
    status: str
    deadline_iso: str
    extended: bool
    extension_reason: "str | None"
    request_notes: str
    timestamp_received: str
    timestamp_completed: "str | None"
    response_path: "str | None"
    receipt_hmac: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "dsar_id": self.dsar_id,
            "data_subject_id": self.data_subject_id,
            "requester_ref": self.requester_ref,
            "status": self.status,
            "deadline_iso": self.deadline_iso,
            "extended": self.extended,
            "extension_reason": self.extension_reason,
            "request_notes": self.request_notes,
            "timestamp_received": self.timestamp_received,
            "timestamp_completed": self.timestamp_completed,
            "response_path": self.response_path,
            "receipt_hmac": self.receipt_hmac,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DSARRecord":
        return cls(
            dsar_id=data["dsar_id"],
            data_subject_id=data["data_subject_id"],
            requester_ref=data["requester_ref"],
            status=data["status"],
            deadline_iso=data["deadline_iso"],
            extended=data.get("extended", False),
            extension_reason=data.get("extension_reason"),
            request_notes=data.get("request_notes", ""),
            timestamp_received=data["timestamp_received"],
            timestamp_completed=data.get("timestamp_completed"),
            response_path=data.get("response_path"),
            receipt_hmac=data["receipt_hmac"],
        )


# ---------------------------------------------------------------------------
# Redaction Engine (P56)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class RedactionReceipt:
    redaction_id: str
    data_subject_id: str
    art17_ground: str
    entries_affected: int
    fields_redacted: list[str]
    preserve_for_legal_claims: bool
    operator_id: str
    timestamp: str
    receipt_hmac: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "redaction_id": self.redaction_id,
            "data_subject_id": self.data_subject_id,
            "art17_ground": self.art17_ground,
            "entries_affected": self.entries_affected,
            "fields_redacted": self.fields_redacted,
            "preserve_for_legal_claims": self.preserve_for_legal_claims,
            "operator_id": self.operator_id,
            "timestamp": self.timestamp,
            "receipt_hmac": self.receipt_hmac,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RedactionReceipt":
        return cls(
            redaction_id=data["redaction_id"],
            data_subject_id=data["data_subject_id"],
            art17_ground=data["art17_ground"],
            entries_affected=data["entries_affected"],
            fields_redacted=data["fields_redacted"],
            preserve_for_legal_claims=data["preserve_for_legal_claims"],
            operator_id=data["operator_id"],
            timestamp=data["timestamp"],
            receipt_hmac=data["receipt_hmac"],
        )


# ---------------------------------------------------------------------------
# Records of Processing (P57) — GDPR Art. 30 record
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Art30Record:
    """A GDPR Art. 30 Record of Processing Activities (RoPA).

    Generated by :class:`hummbl_governance.records_of_processing.RecordsOfProcessing`.
    Immutable after creation (frozen dataclass).

    Attributes:
        record_id:                UUID4 identifier for this record.
        generated_at:             ISO 8601 timestamp of generation (UTC).
        role:                     ``'controller'`` or ``'processor'``.
        controller_name:          Legal name of the data controller.
        controller_contact:       Controller representative contact.
        dpo_contact:              Data Protection Officer contact (may be empty).
        processing_purposes:      List of processing purpose descriptions.
        data_subject_categories:  Categories of data subjects.
        personal_data_categories: Categories of personal data processed.
        recipient_categories:     Categories of recipients.
        third_country_transfers:  Transfer records for third-country destinations.
        retention_periods:        Mapping of data category to retention period string.
        security_measures_summary: Summary of technical/organisational safeguards.
        primitive_sources:        Governance primitives that contributed data.
        boundary_disclaimer:      Mandatory legal disclaimer text.
        receipt_hmac:             HMAC-SHA256 fingerprint over key record fields.
        sme_exempt:               True if the Art. 30(5) SME exemption applies.
    """

    record_id: str
    generated_at: str
    role: str
    controller_name: str
    controller_contact: str
    dpo_contact: str
    processing_purposes: list
    data_subject_categories: list
    personal_data_categories: list
    recipient_categories: list
    third_country_transfers: list
    retention_periods: dict
    security_measures_summary: str
    primitive_sources: list
    boundary_disclaimer: str
    receipt_hmac: str
    sme_exempt: bool = False


# ---------------------------------------------------------------------------
# DPIA Generator (P58) — GDPR Art. 35 / AI Act Art. 27
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DPIASection:
    """A single Art. 35(7) statutory DPIA section."""

    title: str
    content: str
    evidence_refs: list  # list[str] — primitive receipt IDs or source names


@dataclass
class DPIADocument:
    """A structured GDPR Art. 35 DPIA document assembled from governance evidence.

    Generated by DPIAGenerator.generate().  Fields are intentionally mutable
    so that the controller's DPO can annotate prior to formal sign-off.
    """

    dpia_id: str              # uuid4
    generated_at: str         # ISO 8601
    system_name: str
    art35_triggers: list      # list[str] — which Art.35(3) conditions triggered
    sections: list            # list[DPIASection] — 4 statutory sections
    fria_addendum: "str | None"   # AI Act Art. 27 FRIA text if requested
    risk_summary: dict        # {critical: n, high: n, medium: n, low: n, info: n}
    measures_summary: list    # list[str] — safeguards implemented
    boundary_disclaimer: str
    receipt_hmac: str

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a JSON-safe dictionary."""
        return {
            "dpia_id": self.dpia_id,
            "generated_at": self.generated_at,
            "system_name": self.system_name,
            "art35_triggers": self.art35_triggers,
            "sections": [
                {
                    "title": s.title,
                    "content": s.content,
                    "evidence_refs": s.evidence_refs,
                }
                for s in self.sections
            ],
            "fria_addendum": self.fria_addendum,
            "risk_summary": self.risk_summary,
            "measures_summary": self.measures_summary,
            "boundary_disclaimer": self.boundary_disclaimer,
            "receipt_hmac": self.receipt_hmac,
        }

    def to_markdown(self) -> str:
        """Render the DPIA document as a Markdown string."""
        lines: list[str] = []
        lines.append(f"# GDPR Art. 35 DPIA — {self.system_name}")
        lines.append("")
        lines.append(f"**DPIA ID:** `{self.dpia_id}`  ")
        lines.append(f"**Generated:** {self.generated_at}  ")
        lines.append("")

        if self.art35_triggers:
            lines.append("## Art. 35(3) Triggers")
            for trigger in self.art35_triggers:
                lines.append(f"- {trigger}")
            lines.append("")

        for section in self.sections:
            lines.append(f"## {section.title}")
            lines.append("")
            lines.append(section.content)
            lines.append("")
            if section.evidence_refs:
                lines.append("**Evidence references:**")
                for ref in section.evidence_refs:
                    lines.append(f"- {ref}")
                lines.append("")

        lines.append("## Risk Summary")
        lines.append("")
        for level, count in self.risk_summary.items():
            lines.append(f"- {level.capitalize()}: {count}")
        lines.append("")

        lines.append("## Measures Envisaged (Summary)")
        lines.append("")
        for measure in self.measures_summary:
            lines.append(f"- {measure}")
        lines.append("")

        if self.fria_addendum:
            lines.append("## FRIA Addendum (AI Act Art. 27)")
            lines.append("")
            lines.append(self.fria_addendum)
            lines.append("")

        lines.append("---")
        lines.append("")
        lines.append(f"> **Boundary Disclaimer:** {self.boundary_disclaimer}")
        lines.append("")
        lines.append(f"**Receipt HMAC:** `{self.receipt_hmac}`")
        lines.append("")

        return "\n".join(lines)
