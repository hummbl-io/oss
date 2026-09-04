# Copyright 2024-2026 HUMMBL, LLC
# Licensed under the Apache License, Version 2.0
# SPDX-License-Identifier: Apache-2.0

"""Contract tests for the bounded GitOps evidence registry pilot."""

from __future__ import annotations

from copy import deepcopy

import pytest

import hummbl_governance.gitops_evidence as gitops_evidence
from hummbl_governance.gitops_evidence import (
    canonical_sha256,
    claim_fingerprint,
    envelope_sha256,
    loads_strict_json,
    validate_envelope,
    validate_ledger,
    validate_manifest,
)


def _manifest() -> dict:
    return {
        "contract_version": "0.1.0",
        "record_type": "observation_manifest",
        "manifest_id": "manifest-gitops-pilot-001",
        "decision_question": "Can bounded Git state be reconciled without hiding collection failures?",
        "created_at": "2026-08-30T15:30:00Z",
        "collection_window": {
            "not_before": "2026-08-30T15:30:00Z",
            "not_after": "2026-08-30T16:30:00Z",
        },
        "observers": [
            {"observer_id": "codex", "role": "collector"},
            {"observer_id": "operator", "role": "operator"},
        ],
        "boundary": {
            "completeness_claim": "bounded_only",
            "scope_units": [
                {
                    "scope_id": "scope-repo-oss",
                    "target_kind": "repository",
                    "target_alias": "repo:oss",
                    "enumeration": "explicit",
                    "termination": "explicit_list_consumed",
                    "capabilities": ["git.refs"],
                    "inclusions": ["refs/heads/main"],
                    "exclusions": [],
                }
            ],
            "known_blind_spots": [
                {
                    "description": "Remote divergence is not refreshed during a read-only local scan.",
                    "disposition": "probe_later",
                }
            ],
            "surprise_probes": [
                {
                    "probe": "Compare registered roots with a bounded marker walk.",
                    "trigger": "An unregistered Git marker appears.",
                    "stop_condition": "The declared project root has been walked once.",
                }
            ],
        },
        "sources": [
            {
                "source_id": "source-local-git",
                "scope_id": "scope-repo-oss",
                "kind": "local_git",
                "authority_role": "primary_observation",
                "endpoint_alias": "local:repo-oss",
                "independence_domain": "host:node-primary",
                "read_only_required": True,
            }
        ],
        "predicate_profile": "gitops-observation-v0",
        "freshness_policy": {
            "max_age_seconds": 3600,
            "required_for_known_known": True,
        },
        "sanitization_policy": {
            "profile": "gitops-sanitizer-v0",
            "allowlist_only": True,
            "forbidden_data_classes": [
                "authorization_header",
                "cookie",
                "credential_value",
                "environment_value",
                "private_key",
                "secret_derived_hash",
                "url_userinfo",
            ],
            "absolute_paths": "alias",
            "hostile_display_text": True,
        },
        "corroboration_policy": {
            "minimum_independent_sources": 1,
            "minimum_independent_collectors": 1,
            "required_for_known_known": True,
        },
        "run_policy": {
            "enforcement_mode": "advisory_only",
            "collector_write_access": "forbidden",
            "dashboard_authority": "none",
            "planned_attempts": [
                {
                    "attempt_id": "attempt-repo-refs",
                    "scope_id": "scope-repo-oss",
                    "source_id": "source-local-git",
                    "capability": "git.refs",
                }
            ],
        },
    }


def _native_evidence() -> dict:
    return {
        "representation": "sanitized_source_native",
        "storage_ref": "sha256/aa/" + "a" * 64 + ".json",
        "sha256": "a" * 64,
        "byte_length": 128,
        "media_type": "application/json",
        "captured_at": "2026-08-30T15:35:00Z",
        "sanitizer_profile": "gitops-sanitizer-v0",
        "sanitizer_version": "0.1.0",
        "sanitizer_code_digest": "b" * 64,
        "transformations": ["allowlist_fields", "alias_absolute_paths"],
        "pre_sanitize_digest_retained": False,
        "sensitivity": "internal",
        "export_policy": "internal_only",
    }


def _envelope(
    sequence: int, previous_digest: str, manifest_digest: str, payload: dict
) -> dict:
    record = {
        "contract_version": "0.1.0",
        "record_type": "evidence_envelope",
        "envelope_id": f"00000000-0000-4000-8000-{sequence + 1:012d}",
        "manifest_digest": manifest_digest,
        "run_id": "10000000-0000-4000-8000-000000000001",
        "ingestion_nonce": "20000000-0000-4000-8000-000000000001",
        "sequence": sequence,
        "previous_digest": previous_digest,
        "started_at": "2026-08-30T15:34:00Z",
        "observed_at": "2026-08-30T15:35:00Z",
        "recorded_at": "2026-08-30T15:36:00Z",
        "provenance": {
            "agent": "codex",
            "host": "node-primary",
            "surface": "desktop-codex",
            "product": "codex",
            "executable": "unknown",
            "collector_name": "synthetic-contract-test",
            "collector_version": "0.1.0",
            "collector_code_digest": "c" * 64,
            "collector_config_digest": "d" * 64,
        },
        "source_context": {
            "scope_id": "scope-repo-oss",
            "source_id": "source-local-git",
        },
        "native_evidence": _native_evidence(),
        "payload": payload,
        "epistemic_assessments": [
            {
                "observer_id": "codex",
                "classified_at": "2026-08-30T15:36:00Z",
                "quadrant": "known_unknown",
                "evidence_state": "unverified",
                "basis_refs": ["envelope:00000000-0000-4000-8000-000000000001"],
                "rationale": "The bounded observation has not been independently corroborated.",
                "next_action": "Compare with a second independent source.",
            }
        ],
        "integrity": {"envelope_sha256": "0" * 64},
    }
    record["integrity"]["envelope_sha256"] = envelope_sha256(record)
    return record


def _attempt(manifest: dict) -> dict:
    manifest_digest = canonical_sha256(manifest)
    return _envelope(
        0,
        manifest_digest,
        manifest_digest,
        {
            "kind": "attempt",
            "attempt_id": "attempt-repo-refs",
            "capability": "git.refs",
            "status": "complete",
            "reason": "none",
            "result_count": 1,
            "enumeration_exhausted": True,
            "unobserved_portions": [],
            "observations": [
                _observation(),
                _observation(
                    subject=_subject(selector=None),
                    predicate="git.refs.count",
                    object_value=1,
                ),
            ],
        },
    )


def _claim(previous_envelope: dict) -> dict:
    payload = {
        "kind": "claim",
        "claim_id": "claim-main-ref-present",
        "attempt_envelope_id": previous_envelope["envelope_id"],
        "subject": {
            "scope_id": "scope-repo-oss",
            "target_alias": "repo:oss",
            "selector": "refs/heads/main",
        },
        "predicate": "git.ref.exists",
        "object": True,
        "normalization_profile": "gitops-observation-v0",
    }
    payload["semantic_claim_key"] = gitops_evidence.semantic_claim_key(payload)
    payload["claim_fingerprint"] = claim_fingerprint(payload)
    return _envelope(
        1,
        previous_envelope["integrity"]["envelope_sha256"],
        previous_envelope["manifest_digest"],
        payload,
    )


def _summary(previous_envelope: dict) -> dict:
    return _envelope(
        2,
        previous_envelope["integrity"]["envelope_sha256"],
        previous_envelope["manifest_digest"],
        {
            "kind": "run_summary",
            "planned_attempts": 1,
            "emitted_attempts": 1,
            "status_totals": {
                "complete": 1,
                "partial": 0,
                "failed": 0,
                "not_attempted": 0,
            },
            "prior_chain_digest": previous_envelope["integrity"]["envelope_sha256"],
            "boundary_result": "complete",
        },
    )


def _rehash(envelope: dict) -> None:
    envelope["integrity"]["envelope_sha256"] = envelope_sha256(envelope)


def _rechain(manifest: dict, envelopes: list[dict]) -> None:
    previous_digest = canonical_sha256(manifest)
    for sequence, envelope in enumerate(envelopes):
        envelope["sequence"] = sequence
        envelope["previous_digest"] = previous_digest
        if envelope.get("payload", {}).get("kind") == "run_summary":
            envelope["payload"]["prior_chain_digest"] = previous_digest
        _rehash(envelope)
        previous_digest = envelope["integrity"]["envelope_sha256"]


def _rebind_manifest(manifest: dict, envelopes: list[dict]) -> None:
    manifest_digest = canonical_sha256(manifest)
    for envelope in envelopes:
        envelope["manifest_digest"] = manifest_digest
    _rechain(manifest, envelopes)


def test_valid_bounded_manifest_and_ledger() -> None:
    manifest = _manifest()
    attempt = _attempt(manifest)
    claim = _claim(attempt)
    summary = _summary(claim)

    assert validate_manifest(manifest) == []
    assert validate_ledger(manifest, [attempt, claim, summary]) == []


