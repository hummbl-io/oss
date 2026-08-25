from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Any, Dict

from .base import IDPTuple


@dataclass(frozen=True, slots=True, kw_only=True)
class ContractTuple(IDPTuple):
    """Specifies objective acceptance criteria for a delegated task.

    Schema: contract.schema.json
    Required tuple_data: objective, allowed_tools, outputs, risk_tier
    """

    objective: str = ""
    allowed_tools: List[str] = field(default_factory=list)
    outputs: List[str] = field(default_factory=list)
    risk_tier: str = ""
    contract_id: Optional[str] = None
    delegatee: Optional[str] = None
    denied_tools: Optional[List[str]] = None
    inputs: Optional[List[str]] = None
    evidence_requirements: Optional[List[str]] = None
    max_subdelegation_depth: Optional[int] = None
    tuple_type: str = "CONTRACT"


@dataclass(frozen=True, slots=True, kw_only=True)
class DCTTuple(IDPTuple):
    """Delegation Capability Token: grants specific capabilities.

    Schema: dct.schema.json
    Required tuple_data: issuer, subject, ops_allowed
    """

    issuer: str = ""
    subject: str = ""
    ops_allowed: List[str] = field(default_factory=list)
    event: Optional[str] = None
    token_id: Optional[str] = None
    tuple_type: str = "DCT"


@dataclass(frozen=True, slots=True, kw_only=True)
class DCTXTuple(IDPTuple):
    """Delegation Context: full context of a delegation event.

    Schema: dctx.schema.json
    Required tuple_data: event
    """

    event: str = ""
    status: Optional[str] = None
    parent_task_id: Optional[str] = None
    chain_depth: Optional[int] = None
    adapter: Optional[str] = None
    tuple_type: str = "DCTX"


@dataclass(frozen=True, slots=True, kw_only=True)
class PromotionReceiptTuple(IDPTuple):
    """Governed promotion decision across environments or trust/compute rungs.

    Schema: promotion_receipt.schema.json
    Required tuple_data: candidate_id, rung_from, rung_to, decision,
    decided_by, policy_version
    """

    candidate_id: str = ""
    rung_from: str = ""
    rung_to: str = ""
    decision: str = ""
    decided_by: str = ""
    policy_version: str = ""
    reason_codes: List[str] = field(default_factory=list)
    artifact_manifest: Dict[str, str] = field(default_factory=dict)
    rollback_reference: Optional[str] = None
    tuple_type: str = "PROMOTION_RECEIPT"


@dataclass(frozen=True, slots=True, kw_only=True)
class RevocationTuple(IDPTuple):
    """Explicit withdrawal of delegated authority.

    Schema: revocation.schema.json
    Required tuple_data: token_id, subject, revoked_by, reason
    """

    token_id: str = ""
    subject: str = ""
    revoked_by: str = ""
    reason: str = ""
    cascade: bool = False
    terminal_state: str = "REVOKED"
    replacement_token_hash: Optional[str] = None
    tuple_type: str = "REVOCATION"


@dataclass(frozen=True, slots=True, kw_only=True)
class EvidenceTuple(IDPTuple):
    """Execution proof artifacts produced during task execution.

    Schema: evidence.schema.json
    Required tuple_data: event
    """

    event: str = ""
    evidence_id: Optional[str] = None
    duration_s: Optional[float] = None
    warnings_count: Optional[int] = None
    agents_ready: Optional[bool] = None
    budget_exceeded: Optional[bool] = None
    tuple_type: str = "EVIDENCE"


@dataclass(frozen=True, slots=True, kw_only=True)
class AttestTuple(IDPTuple):
    """Records the outcome of verifying a task against its contract.

    Schema: attest.schema.json
    Required tuple_data: event, evidence_hash, verifier_id, passed
    """

    event: str = ""
    evidence_hash: str = ""
    verifier_id: str = ""
    passed: bool = False
    findings: Optional[List[str]] = None
    tuple_type: str = "ATTEST"


@dataclass(frozen=True, slots=True, kw_only=True)
class SystemTuple(IDPTuple):
    """Meta-level system state or configuration changes.

    Schema: system.schema.json
    Required tuple_data: event
    """

    event: str = ""
    adapter: Optional[str] = None
    enforcement: Optional[str] = None
    error: Optional[str] = None
    required_capability: Optional[str] = None
    ops_allowed: Optional[List[str]] = None
    tuple_type: str = "SYSTEM"
