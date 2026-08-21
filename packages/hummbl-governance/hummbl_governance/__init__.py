"""hummbl-governance -- Governance primitives for AI agent orchestration.

Standalone, stdlib-only Python package providing:
- Kernel: Governance operating system — receipts, identity, roles, laws, evidence, doctrine (v1.2.2)
- KillSwitch: Emergency halt system with graduated response (4 modes)
- CircuitBreaker: Automatic failure detection and recovery (3 states)
- CostGovernor: Budget tracking with soft/hard caps and ALLOW/WARN/DENY decisions
- ApprovalManager: Human-in-the-loop approval gate with risk tiers, notifications, and persistence
- DelegationToken: HMAC-SHA256 signed capability tokens for agent delegation
- AuditLog: Append-only JSONL governance audit log with rotation and retention
- AgentRegistry: Configurable agent identity, aliases, and trust tiers
- SchemaValidator: Stdlib-only JSON Schema validator (Draft 2020-12 subset)
- BusWriter: Append-only TSV coordination bus with flock locking and HMAC signing
- ComplianceMapper: Map governance traces to SOC2, GDPR, OWASP, NIST AI RMF, and EU AI Act controls
- HealthCollector: Composable health probe framework with latency tracking
- OutputValidator: Rule-based content validation for agent outputs (ASI-06)
- CapabilityFence: Soft sandbox enforcing capability boundaries (ASI-07)
- EAL: Execution Assurance Layer — deterministic receipt validation against contracts
- PhysicalGovernor: Safety and kinematic constraints for physical AI (pHRI)
- LamportClock: Hardened logical clock for causal ordering (v0.5.0)
- EvolutionLineage: In-memory lineage tracking for eAI variants

All modules use only Python stdlib. Zero third-party runtime dependencies.

Copyright 2026 HUMMBL, LLC. Licensed under Apache 2.0.
"""

import threading

__version__ = "1.4.0"

# Kernel — Governance operating system (v1.2.2)
from hummbl_governance.kernel import (
    Kernel,
    KernelInvariant,
    KernelPanic,
    Receipt,
    ReceiptEngine,
    LawEngine,
    IdentityEngine,
    SequenceEngine,
    EvidenceEngine,
    AuthorityEngine,
    ScheduleEngine,
    DoctrineEngine,
    Stage,
)

from hummbl_governance.kill_switch import KillSwitch, KillSwitchMode
from hummbl_governance.circuit_breaker import CircuitBreaker, CircuitBreakerState
from hummbl_governance.cost_governor import CostGovernor
from hummbl_governance.approval import (
    ApprovalManager,
    ApprovalError,
    ApprovalExpiredError,
    ApprovalNotFoundError,
    ApprovalAlreadyDecidedError,
)
from hummbl_governance._types import ApprovalStatus, RiskLevel, ApprovalRequest
from hummbl_governance.transition_receipt import (
    ToolTransitionReceipt,
    build_tool_transition_receipt,
    verify_tool_transition_receipt,
)
from hummbl_governance.delegation import DelegationToken, DelegationTokenManager
from hummbl_governance.audit_log import AuditLog
from hummbl_governance.tool_audit import ToolCallAuditor
from hummbl_governance.attest import Attest, AttestResult, ALLOWLIST, BLOCKLIST, CAPABILITY_FENCE
from hummbl_governance.delegation_context import DelegationContext, DelegationContextManager
from hummbl_governance.identity import AgentRegistry, TrustTier
from hummbl_governance.schema_validator import RefRegistry, RefResolutionError, SchemaValidator, ValidationError
from hummbl_governance.contract_enforcement import (
    EnforcementResult,
    build_contract_registry,
    enforce_compatibility_manifest,
    enforce_contract,
    enforce_files,
)
try:
    from hummbl_governance.coordination_bus import BusWriter, PolicyLevel
except ImportError:
    BusWriter = None  # fcntl not available on Windows
    PolicyLevel = None