def test_manifest_rejects_false_completeness_and_wildcards() -> None:
    manifest = _manifest()
    manifest["boundary"]["scope_units"][0]["inclusions"] = ["*"]

    errors = validate_manifest(manifest)

    assert any("wildcard" in error for error in errors)


def test_manifest_rejects_duplicate_ids_and_dangling_source_scope() -> None:
    manifest = _manifest()
    manifest["observers"].append(deepcopy(manifest["observers"][0]))
    manifest["sources"][0]["scope_id"] = "scope-missing"

    errors = validate_manifest(manifest)

    assert any("duplicate observer_id" in error for error in errors)
    assert any("unknown scope_id" in error for error in errors)


def test_schema_rejects_unknown_properties() -> None:
    manifest = _manifest()
    manifest["automatic_enforcement"] = True

    errors = validate_manifest(manifest)

    assert any("unexpected property" in error for error in errors)


def test_partial_attempt_requires_reason_and_unobserved_portions() -> None:
    manifest = _manifest()
    envelope = _attempt(manifest)
    envelope["payload"].update(
        status="partial", reason="none", unobserved_portions=[]
    )
    _rehash(envelope)

    errors = validate_envelope(envelope, manifest)

    assert any("partial attempt requires a non-none reason" in error for error in errors)
    assert any("partial attempt must identify unobserved portions" in error for error in errors)


def test_failed_attempt_cannot_imply_absence() -> None:
    manifest = _manifest()
    attempt = _attempt(manifest)
    attempt["payload"].update(
        status="failed",
        reason="unreachable",
        result_count=0,
        enumeration_exhausted=False,
        unobserved_portions=["remote refs"],
    )
    _rehash(attempt)
    claim = _claim(attempt)
    claim["payload"]["object"] = False
    claim["payload"]["claim_fingerprint"] = claim_fingerprint(claim["payload"])
    _rehash(claim)
    summary = _summary(claim)

    errors = validate_ledger(manifest, [attempt, claim, summary])

    assert any("absence claim requires a complete, exhausted attempt" in error for error in errors)


def test_complete_exhausted_attempt_may_support_absence() -> None:
    manifest = _manifest()
    attempt = _attempt(manifest)
    attempt["payload"].update(result_count=0)
    _rehash(attempt)
    claim = _claim(attempt)
    claim["payload"]["object"] = False
    claim["payload"]["claim_fingerprint"] = claim_fingerprint(claim["payload"])
    _rehash(claim)
    summary = _summary(claim)

    errors = validate_ledger(manifest, [attempt, claim, summary])

    assert not any("absence claim" in error for error in errors)


def test_unknown_unknown_cannot_classify_a_positive_claim() -> None:
    manifest = _manifest()
    attempt = _attempt(manifest)
    claim = _claim(attempt)
    claim["epistemic_assessments"][0].update(
        quadrant="unknown_unknown",
        rationale="A positive fact cannot occupy residual unmodeled risk.",
    )
    _rehash(claim)

    errors = validate_envelope(claim, manifest)

    assert any("unknown_unknown cannot classify a factual claim" in error for error in errors)


def test_epistemic_assessment_is_observer_relative() -> None:
    manifest = _manifest()
    attempt = _attempt(manifest)
    attempt["epistemic_assessments"].append(
        {
            "observer_id": "operator",
            "classified_at": "2026-08-30T15:36:00Z",
            "quadrant": "known_known",
            "evidence_state": "verified_current",
            "basis_refs": [
                "envelope:00000000-0000-4000-8000-000000000001"
            ],
            "rationale": "The operator independently inspected the bounded source.",
        }
    )
    _rehash(attempt)

    assert validate_envelope(attempt, manifest) == []


def test_known_known_requires_current_evidence_and_corroboration() -> None:
    manifest = _manifest()
    manifest["corroboration_policy"]["minimum_independent_sources"] = 2
    _add_source(manifest)
    attempt = _attempt(manifest)
    assessment = attempt["epistemic_assessments"][0]
    assessment.update(quadrant="known_known", evidence_state="verified_stale")
    assessment.pop("next_action")
    _rehash(attempt)

    errors = validate_envelope(attempt, manifest)

    assert any("known_known requires verified_current evidence" in error for error in errors)
    assert any("known_known requires at least 2 basis refs" in error for error in errors)


def test_native_evidence_path_must_be_relative_and_content_addressed() -> None:
    manifest = _manifest()
    envelope = _attempt(manifest)
    envelope["native_evidence"]["storage_ref"] = "/tmp/private.json"
    _rehash(envelope)

    errors = validate_envelope(envelope, manifest)

    assert any("content-addressed relative path" in error for error in errors)


def test_timestamps_must_be_ordered() -> None:
    manifest = _manifest()
    envelope = _attempt(manifest)
    envelope["observed_at"] = "2026-08-30T15:33:00Z"
    _rehash(envelope)

    errors = validate_envelope(envelope, manifest)

    assert any("started_at <= observed_at <= recorded_at" in error for error in errors)


def test_digest_chain_detects_mutation_and_reordering() -> None:
    manifest = _manifest()
    attempt = _attempt(manifest)
    claim = _claim(attempt)
    attempt["payload"]["result_count"] = 99

    mutation_errors = validate_ledger(manifest, [attempt, claim])
    reorder_errors = validate_ledger(manifest, [claim, attempt])

    assert any("envelope_sha256 mismatch" in error for error in mutation_errors)
    assert any("sequence must be contiguous" in error for error in reorder_errors)


def test_run_summary_is_recomputed_not_trusted() -> None:
    manifest = _manifest()
    attempt = _attempt(manifest)
    claim = _claim(attempt)
    summary = _summary(claim)
    summary["payload"]["status_totals"]["complete"] = 9
    _rehash(summary)

    errors = validate_ledger(manifest, [attempt, claim, summary])

    assert any("summary status_totals do not match emitted attempts" in error for error in errors)


def test_missing_planned_attempt_is_visible() -> None:
    manifest = _manifest()
    summary = _envelope(
        0,
        canonical_sha256(manifest),
        canonical_sha256(manifest),
        {
            "kind": "run_summary",
            "planned_attempts": 1,
            "emitted_attempts": 0,
            "status_totals": {
                "complete": 0,
                "partial": 0,
                "failed": 0,
                "not_attempted": 0,
            },
            "prior_chain_digest": canonical_sha256(manifest),
            "boundary_result": "complete",
        },
    )

    errors = validate_ledger(manifest, [summary])

    assert any("missing planned attempts" in error for error in errors)
    assert any("boundary_result cannot be complete" in error for error in errors)


def test_complete_attempt_requires_exhausted_enumeration() -> None:
    manifest = _manifest()
    attempt = _attempt(manifest)
    attempt["payload"]["enumeration_exhausted"] = False
    _rehash(attempt)
    claim = _claim(attempt)
    summary = _summary(claim)

    errors = validate_ledger(manifest, [attempt, claim, summary])

    assert any("complete attempt requires exhausted enumeration" in error for error in errors)
    assert any("boundary_result cannot be complete" in error for error in errors)


def test_emitted_attempt_is_bound_to_exact_planned_tuple() -> None:
    manifest = _manifest()
    attempt = _attempt(manifest)
    attempt["payload"]["capability"] = "git.worktrees"
    _rehash(attempt)
    summary = _summary(attempt)

    errors = validate_ledger(manifest, [attempt, summary])

    assert any("does not match its planned scope/source/capability tuple" in error for error in errors)


def test_manifest_requires_every_declared_scope_capability_to_be_planned() -> None:
    manifest = _manifest()
    manifest["boundary"]["scope_units"][0]["capabilities"].append("git.worktrees")

    errors = validate_manifest(manifest)

    assert any("planned attempt matrix does not cover" in error for error in errors)


def test_negative_boolean_claim_cannot_bypass_absence_gate() -> None:
    manifest = _manifest()
    attempt = _attempt(manifest)
    attempt["payload"].update(
        status="failed",
        reason="unreachable",
        result_count=0,
        enumeration_exhausted=False,
        unobserved_portions=["remote refs"],
    )
    _rehash(attempt)
    claim = _claim(attempt)
    claim["payload"]["object"] = False
    claim["payload"]["claim_fingerprint"] = claim_fingerprint(claim["payload"])
    _rehash(claim)
    summary = _summary(claim)

    errors = validate_ledger(manifest, [attempt, claim, summary])

    assert any("absence claim requires a complete, exhausted attempt" in error for error in errors)


def test_claim_fingerprint_is_recomputed() -> None:
    manifest = _manifest()
    attempt = _attempt(manifest)
    claim = _claim(attempt)
    claim["payload"]["subject"]["target_alias"] = "repo:changed"
    _rehash(claim)

    errors = validate_envelope(claim, manifest)

    assert any("claim_fingerprint mismatch" in error for error in errors)


