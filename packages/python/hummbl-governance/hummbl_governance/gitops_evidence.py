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

"""Validation helpers for the bounded GitOps evidence registry pilot.

The contract is advisory only. Validation establishes conformance and internal
integrity; it does not establish that a collector or an upstream source is
honest, and it grants no authority to mutate Git or forge state.
"""

from __future__ import annotations

import hashlib
import json
import re
from copy import deepcopy
from datetime import datetime
from importlib.resources import files
from typing import Any

from hummbl_governance.schema_validator import SchemaValidator

_SCHEMA_NAME = "gitops_evidence_registry.v0.1.schema.json"
_CONTENT_ADDRESS_PATTERN = re.compile(
    r"^sha256/(?P<shard>[a-f0-9]{2})/(?P<digest>[a-f0-9]{64})"
    r"\.(?P<extension>json|jsonl|txt|bin)$"
)
_UTC_TIMESTAMP_PATTERN = re.compile(
    r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}"
    r"(?:\.[0-9]{1,6})?Z$"
)
_WINDOWS_ABSOLUTE_PATH_PATTERN = re.compile(r"^[A-Za-z]:[\\/]")
_WINDOWS_DRIVE_RELATIVE_PATH_PATTERN = re.compile(r"^[A-Za-z]:(?![\\/])")
_NAMESPACED_ALIAS_PATTERN = re.compile(
    r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*:[a-z0-9]+(?:-[a-z0-9]+)*$"
)
_COLLECTOR_NAME_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_RESERVED_URI_NAMESPACES = frozenset(
    {"file", "ftp", "git", "http", "https", "sftp", "ssh"}
)
_TARGET_NAMESPACE_BY_KIND = {
    "host": "host",
    "forge_account": "forge",
    "repository": "repo",
    "policy_store": "policy",
}
_BARE_BOUNDARY_WORDS = {"*", "**", "all", "everything"}
_FORBIDDEN_DATA_CLASSES = frozenset(
    {
        "authorization_header",
        "cookie",
        "credential_value",
        "environment_value",
        "private_key",
        "secret_derived_hash",
        "url_userinfo",
    }
)
_MEDIA_TYPE_BY_EXTENSION = {
    "json": "application/json",
    "jsonl": "application/jsonl",
    "txt": "text/plain",
    "bin": "application/octet-stream",
}
_PREDICATE_CAPABILITIES = {
    "git.repository.exists": "git.repository",
    "git.ref.exists": "git.refs",
    "git.refs.count": "git.refs",
    "git.remote.exists": "git.remotes",
    "git.remotes.count": "git.remotes",
    "git.worktree.exists": "git.worktrees",
    "git.worktrees.count": "git.worktrees",
    "git.stash.exists": "git.stashes",
    "git.stashes.count": "git.stashes",
    "git.workflow.exists": "forge.workflows",
    "git.protection.enabled": "forge.protection",
    "git.runner.online": "ci.runners",
    "git.mirror.current": "git.mirror",
}
_BOOLEAN_EXISTENCE_PREDICATES = frozenset(
    predicate
    for predicate in _PREDICATE_CAPABILITIES
    if predicate.endswith(".exists")
)
_COUNT_PREDICATES = frozenset(
    predicate for predicate in _PREDICATE_CAPABILITIES if predicate.endswith(".count")
)
_BOOLEAN_STATE_PREDICATES = (
    frozenset(_PREDICATE_CAPABILITIES)
    - _BOOLEAN_EXISTENCE_PREDICATES
    - _COUNT_PREDICATES
)
_BOOLEAN_PREDICATES = _BOOLEAN_EXISTENCE_PREDICATES | _BOOLEAN_STATE_PREDICATES
_SELECTOR_REQUIRED_PREDICATES = (
    _BOOLEAN_EXISTENCE_PREDICATES - {"git.repository.exists"}
) | _BOOLEAN_STATE_PREDICATES
_MAX_JCS_INTEGER = (1 << 53) - 1

__all__ = [
    "canonical_sha256",
    "claim_fingerprint",
    "envelope_sha256",
    "loads_strict_json",
    "semantic_claim_key",
    "validate_envelope",
    "validate_ledger",
    "validate_manifest",
]


def _reject_duplicate_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON object key: {key!r}")
        result[key] = value
    return result


def _parse_json_integer(raw: str) -> int:
    value = int(raw)
    if abs(value) > _MAX_JCS_INTEGER:
        raise ValueError("JSON integer exceeds the interoperable JCS range")
    return value


def _reject_json_number(raw: str) -> Any:
    raise ValueError(f"floating-point JSON numbers are not permitted: {raw}")


def loads_strict_json(document: str | bytes) -> Any:
    """Parse UTF-8 JSON while rejecting duplicate keys and lossy numbers.

    Contract records use integers only. Raw JSON must pass through this loader
    before validation so duplicate object names cannot be hidden by a normal
    ``json.loads`` last-value-wins conversion.
    """
    if isinstance(document, bytes):
        text = document.decode("utf-8", errors="strict")
    elif isinstance(document, str):
        text = document
    else:
        raise TypeError("JSON input must be str or UTF-8 bytes")
    loaded = json.loads(
        text,
        object_pairs_hook=_reject_duplicate_pairs,
        parse_int=_parse_json_integer,
        parse_float=_reject_json_number,
        parse_constant=_reject_json_number,
    )
    _reject_lone_surrogates(loaded)
    return loaded


def _reject_lone_surrogates(value: Any, path: str = "$") -> None:
    """Reject strings that cannot be represented as UTF-8 Unicode scalars."""
    if isinstance(value, str):
        try:
            value.encode("utf-8", errors="strict")
        except UnicodeEncodeError as exc:
            raise ValueError(f"{path} contains a lone Unicode surrogate") from exc
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            _reject_lone_surrogates(item, f"{path}[{index}]")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            _reject_lone_surrogates(key, f"{path}.<key>")
            _reject_lone_surrogates(item, f"{path}.{key}")


def _canonical_json(value: Any) -> str:
    """Serialize the contract's integer-only JSON profile using JCS ordering."""
    if value is None:
        return "null"
    if type(value) is bool:
        return "true" if value else "false"
    if type(value) is int:
        if abs(value) > _MAX_JCS_INTEGER:
            raise ValueError("integer exceeds the interoperable JCS range")
        return str(value)
    if isinstance(value, float):
        raise ValueError("canonical contract JSON forbids floating-point numbers")
    if isinstance(value, str):
        try:
            value.encode("utf-8", errors="strict")
        except UnicodeEncodeError as exc:
            raise ValueError("canonical contract JSON forbids lone Unicode surrogates") from exc
        return json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    if isinstance(value, list):
        return "[" + ",".join(_canonical_json(item) for item in value) + "]"
    if isinstance(value, dict):
        if not all(isinstance(key, str) for key in value):
            raise TypeError("canonical JSON object keys must be strings")
        try:
            ordered_keys = sorted(value, key=lambda key: key.encode("utf-16-be"))
        except UnicodeEncodeError as exc:
            raise ValueError("canonical contract JSON forbids lone Unicode surrogates") from exc
        members = (
            f"{_canonical_json(key)}:{_canonical_json(value[key])}"
            for key in ordered_keys
        )
        return "{" + ",".join(members) + "}"
    raise TypeError(f"value of type {type(value).__name__} is not JSON-compatible")


