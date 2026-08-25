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

"""Contract Net Protocol -- Market-based task allocation for multi-agent systems.

Implements the Contract Net Protocol (Smith 1980, refined by Durfee 2001)
for decentralized task allocation. An announcer broadcasts a task, agents
submit bids, and the best bid wins a delegation token.

Flow:
    1. Announcer posts TaskAnnouncement (requirements, deadline)
    2. Agents submit Bids (cost, capability_score, estimated_time)
    3. Announcer evaluates bids via configurable strategy
    4. Winner is awarded the task

Usage::

    from hummbl_governance.contract_net import ContractNetManager, TaskAnnouncement, Bid

    mgr = ContractNetManager()
    ann_id = mgr.announce("orchestrator", "parse-invoices",
                          requirements={"skill": "ocr"}, deadline_seconds=30)
    mgr.submit_bid(ann_id, Bid(bidder="worker-1", cost=0.5, capability=0.9))
    mgr.submit_bid(ann_id, Bid(bidder="worker-2", cost=0.3, capability=0.7))
    winner = mgr.evaluate(ann_id)  # worker-2 (lowest cost)

Stdlib-only. Thread-safe.

Reference:
    Durfee, E. H. (2001). Distributed Problem Solving and Planning.
    LNCS 2086, pp. 118-149. DOI: 10.1007/3-540-47745-4_6
"""

from __future__ import annotations

import threading
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable


class ContractPhase(Enum):
    """Phases of the Contract Net Protocol."""

    ANNOUNCED = "announced"
    BIDDING = "bidding"
    AWARDED = "awarded"
    EXECUTING = "executing"
    COMPLETE = "complete"
    FAILED = "failed"
    EXPIRED = "expired"


@dataclass(frozen=True)
class Bid:
    """A bid submitted by an agent for a task."""

    bidder: str
    cost: float = 0.0
    capability: float = 1.0
    estimated_seconds: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def cost_capability_ratio(self) -> float:
        """Lower is better: cost per unit of capability."""
        if self.capability <= 0:
            return float("inf")
        return self.cost / self.capability


@dataclass
class TaskAnnouncement:
    """A task announced to the agent pool."""

    announcement_id: str
    announcer: str
    task_id: str
    requirements: dict[str, Any]
    deadline_seconds: float
    phase: ContractPhase
    created_at: float  # monotonic time
    bids: list[Bid] = field(default_factory=list)
    winner: Bid | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def is_expired(self) -> bool:
        """Check if the bidding deadline has passed."""
        return (time.monotonic() - self.created_at) >= self.deadline_seconds


# Built-in evaluation strategies
def _strategy_lowest_cost(bids: list[Bid]) -> Bid | None:
    """Select the bid with the lowest cost."""
    return min(bids, key=lambda b: b.cost) if bids else None


def _strategy_highest_capability(bids: list[Bid]) -> Bid | None:
    """Select the bid with the highest capability score."""
    return max(bids, key=lambda b: b.capability) if bids else None


def _strategy_best_ratio(bids: list[Bid]) -> Bid | None:
    """Select the bid with the best cost/capability ratio."""
    return min(bids, key=lambda b: b.cost_capability_ratio) if bids else None


_STRATEGIES: dict[str, Callable[[list[Bid]], Bid | None]] = {
    "lowest_cost": _strategy_lowest_cost,
    "highest_capability": _strategy_highest_capability,
    "best_ratio": _strategy_best_ratio,
}


