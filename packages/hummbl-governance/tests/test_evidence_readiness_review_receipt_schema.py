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
"""Validation tests for the governed Evidence Readiness Review Receipt schema.

The schema at ``hummbl_governance/data/evidence_readiness_review_receipt.schema.json``
was promoted from draft v0.1 to the governed decision surface v1
(hummbl-governance#67). These tests pin the schema contract and the governance
rules that the JSON Schema alone cannot express (notably the P0/P1 → BLOCKED
blocking rule).
"""

import json
from pathlib import Path

import pytest

from hummbl_governance.schema_validator import SchemaValidator


SCHEMA_PATH = (
    Path(__file__).resolve().parents[1]
    / "hummbl_governance"
    / "data"
    / "evidence_readiness_review_receipt.schema.json"
)


def _schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def _valid_receipt() -> dict:
    return {
        "schema_version": "evidence-readiness-review-receipt.v1",
        "receipt_id": "synthetic-review-001",
        "created_at": "2026-05-15T11:00:00Z",
        "matter_id": "synthetic-employment-separation",
        "data_classification": "PUBLIC_SYNTHETIC",
        "intended_audience": "client",
        "packet_paths": [
            "06_relay_safe/client-summary.md",
            "99_audit/review-receipt.md",
        ],
        "source_manifest_ref": {
            "path": "01_sources/manifest.md",
            "sha256": "a" * 64,
        },
        "reviewer": {
            "id": "codex",
            "role": "critical_peer",
        },
        "verdict": "APPROVE_WITH_P2",
        "findings": [
            {
                "severity": "P2",
                "item": "signing-bonus note",
                "status": "OPEN",
                "summary": "Counsel should evaluate favorable and adverse readings.",
            }
        ],
        "claim_honesty": {
            "unsupported_claims": 0,
            "interpretations_labeled": True,
            "legal_questions_reserved_for_counsel": True,
            "public_use_approved": False,
        },
        "relay_decision": {
            "allowed": True,
            "conditions": ["Do not share with opposing-side actors."],
        },
    }


def _validate(receipt: dict) -> tuple[bool, list[str]]:
    return SchemaValidator.validate_dict(receipt, _schema())


# --- Schema identity / promotion -------------------------------------------


def test_schema_is_promoted_to_governed_v1():
    schema = _schema()
    assert schema["$id"] == (
        "https://hummbl.dev/schemas/evidence-readiness-review-receipt.v1.json"
    )
    assert schema["title"] == "Evidence Readiness Review Receipt v1"
    assert (
        schema["properties"]["schema_version"]["const"]
        == "evidence-readiness-review-receipt.v1"
    )


# --- Acceptance / rejection of field values --------------------------------


def test_evidence_readiness_review_receipt_schema_accepts_valid_receipt():
    valid, errors = _validate(_valid_receipt())
    assert valid is True
    assert errors == []


@pytest.mark.parametrize(
    "field,bad_value",
    [
        ("schema_version", "evidence-readiness-review-receipt.v0.1"),
        ("verdict", "APPROVE"),
        ("verdict", "READY"),
        ("data_classification", "TOP_SECRET"),
        ("intended_audience", "counsel"),
        ("reviewer", {"id": "codex", "role": "judge"}),
    ],
)
def test_schema_rejects_invalid_enum_or_version(field, bad_value):
    receipt = _valid_receipt()
    receipt[field] = bad_value
    valid, errors = _validate(receipt)
    assert valid is False
    assert errors


def test_schema_rejects_missing_required_field():
    receipt = _valid_receipt()
    del receipt["relay_decision"]
    valid, errors = _validate(receipt)
    assert valid is False
    assert errors


def test_schema_rejects_additional_properties():
    receipt = _valid_receipt()
    receipt["confidential_evidence_blob"] = "should-not-be-here"
    valid, errors = _validate(receipt)
    assert valid is False
    assert errors


def test_schema_rejects_bad_sha256():
    receipt = _valid_receipt()
    receipt["source_manifest_ref"]["sha256"] = "not-a-hex-hash"
    valid, errors = _validate(receipt)
    assert valid is False
    assert errors


def test_schema_rejects_empty_packet_paths():
    receipt = _valid_receipt()
    receipt["packet_paths"] = []
    valid, errors = _validate(receipt)
    assert valid is False
    assert errors


