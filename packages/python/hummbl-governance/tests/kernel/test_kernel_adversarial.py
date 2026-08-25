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

"""Comprehensive evaluation suite for the HUMMBL Governance Kernel.

Categories:
  1. Adversarial — try to bypass invariants, forge receipts, escalate privileges
  2. Edge Cases — empty strings, unicode, max sizes, null bytes, injection
  3. Race Conditions — concurrent receipt creation, shared state mutation
  4. Recovery — corrupted chains, missing files, truncated JSONL
  5. Invariant Enforcement — verify every panic triggers on violation
  6. Performance — large receipt volumes, long chains, bulk operations
  7. Fuzzing — random payloads, random agents, random sequences
  8. Cross-Engine Integration — Receipt + Law + Identity + Authority together

Usage:
    python -m pytest hummbl_governance/kernel/test_kernel_evals.py -v
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from hummbl_governance.kernel import (
    IdentityEngine,
    Kernel,
    ReceiptEngine,
    SequenceEngine,
)
from hummbl_governance.kernel.invariants import KernelInvariant, KernelPanic


def _tmp() -> Path:
    return Path(tempfile.mkdtemp(prefix="kernel_eval_"))


def _make_kernel(tmpdir: Path) -> Kernel:
    return Kernel.boot(state_dir=tmpdir)


# ===========================================================================
# 1. ADVERSARIAL EVALS
# ===========================================================================

class TestAdversarialReceiptEngine:
    """Try to forge receipts, bypass signatures, or corrupt chains."""

    def test_forged_signature_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = ReceiptEngine(Path(tmpdir))
            receipt = engine.create(agent_id="attacker", action_type="FORGE")
            receipt.signature = "a" * 64
            assert engine.validate(receipt) is False

    def test_tampered_payload_detected(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = ReceiptEngine(Path(tmpdir))
            receipt = engine.create(agent_id="attacker", action_type="TAMPER", payload={"x": 1})
            receipt.payload["x"] = 2
            assert engine.validate(receipt) is False

    def test_replay_attack(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = ReceiptEngine(Path(tmpdir))
            receipt = engine.create(agent_id="attacker", action_type="REPLAY")
            engine.store(receipt)
            engine.store(receipt)
            assert len(engine.list_for_agent("attacker")) == 2

    def test_chain_break_on_missing_prev(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = ReceiptEngine(Path(tmpdir))
            r1 = engine.create(agent_id="attacker", action_type="FIRST")
            engine.store(r1)
            r2 = engine.create(agent_id="attacker", action_type="SECOND", prev_receipt_hash="wrong_hash")
            engine.store(r2)
            valid, _ = engine.verify_chain("attacker")
            assert valid is False

    def test_empty_agent_id_panics(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = ReceiptEngine(Path(tmpdir))
            with pytest.raises(KernelPanic) as exc:
                engine.create(agent_id="", action_type="TEST")
            assert exc.value.invariant == KernelInvariant.RECEIPT

    def test_null_bytes_in_payload(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = ReceiptEngine(Path(tmpdir))
            receipt = engine.create(
                agent_id="attacker",
                action_type="INJECT",
                payload={"message": "hello\x00world"},
            )
            assert receipt.payload["message"] == "hello\x00world"
            engine.store(receipt)
            assert len(engine.list_for_agent("attacker")) == 1

class TestAdversarialIdentityEngine:
    """Try to escalate privileges, claim roles without permission."""

    def test_revoked_agent_cannot_claim(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = IdentityEngine(Path(tmpdir))
            engine.register("bad-agent", trust_tier="REVOKED")
            with pytest.raises(KernelPanic) as exc:
                engine.claim_role("bad-agent", "AI-PE")
            assert exc.value.invariant == KernelInvariant.ROLE

    def test_unregistered_agent_cannot_claim(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = IdentityEngine(Path(tmpdir))
            with pytest.raises(KernelPanic) as exc:
                engine.claim_role("ghost", "AI-PE")
            assert exc.value.invariant == KernelInvariant.ROLE

    def test_self_confirm_without_receipts(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = IdentityEngine(Path(tmpdir))
            engine.register("impatient")
            engine.claim_role("impatient", "AI-PE")
            assert engine.confirm_role("impatient", "AI-PE") is False

    def test_impersonate_existing_id(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = IdentityEngine(Path(tmpdir))
            engine.register("victim", trust_tier="OWNER")
            with pytest.raises(KernelPanic) as exc:
                engine.register("victim", trust_tier="PROBATIONARY")
            assert exc.value.invariant == KernelInvariant.IDENTITY

    def test_demote_without_role(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = IdentityEngine(Path(tmpdir))
            engine.register("agent")
            assert engine.demote_role("agent", "AI-PE", "reason") is False

class TestAdversarialAuthorityEngine:
    """Try to exercise authority without holding the role."""

    def test_no_role_no_authority(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            kernel = _make_kernel(Path(tmpdir))
            kernel.identity.register("rogue")
            check = kernel.exercise_authority(
                agent_id="rogue", role_id="AI-CCO", authority="BLOCK_MERGE", context={},
            )
            assert check.permitted is False

    def test_role_without_charter_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            kernel = _make_kernel(Path(tmpdir))
            kernel.identity.register("agent")
            check = kernel.check_authority("agent", "FAKE-ROLE", "DO_ANYTHING", {})
            assert check.permitted is False

class TestAdversarialSequenceEngine:
    """Try to manipulate sequence ordering."""

    def test_duplicate_sequence_id(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = SequenceEngine(Path(tmpdir))
            engine.next("agent")
            engine.next("agent")
            assert engine.validate("agent", 1) is False

    def test_negative_sequence_id(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = SequenceEngine(Path(tmpdir))
            assert engine.validate("agent", -1) is False

    def test_giant_sequence_gap(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = SequenceEngine(Path(tmpdir))
            engine.counters["agent"] = 5
            engine._save_counters()
            assert engine.validate("agent", 1000) is True


# ===========================================================================
# 2. EDGE CASE EVALS
# ===========================================================================
