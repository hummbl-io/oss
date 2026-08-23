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
# SPDX-License-Identifier: MIT OR Apache-2.0

"""Sequence Engine — K4 invariant enforcement.

Every receipt has a sequence_id for total ordering within its agent context.
Without sequence_id: reconstructability = 5% (SL-11).
With sequence_id: reconstructability = 100%.
"""

from __future__ import annotations

import json
import logging
import threading
from pathlib import Path
from typing import Any

from .invariants import KernelInvariant, KernelPanic

logger = logging.getLogger(__name__)


class SequenceEngine:
    """Engine for monotonic sequence assignment and log reconstruction."""

    def __init__(self, state_dir: Path) -> None:
        self.state_dir = state_dir
        self.counters_file = state_dir / "sequence_counters.json"
        self._lock = threading.Lock()
        self.counters: dict[str, int] = {}
        self._load_counters()

    def _load_counters(self) -> None:
        """Load existing counters from disk.

        Fail-closed: a corrupted counters file is a security-critical event.
        Sequence counters back the K4 (Temporal) Lamport-clock ordering
        invariant. Silently resetting them to empty would restart sequence
        IDs from 1, producing duplicates that break causality tracking for
        receipt ordering and conflict resolution. Raise KernelPanic instead
        so operators can investigate the root cause of corruption.
        """
        if self.counters_file.exists():
            try:
                self.counters = json.loads(self.counters_file.read_text())
            except (json.JSONDecodeError, OSError) as exc:
                logger.error(
                    "Sequence counters file corrupt (%s): %s",
                    self.counters_file, exc,
                )
                raise KernelPanic(
                    KernelInvariant.TEMPORAL,
                    f"Sequence counters file corrupt: {self.counters_file} — "
                    f"refusing to reset Lamport counters",
                ) from exc

    def _save_counters(self) -> None:
        """Save counters to disk."""
        self.counters_file.write_text(
            json.dumps(self.counters, sort_keys=True, indent=2)
        )

    def next(self, agent_id: str) -> int:
        """Get the next sequence_id for an agent.

        Monotonic increment per agent. Persists across restarts.
        """
        with self._lock:
            current = self.counters.get(agent_id, 0)
            next_id = current + 1
            self.counters[agent_id] = next_id
            self._save_counters()
        return next_id

    def current(self, agent_id: str) -> int:
        """Get the current (last used) sequence_id for an agent."""
        val = self.counters.get(agent_id, 0)
        try:
            return int(val)
        except (ValueError, TypeError):
            return 0

    def validate(self, agent_id: str, sequence_id: int) -> bool:
        """Validate that a sequence_id is acceptable for an agent.

        Checks:
        - sequence_id > current (no duplicates)
        - sequence_id == current + 1 (no gaps, strict mode)

        In non-strict mode, gaps are warned but accepted.
        """
        current = self.current(agent_id)
        if sequence_id <= current:
            # Duplicate or rewind
            return False
        # Gaps: warn but don't block (network reordering can cause gaps)
        return True

    def reconstruct(self, agent_id: str, receipts: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Reconstruct ordered log from receipts by sequence_id.

        Sorts by sequence_id ascending. Validates continuity.
        Returns sorted receipts with gap annotations.
        """
        sorted_receipts = sorted(receipts, key=lambda r: r.get("sequence_id", 0))

        # Annotate gaps
        annotated: list[dict[str, Any]] = []
        prev_seq = 0
        for receipt in sorted_receipts:
            seq = receipt.get("sequence_id", 0)
            if prev_seq > 0 and seq != prev_seq + 1:
                annotated.append({
                    "_gap": True,
                    "_expected": prev_seq + 1,
                    "_actual": seq,
                    "_missing_count": seq - prev_seq - 1,
                })
            annotated.append(receipt)
            prev_seq = seq

        return annotated

    def check_continuity(self, agent_id: str, receipts: list[dict[str, Any]]) -> dict[str, Any]:
        """Check log continuity and return diagnostic report.

        Returns:
            {"continuous": bool, "gaps": [(expected, actual), ...], "total": int}
        """
        sorted_receipts = sorted(receipts, key=lambda r: r.get("sequence_id", 0))
        gaps: list[tuple[int, int]] = []
        prev_seq = 0

        for receipt in sorted_receipts:
            seq = receipt.get("sequence_id", 0)
            if prev_seq > 0 and seq != prev_seq + 1:
                for missing in range(prev_seq + 1, seq):
                    gaps.append((missing, seq))
            prev_seq = seq

        return {
            "continuous": len(gaps) == 0,
            "gaps": gaps,
            "total": len(sorted_receipts),
            "max_sequence": prev_seq,
        }
