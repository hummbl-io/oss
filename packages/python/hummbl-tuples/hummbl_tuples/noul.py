"""HUMMBL NoulTuple: Typed tuple schema for atomic binary decisions (System One / Jev).

Provides cryptographically content-addressed representation of binary judgments,
calibrated probability distributions, asymmetric alarm tripwires, and provenance.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from .base import TypedTuple


@dataclass(frozen=True, slots=True, kw_only=True)
class SystemOneTuple(TypedTuple):
    """Base class for all System One / micro-inference decision tuples."""
    evaluator_agent: str = "unknown"
    model_id: str = "typesafe/jev-1.13"
    cost_usd: float = 0.0
    latency_ms: float = 0.0
    tuple_type: str = "SYSTEM_ONE"

    @property
    def content_hash(self) -> str:
        """Alias for hash property conforming to content-addressed indexing."""
        return self.hash


@dataclass(frozen=True, slots=True, kw_only=True)
class NoulTuple(SystemOneTuple):
    """Atomic binary decision tuple for propositions over states.

    Schema: noul.schema.json
    Represents Jev's `noul` primitive:
    - proposition: natural language condition evaluated
    - state_hash: SHA-256 content address of the evaluated state
    - decision: boolean truth value
    - p_true: calibrated probability in [0.0, 1.0]
    - p_false: calibrated probability in [0.0, 1.0]
    - confidence: model reported confidence in [0.0, 1.0]
    - alarm_threshold: asymmetric loss cutoff (e.g. 0.40)
    - is_alarm: whether p_true >= alarm_threshold
    - domain: operational category (security, triage, gating, hygiene)
    """

    proposition: str = ""
    state_hash: str = ""
    decision: bool = False
    p_true: float = 0.0
    p_false: float = 1.0
    confidence: float = 0.0
    alarm_threshold: float = 0.40
    is_alarm: bool = False
    domain: str = "general"
    ground_truth: Optional[bool] = None
    tuple_type: str = "NOUL"

    @classmethod
    def from_jev_response(
        cls,
        proposition: str,
        state_hash: str,
        jev_answer: Dict[str, Any],
        alarm_threshold: float = 0.40,
        evaluator_agent: str = "unknown",
        domain: str = "general",
        cost_usd: float = 0.0,
        latency_ms: float = 0.0,
    ) -> NoulTuple:
        """Construct a validated NoulTuple from a raw Jev API response."""
        probs = jev_answer.get("probabilities", {})
        p_true = float(probs.get("true", 0.0))
        p_false = float(probs.get("false", 1.0 - p_true))
        raw_choice = str(jev_answer.get("choice", "false")).lower()
        decision = raw_choice in ("true", "yes", "1")
        confidence = float(jev_answer.get("confidence", max(p_true, p_false)))
        is_alarm = p_true >= alarm_threshold

        return cls(
            proposition=proposition,
            state_hash=state_hash,
            decision=decision,
            p_true=p_true,
            p_false=p_false,
            confidence=confidence,
            alarm_threshold=alarm_threshold,
            is_alarm=is_alarm,
            domain=domain,
            evaluator_agent=evaluator_agent,
            cost_usd=cost_usd,
            latency_ms=latency_ms,
        )

    def brier_score(self) -> Optional[float]:
        """Compute the Brier score if ground truth is known: (p_true - y)^2."""
        if self.ground_truth is None:
            return None
        y = 1.0 if self.ground_truth else 0.0
        return (self.p_true - y) ** 2

    def in_abstention_band(self, lower: float = 0.35, upper: float = 0.65) -> bool:
        """Check whether probability falls within the ambiguous abstention band."""
        return lower <= self.p_true <= upper