from hummbl_governance.compliance_mapper import ComplianceMapper, ComplianceReport
from hummbl_governance.health_probe import HealthCollector, HealthProbe, HealthReport, ProbeResult
from hummbl_governance.lamport_clock import LamportClock, LamportTimestamp
from hummbl_governance.stride_mapper import StrideMapper, StrideReport, Interaction, ThreatFinding
from hummbl_governance.lifecycle import GovernanceLifecycle, AuthorizationDecision, GovernanceStatus
from hummbl_governance.contract_net import ContractNetManager, Bid, TaskAnnouncement, ContractPhase
from hummbl_governance.convergence_guard import ConvergenceDetector, ConvergentGoal, ConvergenceAlert
from hummbl_governance.reward_monitor import BehaviorMonitor, DriftReport
from hummbl_governance.output_validator import (
    OutputValidator, PIIDetector, InjectionDetector, LengthBounds, BlocklistFilter,
    JailbreakPatternDetector, SteganographyDetector, EncodingBypassDetector,
)
from hummbl_governance.capability_fence import CapabilityFence, CapabilityDenied
from hummbl_governance.reasoning import ReasoningEngine, ApplyResult
from hummbl_governance.eal import (
    evaluate_validation as eal_validate,
    evaluate_temporal_validation as eal_revalidate,
    evaluate_compat as eal_compat,
)
from hummbl_governance.physical_governor import KinematicGovernor, pHRISafetyMonitor, PhysicalSafetyMode
from hummbl_governance.errors import FailureMode, HummblError, fm_to_errors
from hummbl_governance.failure_modes import (
    FailureModeRecord,
    ErrorRecord,
    all_failure_modes,
    get_fm,
    classify_subclass,
    get_errors_for_fm,
    all_error_records,
)
from hummbl_governance.corpus_adapter import CorpusAdapter
from hummbl_governance.evolution_lineage import (
    EvolutionLineage,
    VariantRecord,
    ModificationRecord,
    EvolutionDriftReport,
)

# Canon Registry (P27) — governs promotion from draft to canonical status
from hummbl_governance.kernel.canon_registry import (
    CanonLevel,
    validate_canon_registry,
    validate_transition,
    validate_operator_approval,
    validate_review_required,
    validate_promotion,
)

# Rollback (P28) — enforces K9 (REVERSIBILITY)
from hummbl_governance.kernel.rollback import (
    validate_rollback,
    validate_reversibility,
    validate_rollback_declaration,
    raise_on_rollback_violation,
)

# Recovery Verifier (P29) — gates re-engagement after halt (K10 RECOVERY)
from hummbl_governance.kernel.recovery_verifier import (
    validate_recovery_verifier,
    validate_root_cause,
    validate_recovery_operator_approval,
    validate_recovery,
    raise_on_recovery_violation,
)

# Receipt Integrity Monitor (P30) — detects receipt sequence gaps, hash chain breaks
from hummbl_governance.kernel.receipt_integrity_monitor import (
    check_sequence,
    check_hash_chain,
    check_timestamps,
    run_integrity_check,
    raise_on_integrity_violation,
    validate_receipt_integrity_monitor,
    validate_monitor_report,
)

# Contestability (P31) — enforces D6 (CONTESTABILITY)
from hummbl_governance.kernel.contestability import (
    ContestStatus,
    ReviewOutcome,
    validate_contestability,
    validate_contest_evidence,
    validate_review_consistency,
    validate_contest,
)

# Doctrine Amendment (P38) — enforces D7 (DOCTRINE_AMENDMENT)
from hummbl_governance.kernel.doctrine_amendment import (
    AmendmentType,
    AmendmentStatus,
    validate_doctrine_amendment,
    validate_operator_approval as validate_amendment_operator_approval,
    validate_amendment_evidence,
    validate_amendment,
)

# Convenience aliases — match code examples shown on hummbl.io
DCT = DelegationTokenManager  # Short alias for DelegationTokenManager
DCTX = DelegationContext  # Short alias for DelegationContext


class _B120Shortcut:
    """Lazy shortcut for Base120 ReasoningEngine access."""

    def __init__(self) -> None:
        self._engine: ReasoningEngine | None = None
        self._lock = threading.Lock()

    def _ensure(self) -> ReasoningEngine:
        if self._engine is None:
            with self._lock:
                if self._engine is None:
                    self._engine = ReasoningEngine()
        return self._engine

    def get(self, key: str):  # type: ignore[no-untyped-def]
        return self._ensure().get_model(key)

    def search(self, query: str, **kwargs):  # type: ignore[no-untyped-def]
        return self._ensure().search(query, **kwargs)

    def __contains__(self, key: object) -> bool:
        return isinstance(key, str) and key in self._ensure()

    def __iter__(self):
        return iter(self._ensure())

    def __len__(self) -> int:
        return len(self._ensure())

    def list(self):  # type: ignore[no-untyped-def]
        return list(self._ensure().models.keys())


b120 = _B120Shortcut()

