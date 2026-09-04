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

"""Pre-Mutation Gate — intercepts mutations before execution.

Wires the authority engine and approval system into a single gate that
every mutation must pass through. Classifies mutations by risk level,
enforces authority checks, requires operator DECISION receipts for HIGH
actions, and logs every exercise.

This closes gap-1 (#406): the authority engine had zero production call
sites. This module provides the call site.

Mutation classification:
    LOW      — read-only, bus post, receipt creation
    MEDIUM   — commit, PR creation, file write within scope
    HIGH     — archive, delete, force-push, secret rotation, branch protection change
    CRITICAL — org-level change, key rotation, production deploy

Enforcement:
    LOW      — logged, no authority check required
    MEDIUM   — authority check + logged
    HIGH     — authority check + operator DECISION receipt + logged
    CRITICAL — authority check + operator DECISION receipt + two-person rule + logged
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import auto
from typing import Any, Callable, TypeVar

from hummbl_governance.kernel.authority_engine import AuthorityCheck

T = TypeVar("T")


class MutationRisk(auto):
    """Risk classification for mutations."""


class MutationLevel:
    """Mutation risk levels (mirrors RiskLevel from _types but independent)."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


# Mutation type → risk level mapping
_MUTATION_RISK_MAP: dict[str, str] = {
    # LOW — no authority check required
    "bus_post": MutationLevel.LOW,
    "receipt_create": MutationLevel.LOW,
    "file_read": MutationLevel.LOW,
    "status_update": MutationLevel.LOW,
    # MEDIUM — authority check required
    "commit": MutationLevel.MEDIUM,
    "pr_create": MutationLevel.MEDIUM,
    "pr_review": MutationLevel.MEDIUM,
    "file_write": MutationLevel.MEDIUM,
    "branch_create": MutationLevel.MEDIUM,
    "issue_create": MutationLevel.MEDIUM,
    "issue_comment": MutationLevel.MEDIUM,
    # HIGH — authority check + operator DECISION receipt
    "pr_merge": MutationLevel.HIGH,
    "archive_repo": MutationLevel.HIGH,
    "delete_file": MutationLevel.HIGH,
    "delete_branch": MutationLevel.HIGH,
    "force_push": MutationLevel.HIGH,
    "branch_protection_change": MutationLevel.HIGH,
    "secret_rotation": MutationLevel.HIGH,
    "kill_switch_activate": MutationLevel.HIGH,
    # CRITICAL — authority check + operator DECISION + two-person
    "org_change": MutationLevel.CRITICAL,
    "key_rotation": MutationLevel.CRITICAL,
    "production_deploy": MutationLevel.CRITICAL,
    "doctrine_amendment": MutationLevel.CRITICAL,
}


@dataclass
class MutationRequest:
    """A request to perform a mutation."""

    mutation_type: str
    agent_id: str
    role_id: str
    target: str  # repo, file path, or resource identifier
    context: dict[str, Any] = field(default_factory=dict)
    operator_decision_receipt: str | None = None  # bus receipt ID for HIGH/CRITICAL
    second_approver_receipt: str | None = None  # for CRITICAL two-person rule


@dataclass
class GateResult:
    """Result of a pre-mutation gate check."""

    permitted: bool
    risk_level: str
    reason: str
    authority_check: AuthorityCheck | None = None
    receipt_id: str = ""
    logged: bool = False


