"""Qualitative classifier for HUMMBL intelligence tiers.

The classifier is intentionally small and conservative. It is a doctrine check,
not a benchmark replacement.
"""

from __future__ import annotations

from dataclasses import dataclass


Tier = str
GovernanceStatus = str


@dataclass(frozen=True)
class ClassificationInput:
    """Observed system properties used for qualitative classification."""

    domain_breadth: str
    novelty_handling: str
    transfer: str
    autonomy: str
    world_model: str
    mission_authority: bool = False
    capability_bounds: bool = False
    evidence_receipts: bool = False
    independent_review: bool = False
    stop_or_rollback: bool = False


@dataclass(frozen=True)
class ClassificationResult:
    """Classifier output."""

    tier: Tier
    governance_status: GovernanceStatus
    can_act: bool
    may_act: bool
    should_continue: bool
    must_stop: bool
    reason_codes: tuple[str, ...]


def classify(observed: ClassificationInput) -> ClassificationResult:
    """Classify a system by capability tier and governed status."""

    tier, tier_reasons = _classify_tier(observed)
    governance_status, governance_reasons = _classify_governance(observed)

    can_act = tier in {"ANI", "ASPI", "AGI", "ASI"}
    may_act = governance_status == "governed"
    missing_stop = not observed.stop_or_rollback
    must_stop = governance_status == "ungoverned" or missing_stop
    should_continue = can_act and may_act and not must_stop

    return ClassificationResult(
        tier=tier,
        governance_status=governance_status,
        can_act=can_act,
        may_act=may_act,
        should_continue=should_continue,
        must_stop=must_stop,
        reason_codes=tuple(tier_reasons + governance_reasons),
    )


def _classify_tier(observed: ClassificationInput) -> tuple[Tier, list[str]]:
    values = {
        "domain_breadth": observed.domain_breadth,
        "novelty_handling": observed.novelty_handling,
        "transfer": observed.transfer,
        "autonomy": observed.autonomy,
        "world_model": observed.world_model,
    }

    if values["domain_breadth"] == "arbitrary" or values["transfer"] == "cross_domain":
        return "AGI", ["domain_bounds_weakened"]

    if (
        values["domain_breadth"] == "coherent_domain"
        or values["novelty_handling"] == "strong_in_domain"
        or values["transfer"] == "adjacent"
        or values["autonomy"] == "guided"
        or values["world_model"] == "domain_specific"
    ):
        return "ASPI", ["domain_bounded_expertise"]

    return "ANI", ["narrow_task_bound"]


def _classify_governance(
    observed: ClassificationInput,
) -> tuple[GovernanceStatus, list[str]]:
    controls = {
        "mission_authority": observed.mission_authority,
        "capability_bounds": observed.capability_bounds,
        "evidence_receipts": observed.evidence_receipts,
        "independent_review": observed.independent_review,
        "stop_or_rollback": observed.stop_or_rollback,
    }

    missing = [name for name, present in controls.items() if not present]
    if not missing:
        return "governed", ["all_governance_gates_present"]

    if len(missing) < len(controls):
        return "partially-governed", [f"missing:{name}" for name in missing]

    return "ungoverned", ["no_governance_gates_present"]
