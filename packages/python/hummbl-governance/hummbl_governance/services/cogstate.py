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

"""Cognitive State Manager -- tracks agent cognitive state transitions.

Provides a minimal, stdlib-only state machine for tracking cognitive states
(hyperfocus, transition, recovery, available, etc.) with a JSONL audit log.

Usage:
    from hummbl_governance.services.cogstate import (
        create_cogstate_manager, CogState,
    )
    from pathlib import Path

    mgr = create_cogstate_manager(state_dir=Path('_state/cognition'))
    print(mgr.current_state.value)
    mgr.transition(CogState.HYPERFOCUS, reason='deep work')
    print(mgr.current_record.record_id)

Stdlib-only: enum, json, pathlib, datetime, typing, dataclasses.
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class CogState(Enum):
    """Cognitive states an agent can be in."""

    AVAILABLE = "available"
    HYPERFOCUS = "hyperfocus"
    TRANSITION = "transition"
    RECOVERY = "recovery"
    DEPLETED = "depleted"
    OFFLINE = "offline"


@dataclass(frozen=True, slots=True)
class CogStateRecord:
    """A single cognitive state transition record."""

    record_id: str
    state: CogState
    previous_state: CogState | None
    timestamp: str
    reason: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


class CogStateManager:
    """Manages cognitive state transitions with a JSONL audit log.

    The state file is ``<state_dir>/cogstate.jsonl``. Each line is a JSON
    record of a state transition. The current state is the last record.
    """

    def __init__(self, state_dir: Path, *, filename: str = "cogstate.jsonl") -> None:
        self._state_dir = Path(state_dir)
        self._state_dir.mkdir(parents=True, exist_ok=True)
        self._state_file = self._state_dir / filename
        self._records: list[CogStateRecord] = []
        self._load()

    def _load(self) -> None:
        """Load existing records from the state file."""
        if not self._state_file.exists():
            self._records = []
            return
        with self._state_file.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    state = CogState(data["state"])
                    prev = CogState(data["previous_state"]) if data.get("previous_state") else None
                    rec = CogStateRecord(
                        record_id=data["record_id"],
                        state=state,
                        previous_state=prev,
                        timestamp=data["timestamp"],
                        reason=data.get("reason", ""),
                        metadata=data.get("metadata", {}),
                    )
                    self._records.append(rec)
                except (json.JSONDecodeError, KeyError, ValueError) as exc:
                    logger.warning("Skipping malformed cogstate record: %s", exc)

    def _persist(self, record: CogStateRecord) -> None:
        """Append a record to the state file atomically."""
        data = {
            "record_id": record.record_id,
            "state": record.state.value,
            "previous_state": record.previous_state.value if record.previous_state else None,
            "timestamp": record.timestamp,
            "reason": record.reason,
            "metadata": record.metadata,
        }
        line = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
        with self._state_file.open("a", encoding="utf-8") as f:
            f.write(line + "\n")
            f.flush()
            os.fsync(f.fileno())

    @property
    def current_state(self) -> CogState:
        """The current cognitive state (last record's state, or AVAILABLE)."""
        if not self._records:
            return CogState.AVAILABLE
        return self._records[-1].state

    @property
    def current_record(self) -> CogStateRecord:
        """The most recent state record.

        Returns a synthetic AVAILABLE record if no records exist.
        """
        if not self._records:
            return CogStateRecord(
                record_id="initial",
                state=CogState.AVAILABLE,
                previous_state=None,
                timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                reason="no records yet",
            )
        return self._records[-1]

    @property
    def history(self) -> list[CogStateRecord]:
        """All state transition records."""
        return list(self._records)

    def transition(
        self,
        new_state: CogState,
        *,
        reason: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> CogStateRecord:
        """Transition to a new cognitive state.

        Args:
            new_state: The target CogState.
            reason: Human-readable reason for the transition.
            metadata: Optional metadata dict.

        Returns:
            The new CogStateRecord.
        """
        prev = self.current_state
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        rid = f"cogstate-{len(self._records) + 1:06d}-{int(datetime.now(timezone.utc).timestamp())}"
        record = CogStateRecord(
            record_id=rid,
            state=new_state,
            previous_state=prev,
            timestamp=ts,
            reason=reason,
            metadata=metadata or {},
        )
        self._records.append(record)
        self._persist(record)
        logger.info("CogState transition: %s -> %s (%s)", prev.value, new_state.value, reason)
        return record


def create_cogstate_manager(state_dir: Path, *, filename: str = "cogstate.jsonl") -> CogStateManager:
    """Factory: create a CogStateManager for the given state directory.

    Args:
        state_dir: Directory where cogstate.jsonl lives.
        filename: Optional override for the state filename.

    Returns:
        A CogStateManager instance.
    """
    return CogStateManager(state_dir=Path(state_dir), filename=filename)
