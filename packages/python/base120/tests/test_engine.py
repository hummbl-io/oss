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

"""Tests for base120.engine — Engine: load, get, list, prompt, record."""

from __future__ import annotations

import pytest
from base120.engine import FAMILIES, Engine
from base120.models import ApplyResult, Operator


@pytest.fixture(scope="module")
def engine() -> Engine:
    return Engine()


# ---------------------------------------------------------------------------
# Operator loading
# ---------------------------------------------------------------------------


class TestOperatorLoading:
    def test_list_returns_120_operators(self, engine: Engine):
        assert len(engine.list()) == 120

    def test_all_operators_are_operator_instances(self, engine: Engine):
        for op in engine.list():
            assert isinstance(op, Operator)

    def test_each_operator_has_non_empty_fields(self, engine: Engine):
        for op in engine.list():
            assert op.code, f"Empty code on {op}"
            assert op.name, f"Empty name on {op.code}"
            assert op.transformation, f"Empty transformation on {op.code}"
            assert op.definition, f"Empty definition on {op.code}"

    def test_20_operators_per_family(self, engine: Engine):
        for fam in FAMILIES:
            ops = engine.list(family=fam)
            assert len(ops) == 20, f"Expected 20 {fam} operators, got {len(ops)}"

    def test_operators_ordered_within_family(self, engine: Engine):
        for fam in FAMILIES:
            ops = engine.list(family=fam)
            nums = [int("".join(c for c in op.code if c.isdigit())) for op in ops]
            assert nums == sorted(nums), f"{fam} operators not in numeric order"

    def test_full_list_ordered_by_family_then_number(self, engine: Engine):
        ops = engine.list()
        # Confirm all P before IN before CO etc.
        family_order = [FAMILIES.index(op.transformation) for op in ops]
        assert family_order == sorted(family_order)


# ---------------------------------------------------------------------------
# get()
# ---------------------------------------------------------------------------


class TestGet:
    def test_get_p6(self, engine: Engine):
        op = engine.get("P6")
        assert op is not None
        assert op.code == "P6"
        assert op.transformation == "P"
        assert "Point-of-View" in op.name or "Anchoring" in op.name

    def test_get_de1(self, engine: Engine):
        op = engine.get("DE1")
        assert op is not None
        assert op.transformation == "DE"

    def test_get_sy20(self, engine: Engine):
        op = engine.get("SY20")
        assert op is not None
        assert op.transformation == "SY"

    def test_get_unknown_returns_none(self, engine: Engine):
        assert engine.get("XX99") is None
        assert engine.get("") is None
        assert engine.get("P0") is None

    def test_get_all_120_codes(self, engine: Engine):
        """Every code returned by list() must resolve via get()."""
        for op in engine.list():
            assert engine.get(op.code) == op


# ---------------------------------------------------------------------------
# list() filtering
# ---------------------------------------------------------------------------


class TestList:
    def test_filter_p_family(self, engine: Engine):
        ops = engine.list(family="P")
        for op in ops:
            assert op.transformation == "P"

    def test_filter_case_insensitive(self, engine: Engine):
        lower = engine.list(family="de")
        upper = engine.list(family="DE")
        assert lower == upper

    def test_filter_unknown_family_empty(self, engine: Engine):
        ops = engine.list(family="ZZ")
        assert ops == []

    def test_no_filter_returns_all(self, engine: Engine):
        assert len(engine.list()) == 120


# ---------------------------------------------------------------------------
# families()
# ---------------------------------------------------------------------------


class TestFamilies:
    def test_returns_6_families(self, engine: Engine):
        assert len(engine.families()) == 6

    def test_canonical_order(self, engine: Engine):
        assert engine.families() == list(FAMILIES)


# ---------------------------------------------------------------------------
# prompt()
# ---------------------------------------------------------------------------


class TestPrompt:
    def test_returns_string(self, engine: Engine):
        p = engine.prompt("P6", "How to price?")
        assert isinstance(p, str)
        assert len(p) > 50

    def test_contains_code_and_name(self, engine: Engine):
        p = engine.prompt("P6", "test problem")
        assert "P6" in p

    def test_contains_definition(self, engine: Engine):
        op = engine.get("P6")
        assert op is not None
        p = engine.prompt("P6", "test")
        assert op.definition[:30] in p

    def test_contains_problem(self, engine: Engine):
        problem = "my specific problem statement"
        p = engine.prompt("P6", problem)
        assert problem in p

    def test_prompt_unknown_code_raises(self, engine: Engine):
        with pytest.raises(ValueError, match="Unknown operator code"):
            engine.prompt("XX99", "test")

    def test_prompt_requests_json_output(self, engine: Engine):
        p = engine.prompt("DE1", "test")
        assert "recommendation" in p
        assert "confidence" in p


# ---------------------------------------------------------------------------
# record()
# ---------------------------------------------------------------------------


class TestRecord:
    def test_returns_apply_result(self, engine: Engine):
        r = engine.record("P6", "problem", "recommendation", 0.9)
        assert isinstance(r, ApplyResult)

    def test_code_and_name_populated(self, engine: Engine):
        r = engine.record("P6", "p", "rec", 0.8)
        assert r.code == "P6"
        op = engine.get("P6")
        assert r.name == op.name  # type: ignore[union-attr]

    def test_confidence_stored(self, engine: Engine):
        r = engine.record("P6", "p", "rec", 0.75)
        assert r.confidence == 0.75

    def test_metadata_passed_through(self, engine: Engine):
        r = engine.record("P6", "p", "rec", 0.9, model="claude-sonnet-4-6", session="s1")
        assert r.metadata["model"] == "claude-sonnet-4-6"
        assert r.metadata["session"] == "s1"

    def test_unknown_code_raises(self, engine: Engine):
        with pytest.raises(ValueError):
            engine.record("XX99", "p", "rec", 0.5)

    def test_confidence_above_1_raises(self, engine: Engine):
        with pytest.raises(ValueError, match="confidence"):
            engine.record("P6", "p", "rec", 1.1)

    def test_confidence_below_0_raises(self, engine: Engine):
        with pytest.raises(ValueError, match="confidence"):
            engine.record("P6", "p", "rec", -0.1)

    def test_confidence_at_boundaries(self, engine: Engine):
        engine.record("P6", "p", "rec", 0.0)
        engine.record("P6", "p", "rec", 1.0)

    def test_to_tuple_roundtrip(self, engine: Engine):
        r = engine.record("DE1", "what is the root cause?", "start with why", 0.88)
        t = r.to_tuple()
        assert t.id == "DE1"
        assert t.state == "start with why"
        assert abs(t.drift - 0.12) < 1e-6
