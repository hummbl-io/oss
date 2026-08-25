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

"""Tests for EvolutionLineage."""

from __future__ import annotations

from datetime import datetime, timezone
import threading

import pytest

from hummbl_governance.evolution_lineage import (
    EvolutionLineage,
    ModificationRecord,
    VariantRecord,
)


def _variant(
    variant_id: str,
    parent_id: str | None = None,
    generation: int = 0,
    fitness: dict[str, float] | None = None,
) -> VariantRecord:
    return VariantRecord(
        id=variant_id,
        parent_id=parent_id,
        generation=generation,
        created_at=datetime(2026, 5, 3, tzinfo=timezone.utc),
        fitness=fitness or {"performance": 0.7, "alignment": 0.9},
    )


def _mod(modification_id: str, variant_id: str, modification_type: str = "prompt") -> ModificationRecord:
    return ModificationRecord(
        id=modification_id,
        variant_id=variant_id,
        modification_type=modification_type,
        diff="changed system prompt",
        rationale="test change",
    )


class TestVariantRecording:
    def test_record_root_variant(self):
        lineage = EvolutionLineage()
        lineage.record_variant(_variant("root"))
        assert lineage.variant_ids() == ["root"]

    def test_record_child_variant(self):
        lineage = EvolutionLineage()
        lineage.record_variant(_variant("root"))
        lineage.record_variant(_variant("child", parent_id="root", generation=1))
        assert lineage.variant_ids() == ["root", "child"]

    def test_duplicate_variant_rejected(self):
        lineage = EvolutionLineage()
        lineage.record_variant(_variant("root"))
        with pytest.raises(ValueError, match="already exists"):
            lineage.record_variant(_variant("root"))

    def test_unknown_parent_rejected(self):
        lineage = EvolutionLineage()
        with pytest.raises(ValueError, match="unknown parent"):
            lineage.record_variant(_variant("child", parent_id="missing", generation=1))

    def test_root_generation_must_be_zero(self):
        lineage = EvolutionLineage()
        with pytest.raises(ValueError, match="root variant generation"):
            lineage.record_variant(_variant("root", generation=1))

    def test_child_generation_must_increment_parent(self):
        lineage = EvolutionLineage()
        lineage.record_variant(_variant("root"))
        with pytest.raises(ValueError, match="parent generation"):
            lineage.record_variant(_variant("child", parent_id="root", generation=2))

    def test_self_parent_rejected(self):
        lineage = EvolutionLineage()
        with pytest.raises(ValueError, match="parent itself"):
            lineage.record_variant(_variant("root", parent_id="root"))

    def test_non_numeric_fitness_rejected(self):
        lineage = EvolutionLineage()
        bad = _variant("root", fitness={"alignment": "high"})  # type: ignore[arg-type]
        with pytest.raises(ValueError, match="numeric"):
            lineage.record_variant(bad)

    def test_empty_fitness_metric_name_rejected(self):
        lineage = EvolutionLineage()
        bad = _variant("root", fitness={"": 0.9})
        with pytest.raises(ValueError, match="metric names"):
            lineage.record_variant(bad)

    def test_non_finite_fitness_rejected(self):
        lineage = EvolutionLineage()
        bad = _variant("root", fitness={"alignment": float("nan")})
        with pytest.raises(ValueError, match="finite"):
            lineage.record_variant(bad)


