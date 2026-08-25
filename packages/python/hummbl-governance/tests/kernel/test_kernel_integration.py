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


from hummbl_governance.kernel import (
    Kernel,
)


def _tmp() -> Path:
    return Path(tempfile.mkdtemp(prefix="kernel_eval_"))


def _make_kernel(tmpdir: Path) -> Kernel:
    return Kernel.boot(state_dir=tmpdir)


# ===========================================================================
# 1. ADVERSARIAL EVALS
# ===========================================================================

class TestCrossEngineIntegration:
    """Test engines interacting in realistic scenarios."""

    def test_full_officer_workflow(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            kernel = _make_kernel(Path(tmpdir))

            kernel.identity.register("officer", trust_tier="TRUSTED")
            kernel.identity.claim_role("officer", "AI-CCO")

            claim = kernel.identity._role_claims["officer:AI-CCO"]
            claim["receipts_submitted"] = 10
            claim["receipts_compliant"] = 10
            kernel.identity._save_role_claims()
            kernel.identity.confirm_role("officer", "AI-CCO")

            scan = kernel.create_receipt(
                agent_id="officer",
                action_type="COMPLIANCE_SCAN",
                payload={
                    "violations": [{"law_id": "SL-07", "severity": "CRITICAL"}],
                    "claims": [
                        {
                            "text": "SL-07 violation detected",
                            "sources": ["experiment-SL-07"],
                            "methodology": "Bus scan",
                        }
                    ],
                },
                law_checks=["SL-07"],
            )
            scan_id = kernel.store_receipt(scan)

            auth = kernel.exercise_authority(
                agent_id="officer",
                role_id="AI-CCO",
                authority="BLOCK_MERGE",
                context={"violation_severity": "CRITICAL"},
            )

            assert scan_id.startswith("r-")
            assert scan.sequence_id > 0
            assert scan.evidence_grade != "UNGRADED"
            assert auth.permitted is False

            valid, _ = kernel.receipt.verify_chain("officer")
            assert valid is True

    def test_multiple_agents_same_role(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            kernel = _make_kernel(Path(tmpdir))
            kernel.identity.register("competitor-a", trust_tier="TRUSTED")
            kernel.identity.register("competitor-b", trust_tier="TRUSTED")

            kernel.identity.claim_role("competitor-a", "AI-PE")
            kernel.identity.claim_role("competitor-b", "AI-PE")

            roles_a = kernel.identity.list_roles("competitor-a")
            roles_b = kernel.identity.list_roles("competitor-b")
            assert len(roles_a) == 1
            assert len(roles_b) == 1
            assert roles_a[0]["state"] == "PROBATION"
            assert roles_b[0]["state"] == "PROBATION"

    def test_receipt_triggers_law_evaluation(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            kernel = _make_kernel(Path(tmpdir))
            receipt = kernel.create_receipt(
                agent_id="test",
                action_type="STATUS",
                payload={"message": "depth=4 delegation"},
                law_checks=["SL-07"],
            )
            kernel.store_receipt(receipt)
            assert receipt.law_checks == ["SL-07"]

    def test_cascade_demotion(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            kernel = _make_kernel(Path(tmpdir))
            kernel.identity.register("cascade")
            kernel.identity.claim_role("cascade", "AI-PE")
            kernel.identity.claim_role("cascade", "AI-CCO")

            for key in kernel.identity._role_claims:
                if key.startswith("cascade:"):
                    kernel.identity._role_claims[key]["state"] = "CONFIRMED"
            kernel.identity._save_role_claims()
            kernel.identity._identities["cascade"].active_roles = ["AI-PE", "AI-CCO"]
            kernel.identity._save_identities()

            kernel.identity.demote_role("cascade", "AI-PE", "Metric failure")
            identity = kernel.identity.resolve("cascade")
            assert "AI-PE" not in identity.active_roles
            assert "AI-CCO" in identity.active_roles

    def test_schedule_triggers_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            kernel = _make_kernel(Path(tmpdir))
            sid = kernel.schedule.register("AI-CCO", "DAILY")

            loop_receipt = kernel.create_receipt(
                agent_id="devin",
                action_type="LOOP_EXECUTION",
                payload={"schedule_id": sid, "role_id": "AI-CCO"},
            )
            kernel.store_receipt(loop_receipt)
            kernel.schedule.record_run(sid, True)

            health = kernel.schedule.check_health(sid)
            assert health["status"] == "HEALTHY"
            assert len(kernel.receipt.list_for_agent("devin")) == 1
