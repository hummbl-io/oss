#!/usr/bin/env python3
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

"""Property-based tests for the HUMMBL Governance Kernel — stdlib only.

Generates thousands of random inputs to find edge cases and invariants.
No Hypothesis dependency — pure stdlib random/string generation.

Usage:
    python -m pytest hummbl_governance/kernel/test_kernel_properties.py -v
"""

from __future__ import annotations

import random
import string
import tempfile
from pathlib import Path
from typing import Any

import pytest

from hummbl_governance.kernel import (
    EvidenceEngine,
    IdentityEngine,
    Kernel,
    ReceiptEngine,
    SequenceEngine,
)
from hummbl_governance.kernel.invariants import KernelInvariant, KernelPanic


# ===========================================================================
# Property-Based Receipt Engine Tests
# ===========================================================================

class TestReceiptProperties:
    """Generate random receipts and verify invariants hold."""

    def test_random_receipts_roundtrip(self) -> None:
        """Generate 500 random receipts, store, retrieve, verify all invariants."""
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = ReceiptEngine(Path(tmpdir))
            agents = ["a", "b", "c", "d", "e"]
            actions = ["CREATE", "UPDATE", "DELETE", "STATUS", "SCAN"]
            last_receipts: dict[str, Any] = {}

            for _ in range(500):
                agent = random.choice(agents)
                action = random.choice(actions)
                payload = self._random_payload()
                prev_hash = ""
                if agent in last_receipts:
                    prev_hash = last_receipts[agent].compute_hash()
                receipt = engine.create(
                    agent_id=agent,
                    action_type=action,
                    payload=payload,
                    law_checks=["SL-07", "SL-10"],
                    prev_receipt_hash=prev_hash,
                )
                assert receipt.agent_id == agent
                assert receipt.action_type == action
                assert receipt.receipt_id.startswith("r-")
                assert receipt.signature != ""
                assert receipt.compute_hash() != ""
                engine.store(receipt)
                last_receipts[agent] = receipt

            # Verify all chains
            for agent in agents:
                receipts = engine.list_for_agent(agent)
                if len(receipts) >= 2:
                    valid, _ = engine.verify_chain(agent)
                    assert valid is True, f"Chain broken for {agent}"

    def test_receipt_signature_invariant(self) -> None:
        """Every stored receipt must have a valid signature."""
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = ReceiptEngine(Path(tmpdir))
            for _ in range(200):
                receipt = engine.create(
                    agent_id="sig-test",
                    action_type="TEST",
                    payload=self._random_payload(),
                )
                engine.store(receipt)
                assert engine.validate(receipt) is True

    def test_sequence_monotonic_property(self) -> None:
        """For any sequence of receipts, sequence_id must be strictly increasing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            kernel = Kernel.boot(state_dir=Path(tmpdir))
            seq_ids: list[int] = []
            for _ in range(100):
                receipt = kernel.create_receipt("mono", "TEST", payload=self._random_payload())
                kernel.store_receipt(receipt)
                seq_ids.append(receipt.sequence_id)
            assert seq_ids == sorted(seq_ids)
            assert len(set(seq_ids)) == len(seq_ids)  # All unique

    def test_hash_chain_property(self) -> None:
        """For any two consecutive receipts, receipt[N].prev_hash == hash(receipt[N-1])."""
        with tempfile.TemporaryDirectory() as tmpdir:
            kernel = Kernel.boot(state_dir=Path(tmpdir))
            prev_receipt = None
            for _ in range(50):
                receipt = kernel.create_receipt("chain", "TEST")
                kernel.store_receipt(receipt)
                if prev_receipt is not None:
                    expected = prev_receipt.compute_hash()
                    assert receipt.prev_receipt_hash == expected
                prev_receipt = receipt

    def test_receipt_id_uniqueness_property(self) -> None:
        """All receipt IDs must be unique across all agents."""
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = ReceiptEngine(Path(tmpdir))
            all_ids: set[str] = set()
            for _ in range(300):
                agent = f"agent-{random.randint(0, 9)}"
                receipt = engine.create(agent, "TEST")
                engine.store(receipt)
                assert receipt.receipt_id not in all_ids
                all_ids.add(receipt.receipt_id)

    def _random_payload(self) -> dict[str, str | int | float | bool]:
        """Generate a random payload."""
        return {
            "s": "".join(random.choices(string.ascii_letters + string.digits + " _-", k=random.randint(0, 100))),
            "i": random.randint(-10000, 10000),
            "f": random.random() * 1000,
            "b": random.choice([True, False]),
        }


# ===========================================================================
# Property-Based Sequence Engine Tests
# ===========================================================================

class TestSequenceProperties:
    """Generate random sequence operations and verify monotonicity."""

    def test_next_always_increments(self) -> None:
        """For any agent, next() always returns current + 1."""
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = SequenceEngine(Path(tmpdir))
            for _ in range(100):
                agent = f"agent-{random.randint(0, 20)}"
                before = engine.current(agent)
                after = engine.next(agent)
                assert after == before + 1

    def test_validate_rejects_used_ids(self) -> None:
        """validate() must reject any sequence_id <= current."""
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = SequenceEngine(Path(tmpdir))
            for _ in range(100):
                agent = f"agent-{random.randint(0, 20)}"
                current = engine.current(agent)
                # All IDs <= current should be rejected
                for seq_id in range(current - 5, current + 1):
                    if seq_id > 0:
                        assert engine.validate(agent, seq_id) is False

    def test_reconstruct_preserves_order(self) -> None:
        """reconstruct() always produces ascending sequence."""
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = SequenceEngine(Path(tmpdir))
            for _ in range(50):
                n = random.randint(1, 100)
                receipts = [
                    {"sequence_id": random.randint(1, n * 2)}
                    for _ in range(n)
                ]
                result = engine.reconstruct("agent", receipts)
                seq_ids = [r["sequence_id"] for r in result if "sequence_id" in r]
                assert seq_ids == sorted(seq_ids)

    def test_continuity_detects_gaps_property(self) -> None:
        """A continuous sequence has no gaps; a gapped sequence is detected."""
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = SequenceEngine(Path(tmpdir))
            # Continuous: 1,2,3,4,5
            continuous = [{"sequence_id": i} for i in range(1, 6)]
            report = engine.check_continuity("agent", continuous)
            assert report["continuous"] is True

            # Gapped: 1,3,5 (missing 2,4)
            gapped = [{"sequence_id": i} for i in [1, 3, 5]]
            report = engine.check_continuity("agent", gapped)
            assert report["continuous"] is False


# ===========================================================================
# Property-Based Identity Engine Tests
# ===========================================================================

class TestIdentityProperties:
    """Generate random identity operations and verify registry invariants."""

    TRUST_TIERS = ["OWNER", "TRUSTED", "MEDIUM-HIGH", "MEDIUM", "PROBATIONARY", "REVOKED"]

    def test_register_then_resolve(self) -> None:
        """For any registered agent, resolve() returns matching identity."""
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = IdentityEngine(Path(tmpdir))
            for _ in range(100):
                agent_id = self._random_agent_id()
                tier = random.choice(self.TRUST_TIERS)
                engine.register(agent_id, trust_tier=tier)
                resolved = engine.resolve(agent_id)
                assert resolved is not None
                assert resolved.agent_id == agent_id
                assert resolved.trust_tier == tier

    def test_duplicate_register_always_panics(self) -> None:
        """Registering the same agent_id twice must always raise KernelPanic."""
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = IdentityEngine(Path(tmpdir))
            for _ in range(50):
                agent_id = self._random_agent_id()
                engine.register(agent_id)
                with pytest.raises(KernelPanic) as exc:
                    engine.register(agent_id)
                assert exc.value.invariant == KernelInvariant.IDENTITY

    def test_role_claim_state_machine(self) -> None:
        """Role claim must follow: UNCLAIMED -> CLAIMED -> PROBATION."""
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = IdentityEngine(Path(tmpdir))
            for _ in range(50):
                agent_id = self._random_agent_id()
                role_id = random.choice(["AI-PE", "AI-CCO", "AI-CISO", "AI-QA"])
                engine.register(agent_id)
                token = engine.claim_role(agent_id, role_id)
                assert token["state"] == "PROBATION"
                assert token["agent_id"] == agent_id
                assert token["role_id"] == role_id

    def test_confirm_requires_80_percent(self) -> None:
        """confirm_role() returns True iff metric_score >= 0.80."""
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = IdentityEngine(Path(tmpdir))
            for _ in range(50):
                agent_id = self._random_agent_id()
                role_id = "AI-PE"
                engine.register(agent_id)
                engine.claim_role(agent_id, role_id)

                total = random.randint(1, 20)
                compliant = random.randint(0, total)
                token = engine._role_claims[f"{agent_id}:{role_id}"]
                token["receipts_submitted"] = total
                token["receipts_compliant"] = compliant
                engine._save_role_claims()

                expected = compliant / total >= 0.80
                actual = engine.confirm_role(agent_id, role_id)
                assert actual == expected, f"total={total}, compliant={compliant}, expected={expected}, actual={actual}"

    def test_demote_removes_from_active_roles(self) -> None:
        """After demote_role(), the role is not in active_roles."""
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = IdentityEngine(Path(tmpdir))
            for _ in range(30):
                agent_id = self._random_agent_id()
                role_id = "AI-PE"
                engine.register(agent_id)
                engine.claim_role(agent_id, role_id)
                # Manually promote for testing
                engine._role_claims[f"{agent_id}:{role_id}"]["state"] = "CONFIRMED"
                engine._save_role_claims()
                engine._identities[agent_id].active_roles.append(role_id)
                engine._save_identities()

                engine.demote_role(agent_id, role_id, "test")
                identity = engine.resolve(agent_id)
                assert role_id not in identity.active_roles

    def test_revoked_agent_cannot_claim_any_role(self) -> None:
        """For any role, a REVOKED agent cannot claim it."""
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = IdentityEngine(Path(tmpdir))
            for _ in range(20):
                agent_id = self._random_agent_id()
                role_id = random.choice(["AI-PE", "AI-CCO", "AI-CISO"])
                engine.register(agent_id, trust_tier="REVOKED")
                with pytest.raises(KernelPanic) as exc:
                    engine.claim_role(agent_id, role_id)
                assert exc.value.invariant == KernelInvariant.ROLE

    def _random_agent_id(self) -> str:
        """Generate a random agent ID."""
        chars = string.ascii_lowercase + string.digits + "_-"
        return "".join(random.choices(chars, k=random.randint(3, 32)))


# ===========================================================================
# Property-Based Evidence Engine Tests
# ===========================================================================

class TestEvidenceProperties:
    """Generate random evidence inputs and verify grading invariants."""

    def test_grade_always_returns_valid_average(self) -> None:
        """For any inputs, grade.average() is always A, B, or C."""
        engine = EvidenceEngine()
        for _ in range(500):
            claim = self._random_string(0, 500)
            sources = [self._random_string(5, 50) for _ in range(random.randint(0, 10))]
            methodology = self._random_string(0, 200)
            grade = engine.grade(claim, sources, methodology)
            assert grade.average() in ("A", "B", "C")

    def test_is_acceptable_consistent_with_average(self) -> None:
        """If average() == C, is_acceptable() may still be True (not all-C dims)."""
        engine = EvidenceEngine()
        for _ in range(200):
            grade = engine.grade(
                claim=self._random_string(10, 100),
                sources=[self._random_string(5, 50) for _ in range(random.randint(1, 5))],
                methodology=self._random_string(10, 100),
            )
            # At least one dimension must be A or B for average to be A or B
            if grade.average() in ("A", "B"):
                assert grade.is_acceptable() is True

    def test_canonicalize_is_deterministic(self) -> None:
        """For any string, canonicalize() always returns the same ID."""
        engine = EvidenceEngine()
        for _ in range(100):
            claim = self._random_string(5, 100)
            id1 = engine.canonicalize(claim)
            id2 = engine.canonicalize(claim)
            assert id1 == id2
            assert len(id1) == 16  # SHA-256 hex, first 16 chars

    def test_canonicalize_is_case_insensitive(self) -> None:
        """canonicalize() must be case-insensitive."""
        engine = EvidenceEngine()
        for _ in range(100):
            claim = self._random_string(5, 50)
            id1 = engine.canonicalize(claim.lower())
            id2 = engine.canonicalize(claim.upper())
            assert id1 == id2

    def test_validate_receipt_claims_no_crash(self) -> None:
        """For any payload, validate_receipt_claims() must not crash."""
        engine = EvidenceEngine()
        for _ in range(200):
            payload = {
                "claims": [
                    {
                        "text": self._random_string(0, 200),
                        "sources": [self._random_string(0, 50) for _ in range(random.randint(0, 5))],
                        "methodology": self._random_string(0, 100),
                    }
                    for _ in range(random.randint(0, 5))
                ]
            }
            acceptable, reasons = engine.validate_receipt_claims(payload)
            assert isinstance(acceptable, bool)
            assert isinstance(reasons, list)

    def _random_string(self, min_len: int, max_len: int) -> str:
        """Generate a random string."""
        chars = string.ascii_letters + string.digits + " _-.,!?"
        return "".join(random.choices(chars, k=random.randint(min_len, max_len)))


# ===========================================================================
# Property-Based Kernel Integration Tests
# ===========================================================================

class TestKernelIntegrationProperties:
    """Test the full Kernel with random multi-agent scenarios."""

    def test_multi_agent_receipt_isolation(self) -> None:
        """Receipts from different agents must never mix."""
        with tempfile.TemporaryDirectory() as tmpdir:
            kernel = Kernel.boot(state_dir=Path(tmpdir))
            agents = [f"agent-{i}" for i in range(10)]

            for agent in agents:
                kernel.identity.register(agent)
                for _ in range(random.randint(1, 10)):
                    receipt = kernel.create_receipt(agent, "TEST")
                    kernel.store_receipt(receipt)

            for agent in agents:
                receipts = kernel.receipt.list_for_agent(agent)
                for r in receipts:
                    assert r.agent_id == agent

    def test_boot_produces_valid_receipt(self) -> None:
        """Every Kernel boot produces a valid KERNEL_BOOT receipt."""
        with tempfile.TemporaryDirectory() as tmpdir:
            kernel = Kernel.boot(state_dir=Path(tmpdir))
            boot_receipts = [
                r for r in kernel.receipt.list_for_agent("kernel")
                if r.action_type == "KERNEL_BOOT"
            ]
            assert len(boot_receipts) >= 1
            for receipt in boot_receipts:
                assert receipt.signature != ""
                assert receipt.sequence_id > 0
                assert kernel.receipt.validate(receipt) is True

    def test_full_random_workflow(self) -> None:
        """Generate a random multi-step workflow and verify no invariants break."""
        with tempfile.TemporaryDirectory() as tmpdir:
            kernel = Kernel.boot(state_dir=Path(tmpdir))
            agents = [f"agent-{i}" for i in range(5)]
            roles = ["AI-PE", "AI-CCO", "AI-CISO", "AI-QA", "AI-REL"]

            for agent in agents:
                kernel.identity.register(agent)
                role = random.choice(roles)
                kernel.identity.claim_role(agent, role)
                # Simulate probation with random compliance
                total = random.randint(5, 20)
                compliant = random.randint(0, total)
                token = kernel.identity._role_claims[f"{agent}:{role}"]
                token["receipts_submitted"] = total
                token["receipts_compliant"] = compliant
                kernel.identity._save_role_claims()
                kernel.identity.confirm_role(agent, role)

                # Create random receipts
                for _ in range(random.randint(1, 5)):
                    receipt = kernel.create_receipt(
                        agent,
                        random.choice(["STATUS", "SCAN", "REVIEW", "ACK"]),
                        payload={"data": random.randint(0, 1000)},
                    )
                    kernel.store_receipt(receipt)

            # Verify no panics occurred and all chains are valid
            for agent in agents:
                receipts = kernel.receipt.list_for_agent(agent)
                if len(receipts) >= 2:
                    valid, _ = kernel.receipt.verify_chain(agent)
                    assert valid is True

    def test_health_always_reportable(self) -> None:
        """For any Kernel state, health() must return a dict with expected keys."""
        with tempfile.TemporaryDirectory() as tmpdir:
            kernel = Kernel.boot(state_dir=Path(tmpdir))
            health = kernel.health()
            assert "status" in health
            assert "healthy" in health
            assert "booted" in health
            assert isinstance(health["healthy"], bool)