class MutationGate:
    """Pre-mutation gate that enforces authority checks before mutations.

    Usage:
        gate = MutationGate(kernel)
        result = gate.check(MutationRequest(
            mutation_type="archive_repo",
            agent_id="devin",
            role_id="primary_agent",
            target="hummbl-governance",
            operator_decision_receipt="bus:2026-08-31T23:00:00Z",
        ))
        if not result.permitted:
            raise PermissionError(f"Mutation blocked: {result.reason}")
        # proceed with mutation
    """

    def __init__(self, kernel: Any) -> None:
        """Initialize the gate with a Kernel instance.

        Args:
            kernel: A booted Kernel instance with authority and receipt engines.
        """
        self.kernel = kernel
        self.authority = kernel.authority
        self.gate_log = kernel.state_dir / "mutation_gate.jsonl"

    def classify(self, mutation_type: str) -> str:
        """Classify a mutation type by risk level.

        Args:
            mutation_type: The type of mutation (e.g. "commit", "archive_repo").

        Returns:
            Risk level string: LOW, MEDIUM, HIGH, or CRITICAL.
        """
        return _MUTATION_RISK_MAP.get(mutation_type, MutationLevel.HIGH)

    def check(self, request: MutationRequest) -> GateResult:
        """Check if a mutation is permitted.

        This is the main entry point. Every mutation in production code must
        pass through this method before executing.

        Args:
            request: The mutation request with agent, role, target, and context.

        Returns:
            GateResult with permitted flag and reason.
        """
        risk_level = self.classify(request.mutation_type)

        # LOW mutations: log and permit
        if risk_level == MutationLevel.LOW:
            result = GateResult(
                permitted=True,
                risk_level=risk_level,
                reason="LOW risk mutation — logged without authority check",
            )
            self._log(request, result)
            return result

        # MEDIUM+ mutations: require authority check
        authority_name = self._mutation_to_authority(request.mutation_type)
        check = self.kernel.exercise_authority(
            agent_id=request.agent_id,
            role_id=request.role_id,
            authority=authority_name,
            context=request.context,
        )

        if not check.permitted:
            result = GateResult(
                permitted=False,
                risk_level=risk_level,
                reason=f"Authority check failed: {check.reason}",
                authority_check=check,
            )
            self._log(request, result)
            return result

        # HIGH mutations: require operator DECISION receipt
        if risk_level == MutationLevel.HIGH:
            if not request.operator_decision_receipt:
                result = GateResult(
                    permitted=False,
                    risk_level=risk_level,
                    reason="HIGH risk mutation requires operator DECISION receipt — none provided",
                    authority_check=check,
                )
                self._log(request, result)
                return result
            # Verify the receipt exists in the bus (simplified: check non-empty)
            if not self._verify_decision_receipt(request.operator_decision_receipt):
                result = GateResult(
                    permitted=False,
                    risk_level=risk_level,
                    reason=f"Operator DECISION receipt not verified: {request.operator_decision_receipt}",
                    authority_check=check,
                )
                self._log(request, result)
                return result

        # CRITICAL mutations: require operator DECISION + two-person rule
        if risk_level == MutationLevel.CRITICAL:
            if not request.operator_decision_receipt:
                result = GateResult(
                    permitted=False,
                    risk_level=risk_level,
                    reason="CRITICAL risk mutation requires operator DECISION receipt — none provided",
                    authority_check=check,
                )
                self._log(request, result)
                return result
            if not request.second_approver_receipt:
                result = GateResult(
                    permitted=False,
                    risk_level=risk_level,
                    reason="CRITICAL risk mutation requires second approver (two-person rule) — none provided",
                    authority_check=check,
                )
                self._log(request, result)
                return result
            if not self._verify_decision_receipt(request.operator_decision_receipt):
                result = GateResult(
                    permitted=False,
                    risk_level=risk_level,
                    reason=f"Operator DECISION receipt not verified: {request.operator_decision_receipt}",
                    authority_check=check,
                )
                self._log(request, result)
                return result
            if not self._verify_decision_receipt(request.second_approver_receipt):
                result = GateResult(
                    permitted=False,
                    risk_level=risk_level,
                    reason=f"Second approver receipt not verified: {request.second_approver_receipt}",
                    authority_check=check,
                )
                self._log(request, result)
                return result

        # All checks passed
        result = GateResult(
            permitted=True,
            risk_level=risk_level,
            reason=f"{risk_level} risk mutation permitted — authority verified",
            authority_check=check,
            receipt_id=getattr(check, "_receipt_id", ""),
        )
        self._log(request, result)
        return result

    def guard(
        self,
        request: MutationRequest,
        action: Callable[[], T],
    ) -> T:
        """Execute an action only if the gate permits it.

        This is the convenience wrapper for synchronous mutation paths.

        Args:
            request: The mutation request.
            action: A callable that performs the mutation.

        Returns:
            The result of the action.

        Raises:
            PermissionError: If the gate blocks the mutation.
        """
        result = self.check(request)
        if not result.permitted:
            raise PermissionError(
                f"Mutation gate blocked {request.mutation_type} on {request.target}: {result.reason}"
            )
        return action()

    def _mutation_to_authority(self, mutation_type: str) -> str:
        """Map a mutation type to an authority name for charter lookup.

        The authority name is the mutation_type itself — role charters define
        which authorities each role can exercise.
        """
        return mutation_type

    def _verify_decision_receipt(self, receipt_id: str) -> bool:
        """Verify that a DECISION receipt exists.

        In production, this checks the coordination bus for a DECISION message
        with the given receipt ID. For now, we check that the ID is non-empty
        and follows the expected format.

        Args:
            receipt_id: The bus receipt ID to verify.

        Returns:
            True if the receipt appears valid.
        """
        if not receipt_id or not receipt_id.strip():
            return False
        # Accept bus: prefix or any non-empty string >= 8 chars
        # Full implementation would query the bus bridge
        return len(receipt_id) >= 8

    def _log(self, request: MutationRequest, result: GateResult) -> None:
        """Log a gate decision to the append-only log."""
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "mutation_type": request.mutation_type,
            "agent_id": request.agent_id,
            "role_id": request.role_id,
            "target": request.target,
            "risk_level": result.risk_level,
            "permitted": result.permitted,
            "reason": result.reason,
            "operator_decision_receipt": request.operator_decision_receipt,
            "second_approver_receipt": request.second_approver_receipt,
        }
        self.gate_log.parent.mkdir(parents=True, exist_ok=True)
        with open(self.gate_log, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, sort_keys=True) + "\n")
        result.logged = True

    def list_decisions(
        self, agent_id: str | None = None, permitted: bool | None = None
    ) -> list[dict[str, Any]]:
        """List gate decisions, optionally filtered.

        Args:
            agent_id: Filter by agent.
            permitted: Filter by permitted/blocked.

        Returns:
            List of decision records.
        """
        if not self.gate_log.exists():
            return []
        decisions = []
        for line in self.gate_log.read_text().strip().split("\n"):
            if line:
                entry = json.loads(line)
                if agent_id is not None and entry.get("agent_id") != agent_id:
                    continue
                if permitted is not None and entry.get("permitted") != permitted:
                    continue
                decisions.append(entry)
        return decisions


__all__ = [
    "MutationGate",
    "MutationRequest",
    "GateResult",
    "MutationLevel",
]