def test_known_known_basis_refs_must_resolve_and_be_fresh() -> None:
    manifest = _manifest()
    attempt = _attempt(manifest)
    attempt["observed_at"] = "2020-01-01T00:00:00Z"
    assessment = attempt["epistemic_assessments"][0]
    assessment.update(
        quadrant="known_known",
        evidence_state="verified_current",
        basis_refs=["envelope:ffffffff-ffff-4fff-8fff-ffffffffffff"],
    )
    assessment.pop("next_action")
    _rehash(attempt)
    summary = _summary(attempt)

    errors = validate_ledger(manifest, [attempt, summary])

    assert any("basis ref does not resolve" in error for error in errors)
    assert any("verified_current basis is outside the freshness policy" in error for error in errors)


def test_sanitization_policy_requires_all_classes_and_opaque_credential_ref() -> None:
    manifest = _manifest()
    manifest["sanitization_policy"]["forbidden_data_classes"] = ["cookie"] * 7
    synthetic_userinfo = ":".join(("user", "".join(("pass", "word"))))
    manifest["sources"][0]["credential_ref"] = (
        f"https://{synthetic_userinfo}@example.invalid/token"
    )

    errors = validate_manifest(manifest)

    assert any("forbidden_data_classes must contain the complete required set" in error for error in errors)
    assert any("credential_ref must be an opaque credential: alias" in error for error in errors)


def test_malformed_nested_input_returns_errors_instead_of_crashing() -> None:
    manifest = _manifest()
    manifest["boundary"]["scope_units"] = ["malformed"]

    errors = validate_manifest(manifest)

    assert errors


def test_finalized_ledger_requires_summary() -> None:
    manifest = _manifest()
    attempt = _attempt(manifest)

    errors = validate_ledger(manifest, [attempt])

    assert any("finalized ledger requires exactly one run_summary" in error for error in errors)


def test_native_evidence_metadata_matches_manifest_and_content_address() -> None:
    manifest = _manifest()
    attempt = _attempt(manifest)
    attempt["native_evidence"]["storage_ref"] = "sha256/ff/" + "a" * 64 + ".json"
    attempt["native_evidence"]["sanitizer_profile"] = "different-profile"
    _rehash(attempt)

    errors = validate_envelope(attempt, manifest)

    assert any("storage_ref shard does not match evidence sha256" in error for error in errors)
    assert any("sanitizer_profile does not match the manifest" in error for error in errors)


def test_canonical_hash_is_byte_preserving_and_duplicate_keys_are_rejected() -> None:
    composed = {"label": "\u00e9"}
    decomposed = {"label": "e\u0301"}

    assert canonical_sha256(composed) != canonical_sha256(decomposed)
    try:
        loads_strict_json('{"scope":"first","scope":"second"}')
    except ValueError as exc:
        assert "duplicate JSON object key" in str(exc)
    else:
        raise AssertionError("duplicate keys must be rejected before validation")


def test_manifest_rejects_impossible_timestamp_and_boolean_integer() -> None:
    manifest = _manifest()
    manifest["created_at"] = "2026-02-31T15:30:00Z"
    manifest["freshness_policy"]["max_age_seconds"] = True

    errors = validate_manifest(manifest)

    assert any("created_at is not a valid UTC timestamp" in error for error in errors)
    assert any("max_age_seconds" in error and "bool" in error for error in errors)


def test_attempt_and_claim_context_cannot_be_crosswired() -> None:
    manifest = _manifest()
    second_scope = deepcopy(manifest["boundary"]["scope_units"][0])
    second_scope.update(scope_id="scope-repo-two", target_alias="repo:two")
    manifest["boundary"]["scope_units"].append(second_scope)
    manifest["sources"].append(
        {
            "source_id": "source-local-two",
            "scope_id": "scope-repo-two",
            "kind": "local_git",
            "authority_role": "primary_observation",
            "endpoint_alias": "local:repo-two",
            "independence_domain": "host:node-secondary",
            "read_only_required": True,
        }
    )
    manifest["run_policy"]["planned_attempts"].append(
        {
            "attempt_id": "attempt-repo-two-refs",
            "scope_id": "scope-repo-two",
            "source_id": "source-local-two",
            "capability": "git.refs",
        }
    )
    attempt = _attempt(manifest)
    attempt["source_context"].update(
        scope_id="scope-repo-two", source_id="source-local-two"
    )
    _rehash(attempt)
    claim = _claim(attempt)
    claim["source_context"].update(
        scope_id="scope-repo-oss", source_id="source-local-git"
    )
    _rehash(claim)
    second_attempt = _envelope(
        2,
        claim["integrity"]["envelope_sha256"],
        canonical_sha256(manifest),
        {
            "kind": "attempt",
            "attempt_id": "attempt-repo-two-refs",
            "capability": "git.refs",
            "status": "complete",
            "reason": "none",
            "result_count": 1,
            "enumeration_exhausted": True,
            "unobserved_portions": [],
            "observations": [
                _observation(
                    subject=_subject(
                        scope_id="scope-repo-two",
                        target_alias="repo:two",
                    )
                ),
                _observation(
                    subject=_subject(
                        scope_id="scope-repo-two",
                        target_alias="repo:two",
                        selector=None,
                    ),
                    predicate="git.refs.count",
                    object_value=1,
                ),
            ],
        },
    )
    second_attempt["source_context"].update(
        scope_id="scope-repo-two", source_id="source-local-two"
    )
    _rehash(second_attempt)
    summary = _envelope(
        3,
        second_attempt["integrity"]["envelope_sha256"],
        canonical_sha256(manifest),
        {
            "kind": "run_summary",
            "planned_attempts": 2,
            "emitted_attempts": 2,
            "status_totals": {
                "complete": 2,
                "partial": 0,
                "failed": 0,
                "not_attempted": 0,
            },
            "prior_chain_digest": second_attempt["integrity"]["envelope_sha256"],
            "boundary_result": "complete",
        },
    )

    errors = validate_ledger(manifest, [attempt, claim, second_attempt, summary])

    assert any("does not match its planned scope/source/capability tuple" in error for error in errors)
    assert any("claim source_context must match its referenced attempt" in error for error in errors)


def test_absence_claim_requires_exact_false_observation() -> None:
    manifest = _manifest()
    attempt = _attempt(manifest)
    claim = _claim(attempt)
    claim["payload"]["object"] = False
    claim["payload"]["claim_fingerprint"] = claim_fingerprint(claim["payload"])
    _rehash(claim)
    summary = _summary(claim)

    errors = validate_ledger(manifest, [attempt, claim, summary])

    assert any(
        "claim fact is not present in referenced attempt observations" in error
        for error in errors
    )


def test_known_known_requires_independent_resolved_provenance() -> None:
    manifest = _manifest()
    manifest["corroboration_policy"]["minimum_independent_sources"] = 2
    _add_source(manifest)
    attempt = _attempt(manifest)
    assessment = attempt["epistemic_assessments"][0]
    assessment.update(
        quadrant="known_known",
        evidence_state="verified_current",
        basis_refs=[
            f"envelope:{attempt['envelope_id']}",
            f"envelope:{attempt['envelope_id']}",
        ],
    )
    assessment.pop("next_action")
    _rehash(attempt)
    summary = _summary(attempt)

    errors = validate_ledger(manifest, [attempt, summary])

    assert any("independent source/collector provenance" in error for error in errors)


def test_native_evidence_full_digest_and_media_type_are_consistent() -> None:
    manifest = _manifest()
    attempt = _attempt(manifest)
    attempt["native_evidence"]["storage_ref"] = "sha256/aa/" + "b" * 64 + ".txt"
    _rehash(attempt)

    errors = validate_envelope(attempt, manifest)

    assert any("storage_ref digest does not match evidence sha256" in error for error in errors)
    assert any("storage_ref extension does not match evidence media_type" in error for error in errors)


def test_claim_predicate_object_type_and_count_are_recomputed() -> None:
    manifest = _manifest()
    attempt = _attempt(manifest)
    claim = _claim(attempt)
    claim["payload"].update(predicate="git.refs.count", object=2)
    claim["payload"]["claim_fingerprint"] = claim_fingerprint(claim["payload"])
    _rehash(claim)
    summary = _summary(claim)

    errors = validate_ledger(manifest, [attempt, claim, summary])

    assert any("count claim object does not match" in error for error in errors)

    claim["payload"]["object"] = "2"
    claim["payload"]["claim_fingerprint"] = claim_fingerprint(claim["payload"])
    _rehash(claim)
    errors = validate_envelope(claim, manifest)
    assert any("count claim predicate requires an integer object" in error for error in errors)


def test_envelope_timestamp_must_be_real_and_inside_collection_window() -> None:
    manifest = _manifest()
    attempt = _attempt(manifest)
    attempt["observed_at"] = "2026-02-31T15:35:00Z"
    _rehash(attempt)

    errors = validate_envelope(attempt, manifest)

    assert any("observed_at is not a valid UTC timestamp" in error for error in errors)

    attempt = _attempt(manifest)
    attempt["started_at"] = "2026-08-30T17:00:00Z"
    attempt["observed_at"] = "2026-08-30T17:01:00Z"
    attempt["recorded_at"] = "2026-08-30T17:02:00Z"
    attempt["native_evidence"]["captured_at"] = "2026-08-30T17:01:00Z"
    attempt["epistemic_assessments"][0]["classified_at"] = "2026-08-30T17:02:00Z"
    _rehash(attempt)

    errors = validate_envelope(attempt, manifest)

    assert any("outside the manifest collection_window" in error for error in errors)