def canonical_sha256(value: Any) -> str:
    """Return SHA-256 over byte-preserving, integer-only canonical JSON."""
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def envelope_sha256(envelope: dict[str, Any]) -> str:
    """Hash an envelope while excluding its self-referential digest field."""
    unsigned = deepcopy(envelope)
    integrity = unsigned.get("integrity")
    if isinstance(integrity, dict):
        integrity.pop("envelope_sha256", None)
    return canonical_sha256(unsigned)


def claim_fingerprint(payload: dict[str, Any]) -> str:
    """Hash the complete claim payload except its self-referential fingerprint."""
    unsigned = deepcopy(payload)
    unsigned.pop("claim_fingerprint", None)
    return canonical_sha256(unsigned)


def semantic_claim_key(payload: dict[str, Any]) -> str:
    """Hash only the normalized fact identity, excluding record linkage."""
    fact = {
        "subject": deepcopy(payload["subject"]),
        "predicate": payload["predicate"],
        "object": deepcopy(payload["object"]),
        "normalization_profile": payload["normalization_profile"],
    }
    return canonical_sha256(fact)


def _load_schema() -> dict[str, Any]:
    resource = files("hummbl_governance").joinpath("data", _SCHEMA_NAME)
    loaded = loads_strict_json(resource.read_bytes())
    if not isinstance(loaded, dict):
        raise ValueError("GitOps evidence schema root must be an object")
    return loaded


def _record_schema(definition: str) -> dict[str, Any]:
    schema = _load_schema()
    return {
        "$schema": schema["$schema"],
        "$defs": schema["$defs"],
        "$ref": f"#/$defs/{definition}",
    }


def _parse_utc(value: Any) -> datetime:
    if not isinstance(value, str) or not _UTC_TIMESTAMP_PATTERN.fullmatch(value):
        raise ValueError("timestamp must be an RFC 3339 UTC string")
    return datetime.fromisoformat(value.removesuffix("Z") + "+00:00")


def _duplicates(values: list[str]) -> set[str]:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for value in values:
        if value in seen:
            duplicates.add(value)
        seen.add(value)
    return duplicates


def _is_wildcard(value: str) -> bool:
    normalized = value.strip().lower()
    return normalized in _BARE_BOUNDARY_WORDS or "*" in normalized


def _is_absolute_path(value: str) -> bool:
    """Recognize POSIX, Windows drive-rooted, and UNC/rooted paths."""
    value = value.strip()
    return (
        value.startswith(("/", "\\"))
        or _WINDOWS_ABSOLUTE_PATH_PATTERN.match(value) is not None
    )


def _canonical_identifier(value: str) -> str:
    return value.strip().casefold()


def _opaque_alias_error(
    value: Any,
    *,
    maximum_length: int = 256,
    namespaced: bool = True,
) -> bool:
    """Return whether a public identifier could hide a path, URI, or variant."""
    if not isinstance(value, str):
        return False
    canonical = _canonical_identifier(value)
    pattern = _NAMESPACED_ALIAS_PATTERN if namespaced else _COLLECTOR_NAME_PATTERN
    namespace = value.partition(":")[0] if namespaced else ""
    return (
        value != canonical
        or len(value) > maximum_length
        or pattern.fullmatch(value) is None
        or namespace in _RESERVED_URI_NAMESPACES
        or _is_absolute_path(value)
        or _WINDOWS_DRIVE_RELATIVE_PATH_PATTERN.match(value) is not None
        or "://" in value
        or value.startswith("file:")
        or any(character in value for character in ("@", "?", "#"))
    )


def _canonical_input_error(value: Any) -> str | None:
    """Return a fail-closed error for a non-canonical JSON-shaped value."""
    try:
        _canonical_json(value)
    except (TypeError, ValueError, OverflowError, RecursionError) as exc:
        return str(exc)
    return None


def _boundary_strings(manifest: dict[str, Any]) -> list[tuple[str, str]]:
    found: list[tuple[str, str]] = []
    boundary = manifest["boundary"]
    for index, scope in enumerate(boundary["scope_units"]):
        found.append((f"scope_units[{index}].target_alias", scope["target_alias"]))
        for field in ("capabilities", "inclusions"):
            for item_index, value in enumerate(scope[field]):
                found.append((f"scope_units[{index}].{field}[{item_index}]", value))
        for item_index, exclusion in enumerate(scope["exclusions"]):
            found.append(
                (
                    f"scope_units[{index}].exclusions[{item_index}].selector",
                    exclusion["selector"],
                )
            )
    return found


def _manifest_declaration_errors(manifest: Any) -> list[str]:
    """Safely check high-risk declarations even when the schema is invalid."""
    if not isinstance(manifest, dict):
        return []
    errors: list[str] = []
    boundary = manifest.get("boundary")
    if isinstance(boundary, dict):
        scopes = boundary.get("scope_units")
        if isinstance(scopes, list):
            for index, scope in enumerate(scopes):
                if not isinstance(scope, dict):
                    continue
                target_alias = scope.get("target_alias")
                if isinstance(target_alias, str):
                    if _opaque_alias_error(target_alias):
                        errors.append(
                            f"scope_units[{index}].target_alias must be a canonical "
                            "opaque alias"
                        )
                    if _is_absolute_path(target_alias):
                        errors.append(
                            f"scope_units[{index}].target_alias must not be an "
                            "absolute path"
                        )
    policy = manifest.get("sanitization_policy")
    if isinstance(policy, dict):
        classes = policy.get("forbidden_data_classes")
        if not (
            isinstance(classes, list)
            and all(isinstance(item, str) for item in classes)
            and len(classes) == len(_FORBIDDEN_DATA_CLASSES)
            and set(classes) == _FORBIDDEN_DATA_CLASSES
        ):
            errors.append(
                "forbidden_data_classes must contain the complete required set exactly once"
            )
    sources = manifest.get("sources")
    if isinstance(sources, list):
        for index, source in enumerate(sources):
            if not isinstance(source, dict):
                continue
            credential_ref = source.get("credential_ref")
            if credential_ref is not None and not (
                isinstance(credential_ref, str)
                and re.fullmatch(r"credential:[a-z0-9][a-z0-9._/-]{0,255}", credential_ref)
            ):
                errors.append(
                    f"sources[{index}].credential_ref must be an opaque credential: alias"
                )
            endpoint_alias = source.get("endpoint_alias")
            if isinstance(endpoint_alias, str):
                if _opaque_alias_error(endpoint_alias):
                    errors.append(
                        f"sources[{index}].endpoint_alias must be a canonical "
                        "opaque alias"
                    )
                if _is_absolute_path(endpoint_alias):
                    errors.append(
                        f"sources[{index}].endpoint_alias must not be an absolute path"
                    )
            independence_domain = source.get("independence_domain")
            if isinstance(independence_domain, str) and _opaque_alias_error(
                independence_domain
            ):
                errors.append(
                    f"sources[{index}].independence_domain must be a canonical "
                    "opaque alias"
                )
    return errors


