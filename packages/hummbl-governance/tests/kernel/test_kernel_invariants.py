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
)
from hummbl_governance.kernel.invariants import KernelInvariant, KernelPanic


def _tmp() -> Path:
    return Path(tempfile.mkdtemp(prefix="kernel_eval_"))


def _make_kernel(tmpdir: Path) -> Kernel:
    return Kernel.boot(state_dir=tmpdir)


# ===========================================================================
# 1. ADVERSARIAL EVALS
# ===========================================================================

class TestInvariantEnforcement:
    """Every invariant must have a test verifying panic on violation."""

    def test_k1_empty_agent(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = ReceiptEngine(Path(tmpdir))
            with pytest.raises(KernelPanic) as exc:
                engine.create(agent_id="", action_type="TEST")
            assert exc.value.invariant == KernelInvariant.RECEIPT

    def test_k1_empty_action(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = ReceiptEngine(Path(tmpdir))
            with pytest.raises(KernelPanic) as exc:
                engine.create(agent_id="test", action_type="")
            assert exc.value.invariant == KernelInvariant.RECEIPT

    def test_k3_invalid_tier(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = IdentityEngine(Path(tmpdir))
            with pytest.raises(KernelPanic) as exc:
                engine.register("test", trust_tier="GOD")
            assert exc.value.invariant == KernelInvariant.IDENTITY

    def test_k3_duplicate_identity(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = IdentityEngine(Path(tmpdir))
            engine.register("test")
            with pytest.raises(KernelPanic) as exc:
                engine.register("test")
            assert exc.value.invariant == KernelInvariant.IDENTITY

    def test_k7_revoked_cannot_claim(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = IdentityEngine(Path(tmpdir))
            engine.register("bad", trust_tier="REVOKED")
            with pytest.raises(KernelPanic) as exc:
                engine.claim_role("bad", "AI-PE")
            assert exc.value.invariant == KernelInvariant.ROLE

    def test_k7_unregistered_cannot_claim(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = IdentityEngine(Path(tmpdir))
            with pytest.raises(KernelPanic) as exc:
                engine.claim_role("ghost", "AI-PE")
            assert exc.value.invariant == KernelInvariant.ROLE

    def test_kernel_not_booted(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            kernel = Kernel(state_dir=Path(tmpdir))
            with pytest.raises(KernelPanic) as exc:
                kernel.create_receipt("test", "TEST")
            assert exc.value.invariant == KernelInvariant.RECEIPT
            assert "not booted" in str(exc.value).lower()


# ===========================================================================
# 6. PERFORMANCE EVALS
# ===========================================================================