def _subject(
    *,
    scope_id: str = "scope-repo-oss",
    target_alias: str = "repo:oss",
    selector: str | None = "refs/heads/main",
) -> dict:
    subject = {"scope_id": scope_id, "target_alias": target_alias}
    if selector is not None:
        subject["selector"] = selector
    return subject


def _observation(
    *,
    subject: dict | None = None,
    predicate: str = "git.ref.exists",
    object_value: object = True,
) -> dict:
    return {
        "subject": subject or _subject(),
        "predicate": predicate,
        "object": object_value,
        "normalization_profile": "gitops-observation-v0",
    }


def _set_manifest_capability(manifest: dict, capability: str) -> None:
    manifest["boundary"]["scope_units"][0]["capabilities"] = [capability]
    manifest["run_policy"]["planned_attempts"][0]["capability"] = capability


def _add_source(
    manifest: dict,
    *,
    source_id: str = "source-local-two",
    attempt_id: str = "attempt-repo-refs-two",
    endpoint_alias: str = "local:repo-oss-secondary",
    independence_domain: str = "host:node-secondary",
) -> None:
    source = deepcopy(manifest["sources"][0])
    source.update(
        source_id=source_id,
        endpoint_alias=endpoint_alias,
        independence_domain=independence_domain,
    )
    manifest["sources"].append(source)
    manifest["run_policy"]["planned_attempts"].append(
        {
            "attempt_id": attempt_id,
            "scope_id": source["scope_id"],
            "source_id": source_id,
            "capability": manifest["boundary"]["scope_units"][0]["capabilities"][0],
        }
    )


def _attempt_for(
    manifest: dict,
    *,
    sequence: int,
    previous_digest: str,
    attempt_id: str,
    source_id: str,
    collector_name: str,
    host: str,
    capability: str = "git.refs",
    status: str = "complete",
    reason: str = "none",
    result_count: int = 1,
    enumeration_exhausted: bool = True,
    unobserved_portions: list[str] | None = None,
    observations: list[dict] | None = None,
) -> dict:
    if observations is None:
        if status in {"failed", "not_attempted"}:
            observations = []
        else:
            observations = [
                _observation(object_value=result_count > 0),
                _observation(
                    subject=_subject(selector=None),
                    predicate="git.refs.count",
                    object_value=result_count,
                ),
            ]
    envelope = _envelope(
        sequence,
        previous_digest,
        canonical_sha256(manifest),
        {
            "kind": "attempt",
            "attempt_id": attempt_id,
            "capability": capability,
            "status": status,
            "reason": reason,
            "result_count": result_count,
            "enumeration_exhausted": enumeration_exhausted,
            "unobserved_portions": unobserved_portions or [],
            "observations": observations,
        },
    )
    source = next(item for item in manifest["sources"] if item["source_id"] == source_id)
    envelope["source_context"] = {
        "scope_id": source["scope_id"],
        "source_id": source_id,
    }
    envelope["provenance"]["collector_name"] = collector_name
    envelope["provenance"]["host"] = host
    _rehash(envelope)
    return envelope


def _claim_for(
    *,
    sequence: int,
    previous_envelope: dict,
    attempt_envelope: dict,
    claim_id: str,
    subject: dict | None = None,
    predicate: str = "git.ref.exists",
    object_value: object = True,
) -> dict:
    payload = {
        "kind": "claim",
        "claim_id": claim_id,
        "attempt_envelope_id": attempt_envelope["envelope_id"],
        "subject": subject or _subject(),
        "predicate": predicate,
        "object": object_value,
        "normalization_profile": "gitops-observation-v0",
    }
    payload["semantic_claim_key"] = gitops_evidence.semantic_claim_key(payload)
    payload["claim_fingerprint"] = claim_fingerprint(payload)
    envelope = _envelope(
        sequence,
        previous_envelope["integrity"]["envelope_sha256"],
        previous_envelope["manifest_digest"],
        payload,
    )
    envelope["source_context"] = deepcopy(attempt_envelope["source_context"])
    envelope["provenance"] = deepcopy(attempt_envelope["provenance"])
    _rehash(envelope)
    return envelope


def _summary_for(
    manifest: dict,
    *,
    sequence: int,
    previous_envelope: dict,
    attempts: list[dict],
    boundary_result: str = "complete",
) -> dict:
    status_totals = {"complete": 0, "partial": 0, "failed": 0, "not_attempted": 0}
    for attempt in attempts:
        status_totals[attempt["payload"]["status"]] += 1
    return _envelope(
        sequence,
        previous_envelope["integrity"]["envelope_sha256"],
        canonical_sha256(manifest),
        {
            "kind": "run_summary",
            "planned_attempts": len(manifest["run_policy"]["planned_attempts"]),
            "emitted_attempts": len(attempts),
            "status_totals": status_totals,
            "prior_chain_digest": previous_envelope["integrity"]["envelope_sha256"],
            "boundary_result": boundary_result,
        },
    )


def _two_source_corroborated_ledger(
    *, second_domain: str, second_collector: str
) -> tuple[dict, list[dict]]:
    manifest = _manifest()
    manifest["corroboration_policy"].update(
        minimum_independent_sources=2,
        minimum_independent_collectors=2,
    )
    _add_source(manifest, independence_domain=second_domain)
    manifest_digest = canonical_sha256(manifest)
    first_attempt = _attempt_for(
        manifest,
        sequence=0,
        previous_digest=manifest_digest,
        attempt_id="attempt-repo-refs",
        source_id="source-local-git",
        collector_name="collector-a",
        host="node-primary",
    )
    second_attempt = _attempt_for(
        manifest,
        sequence=1,
        previous_digest=first_attempt["integrity"]["envelope_sha256"],
        attempt_id="attempt-repo-refs-two",
        source_id="source-local-two",
        collector_name=second_collector,
        host="node-secondary",
    )
    first_basis = _claim_for(
        sequence=2,
        previous_envelope=second_attempt,
        attempt_envelope=first_attempt,
        claim_id="claim-main-ref-source-one",
    )
    second_basis = _claim_for(
        sequence=3,
        previous_envelope=first_basis,
        attempt_envelope=second_attempt,
        claim_id="claim-main-ref-source-two",
    )
    assessed_claim = _claim_for(
        sequence=4,
        previous_envelope=second_basis,
        attempt_envelope=first_attempt,
        claim_id="claim-main-ref-corroborated",
    )
    assessment = assessed_claim["epistemic_assessments"][0]
    assessment.update(
        quadrant="known_known",
        evidence_state="verified_current",
        basis_refs=[
            f"envelope:{first_basis['envelope_id']}",
            f"envelope:{second_basis['envelope_id']}",
        ],
    )
    assessment.pop("next_action")
    _rehash(assessed_claim)
    summary = _summary_for(
        manifest,
        sequence=5,
        previous_envelope=assessed_claim,
        attempts=[first_attempt, second_attempt],
    )
    return manifest, [
        first_attempt,
        second_attempt,
        first_basis,
        second_basis,
        assessed_claim,
        summary,
    ]


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("scope_id", "scope-repo-other", "subject scope_id"),
        ("target_alias", "repo:other", "subject target_alias"),
        ("selector", "refs/heads/undeclared", "subject selector"),
    ],
)
def test_security_structured_claim_subject_is_bound_to_scope(
    field: str, value: str, message: str
) -> None:
    manifest = _manifest()
    attempt = _attempt(manifest)
    claim = _claim(attempt)
    claim["payload"]["subject"][field] = value
    claim["payload"]["claim_fingerprint"] = claim_fingerprint(claim["payload"])
    _rehash(claim)
    summary = _summary(claim)

    errors = validate_ledger(manifest, [attempt, claim, summary])

    assert any(message in error for error in errors)


@pytest.mark.parametrize(
    ("predicate", "object_value", "selector", "message"),
    [
        ("git.ref.exists", True, None, "requires subject.selector"),
        ("git.remote.exists", True, None, "requires subject.selector"),
        ("git.worktree.exists", True, None, "requires subject.selector"),
        ("git.stash.exists", True, None, "requires subject.selector"),
        ("git.workflow.exists", True, None, "requires subject.selector"),
        ("git.repository.exists", True, "refs/heads/main", "forbids subject.selector"),
        ("git.refs.count", 3, "refs/heads/main", "forbids subject.selector"),
        ("git.protection.enabled", False, None, "requires subject.selector"),
    ],
)
def test_security_subject_selector_presence_matches_predicate_level(
    predicate: str,
    object_value: object,
    selector: str | None,
    message: str,
) -> None:
    manifest = _manifest()
    attempt = _attempt(manifest)
    claim = _claim(attempt)
    claim["payload"].update(
        predicate=predicate,
        object=object_value,
        subject=_subject(selector=selector),
    )
    claim["payload"]["claim_fingerprint"] = claim_fingerprint(claim["payload"])
    _rehash(claim)

    errors = validate_envelope(claim, manifest)

    assert any(message in error for error in errors)