class ContractNetManager:
    """Manages the Contract Net Protocol lifecycle.

    Thread-safe. Supports multiple concurrent task announcements.

    Args:
        min_trust_tier: Minimum trust tier name for bidders (informational;
            enforcement is the caller's responsibility via AgentRegistry).
        default_strategy: Default bid evaluation strategy.
    """

    def __init__(
        self,
        min_trust_tier: str = "low",
        default_strategy: str = "lowest_cost",
    ) -> None:
        self._announcements: dict[str, TaskAnnouncement] = {}
        self._min_trust_tier = min_trust_tier
        self._default_strategy = default_strategy
        self._lock = threading.Lock()

    def announce(
        self,
        announcer: str,
        task_id: str,
        requirements: dict[str, Any] | None = None,
        deadline_seconds: float = 30.0,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """Announce a task for bidding.

        Args:
            announcer: Agent posting the task.
            task_id: Identifier for the task.
            requirements: Capability requirements for bidders.
            deadline_seconds: Bidding window duration.
            metadata: Additional task metadata.

        Returns:
            announcement_id for submitting bids.
        """
        ann_id = str(uuid.uuid4())
        announcement = TaskAnnouncement(
            announcement_id=ann_id,
            announcer=announcer,
            task_id=task_id,
            requirements=requirements or {},
            deadline_seconds=deadline_seconds,
            phase=ContractPhase.ANNOUNCED,
            created_at=time.monotonic(),
            metadata=metadata or {},
        )
        with self._lock:
            self._announcements[ann_id] = announcement
            announcement.phase = ContractPhase.BIDDING
        return ann_id

    def submit_bid(self, announcement_id: str, bid: Bid) -> bool:
        """Submit a bid for a task.

        Args:
            announcement_id: The announcement to bid on.
            bid: The bid to submit.

        Returns:
            True if bid was accepted, False if announcement not found,
            expired, or not in bidding phase.
        """
        with self._lock:
            ann = self._announcements.get(announcement_id)
            if ann is None:
                return False
            if ann.phase != ContractPhase.BIDDING:
                return False
            if ann.is_expired:
                ann.phase = ContractPhase.EXPIRED
                return False
            ann.bids.append(bid)
            return True

    def evaluate(
        self,
        announcement_id: str,
        strategy: str | None = None,
    ) -> Bid | None:
        """Evaluate bids and select a winner.

        Args:
            announcement_id: The announcement to evaluate.
            strategy: Evaluation strategy name ("lowest_cost",
                "highest_capability", "best_ratio"). Defaults to
                the manager's default_strategy.

        Returns:
            The winning Bid, or None if no valid bids.

        Raises:
            KeyError: If announcement_id not found.
            ValueError: If strategy name is unknown.
        """
        strat_name = strategy or self._default_strategy
        strat_fn = _STRATEGIES.get(strat_name)
        if strat_fn is None:
            raise ValueError(
                f"Unknown strategy {strat_name!r}. "
                f"Available: {', '.join(_STRATEGIES)}"
            )

        with self._lock:
            ann = self._announcements.get(announcement_id)
            if ann is None:
                raise KeyError(f"Announcement {announcement_id!r} not found")

            if not ann.bids:
                ann.phase = ContractPhase.FAILED
                return None

            winner = strat_fn(ann.bids)
            if winner is not None:
                ann.winner = winner
                ann.phase = ContractPhase.AWARDED
            else:
                ann.phase = ContractPhase.FAILED
            return winner

    def complete(self, announcement_id: str) -> None:
        """Mark a task as complete."""
        with self._lock:
            ann = self._announcements.get(announcement_id)
            if ann is not None:
                ann.phase = ContractPhase.COMPLETE

    def fail(self, announcement_id: str) -> None:
        """Mark a task as failed."""
        with self._lock:
            ann = self._announcements.get(announcement_id)
            if ann is not None:
                ann.phase = ContractPhase.FAILED

    def get_announcement(self, announcement_id: str) -> TaskAnnouncement | None:
        """Retrieve an announcement by ID."""
        with self._lock:
            return self._announcements.get(announcement_id)

    def get_phase(self, announcement_id: str) -> ContractPhase | None:
        """Get the current phase of an announcement."""
        with self._lock:
            ann = self._announcements.get(announcement_id)
            return ann.phase if ann else None

    def list_active(self) -> list[TaskAnnouncement]:
        """List all announcements in BIDDING phase."""
        with self._lock:
            return [
                a for a in self._announcements.values()
                if a.phase == ContractPhase.BIDDING and not a.is_expired
            ]

    def summary(self) -> dict[str, int]:
        """Count announcements by phase."""
        counts: dict[str, int] = {}
        with self._lock:
            for ann in self._announcements.values():
                phase = ann.phase.value
                counts[phase] = counts.get(phase, 0) + 1
        return counts