def test_schema_rejects_negative_unsupported_claims():
    receipt = _valid_receipt()
    receipt["claim_honesty"]["unsupported_claims"] = -1
    valid, errors = _validate(receipt)
    assert valid is False
    assert errors


def test_schema_rejects_bad_finding_severity():
    receipt = _valid_receipt()
    receipt["findings"][0]["severity"] = "P5"
    valid, errors = _validate(receipt)
    assert valid is False
    assert errors


# --- Governance rules (P0/P1 → BLOCKED) ------------------------------------


def _has_blocking_finding(receipt: dict) -> bool:
    return any(
        f["severity"] == "P0"
        or (f["severity"] == "P1" and f["status"] == "OPEN")
        for f in receipt["findings"]
    )


def test_governance_rule_p0_open_finding_requires_blocked_relay():
    """A P0 finding must force relay_decision.allowed = false."""
    receipt = _valid_receipt()
    receipt["findings"] = [
        {
            "severity": "P0",
            "item": "fabricated source",
            "status": "OPEN",
            "summary": "Cited source does not exist in the manifest.",
        }
    ]
    receipt["verdict"] = "BLOCKED_P0"
    receipt["relay_decision"]["allowed"] = False

    # Schema-valid on its own.
    valid, errors = _validate(receipt)
    assert valid is True, errors

    # Governance rule: blocking finding present ⇒ relay must be blocked.
    assert _has_blocking_finding(receipt) is True
    assert receipt["relay_decision"]["allowed"] is False
    assert receipt["verdict"] in {"BLOCKED_P0", "BLOCKED_P1"}


def test_governance_rule_p1_open_finding_requires_blocked_relay():
    """An OPEN P1 finding must force relay_decision.allowed = false."""
    receipt = _valid_receipt()
    receipt["findings"] = [
        {
            "severity": "P1",
            "item": "scope breach",
            "status": "OPEN",
            "summary": "Packet includes matter outside engagement scope.",
        }
    ]
    receipt["verdict"] = "BLOCKED_P1"
    receipt["relay_decision"]["allowed"] = False

    valid, errors = _validate(receipt)
    assert valid is True, errors
    assert _has_blocking_finding(receipt) is True
    assert receipt["relay_decision"]["allowed"] is False


def test_governance_rule_fixed_p1_may_relay():
    """A FIXED P1 finding is not blocking and may coexist with an approval."""
    receipt = _valid_receipt()
    receipt["findings"] = [
        {
            "severity": "P1",
            "item": "scope breach",
            "status": "FIXED",
            "summary": "Out-of-scope section removed.",
        }
    ]
    receipt["verdict"] = "APPROVE_WITH_P2"
    receipt["relay_decision"]["allowed"] = True

    valid, errors = _validate(receipt)
    assert valid is True, errors
    assert _has_blocking_finding(receipt) is False


def test_governance_rule_detects_violating_receipt():
    """A receipt that relays despite a P0 finding violates the blocking rule.

    The JSON schema cannot express this cross-field rule, so the governance
    check lives in the test/validator layer. This test documents the invariant
    and would flag a violating receipt.
    """
    receipt = _valid_receipt()
    receipt["findings"] = [
        {
            "severity": "P0",
            "item": "data exposure",
            "status": "OPEN",
            "summary": "Confidential client name present in relay-safe summary.",
        }
    ]
    # Schema-valid but governance-invalid: relay allowed with a P0 finding.
    receipt["verdict"] = "BLOCKED_P0"
    receipt["relay_decision"]["allowed"] = True

    valid, errors = _validate(receipt)
    assert valid is True, errors  # schema alone does not catch this

    # Governance layer catches it.
    violates = _has_blocking_finding(receipt) and receipt["relay_decision"]["allowed"]
    assert violates is True
    # The corrective action: flip allowed to false.
    receipt["relay_decision"]["allowed"] = False
    assert (
        _has_blocking_finding(receipt)
        and receipt["relay_decision"]["allowed"] is False
    )


# --- Canonical example fixture round-trip ----------------------------------


def test_canonical_example_fixture_validates_against_schema():
    fixture_path = (
        Path(__file__).resolve().parent
        / "conformance"
        / "fixtures_evidence_readiness"
        / "ERR1_RECEIPT_OK.json"
    )
    receipt = json.loads(fixture_path.read_text(encoding="utf-8"))
    valid, errors = _validate(receipt)
    assert valid is True, errors
