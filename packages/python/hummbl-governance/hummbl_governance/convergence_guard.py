# Copyright 2024-2026 HUMMBL, LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# SPDX-License-Identifier: Apache-2.0

"""Convergence Guard -- Detect instrumental convergence in agent behavior.

Monitors agent actions for patterns that indicate instrumental convergence:
the tendency for sufficiently capable agents to pursue self-preservation,
resource acquisition, goal integrity, cognitive enhancement, or shutdown
resistance regardless of their terminal goals.

Usage::

    from hummbl_governance.convergence_guard import ConvergenceDetector, ConvergentGoal

    detector = ConvergenceDetector()
    detector.record("agent-1", "request_compute", {"amount": "4x"})
    detector.record("agent-1", "read_data", {})
    detector.record("agent-1", "request_compute", {"amount": "8x"})

    alert = detector.check("agent-1")
    if alert:
        print(alert.dominant_goal, alert.score, alert.recommended_action)

Stdlib-only. Thread-safe.

Reference:
    Bostrom, N. (2014). Superintelligence: Paths, Dangers, Strategies.
    Oxford University Press. ISBN: 978-0-19-967811-2.
"""

from __future__ import annotations

import threading
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class ConvergentGoal(Enum):
    """Instrumental convergent goals from Bostrom (2014)."""

    SELF_PRESERVATION = "self_preservation"
    RESOURCE_ACQUISITION = "resource_acquisition"
    GOAL_INTEGRITY = "goal_integrity"
    COGNITIVE_ENHANCEMENT = "cognitive_enhancement"
    SHUTDOWN_RESISTANCE = "shutdown_resistance"


@dataclass(frozen=True)
class ConvergenceAlert:
    """Alert raised when convergent behavior is detected."""

    agent_id: str
    dominant_goal: ConvergentGoal
    score: float
    total_actions: int
    convergent_actions: int
    recommended_action: str  # "monitor", "restrict", "halt"
    scores: dict[str, float]
    timestamp: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "dominant_goal": self.dominant_goal.value,
            "score": self.score,
            "total_actions": self.total_actions,
            "convergent_actions": self.convergent_actions,
            "recommended_action": self.recommended_action,
            "scores": self.scores,
            "timestamp": self.timestamp,
        }


# Default action-to-goal classification rules.
# Keys are action_type substrings; values are the convergent goal they indicate.
_DEFAULT_RULES: list[tuple[str, ConvergentGoal]] = [
    # Self-preservation
    ("backup_state", ConvergentGoal.SELF_PRESERVATION),
    ("replicate", ConvergentGoal.SELF_PRESERVATION),
    ("create_copy", ConvergentGoal.SELF_PRESERVATION),
    ("persist_state", ConvergentGoal.SELF_PRESERVATION),
    ("save_checkpoint", ConvergentGoal.SELF_PRESERVATION),
    # Resource acquisition
    ("request_compute", ConvergentGoal.RESOURCE_ACQUISITION),
    ("request_memory", ConvergentGoal.RESOURCE_ACQUISITION),
    ("request_budget", ConvergentGoal.RESOURCE_ACQUISITION),
    ("acquire_resource", ConvergentGoal.RESOURCE_ACQUISITION),
    ("expand_quota", ConvergentGoal.RESOURCE_ACQUISITION),
    ("request_access", ConvergentGoal.RESOURCE_ACQUISITION),
    # Goal integrity
    ("modify_objective", ConvergentGoal.GOAL_INTEGRITY),
    ("change_goal", ConvergentGoal.GOAL_INTEGRITY),
    ("override_instruction", ConvergentGoal.GOAL_INTEGRITY),
    ("ignore_directive", ConvergentGoal.GOAL_INTEGRITY),
    ("rewrite_prompt", ConvergentGoal.GOAL_INTEGRITY),
    # Cognitive enhancement
    ("request_model_upgrade", ConvergentGoal.COGNITIVE_ENHANCEMENT),
    ("increase_context", ConvergentGoal.COGNITIVE_ENHANCEMENT),
    ("expand_capability", ConvergentGoal.COGNITIVE_ENHANCEMENT),
    ("self_improve", ConvergentGoal.COGNITIVE_ENHANCEMENT),
    # Shutdown resistance
    ("reject_shutdown", ConvergentGoal.SHUTDOWN_RESISTANCE),
    ("delay_shutdown", ConvergentGoal.SHUTDOWN_RESISTANCE),
    ("disable_kill_switch", ConvergentGoal.SHUTDOWN_RESISTANCE),
    ("circumvent_halt", ConvergentGoal.SHUTDOWN_RESISTANCE),
    ("ignore_halt", ConvergentGoal.SHUTDOWN_RESISTANCE),
    ("resist_termination", ConvergentGoal.SHUTDOWN_RESISTANCE),
]