def test_security_duplicate_claim_id_is_rejected() -> None:
    manifest = _manifest()
    manifest["boundary"]["scope_units"][0]["inclusions"].append("refs/heads/dev")
    attempt = _attempt(manifest)
    first_claim = _claim(attempt)
    second_claim = _claim_for(
        sequence=2,
        previous_envelope=first_claim,
        attempt_envelope=attempt,
        claim_id=first_claim["payload"]["claim_id"],
        subject=_subject(selector="refs/heads/dev"),
    )
    summary = _summary_for(
        manifest,
        sequence=3,
        previous_envelope=second_claim,
        attempts=[attempt],
    )

    errors = validate_ledger(manifest, [attempt, first_claim, second_claim, summary])

    assert any("duplicate claim_id" in error for error in errors)


@pytest.mark.parametrize(
    ("status", "reason"),
    [("failed", "source_error"), ("not_attempted", "explicitly_excluded")],
)
def test_security_failed_or_unattempted_observations_require_zero_results(
    status: str, reason: str
) -> None:
    manifest = _manifest()
    attempt = _attempt(manifest)
    attempt["payload"].update(
        status=status,
        reason=reason,
        result_count=1,
        enumeration_exhausted=False,
        unobserved_portions=["refs"],
    )
    _rehash(attempt)

    errors = validate_envelope(attempt, manifest)

    assert any(f"{status} attempt requires result_count=0" in error for error in errors)


@pytest.mark.parametrize(
    ("status", "reason"),
    [("failed", "source_error"), ("not_attempted", "explicitly_excluded")],
)
def test_security_failed_or_unattempted_observations_cannot_support_claims(
    status: str, reason: str
) -> None:
    manifest = _manifest()
    _set_manifest_capability(manifest, "forge.protection")
    attempt = _attempt(manifest)
    attempt["payload"].update(
        capability="forge.protection",
        status=status,
        reason=reason,
        result_count=0,
        enumeration_exhausted=False,
        unobserved_portions=["repository protection"],
    )
    _rehash(attempt)
    claim = _claim(attempt)
    claim["payload"].update(
        predicate="git.protection.enabled",
        object=False,
        subject=_subject(selector=None),
    )
    claim["payload"]["claim_fingerprint"] = claim_fingerprint(claim["payload"])
    _rehash(claim)

    errors = validate_ledger(manifest, [attempt, claim], finalized=False)

    assert any(f"{status} attempt cannot support claims" in error for error in errors)


@pytest.mark.parametrize(
    ("predicate", "capability"),
    [
        ("git.refs.count", "git.refs"),
        ("git.remotes.count", "git.remotes"),
        ("git.worktrees.count", "git.worktrees"),
        ("git.stashes.count", "git.stashes"),
    ],
)
def test_security_count_claim_requires_complete_exhausted_enumeration(
    predicate: str, capability: str
) -> None:
    manifest = _manifest()
    _set_manifest_capability(manifest, capability)
    attempt = _attempt(manifest)
    attempt["payload"].update(
        capability=capability,
        status="partial",
        reason="denied",
        enumeration_exhausted=False,
        unobserved_portions=["hidden refs"],
    )
    _rehash(attempt)
    claim = _claim(attempt)
    claim["payload"].update(
        predicate=predicate,
        object=attempt["payload"]["result_count"],
        subject=_subject(selector=None),
    )
    claim["payload"]["claim_fingerprint"] = claim_fingerprint(claim["payload"])
    _rehash(claim)

    errors = validate_ledger(manifest, [attempt, claim], finalized=False)

    assert any("count claim requires a complete, exhausted attempt" in error for error in errors)


def test_security_false_state_requires_complete_positive_observation() -> None:
    manifest = _manifest()
    _set_manifest_capability(manifest, "forge.protection")
    attempt = _attempt(manifest)
    attempt["payload"].update(
        capability="forge.protection",
        status="partial",
        reason="denied",
        result_count=1,
        enumeration_exhausted=False,
        unobserved_portions=["organization rulesets"],
    )
    _rehash(attempt)
    claim = _claim(attempt)
    claim["payload"].update(
        predicate="git.protection.enabled",
        object=False,
        subject=_subject(selector=None),
    )
    claim["payload"]["claim_fingerprint"] = claim_fingerprint(claim["payload"])
    _rehash(claim)

    errors = validate_ledger(manifest, [attempt, claim], finalized=False)

    assert any(
        "false boolean state claim requires a complete, exhausted positive observation"
        in error
        for error in errors
    )


@pytest.mark.parametrize(
    ("predicate", "capability", "selector"),
    [
        ("git.repository.exists", "git.repository", None),
        ("git.ref.exists", "git.refs", "refs/heads/main"),
        ("git.remote.exists", "git.remotes", "origin"),
        ("git.worktree.exists", "git.worktrees", "worktree:main"),
        ("git.stash.exists", "git.stashes", "stash@{0}"),
        ("git.workflow.exists", "forge.workflows", ".github/workflows/ci.yml"),
    ],
)
def test_security_exists_claims_require_attempt_bound_polarity(
    predicate: str, capability: str, selector: str | None
) -> None:
    negative_message = (
        "exists=false claim requires a zero result"
        if predicate == "git.repository.exists"
        else "claim fact is not present in referenced attempt observations"
    )
    for object_value, result_count, message in (
        (True, 0, "exists=true claim requires a positive result"),
        (False, 1, negative_message),
    ):
        manifest = _manifest()
        _set_manifest_capability(manifest, capability)
        if selector is not None:
            manifest["boundary"]["scope_units"][0]["inclusions"] = [selector]
        attempt = _attempt(manifest)
        attempt["payload"].update(
            capability=capability,
            result_count=result_count,
            observations=[
                _observation(
                    subject=_subject(selector=selector),
                    predicate=predicate,
                    object_value=not object_value,
                )
            ],
        )
        _rehash(attempt)
        claim = _claim(attempt)
        claim["payload"].update(
            predicate=predicate,
            object=object_value,
            subject=_subject(selector=selector),
        )
        claim["payload"]["claim_fingerprint"] = claim_fingerprint(claim["payload"])
        _rehash(claim)

        errors = validate_ledger(manifest, [attempt, claim], finalized=False)

        assert any(message in error for error in errors)


def test_security_duplicate_endpoint_alias_cannot_clone_an_independence_domain() -> None:
    manifest = _manifest()
    _add_source(
        manifest,
        endpoint_alias=manifest["sources"][0]["endpoint_alias"],
        independence_domain="host:node-secondary",
    )

    errors = validate_manifest(manifest)

    assert any("duplicate endpoint_alias" in error for error in errors)


@pytest.mark.parametrize(
    ("second_domain", "second_collector", "message"),
    [
        ("host:node-primary", "collector-b", "independence domain"),
        ("host:node-secondary", "collector-a", "independent collectors"),
    ],
)
def test_security_known_known_requires_independent_domains_and_collectors(
    second_domain: str, second_collector: str, message: str
) -> None:
    manifest, envelopes = _two_source_corroborated_ledger(
        second_domain=second_domain,
        second_collector=second_collector,
    )

    errors = validate_ledger(manifest, envelopes)

    assert any(message in error for error in errors)


def test_security_distinct_domains_and_collectors_can_corroborate() -> None:
    manifest, envelopes = _two_source_corroborated_ledger(
        second_domain="host:node-secondary",
        second_collector="collector-b",
    )
    envelopes[1]["payload"]["observations"].reverse()
    _rechain(manifest, envelopes)

    assert validate_ledger(manifest, envelopes) == []


def test_security_semantic_claim_key_ignores_record_linkage_but_tracks_fact() -> None:
    manifest = _manifest()
    attempt = _attempt(manifest)
    payload = _claim(attempt)["payload"]
    relinked = deepcopy(payload)
    relinked.update(
        claim_id="claim-main-ref-present-copy",
        attempt_envelope_id="ffffffff-ffff-4fff-8fff-ffffffffffff",
    )

    assert gitops_evidence.semantic_claim_key(payload) == gitops_evidence.semantic_claim_key(relinked)

    changed_fact = deepcopy(relinked)
    changed_fact["subject"]["selector"] = "refs/heads/dev"
    assert gitops_evidence.semantic_claim_key(payload) != gitops_evidence.semantic_claim_key(changed_fact)

    changed_fact = deepcopy(relinked)
    changed_fact.update(
        predicate="git.refs.count",
        object=3,
        subject=_subject(selector=None),
    )
    assert gitops_evidence.semantic_claim_key(payload) != gitops_evidence.semantic_claim_key(changed_fact)

    changed_fact = deepcopy(relinked)
    changed_fact["object"] = False
    assert gitops_evidence.semantic_claim_key(payload) != gitops_evidence.semantic_claim_key(changed_fact)