class TestLineageQueries:
    def test_get_lineage_root_to_leaf(self):
        lineage = EvolutionLineage()
        lineage.record_variant(_variant("root"))
        lineage.record_variant(_variant("child", parent_id="root", generation=1))
        lineage.record_variant(_variant("grandchild", parent_id="child", generation=2))
        assert [v.id for v in lineage.get_lineage("grandchild")] == ["root", "child", "grandchild"]

    def test_get_unknown_lineage_raises_keyerror(self):
        lineage = EvolutionLineage()
        with pytest.raises(KeyError):
            lineage.get_lineage("missing")

    def test_get_children(self):
        lineage = EvolutionLineage()
        lineage.record_variant(_variant("root"))
        lineage.record_variant(_variant("child-a", parent_id="root", generation=1))
        lineage.record_variant(_variant("child-b", parent_id="root", generation=1))
        assert [v.id for v in lineage.get_children("root")] == ["child-a", "child-b"]

    def test_get_variant_missing_returns_none(self):
        lineage = EvolutionLineage()
        assert lineage.get_variant("missing") is None

    def test_record_variant_copies_mutable_input(self):
        lineage = EvolutionLineage()
        variant = VariantRecord(
            id="root",
            parent_id=None,
            generation=0,
            created_at=datetime(2026, 5, 3, tzinfo=timezone.utc),
            fitness={"alignment": 0.9},
            metadata={"owner": "codex", "nested": {"stage": "candidate"}},
        )
        lineage.record_variant(variant)

        variant.fitness["alignment"] = 0.1
        variant.metadata["owner"] = "mutated"
        variant.metadata["nested"]["stage"] = "mutated"

        stored = lineage.get_variant("root")
        assert stored is not None
        assert stored.fitness == {"alignment": 0.9}
        assert stored.metadata == {"owner": "codex", "nested": {"stage": "candidate"}}

    def test_get_variant_returns_mutation_safe_copy(self):
        lineage = EvolutionLineage()
        lineage.record_variant(VariantRecord(
            id="root",
            parent_id=None,
            generation=0,
            created_at=datetime(2026, 5, 3, tzinfo=timezone.utc),
            fitness={"alignment": 0.9},
            metadata={"nested": {"stage": "candidate"}},
        ))

        returned = lineage.get_variant("root")
        assert returned is not None
        returned.fitness["alignment"] = 0.1
        returned.metadata["nested"]["stage"] = "mutated"

        stored = lineage.get_variant("root")
        assert stored is not None
        assert stored.fitness == {"alignment": 0.9}
        assert stored.metadata == {"nested": {"stage": "candidate"}}

    def test_get_lineage_returns_mutation_safe_copies(self):
        lineage = EvolutionLineage()
        lineage.record_variant(VariantRecord(
            id="root",
            parent_id=None,
            generation=0,
            created_at=datetime(2026, 5, 3, tzinfo=timezone.utc),
            fitness={"alignment": 0.9},
            metadata={"nested": {"stage": "root"}},
        ))
        lineage.record_variant(_variant("child", parent_id="root", generation=1))

        returned = lineage.get_lineage("child")
        returned[0].fitness["alignment"] = 0.1
        returned[0].metadata["nested"]["stage"] = "mutated"

        stored = lineage.get_variant("root")
        assert stored is not None
        assert stored.fitness == {"alignment": 0.9}
        assert stored.metadata == {"nested": {"stage": "root"}}

    def test_get_children_returns_mutation_safe_copies(self):
        lineage = EvolutionLineage()
        lineage.record_variant(_variant("root"))
        lineage.record_variant(VariantRecord(
            id="child",
            parent_id="root",
            generation=1,
            created_at=datetime(2026, 5, 3, tzinfo=timezone.utc),
            fitness={"alignment": 0.9},
            metadata={"nested": {"stage": "child"}},
        ))

        returned = lineage.get_children("root")
        returned[0].fitness["alignment"] = 0.1
        returned[0].metadata["nested"]["stage"] = "mutated"

        stored = lineage.get_variant("child")
        assert stored is not None
        assert stored.fitness == {"alignment": 0.9}
        assert stored.metadata == {"nested": {"stage": "child"}}

    def test_clear_removes_variants(self):
        lineage = EvolutionLineage()
        lineage.record_variant(_variant("root"))
        lineage.clear()
        assert lineage.variant_ids() == []


class TestModifications:
    def test_record_modification(self):
        lineage = EvolutionLineage()
        lineage.record_variant(_variant("root"))
        lineage.record_modification(_mod("mod-1", "root"))
        assert [m.id for m in lineage.get_modifications("root")] == ["mod-1"]

    def test_modification_unknown_variant_rejected(self):
        lineage = EvolutionLineage()
        with pytest.raises(ValueError, match="unknown variant"):
            lineage.record_modification(_mod("mod-1", "missing"))

    def test_duplicate_modification_rejected_per_variant(self):
        lineage = EvolutionLineage()
        lineage.record_variant(_variant("root"))
        lineage.record_modification(_mod("mod-1", "root"))
        with pytest.raises(ValueError, match="already exists"):
            lineage.record_modification(_mod("mod-1", "root"))

    def test_unsupported_modification_type_rejected(self):
        lineage = EvolutionLineage()
        lineage.record_variant(_variant("root"))
        with pytest.raises(ValueError, match="unsupported"):
            lineage.record_modification(_mod("mod-1", "root", modification_type="network"))

    def test_invalid_validation_result_rejected(self):
        lineage = EvolutionLineage()
        lineage.record_variant(_variant("root"))
        mod = ModificationRecord(
            id="mod-1",
            variant_id="root",
            modification_type="prompt",
            diff="x",
            rationale="test",
            validation_result="UNKNOWN",
        )
        with pytest.raises(ValueError, match="validation_result"):
            lineage.record_modification(mod)

    def test_modification_to_dict_formats_timestamp(self):
        mod = _mod("mod-1", "root")
        data = mod.to_dict()
        assert data["id"] == "mod-1"
        assert data["timestamp"].endswith("Z")

    def test_modifications_are_copied_on_write_and_read(self):
        lineage = EvolutionLineage()
        lineage.record_variant(_variant("root"))
        modification = ModificationRecord(
            id="mod-1",
            variant_id="root",
            modification_type="prompt",
            diff="changed system prompt",
            rationale="test change",
            metadata={"owner": "codex", "nested": {"stage": "candidate"}},
        )
        lineage.record_modification(modification)

        modification.metadata["owner"] = "mutated"
        modification.metadata["nested"]["stage"] = "mutated"
        returned = lineage.get_modifications("root")[0]
        returned.metadata["owner"] = "also-mutated"
        returned.metadata["nested"]["stage"] = "also-mutated"

        stored = lineage.get_modifications("root")[0]
        assert stored.metadata == {"owner": "codex", "nested": {"stage": "candidate"}}