def _timestamp_error(label: str, value: Any) -> str | None:
    try:
        _parse_utc(value)
    except (TypeError, ValueError, OverflowError):
        return f"{label} is not a valid UTC timestamp"
    return None


def _expected_attempt_tuples(manifest: dict[str, Any]) -> set[tuple[str, str, str]]:
    sources_by_scope: dict[str, list[str]] = {}
    for source in manifest["sources"]:
        sources_by_scope.setdefault(source["scope_id"], []).append(source["source_id"])
    return {
        (scope["scope_id"], source_id, capability)
        for scope in manifest["boundary"]["scope_units"]
        for source_id in sources_by_scope.get(scope["scope_id"], [])
        for capability in scope["capabilities"]
    }


def validate_manifest(manifest: Any) -> list[str]:
    """Validate one bounded observation manifest."""
    canonical_error = _canonical_input_error(manifest)
    if canonical_error:
        return [f"canonical JSON: {canonical_error}"]
    valid, structural = SchemaValidator.validate_dict(
        manifest, _record_schema("ObservationManifest")
    )
    errors = [f"schema: {error}" for error in structural]
    errors.extend(_manifest_declaration_errors(manifest))
    if not valid:
        if isinstance(manifest, dict):
            created_at_error = _timestamp_error("created_at", manifest.get("created_at"))
            if created_at_error:
                errors.append(created_at_error)
        return errors

    observers = manifest["observers"]
    for observer_id in sorted(_duplicates([item["observer_id"] for item in observers])):
        errors.append(f"duplicate observer_id: {observer_id}")

    scopes = manifest["boundary"]["scope_units"]
    scope_ids = [item["scope_id"] for item in scopes]
    for scope_id in sorted(_duplicates(scope_ids)):
        errors.append(f"duplicate scope_id: {scope_id}")
    scope_id_set = set(scope_ids)
    capabilities_by_scope = {
        scope["scope_id"]: set(scope["capabilities"]) for scope in scopes
    }
    for scope in scopes:
        expected_namespace = _TARGET_NAMESPACE_BY_KIND[scope["target_kind"]]
        actual_namespace = scope["target_alias"].partition(":")[0]
        if actual_namespace != expected_namespace:
            errors.append(
                f"scope {scope['scope_id']} target_alias namespace must match "
                "target_kind"
            )
        for capability in sorted(_duplicates(scope["capabilities"])):
            errors.append(
                f"scope {scope['scope_id']} contains duplicate capability {capability}"
            )
        for selector in sorted(_duplicates(scope["inclusions"])):
            errors.append(
                f"scope {scope['scope_id']} contains duplicate inclusion {selector}"
            )
        excluded_selectors = [item["selector"] for item in scope["exclusions"]]
        for selector in sorted(_duplicates(excluded_selectors)):
            errors.append(
                f"scope {scope['scope_id']} contains duplicate exclusion {selector}"
            )
        for selector in sorted(set(scope["inclusions"]) & set(excluded_selectors)):
            errors.append(
                f"scope {scope['scope_id']} selector cannot be both included and "
                f"excluded: {selector}"
            )

    sources = manifest["sources"]
    source_ids = [item["source_id"] for item in sources]
    for source_id in sorted(_duplicates(source_ids)):
        errors.append(f"duplicate source_id: {source_id}")
    endpoint_aliases = [
        _canonical_identifier(item["endpoint_alias"]) for item in sources
    ]
    for endpoint_alias in sorted(_duplicates(endpoint_aliases)):
        errors.append(f"duplicate endpoint_alias: {endpoint_alias}")
    source_by_id = {item["source_id"]: item for item in sources}
    for source in sources:
        if source["scope_id"] not in scope_id_set:
            errors.append(
                f"source {source['source_id']} references unknown scope_id {source['scope_id']!r}"
            )
    for scope_id in scope_id_set:
        if not any(source["scope_id"] == scope_id for source in sources):
            errors.append(f"scope {scope_id} has no declared source")
        independent_domains = {
            _canonical_identifier(source["independence_domain"])
            for source in sources
            if source["scope_id"] == scope_id
            and source["authority_role"] == "primary_observation"
        }
        minimum_sources = manifest["corroboration_policy"][
            "minimum_independent_sources"
        ]
        if len(independent_domains) < minimum_sources:
            errors.append(
                f"scope {scope_id} has {len(independent_domains)} independence domain(s); "
                f"corroboration requires {minimum_sources} for independent "
                "source/collector provenance"
            )

    for location, value in _boundary_strings(manifest):
        if _is_wildcard(value):
            errors.append(f"boundary wildcard is forbidden at {location}: {value!r}")

    attempts = manifest["run_policy"]["planned_attempts"]
    attempt_ids = [item["attempt_id"] for item in attempts]
    for attempt_id in sorted(_duplicates(attempt_ids)):
        errors.append(f"duplicate attempt_id: {attempt_id}")
    actual_tuples = {
        (item["scope_id"], item["source_id"], item["capability"])
        for item in attempts
    }
    if len(actual_tuples) != len(attempts):
        errors.append("planned_attempts contains a duplicate scope/source/capability tuple")
    for attempt in attempts:
        source = source_by_id.get(attempt["source_id"])
        if attempt["scope_id"] not in scope_id_set:
            errors.append(
                f"planned attempt {attempt['attempt_id']} references unknown scope_id"
            )
        if source is None:
            errors.append(
                f"planned attempt {attempt['attempt_id']} references unknown source_id"
            )
        elif source["scope_id"] != attempt["scope_id"]:
            errors.append(
                f"planned attempt {attempt['attempt_id']} crosswires source and scope"
            )
        if attempt["capability"] not in capabilities_by_scope.get(
            attempt["scope_id"], set()
        ):
            errors.append(
                f"planned attempt {attempt['attempt_id']} uses an undeclared scope capability"
            )

    expected_tuples = _expected_attempt_tuples(manifest)
    missing_tuples = expected_tuples - actual_tuples
    unexpected_tuples = actual_tuples - expected_tuples
    if missing_tuples:
        errors.append(
            "planned attempt matrix does not cover: "
            + ", ".join("/".join(item) for item in sorted(missing_tuples))
        )
    if unexpected_tuples:
        errors.append(
            "planned attempt matrix contains unexpected tuples: "
            + ", ".join("/".join(item) for item in sorted(unexpected_tuples))
        )

    timestamp_fields = {
        "created_at": manifest["created_at"],
        "collection_window.not_before": manifest["collection_window"]["not_before"],
        "collection_window.not_after": manifest["collection_window"]["not_after"],
    }
    parsed: dict[str, datetime] = {}
    for label, value in timestamp_fields.items():
        error = _timestamp_error(label, value)
        if error:
            errors.append(error)
        else:
            parsed[label] = _parse_utc(value)
    if (
        "collection_window.not_before" in parsed
        and "collection_window.not_after" in parsed
        and parsed["collection_window.not_before"] > parsed["collection_window.not_after"]
    ):
        errors.append("collection_window requires not_before <= not_after")
    if (
        "created_at" in parsed
        and "collection_window.not_before" in parsed
        and parsed["created_at"] > parsed["collection_window.not_before"]
    ):
        errors.append(
            "created_at must be no later than collection_window.not_before"
        )

    return errors


