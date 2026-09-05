"""Delegation Context (DCTX) implementation for IDP v0.1.

This module implements the Delegation Context tuple per IDP specification,
enforcing I3 invariant (Bounded Chain Depth) and state machine transitions.

IDP References:
- IDP_SPEC.md Section 2.1: DCTX tuple schema
- IDP_INVARIANTS.md Section I3: Bounded Chain Depth
- IDP_SPEC.md Section 3: State Machine
"""

from __future__ import annotations

import os
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Literal


# Feature flag
def _is_idp_enabled() -> bool:
    """Check if IDP feature flag is enabled (runtime check)."""
    return os.environ.get("ENABLE_IDP", "true").lower() == "true"


# Error codes per IDP_FAILURE_CODES.md
IDP_E_DEPTH_EXCEEDED = "IDP_E_DEPTH_EXCEEDED"
IDP_E_INVALID_STATE_TRANSITION = "IDP_E_INVALID_STATE_TRANSITION"
IDP_E_REPLAN_LIMIT = "IDP_E_REPLAN_LIMIT"
IDP_E_CAPABILITY_ESCALATION = "IDP_E_CAPABILITY_ESCALATION"
IDP_E_BUDGET_ESCALATION = "IDP_E_BUDGET_ESCALATION"
# G3: Dynamic trust-decay depth exceeded
IDP_E_TRUST_DEPTH_EXCEEDED = "IDP_E_TRUST_DEPTH_EXCEEDED"

# Default constants
DEFAULT_MAX_CHAIN_DEPTH = 3
DEFAULT_MAX_REPLANS = 2

# G3: Trust-decay depth thresholds per risk tier (matches paper formula)
# δ_effective(o, t) = min(δ_max, floor(t_score / τ_o))
# where τ_STANDARD=0.15, τ_ELEVATED=0.25, τ_CRITICAL=0.40
_TAU_BY_RISK_TIER: dict[str, float] = {
    "LOW": 0.15,       # STANDARD equivalent
    "MEDIUM": 0.20,    # Between STANDARD and ELEVATED
    "HIGH": 0.25,      # ELEVATED equivalent
    "CRITICAL": 0.40,
}


