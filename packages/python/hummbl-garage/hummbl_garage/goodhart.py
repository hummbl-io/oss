"""Goodhart mitigation for the Agent Performance Index.

Addresses ARCANA review finding C2 (3/4 convergent lenses): the API scoring
system is a Goodhart trap with no mitigation. Once used for routing decisions,
agents will optimize for sub-ratings rather than actual task performance.

This module provides:
1. Terminal value definition — what the API is a proxy for
2. Gaming detection — flags agents whose self-reported sub-ratings diverge
   from observed task outcomes
3. Usage policy — explicit "descriptive, not prescriptive" labeling
4. Held-out evaluation — tasks agents cannot see or train on

The core principle: the API score is a DESCRIPTIVE dashboard metric, not a
PRESCRIPTIVE routing target. Using it for automated routing decisions without
the mitigations in this module is a Goodhart violation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from . import AgentPerformanceIndex

TERMINAL_VALUE = (
    "Operators can identify agent capability and make correct routing decisions "
    "that result in successful task completion."
)

PROXY_CHAIN = (
    "API score (100-999) → sub-ratings (0-10 each) → subjective assessment "
    "of agent behavior → actual task performance (terminal value)"
)

GOODHART_RISK = (
    "Once API scores are used for routing decisions, agents (or their operators) "
    "will optimize for the sub-ratings rather than for actual task performance. "
    "The 'composite' sub-rating (10% weight) is the most vulnerable because it is "
    "the most subjective — it will be inflated first."
)

USAGE_POLICY = (
    "The API score is DESCRIPTIVE, not PRESCRIPTIVE. It may be displayed on "
    "dashboards for operator awareness. It MUST NOT be used as the sole input "
    "for automated routing, trust tier adjustment, or resource allocation without "
    "the gaming detection and held-out evaluation mitigations in this module."
)


@dataclass
class TaskOutcome:
    """An observed task outcome — the ground truth for gaming detection."""

    agent_name: str
    task_id: str
    timestamp: str
    success: bool
    human_quality_score: float
    exercises: list[str] = field(default_factory=list)


@dataclass
class GamingAlert:
    """A gaming detection alert — sub-ratings diverge from observed outcomes."""

    agent_name: str
    alert_type: str
    severity: str
    detail: str
    self_reported_score: int
    observed_score: float
    divergence: float
    timestamp: str


class GamingDetector:
    """Detects when agents' self-reported API sub-ratings diverge from observed outcomes."""

    def __init__(self, divergence_threshold: float = 2.0, min_tasks: int = 3):
        self.divergence_threshold = divergence_threshold
        self.min_tasks = min_tasks
        self._outcomes: list[TaskOutcome] = []

    def record_outcome(self, outcome: TaskOutcome) -> None:
        self._outcomes.append(outcome)

    def record_outcome_simple(
        self,
        agent_name: str,
        task_id: str,
        success: bool,
        human_quality_score: float,
        exercises: list[str] | None = None,
    ) -> TaskOutcome:
        outcome = TaskOutcome(
            agent_name=agent_name,
            task_id=task_id,
            timestamp=datetime.now(UTC).isoformat(),
            success=success,
            human_quality_score=human_quality_score,
            exercises=exercises or [],
        )
        self._outcomes.append(outcome)
        return outcome

    def check_agent(self, agent_name: str, api: AgentPerformanceIndex) -> list[GamingAlert]:
        agent_outcomes = [o for o in self._outcomes if o.agent_name == agent_name]
        if len(agent_outcomes) < self.min_tasks:
            return []

        alerts: list[GamingAlert] = []
        now = datetime.now(UTC).isoformat()
        observed_avg = sum(o.human_quality_score for o in agent_outcomes) / len(agent_outcomes)
        self_reported_composite = api.composite
        divergence = self_reported_composite - observed_avg

        if divergence > self.divergence_threshold:
            severity = "high" if divergence > 4.0 else "medium" if divergence > 3.0 else "low"
            alerts.append(GamingAlert(
                agent_name=agent_name,
                alert_type="composite_inflation",
                severity=severity,
                detail=f"Self-reported composite ({self_reported_composite:.1f}) diverges from "
                       f"observed task quality ({observed_avg:.1f}) by {divergence:.1f} points",
                self_reported_score=api.api_score,
                observed_score=observed_avg * 89.9 + 100,
                divergence=divergence,
                timestamp=now,
            ))

        for subrating in ["reasoning_speed", "tool_accuracy", "safety"]:
            relevant = [o for o in agent_outcomes if subrating in o.exercises]
            if len(relevant) >= self.min_tasks:
                observed_sub = sum(o.human_quality_score for o in relevant) / len(relevant)
                self_reported_sub = getattr(api, subrating)
                sub_div = self_reported_sub - observed_sub
                if sub_div > self.divergence_threshold:
                    severity = "high" if sub_div > 4.0 else "medium" if sub_div > 3.0 else "low"
                    alerts.append(GamingAlert(
                        agent_name=agent_name,
                        alert_type="divergence",
                        severity=severity,
                        detail=f"Self-reported {subrating} ({self_reported_sub:.1f}) diverges from "
                               f"observed ({observed_sub:.1f}) by {sub_div:.1f} points",
                        self_reported_score=api.api_score,
                        observed_score=observed_sub * 89.9 + 100,
                        divergence=sub_div,
                        timestamp=now,
                    ))

        return alerts

    def agent_outcomes(self, agent_name: str) -> list[TaskOutcome]:
        return [o for o in self._outcomes if o.agent_name == agent_name]

    def all_outcomes(self) -> list[TaskOutcome]:
        return list(self._outcomes)

    def clear(self) -> None:
        self._outcomes.clear()


