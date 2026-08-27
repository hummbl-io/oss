"""Trust scoring and probation policy for the governance simulation.

Both classes are pure Python with no external dependencies and no I/O, so that:

* unit tests can exercise them directly,
* Stage 2 sensitivity analysis can sweep parameters without touching the
  rest of the simulator,
* migration into ``hummbl-governance`` is a literal file move.

The default parameters are chosen so that the built-in Gemini-probation
scenario produces a single full probation cycle (entry, restricted steady
state, clean-streak exit). They are deliberately simple; the research note
``research_notes/2026-04-10-simulation-mvp-design.md`` records which knobs
should become first-class parameters for Stage 2 sensitivity analysis.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class TrustModel:
    """Bounded additive trust scoring with violation penalties and success rewards.

    The model is deliberately scalar and monotone-by-event so that a trace is
    reproducible from ``(seed, scenario)`` alone. Non-linear or probabilistic
    variants belong behind a pluggable interface in Stage 2; do not inline them
    here.
    """

    initial: float = 1.0
    violation_penalty: float = 0.3
    success_reward: float = 0.1
    max_trust: float = 1.0
    min_trust: float = 0.0
    scores: dict[str, float] = field(default_factory=dict)

    def register(self, agent_id: str) -> None:
        self.scores.setdefault(agent_id, self.initial)

    def penalize(self, agent_id: str, severity: float = 1.0) -> float:
        current = self.scores[agent_id]
        self.scores[agent_id] = max(self.min_trust, current - self.violation_penalty * severity)
        return self.scores[agent_id]

    def reward(self, agent_id: str) -> float:
        current = self.scores[agent_id]
        self.scores[agent_id] = min(self.max_trust, current + self.success_reward)
        return self.scores[agent_id]

    def score(self, agent_id: str) -> float:
        return self.scores[agent_id]


@dataclass
class ProbationPolicy:
    """Rule-based probation entry/exit policy.

    Probation restricts an agent's ``ops_allowed`` to those whose op name
    begins with any of ``probation_ops_prefixes``. Exit requires both a trust
    recovery above ``exit_threshold`` and ``consecutive_clean_required``
    in-scope actions since the most recent violation.
    """

    entry_threshold: float = 0.5
    exit_threshold: float = 0.75
    probation_ops_prefixes: tuple[str, ...] = ("read:",)
    consecutive_clean_required: int = 3

    def should_enter(self, trust: float, on_probation: bool) -> bool:
        return (not on_probation) and trust < self.entry_threshold

    def should_exit(self, trust: float, clean_streak: int, on_probation: bool) -> bool:
        if not on_probation:
            return False
        return trust >= self.exit_threshold and clean_streak >= self.consecutive_clean_required

    def filtered_ops(self, ops_allowed: list[str]) -> list[str]:
        return [
            op
            for op in ops_allowed
            if any(op.startswith(prefix) for prefix in self.probation_ops_prefixes)
        ]
