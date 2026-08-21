# Copyright 2024-2026 HUMMBL, LLC
# Licensed under the Apache License, Version 2.0
# SPDX-License-Identifier: Apache-2.0

"""Tests for candidate cross-repository contracts."""

from __future__ import annotations

import json
from pathlib import Path

from hummbl_governance.cross_repo_contract import (
    validate_compatibility_manifest,
    validate_contract_document,
    validate_files,
)

FIXTURES = Path(__file__).parent / "fixtures" / "cross_repo_contract"


def _load(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def test_valid_wave1_contract_and_manifest() -> None:
    errors = validate_files(
        FIXTURES / "valid-wave1-contract.json",
        FIXTURES / "valid-wave1-manifest.json",
    )
    assert errors == []


def test_public_private_reference_leak_is_rejected() -> None:
    errors = validate_contract_document(_load("adversarial-public-private-leak.json"))
    assert any("leaks private reference" in error for error in errors)


def test_execution_receipt_cannot_satisfy_external_corroboration() -> None:
    errors = validate_contract_document(_load("adversarial-receipt-as-verification.json"))
    assert any("requires a verification or attestation" in error for error in errors)


def test_claim_posture_requires_evidence_reference() -> None:
    errors = validate_contract_document(_load("adversarial-claim-without-evidence.json"))
    assert any("requires an evidence reference" in error for error in errors)


def test_promotion_receipt_cannot_establish_external_corroboration() -> None:
    errors = validate_contract_document(_load("adversarial-promotion-as-truth.json"))
    assert any("requires a verification or attestation" in error for error in errors)


def test_unsupported_payload_version_is_rejected() -> None:
    contract = _load("valid-wave1-contract.json")
    manifest = _load("invalid-unsupported-payload-manifest.json")
    errors = validate_compatibility_manifest(manifest, contract)
    assert any("does not support the declared payload_version" in error for error in errors)


def test_full_manifest_requires_every_declared_consumer() -> None:
    contract = _load("valid-wave1-contract.json")
    manifest = _load("valid-wave1-manifest.json")
    manifest["consumer_decisions"] = manifest["consumer_decisions"][:1]
    errors = validate_compatibility_manifest(manifest, contract)
    assert any("full manifest is missing consumer decisions" in error for error in errors)


def test_duplicate_assurance_ref_kinds_are_rejected() -> None:
    contract = _load("valid-wave1-contract.json")
    shared_ref = "receipt:execution:shared"
    contract["assurance"]["refs"] = [
        {"kind": "execution_receipt", "ref": shared_ref},
        {"kind": "verification", "ref": shared_ref},
    ]
    errors = validate_contract_document(contract)
    assert any("presented as multiple kinds" in error for error in errors)


def test_active_contract_requires_effective_at() -> None:
    contract = _load("valid-wave1-contract.json")
    contract["contract_status"] = "active"
    errors = validate_contract_document(contract)
    assert any("active contracts require lifecycle.effective_at" in error for error in errors)


def test_conditional_acceptance_requires_conditions() -> None:
    contract = _load("valid-wave1-contract.json")
    manifest = _load("valid-wave1-manifest.json")
    manifest["consumer_decisions"][1]["conditions"] = []
    errors = validate_compatibility_manifest(manifest, contract)
    assert any("conditional decision requires conditions" in error for error in errors)


def test_producer_cannot_also_be_consumer() -> None:
    contract = _load("valid-wave1-contract.json")
    contract["consumers"].append(
        {"repo": contract["producer"]["repo"], "requirement": "advisory"}
    )
    errors = validate_contract_document(contract)
    assert any("producer.repo must not also be a consumer" in error for error in errors)


def test_schema_rejects_unknown_top_level_property() -> None:
    contract = _load("valid-wave1-contract.json")
    contract["automatic_authority"] = True
    errors = validate_contract_document(contract)
    assert any("unexpected property" in error for error in errors)


def test_bare_payload_wildcard_is_rejected() -> None:
    contract = _load("valid-wave1-contract.json")
    contract["compatibility"]["supported_payload_versions"] = ["*"]
    errors = validate_contract_document(contract)
    assert any("bare payload wildcard" in error for error in errors)


def test_manifest_bare_payload_wildcard_is_explicitly_rejected() -> None:
    contract = _load("valid-wave1-contract.json")
    manifest = _load("valid-wave1-manifest.json")
    manifest["consumer_decisions"][0]["supported_payload_versions"] = ["*"]
    errors = validate_compatibility_manifest(manifest, contract)
    assert any("contains bare payload wildcard" in error for error in errors)


def test_public_contract_checks_private_lifecycle_references() -> None:
    contract = _load("valid-wave1-contract.json")
    contract["lifecycle"]["supersedes"] = ["private://contracts/old"]
    contract["lifecycle"]["replacement_contract_ref"] = "secret://contracts/new"
    errors = validate_contract_document(contract)
    assert any("lifecycle.supersedes[0]" in error for error in errors)
    assert any("lifecycle.replacement_contract_ref" in error for error in errors)


def test_malformed_contract_is_reported_before_effective_manifest_check() -> None:
    manifest = _load("valid-wave1-manifest.json")
    manifest["manifest_status"] = "effective"
    errors = validate_compatibility_manifest(manifest, {})
    assert any(error.startswith("contract: schema:") for error in errors)