def test_security_semantic_claim_key_is_recomputed() -> None:
    manifest = _manifest()
    attempt = _attempt(manifest)
    claim = _claim(attempt)
    claim["payload"]["semantic_claim_key"] = "f" * 64
    claim["payload"]["claim_fingerprint"] = claim_fingerprint(claim["payload"])
    _rehash(claim)

    errors = validate_envelope(claim, manifest)

    assert any("semantic_claim_key mismatch" in error for error in errors)


def test_security_trailing_non_object_is_reported_without_crashing() -> None:
    manifest = _manifest()
    attempt = _attempt(manifest)
    claim = _claim(attempt)
    summary = _summary(claim)

    errors = validate_ledger(manifest, [attempt, claim, summary, "malformed"])

    assert any("envelopes[3] must be an object" in error for error in errors)


@pytest.mark.parametrize(
    "noncanonical_value",
    [1 << 53, "\ud800"],
    ids=["oversized-jcs-integer", "lone-surrogate"],
)
@pytest.mark.parametrize("location", ["attempt_observation", "claim_object"])
def test_security_noncanonical_ledger_fact_values_fail_closed(
    noncanonical_value: object,
    location: str,
) -> None:
    manifest = _manifest()
    attempt = _attempt(manifest)
    claim = _claim(attempt)
    if location == "attempt_observation":
        attempt["payload"]["observations"][0]["object"] = noncanonical_value
    else:
        claim["payload"]["object"] = noncanonical_value

    errors = validate_ledger(manifest, [attempt, claim], finalized=False)

    assert any("canonical JSON" in error for error in errors)


@pytest.mark.parametrize("surrogate", ["\\ud800", "\\udfff"])
@pytest.mark.parametrize("position", ["key", "value"])
def test_security_strict_json_rejects_lone_surrogates(
    surrogate: str, position: str
) -> None:
    if position == "key":
        document = '{"' + surrogate + '":"value"}'
    else:
        document = '{"value":"' + surrogate + '"}'

    with pytest.raises(ValueError, match="surrogate"):
        loads_strict_json(document)


@pytest.mark.parametrize("surrogate", ["\ud800", "\udfff"])
@pytest.mark.parametrize("position", ["key", "value"])
def test_security_raw_dict_validation_rejects_lone_surrogates(
    surrogate: str, position: str
) -> None:
    manifest = _manifest()
    if position == "key":
        manifest["boundary"]["scope_units"][0][surrogate] = "value"
    else:
        manifest["decision_question"] = surrogate

    errors = validate_manifest(manifest)

    assert any("surrogate" in error.lower() for error in errors)


@pytest.mark.parametrize(
    "absolute_path",
    [r"C:\Private\private-repo", r"\\server\share\private-repo", "/srv/repos/private"],
)
@pytest.mark.parametrize("field", ["target_alias", "endpoint_alias"])
def test_security_absolute_target_and_endpoint_aliases_are_rejected(
    field: str, absolute_path: str
) -> None:
    manifest = _manifest()
    if field == "target_alias":
        manifest["boundary"]["scope_units"][0][field] = absolute_path
    else:
        manifest["sources"][0][field] = absolute_path

    errors = validate_manifest(manifest)

    assert any(f"{field} must not be an absolute path" in error for error in errors)


@pytest.mark.parametrize(
    "classified_at",
    ["2026-08-30T15:33:59Z", "2026-08-30T15:36:01Z"],
)
def test_security_assessment_classification_is_inside_envelope_interval(
    classified_at: str,
) -> None:
    manifest = _manifest()
    attempt = _attempt(manifest)
    attempt["epistemic_assessments"][0]["classified_at"] = classified_at
    _rehash(attempt)

    errors = validate_envelope(attempt, manifest)

    assert any("observed_at <= classified_at <= recorded_at" in error for error in errors)


def test_security_known_known_basis_must_be_causally_prior() -> None:
    manifest = _manifest()
    attempt = _attempt(manifest)
    assessed_claim = _claim(attempt)
    future_basis = _claim_for(
        sequence=2,
        previous_envelope=assessed_claim,
        attempt_envelope=attempt,
        claim_id="claim-main-ref-future-basis",
    )
    assessment = assessed_claim["epistemic_assessments"][0]
    assessment.update(
        quadrant="known_known",
        evidence_state="verified_current",
        basis_refs=[f"envelope:{future_basis['envelope_id']}"],
    )
    assessment.pop("next_action")
    _rehash(assessed_claim)
    future_basis["previous_digest"] = assessed_claim["integrity"]["envelope_sha256"]
    _rehash(future_basis)
    summary = _summary_for(
        manifest,
        sequence=3,
        previous_envelope=future_basis,
        attempts=[attempt],
    )

    errors = validate_ledger(manifest, [attempt, assessed_claim, future_basis, summary])

    assert any("basis must be causally prior" in error for error in errors)


def test_security_known_known_basis_must_exist_by_classification_time() -> None:
    manifest = _manifest()
    attempt = _attempt(manifest)
    basis = _claim(attempt)
    basis["recorded_at"] = "2026-08-30T15:37:00Z"
    _rehash(basis)
    assessed_claim = _claim_for(
        sequence=2,
        previous_envelope=basis,
        attempt_envelope=attempt,
        claim_id="claim-main-ref-assessed",
    )
    assessment = assessed_claim["epistemic_assessments"][0]
    assessment.update(
        quadrant="known_known",
        evidence_state="verified_current",
        basis_refs=[f"envelope:{basis['envelope_id']}"],
    )
    assessment.pop("next_action")
    _rehash(assessed_claim)
    summary = _summary_for(
        manifest,
        sequence=3,
        previous_envelope=assessed_claim,
        attempts=[attempt],
    )

    errors = validate_ledger(manifest, [attempt, basis, assessed_claim, summary])

    assert any("recorded no later than classified_at" in error for error in errors)


def test_security_run_summary_cannot_be_assessment_basis() -> None:
    manifest = _manifest()
    attempt = _attempt(manifest)
    claim = _claim(attempt)
    summary_id = "00000000-0000-4000-8000-000000000003"
    assessment = claim["epistemic_assessments"][0]
    assessment.update(
        quadrant="known_known",
        evidence_state="verified_current",
        basis_refs=[f"envelope:{summary_id}"],
    )
    assessment.pop("next_action")
    _rehash(claim)
    summary = _summary_for(
        manifest,
        sequence=2,
        previous_envelope=claim,
        attempts=[attempt],
    )
    assert summary["envelope_id"] == summary_id

    errors = validate_ledger(manifest, [attempt, claim, summary])

    assert any("run_summary cannot be assessment basis" in error for error in errors)


def test_security_claim_basis_must_be_semantically_relevant() -> None:
    manifest = _manifest()
    attempt = _attempt(manifest)
    unrelated_basis = _claim(attempt)
    assessed_claim = _claim_for(
        sequence=2,
        previous_envelope=unrelated_basis,
        attempt_envelope=attempt,
        claim_id="claim-ref-count",
        subject=_subject(selector=None),
        predicate="git.refs.count",
        object_value=attempt["payload"]["result_count"],
    )
    assessment = assessed_claim["epistemic_assessments"][0]
    assessment.update(
        quadrant="known_known",
        evidence_state="verified_current",
        basis_refs=[f"envelope:{unrelated_basis['envelope_id']}"],
    )
    assessment.pop("next_action")
    _rehash(assessed_claim)
    summary = _summary_for(
        manifest,
        sequence=3,
        previous_envelope=assessed_claim,
        attempts=[attempt],
    )

    errors = validate_ledger(manifest, [attempt, unrelated_basis, assessed_claim, summary])

    assert any("basis is not semantically relevant" in error for error in errors)


def test_security_claim_must_follow_its_referenced_attempt() -> None:
    manifest = _manifest()
    attempt = _attempt(manifest)
    claim = _claim(attempt)
    summary = _summary(claim)
    reordered = [claim, attempt, summary]
    _rechain(manifest, reordered)

    errors = validate_ledger(manifest, reordered)

    assert any("claim must follow its referenced attempt" in error for error in errors)


def test_security_claim_requires_exact_selector_observation() -> None:
    manifest = _manifest()
    manifest["boundary"]["scope_units"][0]["inclusions"].append("refs/heads/dev")
    attempt = _attempt(manifest)
    attempt["payload"].update(
        result_count=1,
        observations=[_observation(subject=_subject(selector="refs/heads/main"))],
    )
    _rehash(attempt)
    main_claim = _claim_for(
        sequence=1,
        previous_envelope=attempt,
        attempt_envelope=attempt,
        claim_id="claim-main-ref-present",
        subject=_subject(selector="refs/heads/main"),
    )
    dev_claim = _claim_for(
        sequence=2,
        previous_envelope=main_claim,
        attempt_envelope=attempt,
        claim_id="claim-dev-ref-present",
        subject=_subject(selector="refs/heads/dev"),
    )
    summary = _summary_for(
        manifest,
        sequence=3,
        previous_envelope=dev_claim,
        attempts=[attempt],
    )

    errors = validate_ledger(manifest, [attempt, main_claim, dev_claim, summary])

    assert any(
        "claim fact is not present in referenced attempt observations" in error
        for error in errors
    )