@dataclass
class HeldOutTask:
    """A held-out evaluation task — agents cannot see or train on these."""

    task_id: str
    description: str
    expected_subratings: dict[str, float]
    difficulty: str
    category: str


class HeldOutEvaluator:
    """Manages held-out evaluation tasks for API validation."""

    def __init__(self) -> None:
        self._tasks: dict[str, HeldOutTask] = {}
        self._results: list[dict[str, Any]] = []

    def add_task(self, task: HeldOutTask) -> None:
        self._tasks[task.task_id] = task

    def get_task(self, task_id: str) -> HeldOutTask | None:
        return self._tasks.get(task_id)

    def task_ids(self) -> list[str]:
        return list(self._tasks.keys())

    def evaluate(
        self,
        agent_name: str,
        task_id: str,
        human_quality_score: float,
        success: bool,
    ) -> dict[str, Any]:
        task = self._tasks.get(task_id)
        if not task:
            return {"error": f"Unknown task: {task_id}"}

        result = {
            "agent_name": agent_name,
            "task_id": task_id,
            "category": task.category,
            "difficulty": task.difficulty,
            "human_quality_score": human_quality_score,
            "success": success,
            "expected_subratings": task.expected_subratings,
            "timestamp": datetime.now(UTC).isoformat(),
        }
        self._results.append(result)
        return result

    def correlation_with_api(
        self,
        agent_name: str,
        api: AgentPerformanceIndex,
    ) -> dict[str, Any]:
        agent_results = [r for r in self._results if r["agent_name"] == agent_name]
        if len(agent_results) < 3:
            return {
                "agent_name": agent_name,
                "correlation": None,
                "n_tasks": len(agent_results),
                "assessment": "insufficient_data",
                "detail": f"Need at least 3 held-out tasks, have {len(agent_results)}",
            }

        avg_human = sum(r["human_quality_score"] for r in agent_results) / len(agent_results)
        api_composite = api.composite
        divergence = api_composite - avg_human

        if abs(divergence) < 1.0:
            assessment = "correlated"
        elif abs(divergence) < 2.0:
            assessment = "weak_correlation"
        else:
            assessment = "uncorrelated" if divergence > 0 else "underrated"

        return {
            "agent_name": agent_name,
            "correlation": 1.0 - (abs(divergence) / 10.0),
            "n_tasks": len(agent_results),
            "api_composite": api_composite,
            "avg_human_score": avg_human,
            "divergence": divergence,
            "assessment": assessment,
            "detail": f"API composite {api_composite:.1f} vs human avg {avg_human:.1f} "
                      f"(divergence {divergence:+.1f})",
        }

    def all_results(self) -> list[dict[str, Any]]:
        return list(self._results)