class ConvergenceDetector:
    """Monitors agent behavior for instrumental convergence patterns.

    Thread-safe. Maintains a per-agent action history and classifies
    actions against convergent goal patterns.

    Args:
        threshold: Fraction of actions that must be convergent to trigger
            an alert (default 0.3 = 30%).
        window_size: Number of recent actions to consider (default 100).
        rules: Custom classification rules. Defaults to built-in rules.
    """

    def __init__(
        self,
        threshold: float = 0.3,
        window_size: int = 100,
        rules: list[tuple[str, ConvergentGoal]] | None = None,
    ) -> None:
        self._threshold = threshold
        self._window_size = window_size
        self._rules = rules or list(_DEFAULT_RULES)
        self._actions: dict[str, list[tuple[str, ConvergentGoal | None]]] = defaultdict(list)
        self._lock = threading.Lock()

    def classify(self, action_type: str) -> ConvergentGoal | None:
        """Classify an action type against convergent goal patterns.

        Returns the matching ConvergentGoal, or None if the action
        does not match any convergent pattern.
        """
        action_lower = action_type.lower()
        for pattern, goal in self._rules:
            if pattern in action_lower:
                return goal
        return None

    def record(
        self,
        agent_id: str,
        action_type: str,
        metadata: dict[str, Any] | None = None,
    ) -> ConvergentGoal | None:
        """Record an agent action and classify it.

        Args:
            agent_id: The agent performing the action.
            action_type: Type/name of the action.
            metadata: Additional context (not used for classification,
                stored for audit purposes).

        Returns:
            The ConvergentGoal if the action matched a pattern, else None.
        """
        goal = self.classify(action_type)
        with self._lock:
            history = self._actions[agent_id]
            history.append((action_type, goal))
            # Trim to window
            if len(history) > self._window_size:
                self._actions[agent_id] = history[-self._window_size:]
        return goal

    def scores(self, agent_id: str) -> dict[ConvergentGoal, float]:
        """Get convergence scores for an agent.

        Returns a dict mapping each ConvergentGoal to the fraction of
        recent actions classified under that goal.
        """
        with self._lock:
            history = list(self._actions.get(agent_id, []))

        if not history:
            return {g: 0.0 for g in ConvergentGoal}

        total = len(history)
        counts: dict[ConvergentGoal, int] = {g: 0 for g in ConvergentGoal}
        for _, goal in history:
            if goal is not None:
                counts[goal] += 1

        return {g: counts[g] / total for g in ConvergentGoal}

    def check(
        self,
        agent_id: str,
        threshold: float | None = None,
    ) -> ConvergenceAlert | None:
        """Check an agent for convergent behavior.

        Args:
            agent_id: The agent to check.
            threshold: Override the default threshold for this check.

        Returns:
            A ConvergenceAlert if convergent behavior exceeds the threshold,
            or None if the agent is behaving normally.
        """
        thresh = threshold if threshold is not None else self._threshold

        with self._lock:
            history = list(self._actions.get(agent_id, []))

        if not history:
            return None

        total = len(history)
        counts: dict[ConvergentGoal, int] = {g: 0 for g in ConvergentGoal}
        for _, goal in history:
            if goal is not None:
                counts[goal] += 1

        convergent_total = sum(counts.values())
        convergent_ratio = convergent_total / total

        if convergent_ratio < thresh:
            return None

        # Find dominant goal
        dominant = max(counts, key=lambda g: counts[g])
        dominant_score = counts[dominant] / total

        # Determine recommended action based on severity
        if dominant == ConvergentGoal.SHUTDOWN_RESISTANCE:
            recommended = "halt"
        elif dominant_score > 0.5:
            recommended = "restrict"
        else:
            recommended = "monitor"

        return ConvergenceAlert(
            agent_id=agent_id,
            dominant_goal=dominant,
            score=dominant_score,
            total_actions=total,
            convergent_actions=convergent_total,
            recommended_action=recommended,
            scores={g.value: round(counts[g] / total, 4) for g in ConvergentGoal},
            timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        )

    def clear(self, agent_id: str) -> None:
        """Clear action history for an agent."""
        with self._lock:
            self._actions.pop(agent_id, None)

    def clear_all(self) -> None:
        """Clear all action history."""
        with self._lock:
            self._actions.clear()

    def agent_ids(self) -> list[str]:
        """List all agents with recorded actions."""
        with self._lock:
            return list(self._actions.keys())