def _fact_identity(fact: dict[str, Any]) -> str:
    """Return a type-stable key for one normalized subject and predicate."""
    return canonical_sha256(
        {
            "subject": fact["subject"],
            "predicate": fact["predicate"],
            "normalization_profile": fact["normalization_profile"],
        }
    )


def _fact_signature(fact: dict[str, Any]) -> str:
    """Return a type-stable key for an exact normalized observation."""
    return canonical_sha256(
        {
            "subject": fact["subject"],
            "predicate": fact["predicate"],
            "object": fact["object"],
            "normalization_profile": fact["normalization_profile"],
        }
    )


def _subject_identity(subject: dict[str, Any]) -> str:
    return canonical_sha256(subject)


def _validate_attempt(
    payload: dict[str, Any],
    envelope: dict[str, Any],
    manifest: dict[str, Any],
) -> list[str]:
    errors: list[str] = []
    status = payload["status"]
    reason = payload["reason"]
    unobserved = payload["unobserved_portions"]
    exhausted = payload["enumeration_exhausted"]
    observations = payload["observations"]

    if status == "complete":
        if reason != "none":
            errors.append("complete attempt requires reason=none")
        if unobserved:
            errors.append("complete attempt cannot contain unobserved portions")
        if exhausted is not True:
            errors.append("complete attempt requires exhausted enumeration")
    elif status == "partial":
        if reason == "none":
            errors.append("partial attempt requires a non-none reason")
        if not unobserved:
            errors.append("partial attempt must identify unobserved portions")
        if exhausted is True:
            errors.append("partial attempt cannot claim exhausted enumeration")
    elif status in {"failed", "not_attempted"}:
        if reason == "none":
            errors.append(f"{status} attempt requires a non-none reason")
        if exhausted is True:
            errors.append(f"{status} attempt cannot claim exhausted enumeration")
        if payload["result_count"] != 0:
            errors.append(f"{status} attempt requires result_count=0")
        if observations:
            errors.append(f"{status} attempt cannot contain factual observations")

    observed_values: dict[str, str] = {}
    observed_object_identities: set[str] = set()
    has_object_observations = False
    for index, observation in enumerate(observations):
        prefix = f"attempt observations[{index}]"
        errors.extend(
            _validate_fact_subject(
                observation,
                envelope,
                manifest,
                label=prefix,
            )
        )
        predicate = observation["predicate"]
        value = observation["object"]
        if _PREDICATE_CAPABILITIES[predicate] != payload["capability"]:
            errors.append(
                f"{prefix} predicate is not supported by the attempt capability"
            )
        if predicate in _BOOLEAN_PREDICATES and type(value) is not bool:
            errors.append(f"{prefix} boolean predicate requires a boolean object")
        if predicate in _COUNT_PREDICATES and type(value) is not int:
            errors.append(f"{prefix} count predicate requires an integer object")

        identity = _fact_identity(observation)
        value_signature = canonical_sha256(value)
        previous_value = observed_values.get(identity)
        if previous_value is not None:
            if previous_value == value_signature:
                errors.append(f"duplicate attempt observation at {prefix}")
            else:
                errors.append(f"conflicting attempt observations at {prefix}")
        else:
            observed_values[identity] = value_signature

        if predicate in _COUNT_PREDICATES:
            if type(value) is int and value != payload["result_count"]:
                errors.append(
                    f"{prefix} count object does not match attempt result_count"
                )
            continue

        has_object_observations = True
        if predicate in _BOOLEAN_STATE_PREDICATES or value is True:
            observed_object_identities.add(_subject_identity(observation["subject"]))

    if (
        has_object_observations
        and len(observed_object_identities) != payload["result_count"]
    ):
        errors.append("observed object identities must equal result_count")
    return errors


def _validate_assessments(
    envelope: dict[str, Any], manifest: dict[str, Any]
) -> list[str]:
    errors: list[str] = []
    observer_ids = {item["observer_id"] for item in manifest["observers"]}
    policy = manifest["corroboration_policy"]
    minimum_refs = max(
        policy["minimum_independent_sources"],
        policy["minimum_independent_collectors"],
    )
    payload_kind = envelope["payload"]["kind"]
    assessment_observers = [
        assessment["observer_id"]
        for assessment in envelope["epistemic_assessments"]
    ]
    for observer_id in sorted(_duplicates(assessment_observers)):
        errors.append(f"duplicate assessment observer_id: {observer_id}")

    for index, assessment in enumerate(envelope["epistemic_assessments"]):
        observer_id = assessment["observer_id"]
        prefix = f"epistemic_assessments[{index}]"
        if observer_id not in observer_ids:
            errors.append(f"{prefix} references unknown observer_id {observer_id!r}")

        quadrant = assessment["quadrant"]
        if quadrant == "known_known":
            if assessment["evidence_state"] != "verified_current":
                errors.append("known_known requires verified_current evidence")
            if len(set(assessment["basis_refs"])) < minimum_refs:
                errors.append(
                    f"known_known requires at least {minimum_refs} basis refs"
                )
        elif not assessment.get("next_action"):
            errors.append(f"{prefix} requires next_action unless quadrant is known_known")

        if quadrant == "unknown_unknown" and payload_kind == "claim":
            errors.append("unknown_unknown cannot classify a factual claim")
    return errors


