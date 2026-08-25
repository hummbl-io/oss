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

import random
import string
import tempfile
from pathlib import Path


from hummbl_governance.kernel import (
    EvidenceEngine,
    IdentityEngine,
    Kernel,
    ReceiptEngine,
    SequenceEngine,
)


def _tmp() -> Path:
    return Path(tempfile.mkdtemp(prefix="kernel_eval_"))


def _make_kernel(tmpdir: Path) -> Kernel:
    return Kernel.boot(state_dir=tmpdir)


# ===========================================================================
# 1. ADVERSARIAL EVALS
# ===========================================================================

class TestFuzzing:
    """Random inputs to find unexpected behavior."""

    def test_random_agent_ids(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = IdentityEngine(Path(tmpdir))
            chars = string.ascii_letters + string.digits + "_-"
            for _ in range(50):
                # Use min length 8 to avoid collisions in small char space
                random_id = "".join(random.choices(chars, k=random.randint(8, 64)))
                engine.register(random_id)
            assert len(engine._identities) == 50

    def test_random_payloads(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = ReceiptEngine(Path(tmpdir))
            for _ in range(100):
                payload = {
                    "random_string": "".join(random.choices(string.printable, k=100)),
                    "random_int": random.randint(-1000000, 1000000),
                    "random_float": random.random(),
                    "random_bool": random.choice([True, False]),
                    "random_list": [random.randint(0, 100) for _ in range(10)],
                }
                receipt = engine.create(agent_id="fuzz", action_type="RANDOM", payload=payload)
                engine.store(receipt)
            assert len(engine.list_for_agent("fuzz")) == 100

    def test_random_sequence_gaps(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = SequenceEngine(Path(tmpdir))
            engine.counters["fuzz"] = 100
            engine._save_counters()
            for _ in range(50):
                seq = random.randint(1, 1000)
                result = engine.validate("fuzz", seq)
                assert isinstance(result, bool)

    def test_random_evidence_claims(self) -> None:
        engine = EvidenceEngine()
        for _ in range(100):
            claim = "".join(random.choices(string.ascii_letters + " ", k=random.randint(5, 200)))
            sources = [f"src-{i}" for i in range(random.randint(0, 10))]
            methodology = "".join(random.choices(string.ascii_letters, k=random.randint(0, 100)))
            grade = engine.grade(claim, sources, methodology)
            assert grade.average() in ("A", "B", "C")
            assert grade.is_acceptable() in (True, False)


# ===========================================================================
# 8. CROSS-ENGINE INTEGRATION EVALS
# ===========================================================================
