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

from hummbl_governance.regulatory_context import RegulatoryContext



@dataclass
class AuthorityCheck:
    """Result of an authority check."""

    permitted: bool
    reason: str
    scope: str = ""
    limit: str = ""
    metric: str = ""
    regulatory_profile: str = ""
    regulatory_controls: list[str] | None = None


class AuthorityEngine:
    """Engine for verifying authority scope, limit, and logging exercise."""

    # Default path to the structured authority policy JSON.
    # When present, the engine reads from this instead of scraping markdown charters.
    _DEFAULT_POLICY_PATH = Path(__file__).parent.parent / "data" / "authority_policy.json"

    def __init__(self, state_dir: Path, policy_path: Path | None = None) -> None:
        self.state_dir = state_dir
        self.exercise_log = state_dir / "authority_exercises.jsonl"
        self.policy_path = policy_path or self._DEFAULT_POLICY_PATH
        self._policy_cache: dict[str, Any] | None = None
        self._regulatory_ctx: RegulatoryContext | None = None

    def _load_policy(self) -> dict[str, Any] | None:
        """Load the structured authority policy JSON.

        Returns None if the policy file does not exist (falls back to charter mode).
        """
        if self._policy_cache is not None:
            return self._policy_cache
        if not self.policy_path.exists():
            return None
        with open(self.policy_path, encoding="utf-8") as f:
            self._policy_cache = json.load(f)
        return self._policy_cache

    def check(
        self,
        agent_id: str,
        role_id: str,
        authority: str,
        context: dict[str, Any],
        role_charters_dir: Path | None = None,
    ) -> AuthorityCheck:
        """Check if an authority exercise is within scope and limit.

        Resolution order:
        1. Structured policy JSON (authority_policy.json) — preferred
        2. Markdown charter files — fallback for backward compatibility

        Returns AuthorityCheck with permitted flag and reason.
        """
        policy = self._load_policy()
        if policy is not None:
            return self._check_structured(policy, role_id, authority, context)
        return self._check_charter(role_id, authority, context, role_charters_dir)

    def _check_structured(
        self, policy: dict[str, Any], role_id: str, authority: str, context: dict[str, Any]
    ) -> AuthorityCheck:
        """Check authority against the structured JSON policy."""
        roles = policy.get("roles", {})
        role_def = roles.get(role_id)
        if role_def is None:
            return AuthorityCheck(
                permitted=False,
                reason=f"Role '{role_id}' not defined in authority policy",
            )

        # Determine the mutation class for this authority
        mutation_classes = policy.get("mutation_classes", {})
        authority_class = self._classify_authority(authority, mutation_classes)
        if authority_class is None:
            # Unknown authority — default to HIGH (fail-safe)
            authority_class = "HIGH"

        # Check if the role can authorize this class
        can_authorize = role_def.get("can_authorize", [])
        if authority_class not in can_authorize:
            return AuthorityCheck(
                permitted=False,
                reason=(
                    f"Role '{role_id}' (tier {role_def.get('trust_tier', 'unknown')}) "
                    f"cannot authorize {authority_class} mutations (authority: {authority})"
                ),
                scope=role_def.get("scope", ""),
                limit="; ".join(role_def.get("limits", [])),
            )

        # Check limits
        limits = role_def.get("limits", [])
        for limit in limits:
            violation = self._check_structured_limit(limit, authority_class, context)
            if violation:
                return AuthorityCheck(
                    permitted=False,
                    reason=f"Limit violated: {violation}",
                    scope=role_def.get("scope", ""),
                    limit=limit,
                )

        # Regulatory check: verify action is not prohibited by regulatory profile
        regulatory_profile = role_def.get("regulatory_profile", "")
        if regulatory_profile:
            reg_result = self._check_regulatory(regulatory_profile, authority)
            if not reg_result.permitted:
                return AuthorityCheck(
                    permitted=False,
                    reason=f"Regulatory violation: {reg_result.reason}",
                    scope=role_def.get("scope", ""),
                    limit="; ".join(limits),
                    regulatory_profile=regulatory_profile,
                )
            return AuthorityCheck(
                permitted=True,
                reason=f"Authority '{authority}' ({authority_class}) within scope for role '{role_id}'",
                scope=role_def.get("scope", ""),
                limit="; ".join(limits),
                regulatory_profile=regulatory_profile,
                regulatory_controls=(
                    list(reg_result.applicable_controls.to_dict().keys())
                    if reg_result.applicable_controls
                    else None
                ),
            )
        return AuthorityCheck(
            permitted=True,
            reason=f"Authority '{authority}' ({authority_class}) within scope for role '{role_id}'",
            scope=role_def.get("scope", ""),
            limit="; ".join(limits),
        )

    def _check_regulatory(
        self, profile: str, authority: str
    ):
        """Check if an authority is permitted under the role regulatory profile."""
        if self._regulatory_ctx is None:
            self._regulatory_ctx = RegulatoryContext()
        return self._regulatory_ctx.check(profile, authority)

    def _classify_authority(
        self, authority: str, mutation_classes: dict[str, Any]
    ) -> str | None:
        """Classify an authority name into a mutation class.

        Checks the 'examples' list in each mutation class.
        """
        for class_name, class_def in mutation_classes.items():
            examples = class_def.get("examples", [])
            if authority in examples:
                return class_name
        return None

    def _check_structured_limit(
        self, limit: str, authority_class: str, context: dict[str, Any]
    ) -> str | None:
        """Check a structured limit string against the context.

        Returns violation description or None if no violation.

        Limits are only checked when they reference the current authority_class.
        For example, "cannot authorize HIGH without operator DECISION" only
        fires when authority_class is HIGH.
        """
        limit_lower = limit.lower()
        # Only check limits that reference the current authority class
        # e.g. "cannot authorize HIGH without..." only applies to HIGH mutations
        # e.g. "cannot authorize CRITICAL without..." only applies to CRITICAL mutations
        class_lower = authority_class.lower()
        if class_lower not in limit_lower:
            # This limit doesn't reference the current class — skip it
            return None
        # "cannot authorize X without Y"
        if "without" in limit_lower:
            required = limit.split("without")[-1].strip().rstrip(".")
            # Check if the required condition is met
            if "operator decision" in required.lower():
                if not context.get("operator_decision_receipt"):
                    return f"Missing required condition: {required}"
            if "two-person" in required.lower():
                if not context.get("second_approver_receipt"):
                    return f"Missing required condition: {required}"
        return None

    def _check_charter(
        self,
        role_id: str,
        authority: str,
        context: dict[str, Any],
        role_charters_dir: Path | None,
    ) -> AuthorityCheck:
        """Fallback: check authority against markdown charter files."""
        charter_path = (role_charters_dir or Path("_internal/governance/ai-roles")) / f"{role_id}.md"
        if not charter_path.exists():
            return AuthorityCheck(
                permitted=False,
                reason=f"Role charter not found: {role_id}",
            )

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
