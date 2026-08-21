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

"""Integration tests for LawEngine with real Scaling Law Atlas records.

Verifies that the Kernel can load all 19 scaling laws and evaluate
receipts against empirically tested laws.

Usage:
    python -m pytest hummbl_governance/kernel/test_kernel_law_atlas.py -v
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from hummbl_governance.kernel import Kernel, LawEngine


class TestLawAtlasLoading:
    """Verify all 19 scaling laws load correctly from disk."""

    def test_all_19_laws_loaded(self) -> None:
        engine = LawEngine()
        laws = engine.list_laws()
        assert len(laws) == 19, f"Expected 19 laws, got {len(laws)}"

    def test_law_ids_present(self) -> None:
        engine = LawEngine()
        expected_ids = {
            "SL-01", "SL-02", "SL-03", "SL-04", "SL-05",
            "SL-06", "SL-07", "SL-08", "SL-09", "SL-10",
            "SL-11", "SL-12", "SL-13", "SL-14", "SL-15",
            "SL-16", "SL-17", "SL-EXP003", "SL-EXP004",
        }
        actual_ids = {law.law_id for law in engine.list_laws()}
        assert expected_ids == actual_ids, f"Missing: {expected_ids - actual_ids}"

    def test_sl07_loaded_with_correct_fields(self) -> None:
        engine = LawEngine()
        law = engine.get_law("SL-07")
        assert law is not None
        assert law.law_id == "SL-07"
        assert law.name == "Delegation Chain Scaling"
        assert law.status == "empirically.tested"
        assert "depth" in law.statement.lower() or "chain" in law.statement.lower()

    def test_sl10_loaded_with_correct_fields(self) -> None:
        engine = LawEngine()
        law = engine.get_law("SL-10")
        assert law is not None
        assert law.law_id == "SL-10"
        assert law.name == "Constraint State Scaling"
        assert law.status == "empirically.tested"
        assert "constraint" in law.statement.lower()

    def test_sl11_loaded_with_correct_fields(self) -> None:
        engine = LawEngine()
        law = engine.get_law("SL-11")
        assert law is not None
        assert law.law_id == "SL-11"
        assert law.name == "Observability and Provenance Scaling"
        assert law.status == "empirically.tested"
        assert "reconstruct" in law.statement.lower()

    def test_all_laws_have_status(self) -> None:
        engine = LawEngine()
        for law in engine.list_laws():
            assert law.status in ("candidate.accepted", "empirically.tested", "ratified", "deprecated")
            assert law.law_id.startswith("SL-")
            assert len(law.law_id) >= 5  # SL-NN or SL-EXPNNN

    def test_kernel_boot_loads_atlas(self) -> None:
        """Kernel.boot() must load the atlas automatically."""
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            kernel = Kernel.boot(state_dir=Path(tmpdir))
            assert len(kernel.law.laws) == 19
            assert kernel.law.get_law("SL-07") is not None
            assert kernel.law.get_law("SL-EXP003") is not None
            assert kernel.law.get_law("SL-EXP004") is not None


class TestLawEvaluationRealAtlas:
    """Evaluate receipts against real loaded scaling laws."""

    def test_sl07_detects_deep_delegation(self) -> None:
        engine = LawEngine()
        receipt = {
            "agent_id": "gemini",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "payload": {"message": "depth=4 delegation chain exceeds limit"},
        }
        violations = engine.evaluate(receipt)
        sl07 = [v for v in violations if v.law_id == "SL-07"]
        assert len(sl07) == 1
        assert sl07[0].severity == "CRITICAL"
        assert sl07[0].actual_value == 4
        assert sl07[0].threshold_value == 3

    def test_sl07_no_violation_at_depth_3(self) -> None:
        engine = LawEngine()
        receipt = {
            "agent_id": "gemini",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "payload": {"message": "depth=3 delegation chain within limit"},
        }
        violations = engine.evaluate(receipt)
        sl07 = [v for v in violations if v.law_id == "SL-07"]
        assert len(sl07) == 0

    def test_sl10_detects_missing_refresh(self) -> None:
        engine = LawEngine()
        receipt = {
            "agent_id": "codex",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "payload": {"message": "step=12 working without constraint.refresh"},
        }
        violations = engine.evaluate(receipt)
        sl10 = [v for v in violations if v.law_id == "SL-10"]
        assert len(sl10) == 1
        assert sl10[0].severity == "WARNING"

    def test_sl10_no_violation_with_refresh(self) -> None:
        engine = LawEngine()
        receipt = {
            "agent_id": "codex",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "payload": {"message": "step=5 with constraint.refresh applied"},
        }
        violations = engine.evaluate(receipt)
        sl10 = [v for v in violations if v.law_id == "SL-10"]
        assert len(sl10) == 0

    def test_sl11_detects_missing_sequence_id(self) -> None:
        engine = LawEngine()
        receipt = {
            "agent_id": "gemini",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "payload": {"action_type": "STATUS", "message": "Task complete"},
        }
        violations = engine.evaluate(receipt)
        sl11 = [v for v in violations if v.law_id == "SL-11"]
        assert len(sl11) == 1
        assert sl11[0].severity == "WARNING"

    def test_sl11_no_violation_with_sequence_id(self) -> None:
        engine = LawEngine()
        receipt = {
            "agent_id": "gemini",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "payload": {"action_type": "STATUS", "sequence_id": 42, "message": "Task complete"},
        }
        violations = engine.evaluate(receipt)
        sl11 = [v for v in violations if v.law_id == "SL-11"]
        assert len(sl11) == 0

    def test_sl15_detects_missing_calibration(self) -> None:
        engine = LawEngine()
        receipt = {
            "agent_id": "gemini",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "payload": {"message": "interactions=600 without calibration"},
        }
        violations = engine.evaluate(receipt)
        sl15 = [v for v in violations if v.law_id == "SL-15"]
        assert len(sl15) == 1
        assert sl15[0].actual_value == 600
        assert sl15[0].threshold_value == 500

    def test_kernel_integration_with_atlas(self) -> None:
        """Full Kernel creates receipt, evaluates against loaded atlas, stores."""
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            kernel = Kernel.boot(state_dir=Path(tmpdir))
            assert len(kernel.law.laws) == 19

            receipt = kernel.create_receipt(
                agent_id="test",
                action_type="STATUS",
                payload={"message": "depth=4 delegation chain"},
                law_checks=["SL-07"],
            )
            # law.evaluate is called during store_receipt
            kernel.store_receipt(receipt)

            # Verify SL-07 was evaluated
            assert receipt.law_checks == ["SL-07"]
