from dataclasses import dataclass, field
from typing import Any
from .base import TypedTuple

@dataclass(frozen=True, slots=True, kw_only=True)
class ContractTuple(TypedTuple):
    """Specifies objective acceptance criteria for a delegated task."""
    task_id: str
    delegator_id: str
    delegatee_id: str
    criteria: list[str]
    timeout_seconds: int
    metadata: dict[str, Any] = field(default_factory=dict)
    tuple_type: str = "CONTRACT"

@dataclass(frozen=True, slots=True, kw_only=True)
class DCTTuple(TypedTuple):
    """Delegation Capability Token: Grants specific capabilities."""
    token_id: str
    issuer: str
    subject: str
    ops_allowed: list[str]
    contract_hash: str  # Reference to CONTRACT hash
    parent_token_hash: str | None = None
    tuple_type: str = "DCT"

@dataclass(frozen=True, slots=True, kw_only=True)
class DCTXTuple(TypedTuple):
    """Delegation Context: Represents the full context of a delegation event."""
    task_id: str
    contract_hash: str
    capability_token_hash: str
    status: str = "PROPOSED"
    parent_task_id: str | None = None
    chain_depth: int = 0
    tuple_type: str = "DCTX"

@dataclass(frozen=True, slots=True, kw_only=True)
class EvidenceTuple(TypedTuple):
    """Contains artifacts produced during task execution."""
    task_id: str
    artifacts: dict[str, str]  # Key: name, Value: hash or URI
    execution_duration: float
    tuple_type: str = "EVIDENCE"

@dataclass(frozen=True, slots=True, kw_only=True)
class AttestTuple(TypedTuple):
    """Records the outcome of verifying a task against its contract."""
    task_id: str
    evidence_hash: str
    verifier_id: str
    passed: bool
    findings: list[str]
    tuple_type: str = "ATTEST"

@dataclass(frozen=True, slots=True, kw_only=True)
class SystemTuple(TypedTuple):
    """Meta-level system state or configuration changes."""
    component: str
    event: str
    config_snapshot: dict[str, Any]
    tuple_type: str = "SYSTEM"