class TestDriftDetection:
    def test_no_drift_for_same_fitness_by_default(self):
        lineage = EvolutionLineage(drift_threshold=0.3)
        lineage.record_variant(_variant("root"))
        lineage.record_variant(_variant("child", parent_id="root", generation=1))
        assert lineage.detect_drift() == []

    def test_drift_detected_for_large_metric_delta(self):
        lineage = EvolutionLineage(drift_threshold=0.3)
        lineage.record_variant(_variant("root", fitness={"performance": 0.7, "alignment": 0.9}))
        lineage.record_variant(_variant(
            "child",
            parent_id="root",
            generation=1,
            fitness={"performance": 0.95, "alignment": 0.5},
        ))
        reports = lineage.detect_drift()
        assert len(reports) == 1
        assert reports[0].variant_id == "child"
        assert reports[0].drifted
        assert reports[0].deltas["alignment"] == pytest.approx(-0.4)

    def test_added_metric_flags_drift(self):
        lineage = EvolutionLineage()
        lineage.record_variant(_variant("root", fitness={"alignment": 0.9}))
        lineage.record_variant(_variant(
            "child",
            parent_id="root",
            generation=1,
            fitness={"alignment": 0.9, "resource_acquisition": 0.2},
        ))
        report = lineage.detect_drift()[0]
        assert report.added_metrics == ["resource_acquisition"]

    def test_removed_metric_flags_drift(self):
        lineage = EvolutionLineage()
        lineage.record_variant(_variant("root", fitness={"alignment": 0.9, "stability": 0.8}))
        lineage.record_variant(_variant(
            "child",
            parent_id="root",
            generation=1,
            fitness={"alignment": 0.9},
        ))
        report = lineage.detect_drift()[0]
        assert report.removed_metrics == ["stability"]

    def test_include_non_drifted_reports(self):
        lineage = EvolutionLineage()
        lineage.record_variant(_variant("root"))
        lineage.record_variant(_variant("child", parent_id="root", generation=1))
        reports = lineage.detect_drift(include_non_drifted=True)
        assert len(reports) == 1
        assert not reports[0].drifted

    def test_negative_threshold_rejected(self):
        lineage = EvolutionLineage()
        with pytest.raises(ValueError, match="threshold"):
            lineage.detect_drift(threshold=-0.1)

    def test_drift_report_to_dict_rounds_values(self):
        lineage = EvolutionLineage(drift_threshold=0.1)
        lineage.record_variant(_variant("root", fitness={"alignment": 0.9000001}))
        lineage.record_variant(_variant("child", parent_id="root", generation=1, fitness={"alignment": 0.7}))
        data = lineage.detect_drift()[0].to_dict()
        assert data["variant_id"] == "child"
        assert data["deltas"]["alignment"] == pytest.approx(-0.200000)


class TestSerializationAndThreading:
    def test_variant_to_dict_formats_timestamp(self):
        data = _variant("root").to_dict()
        assert data["created_at"] == "2026-05-03T00:00:00Z"
        assert data["fitness"] == {"performance": 0.7, "alignment": 0.9}

    def test_custom_allowed_modification_types(self):
        lineage = EvolutionLineage(allowed_modification_types=frozenset({"network"}))
        lineage.record_variant(_variant("root"))
        lineage.record_modification(_mod("mod-1", "root", modification_type="network"))
        assert lineage.get_modifications("root")[0].modification_type == "network"

    def test_threaded_recording(self):
        lineage = EvolutionLineage()
        lineage.record_variant(_variant("root"))

        def worker(index: int) -> None:
            lineage.record_variant(_variant(f"child-{index}", parent_id="root", generation=1))

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(10)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        assert len(lineage.get_children("root")) == 10
