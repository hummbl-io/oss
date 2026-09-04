# Copyright 2024-2026 HUMMBL, LLC
# Licensed under the Apache License, Version 2.0
# SPDX-License-Identifier: Apache-2.0

"""Tests for the pure, bounded GitOps deployment comparison probe."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest

from hummbl_governance.gitops_deployment_probe import (
    PROBE_ERROR_CODES,
    evaluate_repository_deployment_probe,
)
from hummbl_governance.gitops_evidence import loads_strict_json


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "gitops_evidence" / "synthetic-deployment-probe.json"


def _fixture() -> dict:
    loaded = loads_strict_json(FIXTURE_PATH.read_bytes())
    assert isinstance(loaded, dict)
    return loaded


def _evaluate(case: dict) -> tuple[dict | None, list[str]]:
    return evaluate_repository_deployment_probe(case["expectation"], case["observed"])


def test_synthetic_private_canary_emits_exact_sanitized_receipt() -> None:
    case = _fixture()
    before = deepcopy(case)

    receipt, errors = _evaluate(case)

    assert errors == []
    assert receipt == {
        "comparison_profile": "gitops-bounded-required-refs-v0",
        "contract_version": "0.1.0",
        "expectation_id": "expectation:synthetic-canary",
        "matched_refs": [
            {
                "oid": "1111111111111111111111111111111111111111",
                "ref": "refs/heads/main",
            },
            {
                "oid": "2222222222222222222222222222222222222222",
                "ref": "refs/tags/canary-v1",
            },
        ],
        "mirror_alias": "repo:synthetic-postflight",
        "object_format": "sha1",
        "record_type": "repository_deployment_probe_receipt",
        "result": "bounded_required_refs_match",
        "source_alias": "repo:synthetic-canonical",
    }
    assert case == before
    serialized = json.dumps(receipt, sort_keys=True)
    assert "repository_identity" not in serialized
    assert "example.invalid" not in serialized
    assert "extra-source" not in serialized
    assert "extra-mirror" not in serialized


def test_valid_extra_refs_are_ignored_not_claimed() -> None:
    receipt, errors = _evaluate(_fixture())

    assert errors == []
    assert receipt is not None
    assert [item["ref"] for item in receipt["matched_refs"]] == [
        "refs/heads/main",
        "refs/tags/canary-v1",
    ]


def test_source_and_mirror_agreement_cannot_override_wrong_expected_oid() -> None:
    case = _fixture()
    wrong_oid = "9" * 40
    case["observed"]["source"]["refs"]["refs/heads/main"] = wrong_oid
    case["observed"]["mirror"]["refs"]["refs/heads/main"] = wrong_oid

    receipt, errors = _evaluate(case)

    assert receipt is None
    assert errors == [
        "MIRROR_REQUIRED_REF_MISMATCH",
        "SOURCE_REQUIRED_REF_MISMATCH",
    ]


@pytest.mark.parametrize("side", ["source", "mirror"])
def test_missing_required_ref_fails_closed(side: str) -> None:
    case = _fixture()
    del case["observed"][side]["refs"]["refs/tags/canary-v1"]

    receipt, errors = _evaluate(case)

    assert receipt is None
    assert errors == [f"{side.upper()}_REQUIRED_REF_MISSING"]


@pytest.mark.parametrize(
    ("mutation", "expected_code"),
    [
        (("source", "private", "true"), "SOURCE_NOT_PRIVATE"),
        (("mirror", "private", 1), "MIRROR_NOT_PRIVATE"),
        (("source", "observation_complete", False), "SOURCE_OBSERVATION_INCOMPLETE"),
        (("mirror", "observation_complete", None), "MIRROR_OBSERVATION_INCOMPLETE"),
        (("mirror", "push_mirror", True), "PUSH_MIRROR_FORBIDDEN"),
        (("source", "role", "pull_mirror"), "SOURCE_ROLE_INVALID"),
        (("mirror", "role", "source"), "MIRROR_ROLE_INVALID"),
    ],
)
def test_role_privacy_completeness_and_direction_are_exact(
    mutation: tuple[str, str, object], expected_code: str
) -> None:
    case = _fixture()
    side, field, value = mutation
    case["observed"][side][field] = value

    receipt, errors = _evaluate(case)

    assert receipt is None
    assert expected_code in errors


@pytest.mark.parametrize(
    ("path", "value", "expected_code"),
    [
        (("expectation", "mirror_alias"), "repo:synthetic-canonical", "ALIASES_NOT_DISTINCT"),
        (
            ("expectation", "mirror_repository_identity"),
            "https://source.example.invalid/acme/canary.git",
            "REPOSITORY_IDENTITIES_NOT_DISTINCT",
        ),
        (
            ("observed", "mirror", "upstream_repository_identity"),
            "https://other.example.invalid/acme/canary.git",
            "UPSTREAM_REPOSITORY_IDENTITY_MISMATCH",
        ),
    ],
)
def test_source_and_mirror_identity_boundaries(path: tuple[str, ...], value: object, expected_code: str) -> None:
    case = _fixture()
    target = case
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value

    receipt, errors = _evaluate(case)

    assert receipt is None
    assert expected_code in errors


def test_explicit_default_https_port_cannot_make_one_repository_look_distinct() -> None:
    case = _fixture()
    equivalent_identity = "https://source.example.invalid:443/acme/canary.git"
    case["expectation"]["mirror_repository_identity"] = equivalent_identity
    case["observed"]["mirror"]["repository_identity"] = equivalent_identity

    receipt, errors = _evaluate(case)

    assert receipt is None
    assert "MIRROR_REPOSITORY_IDENTITY_INVALID" in errors


@pytest.mark.parametrize("empty_delimiter", ["?", "#"])
def test_empty_url_delimiter_cannot_make_one_repository_look_distinct(
    empty_delimiter: str,
) -> None:
    case = _fixture()
    equivalent_identity = "https://source.example.invalid/acme/canary.git" + empty_delimiter
    case["expectation"]["mirror_repository_identity"] = equivalent_identity
    case["observed"]["mirror"]["repository_identity"] = equivalent_identity

    receipt, errors = _evaluate(case)

    assert receipt is None
    assert "MIRROR_REPOSITORY_IDENTITY_INVALID" in errors


@pytest.mark.parametrize("scheme", ["HTTPS://", "HtTpS://"])
def test_scheme_case_cannot_make_one_repository_look_distinct(scheme: str) -> None:
    case = _fixture()
    equivalent_identity = scheme + "source.example.invalid/acme/canary.git"
    case["expectation"]["mirror_repository_identity"] = equivalent_identity
    case["observed"]["mirror"]["repository_identity"] = equivalent_identity

    receipt, errors = _evaluate(case)

    assert receipt is None
    assert "MIRROR_REPOSITORY_IDENTITY_INVALID" in errors


@pytest.mark.parametrize(
    "mirror_host",
    ["127.1", "2130706433", "0177.0.0.1", "0x7f.1", "0x7f000001", "127.0.0.01"],
)
def test_numeric_host_aliases_cannot_make_one_endpoint_look_distinct(
    mirror_host: str,
) -> None:
    case = _fixture()
    source_identity = "https://127.0.0.1/acme/canary.git"
    mirror_identity = f"https://{mirror_host}/acme/canary.git"
    case["expectation"]["source_repository_identity"] = source_identity
    case["expectation"]["mirror_repository_identity"] = mirror_identity
    case["observed"]["source"]["repository_identity"] = source_identity
    case["observed"]["mirror"]["repository_identity"] = mirror_identity
    case["observed"]["mirror"]["upstream_repository_identity"] = source_identity

    receipt, errors = _evaluate(case)

    assert receipt is None
    assert "SOURCE_REPOSITORY_IDENTITY_INVALID" in errors
    assert "MIRROR_REPOSITORY_IDENTITY_INVALID" in errors


def test_object_format_and_full_oid_are_required() -> None:
    case = _fixture()
    case["observed"]["source"]["object_format"] = "sha256"
    case["observed"]["mirror"]["refs"]["refs/heads/main"] = "1" * 12

    receipt, errors = _evaluate(case)

    assert receipt is None
    assert "SOURCE_OBJECT_FORMAT_MISMATCH" in errors
    assert "MIRROR_REFS_INVALID" in errors


def test_sha256_required_refs_can_emit_a_bounded_success_receipt() -> None:
    case = _fixture()
    case["expectation"]["object_format"] = "sha256"
    case["observed"]["source"]["object_format"] = "sha256"
    case["observed"]["mirror"]["object_format"] = "sha256"
    for ref_map in (
        case["expectation"]["required_refs"],
        case["observed"]["source"]["refs"],
        case["observed"]["mirror"]["refs"],
    ):
        for ref, oid in ref_map.items():
            ref_map[ref] = oid[0] * 64

    receipt, errors = _evaluate(case)

    assert errors == []
    assert receipt is not None
    assert receipt["object_format"] == "sha256"
    assert all(len(item["oid"]) == 64 for item in receipt["matched_refs"])


@pytest.mark.parametrize(
    ("location", "value", "expected_code"),
    [
        ("expectation", [], "OBJECT_FORMAT_INVALID"),
        ("source", {}, "SOURCE_OBJECT_FORMAT_INVALID"),
        ("mirror", [], "MIRROR_OBJECT_FORMAT_INVALID"),
    ],
)
def test_unhashable_object_formats_fail_through_fixed_codes(location: str, value: object, expected_code: str) -> None:
    case = _fixture()
    if location == "expectation":
        case["expectation"]["object_format"] = value
    else:
        case["observed"][location]["object_format"] = value

    receipt, errors = _evaluate(case)

    assert receipt is None
    assert expected_code in errors
    assert errors == sorted(set(errors))
    assert all(error in PROBE_ERROR_CODES for error in errors)


def test_null_object_ids_cannot_satisfy_a_required_ref() -> None:
    case = _fixture()
    null_oid = "0" * 40
    case["expectation"]["required_refs"]["refs/heads/main"] = null_oid
    case["observed"]["source"]["refs"]["refs/heads/main"] = null_oid
    case["observed"]["mirror"]["refs"]["refs/heads/main"] = null_oid

    receipt, errors = _evaluate(case)

    assert receipt is None
    assert "REQUIRED_REFS_INVALID" in errors
    assert "SOURCE_REFS_INVALID" in errors
    assert "MIRROR_REFS_INVALID" in errors


def test_malformed_extra_ref_rejects_the_whole_observation() -> None:
    case = _fixture()
    case["observed"]["source"]["refs"]["refs/heads/bad..ref"] = "5" * 40

    receipt, errors = _evaluate(case)

    assert receipt is None
    assert errors == ["SOURCE_REFS_INVALID"]


@pytest.mark.parametrize(
    "malformed_ref",
    ["refs/heads/component.lock/child", "refs/heads/component./child"],
)
def test_invalid_ref_path_component_rejects_the_whole_observation(
    malformed_ref: str,
) -> None:
    case = _fixture()
    case["observed"]["source"]["refs"][malformed_ref] = "5" * 40

    receipt, errors = _evaluate(case)

    assert receipt is None
    assert errors == ["SOURCE_REFS_INVALID"]


@pytest.mark.parametrize("location", ["expectation", "observed", "source", "mirror"])
def test_unknown_or_freshness_fields_are_rejected(location: str) -> None:
    case = _fixture()
    if location == "expectation":
        case["expectation"]["updated_at"] = "2099-01-01T00:00:00Z"
        expected_code = "EXPECTED_FIELDS_INVALID"
    elif location == "observed":
        case["observed"]["fresh"] = True
        expected_code = "OBSERVED_FIELDS_INVALID"
    else:
        case["observed"][location]["mirror_updated"] = "2099-01-01T00:00:00Z"
        expected_code = f"{location.upper()}_FIELDS_INVALID"

    receipt, errors = _evaluate(case)

    assert receipt is None
    assert expected_code in errors


def test_recent_metadata_cannot_override_required_ref_divergence() -> None:
    case = _fixture()
    case["observed"]["mirror"]["refs"]["refs/heads/main"] = "8" * 40
    case["observed"]["mirror"]["updated_at"] = "2099-01-01T00:00:00Z"

    receipt, errors = _evaluate(case)

    assert receipt is None
    assert errors == ["MIRROR_FIELDS_INVALID", "MIRROR_REQUIRED_REF_MISMATCH"]


def test_credential_bearing_identity_is_rejected_without_echo() -> None:
    case = _fixture()
    credential = "synthetic-" + "credential"
    hostile = "https://user:" + credential + "@source.example.invalid/acme/canary.git"
    case["expectation"]["source_repository_identity"] = hostile

    receipt, errors = _evaluate(case)

    assert receipt is None
    assert "SOURCE_REPOSITORY_IDENTITY_INVALID" in errors
    rendered = json.dumps(errors)
    assert credential not in rendered
    assert hostile not in rendered
    assert all(error in PROBE_ERROR_CODES for error in errors)


@pytest.mark.parametrize(
    ("expected", "observed", "expected_code"),
    [
        (None, {}, "EXPECTED_NOT_OBJECT"),
        ({}, None, "OBSERVED_NOT_OBJECT"),
        ({"bad": float("nan")}, {}, "EXPECTED_JSON_INVALID"),
        ({}, {"source": {"bad": "\ud800"}}, "OBSERVED_JSON_INVALID"),
    ],
)
def test_malformed_json_shaped_inputs_are_total_and_fail_closed(
    expected: object, observed: object, expected_code: str
) -> None:
    receipt, errors = evaluate_repository_deployment_probe(expected, observed)

    assert receipt is None
    assert expected_code in errors
    assert errors == sorted(set(errors))
    assert all(error in PROBE_ERROR_CODES for error in errors)


def test_builtin_subclasses_cannot_escape_the_fixed_error_channel() -> None:
    class ExplodingString(str):
        def encode(self, *args: object, **kwargs: object) -> bytes:
            raise RuntimeError("RAW_PROVIDER_ERROR_SHOULD_NOT_ESCAPE")

        def casefold(self) -> str:
            raise RuntimeError("RAW_PROVIDER_ERROR_SHOULD_NOT_ESCAPE")

    case = _fixture()
    case["expectation"]["expectation_id"] = ExplodingString("expectation:synthetic-canary")

    receipt, errors = _evaluate(case)

    assert receipt is None
    assert "EXPECTED_JSON_INVALID" in errors
    assert errors == sorted(set(errors))
    assert all(error in PROBE_ERROR_CODES for error in errors)


def test_receipt_and_errors_are_deterministic() -> None:
    case = _fixture()
    first = _evaluate(case)
    second = _evaluate(deepcopy(case))

    assert first == second

    case["observed"]["source"]["refs"].pop("refs/heads/main")
    case["observed"]["mirror"]["refs"]["refs/tags/canary-v1"] = "8" * 40
    first_failure = _evaluate(case)
    second_failure = _evaluate(deepcopy(case))
    assert first_failure == second_failure
    assert first_failure[1] == sorted(set(first_failure[1]))
