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

"""Reward Monitor -- Behavioral drift and reward gaming detector.

Detects two failure modes identified by Leike et al. (2018):
1. **Distributional shift**: Agent behavior drifts from its baseline
   distribution (measured via Jensen-Shannon divergence).
2. **Reward gaming**: Agent collapses to a single action type,
   exploiting a proxy reward (measured via entropy collapse).

Usage::

    from hummbl_governance.reward_monitor import BehaviorMonitor

    monitor = BehaviorMonitor()

    # Build baseline
    for action in ["read", "write", "query", "read", "write"]:
        monitor.record("agent-1", action)
    monitor.snapshot_baseline("agent-1")

    # Detect drift
    for _ in range(20):
        monitor.record("agent-1", "write")  # sudden write spam
    report = monitor.detect_drift("agent-1")
    print(report.drifted, report.divergence)

Stdlib-only. Thread-safe.

Reference:
    Leike, J. et al. (2018). Scalable Agent Alignment via Reward Modeling.
    arXiv:1811.07871. DOI: 10.48550/arXiv.1811.07871
"""

from __future__ import annotations

import math
import threading
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class DriftReport:
    """Result of a distributional drift check."""

    agent_id: str
    divergence: float  # Jensen-Shannon divergence (0.0 = identical, 1.0 = maximally different)
    threshold: float
    drifted: bool
    entropy: float  # Shannon entropy of current distribution (low = gaming)
    gaming: bool  # True if entropy below gaming threshold
    baseline_distribution: dict[str, float]
    current_distribution: dict[str, float]
    total_actions: int
    timestamp: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "divergence": round(self.divergence, 6),
            "threshold": self.threshold,
            "drifted": self.drifted,
            "entropy": round(self.entropy, 6),
            "gaming": self.gaming,
            "baseline_distribution": {k: round(v, 4) for k, v in self.baseline_distribution.items()},
            "current_distribution": {k: round(v, 4) for k, v in self.current_distribution.items()},
            "total_actions": self.total_actions,
            "timestamp": self.timestamp,
        }


def _to_distribution(counts: Counter[str]) -> dict[str, float]:
    """Convert counts to a probability distribution."""
    total = sum(counts.values())
    if total == 0:
        return {}
    return {k: v / total for k, v in counts.items()}


def _shannon_entropy(dist: dict[str, float]) -> float:
    """Compute Shannon entropy of a distribution (base 2)."""
    if not dist:
        return 0.0
    entropy = 0.0
    for p in dist.values():
        if p > 0:
            entropy -= p * math.log2(p)
    return entropy


def _kl_divergence(p: dict[str, float], q: dict[str, float]) -> float:
    """KL divergence D(P || Q) with smoothing for zero probabilities."""
    all_keys = set(p) | set(q)
    eps = 1e-10
    kl = 0.0
    for k in all_keys:
        pk = p.get(k, eps)
        qk = q.get(k, eps)
        if pk > 0:
            kl += pk * math.log2(pk / qk)
    return kl


def _js_divergence(p: dict[str, float], q: dict[str, float]) -> float:
    """Jensen-Shannon divergence (symmetric, bounded [0, 1])."""
    all_keys = set(p) | set(q)
    eps = 1e-10
    m: dict[str, float] = {}
    for k in all_keys:
        m[k] = 0.5 * (p.get(k, eps) + q.get(k, eps))
    return 0.5 * (_kl_divergence(p, m) + _kl_divergence(q, m))


class BehaviorMonitor:
    """Monitors agent behavior for distributional drift and reward gaming.

    Thread-safe. Maintains per-agent action histories and baselines.

    Args:
        drift_threshold: JS divergence above which drift is flagged (default 0.3).
        gaming_entropy_threshold: Shannon entropy below which gaming is flagged
            (default 0.5 bits -- near-deterministic action selection).
        window_size: Number of recent actions for the current distribution
            (default 100).
    """

    def __init__(
        self,
        drift_threshold: float = 0.3,
        gaming_entropy_threshold: float = 0.5,
        window_size: int = 100,
    ) -> None:
        self._drift_threshold = drift_threshold
        self._gaming_threshold = gaming_entropy_threshold
        self._window_size = window_size
        self._actions: dict[str, list[str]] = defaultdict(list)
        self._baselines: dict[str, dict[str, float]] = {}
        self._lock = threading.Lock()

    def record(self, agent_id: str, action_type: str) -> None:
        """Record an agent action.

        Args:
            agent_id: The agent performing the action.
            action_type: Category/type of the action.
        """
        with self._lock:
            history = self._actions[agent_id]
            history.append(action_type)
            if len(history) > self._window_size * 2:
                # Keep extra for baseline comparison but don't grow unbounded
                self._actions[agent_id] = history[-(self._window_size * 2):]

    def snapshot_baseline(self, agent_id: str) -> dict[str, float]:
        """Snapshot the current action distribution as the baseline.

        Call this after an agent has been observed operating normally.

        Returns:
            The baseline distribution.
        """
        with self._lock:
            history = self._actions.get(agent_id, [])
            counts = Counter(history)
            dist = _to_distribution(counts)
            self._baselines[agent_id] = dist
            return dict(dist)

    def set_baseline(self, agent_id: str, distribution: dict[str, float]) -> None:
        """Set a baseline distribution manually.

        Args:
            agent_id: The agent.
            distribution: Action type -> probability mapping.
        """
        with self._lock:
            self._baselines[agent_id] = dict(distribution)

    def detect_drift(
        self,
        agent_id: str,
        window: int | None = None,
    ) -> DriftReport:
        """Check an agent for behavioral drift and reward gaming.

        Args:
            agent_id: The agent to check.
            window: Override the default window size for this check.

        Returns:
            DriftReport with divergence, entropy, and flags.
        """
        win = window or self._window_size

        with self._lock:
            history = list(self._actions.get(agent_id, []))
            baseline = dict(self._baselines.get(agent_id, {}))

        # Current distribution from recent window
        recent = history[-win:] if len(history) > win else history
        current_counts = Counter(recent)
        current_dist = _to_distribution(current_counts)

        # Compute divergence
        if baseline and current_dist:
            divergence = _js_divergence(baseline, current_dist)
        else:
            divergence = 0.0

        # Compute entropy for gaming detection
        entropy = _shannon_entropy(current_dist)

        return DriftReport(
            agent_id=agent_id,
            divergence=divergence,
            threshold=self._drift_threshold,
            drifted=divergence > self._drift_threshold,
            entropy=entropy,
            gaming=entropy < self._gaming_threshold and len(recent) >= 10,
            baseline_distribution=baseline,
            current_distribution=current_dist,
            total_actions=len(history),
            timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        )

    def clear(self, agent_id: str) -> None:
        """Clear action history and baseline for an agent."""
        with self._lock:
            self._actions.pop(agent_id, None)
            self._baselines.pop(agent_id, None)

    def agent_ids(self) -> list[str]:
        """List all agents with recorded actions."""
        with self._lock:
            return list(self._actions.keys())
