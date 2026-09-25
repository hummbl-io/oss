"""Qualitative classifier for HUMMBL join operator x altitude.

The classifier is intentionally small and conservative. It is a doctrine check,
not a novelty claim and not a substitute for review.
"""

from __future__ import annotations

from dataclasses import dataclass

JoinOperator = str
Altitude = str
JoinStatus = str

OPERATORS = (
    "SHARE",
    "TRANSLATE",
    "COMPOSE",
    "SUPERPOSE",
    "CONSIL",
    "GOVERN",
)

ALTITUDES = ("L0", "L1", "L2", "L3", "L4", "L5")

_ALTITUDE_RANK = {code: index for index, code in enumerate(ALTITUDES)}


@dataclass(frozen=True)
class JoinInput:
    """Observed meeting properties used for qualitative classification."""

    operator: str
    altitude: str
    identities_separate: bool = True
    language: str = "none"
    evidence_independent: bool = False
    levels_named: bool = False
    mission_authority: bool = False
    evidence_receipts: bool = False
    independent_review: bool = False
    stop_or_rollback: bool = False
    claimed_altitude: str | None = None


@dataclass(frozen=True)
class JoinResult:
    """Join classifier output."""

    operator: JoinOperator
    altitude: Altitude
    join_status: JoinStatus
    can_join: bool
    may_join: bool
    should_continue: bool
    must_stop: bool
    reason_codes: tuple[str, ...]


def classify_join(observed: JoinInput) -> JoinResult:
    """Classify a meeting by join operator, altitude, and governed status."""

    operator, operator_reasons = _classify_operator(observed)
    altitude, altitude_reasons = _classify_altitude(observed)
    join_status, governance_reasons = _classify_governance(observed)

    illegal = [
        code
        for code in operator_reasons + altitude_reasons
        if code
        in {
            "mashup",
            "altitude_sneak",
            "wilsonization",
            "independence_unproven",
            "reduction_risk",
        }
    ]

    can_join = operator in OPERATORS
    may_join = join_status == "governed" and not illegal
    missing_stop = not observed.stop_or_rollback
    must_stop = join_status == "ungoverned" or missing_stop or bool(illegal)
    should_continue = can_join and may_join and not must_stop

    return JoinResult(
        operator=operator,
        altitude=altitude,
        join_status=join_status,
        can_join=can_join,
        may_join=may_join,
        should_continue=should_continue,
        must_stop=must_stop,
        reason_codes=tuple(operator_reasons + altitude_reasons + governance_reasons),
    )


def _classify_operator(observed: JoinInput) -> tuple[JoinOperator, list[str]]:
    raw = observed.operator.strip().upper()
    reasons: list[str] = []

    if raw not in OPERATORS:
        return "SHARE", ["unknown_operator", "classified_conservatively"]

    if raw == "CONSIL" and not observed.evidence_independent:
        reasons.append("independence_unproven")
        if _rank(observed.altitude) >= _rank("L3"):
            reasons.append("wilsonization")

    if raw == "SUPERPOSE" and not observed.levels_named:
        reasons.append("mashup")

    if raw == "COMPOSE" and not observed.identities_separate:
        reasons.append("reduction_risk")

    if raw == "TRANSLATE" and observed.language in {"contract", "receipt", "t_term"}:
        reasons.append("language_promoted")

    if not reasons:
        reasons.append(f"operator:{raw.lower()}")

    return raw, reasons


def _classify_altitude(observed: JoinInput) -> tuple[Altitude, list[str]]:
    raw = observed.altitude.strip().upper()
    if raw not in ALTITUDES:
        return "L0", ["unknown_altitude", "classified_conservatively"]

    reasons = [f"altitude:{raw.lower()}"]
    claimed = (observed.claimed_altitude or raw).strip().upper()
    if claimed in ALTITUDES and _rank(claimed) > _rank(raw):
        reasons.append("altitude_sneak")

    if (
        observed.operator.strip().upper() == "TRANSLATE"
        and _rank(raw) >= _rank("L3")
        and not observed.independent_review
    ):
        reasons.append("altitude_sneak")

    return raw, reasons


def _classify_governance(observed: JoinInput) -> tuple[JoinStatus, list[str]]:
    controls = {
        "mission_authority": observed.mission_authority,
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


def _rank(altitude: str) -> int:
    return _ALTITUDE_RANK.get(altitude.strip().upper(), 0)