def _validate_fact_subject(
    fact: dict[str, Any],
    envelope: dict[str, Any],
    manifest: dict[str, Any],
    *,
    label: str,
) -> list[str]:
    errors: list[str] = []
    subject = fact["subject"]
    context_scope_id = envelope["source_context"]["scope_id"]
    subject_scope_id = subject["scope_id"]
    if subject_scope_id != context_scope_id:
        errors.append(f"{label} subject scope_id must match source_context scope_id")

    scope_by_id = {
        scope["scope_id"]: scope for scope in manifest["boundary"]["scope_units"]
    }
    scope = scope_by_id.get(subject_scope_id)
    if scope is None:
        errors.append(f"{label} subject scope_id is not declared by the manifest")
    else:
        if subject["target_alias"] != scope["target_alias"]:
            errors.append(f"{label} subject target_alias must match its declared scope")
        selector = subject.get("selector")
        if selector is not None and selector not in scope["inclusions"]:
            errors.append(
                f"{label} subject selector must be a declared scope inclusion"
            )

    predicate = fact["predicate"]
    has_selector = "selector" in subject
    if predicate in _SELECTOR_REQUIRED_PREDICATES and not has_selector:
        errors.append(f"{label} {predicate} requires subject.selector")
    elif predicate not in _SELECTOR_REQUIRED_PREDICATES and has_selector:
        errors.append(f"{label} {predicate} forbids subject.selector")
    return errors


def _validate_claim_subject(
    payload: dict[str, Any],
    envelope: dict[str, Any],
    manifest: dict[str, Any],
) -> list[str]:
    return _validate_fact_subject(
        payload,
        envelope,
        manifest,
        label="claim",
    )


def validate_envelope(envelope: Any, manifest: Any) -> list[str]:
    """Validate one envelope's structure and metadata against a manifest.

    This function verifies content-address metadata but does not dereference the
    storage object. Artifact-byte verification belongs at the storage boundary.
    """
    canonical_error = _canonical_input_error(envelope)
    if canonical_error:
        return [f"canonical JSON: {canonical_error}"]
    valid, structural = SchemaValidator.validate_dict(
        envelope, _record_schema("EvidenceEnvelope")
    )
    errors = [f"schema: {error}" for error in structural]
    if isinstance(envelope, dict):
        provenance = envelope.get("provenance")
        if isinstance(provenance, dict):
            collector_name = provenance.get("collector_name")
            if isinstance(collector_name, str) and _opaque_alias_error(
                collector_name,
                maximum_length=128,
                namespaced=False,
            ):
                errors.append("collector_name must be a canonical opaque alias")
    if not valid:
        if isinstance(envelope, dict):
            native = envelope.get("native_evidence")
            if isinstance(native, dict):
                storage_ref = native.get("storage_ref")
                if isinstance(storage_ref, str) and not _CONTENT_ADDRESS_PATTERN.fullmatch(
                    storage_ref
                ):
                    errors.append(
                        "native evidence storage_ref must be a content-addressed relative path"
                    )
        return errors

    manifest_errors = validate_manifest(manifest)
    if manifest_errors:
        return [f"manifest: {error}" for error in manifest_errors]

    expected_manifest_digest = canonical_sha256(manifest)
    if envelope["manifest_digest"] != expected_manifest_digest:
        errors.append("manifest_digest does not match the supplied manifest")

    scope_ids = {
        item["scope_id"] for item in manifest["boundary"]["scope_units"]
    }
    source_by_id = {item["source_id"]: item for item in manifest["sources"]}
    context = envelope["source_context"]
    if context["scope_id"] not in scope_ids:
        errors.append("source_context references unknown scope_id")
    source = source_by_id.get(context["source_id"])
    if source is None:
        errors.append("source_context references unknown source_id")
    elif source["scope_id"] != context["scope_id"]:
        errors.append("source_context source does not belong to its scope")

    parsed_times: dict[str, datetime] = {}
    timestamp_fields = {
        "started_at": envelope["started_at"],
        "observed_at": envelope["observed_at"],
        "recorded_at": envelope["recorded_at"],
        "native_evidence.captured_at": envelope["native_evidence"]["captured_at"],
    }
    for index, assessment in enumerate(envelope["epistemic_assessments"]):
        timestamp_fields[f"epistemic_assessments[{index}].classified_at"] = assessment[
            "classified_at"
        ]
    for label, value in timestamp_fields.items():
        error = _timestamp_error(label, value)
        if error:
            errors.append(error)
        else:
            parsed_times[label] = _parse_utc(value)
    if all(name in parsed_times for name in ("started_at", "observed_at", "recorded_at")):
        if not (
            parsed_times["started_at"]
            <= parsed_times["observed_at"]
            <= parsed_times["recorded_at"]
        ):
            errors.append("timestamps require started_at <= observed_at <= recorded_at")
        window_start = _parse_utc(manifest["collection_window"]["not_before"])
        window_end = _parse_utc(manifest["collection_window"]["not_after"])
        if not window_start <= parsed_times["observed_at"] <= window_end:
            errors.append("observed_at falls outside the manifest collection_window")
        for index, _assessment in enumerate(envelope["epistemic_assessments"]):
            classified_label = f"epistemic_assessments[{index}].classified_at"
            if classified_label not in parsed_times:
                continue
            if not (
                parsed_times["observed_at"]
                <= parsed_times[classified_label]
                <= parsed_times["recorded_at"]
            ):
                errors.append(
                    f"{classified_label} requires observed_at <= classified_at <= recorded_at"
                )
    if all(
        name in parsed_times
        for name in ("started_at", "native_evidence.captured_at", "recorded_at")
    ):
        if not (
            parsed_times["started_at"]
            <= parsed_times["native_evidence.captured_at"]
            <= parsed_times["recorded_at"]
        ):
            errors.append("native evidence captured_at must fall within the envelope interval")

    declared_digest = envelope["integrity"]["envelope_sha256"]
    if declared_digest != envelope_sha256(envelope):
        errors.append("envelope_sha256 mismatch")

    native = envelope["native_evidence"]
    storage_match = _CONTENT_ADDRESS_PATTERN.fullmatch(native["storage_ref"])
    if storage_match is None:
        errors.append("native evidence storage_ref must be a content-addressed relative path")
    else:
        if storage_match.group("shard") != native["sha256"][:2]:
            errors.append("storage_ref shard does not match evidence sha256")
        if storage_match.group("digest") != native["sha256"]:
            errors.append("storage_ref digest does not match evidence sha256")
        expected_media_type = _MEDIA_TYPE_BY_EXTENSION[storage_match.group("extension")]
        if native["media_type"] != expected_media_type:
            errors.append("storage_ref extension does not match evidence media_type")
    if native["sanitizer_profile"] != manifest["sanitization_policy"]["profile"]:
        errors.append("sanitizer_profile does not match the manifest")

    payload = envelope["payload"]
    if payload["kind"] == "attempt":
        errors.extend(_validate_attempt(payload, envelope, manifest))
    elif payload["kind"] == "claim":
        predicate = payload["predicate"]
        value = payload["object"]
        if predicate in _BOOLEAN_PREDICATES and type(value) is not bool:
            errors.append("claim predicate requires a boolean object")
        if predicate in _COUNT_PREDICATES and type(value) is not int:
            errors.append("count claim predicate requires an integer object")
        errors.extend(_validate_claim_subject(payload, envelope, manifest))
        if payload["semantic_claim_key"] != semantic_claim_key(payload):
            errors.append("semantic_claim_key mismatch")
        if payload["claim_fingerprint"] != claim_fingerprint(payload):
            errors.append("claim_fingerprint mismatch")
    errors.extend(_validate_assessments(envelope, manifest))
    return errors


