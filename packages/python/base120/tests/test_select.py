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

"""Tests for Engine.select() — operator recommendation from problem description."""

from __future__ import annotations

import pytest
from base120.engine import Engine, _tokenize
from base120.models import Operator

_engine = Engine()


# ---------------------------------------------------------------------------
# Return shape
# ---------------------------------------------------------------------------


class TestReturnShape:
    def test_returns_list(self):
        result = _engine.select("how to improve governance?")
        assert isinstance(result, list)

    def test_each_item_is_operator_float_tuple(self):
        result = _engine.select("root cause analysis")
        for item in result:
            assert isinstance(item, tuple) and len(item) == 2
            op, score = item
            assert isinstance(op, Operator)
            assert isinstance(score, float)

    def test_default_n_is_5(self):
        result = _engine.select("problem")
        assert len(result) == 5

    def test_custom_n(self):
        result = _engine.select("problem", n=3)
        assert len(result) == 3

    def test_n_1(self):
        result = _engine.select("problem", n=1)
        assert len(result) == 1

    def test_n_exceeds_total_returns_all(self):
        result = _engine.select("problem", n=999)
        assert len(result) == 120

    def test_n_0_returns_empty(self):
        result = _engine.select("problem", n=0)
        assert result == []

    def test_negative_n_raises(self):
        with pytest.raises(ValueError, match="non-negative"):
            _engine.select("problem", n=-1)

    def test_empty_problem_returns_n(self):
        result = _engine.select("", n=5)
        assert len(result) == 5


# ---------------------------------------------------------------------------
# Score invariants
# ---------------------------------------------------------------------------


class TestScores:
    def test_scores_in_unit_interval(self):
        for _, score in _engine.select("governance risk analysis", n=20):
            assert 0.0 <= score <= 1.0, f"Score out of range: {score}"

    def test_sorted_descending(self):
        result = _engine.select("decompose root cause stakeholder", n=10)
        scores = [s for _, s in result]
        assert scores == sorted(scores, reverse=True)

    def test_no_duplicates(self):
        result = _engine.select("problem", n=10)
        codes = [op.code for op, _ in result]
        assert len(codes) == len(set(codes))


# ---------------------------------------------------------------------------
# Relevance — known matches from productization matrix
# ---------------------------------------------------------------------------


class TestRelevance:
    def test_root_cause_surfaces_de1(self):
        codes = [op.code for op, _ in _engine.select("root cause why", n=10)]
        assert "DE1" in codes, f"DE1 not in top 10 for 'root cause why': {codes}"

    def test_premortem_surfaces_in2(self):
        codes = [op.code for op, _ in _engine.select("premortem analysis", n=10)]
        assert "IN2" in codes, f"IN2 not in top 10 for 'premortem analysis': {codes}"

    def test_stakeholder_surfaces_p2(self):
        codes = [op.code for op, _ in _engine.select("stakeholder mapping", n=10)]
        assert "P2" in codes, f"P2 not in top 10 for 'stakeholder mapping': {codes}"

    def test_gibberish_still_returns_n(self):
        result = _engine.select("zxcvbnm qwerty asdfgh", n=5)
        assert len(result) == 5

    def test_exact_operator_name_scores_highly(self):
        # "5 Whys" is in DE1's name — should score very high
        result = _engine.select("5 whys", n=1)
        assert result[0][0].code == "DE1"

    def test_governance_problem_biases_toward_sy_or_de(self):
        result = _engine.select("governance patterns risk resilience", n=5)
        families = {op.family for op, _ in result}
        # Governance operators are primarily in SY and DE families
        assert families & {"SY", "DE"}, f"No SY/DE in top 5: {families}"


# ---------------------------------------------------------------------------
# Tie-breaking — equal primary scores order by operator specificity
# ---------------------------------------------------------------------------


class TestTieBreaking:
    def test_score_ties_broken_by_specificity(self):
        # A single-token problem gives every containing operator the same
        # primary score (overlap / 1). Order among them must follow
        # specificity: shorter operator text ranks first.
        token_ops: dict[str, list[int]] = {}
        for op in _engine.list():
            toks = _tokenize(op.name + " " + op.definition)
            for tok in toks:
                token_ops.setdefault(tok, []).append(len(toks))
        shared = [
            tok
            for tok, sizes in token_ops.items()
            if len(sizes) >= 2 and len(set(sizes)) >= 2
        ]
        if not shared:
            pytest.skip("no token shared by operators of differing sizes")
        token = shared[0]
        k = len(token_ops[token])
        result = _engine.select(token, n=k)
        assert len({s for _, s in result}) == 1
        sizes = [
            len(_tokenize(op.name + " " + op.definition)) for op, _ in result
        ]
        assert sizes == sorted(sizes), (
            f"equal scores not ordered by ascending operator size: {sizes}"
        )

    def test_select_still_returns_operator_score_tuples(self):
        for item in _engine.select("decompose", n=3):
            assert len(item) == 2
