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

"""Tests for the pre-mutation gate (gap-1 / #406).

Verifies that the mutation gate:
- Classifies mutations by risk level
- Permits LOW mutations without authority checks
- Requires authority checks for MEDIUM mutations
- Blocks HIGH mutations without operator DECISION receipts
- Blocks CRITICAL mutations without two-person rule
- Logs every gate decision
- Integrates with the Kernel
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from hummbl_governance.kernel import Kernel
from hummbl_governance.kernel.mutation_gate import (
    MutationGate,
    MutationLevel,
    MutationRequest,
)
from hummbl_governance.kernel.authority_engine import AuthorityCheck


@pytest.fixture
def tmp_kernel(tmp_path: Path) -> Kernel:
    """Create a Kernel with a temporary state directory."""
    return Kernel(state_dir=tmp_path / "kernel")


@pytest.fixture
def gate(tmp_kernel: Kernel) -> MutationGate:
    """Create a mutation gate wired to a temporary kernel."""
    return tmp_kernel.mutation_gate


class TestMutationClassification:
    """Test mutation type → risk level mapping."""

    def test_low_mutations(self, gate: MutationGate) -> None:
        assert gate.classify("bus_post") == MutationLevel.LOW
        assert gate.classify("receipt_create") == MutationLevel.LOW
        assert gate.classify("file_read") == MutationLevel.LOW
        assert gate.classify("status_update") == MutationLevel.LOW

    def test_medium_mutations(self, gate: MutationGate) -> None:
        assert gate.classify("commit") == MutationLevel.MEDIUM
        assert gate.classify("pr_create") == MutationLevel.MEDIUM
        assert gate.classify("file_write") == MutationLevel.MEDIUM
        assert gate.classify("branch_create") == MutationLevel.MEDIUM

    def test_high_mutations(self, gate: MutationGate) -> None:
        assert gate.classify("archive_repo") == MutationLevel.HIGH
        assert gate.classify("delete_file") == MutationLevel.HIGH
        assert gate.classify("force_push") == MutationLevel.HIGH
        assert gate.classify("pr_merge") == MutationLevel.HIGH
        assert gate.classify("kill_switch_activate") == MutationLevel.HIGH

    def test_critical_mutations(self, gate: MutationGate) -> None:
        assert gate.classify("org_change") == MutationLevel.CRITICAL
        assert gate.classify("key_rotation") == MutationLevel.CRITICAL
        assert gate.classify("production_deploy") == MutationLevel.CRITICAL
        assert gate.classify("doctrine_amendment") == MutationLevel.CRITICAL

    def test_unknown_mutation_defaults_to_high(self, gate: MutationGate) -> None:
        """Unknown mutation types should default to HIGH (fail-safe)."""
        assert gate.classify("unknown_mutation") == MutationLevel.HIGH


class TestLowMutations:
    """Test LOW risk mutations — should be permitted without authority check."""

    def test_bus_post_permitted(self, gate: MutationGate) -> None:
        result = gate.check(MutationRequest(
            mutation_type="bus_post",
            agent_id="devin",
            role_id="primary_agent",
            target="bus",
        ))
        assert result.permitted is True
        assert result.risk_level == MutationLevel.LOW
        assert result.logged is True

    def test_receipt_create_permitted(self, gate: MutationGate) -> None:
        result = gate.check(MutationRequest(
            mutation_type="receipt_create",
            agent_id="devin",
            role_id="primary_agent",
            target="receipts",
        ))
        assert result.permitted is True
        assert result.risk_level == MutationLevel.LOW


class TestMediumMutations:
    """Test MEDIUM risk mutations — require authority check."""

    def test_commit_permitted_with_authority(self, tmp_kernel: Kernel) -> None:
        """MEDIUM mutation should be permitted when authority check passes."""
        with patch.object(tmp_kernel, "exercise_authority") as mock_exercise:
            mock_exercise.return_value = AuthorityCheck(
                permitted=True,
                reason="Within scope",
            )
            gate = tmp_kernel.mutation_gate
            result = gate.check(MutationRequest(
                mutation_type="commit",
                agent_id="devin",
                role_id="primary_agent",
                target="hummbl-governance",
            ))
        assert result.permitted is True
        assert result.risk_level == MutationLevel.MEDIUM
        mock_exercise.assert_called_once()

    def test_commit_blocked_without_authority(self, tmp_kernel: Kernel) -> None:
        """MEDIUM mutation should be blocked when authority check fails."""
        with patch.object(tmp_kernel, "exercise_authority") as mock_exercise:
            mock_exercise.return_value = AuthorityCheck(
                permitted=False,
                reason="Authority not defined in charter",
            )
            gate = tmp_kernel.mutation_gate
            result = gate.check(MutationRequest(
                mutation_type="commit",
                agent_id="devin",
                role_id="primary_agent",
                target="hummbl-governance",
            ))
        assert result.permitted is False
        assert result.risk_level == MutationLevel.MEDIUM
        assert "Authority check failed" in result.reason


class TestHighMutations:
    """Test HIGH risk mutations — require authority check + operator DECISION receipt."""

    def test_archive_blocked_without_decision_receipt(self, tmp_kernel: Kernel) -> None:
        """HIGH mutation should be blocked without operator DECISION receipt."""
        with patch.object(tmp_kernel, "exercise_authority") as mock_exercise:
            mock_exercise.return_value = AuthorityCheck(
                permitted=True,
                reason="Within scope",
            )
            gate = tmp_kernel.mutation_gate
            result = gate.check(MutationRequest(
                mutation_type="archive_repo",
                agent_id="devin",
                role_id="primary_agent",
                target="hummbl-governance",
            ))
        assert result.permitted is False
        assert result.risk_level == MutationLevel.HIGH
        assert "operator DECISION receipt" in result.reason

    def test_archive_permitted_with_decision_receipt(self, tmp_kernel: Kernel) -> None:
        """HIGH mutation should be permitted with valid operator DECISION receipt."""
        with patch.object(tmp_kernel, "exercise_authority") as mock_exercise:
            mock_exercise.return_value = AuthorityCheck(
                permitted=True,
                reason="Within scope",
            )
            gate = tmp_kernel.mutation_gate
            result = gate.check(MutationRequest(
                mutation_type="archive_repo",
                agent_id="devin",
                role_id="primary_agent",
                target="hummbl-governance",
                operator_decision_receipt="bus:2026-08-31T23:00:00Z",
            ))
        assert result.permitted is True
        assert result.risk_level == MutationLevel.HIGH

    def test_archive_blocked_with_short_receipt(self, tmp_kernel: Kernel) -> None:
        """HIGH mutation should be blocked with invalid (too short) receipt."""
        with patch.object(tmp_kernel, "exercise_authority") as mock_exercise:
            mock_exercise.return_value = AuthorityCheck(
                permitted=True,
                reason="Within scope",
            )
            gate = tmp_kernel.mutation_gate
            result = gate.check(MutationRequest(
                mutation_type="archive_repo",
                agent_id="devin",
                role_id="primary_agent",
                target="hummbl-governance",
                operator_decision_receipt="short",
            ))
        assert result.permitted is False
        assert "not verified" in result.reason

    def test_force_push_blocked_without_receipt(self, tmp_kernel: Kernel) -> None:
        """force_push should be blocked without operator DECISION receipt."""
        with patch.object(tmp_kernel, "exercise_authority") as mock_exercise:
            mock_exercise.return_value = AuthorityCheck(
                permitted=True,
                reason="Within scope",
            )
            gate = tmp_kernel.mutation_gate
            result = gate.check(MutationRequest(
                mutation_type="force_push",
                agent_id="devin",
                role_id="primary_agent",
                target="hummbl-governance",
            ))
        assert result.permitted is False
        assert result.risk_level == MutationLevel.HIGH


class TestCriticalMutations:
    """Test CRITICAL risk mutations — require authority + operator + two-person."""

    def test_key_rotation_blocked_without_second_approver(self, tmp_kernel: Kernel) -> None:
        """CRITICAL mutation should be blocked without second approver."""
        with patch.object(tmp_kernel, "exercise_authority") as mock_exercise:
            mock_exercise.return_value = AuthorityCheck(
                permitted=True,
                reason="Within scope",
            )
            gate = tmp_kernel.mutation_gate
            result = gate.check(MutationRequest(
                mutation_type="key_rotation",
                agent_id="devin",
                role_id="primary_agent",
                target="signing-registry",
                operator_decision_receipt="bus:2026-08-31T23:00:00Z",
            ))
        assert result.permitted is False
        assert result.risk_level == MutationLevel.CRITICAL
        assert "two-person" in result.reason

    def test_key_rotation_permitted_with_both_approvers(self, tmp_kernel: Kernel) -> None:
        """CRITICAL mutation should be permitted with both approver receipts."""
        with patch.object(tmp_kernel, "exercise_authority") as mock_exercise:
            mock_exercise.return_value = AuthorityCheck(
                permitted=True,
                reason="Within scope",
            )
            gate = tmp_kernel.mutation_gate
            result = gate.check(MutationRequest(
                mutation_type="key_rotation",
                agent_id="devin",
                role_id="primary_agent",
                target="signing-registry",
                operator_decision_receipt="bus:2026-08-31T23:00:00Z",
                second_approver_receipt="bus:2026-08-31T23:05:00Z",
            ))
        assert result.permitted is True
        assert result.risk_level == MutationLevel.CRITICAL

    def test_production_deploy_blocked_without_any_receipts(self, tmp_kernel: Kernel) -> None:
        """CRITICAL mutation should be blocked without any receipts."""
        with patch.object(tmp_kernel, "exercise_authority") as mock_exercise:
            mock_exercise.return_value = AuthorityCheck(
                permitted=True,
                reason="Within scope",
            )
            gate = tmp_kernel.mutation_gate
            result = gate.check(MutationRequest(
                mutation_type="production_deploy",
                agent_id="devin",
                role_id="primary_agent",
                target="hummbl-production",
            ))
        assert result.permitted is False
        assert result.risk_level == MutationLevel.CRITICAL


class TestGateLogging:
    """Test that the gate logs every decision."""

    def test_log_created_on_permit(self, gate: MutationGate) -> None:
        result = gate.check(MutationRequest(
            mutation_type="bus_post",
            agent_id="devin",
            role_id="primary_agent",
            target="bus",
        ))
        assert result.logged is True
        assert gate.gate_log.exists()
        lines = gate.gate_log.read_text().strip().split("\n")
        assert len(lines) == 1
        entry = json.loads(lines[0])
        assert entry["mutation_type"] == "bus_post"
        assert entry["permitted"] is True
        assert entry["agent_id"] == "devin"

    def test_log_created_on_block(self, tmp_kernel: Kernel) -> None:
        with patch.object(tmp_kernel, "exercise_authority") as mock_exercise:
            mock_exercise.return_value = AuthorityCheck(
                permitted=False,
                reason="Not in charter",
            )
            gate = tmp_kernel.mutation_gate
            result = gate.check(MutationRequest(
                mutation_type="commit",
                agent_id="devin",
                role_id="unknown_role",
                target="hummbl-governance",
            ))
        assert result.logged is True
        entry = json.loads(gate.gate_log.read_text().strip().split("\n")[0])
        assert entry["permitted"] is False

    def test_list_decisions_filtered(self, gate: MutationGate) -> None:
        gate.check(MutationRequest(
            mutation_type="bus_post",
            agent_id="devin",
            role_id="primary_agent",
            target="bus",
        ))
        gate.check(MutationRequest(
            mutation_type="receipt_create",
            agent_id="codex",
            role_id="engineer",
            target="receipts",
        ))
        all_decisions = gate.list_decisions()
        assert len(all_decisions) == 2
        devin_only = gate.list_decisions(agent_id="devin")
        assert len(devin_only) == 1
        assert devin_only[0]["agent_id"] == "devin"
        permitted_only = gate.list_decisions(permitted=True)
        assert len(permitted_only) == 2


class TestKernelIntegration:
    """Test that the gate is wired into the Kernel."""

    def test_kernel_has_mutation_gate(self, tmp_kernel: Kernel) -> None:
        assert hasattr(tmp_kernel, "mutation_gate")
        assert isinstance(tmp_kernel.mutation_gate, MutationGate)

    def test_kernel_check_mutation_low(self, tmp_kernel: Kernel) -> None:
        result = tmp_kernel.check_mutation(
            mutation_type="bus_post",
            agent_id="devin",
            role_id="primary_agent",
            target="bus",
        )
        assert result.permitted is True
        assert result.risk_level == MutationLevel.LOW

    def test_kernel_check_mutation_high_blocked(self, tmp_kernel: Kernel) -> None:
        """Kernel.check_mutation should block HIGH without operator receipt."""
        with patch.object(tmp_kernel, "exercise_authority") as mock_exercise:
            mock_exercise.return_value = AuthorityCheck(
                permitted=True,
                reason="Within scope",
            )
            result = tmp_kernel.check_mutation(
                mutation_type="archive_repo",
                agent_id="devin",
                role_id="primary_agent",
                target="hummbl-governance",
            )
        assert result.permitted is False
        assert result.risk_level == MutationLevel.HIGH

    def test_kernel_guard_mutation_blocks(self, tmp_kernel: Kernel) -> None:
        """Kernel.guard_mutation should raise PermissionError on block."""
        with patch.object(tmp_kernel, "exercise_authority") as mock_exercise:
            mock_exercise.return_value = AuthorityCheck(
                permitted=True,
                reason="Within scope",
            )
            with pytest.raises(PermissionError, match="Mutation gate blocked"):
                tmp_kernel.guard_mutation(
                    mutation_type="archive_repo",
                    agent_id="devin",
                    role_id="primary_agent",
                    target="hummbl-governance",
                    action=lambda: "should not execute",
                )

    def test_kernel_guard_mutation_permits(self, tmp_kernel: Kernel) -> None:
        """Kernel.guard_mutation should execute action on permit."""
        result = tmp_kernel.guard_mutation(
            mutation_type="bus_post",
            agent_id="devin",
            role_id="primary_agent",
            target="bus",
            action=lambda: "executed",
        )
        assert result == "executed"


class TestIntegrationScenario:
    """Integration test: gate blocks unauthorized archive (the baseline incident)."""

    def test_unauthorized_archive_blocked(self, tmp_kernel: Kernel) -> None:
        """Reproduce the 2026-08-26 incident: agent archives repo without authority.

        The gate should block this even if the authority check passes,
        because no operator DECISION receipt is provided.
        """
        with patch.object(tmp_kernel, "exercise_authority") as mock_exercise:
            mock_exercise.return_value = AuthorityCheck(
                permitted=True,
                reason="Within scope",
            )
            gate = tmp_kernel.mutation_gate
            result = gate.check(MutationRequest(
                mutation_type="archive_repo",
                agent_id="devin",
                role_id="primary_agent",
                target="hummbl-governance",
                # No operator_decision_receipt — should be blocked
            ))

        assert result.permitted is False
        assert result.risk_level == MutationLevel.HIGH
        assert "operator DECISION receipt" in result.reason
        assert result.logged is True

        # Verify the block is in the log
        decisions = gate.list_decisions(permitted=False)
        assert len(decisions) == 1
        assert decisions[0]["mutation_type"] == "archive_repo"
