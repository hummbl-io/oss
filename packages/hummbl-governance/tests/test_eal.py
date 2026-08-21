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

"""Tests for hummbl_governance.eal — Execution Assurance Layer.

Exercises all conformance fixtures from the AAA repo:
- Validation fixtures (T1-T18): contract+receipt → classification
- Receipt fixtures (R1-R5): receipt schema → deterministic report
- Temporal fixtures (T6-T10): cross-epoch revalidation
- Compat fixtures (C1-C9): contract evolution compatibility
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from hummbl_governance.eal import (
    EAL_PRECEDENCE_INDEX,
    COMPAT_PRECEDENCE_INDEX,
    evaluate_validation,
    evaluate_temporal_validation,
    evaluate_compat,
    sha256_hex,
)

CONFORMANCE_DIR = Path(__file__).parent / "conformance"


def _load_fixtures(subdir: str) -> list[tuple[str, dict]]:
    """Load all JSON fixtures from a conformance subdirectory."""
    fixture_dir = CONFORMANCE_DIR / subdir
    if not fixture_dir.exists():
        return []
    fixtures = []
    for path in sorted(fixture_dir.glob("*.json")):
        with path.open("r", encoding="utf-8") as f:
            fixtures.append((path.name, json.load(f)))
    return fixtures


def _verify_reason_order(report: dict, precedence_index: dict[str, int]) -> None:
    """Assert reason_codes are precedence-ordered and primary matches [0]."""
    reason_codes = report["reason_codes"]
    assert reason_codes, "reason_codes must not be empty"
    assert report["primary_reason_code"] == reason_codes[0], (
        f"primary_reason_code ({report['primary_reason_code']}) != reason_codes[0] ({reason_codes[0]})"
    )
    expected = sorted(reason_codes, key=lambda c: precedence_index[c])
    assert expected == reason_codes, f"reason_codes not in precedence order: {reason_codes}"


def _verify_hash(report: dict, expected_hash: str) -> None:
    """Assert canonical JSON hash matches declared hash."""
    digest = sha256_hex(report)
    assert digest == expected_hash, f"hash mismatch: {digest} != {expected_hash}"


# --- Validation fixtures (T1-T18) ---

VALIDATION_FIXTURES = _load_fixtures("fixtures")


@pytest.mark.parametrize("name,fixture", VALIDATION_FIXTURES, ids=[f[0] for f in VALIDATION_FIXTURES])
def test_validation_fixture(name: str, fixture: dict) -> None:
    inputs = fixture["inputs"]
    expected = fixture["expected_report"]

    if "contract" in inputs and "receipt" in inputs:
        derived = evaluate_validation(inputs["contract"], inputs["receipt"])
        assert derived == expected, f"{name}: derived report != expected"

    _verify_reason_order(expected, EAL_PRECEDENCE_INDEX)
    _verify_hash(expected, fixture["expected_report_sha256"])


# --- Receipt fixtures (R1-R5) ---

RECEIPT_FIXTURES = _load_fixtures("fixtures_receipt")


@pytest.mark.parametrize("name,fixture", RECEIPT_FIXTURES, ids=[f[0] for f in RECEIPT_FIXTURES])
def test_receipt_fixture(name: str, fixture: dict) -> None:
    inputs = fixture["inputs"]
    expected = fixture["expected_report"]

    derived = evaluate_validation(inputs["contract"], inputs["receipt"])
    assert derived == expected, f"{name}: derived receipt report != expected"

    _verify_reason_order(expected, EAL_PRECEDENCE_INDEX)
    _verify_hash(expected, fixture["expected_report_sha256"])


# --- Temporal fixtures (T6-T10) ---

TEMPORAL_FIXTURES = _load_fixtures("fixtures_temporal")


@pytest.mark.parametrize("name,fixture", TEMPORAL_FIXTURES, ids=[f[0] for f in TEMPORAL_FIXTURES])
def test_temporal_fixture(name: str, fixture: dict) -> None:
    inputs = fixture["inputs"]
    expected = fixture["expected_report"]

    derived = evaluate_temporal_validation(
        inputs["contract_a"],
        inputs["contract_b"],
        inputs["receipt"],
    )
    assert derived == expected, f"{name}: derived temporal report != expected"

    _verify_reason_order(expected, EAL_PRECEDENCE_INDEX)
    _verify_hash(expected, fixture["expected_report_sha256"])


# --- Compat fixtures (C1-C9) ---

COMPAT_FIXTURES = _load_fixtures("fixtures_compat")


@pytest.mark.parametrize("name,fixture", COMPAT_FIXTURES, ids=[f[0] for f in COMPAT_FIXTURES])
def test_compat_fixture(name: str, fixture: dict) -> None:
    inputs = fixture["inputs"]
    expected = fixture["expected_compat_report"]

    derived = evaluate_compat(inputs["contract_a"], inputs["contract_b"])
    assert derived == expected, f"{name}: derived compat report != expected"

    _verify_reason_order(expected, COMPAT_PRECEDENCE_INDEX)
    _verify_hash(expected, fixture["expected_compat_report_sha256"])


# --- Unit tests for core functions ---

def test_precedence_completeness() -> None:
    """All EAL codes appear in precedence list exactly once."""
    from hummbl_governance.eal import EAL_CODE_CLASS
    for code in EAL_CODE_CLASS:
        assert code in EAL_PRECEDENCE_INDEX, f"{code} missing from EAL_PRECEDENCE"


def test_evaluate_validation_malformed_contract() -> None:
    report = evaluate_validation("not a dict", {"receipt_id": "r1"})
    assert report["classification"] == "INDETERMINATE"
    assert report["primary_reason_code"] == "E_INPUT_MALFORMED"


def test_evaluate_validation_malformed_receipt() -> None:
    contract = {
        "contract_id": "c1",
        "contract_hash": "sha256:abc",
        "action_space": ["act1"],
    }
    report = evaluate_validation(contract, "not a dict")
    assert report["classification"] == "INDETERMINATE"
    assert report["primary_reason_code"] == "E_INPUT_MALFORMED"


def test_evaluate_compat_backward_compatible() -> None:
    a = {
        "contract_id": "c1",
        "contract_hash": "sha256:a",
        "action_space": ["act1"],
    }
    b = {
        "contract_id": "c2",
        "contract_hash": "sha256:b",
        "action_space": ["act1", "act2"],
    }
    report = evaluate_compat(a, b)
    assert report["classification"] == "BACKWARD_COMPATIBLE"


def test_evaluate_compat_incompatible_action_removed() -> None:
    a = {
        "contract_id": "c1",
        "contract_hash": "sha256:a",
        "action_space": ["act1", "act2"],
    }
    b = {
        "contract_id": "c2",
        "contract_hash": "sha256:b",
        "action_space": ["act1"],
    }
    report = evaluate_compat(a, b)
    assert report["classification"] == "INCOMPATIBLE"
    assert "COMPAT_ACTION_REMOVED" in report["reason_codes"]