def compute_dynamic_depth(trust_score: float, risk_tier: str, delta_max: int = DEFAULT_MAX_CHAIN_DEPTH) -> int:
    """Compute effective delegation depth using trust-decay model (ADR-FM-011 companion).

    Implements the paper formula: δ_effective = min(δ_max, floor(t_score / τ_o))

    Args:
        trust_score: Beta trust score τ in [0.0, 1.0]
        risk_tier: One of LOW, MEDIUM, HIGH, CRITICAL
        delta_max: Hard ceiling (default 3)

    Returns:
        Maximum permitted chain depth for this delegatee and operation class.
        Returns 0 for trust_score outside [0.0, 1.0] or unknown risk_tier
        (fail-closed).
    """
    if not isinstance(trust_score, (int, float)) or trust_score < 0.0 or trust_score > 1.0:
        return 0
    if delta_max < 0:
        return 0
    # Fail-closed: unknown risk tier defaults to CRITICAL (most restrictive)
    # rather than LOW (most permissive). An unknown tier means we don't know
    # the risk level, so we must assume the worst.
    tau = _TAU_BY_RISK_TIER.get(risk_tier)
    if tau is None:
        return 0
    return min(delta_max, int(trust_score // tau))


DCTXStatus = Literal[
    "PROPOSED",  # Task proposed but not issued
    "ISSUED",  # CONTRACT and DCT created
    "RUNNING",  # Delegatee executing
    "EVIDENCE_READY",  # Execution complete
    "VERIFIED",  # ATTEST created with PASS
    "REPLANNED",  # Failed, explicit replan decision
    "FAILED",  # Failed and cannot replan
]


@dataclass
class DelegationBudget:
    """Budget constraints for delegation.

    Matches IDP_SPEC.md DCTX.budget schema.
    Tracks allocated resources to prevent subtree budget explosion.
    """

    max_tokens: int = 0  # 0 = unlimited
    max_cost_usd: float = 0.0  # 0.0 = unlimited
    max_wall_time_seconds: int = 0  # 0 = unlimited
    allocated_tokens: int = 0
    allocated_cost_usd: float = 0.0
    allocated_wall_time_seconds: int = 0

    @property
    def remaining_tokens(self) -> int:
        """Remaining tokens available for subdelegation (0 if unlimited)."""
        if self.max_tokens <= 0:
            return 0
        return max(0, self.max_tokens - self.allocated_tokens)

    @property
    def remaining_cost_usd(self) -> float:
        """Remaining cost available for subdelegation (0.0 if unlimited)."""
        if self.max_cost_usd <= 0.0:
            return 0.0
        return max(0.0, self.max_cost_usd - self.allocated_cost_usd)

    @property
    def remaining_wall_time_seconds(self) -> int:
        """Remaining wall time available for subdelegation (0 if unlimited)."""
        if self.max_wall_time_seconds <= 0:
            return 0
        return max(0, self.max_wall_time_seconds - self.allocated_wall_time_seconds)

    def is_exceeded(self, tokens: int = 0, cost: float = 0.0, seconds: int = 0) -> bool:
        """Check if current usage exceeds budget."""
        if self.max_tokens > 0 and tokens > self.max_tokens:
            return True
        if self.max_cost_usd > 0.0 and cost > self.max_cost_usd:
            return True
        return bool(self.max_wall_time_seconds > 0 and seconds > self.max_wall_time_seconds)


@dataclass
class DelegationContext:
    """Delegation Context Tuple (DCTX) per IDP v0.1.

    Represents the full context of a single delegation event with
    chain depth tracking and state machine enforcement.

    Fields:
        intent_id: Root intent identifier (shared across delegation tree)
        task_id: Unique identifier for this specific task
        parent_task_id: Reference to parent task (null for root)
        delegator_id: Agent issuing the delegation
        delegatee_id: Agent receiving the delegation
        contract_id: Reference to CONTRACT tuple
        verification_id: Reference to ATTEST tuple (null until verified)
        capability_token_id: Reference to DCT tuple
        risk_tier: Risk classification (LOW/MEDIUM/HIGH/CRITICAL)
        chain_depth: Number of subdelegation levels (0 = root)
        budget: Resource constraints
        status: Current delegation state
        created_at: ISO8601 timestamp
        replan_count: Number of replans executed
        metadata: Additional context data
    """

    intent_id: str
    task_id: str
    delegator_id: str
    delegatee_id: str
    contract_id: str
    parent_task_id: str | None = None
    verification_id: str | None = None
    capability_token_id: str | None = None
    risk_tier: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"] = "MEDIUM"
    chain_depth: int = 0
    budget: DelegationBudget = field(default_factory=DelegationBudget)
    status: DCTXStatus = "PROPOSED"
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc)
        .isoformat()
        .replace("+00:00", "Z")
    )
    replan_count: int = 0
    ops_allowed: tuple[str, ...] = ()  # Capabilities granted (empty = unconstrained)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate invariants after initialization."""
        if _is_idp_enabled():
            # I3: Validate chain depth
            if self.chain_depth > DEFAULT_MAX_CHAIN_DEPTH:
                raise ValueError(
                    f"IDP_E_DEPTH_EXCEEDED: chain_depth {self.chain_depth} > max {DEFAULT_MAX_CHAIN_DEPTH}"
                )

            # Validate parent/depth consistency
            if self.parent_task_id is not None and self.chain_depth == 0:
                raise ValueError("Non-root task must have chain_depth > 0")
            if self.parent_task_id is None and self.chain_depth != 0:
                raise ValueError("Root task must have chain_depth = 0")

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "intent_id": self.intent_id,
            "task_id": self.task_id,
            "parent_task_id": self.parent_task_id,
            "delegator_id": self.delegator_id,
            "delegatee_id": self.delegatee_id,
            "contract_id": self.contract_id,
            "verification_id": self.verification_id,
            "capability_token_id": self.capability_token_id,
            "risk_tier": self.risk_tier,
            "chain_depth": self.chain_depth,
            "budget": {
                "max_tokens": self.budget.max_tokens,
                "max_cost_usd": self.budget.max_cost_usd,
                "max_wall_time_seconds": self.budget.max_wall_time_seconds,
                "allocated_tokens": self.budget.allocated_tokens,
                "allocated_cost_usd": self.budget.allocated_cost_usd,
                "allocated_wall_time_seconds": self.budget.allocated_wall_time_seconds,
            },
            "status": self.status,
            "created_at": self.created_at,
            "replan_count": self.replan_count,
            "ops_allowed": list(self.ops_allowed),
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DelegationContext:
        """Deserialize from dictionary."""
        budget_data = data.get("budget", {})
        budget = DelegationBudget(
            max_tokens=budget_data.get("max_tokens", 0),
            max_cost_usd=budget_data.get("max_cost_usd", 0.0),
            max_wall_time_seconds=budget_data.get("max_wall_time_seconds", 0),
            allocated_tokens=budget_data.get("allocated_tokens", 0),
            allocated_cost_usd=budget_data.get("allocated_cost_usd", 0.0),
            allocated_wall_time_seconds=budget_data.get("allocated_wall_time_seconds", 0),
        )
        return cls(
            intent_id=data["intent_id"],
            task_id=data["task_id"],
            delegator_id=data["delegator_id"],
            delegatee_id=data["delegatee_id"],
            contract_id=data["contract_id"],
            parent_task_id=data.get("parent_task_id"),
            verification_id=data.get("verification_id"),
            capability_token_id=data.get("capability_token_id"),
            risk_tier=data.get("risk_tier", "MEDIUM"),
            chain_depth=data.get("chain_depth", 0),
            budget=budget,
            status=data.get("status", "PROPOSED"),
            created_at=data.get("created_at"),
            replan_count=data.get("replan_count", 0),
            ops_allowed=tuple(data.get("ops_allowed", ())),
            metadata=data.get("metadata", {}),
        )

    def transition(self, new_status: DCTXStatus) -> tuple[bool, str | None]:
        """Execute state machine transition.

        Valid transitions per IDP_SPEC.md:
        PROPOSED → ISSUED
        ISSUED → RUNNING
        RUNNING → EVIDENCE_READY
        EVIDENCE_READY → VERIFIED
        EVIDENCE_READY → REPLANNED
        REPLANNED → PROPOSED (with replan_count check)
        REPLANNED → FAILED
        ISSUED → FAILED
        RUNNING → FAILED

        Args:
            new_status: Target state

        Returns:
            Tuple of (success, error_code)
        """
        if not _is_idp_enabled():
            self.status = new_status
            return True, None

        valid_transitions: dict[DCTXStatus, list[DCTXStatus]] = {
            "PROPOSED": ["ISSUED"],
            "ISSUED": ["RUNNING", "FAILED"],
            "RUNNING": ["EVIDENCE_READY", "FAILED"],
            "EVIDENCE_READY": ["VERIFIED", "REPLANNED"],
            "REPLANNED": ["PROPOSED", "FAILED"],
            "VERIFIED": [],  # Terminal state
            "FAILED": [],  # Terminal state
        }

        allowed = valid_transitions.get(self.status, [])
        if new_status not in allowed:
            return False, IDP_E_INVALID_STATE_TRANSITION

        # I5: Check replan limit for REPLANNED → PROPOSED
        if self.status == "EVIDENCE_READY" and new_status == "REPLANNED":
            if self.replan_count >= DEFAULT_MAX_REPLANS:
                return False, IDP_E_REPLAN_LIMIT

        # Update replan count when transitioning to REPLANNED
        if new_status == "REPLANNED":
            self.replan_count += 1

        self.status = new_status
        return True, None

    def can_subdelegate(
        self, max_depth: int = DEFAULT_MAX_CHAIN_DEPTH
    ) -> tuple[bool, str | None]:
        """Check if this task can be subdelegated (I3 invariant).

        Args:
            max_depth: Maximum allowed chain depth

        Returns:
            Tuple of (can_subdelegate, error_code)
        """
        if not _is_idp_enabled():
            return True, None

        if self.chain_depth + 1 > max_depth:
            return False, IDP_E_DEPTH_EXCEEDED
        return True, None

    def create_child(
        self,
        delegatee_id: str,
        contract_id: str,
        risk_tier: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"] | None = None,
        budget: DelegationBudget | None = None,
        ops_allowed: tuple[str, ...] | None = None,
        trust_score: float | None = None,
    ) -> tuple[DelegationContext | None, str | None]:
        """Create child delegation context (subdelegation).

        Enforces I2 monotonic capability attenuation and I3 bounded chain depth.
        When trust_score is provided, uses dynamic trust-decay depth model (G3);
        otherwise falls back to static DEFAULT_MAX_CHAIN_DEPTH.

        Args:
            delegatee_id: Agent receiving subdelegation
            contract_id: Contract for child task
            risk_tier: Child risk tier (default: same as parent)
            budget: Child budget (default: same as parent)
            ops_allowed: Child operations (must be subset of parent's; default: same as parent)
            trust_score: Optional Beta trust score τ in [0.0, 1.0]. When provided,
                computes dynamic depth bound δ_effective = min(δ_max, floor(τ / τ_o)).

        Returns:
            Tuple of (child_context, error_code). Error codes:
            - IDP_E_DEPTH_EXCEEDED: Would exceed static max chain depth
            - IDP_E_TRUST_DEPTH_EXCEEDED: Would exceed dynamic trust-decay depth
            - IDP_E_CAPABILITY_ESCALATION: Child ops not subset of parent ops
        """
        if not _is_idp_enabled():
            return None, None

        # G3: Dynamic trust-decay depth (supersedes static bound when trust_score provided)
        resolved_risk = risk_tier or self.risk_tier
        if trust_score is not None:
            dynamic_max = compute_dynamic_depth(trust_score, resolved_risk)
            if self.chain_depth + 1 > dynamic_max:
                return None, IDP_E_TRUST_DEPTH_EXCEEDED
        else:
            can_sub, error = self.can_subdelegate()
            if not can_sub:
                return None, error

        # I2: Monotonic capability attenuation
        # Child ops must be a subset of parent ops (capabilities can only narrow).
        child_ops = ops_allowed if ops_allowed is not None else self.ops_allowed
        if self.ops_allowed and child_ops:
            parent_set = set(self.ops_allowed)
            child_set = set(child_ops)
            if not child_set.issubset(parent_set):
                return None, IDP_E_CAPABILITY_ESCALATION

        # Subtree budget attenuation & allocation
        child_budget: DelegationBudget
        if budget is not None:
            # Escalation check: Child cannot ask for unlimited when parent is bounded,
            # nor exceed parent's remaining pool.
            if self.budget.max_tokens > 0:
                if budget.max_tokens <= 0 or budget.max_tokens > self.budget.remaining_tokens:
                    return None, IDP_E_BUDGET_ESCALATION
            if self.budget.max_cost_usd > 0.0:
                if budget.max_cost_usd <= 0.0 or budget.max_cost_usd > self.budget.remaining_cost_usd:
                    return None, IDP_E_BUDGET_ESCALATION
            if self.budget.max_wall_time_seconds > 0:
                if budget.max_wall_time_seconds <= 0 or budget.max_wall_time_seconds > self.budget.remaining_wall_time_seconds:
                    return None, IDP_E_BUDGET_ESCALATION
            child_budget = DelegationBudget(
                max_tokens=budget.max_tokens,
                max_cost_usd=budget.max_cost_usd,
                max_wall_time_seconds=budget.max_wall_time_seconds,
            )
        else:
            # Child inherits remaining budget from parent
            child_budget = DelegationBudget(
                max_tokens=self.budget.remaining_tokens if self.budget.max_tokens > 0 else 0,
                max_cost_usd=self.budget.remaining_cost_usd if self.budget.max_cost_usd > 0.0 else 0.0,
                max_wall_time_seconds=self.budget.remaining_wall_time_seconds if self.budget.max_wall_time_seconds > 0 else 0,
            )

        # Decrement parent's remaining capacity by recording allocation
        if child_budget.max_tokens > 0:
            self.budget.allocated_tokens += child_budget.max_tokens
        if child_budget.max_cost_usd > 0.0:
            self.budget.allocated_cost_usd += child_budget.max_cost_usd
        if child_budget.max_wall_time_seconds > 0:
            self.budget.allocated_wall_time_seconds += child_budget.max_wall_time_seconds

        return (
            DelegationContext(
                intent_id=self.intent_id,  # Same intent (shared tree)
                task_id=str(uuid.uuid4()),
                parent_task_id=self.task_id,
                delegator_id=self.delegatee_id,  # Child's delegator is this task's delegatee
                delegatee_id=delegatee_id,
                contract_id=contract_id,
                risk_tier=risk_tier or self.risk_tier,
                chain_depth=self.chain_depth + 1,
                budget=child_budget,
                ops_allowed=child_ops,
                status="PROPOSED",
            ),
            None,
        )

    def is_terminal(self) -> bool:
        """Check if task is in terminal state."""
        return self.status in ("VERIFIED", "FAILED")

    def is_active(self) -> bool:
        """Check if task is actively running."""
        return self.status in ("ISSUED", "RUNNING")


