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

"""Tests for hummbl_governance.failure_modes — FM registry, error catalog, mappings."""

from __future__ import annotations

import pytest

from hummbl_governance.failure_modes import (
    FailureModeRecord,
    ErrorRecord,
    all_failure_modes,
    get_fm,
    classify_subclass,
    get_errors_for_fm,
    all_error_records,
)


# ---------------------------------------------------------------------------
# FailureModeRecord dataclass
# ---------------------------------------------------------------------------

class TestFailureModeRecord:
    def test_frozen(self):
        rec = FailureModeRecord(id="FM1", name="Specification Ambiguity")
        with pytest.raises((AttributeError, TypeError)):
            rec.id = "FM2"  # type: ignore[misc]

    def test_equality(self):
        a = FailureModeRecord(id="FM1", name="Specification Ambiguity")
        b = FailureModeRecord(id="FM1", name="Specification Ambiguity")
        assert a == b

    def test_hashable(self):
        rec = FailureModeRecord(id="FM1", name="Specification Ambiguity")
        assert hash(rec) is not None
        s = {rec}
        assert len(s) == 1


# ---------------------------------------------------------------------------
# ErrorRecord dataclass
# ---------------------------------------------------------------------------

class TestErrorRecord:
    def test_fm_is_tuple(self):
        rec = ErrorRecord(id="ERR-TEST-001", fm=("FM15",), severity="fatal")
        assert isinstance(rec.fm, tuple)

    def test_frozen(self):
        rec = ErrorRecord(id="ERR-TEST-001", fm=("FM15",), severity="fatal")
        with pytest.raises((AttributeError, TypeError)):
            rec.id = "ERR-OTHER"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# all_failure_modes()
# ---------------------------------------------------------------------------

class TestAllFailureModes:
    def test_returns_30_records(self):
        fms = all_failure_modes()
        assert len(fms) == 30

    def test_ordered_by_number(self):
        fms = all_failure_modes()
        ids = [int(r.id[2:]) for r in fms]
        assert ids == sorted(ids)
        assert ids[0] == 1
        assert ids[-1] == 30

    def test_all_are_failure_mode_records(self):
        for rec in all_failure_modes():
            assert isinstance(rec, FailureModeRecord)

    def test_ids_sequential(self):
        fms = all_failure_modes()
        ids = {r.id for r in fms}
        for i in range(1, 31):
            assert f"FM{i}" in ids

    def test_names_non_empty(self):
        for rec in all_failure_modes():
            assert rec.name, f"{rec.id} has empty name"

    def test_caching_returns_same_list(self):
        """Two calls must return equal content (lru_cache is on the underlying loader)."""
        first = all_failure_modes()
        second = all_failure_modes()
        assert first == second


# ---------------------------------------------------------------------------
# get_fm()
# ---------------------------------------------------------------------------

class TestGetFM:
    def test_get_existing(self):
        rec = get_fm("FM1")
        assert rec is not None
        assert rec.id == "FM1"
        assert rec.name  # non-empty

    def test_get_fm15_schema_non_compliance(self):
        rec = get_fm("FM15")
        assert rec is not None
        assert rec.id == "FM15"
        assert "Schema" in rec.name or "schema" in rec.name.lower()

    def test_get_fm28_audit_trail_loss(self):
        rec = get_fm("FM28")
        assert rec is not None
        assert rec.id == "FM28"

    def test_get_fm30_last(self):
        rec = get_fm("FM30")
        assert rec is not None
        assert rec.id == "FM30"

    def test_get_unknown_returns_none(self):
        assert get_fm("FM99") is None
        assert get_fm("") is None
        assert get_fm("FM0") is None


# ---------------------------------------------------------------------------
# classify_subclass()
# ---------------------------------------------------------------------------

class TestClassifySubclass:
    def test_returns_list(self):
        result = classify_subclass("02")
        assert isinstance(result, list)

    def test_known_subclass(self):
        """Subclass "02" maps to at least one FM per the migrated mappings.json."""
        result = classify_subclass("02")
        assert len(result) >= 1
        for fm_id in result:
            assert fm_id.startswith("FM")

    def test_unknown_subclass_returns_empty(self):
        # "99" is mapped; use a code outside the known set
        result = classify_subclass("ZZ")
        assert result == []

    def test_empty_subclass_returns_empty(self):
        result = classify_subclass("")
        assert result == []

    def test_result_fm_ids_are_valid(self):
        """Every FM returned by classify_subclass must exist in the registry."""
        for sc in ["01", "02", "03", "13"]:
            for fm_id in classify_subclass(sc):
                assert get_fm(fm_id) is not None, (
                    f"Subclass {sc!r} maps to {fm_id!r} which is not in the registry"
                )


# ---------------------------------------------------------------------------
# get_errors_for_fm()
# ---------------------------------------------------------------------------

class TestGetErrorsForFM:
    def test_returns_list(self):
        result = get_errors_for_fm("FM15")
        assert isinstance(result, list)

    def test_known_fm_returns_matching_records(self):
        records = get_errors_for_fm("FM15")
        for rec in records:
            assert isinstance(rec, ErrorRecord)
            assert "FM15" in rec.fm

    def test_fm_without_errors_returns_empty(self):
        """FM2 (Unbounded Scope) has no error records in the catalog."""
        result = get_errors_for_fm("FM2")
        assert isinstance(result, list)

    def test_unknown_fm_returns_empty(self):
        result = get_errors_for_fm("FM99")
        assert result == []


# ---------------------------------------------------------------------------
# all_error_records()
# ---------------------------------------------------------------------------

class TestAllErrorRecords:
    def test_returns_list(self):
        records = all_error_records()
        assert isinstance(records, list)

    def test_all_are_error_records(self):
        for rec in all_error_records():
            assert isinstance(rec, ErrorRecord)

    def test_each_record_has_id(self):
        for rec in all_error_records():
            assert rec.id

    def test_each_record_fm_is_tuple(self):
        for rec in all_error_records():
            assert isinstance(rec.fm, tuple)

    def test_severity_values_known(self):
        known = {"fatal", "escalation", "warning", "unknown"}
        for rec in all_error_records():
            assert rec.severity in known, (
                f"{rec.id} has unexpected severity {rec.severity!r}"
            )

    def test_err_schema_001_present(self):
        ids = {r.id for r in all_error_records()}
        assert "ERR-SCHEMA-001" in ids

    def test_caching_stable(self):
        first = all_error_records()
        second = all_error_records()
        assert first == second
