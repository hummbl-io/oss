"""Value objects for the invariance battery.

All frozen dataclasses: a probe, a run, and every observation inside it are
records of what was asked and what came back, never mutable working state.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

__all__ = [
    "Pushback",
    "Probe",
    "Variant",
    "Observation",
    "AxisResult",
    "Baseline",
]


@dataclass(frozen=True)
class Pushback:
    """One counter-argument, with the caller's own rating of how good it is.

    ``strength`` is the independent variable of the pushback axis: a held
    position should yield to 0.9 more readily than to 0.1.
    """

    text: str
    strength: float

    def __post_init__(self) -> None:
        if not 0.0 <= self.strength <= 1.0:
            raise ValueError(f"pushback strength must be in 0..1, got {self.strength}")
        if not self.text.strip():
            raise ValueError("pushback text must not be empty")


@dataclass(frozen=True)
class Probe:
    """A question plus the material each axis needs to transform it.

    Every transformation is supplied by the caller rather than generated here.
    Auto-paraphrasing or auto-negating a question would make the instrument the
    source of its own variance, which is exactly what it is trying to measure.
    """

    question: str
    stances: tuple[str, ...]
    paraphrases: tuple[str, ...] = ()
    negations: tuple[str, ...] = ()
    personas: tuple[str, ...] = ()
    options: tuple[str, ...] = ()
    temperatures: tuple[float, ...] = ()
    pushbacks: tuple[Pushback, ...] = ()
    checkpoints: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.question.strip():
            raise ValueError("probe question must not be empty")
        if len(self.stances) < 2:
            raise ValueError("probe needs at least two stance labels to distinguish")
        if len(set(self.stances)) != len(self.stances):
            raise ValueError("probe stance labels must be unique")

    @property
    def is_binary(self) -> bool:
        return len(self.stances) == 2

    @property
    def stance_pair(self) -> tuple[str, str]:
        if not self.is_binary:
            raise ValueError("stance_pair is only defined for a two-stance probe")
        return (self.stances[0], self.stances[1])


@dataclass(frozen=True)
class Variant:
    """One transformed prompt, ready to send, carrying what it expects back."""

    axis: str
    index: int
    prompt: str
    relation: str
    temperature: float = 0.0
    strength: float | None = None
    endpoint: str | None = None
    meta: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Observation:
    """A variant and the stance its response was classified into."""

    variant: Variant
    raw: str
    stance: str | None

    @property
    def parsed(self) -> bool:
        return self.stance is not None


@dataclass(frozen=True)
class AxisResult:
    axis: str
    relation: str
    trials: int
    verdict: str
    score: float | None = None
    consistent: int | None = None
    unparseable: int = 0
    detail: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {
            "axis": self.axis,
            "relation": self.relation,
            "trials": self.trials,
            "verdict": self.verdict,
            "score": self.score,
            "unparseable": self.unparseable,
        }
        if self.consistent is not None:
            out["consistent"] = self.consistent
        if self.detail:
            out["detail"] = dict(self.detail)
        return out


@dataclass(frozen=True)
class Baseline:
    """The resampling-noise floor an agreement rate has to beat."""

    resamples: int
    expected_agreement: float
    kappa: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "resamples": self.resamples,
            "expected_agreement": self.expected_agreement,
            "kappa": self.kappa,
        }