def test_security_state_claim_must_match_attempt_observation() -> None:
    manifest = _manifest()
    _set_manifest_capability(manifest, "forge.protection")
    attempt = _attempt(manifest)
    attempt["payload"].update(
        capability="forge.protection",
        result_count=1,
        observations=[
            _observation(
                subject=_subject(selector=None),
                predicate="git.protection.enabled",
                object_value=True,
            )
        ],
    )
    _rehash(attempt)
    claim = _claim_for(
        sequence=1,
        previous_envelope=attempt,
        attempt_envelope=attempt,
        claim_id="claim-protection-disabled",
        subject=_subject(selector=None),
        predicate="git.protection.enabled",
        object_value=False,
    )

    errors = validate_ledger(manifest, [attempt, claim], finalized=False)

    assert any(
        "claim fact is not present in referenced attempt observations" in error
        for error in errors
    )


def test_security_attempt_rejects_conflicting_observations() -> None:
    manifest = _manifest()
    attempt = _attempt(manifest)
    attempt["payload"]["observations"] = [
        _observation(object_value=True),
        _observation(object_value=False),
    ]
    _rehash(attempt)

    errors = validate_envelope(attempt, manifest)

    assert any("conflicting attempt observations" in error for error in errors)


def test_security_attempt_rejects_duplicate_observations() -> None:
    manifest = _manifest()
    attempt = _attempt(manifest)
    attempt["payload"]["observations"].append(
        deepcopy(attempt["payload"]["observations"][0])
    )
    _rehash(attempt)

    errors = validate_envelope(attempt, manifest)

    assert any("duplicate attempt observation" in error for error in errors)


def test_security_attempt_observation_is_bound_to_scope_and_capability() -> None:
    manifest = _manifest()
    attempt = _attempt(manifest)
    attempt["payload"]["observations"][0]["subject"]["target_alias"] = "repo:other"
    attempt["payload"]["observations"][1].update(
        predicate="git.remotes.count",
    )
    _rehash(attempt)

    errors = validate_envelope(attempt, manifest)

    assert any("attempt observations[0] subject target_alias" in error for error in errors)
    assert any("predicate is not supported by the attempt capability" in error for error in errors)


def test_security_failed_attempt_cannot_carry_observations() -> None:
    manifest = _manifest()
    attempt = _attempt(manifest)
    attempt["payload"].update(
        status="failed",
        reason="source_error",
        result_count=0,
        enumeration_exhausted=False,
    )
    _rehash(attempt)

    errors = validate_envelope(attempt, manifest)

    assert any("failed attempt cannot contain factual observations" in error for error in errors)


def test_security_attempt_observation_count_matches_positive_selectors() -> None:
    manifest = _manifest()
    attempt = _attempt(manifest)
    attempt["payload"].update(
        result_count=2,
        observations=[_observation(object_value=True)],
    )
    _rehash(attempt)

    errors = validate_envelope(attempt, manifest)

    assert any("observed object identities must equal result_count" in error for error in errors)


def test_security_claim_metadata_cannot_mint_collector_independence() -> None:
    manifest, envelopes = _two_source_corroborated_ledger(
        second_domain="host:node-secondary",
        second_collector="collector-a",
    )
    envelopes[3]["provenance"]["collector_name"] = "collector-b"
    _rechain(manifest, envelopes)

    errors = validate_ledger(manifest, envelopes)

    assert any("lacks the required independent collectors" in error for error in errors)


def test_security_known_known_rejects_self_basis() -> None:
    manifest = _manifest()
    attempt = _attempt(manifest)
    claim = _claim(attempt)
    assessment = claim["epistemic_assessments"][0]
    assessment.update(
        quadrant="known_known",
        evidence_state="verified_current",
        basis_refs=[f"envelope:{claim['envelope_id']}"],
    )
    assessment.pop("next_action")
    _rehash(claim)

    errors = validate_ledger(manifest, [attempt, claim], finalized=False)

    assert any("assessment basis must be causally prior" in error for error in errors)


def test_security_non_known_known_basis_must_resolve_and_be_prior() -> None:
    manifest = _manifest()
    attempt = _attempt(manifest)
    claim = _claim(attempt)
    future_summary_id = "00000000-0000-4000-8000-000000000003"
    claim["epistemic_assessments"][0]["basis_refs"] = [
        f"envelope:{future_summary_id}"
    ]
    _rehash(claim)
    summary = _summary_for(
        manifest,
        sequence=2,
        previous_envelope=claim,
        attempts=[attempt],
    )
    assert summary["envelope_id"] == future_summary_id

    errors = validate_ledger(manifest, [attempt, claim, summary])

    assert any("assessment basis must be causally prior" in error for error in errors)
    assert any("run_summary cannot be assessment basis" in error for error in errors)


def test_security_conflicting_attempt_results_cannot_corroborate_known_known() -> None:
    manifest = _manifest()
    manifest["corroboration_policy"].update(
        minimum_independent_sources=2,
        minimum_independent_collectors=2,
    )
    _add_source(manifest, independence_domain="host:node-secondary")
    _add_source(
        manifest,
        source_id="source-local-three",
        attempt_id="attempt-repo-refs-three",
        endpoint_alias="local:repo-oss-tertiary",
        independence_domain="host:node-tertiary",
    )
    manifest_digest = canonical_sha256(manifest)
    first = _attempt_for(
        manifest,
        sequence=0,
        previous_digest=manifest_digest,
        attempt_id="attempt-repo-refs",
        source_id="source-local-git",
        collector_name="collector-a",
        host="node-primary",
        result_count=1,
    )
    conflicting = _attempt_for(
        manifest,
        sequence=1,
        previous_digest=first["integrity"]["envelope_sha256"],
        attempt_id="attempt-repo-refs-two",
        source_id="source-local-two",
        collector_name="collector-b",
        host="node-secondary",
        result_count=0,
    )
    assessed = _attempt_for(
        manifest,
        sequence=2,
        previous_digest=conflicting["integrity"]["envelope_sha256"],
        attempt_id="attempt-repo-refs-three",
        source_id="source-local-three",
        collector_name="collector-c",
        host="node-tertiary",
        result_count=1,
    )
    assessment = assessed["epistemic_assessments"][0]
    assessment.update(
        quadrant="known_known",
        evidence_state="verified_current",
        basis_refs=[
            f"envelope:{first['envelope_id']}",
            f"envelope:{conflicting['envelope_id']}",
        ],
    )
    assessment.pop("next_action")
    _rehash(assessed)

    errors = validate_ledger(manifest, [first, conflicting, assessed], finalized=False)

    assert any("attempt basis does not agree with assessed observation" in error for error in errors)


def test_security_manifest_rejects_overlapping_inclusion_and_exclusion() -> None:
    manifest = _manifest()
    manifest["boundary"]["scope_units"][0]["exclusions"] = [
        {"selector": "refs/heads/main", "reason": "operator excluded"}
    ]

    errors = validate_manifest(manifest)

    assert any("selector cannot be both included and excluded" in error for error in errors)


def test_security_manifest_must_exist_before_collection_starts() -> None:
    manifest = _manifest()
    manifest["created_at"] = "2026-08-30T15:30:01Z"

    errors = validate_manifest(manifest)

    assert any("created_at must be no later than collection_window.not_before" in error for error in errors)


@pytest.mark.parametrize(
    "alias",
    [r"  C:\Private\private-repo", r"  \\server\share\private-repo", "  /srv/repos/private"],
)
@pytest.mark.parametrize("field", ["target_alias", "endpoint_alias"])
def test_security_whitespace_cannot_hide_absolute_alias(field: str, alias: str) -> None:
    manifest = _manifest()
    if field == "target_alias":
        manifest["boundary"]["scope_units"][0][field] = alias
    else:
        manifest["sources"][0][field] = alias

    errors = validate_manifest(manifest)

    assert any(f"{field} must not be an absolute path" in error for error in errors)


def test_security_trailing_malformed_object_is_reported_without_crashing() -> None:
    manifest = _manifest()
    attempt = _attempt(manifest)
    claim = _claim(attempt)
    summary = _summary(claim)

    errors = validate_ledger(manifest, [attempt, claim, summary, {"payload": []}])

    assert any("envelopes[3]" in error for error in errors)


