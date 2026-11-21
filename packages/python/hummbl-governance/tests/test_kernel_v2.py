# Copyright 2026 Reuben Bowlby
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

"""Unit tests for the Base120 Micro-Kernel (v2.0) and Commutation Invariants."""

import time
import unittest

from hummbl_governance.kernel_v2 import (
    Base120Coordinate,
    Base120Family,
    Base120MicroKernel,
    CapabilityToken,
    CausalLedger,
    ConstraintPredicate,
    GuardedAutomaton,
    ProjectionFunctor,
    QuorumBarrier,
    SeverityLevel,
)


class TestBase120MicroKernel(unittest.TestCase):

    def setUp(self) -> None:
        self.kernel = Base120MicroKernel(release_key=b"test-operator-secret")

    def test_base120_coordinates(self) -> None:
        coord = Base120Coordinate(Base120Family.SYSTEMS, 1)
        self.assertEqual(str(coord), "SY1")
        with self.assertRaises(ValueError):
            Base120Coordinate(Base120Family.INVERSION, 25)

    def test_sy_monotonic_automaton(self) -> None:
        auto = self.kernel.automaton
        self.assertEqual(auto.state.severity, SeverityLevel.DISENGAGED)

        # Autonomous upgrade to HALT_ALL
        auto.transition("ANOMALY", SeverityLevel.HALT_ALL, "Drift detected")
        self.assertEqual(auto.state.severity, SeverityLevel.HALT_ALL)

        # Autonomous downgrade must be blocked
        with self.assertRaises(PermissionError):
            auto.transition("NORMAL", SeverityLevel.DISENGAGED, "Try unhalt")

        # Downgrade with valid operator release token succeeds
        token = auto.generate_release_token(auto.state)
        auto.transition("NORMAL", SeverityLevel.DISENGAGED, "Operator resolved", release_token=token)
        self.assertEqual(auto.state.severity, SeverityLevel.DISENGAGED)

    def test_re_causal_ledger_integrity(self) -> None:
        ledger = self.kernel.ledger
        r1 = ledger.append("agent_01", "write_file", {"path": "a.txt"})
        r2 = ledger.append("agent_01", "deploy_saas", {"env": "prod"})

        self.assertEqual(r1.sequence_id, 1)
        self.assertEqual(r2.sequence_id, 2)
        self.assertEqual(r2.prev_hash, r1.receipt_hash)
        self.assertTrue(ledger.verify_integrity())

    def test_p_capability_token_attenuation(self) -> None:
        root_token = CapabilityToken(
            token_id="tok_root",
            issuer="operator",
            subject="orchestrator",
            depth=3,
            max_depth=3,
            allowed_scopes=("saas:create", "saas:deploy", "db:write"),
            expiry=time.time() + 3600,
        )

        # Child token must attenuate depth and scope
        child_token = root_token.attenuate(
            new_subject="worker_agent",
            sub_scopes={"saas:create", "db:write"},
            lifetime_seconds=600,
        )

        self.assertEqual(child_token.depth, 2)
        self.assertEqual(child_token.issuer, "orchestrator")
        self.assertEqual(child_token.subject, "worker_agent")
        self.assertEqual(set(child_token.allowed_scopes), {"db:write", "saas:create"})

        # Cannot expand scope
        with self.assertRaises(PermissionError):
            child_token.attenuate("sub_worker", {"admin:root"}, 300)

    def test_co_quorum_barrier(self) -> None:
        barrier = QuorumBarrier(
            barrier_id="bar_001",
            action_intent="production_fleet_promotion",
            required_signers={"operator", "security_officer"},
        )

        self.assertFalse(barrier.submit_signature("unauthorized_agent", "sig_123"))
        self.assertTrue(barrier.submit_signature("operator", "sig_op"))
        self.assertEqual(barrier.status.value, "PENDING")

        self.assertTrue(barrier.submit_signature("security_officer", "sig_sec"))
        self.assertEqual(barrier.status.value, "APPROVED")

    def test_in_constraint_predicates(self) -> None:
        pred = self.kernel.predicates
        ok, msg = pred.assert_falsifiability({"hypothesis": "model X is better", "falsifier": "accuracy < 0.90"})
        self.assertTrue(ok)

        bad_ok, bad_msg = pred.assert_falsifiability({"hypothesis": "infinite growth"})
        self.assertFalse(bad_ok)

    def test_de_projection_functors(self) -> None:
        proj = self.kernel.projections
        payload = {"user_id": "usr_123", "email": "john@example.com", "action": "login"}
        redacted = proj.redact_pseudonymize(payload, pii_fields={"email"})

        self.assertEqual(redacted["user_id"], "usr_123")
        self.assertTrue(redacted["email"].startswith("[PSEUDO_"))

    def test_cross_generator_commutation_tensor(self) -> None:
        """Test commutation between Automaton (SY), Filter (P), and Ledger (RE)."""
        token = CapabilityToken(
            token_id="tok_01",
            issuer="operator",
            subject="worker_01",
            depth=1,
            max_depth=1,
            allowed_scopes=("saas:deploy",),
            expiry=time.time() + 300,
        )

        # 1. Healthy execution succeeds and emits receipt
        receipt = self.kernel.execute_governed_action(
            token=token,
            action="deploy",
            scope="saas:deploy",
            payload={"cluster": "us-east-1"},
        )
        self.assertEqual(receipt.sequence_id, 1)

        # 2. Scope violation fails closed without state mutation
        with self.assertRaises(PermissionError):
            self.kernel.execute_governed_action(
                token=token,
                action="nuke_db",
                scope="admin:destructive",
                payload={},
            )
        self.assertEqual(self.kernel.ledger.height, 1)  # No receipt emitted

        # 3. Automaton preemption blocks all actions regardless of capability
        self.kernel.automaton.transition("EMERGENCY_HALT", SeverityLevel.EMERGENCY, "Intrusion alert")
        with self.assertRaises(RuntimeError):
            self.kernel.execute_governed_action(
                token=token,
                action="deploy",
                scope="saas:deploy",
                payload={"cluster": "us-east-1"},
            )
        self.assertEqual(self.kernel.ledger.height, 1)  # Still 1, fail-closed preserved


if __name__ == "__main__":
    unittest.main()
