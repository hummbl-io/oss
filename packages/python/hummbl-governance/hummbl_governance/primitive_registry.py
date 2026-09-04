"""Primitive Registry — runtime-queryable inventory of governance primitives.

Implements organizational pattern O7 (Registry-Based Organization) from the
2026-09-02 assessment. The registry is the authoritative runtime inventory
of all HUMMBL governance primitives, their categories, enforced invariants,
module paths, status, and family codes.

The registry mirrors PRIMITIVES.md in code, making the inventory:
  - Dynamic: queryable at runtime via Python API
  - Versioned: each primitive has a version
  - Discoverable: find primitives by category, invariant, or status
  - Auditable: gap detection (invariants with no enforcing primitive,
    primitives with no enforced invariant)

Usage:
    from hummbl_governance.primitive_registry import PrimitiveRegistry

    reg = PrimitiveRegistry()
    all_primitives = reg.all_primitives()
    k6_enforcers = reg.primitives_for_invariant("K6")
    safety_primitives = reg.primitives_in_category("Safety")
    infra = reg.infrastructure_primitives()

Stdlib-only. Zero third-party dependencies.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class PrimitiveStatus(str, Enum):
    """Lifecycle status of a primitive."""

    IMPLEMENTED = "implemented"
    PROPOSED = "proposed"
    CANDIDATE = "candidate"
    NOT_STARTED = "not_started"


class PrimitiveLayer(str, Enum):
    """Organizational layer (O1 Layered Architecture).

    FOUNDATION: Shared base modules (errors, schema_validator, _types) that
        all layers depend on. Not governance primitives themselves.
    AUTHORITY: Primitives that scope what an agent can do.
    CONTAINMENT: Primitives that bound what happens when things go wrong.
    EVIDENCE: Primitives that prove what actually happened.
    INFRASTRUCTURE: Utility primitives that support the above but do not
        directly enforce an invariant.

    Import direction: FOUNDATION ← AUTHORITY ← CONTAINMENT ← EVIDENCE ← INFRASTRUCTURE
    Higher layers may import from lower layers. FOUNDATION is importable by all.
    """

    FOUNDATION = "foundation"
    AUTHORITY = "authority"
    CONTAINMENT = "containment"
    EVIDENCE = "evidence"
    INFRASTRUCTURE = "infrastructure"


@dataclass(frozen=True)
class PrimitiveEntry:
    """A single primitive in the registry."""

    pid: str
    family_code: str
    name: str
    category: str
    module: str
    enforced_invariants: tuple[str, ...] = field(default_factory=tuple)
    status: PrimitiveStatus = PrimitiveStatus.IMPLEMENTED
    layer: PrimitiveLayer = PrimitiveLayer.INFRASTRUCTURE
    version: str = "1.0.0"
    description: str = ""

    @property
    def is_governance_primitive(self) -> bool:
        """True if this primitive enforces at least one invariant."""
        return len(self.enforced_invariants) > 0

    @property
    def is_infrastructure(self) -> bool:
        """True if this primitive is infrastructure (no invariant enforcement)."""
        return len(self.enforced_invariants) == 0


# Family code mapping (O2 Family-Based Catalog)
_FAMILY_CODES: dict[str, str] = {
    "Governance Kernel": "GK",
    "Safety": "SF",
    "Cost & Budget": "CB",
    "Identity & Auth": "IA",
    "Audit & Compliance": "AC",
    "Reasoning & Contract": "RC",
    "Coordination": "CO",
    "Behavior & Health": "BH",
    "Physical AI": "PA",
    "Execution Assurance": "EA",
    "Error Taxonomy": "ET",
    "Governance Ecology": "GE",
    "Cryptography": "CR",
    "Corpus Integration": "CI",
    "Lifecycle Hygiene": "LH",
    "Concept Layer": "CL",
    "Risk Management": "RM",
}


def _family_code(category: str) -> str:
    """Get the two-letter family code for a category."""
    return _FAMILY_CODES.get(category, "XX")


def _fc(code: str, num: int) -> str:
    """Generate a family-code identifier (e.g., 'SF-1')."""
    return f"{code}-{num}"


# The canonical primitive inventory.
# This mirrors PRIMITIVES.md and is the authoritative runtime source.
# When PRIMITIVES.md is updated, this registry must be updated too.
_PRIMITIVES: list[PrimitiveEntry] = [
    # ── Safety (SF) ──────────────────────────────────────────────
    PrimitiveEntry("P1", _fc("SF", 1), "KillSwitch", "Safety", "kill_switch",
        enforced_invariants=("K12",), layer=PrimitiveLayer.CONTAINMENT,
        description="Emergency halt system with 4 graduated modes"),
    PrimitiveEntry("P2", _fc("SF", 2), "CircuitBreaker", "Safety", "circuit_breaker",
        enforced_invariants=("K12",), layer=PrimitiveLayer.CONTAINMENT,
        description="Automatic failure detection and recovery across 3 states"),
    PrimitiveEntry("P3", _fc("SF", 3), "OutputValidator", "Safety", "output_validator",
        layer=PrimitiveLayer.INFRASTRUCTURE,
        description="Rule-based content validation (PII, injection, blocklists)"),
    PrimitiveEntry("P4", _fc("SF", 4), "CapabilityFence", "Safety", "capability_fence",
        enforced_invariants=("K6",), layer=PrimitiveLayer.CONTAINMENT,
        description="Soft sandbox enforcing capability boundaries per agent role"),

    # ── Cost & Budget (CB) ───────────────────────────────────────
    PrimitiveEntry("P5", _fc("CB", 1), "CostGovernor", "Cost & Budget", "cost_governor",
        enforced_invariants=("K6",), layer=PrimitiveLayer.CONTAINMENT,
        description="Budget tracking with soft/hard caps and ALLOW/WARN/DENY"),

    # ── Identity & Auth (IA) ─────────────────────────────────────
    PrimitiveEntry("P6", _fc("IA", 1), "IdentityRegistry", "Identity & Auth", "identity",
        enforced_invariants=("K3",), layer=PrimitiveLayer.AUTHORITY,
        description="Agent registry with configurable aliases, trust tiers"),
    PrimitiveEntry("P7", _fc("IA", 2), "DelegationTokens", "Identity & Auth", "delegation",
        enforced_invariants=("K6",), layer=PrimitiveLayer.AUTHORITY,
        description="HMAC-SHA256 or Ed25519 signed capability tokens"),
    PrimitiveEntry("P34", _fc("IA", 3), "AuthoritySweeper", "Identity & Auth", "kernel.authority_sweeper",
        enforced_invariants=("K6",), layer=PrimitiveLayer.AUTHORITY,
        description="Sweep validation for expired authority grants"),
    PrimitiveEntry("P36", _fc("IA", 4), "TrustAdjuster", "Identity & Auth", "kernel.trust_adjuster",
        enforced_invariants=("K3",), layer=PrimitiveLayer.AUTHORITY,
        description="Evidence-backed trust-tier reductions"),
    PrimitiveEntry("P48", _fc("IA", 5), "DelegationContext", "Identity & Auth", "delegation_context",
        enforced_invariants=("K6",), layer=PrimitiveLayer.AUTHORITY,
        description="Immutable delegation context with depth and scope attenuation"),

    # ── Audit & Compliance (AC) ──────────────────────────────────
    PrimitiveEntry("P8", _fc("AC", 1), "AuditLog", "Audit & Compliance", "audit_log",
        enforced_invariants=("K1",), layer=PrimitiveLayer.EVIDENCE,
        description="Append-only JSONL governance audit log"),
    PrimitiveEntry("P9", _fc("AC", 2), "ComplianceMapper", "Audit & Compliance", "compliance_mapper",
        layer=PrimitiveLayer.INFRASTRUCTURE,
        description="Map governance traces to SOC2, GDPR, NIST AI RMF, ISO controls"),
    PrimitiveEntry("P10", _fc("AC", 3), "StrideMapper", "Audit & Compliance", "stride_mapper",
        layer=PrimitiveLayer.INFRASTRUCTURE,
        description="Map agent interactions to STRIDE threat categories"),
    PrimitiveEntry("P51", _fc("AC", 4), "TransitionReceipt", "Audit & Compliance", "transition_receipt",
        enforced_invariants=("K1",), layer=PrimitiveLayer.EVIDENCE,
        description="Transition receipts for governed agent/tool execution"),
    PrimitiveEntry("P52", _fc("AC", 5), "ToolAudit", "Audit & Compliance", "tool_audit",
        enforced_invariants=("K1",), layer=PrimitiveLayer.EVIDENCE,
        description="Tool-call audit hook for AI agent integrations"),

    # ── Reasoning & Contract (RC) ────────────────────────────────
    PrimitiveEntry("P11", _fc("RC", 1), "ReasoningEngine", "Reasoning & Contract", "reasoning",
        layer=PrimitiveLayer.INFRASTRUCTURE,
        description="Structured governance reasoning with Base120 mental models"),
    PrimitiveEntry("P12", _fc("RC", 2), "ContractNet", "Reasoning & Contract", "contract_net",
        layer=PrimitiveLayer.INFRASTRUCTURE,
        description="Market-based task allocation protocol (Smith 1980)"),
    PrimitiveEntry("P13", _fc("RC", 3), "SchemaValidator", "Reasoning & Contract", "schema_validator",
        layer=PrimitiveLayer.INFRASTRUCTURE,
        description="Stdlib-only JSON Schema validator (Draft 2020-12 subset)"),
    PrimitiveEntry("P45", _fc("RC", 4), "ContractEnforcement", "Reasoning & Contract", "contract_enforcement",
        enforced_invariants=("K6",), layer=PrimitiveLayer.AUTHORITY,
        description="Cross-repo contract enforcement layer"),
    PrimitiveEntry("P46", _fc("RC", 5), "CrossRepoContract", "Reasoning & Contract", "cross_repo_contract",
        enforced_invariants=("K6",), layer=PrimitiveLayer.AUTHORITY,
        description="Cross-repository contract validation standard (v0.1)"),

    # ── Coordination (CO) ────────────────────────────────────────
    PrimitiveEntry("P14", _fc("CO", 1), "CoordinationBus", "Coordination", "coordination_bus",
        layer=PrimitiveLayer.INFRASTRUCTURE,
        description="Append-only TSV message bus with flock locking and HMAC signing"),
    PrimitiveEntry("P15", _fc("CO", 2), "LamportClock", "Coordination", "lamport_clock",
        enforced_invariants=("K4",), layer=PrimitiveLayer.EVIDENCE,
        description="Hardened logical clock for causal ordering"),
    PrimitiveEntry("P16", _fc("CO", 3), "ConvergenceGuard", "Coordination", "convergence_guard",
        enforced_invariants=("K13",), layer=PrimitiveLayer.CONTAINMENT,
        description="Detect instrumental convergence patterns in agent behavior"),

    # ── Behavior & Health (BH) ───────────────────────────────────
    PrimitiveEntry("P17", _fc("BH", 1), "RewardMonitor", "Behavior & Health", "reward_monitor",
        enforced_invariants=("D4",), layer=PrimitiveLayer.CONTAINMENT,
        description="Behavioral drift and reward gaming detector"),
    PrimitiveEntry("P18", _fc("BH", 2), "HealthProbe", "Behavior & Health", "health_probe",
        layer=PrimitiveLayer.INFRASTRUCTURE,
        description="Composable health probe framework with latency tracking"),
    PrimitiveEntry("P19", _fc("BH", 3), "Lifecycle", "Behavior & Health", "lifecycle",
        layer=PrimitiveLayer.INFRASTRUCTURE,
        description="NIST AI RMF orchestrator composing kill switch, circuit breaker, etc."),

    # ── Physical AI (PA) ─────────────────────────────────────────
    PrimitiveEntry("P20", _fc("PA", 1), "PhysicalGovernor", "Physical AI", "physical_governor",
        enforced_invariants=("K14",), layer=PrimitiveLayer.CONTAINMENT,
        description="Kinematic constraints and pHRI safety modes for physical-AI"),

    # ── Execution Assurance (EA) ─────────────────────────────────
    PrimitiveEntry("P21", _fc("EA", 1), "EAL", "Execution Assurance", "eal",
        layer=PrimitiveLayer.EVIDENCE,
        description="Execution Assurance Layer — Arbiter-verified code quality"),
    PrimitiveEntry("P50", _fc("EA", 2), "MerkleAnchor", "Execution Assurance", "primitives.merkle_anchor",
        enforced_invariants=("K11",), layer=PrimitiveLayer.EVIDENCE,
        description="CT-style Merkle anchoring with signed tree heads"),

    # ── Error Taxonomy (ET) ──────────────────────────────────────
    PrimitiveEntry("P22", _fc("ET", 1), "Errors", "Error Taxonomy", "errors",
        layer=PrimitiveLayer.INFRASTRUCTURE,
        description="HummblError, FailureMode, and fm_to_errors() — typed error taxonomy"),
    PrimitiveEntry("P23", _fc("ET", 2), "FailureModes", "Error Taxonomy", "failure_modes",
        layer=PrimitiveLayer.INFRASTRUCTURE,
        description="Structured failure mode catalog with classification"),
    PrimitiveEntry("P24", _fc("ET", 3), "EvolutionLineage", "Error Taxonomy", "evolution_lineage",
        layer=PrimitiveLayer.INFRASTRUCTURE,
        description="In-memory lineage tracking for eAI variants with drift detection"),

    # ── Governance Kernel (GK) ───────────────────────────────────
    PrimitiveEntry("P25", _fc("GK", 1), "AdmissionControl", "Governance Kernel", "kernel.admission_control",
        enforced_invariants=("D5",), layer=PrimitiveLayer.AUTHORITY,
        description="Bounded admission-control for governed permission of state transitions"),
    PrimitiveEntry("P26", _fc("GK", 2), "ReceiptEngine", "Governance Kernel", "kernel.receipt_engine",
        enforced_invariants=("K1",), layer=PrimitiveLayer.EVIDENCE,
        description="SHA-256 hash-chained receipts with agent-scoped storage"),
    PrimitiveEntry("P27", _fc("GK", 3), "CanonRegistry", "Governance Kernel", "kernel.canon_registry",
        enforced_invariants=("D5",), layer=PrimitiveLayer.AUTHORITY,
        description="Governs promotion from draft to canonical status (6 levels)"),
    PrimitiveEntry("P28", _fc("GK", 4), "Rollback", "Governance Kernel", "kernel.rollback",
        enforced_invariants=("K9",), layer=PrimitiveLayer.CONTAINMENT,
        description="Enforces reversibility: every governed action declares a rollback path"),
    PrimitiveEntry("P29", _fc("GK", 5), "RecoveryVerifier", "Governance Kernel", "kernel.recovery_verifier",
        enforced_invariants=("K10",), layer=PrimitiveLayer.CONTAINMENT,
        description="Gates re-engagement after halt with root-cause verification"),
    PrimitiveEntry("P30", _fc("GK", 6), "ReceiptIntegrityMonitor", "Governance Kernel", "kernel.receipt_integrity_monitor",
        enforced_invariants=("K11",), layer=PrimitiveLayer.EVIDENCE,
        description="Detects receipt sequence gaps, hash chain breaks, retroactive insertion"),
    PrimitiveEntry("P31", _fc("GK", 7), "Contestability", "Governance Kernel", "kernel.contestability",
        enforced_invariants=("D6",), layer=PrimitiveLayer.AUTHORITY,
        description="Allows affected parties to flag AI-mediated decisions for human review"),
    PrimitiveEntry("P38", _fc("GK", 8), "DoctrineAmendment", "Governance Kernel", "kernel.doctrine_amendment",
        enforced_invariants=("D7",), layer=PrimitiveLayer.AUTHORITY,
        description="Governs changes to invariants themselves"),
    PrimitiveEntry("P40", _fc("GK", 9), "DraftSweeper", "Governance Kernel", "kernel.draft_sweeper",
        enforced_invariants=("D5",), status=PrimitiveStatus.NOT_STARTED, layer=PrimitiveLayer.AUTHORITY,
        description="Tracks draft age and flags drafts exceeding max age for review"),

    # ── Governance Ecology (GE) ──────────────────────────────────
    PrimitiveEntry("P37", _fc("GE", 1), "ApprovalManager", "Governance Ecology", "approval",
        enforced_invariants=("D6",), layer=PrimitiveLayer.AUTHORITY,
        description="Human-in-the-loop approval gate with risk tiers"),
    PrimitiveEntry("P32", _fc("GE", 2), "DisputeResolution", "Governance Ecology", "kernel.dispute_resolution",
        status=PrimitiveStatus.NOT_STARTED, layer=PrimitiveLayer.AUTHORITY,
        description="Inter-agent conflict resolution primitive"),
    PrimitiveEntry("P33", _fc("GE", 3), "Succession", "Governance Ecology", "kernel.succession",
        status=PrimitiveStatus.NOT_STARTED, layer=PrimitiveLayer.AUTHORITY,
        description="Authority transfer primitive for governance continuity"),

    # ── Cryptography (CR) ────────────────────────────────────────
    PrimitiveEntry("P44", _fc("CR", 1), "Attest", "Cryptography", "attest",
        enforced_invariants=("K3",), layer=PrimitiveLayer.AUTHORITY,
        description="MCP server identity attestation and policy compliance verification"),
    PrimitiveEntry("P49", _fc("CR", 2), "SovereignCryptosystem", "Cryptography", "sovereign_cryptosystem",
        enforced_invariants=("K3",), layer=PrimitiveLayer.AUTHORITY,
        description="Hardened cryptographic sync router for sovereign key management"),

    # ── Corpus Integration (CI) ──────────────────────────────────
    PrimitiveEntry("P47", _fc("CI", 1), "CorpusAdapter", "Corpus Integration", "corpus_adapter",
        layer=PrimitiveLayer.INFRASTRUCTURE,
        description="Bridges hummbl-governance receipts to unified-framework corpus formats"),

    # ── Candidates (not in P1-P52 total) ─────────────────────────
    PrimitiveEntry("P35", _fc("AC", 6), "RegulatorExport", "Audit & Compliance", "kernel.regulator_export",
        status=PrimitiveStatus.NOT_STARTED, layer=PrimitiveLayer.EVIDENCE,
        description="Produces compliance evidence in regulator-accepted formats"),
    PrimitiveEntry("P39", _fc("BH", 4), "GovernanceFitness", "Behavior & Health", "kernel.governance_fitness",
        enforced_invariants=("K8",), status=PrimitiveStatus.NOT_STARTED, layer=PrimitiveLayer.EVIDENCE,
        description="Evaluates governance pattern effectiveness over time"),
    PrimitiveEntry("P41", _fc("LH", 1), "Retirement", "Lifecycle Hygiene", "kernel.retirement",
        enforced_invariants=("K8",), status=PrimitiveStatus.CANDIDATE, layer=PrimitiveLayer.AUTHORITY,
        description="Governs decommissioning: verify no dependents, archive state"),
    PrimitiveEntry("P42", _fc("CL", 1), "ConceptRegistry", "Concept Layer", "kernel.concept_registry",
        enforced_invariants=("K5",), status=PrimitiveStatus.CANDIDATE, layer=PrimitiveLayer.AUTHORITY,
        description="Governs terminology: ensures terms have canonical definitions"),
    PrimitiveEntry("P43", _fc("RM", 1), "RiskRegister", "Risk Management", "kernel.risk_register",
        status=PrimitiveStatus.CANDIDATE, layer=PrimitiveLayer.INFRASTRUCTURE,
        description="Dedicated risk-register primitive"),
]


class PrimitiveRegistry:
    """Runtime-queryable registry of all HUMMBL governance primitives.

    Implements organizational pattern O7 (Registry-Based Organization).
    The registry is the authoritative runtime inventory — not a static
    document. It enables:
      - Runtime enumeration of available primitives
      - Discovery of primitives by category, invariant, or status
      - Gap detection (invariants with no enforcing primitive)
      - Versioning of individual primitives
    """

    def __init__(self) -> None:
        self._primitives: dict[str, PrimitiveEntry] = {
            p.pid: p for p in _PRIMITIVES
        }
        self._by_family_code: dict[str, PrimitiveEntry] = {
            p.family_code: p for p in _PRIMITIVES
        }

    def all_primitives(self) -> list[PrimitiveEntry]:
        """Return all registered primitives."""
        return list(self._primitives.values())

    def get(self, pid: str) -> PrimitiveEntry | None:
        """Get a primitive by its P-number (e.g., 'P1')."""
        return self._primitives.get(pid)

    def get_by_family_code(self, family_code: str) -> PrimitiveEntry | None:
        """Get a primitive by its family code (e.g., 'SF-1')."""
        return self._by_family_code.get(family_code)

    def primitives_for_invariant(self, invariant_id: str) -> list[PrimitiveEntry]:
        """Return all primitives that enforce the given invariant.

        Args:
            invariant_id: Invariant ID (e.g., 'K1', 'D6').
        """
        return [
            p for p in self._primitives.values()
            if invariant_id in p.enforced_invariants
        ]

    def primitives_in_category(self, category: str) -> list[PrimitiveEntry]:
        """Return all primitives in the given category."""
        return [
            p for p in self._primitives.values()
            if p.category == category
        ]

    def primitives_in_layer(self, layer: PrimitiveLayer) -> list[PrimitiveEntry]:
        """Return all primitives in the given organizational layer."""
        return [
            p for p in self._primitives.values()
            if p.layer == layer
        ]

    def governance_primitives(self) -> list[PrimitiveEntry]:
        """Return all primitives that enforce at least one invariant."""
        return [p for p in self._primitives.values() if p.is_governance_primitive]

    def infrastructure_primitives(self) -> list[PrimitiveEntry]:
        """Return all infrastructure primitives (no invariant enforcement)."""
        return [p for p in self._primitives.values() if p.is_infrastructure]

    def implemented_primitives(self) -> list[PrimitiveEntry]:
        """Return all implemented primitives."""
        return [
            p for p in self._primitives.values()
            if p.status == PrimitiveStatus.IMPLEMENTED
        ]

    def proposed_primitives(self) -> list[PrimitiveEntry]:
        """Return all proposed but not-yet-started primitives."""
        return [
            p for p in self._primitives.values()
            if p.status == PrimitiveStatus.NOT_STARTED
        ]

    def candidate_primitives(self) -> list[PrimitiveEntry]:
        """Return all candidate primitives under consideration."""
        return [
            p for p in self._primitives.values()
            if p.status == PrimitiveStatus.CANDIDATE
        ]

    def all_invariants(self) -> set[str]:
        """Return the set of all invariant IDs that have at least one enforcer."""
        result: set[str] = set()
        for p in self._primitives.values():
            result.update(p.enforced_invariants)
        return result

    def unpaired_primitives(self) -> list[PrimitiveEntry]:
        """Return primitives with no invariant pairing (infrastructure)."""
        return self.infrastructure_primitives()

    def coverage_report(self) -> dict[str, Any]:
        """Generate a coverage report showing pairing gaps.

        Returns a dict with:
          - total_primitives: count of all primitives
          - governance_primitives: count of primitives with invariant pairing
          - infrastructure_primitives: count without pairing
          - pairing_coverage: percentage with pairing
          - invariants_enforced: set of invariant IDs with at least one enforcer
          - all_kernel_invariants: K1-K14
          - all_doctrine_invariants: D1-D7
          - uncovered_invariants: invariants with no enforcing primitive
        """
        all_k = {f"K{i}" for i in range(1, 15)}
        all_d = {f"D{i}" for i in range(1, 8)}
        enforced = self.all_invariants()
        uncovered = (all_k | all_d) - enforced
        total = len(self._primitives)
        gov = len(self.governance_primitives())
        return {
            "total_primitives": total,
            "governance_primitives": gov,
            "infrastructure_primitives": total - gov,
            "pairing_coverage": round(gov / total * 100, 1) if total else 0,
            "invariants_enforced": sorted(enforced),
            "all_kernel_invariants": sorted(all_k),
            "all_doctrine_invariants": sorted(all_d),
            "uncovered_invariants": sorted(uncovered),
        }

    def categories(self) -> dict[str, int]:
        """Return a mapping of category name to primitive count."""
        counts: dict[str, int] = {}
        for p in self._primitives.values():
            counts[p.category] = counts.get(p.category, 0) + 1
        return dict(sorted(counts.items()))

    def family_codes(self) -> dict[str, str]:
        """Return the family code mapping."""
        return dict(_FAMILY_CODES)

    def __len__(self) -> int:
        return len(self._primitives)

    def __contains__(self, pid: str) -> bool:
        return pid in self._primitives


__all__ = [
    "PrimitiveRegistry",
    "PrimitiveEntry",
    "PrimitiveStatus",
    "PrimitiveLayer",
]
