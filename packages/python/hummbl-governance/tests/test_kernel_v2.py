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

import dataclasses
import time
import unittest

from hummbl_governance.kernel_v2 import (
    Base120Coordinate,
    Base120Family,
    Base120MicroKernel,
    CapabilityToken,
    GuardedAutomaton,
    LedgerReceipt,
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

    def test_security_secrets_fail_closed(self) -> None:
        with self.assertRaises(ValueError):
            GuardedAutomaton("ROOT_GOVERNOR")
        with self.assertRaises(ValueError):
            GuardedAutomaton("ROOT_GOVERNOR", release_key=b"")
        with self.assertRaises(ValueError):
            ProjectionFunctor.redact_pseudonymize({"email": "a@example.com"}, {"email"})

    def test_re_causal_ledger_integrity(self) -> None:
        ledger = self.kernel.ledger
        r1 = ledger.append("agent_01", "write_file", {"path": "a.txt"})
        r2 = ledger.append("agent_01", "deploy_saas", {"env": "prod"})

        self.assertEqual(r1.sequence_id, 1)
        self.assertEqual(r2.sequence_id, 2)
        self.assertEqual(r2.prev_hash, r1.receipt_hash)
        self.assertTrue(ledger.verify_integrity())

        # Canonical JSON prevents delimiter collisions and binds coordinate
        h_a = LedgerReceipt.compute_receipt_hash(1, "agent:admin", "deploy", "p", "0" * 64, 1.0, "RE1")
        h_b = LedgerReceipt.compute_receipt_hash(1, "agent", "admin:deploy", "p", "0" * 64, 1.0, "RE1")
        h_c = LedgerReceipt.compute_receipt_hash(1, "agent:admin", "deploy", "p", "0" * 64, 1.0, "SY1")
        self.assertNotEqual(h_a, h_b)
        self.assertNotEqual(h_a, h_c)

    def test_p_capability_token_attenuation(self) -> None:
        root_token = self.kernel.issue_token(
            issuer="operator",
            subject="orchestrator",
            depth=3,
            allowed_scopes=("saas:create", "saas:deploy", "db:write"),
            lifetime_seconds=3600,
        )

        # Child token must attenuate depth and scope
        child_token = self.kernel.attenuate_token(
            root_token,
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
            self.kernel.attenuate_token(child_token, "sub_worker", {"admin:root"}, 300)

        # Tampered token via dataclasses.replace is rejected
        tampered = dataclasses.replace(child_token, allowed_scopes=("admin:root",))
        with self.assertRaises(PermissionError):
            self.kernel.execute_governed_action(tampered, "deploy", "admin:root", {})

        # Forged unsigned token is rejected
        forged = CapabilityToken(
            token_id="tok_forged",
            issuer="operator",
            subject="attacker",
            depth=1,
            max_depth=1,
            allowed_scopes=("saas:deploy",),
            expiry=time.time() + 300,
        )
        with self.assertRaises(PermissionError):
            self.kernel.execute_governed_action(forged, "deploy", "saas:deploy", {})

    def test_co_quorum_barrier(self) -> None:
        op_key = b"operator-hmac-key"
        sec_key = b"security-officer-hmac-key"
        barrier = QuorumBarrier(
            barrier_id="bar_001",
            action_intent="production_fleet_promotion",
            required_signers={"operator", "security_officer"},
            signer_keys={"operator": op_key, "security_officer": sec_key},
        )

        # Unauthorized, empty, and forged proofs must all fail
        self.assertFalse(barrier.submit_signature("unauthorized_agent", "sig_123"))
        self.assertFalse(barrier.submit_signature("operator", ""))
        self.assertFalse(barrier.submit_signature("operator", "forged_sig"))

        op_proof = barrier.sign_approval("operator", op_key)
        sec_proof = barrier.sign_approval("security_officer", sec_key)
        self.assertTrue(barrier.submit_signature("operator", op_proof))
        self.assertEqual(barrier.status.value, "PENDING")

        self.assertTrue(barrier.submit_signature("security_officer", sec_proof))
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
        redacted = proj.redact_pseudonymize(payload, pii_fields={"email"}, salt="test-redaction-salt")

        self.assertEqual(redacted["user_id"], "usr_123")
        self.assertTrue(redacted["email"].startswith("[PSEUDO_"))

    def test_cross_generator_commutation_tensor(self) -> None:
        """Test commutation between Automaton (SY), Filter (P), and Ledger (RE)."""
        token = self.kernel.issue_token(
            issuer="operator",
            subject="worker_01",
            depth=1,
            allowed_scopes=("saas:deploy", "ops:audit"),
            lifetime_seconds=300,
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

        # 3. HALT_NONCRITICAL blocks noncritical actions but permits critical actions
        self.kernel.automaton.transition("DEGRADED", SeverityLevel.HALT_NONCRITICAL, "Budget warning")
        with self.assertRaises(RuntimeError):
            self.kernel.execute_governed_action(
                token=token,
                action="deploy",
                scope="saas:deploy",
                payload={"cluster": "us-east-1"},
            )
        crit_receipt = self.kernel.execute_governed_action(
            token=token,
            action="audit_logging",
            scope="ops:audit",
            payload={"event": "degraded_audit"},
        )
        self.assertEqual(crit_receipt.sequence_id, 2)

        # 4. Automaton preemption (EMERGENCY) blocks all actions regardless of capability
        self.kernel.automaton.transition("EMERGENCY_HALT", SeverityLevel.EMERGENCY, "Intrusion alert")
        with self.assertRaises(RuntimeError):
            self.kernel.execute_governed_action(
                token=token,
                action="audit_logging",
                scope="ops:audit",
                payload={},
            )
        self.assertEqual(self.kernel.ledger.height, 2)  # Still 2, fail-closed preserved

    def test_security_round2_nan_lifetime_cross_kernel_and_quorum_hardening(self) -> None:
        # 1. NaN / inf / non-positive lifetime rejected; NaN expiry fails closed
        for bad_lt in (float("nan"), float("inf"), 0.0, -10.0):
            with self.assertRaises(ValueError):
                self.kernel.issue_token("op", "worker", ("s",), lifetime_seconds=bad_lt)
        nan_tok = CapabilityToken(
            token_id="tok_nan",
            issuer="op",
            subject="w",
            depth=1,
            max_depth=1,
            allowed_scopes=("s",),
            expiry=float("nan"),
        )
        self.assertFalse(nan_tok.is_valid_for("s"))

        # 2. Cross-kernel token replay blocked even with identical release_key
        other = Base120MicroKernel(release_key=b"test-operator-secret")
        tok = self.kernel.issue_token("op", "worker", ("saas:deploy",))
        with self.assertRaises(PermissionError):
            other.execute_governed_action(tok, "deploy", "saas:deploy", {})

        # 3. QuorumBarrier hides signer_keys from repr and ignores unverified pre-populated entries
        op_key = b"op-secret-key"
        sec_key = b"sec-secret-key"
        barrier = QuorumBarrier(
            barrier_id="bar_002",
            action_intent="deploy",
            required_signers={"operator", "security_officer"},
            signer_keys={"operator": op_key, "security_officer": sec_key},
            collected_signatures={"security_officer": "forged_prepopulated"},
        )
        self.assertNotIn("op-secret-key", repr(barrier))
        op_proof = barrier.sign_approval("operator", op_key)
        self.assertTrue(barrier.submit_signature("operator", op_proof))
        self.assertEqual(barrier.status.value, "PENDING")

        # 4. CausalLedger.verify_integrity catches _latest_hash divergence
        self.kernel.ledger.append("a", "act", {})
        self.assertTrue(self.kernel.ledger.verify_integrity())
        self.kernel.ledger._latest_hash = "f" * 64
        self.assertFalse(self.kernel.ledger.verify_integrity())


if __name__ == "__main__":
    unittest.main()
