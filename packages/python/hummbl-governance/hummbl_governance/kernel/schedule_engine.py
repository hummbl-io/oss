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

"""Schedule Engine — manages officer role loops.

Registers loops, tracks health, escalates if loops miss runs.
"""

from __future__ import annotations

import json
import threading
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass
class LoopSchedule:
    """A registered loop schedule."""

    schedule_id: str
    role_id: str
    cadence: str  # DAILY, WEEKLY, PER_PR, PER_RELEASE, PER_EVENT
    last_run: str = ""
    last_success: bool = True
    consecutive_misses: int = 0
    total_runs: int = 0
    total_success: int = 0


class ScheduleEngine:
    """Engine for registering and tracking officer role loops."""

    def __init__(self, state_dir: Path) -> None:
        self.state_dir = state_dir
        self.schedules_file = state_dir / "loop_schedules.jsonl"
        self._lock = threading.Lock()
        self.health_file = state_dir / "loop_health.json"
        self._schedules: dict[str, LoopSchedule] = {}
        self._load()

    def _load(self) -> None:
        """Load schedules from disk."""
        if self.schedules_file.exists():
            for line in self.schedules_file.read_text().strip().split("\n"):
                if line:
                    data = json.loads(line)
                    self._schedules[data["schedule_id"]] = LoopSchedule(**data)

    def _save(self) -> None:
        """Save schedules to disk."""
        with open(self.schedules_file, "w", encoding="utf-8") as f:
            for schedule in self._schedules.values():
                f.write(json.dumps(schedule.__dict__, sort_keys=True) + "\n")

    def register(
        self,
        role_id: str,
        cadence: str,
    ) -> str:
        """Register a loop for a role.

        Returns schedule_id.
        """
        import uuid
        schedule_id = f"sched-{uuid.uuid4().hex[:8]}"
        schedule = LoopSchedule(
            schedule_id=schedule_id,
            role_id=role_id,
            cadence=cadence,
        )
        with self._lock:
            self._schedules[schedule_id] = schedule
            self._save()
        return schedule_id

    def record_run(self, schedule_id: str, success: bool) -> LoopSchedule:
        """Record a loop run outcome."""
        schedule = self._schedules.get(schedule_id)
        if not schedule:
            raise ValueError(f"Schedule {schedule_id} not found")

        with self._lock:
            schedule.last_run = datetime.now(timezone.utc).isoformat()
            schedule.last_success = success
            schedule.total_runs += 1
            if success:
                schedule.consecutive_misses = 0
                schedule.total_success += 1
            else:
                schedule.consecutive_misses += 1

            self._save()
        return schedule

    def check_health(self, schedule_id: str) -> dict[str, Any]:
        """Check loop health and return status.

        Escalates if consecutive_misses >= 3.
        """
        schedule = self._schedules.get(schedule_id)
        if not schedule:
            return {"status": "NOT_FOUND", "escalate": True}

        if schedule.consecutive_misses >= 3:
            return {
                "status": "UNHEALTHY",
                "escalate": True,
                "consecutive_misses": schedule.consecutive_misses,
                "last_run": schedule.last_run,
            }

        if schedule.total_runs == 0:
            return {"status": "PENDING", "escalate": False}

        success_rate = schedule.total_success / schedule.total_runs
        if success_rate < 0.80:
            return {
                "status": "DEGRADED",
                "escalate": False,
                "success_rate": success_rate,
            }

        return {
            "status": "HEALTHY",
            "escalate": False,
            "success_rate": success_rate,
        }

    def list_schedules(self, role_id: str | None = None) -> list[LoopSchedule]:
        """List all schedules, optionally filtered by role."""
        if role_id:
            return [s for s in self._schedules.values() if s.role_id == role_id]
        return list(self._schedules.values())
