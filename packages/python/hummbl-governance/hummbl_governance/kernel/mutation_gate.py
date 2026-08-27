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

"""Pre-Mutation Gate - intercepts GitHub API mutations and enforces
authority + two-person rule before execution.

Gap-1 (issue #406): AuthorityEngine.check() and AdmissionControl had
zero production call sites. This gate is the integration point.

NIST 800-53 AC-3 (Access Enforcement), AC-5 (Separation of Duties),
CM-5 (Access Restrictions for Change), DoD Zero Trust "Verify Explicit
Access."

Operator decision (2026-08-27): pluggable identity resolver ΓÇö ship with
string-lookup default, gap-3 swaps in cryptographic proof as a new
resolver implementation without gate changes.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Protocol


class MutationSeverity(Enum):
    """Severity classification for GitHub API mutations."""

    LOW = "LOW"          # read-only, bus post, status check
    MEDIUM = "MEDIUM"    # commit, PR creation, branch creation
    HIGH = "HIGH"        # archive, delete, force-push, secret rotation
    CRITICAL = "CRITICAL"  # org-level change, key rotation, branch protection removal


@dataclass
class GateDecision:
    """Result of a pre-mutation gate check."""

    permitted: bool
    reason: str
    severity: MutationSeverity
    agent_id: str = ""
    authority_check: Any = None
    decision_receipt_required: bool = False
    decision_receipt_provided: bool = False
    receipt_id: str = ""


class IdentityResolver(Protocol):
    """Pluggable identity resolver interface.

    Gap-1 ships with StringLookupResolver (wraps IdentityEngine.resolve).
    Gap-3 will provide CryptographicIdentityResolver that adds
    cryptographic proof-of-identity ΓÇö no gate changes needed.
    """

    def resolve(self, agent_id: str) -> Any:
        """Resolve an agent identity. Returns an identity object or None.

        The returned object must have a `trust_tier` attribute (int or str)
        and an `agent_id` attribute. None means identity not found.
        """
        ...


class StringLookupResolver:
    """Default identity resolver ΓÇö wraps IdentityEngine.resolve().

    This is the current string-lookup identity resolution. Gap-3 will
    replace this with CryptographicIdentityResolver.
    """

    def __init__(self, identity_engine: Any) -> None:
        self._engine = identity_engine

    def resolve(self, agent_id: str) -> Any:
        return self._engine.resolve(agent_id)


# --- Mutation classification ------------------------------------------------

# GitHub API operations mapped to severity.
# Keys are (operation_category, action) tuples.
# operation_category: "repo", "branch", "issue", "pr", "org", "secret"
# action: the specific API action (e.g., "archive", "delete", "merge")

_HIGH_ACTIONS: set[str] = {
    "archive",           # repo archive
    "delete",            # repo/branch/file deletion
    "force_push",        # force-push to protected branch
    "secret_rotation",   # secret rotation
    "remove_protection",  # remove branch protection
}

_CRITICAL_ACTIONS: set[str] = {
    "org_level_change",   # org-level setting change
    "key_rotation",       # signing key rotation
    "remove_force_push_protection",  # disable force-push protection
}

_MEDIUM_ACTIONS: set[str] = {
    "commit",            # push commits
    "create_pr",         # create pull request
    "merge_pr",          # merge pull request (non-force)
    "create_branch",     # create branch
    "label",             # add/remove labels
    "close_issue",       # close issue
}

# Everything else defaults to LOW


def classify_mutation(operation: str, action: str) -> MutationSeverity:
    """Classify a GitHub API mutation by severity.

    Args:
        operation: The operation category (repo, branch, issue, pr, org, secret).
        action: The specific action being performed.

    Returns:
        MutationSeverity for the mutation.
    """
    if action in _CRITICAL_ACTIONS:
        return MutationSeverity.CRITICAL
    if action in _HIGH_ACTIONS:
        return MutationSeverity.HIGH
    if action in _MEDIUM_ACTIONS:
        return MutationSeverity.MEDIUM
    return MutationSeverity.LOW


# --- Pre-Mutation Gate ------------------------------------------------------


class PreMutationGate:
    """Gate that intercepts GitHub API mutations and enforces authority.

    Flow:
        1. Resolve agent identity via pluggable resolver
        2. Classify mutation severity
        3. Check authority via AuthorityEngine.check()
        4. Require operator DECISION receipt for HIGH/CRITICAL actions
        5. Return GateDecision

    Usage:
        gate = PreMutationGate(
            identity_resolver=StringLookupResolver(identity_engine),
            authority_engine=authority_engine,
        )
        decision = gate.check(
            agent_id="devin",
            role_id="devin",
            authority="github_mutation",
            operation="repo",
            action="archive",
            context={"repo": "hummbl-governance"},
        )
        if not decision.permitted:
            raise PermissionError(decision.reason)
    """

    def __init__(
        self,
        identity_resolver: IdentityResolver,
        authority_engine: Any,
        role_charters_dir: Any = None,
    ) -> None:
        self._resolver = identity_resolver
        self._authority = authority_engine
        self._role_charters_dir = role_charters_dir

    def check(
        self,
        agent_id: str,
        role_id: str,
        authority: str,
        operation: str,
        action: str,
        context: dict[str, Any] | None = None,
        decision_receipt: str | None = None,
    ) -> GateDecision:
        """Check if a GitHub API mutation is permitted.

        Args:
            agent_id: The agent attempting the mutation.
            role_id: The role of the agent (for charter lookup).
            authority: The authority being exercised (e.g., "github_mutation").
            operation: Operation category (repo, branch, issue, pr, org, secret).
            action: Specific action (archive, delete, merge, force_push, etc.).
            context: Additional context for authority check.
            decision_receipt: Operator DECISION receipt ID for HIGH/CRITICAL
                actions (two-person rule). None if not provided.

        Returns:
            GateDecision indicating whether the mutation is permitted.
        """
        context = context or {}
        severity = classify_mutation(operation, action)

        # Step 1: Resolve identity
        identity = self._resolver.resolve(agent_id)
        if identity is None:
            return GateDecision(
                permitted=False,
                reason=f"Identity not found: {agent_id}",
                severity=severity,
                agent_id=agent_id,
            )

        # Step 2: Check authority
        authority_check = self._authority.check(
            agent_id=agent_id,
            role_id=role_id,
            authority=authority,
            context={**context, "operation": operation, "action": action, "severity": severity.value},
            role_charters_dir=self._role_charters_dir,
        )

        if not authority_check.permitted:
            return GateDecision(
                permitted=False,
                reason=f"Authority denied: {authority_check.reason}",
                severity=severity,
                agent_id=agent_id,
                authority_check=authority_check,
            )

        # Step 3: Two-person rule for HIGH/CRITICAL
        if severity in (MutationSeverity.HIGH, MutationSeverity.CRITICAL):
            if not decision_receipt:
                return GateDecision(
                    permitted=False,
                    reason=(
                        f"{severity.value} mutation requires operator DECISION "
                        f"receipt (two-person rule). action={action}"
                    ),
                    severity=severity,
                    agent_id=agent_id,
                    authority_check=authority_check,
                    decision_receipt_required=True,
                    decision_receipt_provided=False,
                )
            # Receipt provided ΓÇö record it
            return GateDecision(
                permitted=True,
                reason=f"{severity.value} mutation permitted with DECISION receipt",
                severity=severity,
                agent_id=agent_id,
                authority_check=authority_check,
                decision_receipt_required=True,
                decision_receipt_provided=True,
                receipt_id=decision_receipt,
            )

        # LOW/MEDIUM ΓÇö authority check is sufficient
        return GateDecision(
            permitted=True,
            reason=f"{severity.value} mutation permitted",
            severity=severity,
            agent_id=agent_id,
            authority_check=authority_check,
        )
