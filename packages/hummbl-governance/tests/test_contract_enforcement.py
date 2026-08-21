# Copyright 2024-2026 HUMMBL, LLC
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

"""Tests for the cross-repo contract enforcement layer.

These tests exercise the ``$ref``-capable enforcement path in
:mod:`hummbl_governance.contract_enforcement`, including validation against a
contract schema that resolves shared definitions through a :class:`RefRegistry`.
"""

from __future__ import annotations

import json
from pathlib import Path

from hummbl_governance.contract_enforcement import (
    EnforcementResult,
    build_contract_registry,
    enforce_compatibility_manifest,
    enforce_contract,
    enforce_files,
)
from hummbl_governance.schema_validator import RefRegistry, SchemaValidator

FIXTURES = Path(__file__).parent / "fixtures" / "cross_repo_contract"
REF_CONTRACT_SCHEMA = "cross_repo_contract_v0.1.ref.schema.json"


def _load_packaged_schema(name: str) -> dict:
    from importlib.resources import files

    resource = files("hummbl_governance").joinpath("data", name)
    return json.loads(resource.read_text(encoding="utf-8"))


def _load(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


class TestBuildContractRegistry:
    """The registry builder must register the shared-refs schema by $id."""

    def test_registry_contains_shared_refs(self):
        registry = build_contract_registry()
        assert "https://hummbl.dev/schemas/cross-repo-shared-refs-v0.1.schema.json" in registry

    def test_registry_resolves_repo_ref(self):
        registry = build_contract_registry()
        instance = {"x": "hummbl-dev/research-source-packets"}
        # Validate a string against the repo_ref definition via the ref schema.
        ref_schema = {"$ref": "https://hummbl.dev/schemas/cross-repo-shared-refs-v0.1.schema.json#/$defs/repo_ref"}
        errors = SchemaValidator.validate(instance["x"], ref_schema, registry=registry)
        assert errors == []


class TestEnforceContract:
    """Enforcement combines $ref schema validation with semantic rules."""

    def test_valid_fixture_passes_enforcement(self):
        contract = _load("valid-wave1-contract.json")
        result = enforce_contract(contract)
        assert result.is_valid is True
        assert result.errors == []

    def test_enforcement_catches_schema_violation(self):
        contract = _load("valid-wave1-contract.json")
        contract["contract_version"] = "not-semver"
        result = enforce_contract(contract)
        assert result.is_valid is False
        assert any("schema:" in e for e in result.schema_errors)

    def test_enforcement_catches_semantic_violation(self):
        contract = _load("valid-wave1-contract.json")
        contract["consumers"].append(
            {"repo": contract["producer"]["repo"], "requirement": "advisory"}
        )
        result = enforce_contract(contract)
        assert result.is_valid is False
        assert any("producer.repo must not also be a consumer" in e for e in result.semantic_errors)

    def test_enforcement_catches_adversarial_public_private_leak(self):
        contract = _load("adversarial-public-private-leak.json")
        result = enforce_contract(contract)
        assert result.is_valid is False
        assert any("leaks private reference" in e for e in result.semantic_errors)

    def test_enforcement_catches_adversarial_claim_without_evidence(self):
        contract = _load("adversarial-claim-without-evidence.json")
        result = enforce_contract(contract)
        assert result.is_valid is False
        assert any("requires an evidence reference" in e for e in result.semantic_errors)

    def test_enforcement_result_partitions_errors(self):
        contract = _load("valid-wave1-contract.json")
        contract["contract_version"] = "bad"
        result = enforce_contract(contract)
        assert isinstance(result, EnforcementResult)
        assert result.schema_errors
        assert result.semantic_errors == []
        # errors property combines both partitions.
        assert result.errors == result.schema_errors


class TestEnforceWithRefSchema:
    """The $ref-based contract schema must validate fixtures via the registry."""

    def test_ref_schema_validates_valid_fixture(self):
        registry = build_contract_registry()
        schema = _load_packaged_schema(REF_CONTRACT_SCHEMA)
        instance = _load("valid-wave1-contract.json")
        errors = SchemaValidator.validate(instance, schema, registry=registry)
        assert errors == []

    def test_ref_schema_catches_bad_repo_ref(self):
        registry = build_contract_registry()
        schema = _load_packaged_schema(REF_CONTRACT_SCHEMA)
        instance = _load("valid-wave1-contract.json")
        instance["producer"]["repo"] = "not-a-valid-repo"
        errors = SchemaValidator.validate(instance, schema, registry=registry)
        assert any("does not match pattern" in e for e in errors)

    def test_ref_schema_catches_bad_contract_version(self):
        registry = build_contract_registry()
        schema = _load_packaged_schema(REF_CONTRACT_SCHEMA)
        instance = _load("valid-wave1-contract.json")
        instance["contract_version"] = "1.0"
        errors = SchemaValidator.validate(instance, schema, registry=registry)
        assert any("does not match pattern" in e for e in errors)

    def test_ref_schema_catches_bad_consumer_requirement(self):
        registry = build_contract_registry()
        schema = _load_packaged_schema(REF_CONTRACT_SCHEMA)
        instance = _load("valid-wave1-contract.json")
        instance["consumers"][0]["requirement"] = "mandatory"
        errors = SchemaValidator.validate(instance, schema, registry=registry)
        assert any("not in enum" in e for e in errors)

    def test_ref_schema_catches_bad_assurance_kind(self):
        registry = build_contract_registry()
        schema = _load_packaged_schema(REF_CONTRACT_SCHEMA)
        instance = _load("valid-wave1-contract.json")
        instance["assurance"]["refs"][0]["kind"] = "truth"
        errors = SchemaValidator.validate(instance, schema, registry=registry)
        assert any("not in enum" in e for e in errors)

    def test_ref_schema_requires_registry(self):
        schema = _load_packaged_schema(REF_CONTRACT_SCHEMA)
        instance = _load("valid-wave1-contract.json")
        errors = SchemaValidator.validate(instance, schema)
        assert any("no registry" in e or "registry" in e for e in errors)

    def test_ref_schema_catches_unregistered_doc(self):
        registry = RefRegistry()  # empty registry
        schema = _load_packaged_schema(REF_CONTRACT_SCHEMA)
        instance = _load("valid-wave1-contract.json")
        errors = SchemaValidator.validate(instance, schema, registry=registry)
        assert any("unregistered" in e for e in errors)


class TestEnforceCompatibilityManifest:
    """Enforcement of compatibility manifests with optional contract."""

    def test_valid_manifest_with_contract_passes(self):
        contract = _load("valid-wave1-contract.json")
        manifest = _load("valid-wave1-manifest.json")
        result = enforce_compatibility_manifest(manifest, contract)
        assert result.is_valid is True
        assert result.errors == []

    def test_invalid_payload_version_is_caught(self):
        contract = _load("valid-wave1-contract.json")
        manifest = _load("invalid-unsupported-payload-manifest.json")
        result = enforce_compatibility_manifest(manifest, contract)
        assert result.is_valid is False
        assert any("payload_version" in e for e in result.semantic_errors)

    def test_manifest_schema_violation_is_caught(self):
        manifest = _load("valid-wave1-manifest.json")
        manifest["schema_version"] = "9.9.9"
        result = enforce_compatibility_manifest(manifest)
        assert result.is_valid is False
        assert result.schema_errors

    def test_manifest_without_contract_skips_cross_validation(self):
        manifest = _load("valid-wave1-manifest.json")
        result = enforce_compatibility_manifest(manifest)
        # Schema-only validation passes for a well-formed manifest.
        assert result.is_valid is True


class TestEnforceFiles:
    """File-based enforcement entry point."""

    def test_valid_contract_and_manifest_files(self):
        result = enforce_files(
            FIXTURES / "valid-wave1-contract.json",
            FIXTURES / "valid-wave1-manifest.json",
        )
        assert result.is_valid is True

    def test_contract_only_file(self):
        result = enforce_files(FIXTURES / "valid-wave1-contract.json")
        assert result.is_valid is True

    def test_adversarial_contract_file_is_rejected(self):
        result = enforce_files(FIXTURES / "adversarial-public-private-leak.json")
        assert result.is_valid is False
        assert any("leaks private reference" in e for e in result.semantic_errors)