def _status_totals(attempts: list[dict[str, Any]]) -> dict[str, int]:
    totals = {"complete": 0, "partial": 0, "failed": 0, "not_attempted": 0}
    for envelope in attempts:
        status = envelope["payload"]["status"]
        totals[status] += 1
    return totals


def _claim_asserts_absence(payload: dict[str, Any]) -> bool:
    predicate = payload["predicate"]
    value = payload["object"]
    return (
        predicate in _BOOLEAN_EXISTENCE_PREDICATES
        and value is False
        or predicate in _COUNT_PREDICATES
        and type(value) is int
        and value == 0
    )


def _basis_is_semantically_relevant(
    assessed: dict[str, Any], basis: dict[str, Any]
) -> bool:
    assessed_payload = assessed["payload"]
    basis_payload = basis["payload"]
    assessed_kind = assessed_payload["kind"]
    if basis_payload["kind"] != assessed_kind:
        return False
    if assessed_kind == "attempt":
        return (
            assessed["source_context"]["scope_id"]
            == basis["source_context"]["scope_id"]
            and assessed_payload["capability"] == basis_payload["capability"]
            and _attempt_observation_signature(assessed)
            == _attempt_observation_signature(basis)
        )
    if assessed_kind == "claim":
        return (
            assessed_payload["semantic_claim_key"]
            == basis_payload["semantic_claim_key"]
        )
    return False


def _attempt_observation_signature(envelope: dict[str, Any]) -> str:
    payload = envelope["payload"]
    return canonical_sha256(
        {
            "scope_id": envelope["source_context"]["scope_id"],
            "capability": payload["capability"],
            "status": payload["status"],
            "reason": payload["reason"],
            "result_count": payload["result_count"],
            "enumeration_exhausted": payload["enumeration_exhausted"],
            "unobserved_portions": sorted(payload["unobserved_portions"]),
            "observation_signatures": sorted(
                _fact_signature(observation)
                for observation in payload["observations"]
            ),
        }
    )


def _collection_envelope(
    basis: dict[str, Any],
    attempt_by_envelope: dict[str, dict[str, Any]],
) -> dict[str, Any] | None:
    if basis["payload"]["kind"] == "attempt":
        return basis
    if basis["payload"]["kind"] == "claim":
        return attempt_by_envelope.get(basis["payload"]["attempt_envelope_id"])
    return None


def _attempt_is_available_and_fresh(
    attempt: dict[str, Any],
    *,
    assessed_sequence: int,
    classified_at: datetime,
    maximum_age: int,
) -> bool:
    if attempt["sequence"] >= assessed_sequence:
        return False
    try:
        observed_at = _parse_utc(attempt["observed_at"])
        recorded_at = _parse_utc(attempt["recorded_at"])
    except (TypeError, ValueError, OverflowError):
        return False
    age = (classified_at - observed_at).total_seconds()
    return recorded_at <= classified_at and 0 <= age <= maximum_age


def _known_known_has_prior_conflict(
    assessed: dict[str, Any],
    classified_at: datetime,
    maximum_age: int,
    attempt_by_envelope: dict[str, dict[str, Any]],
    admissible_envelope_ids: set[str],
) -> bool:
    assessed_payload = assessed["payload"]
    assessed_kind = assessed_payload["kind"]
    for attempt in attempt_by_envelope.values():
        if attempt["envelope_id"] not in admissible_envelope_ids:
            continue
        if not _attempt_is_available_and_fresh(
            attempt,
            assessed_sequence=assessed["sequence"],
            classified_at=classified_at,
            maximum_age=maximum_age,
        ):
            continue

        if assessed_kind == "attempt":
            if (
                attempt["source_context"]["scope_id"]
                == assessed["source_context"]["scope_id"]
                and attempt["payload"]["capability"]
                == assessed_payload["capability"]
                and _attempt_observation_signature(attempt)
                != _attempt_observation_signature(assessed)
            ):
                return True
            continue
        if assessed_kind != "claim":
            continue

        assessed_identity = _fact_identity(assessed_payload)
        assessed_value = canonical_sha256(assessed_payload["object"])
        for observation in attempt["payload"]["observations"]:
            if (
                _fact_identity(observation) == assessed_identity
                and canonical_sha256(observation["object"]) != assessed_value
            ):
                return True

        predicate = assessed_payload["predicate"]
        if (
            predicate in _COUNT_PREDICATES
            and attempt["source_context"]["scope_id"]
            == assessed_payload["subject"]["scope_id"]
            and attempt["payload"]["capability"]
            == _PREDICATE_CAPABILITIES[predicate]
            and attempt["payload"]["status"] == "complete"
            and attempt["payload"]["enumeration_exhausted"] is True
            and attempt["payload"]["result_count"] != assessed_payload["object"]
        ):
            return True
    return False


