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

"""Tests for base120.models — Operator, ApplyResult, OperatorTuple."""

from __future__ import annotations

import re
import uuid

import pytest

from base120.models import ApplyResult, Operator, OperatorTuple

# ---------------------------------------------------------------------------
# Operator dataclass
# ---------------------------------------------------------------------------

class TestOperator:
    def test_frozen(self):
        op = Operator(code="P6", name="POV Anchoring", transformation="P", definition="def")
        with pytest.raises((AttributeError, TypeError)):
            op.code = "P7"  # type: ignore[misc]

    def test_family_alias(self):
        op = Operator(code="DE1", name="5 Whys", transformation="DE", definition="def")
        assert op.family == "DE"
        assert op.family is op.transformation

    def test_hashable(self):
        op = Operator(code="P6", name="POV", transformation="P", definition="def")
        s = {op}
        assert len(s) == 1

    def test_equality(self):
        a = Operator(code="P6", name="POV", transformation="P", definition="def")
        b = Operator(code="P6", name="POV", transformation="P", definition="def")
        assert a == b


# ---------------------------------------------------------------------------
# OperatorTuple (NamedTuple)
# ---------------------------------------------------------------------------

class TestOperatorTuple:
    def test_is_named_tuple(self):
        t = OperatorTuple(id="P6", time="2026-04-14T00:00:00Z", state="rec", drift=0.15)
        assert isinstance(t, tuple)
        assert t.id == "P6"
        assert t.time == "2026-04-14T00:00:00Z"
        assert t.state == "rec"
        assert t.drift == 0.15

    def test_fields(self):
        assert OperatorTuple._fields == ("id", "time", "state", "drift")

    def test_unpacking(self):
        t = OperatorTuple(id="P6", time="t", state="s", drift=0.0)
        op_id, _time, _state, _drift = t
        assert op_id == "P6"


# ---------------------------------------------------------------------------
# ApplyResult + to_tuple()
# ---------------------------------------------------------------------------

class TestApplyResult:
    def _make(self, **kwargs: object) -> ApplyResult:
        defaults: dict[str, object] = {
            "code": "P6",
            "name": "Point-of-View Anchoring",
            "problem": "How to price?",
            "recommendation": "Anchor to compliance officer POV",
            "confidence": 0.85,
        }
        defaults.update(kwargs)
        return ApplyResult(**defaults)  # type: ignore[arg-type]

    def test_frozen(self):
        r = self._make()
        with pytest.raises((AttributeError, TypeError)):
            r.code = "P7"  # type: ignore[misc]

    def test_evidence_id_is_uuid(self):
        r = self._make()
        uuid.UUID(r.evidence_id)  # raises ValueError if not valid UUID

    def test_evidence_id_unique(self):
        a = self._make()
        b = self._make()
        assert a.evidence_id != b.evidence_id

    def test_metadata_default_empty(self):
        r = self._make()
        assert r.metadata == {}

    def test_metadata_stored(self):
        r = self._make(metadata={"model": "claude-sonnet-4-6"})
        assert r.metadata["model"] == "claude-sonnet-4-6"

    def test_to_tuple_returns_operator_tuple(self):
        r = self._make()
        t = r.to_tuple()
        assert isinstance(t, OperatorTuple)

    def test_to_tuple_id_matches_code(self):
        r = self._make(code="DE1")
        t = r.to_tuple()
        assert t.id == "DE1"

    def test_to_tuple_state_is_recommendation(self):
        r = self._make(recommendation="Do the thing")
        t = r.to_tuple()
        assert t.state == "Do the thing"

    def test_to_tuple_drift_is_complement_of_confidence(self):
        r = self._make(confidence=0.85)
        t = r.to_tuple()
        assert abs(t.drift - 0.15) < 1e-6

    def test_to_tuple_drift_at_certainty(self):
        r = self._make(confidence=1.0)
        t = r.to_tuple()
        assert t.drift == 0.0

    def test_to_tuple_drift_at_unknown(self):
        r = self._make(confidence=0.0)
        t = r.to_tuple()
        assert t.drift == 1.0

    def test_to_tuple_time_is_utc_iso(self):
        r = self._make()
        t = r.to_tuple()
        # Must be UTC ISO-8601 ending in Z
        assert t.time.endswith("Z")
        # Must match datetime pattern
        assert re.match(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", t.time)

    def test_to_tuple_time_advances(self):
        import time as _time
        r = self._make()
        t1 = r.to_tuple()
        _time.sleep(0.01)
        t2 = r.to_tuple()
        # time should be close but potentially different microseconds
        assert t1.time <= t2.time