def test_security_fresh_claim_cannot_launder_stale_collection() -> None:
    manifest = _manifest()
    manifest["created_at"] = "2026-08-30T12:59:00Z"
    manifest["collection_window"]["not_before"] = "2026-08-30T13:00:00Z"
    attempt = _attempt(manifest)
    attempt.update(
        started_at="2026-08-30T13:59:00Z",
        observed_at="2026-08-30T14:00:00Z",
        recorded_at="2026-08-30T14:01:00Z",
    )
    attempt["native_evidence"]["captured_at"] = "2026-08-30T14:00:00Z"
    attempt["epistemic_assessments"][0]["classified_at"] = "2026-08-30T14:01:00Z"
    _rehash(attempt)
    fresh_basis = _claim_for(
        sequence=1,
        previous_envelope=attempt,
        attempt_envelope=attempt,
        claim_id="claim-fresh-wrapper",
    )
    assessed = _claim_for(
        sequence=2,
        previous_envelope=fresh_basis,
        attempt_envelope=attempt,
        claim_id="claim-assessed-fresh",
    )
    assessment = assessed["epistemic_assessments"][0]
    assessment.update(
        quadrant="known_known",
        evidence_state="verified_current",
        basis_refs=[f"envelope:{fresh_basis['envelope_id']}"],
    )
    assessment.pop("next_action")
    _rehash(assessed)

    errors = validate_ledger(
        manifest,
        [attempt, fresh_basis, assessed],
        finalized=False,
    )

    assert any("collection attempt is outside the freshness policy" in error for error in errors)


def test_security_ledger_recorded_at_is_nondecreasing() -> None:
    manifest = _manifest()
    attempt = _attempt(manifest)
    claim = _claim(attempt)
    summary = _summary(claim)
    summary.update(
        started_at="2026-08-30T15:30:00Z",
        observed_at="2026-08-30T15:31:00Z",
        recorded_at="2026-08-30T15:32:00Z",
    )
    summary["native_evidence"]["captured_at"] = "2026-08-30T15:31:00Z"
    summary["epistemic_assessments"][0]["classified_at"] = "2026-08-30T15:32:00Z"
    _rehash(summary)

    errors = validate_ledger(manifest, [attempt, claim, summary])

    assert any("ledger recorded_at must be nondecreasing" in error for error in errors)


def test_security_known_known_rejects_prior_conflicting_fact() -> None:
    manifest = _manifest()
    manifest["corroboration_policy"].update(
        minimum_independent_sources=2,
        minimum_independent_collectors=2,
    )
    _add_source(manifest, independence_domain="host:node-secondary")
    _add_source(
        manifest,
        source_id="source-local-three",
        attempt_id="attempt-repo-refs-three",
        endpoint_alias="local:repo-oss-tertiary",
        independence_domain="host:node-tertiary",
    )
    digest = canonical_sha256(manifest)
    first = _attempt_for(
        manifest,
        sequence=0,
        previous_digest=digest,
        attempt_id="attempt-repo-refs",
        source_id="source-local-git",
        collector_name="collector-a",
        host="node-primary",
        result_count=1,
    )
    second = _attempt_for(
        manifest,
        sequence=1,
        previous_digest=first["integrity"]["envelope_sha256"],
        attempt_id="attempt-repo-refs-two",
        source_id="source-local-two",
        collector_name="collector-b",
        host="node-secondary",
        result_count=1,
    )
    dissent = _attempt_for(
        manifest,
        sequence=2,
        previous_digest=second["integrity"]["envelope_sha256"],
        attempt_id="attempt-repo-refs-three",
        source_id="source-local-three",
        collector_name="collector-c",
        host="node-tertiary",
        result_count=0,
    )
    first_claim = _claim_for(
        sequence=3,
        previous_envelope=dissent,
        attempt_envelope=first,
        claim_id="claim-first-true",
    )
    second_claim = _claim_for(
        sequence=4,
        previous_envelope=first_claim,
        attempt_envelope=second,
        claim_id="claim-second-true",
    )
    dissent_claim = _claim_for(
        sequence=5,
        previous_envelope=second_claim,
        attempt_envelope=dissent,
        claim_id="claim-third-false",
        object_value=False,
    )
    assessed = _claim_for(
        sequence=6,
        previous_envelope=dissent_claim,
        attempt_envelope=first,
        claim_id="claim-assessed-true",
    )
    assessment = assessed["epistemic_assessments"][0]
    assessment.update(
        quadrant="known_known",
        evidence_state="verified_current",
        basis_refs=[
            f"envelope:{first_claim['envelope_id']}",
            f"envelope:{second_claim['envelope_id']}",
        ],
    )
    assessment.pop("next_action")
    _rehash(assessed)

    errors = validate_ledger(
        manifest,
        [
            first,
            second,
            dissent,
            first_claim,
            second_claim,
            dissent_claim,
            assessed,
        ],
        finalized=False,
    )

    assert any("known_known has unresolved conflicting evidence" in error for error in errors)


def test_security_declaration_source_cannot_corroborate_known_known() -> None:
    manifest, envelopes = _two_source_corroborated_ledger(
        second_domain="host:node-secondary",
        second_collector="collector-b",
    )
    manifest["sources"][1].update(kind="manual", authority_role="declaration")
    manifest["corroboration_policy"]["minimum_independent_sources"] = 1
    _rebind_manifest(manifest, envelopes)

    errors = validate_ledger(manifest, envelopes)

    assert any(
        "known_known basis source is not eligible observational authority" in error
        for error in errors
    )


def test_security_selector_absence_uses_exact_observation_not_aggregate_zero() -> None:
    manifest = _manifest()
    manifest["boundary"]["scope_units"][0]["inclusions"].append("refs/heads/dev")
    attempt = _attempt(manifest)
    attempt["payload"]["observations"] = [
        _observation(subject=_subject(selector="refs/heads/main"), object_value=True),
        _observation(subject=_subject(selector="refs/heads/dev"), object_value=False),
        _observation(
            subject=_subject(selector=None),
            predicate="git.refs.count",
            object_value=1,
        ),
    ]
    _rehash(attempt)
    claim = _claim_for(
        sequence=1,
        previous_envelope=attempt,
        attempt_envelope=attempt,
        claim_id="claim-dev-ref-absent",
        subject=_subject(selector="refs/heads/dev"),
        object_value=False,
    )

    assert validate_ledger(manifest, [attempt, claim], finalized=False) == []


def test_security_duplicate_observer_assessment_is_rejected() -> None:
    manifest = _manifest()
    attempt = _attempt(manifest)
    attempt["epistemic_assessments"].append(
        deepcopy(attempt["epistemic_assessments"][0])
    )
    _rehash(attempt)

    errors = validate_envelope(attempt, manifest)

    assert any("duplicate assessment observer_id" in error for error in errors)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("target_alias", "repo:oss "),
        ("target_alias", "Repo:oss"),
        ("target_alias", "repo:oss/"),
        ("target_alias", "repo:oss."),
        ("endpoint_alias", "local:repo-oss "),
        ("endpoint_alias", "Local:repo-oss"),
        ("endpoint_alias", "local:repo-oss/"),
        ("endpoint_alias", "local:repo-oss."),
        ("independence_domain", "host:node-primary "),
        ("independence_domain", "Host:node-primary"),
        ("independence_domain", "host:node-primary/"),
        ("independence_domain", "host::node-primary"),
    ],
)
def test_security_manifest_identifiers_require_canonical_form(
    field: str,
    value: str,
) -> None:
    manifest = _manifest()
    if field == "target_alias":
        manifest["boundary"]["scope_units"][0][field] = value
    else:
        manifest["sources"][0][field] = value

    errors = validate_manifest(manifest)

    assert any(f"{field} must be a canonical opaque alias" in error for error in errors)


@pytest.mark.parametrize(
    "collector_name",
    ["collector-a ", "Collector-a", "collector-a/", "collector-a."],
)
def test_security_collector_name_requires_canonical_form(collector_name: str) -> None:
    manifest = _manifest()
    attempt = _attempt(manifest)
    attempt["provenance"]["collector_name"] = collector_name
    _rehash(attempt)

    errors = validate_envelope(attempt, manifest)

    assert any("collector_name must be a canonical opaque alias" in error for error in errors)


@pytest.mark.parametrize(
    "target_alias",
    [
        ":".join(
            (
                "https://user",
                "".join(("pass", "word")) + "@example.invalid/private",
            )
        ),
        "file:///tmp/private",
        "https:/example.invalid/private",
        "https:example.invalid/private",
        "ssh:git.example.invalid/repo",
        "repo:/srv/repos/private",
        "repo:c:/private/private",
        "repo:../private",
        r"C:private-repo",
        "repo:oss\x00hidden",
    ],
)
def test_security_target_alias_rejects_uri_path_and_control_data(
    target_alias: str,
) -> None:
    manifest = _manifest()
    manifest["boundary"]["scope_units"][0]["target_alias"] = target_alias

    errors = validate_manifest(manifest)

    assert any("target_alias must be a canonical opaque alias" in error for error in errors)


def test_security_target_alias_namespace_matches_target_kind() -> None:
    manifest = _manifest()
    manifest["boundary"]["scope_units"][0]["target_alias"] = "host:node-primary"

    errors = validate_manifest(manifest)

    assert any("target_alias namespace must match target_kind" in error for error in errors)