def _validate_resolved_assessments(
    manifest: dict[str, Any],
    envelopes: list[dict[str, Any]],
    envelope_by_id: dict[str, dict[str, Any]],
    attempt_by_envelope: dict[str, dict[str, Any]],
    admissible_envelope_ids: set[str],
) -> list[str]:
    errors: list[str] = []
    maximum_age = manifest["freshness_policy"]["max_age_seconds"]
    minimum_sources = manifest["corroboration_policy"][
        "minimum_independent_sources"
    ]
    minimum_collectors = manifest["corroboration_policy"][
        "minimum_independent_collectors"
    ]
    source_by_id = {source["source_id"]: source for source in manifest["sources"]}
    for envelope in envelopes:
        for assessment in envelope["epistemic_assessments"]:
            known_known = assessment["quadrant"] == "known_known"
            try:
                classified_at = _parse_utc(assessment["classified_at"])
                envelope_observed_at = _parse_utc(envelope["observed_at"])
            except (TypeError, ValueError, OverflowError):
                continue
            if known_known:
                envelope_age = (classified_at - envelope_observed_at).total_seconds()
                if not 0 <= envelope_age <= maximum_age:
                    errors.append("verified_current basis is outside the freshness policy")
                assessed_collection = _collection_envelope(
                    envelope,
                    attempt_by_envelope,
                )
                if (
                    assessed_collection is not None
                    and assessed_collection["envelope_id"] != envelope["envelope_id"]
                ):
                    try:
                        collection_observed_at = _parse_utc(
                            assessed_collection["observed_at"]
                        )
                    except (TypeError, ValueError, OverflowError):
                        pass
                    else:
                        collection_age = (
                            classified_at - collection_observed_at
                        ).total_seconds()
                        if not 0 <= collection_age <= maximum_age:
                            errors.append(
                                "collection attempt is outside the freshness policy"
                            )
                if _known_known_has_prior_conflict(
                    envelope,
                    classified_at,
                    maximum_age,
                    attempt_by_envelope,
                    admissible_envelope_ids,
                ):
                    errors.append(
                        "known_known has unresolved conflicting evidence"
                    )

            independence_domains: set[str] = set()
            independent_collectors: set[str] = set()
            for basis_ref in assessment["basis_refs"]:
                basis = envelope_by_id.get(basis_ref.removeprefix("envelope:"))
                if basis is None:
                    errors.append(f"basis ref does not resolve: {basis_ref}")
                    continue
                causally_valid = (
                    basis["sequence"] < envelope["sequence"]
                    if known_known
                    else basis["sequence"] <= envelope["sequence"]
                )
                if not causally_valid:
                    errors.append("assessment basis must be causally prior")
                if basis["payload"]["kind"] == "run_summary":
                    errors.append("run_summary cannot be assessment basis")
                    continue
                try:
                    basis_observed_at = _parse_utc(basis["observed_at"])
                    basis_recorded_at = _parse_utc(basis["recorded_at"])
                except (TypeError, ValueError, OverflowError):
                    continue
                if basis_recorded_at > classified_at:
                    errors.append(
                        "assessment basis must be recorded no later than classified_at"
                    )
                if not known_known:
                    continue
                if not causally_valid or basis_recorded_at > classified_at:
                    continue
                if not _basis_is_semantically_relevant(envelope, basis):
                    if (
                        envelope["payload"]["kind"] == "attempt"
                        and basis["payload"]["kind"] == "attempt"
                        and envelope["source_context"]["scope_id"]
                        == basis["source_context"]["scope_id"]
                        and envelope["payload"]["capability"]
                        == basis["payload"]["capability"]
                    ):
                        errors.append(
                            "attempt basis does not agree with assessed observation"
                        )
                    else:
                        errors.append("assessment basis is not semantically relevant")
                    continue

                collection = _collection_envelope(basis, attempt_by_envelope)
                if collection is None:
                    errors.append(
                        "assessment basis does not resolve to collection provenance"
                    )
                    continue
                source = source_by_id.get(
                    collection["source_context"]["source_id"]
                )
                if source is not None:
                    if source["authority_role"] != "primary_observation":
                        errors.append(
                            "known_known basis source is not eligible "
                            "observational authority"
                        )
                    else:
                        independence_domains.add(
                            _canonical_identifier(source["independence_domain"])
                        )
                        independent_collectors.add(
                            _canonical_identifier(
                                collection["provenance"]["collector_name"]
                            )
                        )
                basis_age = (classified_at - basis_observed_at).total_seconds()
                if not 0 <= basis_age <= maximum_age:
                    errors.append("verified_current basis is outside the freshness policy")
                if collection["envelope_id"] != basis["envelope_id"]:
                    try:
                        collection_observed_at = _parse_utc(
                            collection["observed_at"]
                        )
                    except (TypeError, ValueError, OverflowError):
                        continue
                    collection_age = (
                        classified_at - collection_observed_at
                    ).total_seconds()
                    if not 0 <= collection_age <= maximum_age:
                        errors.append(
                            "collection attempt is outside the freshness policy"
                        )
            if known_known and len(independence_domains) < minimum_sources:
                errors.append(
                    "known_known lacks the required independence domain provenance "
                    "for independent source/collector provenance"
                )
            if known_known and len(independent_collectors) < minimum_collectors:
                errors.append(
                    "known_known lacks the required independent collectors"
                )
    return errors


