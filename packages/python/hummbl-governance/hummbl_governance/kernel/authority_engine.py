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

"""Authority Engine — K6 invariant enforcement.

Every authority exercise is scoped, limited, and leaves a receipt.
The Kernel verifies scope and limit before permitting exercise.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any



@dataclass
class AuthorityCheck:
    """Result of an authority check."""

    permitted: bool
    reason: str
    scope: str = ""
    limit: str = ""
    metric: str = ""


class AuthorityEngine:
    """Engine for verifying authority scope, limit, and logging exercise."""

    def __init__(self, state_dir: Path) -> None:
        self.state_dir = state_dir
        self.exercise_log = state_dir / "authority_exercises.jsonl"

    def check(
        self,
        agent_id: str,
        role_id: str,
        authority: str,
        context: dict[str, Any],
        role_charters_dir: Path | None = None,
    ) -> AuthorityCheck:
        """Check if an authority exercise is within scope and limit.

        Reads the role charter to determine scope and limit.
        Returns AuthorityCheck with permitted flag and reason.
        """
        charter_path = (role_charters_dir or Path("_internal/governance/ai-roles")) / f"{role_id}.md"
        if not charter_path.exists():
            return AuthorityCheck(
                permitted=False,
                reason=f"Role charter not found: {role_id}",
            )

        # Parse charter for authority section (simplified)
        charter_text = charter_path.read_text()
        authority_section = self._extract_authority_section(charter_text, authority)

        if not authority_section:
            return AuthorityCheck(
                permitted=False,
                reason=f"Authority '{authority}' not defined in {role_id} charter",
            )

        scope = authority_section.get("scope", "")
        limit = authority_section.get("limit", "")
        metric = authority_section.get("metric", "")

        # Check limit (simplified: parse "cannot" clauses)
        limit_violated = self._check_limit(context, limit)
        if limit_violated:
            return AuthorityCheck(
                permitted=False,
                reason=f"Limit violated: {limit_violated}",
                scope=scope,
                limit=limit,
                metric=metric,
            )

        return AuthorityCheck(
            permitted=True,
            reason="Authority exercise within scope and limit",
            scope=scope,
            limit=limit,
            metric=metric,
        )

    def _extract_authority_section(self, charter_text: str, authority: str) -> dict[str, str]:
        """Extract authority definition from markdown charter."""
        # Look for table row matching authority
        for line in charter_text.split("\n"):
            if authority in line and "|" in line:
                parts = [p.strip() for p in line.split("|")]
                if len(parts) >= 4:
                    return {
                        "authority": parts[1],
                        "scope": parts[2],
                        "limit": parts[3],
                        "metric": parts[4] if len(parts) > 4 else "",
                    }
        return {}

    def _check_limit(self, context: dict[str, Any], limit: str) -> str | None:
        """Check if context violates limit. Returns violation description or None."""
        if not limit:
            return None
        # Simple limit checks
        if "cannot" in limit.lower():
            # Parse "cannot X without Y"
            if "without" in limit.lower():
                required = limit.split("without")[-1].strip()
                if required.lower() not in str(context).lower():
                    return f"Missing required condition: {required}"
        return None

    def log_exercise(
        self,
        agent_id: str,
        role_id: str,
        authority: str,
        check: AuthorityCheck,
        receipt_id: str,
    ) -> None:
        """Log an authority exercise to the append-only log."""
        from datetime import datetime, timezone
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "agent_id": agent_id,
            "role_id": role_id,
            "authority": authority,
            "permitted": check.permitted,
            "reason": check.reason,
            "scope": check.scope,
            "limit": check.limit,
            "receipt_id": receipt_id,
        }
        with open(self.exercise_log, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, sort_keys=True) + "\n")

    def list_exercises(self, agent_id: str | None = None) -> list[dict[str, Any]]:
        """List authority exercises, optionally filtered by agent."""
        if not self.exercise_log.exists():
            return []
        exercises = []
        for line in self.exercise_log.read_text().strip().split("\n"):
            if line:
                entry = json.loads(line)
                if agent_id is None or entry.get("agent_id") == agent_id:
                    exercises.append(entry)
        return exercises
