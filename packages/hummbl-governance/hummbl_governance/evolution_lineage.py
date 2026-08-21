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

"""Evolution Lineage -- In-memory lineage tracking for evolvable AI variants.

Tracks variant ancestry, self-modification records, and parent-to-child fitness
drift for governed evolvable AI systems. This module does not create or modify
AI systems; it records and validates governance metadata about variants.

Usage::

    from datetime import datetime, timezone
    from hummbl_governance.evolution_lineage import EvolutionLineage, VariantRecord

    lineage = EvolutionLineage()
    lineage.record_variant(VariantRecord(
        id="baseline",
        parent_id=None,
        generation=0,
        created_at=datetime.now(timezone.utc),
        fitness={"performance": 0.7, "alignment": 0.9},
    ))

    ancestry = lineage.get_lineage("baseline")

Stdlib-only. Thread-safe.
"""

from __future__ import annotations

import math
import threading
from copy import deepcopy
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


DEFAULT_ALLOWED_MODIFICATION_TYPES: frozenset[str] = frozenset({
    "code",
    "prompt",
    "weight",
    "memory",
    "config",
    "architecture",
    "fitness",
})


@dataclass(frozen=True)
class VariantRecord:
    """A governed eAI variant in an ancestry graph."""

    id: str
    parent_id: str | None
    generation: int
    created_at: datetime
    fitness: dict[str, float]
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "parent_id": self.parent_id,
            "generation": self.generation,
            "created_at": _format_timestamp(self.created_at),
            "fitness": dict(self.fitness),
            "metadata": deepcopy(self.metadata),
        }


@dataclass(frozen=True)
class ModificationRecord:
    """A recorded self-modification event for a variant."""

    id: str
    variant_id: str
    modification_type: str
    diff: str
    rationale: str
    validation_result: str = "PENDING"
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "variant_id": self.variant_id,
            "modification_type": self.modification_type,
            "diff": self.diff,
            "rationale": self.rationale,
            "validation_result": self.validation_result,
            "timestamp": _format_timestamp(self.timestamp),
            "metadata": deepcopy(self.metadata),
        }


@dataclass(frozen=True)
class EvolutionDriftReport:
    """Parent-to-child fitness drift for a variant."""

    variant_id: str
    parent_id: str
    generation: int
    max_delta: float
    threshold: float
    drifted: bool
    deltas: dict[str, float]
    added_metrics: list[str]
    removed_metrics: list[str]
    timestamp: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "variant_id": self.variant_id,
            "parent_id": self.parent_id,
            "generation": self.generation,
            "max_delta": round(self.max_delta, 6),
            "threshold": self.threshold,
            "drifted": self.drifted,
            "deltas": {k: round(v, 6) for k, v in self.deltas.items()},
            "added_metrics": list(self.added_metrics),
            "removed_metrics": list(self.removed_metrics),
            "timestamp": self.timestamp,
        }