__all__ = [
    "__version__",
    # Kernel — Governance operating system (v1.2.2)
    "Kernel",
    "KernelInvariant",
    "KernelPanic",
    "Receipt",
    "ReceiptEngine",
    "LawEngine",
    "IdentityEngine",
    "SequenceEngine",
    "EvidenceEngine",
    "AuthorityEngine",
    "ScheduleEngine",
    "DoctrineEngine",
    "Stage",
    "KillSwitch",
    "KillSwitchMode",
    "CircuitBreaker",
    "CircuitBreakerState",
    "CostGovernor",
    "ApprovalManager",
    "ApprovalStatus",
    "RiskLevel",
    "ApprovalRequest",
    "ApprovalError",
    "ApprovalExpiredError",
    "ApprovalNotFoundError",
    "ApprovalAlreadyDecidedError",
    "ToolTransitionReceipt",
    "build_tool_transition_receipt",
    "verify_tool_transition_receipt",
    "DelegationToken",
    "DelegationTokenManager",
    "AuditLog",
    "ToolCallAuditor",
    "AgentRegistry",
    "TrustTier",
    "SchemaValidator",
    "ValidationError",
    "RefRegistry",
    "RefResolutionError",
    "EnforcementResult",
    "build_contract_registry",
    "enforce_compatibility_manifest",
    "enforce_contract",
    "enforce_files",
    "BusWriter",
    "PolicyLevel",
    "ComplianceMapper",
    "ComplianceReport",
    "HealthCollector",
    "HealthProbe",
    "HealthReport",
    "ProbeResult",
    "LamportClock",
    "LamportTimestamp",
    "StrideMapper",
    "StrideReport",
    "Interaction",
    "ThreatFinding",
    "GovernanceLifecycle",
    "AuthorizationDecision",
    "GovernanceStatus",
    "ContractNetManager",
    "Bid",
    "TaskAnnouncement",
    "ContractPhase",
    "ConvergenceDetector",
    "ConvergentGoal",
    "ConvergenceAlert",
    "BehaviorMonitor",
    "DriftReport",
    "OutputValidator",
    "PIIDetector",
    "InjectionDetector",
    "LengthBounds",
    "BlocklistFilter",
    "JailbreakPatternDetector",
    "SteganographyDetector",
    "EncodingBypassDetector",
    "CapabilityFence",
    "CapabilityDenied",
    "ReasoningEngine",
    "ApplyResult",
    "KinematicGovernor",
    "pHRISafetyMonitor",
    "PhysicalSafetyMode",
    # Execution Assurance Layer (v0.4.0)
    "eal_validate",
    "eal_revalidate",
    "eal_compat",
    # Error taxonomy (v0.4.0)
    "FailureMode",
    "HummblError",
    "fm_to_errors",
    "FailureModeRecord",
    "ErrorRecord",
    "all_failure_modes",
    "get_fm",
    "classify_subclass",
    "get_errors_for_fm",
    "all_error_records",
    # eAI governance foundation
    "EvolutionLineage",
    "VariantRecord",
    "ModificationRecord",
    "EvolutionDriftReport",
    "CorpusAdapter",
    # Canon Registry (P27)
    "CanonLevel",
    "validate_canon_registry",
    "validate_transition",
    "validate_operator_approval",
    "validate_review_required",
    "validate_promotion",
    # Rollback (P28)
    "validate_rollback",
    "validate_reversibility",
    "validate_rollback_declaration",
    "raise_on_rollback_violation",
    # Recovery Verifier (P29)
    "validate_recovery_verifier",
    "validate_root_cause",
    "validate_recovery_operator_approval",
    "validate_recovery",
    "raise_on_recovery_violation",
    # Receipt Integrity Monitor (P30)
    "check_sequence",
    "check_hash_chain",
    "check_timestamps",
    "run_integrity_check",
    "raise_on_integrity_violation",
    "validate_receipt_integrity_monitor",
    "validate_monitor_report",
    # Contestability (P31)
    "ContestStatus",
    "ReviewOutcome",
    "validate_contestability",
    "validate_contest_evidence",
    "validate_review_consistency",
    "validate_contest",
    # Doctrine Amendment (P38)
    "AmendmentType",
    "AmendmentStatus",
    "validate_doctrine_amendment",
    "validate_amendment_operator_approval",
    "validate_amendment_evidence",
    "validate_amendment",
    # Attestation (v1.2.2)
    "Attest",
    "AttestResult",
    "ALLOWLIST",
    "BLOCKLIST",
    "CAPABILITY_FENCE",
    # Delegation Context (v1.2.2)
    "DelegationContext",
    "DelegationContextManager",
    # Convenience aliases
    "DCT",
    "DCTX",
    "b120",
]
