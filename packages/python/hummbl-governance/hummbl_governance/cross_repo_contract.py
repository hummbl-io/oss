# Copyright 2024-2026 HUMMBL, LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# SPDX-License-Identifier: Apache-2.0

"""Cross-repository contract validation.

This module validates the candidate v0.1 additive contract envelope and its
producer/consumer compatibility manifest. Validation establishes structural and
declared compatibility properties only. It does not establish factual truth,
scientific validity, security, canon status, or deployment authority.

Stdlib-only.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from importlib.resources import (
    files,  # nosemgrep: python.lang.compatibility.python37.python37-compatibility-importlib2
)
from pathlib import Path
from typing import Any

from hummbl_governance.schema_validator import SchemaValidator

_CONTRACT_SCHEMA = "cross_repo_contract_v0.1.schema.json"
_COMPATIBILITY_SCHEMA = "cross_repo_compatibility_manifest_v0.1.schema.json"
_PRIVATE_MARKERS = ("private://", "github-private://", "secret://", "/private/")


def _load_packaged_schema(name: str) -> dict[str, Any]:
    resource = files("hummbl_governance").joinpath("data", name)
    return json.loads(resource.read_text(encoding="utf-8"))


def _load_json(path: str | Path) -> dict[str, Any]:
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: top-level JSON value must be an object")
    return value


def _is_private_ref(value: str) -> bool:
    lowered = value.lower()
    return any(marker in lowered for marker in _PRIVATE_MARKERS)


def _parse_timestamp(value: str | None, path: str, errors: list[str]) -> datetime | None:
    if value is None:
        return None
    try:
        normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
        parsed = datetime.fromisoformat(normalized)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    except ValueError:
        errors.append(f"{path}: expected ISO-8601 date or date-time, got {value!r}")
        return None


def _contract_version_supported(version: str, supported: list[str]) -> bool:
    major, minor, _patch = version.split(".")
    return version in supported or f"{major}.{minor}.x" in supported


def _payload_version_supported(version: str, supported: list[str]) -> bool:
    for declaration in supported:
        if declaration == version:
            return True
        if declaration != "*" and declaration.endswith("*") and version.startswith(declaration[:-1]):
            return True
    return False


def _iter_contract_refs(contract: dict[str, Any]) -> list[tuple[str, str]]:
    refs: list[tuple[str, str]] = [
        ("producer.authority_ref", contract["producer"]["authority_ref"]),
        ("producer.artifact_locator", contract["producer"]["artifact_locator"]),
        ("interface.payload_schema_uri", contract["interface"]["payload_schema_uri"]),
    ]
    for key in ("valid_fixtures", "invalid_fixtures", "adversarial_fixtures"):
        refs.extend((f"validation.{key}[{index}]", value) for index, value in enumerate(contract["validation"][key]))
    for key in ("on_publish", "on_accept", "on_reject", "receipt_schema_refs"):
        refs.extend((f"receipts.{key}[{index}]", value) for index, value in enumerate(contract["receipts"][key]))
    refs.extend(
        (f"assurance.refs[{index}].ref", item["ref"]) for index, item in enumerate(contract["assurance"]["refs"])
    )
    refs.extend(
        (f"compatibility.migration_refs[{index}]", value)
        for index, value in enumerate(contract["compatibility"]["migration_refs"])
    )
    refs.extend(
        (f"lifecycle.supersedes[{index}]", value) for index, value in enumerate(contract["lifecycle"]["supersedes"])
    )
    replacement = contract["lifecycle"]["replacement_contract_ref"]
    if replacement is not None:
        refs.append(("lifecycle.replacement_contract_ref", replacement))
    return refs


def validate_contract_document(contract: dict[str, Any]) -> list[str]:
    """Validate one candidate cross-repository contract document."""

    schema = _load_packaged_schema(_CONTRACT_SCHEMA)
    errors = [f"schema: {error}" for error in SchemaValidator.validate(contract, schema)]
    if errors:
        return errors

    producer_repo = contract["producer"]["repo"]
    consumers = contract["consumers"]
    consumer_repos = [item["repo"] for item in consumers]

    if producer_repo in consumer_repos:
        errors.append("semantic: producer.repo must not also be a consumer repo")
    if len(consumer_repos) != len(set(consumer_repos)):
        errors.append("semantic: consumer repo declarations must be unique")
    if not _contract_version_supported(
        contract["contract_version"],
        contract["compatibility"]["supported_contract_versions"],
    ):
        errors.append("semantic: contract_version is not included in supported_contract_versions")
    if "*" in contract["compatibility"]["supported_payload_versions"]:
        errors.append(
            "semantic: bare payload wildcard '*' is not allowed; use an exact value "
            "or a non-empty trailing-prefix wildcard"
        )

    try:
        re.compile(contract["interface"]["locator_pattern"])
    except re.error as exc:
        errors.append(f"semantic: interface.locator_pattern is invalid: {exc}")

    lifecycle = contract["lifecycle"]
    effective_at = _parse_timestamp(lifecycle["effective_at"], "lifecycle.effective_at", errors)
    review_by = _parse_timestamp(lifecycle["review_by"], "lifecycle.review_by", errors)
    _parse_timestamp(lifecycle["deprecated_at"], "lifecycle.deprecated_at", errors)

    status = contract["contract_status"]
    if status == "active" and lifecycle["effective_at"] is None:
        errors.append("semantic: active contracts require lifecycle.effective_at")
    if status in {"deprecated", "retired"} and lifecycle["deprecated_at"] is None:
        errors.append("semantic: deprecated or retired contracts require lifecycle.deprecated_at")
    if status == "deprecated" and lifecycle["replacement_contract_ref"] is None:
        errors.append("semantic: deprecated contracts require lifecycle.replacement_contract_ref")
    if effective_at is not None and review_by is not None and review_by < effective_at:
        errors.append("semantic: lifecycle.review_by must not precede effective_at")

    postures = contract["postures"]
    if postures["visibility"] == "public":
        if postures["privacy"] not in {"public_safe", "metadata_only"}:
            errors.append("semantic: public visibility requires public_safe or metadata_only privacy")
        for path, value in _iter_contract_refs(contract):
            if _is_private_ref(value):
                errors.append(f"semantic: public contract leaks private reference at {path}")

    assurance_refs = contract["assurance"]["refs"]
    ref_kinds: dict[str, set[str]] = {}
    for item in assurance_refs:
        ref_kinds.setdefault(item["ref"], set()).add(item["kind"])
    for ref, kinds in ref_kinds.items():
        if len(kinds) > 1:
            errors.append(f"semantic: assurance reference {ref!r} is presented as multiple kinds: {sorted(kinds)}")

    assurance_kinds = {item["kind"] for item in assurance_refs}
    if postures["claim_posture"] in {"evidence_linked", "externally_corroborated"}:
        if "evidence" not in assurance_kinds:
            errors.append(
                "semantic: evidence_linked or externally_corroborated claim posture requires an evidence reference"
            )
    if postures["claim_posture"] == "externally_corroborated":
        if not assurance_kinds.intersection({"verification", "attestation"}):
            errors.append(
                "semantic: externally_corroborated claim posture requires a verification or attestation reference"
            )

    if not contract["validation"]["offline_core_required"]:
        errors.append("semantic: candidate v0.1 requires validation.offline_core_required=true")

    return errors


def validate_compatibility_manifest(
    manifest: dict[str, Any],
    contract: dict[str, Any] | None = None,
) -> list[str]:
    """Validate a compatibility manifest, optionally against its contract."""

    schema = _load_packaged_schema(_COMPATIBILITY_SCHEMA)
    errors = [f"schema: {error}" for error in SchemaValidator.validate(manifest, schema)]
    if errors:
        return errors

    decisions = manifest["consumer_decisions"]
    decision_repos = [item["repo"] for item in decisions]
    if len(decision_repos) != len(set(decision_repos)):
        errors.append("semantic: consumer decision repos must be unique")

    receipt_refs = [manifest["producer"]["publish_receipt_ref"]]
    receipt_refs.extend(item["receipt_ref"] for item in decisions)
    if len(receipt_refs) != len(set(receipt_refs)):
        errors.append("semantic: producer and consumer receipt refs must be unique")

    contract_version = manifest["contract"]["contract_version"]
    payload_version = manifest["contract"]["payload_version"]
    for index, decision in enumerate(decisions):
        path = f"consumer_decisions[{index}]"
        if decision["decision"] in {"accepted", "conditional"}:
            if not _contract_version_supported(contract_version, decision["supported_contract_versions"]):
                errors.append(f"semantic: {path} does not support the declared contract_version")
            if "*" in decision["supported_payload_versions"]:
                errors.append(
                    f"semantic: {path} contains bare payload wildcard '*'; use an exact "
                    "value or a non-empty trailing-prefix wildcard"
                )
            elif not _payload_version_supported(payload_version, decision["supported_payload_versions"]):
                errors.append(f"semantic: {path} does not support the declared payload_version")
        if decision["decision"] == "conditional" and not decision["conditions"]:
            errors.append(f"semantic: {path} conditional decision requires conditions")
        if decision["decision"] == "rejected" and not decision["reason"]:
            errors.append(f"semantic: {path} rejected decision requires a reason")

    if contract is None:
        return errors

    contract_errors = validate_contract_document(contract)
    errors.extend(f"contract: {error}" for error in contract_errors)
    if contract_errors:
        return errors

    if manifest["manifest_status"] == "effective" and contract["contract_status"] != "active":
        errors.append("semantic: effective manifest requires an active contract")

    declared = manifest["contract"]
    if declared["contract_id"] != contract["contract_id"]:
        errors.append("semantic: manifest contract_id does not match contract")
    if declared["contract_version"] != contract["contract_version"]:
        errors.append("semantic: manifest contract_version does not match contract")
    if declared["payload_schema_uri"] != contract["interface"]["payload_schema_uri"]:
        errors.append("semantic: manifest payload_schema_uri does not match contract")
    if manifest["producer"]["repo"] != contract["producer"]["repo"]:
        errors.append("semantic: manifest producer.repo does not match contract producer")

    contract_consumers = {item["repo"]: item["requirement"] for item in contract["consumers"]}
    for index, decision in enumerate(decisions):
        repo = decision["repo"]
        if repo not in contract_consumers:
            errors.append(f"semantic: consumer_decisions[{index}].repo is not declared by contract")

    if manifest["manifest_scope"] == "full":
        missing = sorted(set(contract_consumers) - set(decision_repos))
        if missing:
            errors.append(f"semantic: full manifest is missing consumer decisions for {missing}")

    if contract["postures"]["visibility"] == "public":
        refs = [("producer.publish_receipt_ref", manifest["producer"]["publish_receipt_ref"])]
        refs.extend(
            (f"consumer_decisions[{index}].receipt_ref", item["receipt_ref"]) for index, item in enumerate(decisions)
        )
        for path, value in refs:
            if _is_private_ref(value):
                errors.append(f"semantic: public manifest leaks private reference at {path}")

    return errors


def validate_files(
    contract_path: str | Path,
    manifest_path: str | Path | None = None,
) -> list[str]:
    """Validate files from disk and return all validation errors."""

    contract = _load_json(contract_path)
    if manifest_path is None:
        return validate_contract_document(contract)
    manifest = _load_json(manifest_path)
    return validate_compatibility_manifest(manifest, contract)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Validate HUMMBL candidate cross-repo contracts and compatibility manifests. "
            "A pass establishes declared structural compatibility only."
        )
    )
    parser.add_argument("contract", help="Path to a cross-repo contract JSON document")
    parser.add_argument(
        "--manifest",
        help="Optional compatibility manifest JSON document to validate against the contract",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        errors = validate_files(args.contract, args.manifest)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    if errors:
        print("INVALID")
        for error in errors:
            print(f"- {error}")
        return 1

    print("VALID")
    print(
        "Validation establishes structure and declared compatibility only; "
        "it does not establish truth, security, canon status, or deployment authority."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