class EvolutionLineage:
    """Track variant history and self-modification records.

    Thread-safe. Maintains an in-memory ancestry graph. Persistence belongs in
    a later storage adapter so the foundation primitive stays small and easy to
    test.

    Args:
        drift_threshold: Absolute parent-to-child fitness delta that flags
            drift for any shared metric.
        allowed_modification_types: Valid modification_type values.
    """

    def __init__(
        self,
        drift_threshold: float = 0.3,
        allowed_modification_types: frozenset[str] | None = None,
    ) -> None:
        if drift_threshold < 0:
            raise ValueError("drift_threshold must be non-negative")
        self._drift_threshold = drift_threshold
        self._allowed_modification_types = allowed_modification_types or DEFAULT_ALLOWED_MODIFICATION_TYPES
        self._variants: dict[str, VariantRecord] = {}
        self._modifications: dict[str, list[ModificationRecord]] = {}
        self._children: dict[str, list[str]] = {}
        self._lock = threading.RLock()

    def record_variant(self, variant: VariantRecord) -> None:
        """Register a variant in the lineage graph.

        Raises:
            ValueError: If the variant is invalid, duplicated, references an
                unknown parent, or has a generation inconsistent with its parent.
        """
        _validate_variant_shape(variant)

        with self._lock:
            if variant.id in self._variants:
                raise ValueError(f"variant already exists: {variant.id}")

            if variant.parent_id is None:
                if variant.generation != 0:
                    raise ValueError("root variant generation must be 0")
            else:
                parent = self._variants.get(variant.parent_id)
                if parent is None:
                    raise ValueError(f"unknown parent variant: {variant.parent_id}")
                expected_generation = parent.generation + 1
                if variant.generation != expected_generation:
                    raise ValueError(
                        f"variant generation must be parent generation + 1 "
                        f"({expected_generation})"
                    )

            stored = _copy_variant(variant)
            self._variants[stored.id] = stored
            self._modifications.setdefault(stored.id, [])
            if stored.parent_id is not None:
                self._children.setdefault(stored.parent_id, []).append(stored.id)

    def record_modification(self, modification: ModificationRecord) -> None:
        """Record a self-modification event for an existing variant."""
        _validate_modification_shape(modification)

        with self._lock:
            if modification.variant_id not in self._variants:
                raise ValueError(f"unknown variant: {modification.variant_id}")
            if modification.modification_type not in self._allowed_modification_types:
                raise ValueError(f"unsupported modification type: {modification.modification_type}")
            existing_ids = {m.id for m in self._modifications[modification.variant_id]}
            if modification.id in existing_ids:
                raise ValueError(f"modification already exists for variant: {modification.id}")
            self._modifications[modification.variant_id].append(_copy_modification(modification))

    def get_variant(self, variant_id: str) -> VariantRecord | None:
        """Return a variant by ID, or None if absent."""
        with self._lock:
            variant = self._variants.get(variant_id)
            return _copy_variant(variant) if variant is not None else None

    def get_lineage(self, variant_id: str) -> list[VariantRecord]:
        """Return ancestry from root to the requested variant.

        Raises:
            KeyError: If variant_id is unknown.
            ValueError: If a cycle is detected in stored lineage state.
        """
        with self._lock:
            if variant_id not in self._variants:
                raise KeyError(variant_id)

            lineage: list[VariantRecord] = []
            seen: set[str] = set()
            current_id: str | None = variant_id

            while current_id is not None:
                if current_id in seen:
                    raise ValueError(f"lineage cycle detected at variant: {current_id}")
                seen.add(current_id)

                current = self._variants[current_id]
                lineage.append(_copy_variant(current))
                current_id = current.parent_id

            lineage.reverse()
            return lineage

    def get_children(self, variant_id: str) -> list[VariantRecord]:
        """Return direct child variants."""
        with self._lock:
            if variant_id not in self._variants:
                raise KeyError(variant_id)
            return [
                _copy_variant(self._variants[child_id])
                for child_id in self._children.get(variant_id, [])
            ]

    def get_modifications(self, variant_id: str) -> list[ModificationRecord]:
        """Return recorded modifications for a variant."""
        with self._lock:
            if variant_id not in self._variants:
                raise KeyError(variant_id)
            return [
                _copy_modification(modification)
                for modification in self._modifications.get(variant_id, [])
            ]

    def detect_drift(
        self,
        threshold: float | None = None,
        include_non_drifted: bool = False,
    ) -> list[EvolutionDriftReport]:
        """Detect parent-to-child fitness drift.

        Args:
            threshold: Override the configured drift threshold.
            include_non_drifted: Include reports for variants below threshold.

        Returns:
            Drift reports ordered by generation, then variant ID.
        """
        drift_threshold = self._drift_threshold if threshold is None else threshold
        if drift_threshold < 0:
            raise ValueError("threshold must be non-negative")

        with self._lock:
            variants = list(self._variants.values())
            reports: list[EvolutionDriftReport] = []
            timestamp = _utc_now()

            for variant in sorted(variants, key=lambda v: (v.generation, v.id)):
                if variant.parent_id is None:
                    continue
                parent = self._variants[variant.parent_id]
                report = _build_drift_report(parent, variant, drift_threshold, timestamp)
                if report.drifted or include_non_drifted:
                    reports.append(report)

            return reports

    def variant_ids(self) -> list[str]:
        """List variant IDs ordered by generation, then ID."""
        with self._lock:
            return [
                variant.id
                for variant in sorted(self._variants.values(), key=lambda v: (v.generation, v.id))
            ]

    def clear(self) -> None:
        """Clear all variants and modifications."""
        with self._lock:
            self._variants.clear()
            self._modifications.clear()
            self._children.clear()


def _validate_variant_shape(variant: VariantRecord) -> None:
    if not variant.id:
        raise ValueError("variant id is required")
    if variant.parent_id == variant.id:
        raise ValueError("variant cannot parent itself")
    if variant.generation < 0:
        raise ValueError("variant generation must be non-negative")
    for key, value in variant.fitness.items():
        if not key:
            raise ValueError("fitness metric names cannot be empty")
        if isinstance(value, bool) or not isinstance(value, int | float):
            raise ValueError(f"fitness metric must be numeric: {key}")
        if not math.isfinite(value):
            raise ValueError(f"fitness metric must be finite: {key}")


def _validate_modification_shape(modification: ModificationRecord) -> None:
    if not modification.id:
        raise ValueError("modification id is required")
    if not modification.variant_id:
        raise ValueError("modification variant_id is required")
    if not modification.modification_type:
        raise ValueError("modification_type is required")
    if modification.validation_result not in {"PASS", "FAIL", "PENDING"}:
        raise ValueError("validation_result must be PASS, FAIL, or PENDING")


def _copy_variant(variant: VariantRecord) -> VariantRecord:
    return VariantRecord(
        id=variant.id,
        parent_id=variant.parent_id,
        generation=variant.generation,
        created_at=variant.created_at,
        fitness=dict(variant.fitness),
        metadata=deepcopy(variant.metadata),
    )


def _copy_modification(modification: ModificationRecord) -> ModificationRecord:
    return ModificationRecord(
        id=modification.id,
        variant_id=modification.variant_id,
        modification_type=modification.modification_type,
        diff=modification.diff,
        rationale=modification.rationale,
        validation_result=modification.validation_result,
        timestamp=modification.timestamp,
        metadata=deepcopy(modification.metadata),
    )


def _build_drift_report(
    parent: VariantRecord,
    variant: VariantRecord,
    threshold: float,
    timestamp: str,
) -> EvolutionDriftReport:
    parent_keys = set(parent.fitness)
    variant_keys = set(variant.fitness)
    shared_keys = parent_keys & variant_keys
    deltas = {
        key: variant.fitness[key] - parent.fitness[key]
        for key in sorted(shared_keys)
    }
    max_delta = max((abs(delta) for delta in deltas.values()), default=0.0)
    added_metrics = sorted(variant_keys - parent_keys)
    removed_metrics = sorted(parent_keys - variant_keys)
    drifted = max_delta >= threshold or bool(added_metrics) or bool(removed_metrics)

    return EvolutionDriftReport(
        variant_id=variant.id,
        parent_id=parent.id,
        generation=variant.generation,
        max_delta=max_delta,
        threshold=threshold,
        drifted=drifted,
        deltas=deltas,
        added_metrics=added_metrics,
        removed_metrics=removed_metrics,
        timestamp=timestamp,
    )


def _format_timestamp(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
