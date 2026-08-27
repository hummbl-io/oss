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

"""Tests for Pre-Mutation Gate (gap-1).

Verifies:
- Mutation classification (LOW/MEDIUM/HIGH/CRITICAL)
- Identity resolution via pluggable resolver
- Authority check integration
- Two-person rule: HIGH blocked without DECISION receipt, allowed with
- Pluggable resolver swap (gap-3 forward compatibility)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


from hummbl_governance.kernel.mutation_gate import (
    MutationSeverity,
    PreMutationGate,
    StringLookupResolver,
    classify_mutation,
)


# --- Test fixtures ----------------------------------------------------------


@dataclass
class MockIdentity:
    agent_id: str
    trust_tier: int


class MockAuthorityCheck:
    def __init__(self, permitted: bool, reason: str = "OK") -> None:
        self.permitted = permitted
        self.reason = reason
        self.scope = "test"
        self.limit = "test"
        self.metric = "test"


class MockAuthorityEngine:
    """Mock authority engine that always permits (or configured otherwise)."""

    def __init__(self, permitted: bool = True) -> None:
        self._permitted = permitted

    def check(self, **kwargs: Any) -> MockAuthorityCheck:
        return MockAuthorityCheck(permitted=self._permitted, reason="within scope")


class MockIdentityEngine:
    """Mock identity engine for StringLookupResolver."""

    def __init__(self, identities: dict[str, MockIdentity]) -> None:
        self._identities = identities

    def resolve(self, agent_id: str) -> MockIdentity | None:
        return self._identities.get(agent_id)


class CryptographicResolverStub:
    """Stub showing gap-3 can swap in a new resolver without gate changes."""

    def __init__(self, identities: dict[str, MockIdentity]) -> None:
        self._identities = identities
        self.crypto_proof_verified: dict[str, bool] = {}

    def resolve(self, agent_id: str) -> MockIdentity | None:
        identity = self._identities.get(agent_id)
        if identity is not None:
            # Simulate cryptographic proof verification
            self.crypto_proof_verified[agent_id] = True
        return identity


# --- Classification tests ---------------------------------------------------


class TestMutationClassification:
    def test_low_severity(self) -> None:
        assert classify_mutation("repo", "read") == MutationSeverity.LOW
        assert classify_mutation("issue", "comment") == MutationSeverity.LOW

    def test_medium_severity(self) -> None:
        assert classify_mutation("repo", "commit") == MutationSeverity.MEDIUM
        assert classify_mutation("pr", "create_pr") == MutationSeverity.MEDIUM
        assert classify_mutation("pr", "merge_pr") == MutationSeverity.MEDIUM

    def test_high_severity(self) -> None:
        assert classify_mutation("repo", "archive") == MutationSeverity.HIGH
        assert classify_mutation("branch", "delete") == MutationSeverity.HIGH
        assert classify_mutation("branch", "force_push") == MutationSeverity.HIGH
        assert classify_mutation("secret", "secret_rotation") == MutationSeverity.HIGH

    def test_critical_severity(self) -> None:
        assert classify_mutation("org", "org_level_change") == MutationSeverity.CRITICAL
        assert classify_mutation("org", "key_rotation") == MutationSeverity.CRITICAL
        assert classify_mutation("branch", "remove_force_push_protection") == MutationSeverity.CRITICAL


# --- Gate tests -------------------------------------------------------------


class TestPreMutationGate:
    def _make_gate(
        self,
        identities: dict[str, MockIdentity] | None = None,
        authority_permitted: bool = True,
        resolver: Any = None,
    ) -> PreMutationGate:
        if resolver is None:
            identities = identities or {"devin": MockIdentity("devin", 2)}
            engine = MockIdentityEngine(identities)
            resolver = StringLookupResolver(engine)
        authority = MockAuthorityEngine(permitted=authority_permitted)
        return PreMutationGate(
            identity_resolver=resolver,
            authority_engine=authority,
        )

    def test_low_mutation_permitted(self) -> None:
        gate = self._make_gate()
        decision = gate.check(
            agent_id="devin", role_id="devin", authority="github_mutation",
            operation="repo", action="read",
        )
        assert decision.permitted
        assert decision.severity == MutationSeverity.LOW
        assert not decision.decision_receipt_required

    def test_medium_mutation_permitted(self) -> None:
        gate = self._make_gate()
        decision = gate.check(
            agent_id="devin", role_id="devin", authority="github_mutation",
            operation="repo", action="commit",
        )
        assert decision.permitted
        assert decision.severity == MutationSeverity.MEDIUM
        assert not decision.decision_receipt_required

    def test_high_mutation_blocked_without_receipt(self) -> None:
        """Two-person rule: HIGH mutation blocked without DECISION receipt."""
        gate = self._make_gate()
        decision = gate.check(
            agent_id="devin", role_id="devin", authority="github_mutation",
            operation="repo", action="archive",
            context={"repo": "hummbl-governance"},
        )
        assert not decision.permitted
        assert decision.severity == MutationSeverity.HIGH
        assert decision.decision_receipt_required
        assert not decision.decision_receipt_provided
        assert "DECISION" in decision.reason

    def test_high_mutation_allowed_with_receipt(self) -> None:
        """Two-person rule: HIGH mutation allowed with DECISION receipt."""
        gate = self._make_gate()
        decision = gate.check(
            agent_id="devin", role_id="devin", authority="github_mutation",
            operation="repo", action="archive",
            context={"repo": "hummbl-governance"},
            decision_receipt="DECISION-2026-08-27-archive-gov",
        )
        assert decision.permitted
        assert decision.severity == MutationSeverity.HIGH
        assert decision.decision_receipt_required
        assert decision.decision_receipt_provided
        assert decision.receipt_id == "DECISION-2026-08-27-archive-gov"

    def test_critical_mutation_blocked_without_receipt(self) -> None:
        gate = self._make_gate()
        decision = gate.check(
            agent_id="devin", role_id="devin", authority="github_mutation",
            operation="org", action="key_rotation",
        )
        assert not decision.permitted
        assert decision.severity == MutationSeverity.CRITICAL
        assert decision.decision_receipt_required

    def test_critical_mutation_allowed_with_receipt(self) -> None:
        gate = self._make_gate()
        decision = gate.check(
            agent_id="devin", role_id="devin", authority="github_mutation",
            operation="org", action="key_rotation",
            decision_receipt="DECISION-2026-08-27-key-rotation",
        )
        assert decision.permitted
        assert decision.severity == MutationSeverity.CRITICAL

    def test_identity_not_found_blocks(self) -> None:
        gate = self._make_gate(identities={})
        decision = gate.check(
            agent_id="unknown", role_id="unknown", authority="github_mutation",
            operation="repo", action="read",
        )
        assert not decision.permitted
        assert "Identity not found" in decision.reason

    def test_authority_denied_blocks(self) -> None:
        gate = self._make_gate(authority_permitted=False)
        decision = gate.check(
            agent_id="devin", role_id="devin", authority="github_mutation",
            operation="repo", action="commit",
        )
        assert not decision.permitted
        assert "Authority denied" in decision.reason

    def test_force_push_blocked_without_receipt(self) -> None:
        """Force-push is HIGH — blocked without DECISION receipt."""
        gate = self._make_gate()
        decision = gate.check(
            agent_id="devin", role_id="devin", authority="github_mutation",
            operation="branch", action="force_push",
        )
        assert not decision.permitted
        assert decision.severity == MutationSeverity.HIGH
        assert decision.decision_receipt_required


class TestPluggableResolver:
    """Verify gap-3 can swap in a cryptographic resolver without gate changes."""

    def test_cryptographic_resolver_works(self) -> None:
        identities = {"devin": MockIdentity("devin", 2)}
        resolver = CryptographicResolverStub(identities)
        gate = PreMutationGate(
            identity_resolver=resolver,
            authority_engine=MockAuthorityEngine(permitted=True),
        )
        decision = gate.check(
            agent_id="devin", role_id="devin", authority="github_mutation",
            operation="repo", action="commit",
        )
        assert decision.permitted
        assert resolver.crypto_proof_verified.get("devin") is True

    def test_cryptographic_resolver_high_with_receipt(self) -> None:
        identities = {"devin": MockIdentity("devin", 2)}
        resolver = CryptographicResolverStub(identities)
        gate = PreMutationGate(
            identity_resolver=resolver,
            authority_engine=MockAuthorityEngine(permitted=True),
        )
        decision = gate.check(
            agent_id="devin", role_id="devin", authority="github_mutation",
            operation="repo", action="delete",
            decision_receipt="DECISION-2026-08-27-delete-repo",
        )
        assert decision.permitted
        assert decision.severity == MutationSeverity.HIGH