def validate_ledger(
    manifest: Any,
    envelopes: Any,
    *,
    finalized: bool = True,
) -> list[str]:
    """Validate an ordered in-memory envelope ledger.

    ``ingestion_nonce`` correlates one ingestion only. Cross-ingestion replay
    prevention requires an external nonce registry and is outside this pure
    validator. Set ``finalized=False`` only while a stream is still open.
    """
    manifest_errors = validate_manifest(manifest)
    if manifest_errors:
        return [f"manifest: {error}" for error in manifest_errors]
    if not isinstance(envelopes, list):
        return ["ledger must be a JSON array"]

    errors: list[str] = []
    manifest_digest = canonical_sha256(manifest)
    expected_previous = manifest_digest
    run_ids: set[str] = set()
    ingestion_nonces: set[str] = set()
    envelope_ids: set[str] = set()
    admissible_envelope_ids: set[str] = set()
    valid_envelopes: list[dict[str, Any]] = []
    attempts: list[dict[str, Any]] = []
    attempt_by_envelope: dict[str, dict[str, Any]] = {}
    claims: list[dict[str, Any]] = []
    summaries: list[dict[str, Any]] = []
    previous_recorded_at: datetime | None = None
    structurally_valid_envelope_count = 0

    envelope_schema = _record_schema("EvidenceEnvelope")
    for index, envelope in enumerate(envelopes):
        if not isinstance(envelope, dict):
            errors.append(f"envelopes[{index}] must be an object")
            continue
        canonical_envelope_error = _canonical_input_error(envelope)
        envelope_errors = validate_envelope(envelope, manifest)
        errors.extend(f"envelopes[{index}]: {error}" for error in envelope_errors)
        structurally_valid, _ = SchemaValidator.validate_dict(envelope, envelope_schema)
        if not structurally_valid:
            continue
        structurally_valid_envelope_count += 1

        try:
            recorded_at = _parse_utc(envelope["recorded_at"])
        except (TypeError, ValueError, OverflowError):
            recorded_at = None
        if (
            recorded_at is not None
            and previous_recorded_at is not None
            and recorded_at < previous_recorded_at
        ):
            errors.append("ledger recorded_at must be nondecreasing by sequence")
        if recorded_at is not None:
            previous_recorded_at = recorded_at

        if envelope["sequence"] != index:
            errors.append(f"envelopes[{index}]: sequence must be contiguous from zero")
        if envelope["previous_digest"] != expected_previous:
            errors.append(f"envelopes[{index}]: previous_digest breaks the chain")
        expected_previous = envelope["integrity"]["envelope_sha256"]

        envelope_id = envelope["envelope_id"]
        if envelope_id in envelope_ids:
            errors.append(f"duplicate envelope_id: {envelope_id}")
        envelope_ids.add(envelope_id)
        run_ids.add(envelope["run_id"])
        ingestion_nonces.add(envelope["ingestion_nonce"])

        if canonical_envelope_error:
            continue
        valid_envelopes.append(envelope)
        if not envelope_errors:
            admissible_envelope_ids.add(envelope_id)

        kind = envelope["payload"]["kind"]
        if kind == "attempt":
            attempts.append(envelope)
            attempt_by_envelope[envelope_id] = envelope
        elif kind == "claim":
            claims.append(envelope)
        elif kind == "run_summary":
            summaries.append(envelope)

    if envelopes and structurally_valid_envelope_count != len(envelopes):
        errors.append("ledger contains structurally invalid envelopes")
    if len(run_ids) > 1:
        errors.append("ledger envelopes must share one run_id")
    if len(ingestion_nonces) > 1:
        errors.append("ledger envelopes must share one ingestion_nonce")
    if finalized and len(summaries) != 1:
        errors.append("finalized ledger requires exactly one run_summary")
    elif not finalized and len(summaries) > 1:
        errors.append("streaming ledger may contain at most one run_summary")
    if summaries:
        final_envelope = envelopes[-1]
        final_payload = (
            final_envelope.get("payload")
            if isinstance(final_envelope, dict)
            else None
        )
        if not isinstance(final_payload, dict) or final_payload.get(
            "kind"
        ) != "run_summary":
            errors.append("run_summary must be the final envelope")

    planned = manifest["run_policy"]["planned_attempts"]
    planned_by_id = {item["attempt_id"]: item for item in planned}
    emitted_ids = [item["payload"]["attempt_id"] for item in attempts]
    for attempt_id in sorted(_duplicates(emitted_ids)):
        errors.append(f"duplicate emitted attempt_id: {attempt_id}")
    emitted_id_set = set(emitted_ids)
    planned_id_set = set(planned_by_id)
    missing_attempts = sorted(planned_id_set - emitted_id_set)
    unexpected_attempts = sorted(emitted_id_set - planned_id_set)
    if missing_attempts:
        errors.append(f"missing planned attempts: {', '.join(missing_attempts)}")
    if unexpected_attempts:
        errors.append(f"unexpected attempts: {', '.join(unexpected_attempts)}")

    for attempt in attempts:
        payload = attempt["payload"]
        expected = planned_by_id.get(payload["attempt_id"])
        if expected is None:
            continue
        context = attempt["source_context"]
        actual_tuple = (
            context["scope_id"],
            context["source_id"],
            payload["capability"],
        )
        expected_tuple = (
            expected["scope_id"],
            expected["source_id"],
            expected["capability"],
        )
        if actual_tuple != expected_tuple:
            errors.append(
                f"attempt {payload['attempt_id']} does not match its planned "
                "scope/source/capability tuple"
            )

    claim_ids = [item["payload"]["claim_id"] for item in claims]
    for claim_id in sorted(_duplicates(claim_ids)):
        errors.append(f"duplicate claim_id: {claim_id}")

    for claim in claims:
        payload = claim["payload"]
        referenced_attempt = attempt_by_envelope.get(payload["attempt_envelope_id"])
        if referenced_attempt is None:
            errors.append(
                f"claim {payload['claim_id']} references an unknown attempt envelope"
            )
            continue
        if referenced_attempt["sequence"] >= claim["sequence"]:
            errors.append("claim must follow its referenced attempt")
        try:
            attempt_recorded_at = _parse_utc(referenced_attempt["recorded_at"])
            claim_recorded_at = _parse_utc(claim["recorded_at"])
        except (TypeError, ValueError, OverflowError):
            pass
        else:
            if attempt_recorded_at > claim_recorded_at:
                errors.append("claim cannot be recorded before its referenced attempt")
        if claim["source_context"] != referenced_attempt["source_context"]:
            errors.append("claim source_context must match its referenced attempt")
        expected_capability = _PREDICATE_CAPABILITIES[payload["predicate"]]
        if referenced_attempt["payload"]["capability"] != expected_capability:
            errors.append("claim predicate is not supported by its referenced attempt capability")
        attempt_payload = referenced_attempt["payload"]
        status = attempt_payload["status"]
        exhausted = attempt_payload["enumeration_exhausted"] is True
        result_count = attempt_payload["result_count"]
        predicate = payload["predicate"]
        value = payload["object"]

        if predicate not in _COUNT_PREDICATES:
            observation_signatures = {
                _fact_signature(observation)
                for observation in attempt_payload["observations"]
            }
            if _fact_signature(payload) not in observation_signatures:
                errors.append(
                    "claim fact is not present in referenced attempt observations"
                )

        if status in {"failed", "not_attempted"}:
            errors.append(f"{status} attempt cannot support claims")

        if predicate in _COUNT_PREDICATES:
            if type(value) is int and value != result_count:
                errors.append("count claim object does not match the attempt result_count")
            if not (status == "complete" and exhausted):
                errors.append("count claim requires a complete, exhausted attempt")

        if predicate in _BOOLEAN_EXISTENCE_PREDICATES:
            if value is True and result_count == 0:
                errors.append("exists=true claim requires a positive result")
                errors.append("positive boolean claim requires a nonzero attempt result_count")
            elif value is False:
                if not (status == "complete" and exhausted):
                    errors.append("absence claim requires a complete, exhausted attempt")
                if predicate == "git.repository.exists" and result_count != 0:
                    errors.append("exists=false claim requires a zero result")
                    errors.append("absence claim requires an attempt result_count of zero")

        if predicate in _BOOLEAN_STATE_PREDICATES and not (
            status == "complete" and exhausted and result_count > 0
        ):
            qualifier = "false " if value is False else ""
            errors.append(
                f"{qualifier}boolean state claim requires a complete, "
                "exhausted positive observation"
            )

        if _claim_asserts_absence(payload) and predicate in _COUNT_PREDICATES:
            if not (
                status == "complete"
                and exhausted
            ):
                errors.append("absence claim requires a complete, exhausted attempt")
            if result_count != 0:
                errors.append("absence claim requires an attempt result_count of zero")

    envelope_by_id = {item["envelope_id"]: item for item in valid_envelopes}
    errors.extend(
        _validate_resolved_assessments(
            manifest,
            valid_envelopes,
            envelope_by_id,
            attempt_by_envelope,
            admissible_envelope_ids,
        )
    )

    if summaries:
        summary = summaries[0]
        payload = summary["payload"]
        actual_totals = _status_totals(attempts)
        if payload["status_totals"] != actual_totals:
            errors.append("summary status_totals do not match emitted attempts")
        if payload["planned_attempts"] != len(planned_by_id):
            errors.append("summary planned_attempts does not match the manifest")
        if payload["emitted_attempts"] != len(attempts):
            errors.append("summary emitted_attempts does not match the ledger")
        if payload["prior_chain_digest"] != summary["previous_digest"]:
            errors.append("summary prior_chain_digest does not match the preceding chain")

        all_complete = (
            not missing_attempts
            and not unexpected_attempts
            and len(attempts) == len(planned_by_id)
            and all(
                item["payload"]["status"] == "complete"
                and item["payload"]["enumeration_exhausted"] is True
                for item in attempts
            )
        )
        if payload["boundary_result"] == "complete" and not all_complete:
            errors.append(
                "boundary_result cannot be complete with missing, non-complete, "
                "or non-exhausted attempts"
            )

    return errors