class DelegationContextManager:
    """Manager for DCTX lifecycle operations.

    Tracks active delegations and enforces invariants.
    """

    def __init__(self, max_depth: int = DEFAULT_MAX_CHAIN_DEPTH):
        """Initialize context manager.

        Args:
            max_depth: Maximum delegation chain depth (default: 3)
        """
        self._max_depth = max_depth
        self._contexts: dict[str, DelegationContext] = {}

    def create_root(
        self,
        intent_id: str,
        delegator_id: str,
        delegatee_id: str,
        contract_id: str,
        risk_tier: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"] = "MEDIUM",
        budget: DelegationBudget | None = None,
    ) -> DelegationContext:
        """Create root delegation context (chain_depth = 0).

        Args:
            intent_id: Root intent identifier
            delegator_id: Agent issuing delegation
            delegatee_id: Agent receiving delegation
            contract_id: Contract ID
            risk_tier: Risk classification
            budget: Resource constraints

        Returns:
            New root DelegationContext
        """
        ctx = DelegationContext(
            intent_id=intent_id,
            task_id=str(uuid.uuid4()),
            delegator_id=delegator_id,
            delegatee_id=delegatee_id,
            contract_id=contract_id,
            risk_tier=risk_tier,
            chain_depth=0,
            budget=budget or DelegationBudget(),
            status="PROPOSED",
        )
        self._contexts[ctx.task_id] = ctx
        return ctx

    def get_context(self, task_id: str) -> DelegationContext | None:
        """Get context by task ID."""
        return self._contexts.get(task_id)

    def get_by_intent(self, intent_id: str) -> list[DelegationContext]:
        """Get all contexts for an intent."""
        return [ctx for ctx in self._contexts.values() if ctx.intent_id == intent_id]

    def get_chain(self, task_id: str) -> list[DelegationContext]:
        """Get full delegation chain from root to task."""
        chain = []
        current = self._contexts.get(task_id)
        while current:
            chain.append(current)
            if current.parent_task_id is None:
                break
            current = self._contexts.get(current.parent_task_id)
        return list(reversed(chain))


# Convenience functions
def create_root_context(
    intent_id: str, delegator_id: str, delegatee_id: str, contract_id: str, **kwargs
) -> DelegationContext:
    """Convenience function to create root context."""
    return DelegationContext(
        intent_id=intent_id,
        task_id=str(uuid.uuid4()),
        delegator_id=delegator_id,
        delegatee_id=delegatee_id,
        contract_id=contract_id,
        chain_depth=0,
        **kwargs,
    )


def create_child_context(
    parent: DelegationContext, delegatee_id: str, contract_id: str, **kwargs
) -> tuple[DelegationContext | None, str | None]:
    """Convenience function to create child context."""
    return parent.create_child(delegatee_id, contract_id, **kwargs)
