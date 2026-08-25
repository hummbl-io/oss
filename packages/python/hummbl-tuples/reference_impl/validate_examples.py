#!/usr/bin/env python3
"""Validate HUMMBL tuple examples against local JSON Schemas.

Stdlib-only validator for the repo scaffold. It intentionally implements
only the subset of JSON Schema features used in this repository:

- type
- const
- enum
- required
- properties
- additionalProperties
- minLength
- minimum
- maximum
- minItems
- items
- pattern
- format (uuid only)
- allOf
- if / then / else
- not

This keeps the reference implementation portable and easy to audit.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

_UUID_RE = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
)

REPO_ROOT = Path(__file__).resolve().parent.parent
SCHEMAS_DIR = REPO_ROOT / "schemas"
EXAMPLES_DIR = REPO_ROOT / "examples"


class ValidationError(Exception):
    pass


SUPPORTED_SCHEMA_KEYS = {
    "$id",
    "$schema",
    "additionalProperties",
    "allOf",
    "const",
    "description",
    "else",
    "enum",
    "examples",
    "format",
    "if",
    "items",
    "maximum",
    "minItems",
    "minimum",
    "minLength",
    "not",
    "pattern",
    "properties",
    "required",
    "then",
    "title",
    "type",
}


def _check_schema_features(schema: dict, path: str = "$schema") -> None:
    """Fail loudly if a schema uses features outside this validator subset."""
    if not isinstance(schema, dict):
        raise ValidationError(f"{path}: schema must be an object")

    for key, value in schema.items():
        if key not in SUPPORTED_SCHEMA_KEYS:
            raise ValidationError(f"{path}: unsupported schema keyword {key!r}")

        if key == "properties":
            if not isinstance(value, dict):
                raise ValidationError(f"{path}.properties: expected object")
            for prop_name, prop_schema in value.items():
                _check_schema_features(prop_schema, f"{path}.properties.{prop_name}")
        elif key == "items":
            _check_schema_features(value, f"{path}.items")
        elif key == "additionalProperties" and isinstance(value, dict):
            _check_schema_features(value, f"{path}.additionalProperties")
        elif key == "allOf":
            if not isinstance(value, list):
                raise ValidationError(f"{path}.allOf: expected array")
            for idx, sub in enumerate(value):
                _check_schema_features(sub, f"{path}.allOf[{idx}]")
        elif key in ("if", "then", "else", "not"):
            _check_schema_features(value, f"{path}.{key}")


def _check_type(value, expected: str, path: str) -> None:
    type_map = {
        "object": dict,
        "array": list,
        "string": str,
        "integer": int,
        "number": (int, float),
        "boolean": bool,
        "null": type(None),
    }
    py_type = type_map.get(expected)
    if py_type is None:
        raise ValidationError(f"{path}: unsupported schema type {expected!r}")
    if expected == "integer" and isinstance(value, bool):
        raise ValidationError(f"{path}: expected integer, got boolean")
    if expected == "number" and isinstance(value, bool):
        raise ValidationError(f"{path}: expected number, got boolean")
    if not isinstance(value, py_type):
        raise ValidationError(f"{path}: expected {expected}, got {type(value).__name__}")


def _matches_type(value, expected: str) -> bool:
    """Return True if value matches the expected JSON Schema type (no raise)."""
    try:
        _check_type(value, expected, "$")
        return True
    except ValidationError:
        return False


def _matches(value, schema: dict) -> bool:
    """Return True iff value validates against schema (no errors raised)."""
    try:
        _validate(value, schema, "$")
        return True
    except ValidationError:
        return False


def _validate(value, schema: dict, path: str = "$") -> None:
    _check_schema_features(schema)

    expected_type = schema.get("type")
    if expected_type is not None:
        if isinstance(expected_type, list):
            # Union type (e.g., ["string", "null"]) — value must match at least one
            if not any(_matches_type(value, t) for t in expected_type):
                raise ValidationError(
                    f"{path}: expected one of types {expected_type!r}, got {type(value).__name__}"
                )
        else:
            _check_type(value, expected_type, path)

    if "const" in schema and value != schema["const"]:
        raise ValidationError(f"{path}: expected const {schema['const']!r}, got {value!r}")

    if "enum" in schema and value not in schema["enum"]:
        raise ValidationError(f"{path}: expected one of {schema['enum']!r}, got {value!r}")

    if isinstance(value, str):
        if "minLength" in schema and len(value) < schema["minLength"]:
            raise ValidationError(f"{path}: string length {len(value)} < minLength {schema['minLength']}")
        if "pattern" in schema and not re.search(schema["pattern"], value):
            raise ValidationError(f"{path}: value {value!r} does not match pattern {schema['pattern']!r}")
        if schema.get("format") == "uuid" and not _UUID_RE.match(value):
            raise ValidationError(f"{path}: value {value!r} is not a valid uuid")

    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if "minimum" in schema and value < schema["minimum"]:
            raise ValidationError(f"{path}: value {value} < minimum {schema['minimum']}")
        if "maximum" in schema and value > schema["maximum"]:
            raise ValidationError(f"{path}: value {value} > maximum {schema['maximum']}")

    if isinstance(value, list):
        if "minItems" in schema and len(value) < schema["minItems"]:
            raise ValidationError(f"{path}: item count {len(value)} < minItems {schema['minItems']}")
        item_schema = schema.get("items")
        if item_schema is not None:
            for idx, item in enumerate(value):
                _validate(item, item_schema, f"{path}[{idx}]")

    if isinstance(value, dict):
        required = schema.get("required", [])
        for key in required:
            if key not in value:
                raise ValidationError(f"{path}: missing required key {key!r}")

        properties = schema.get("properties", {})
        for key, subvalue in value.items():
            if key in properties:
                _validate(subvalue, properties[key], f"{path}.{key}")
            else:
                additional = schema.get("additionalProperties", True)
                if additional is False:
                    raise ValidationError(f"{path}: unexpected key {key!r}")
                if isinstance(additional, dict):
                    _validate(subvalue, additional, f"{path}.{key}")

    if "allOf" in schema:
        for idx, sub in enumerate(schema["allOf"]):
            _validate(value, sub, f"{path}.allOf[{idx}]")

    if "if" in schema:
        if _matches(value, schema["if"]):
            if "then" in schema:
                _validate(value, schema["then"], f"{path}.then")
        else:
            if "else" in schema:
                _validate(value, schema["else"], f"{path}.else")

    if "not" in schema:
        if _matches(value, schema["not"]):
            raise ValidationError(f"{path}: value matches 'not' subschema, expected mismatch")


def _schema_for_example(example_path: Path) -> Path | None:
    name = example_path.name
    prefix_to_schema = {
        "contract.": "contract.schema.json",
        "dct.": "dct.schema.json",
        "dctx.": "dctx.schema.json",
        "evidence.": "evidence.schema.json",
        "attest.": "attest.schema.json",
        "system.": "system.schema.json",
        "mm_applied.": "experimental/mm_applied.schema.json",
        "pretraining_trace.": "pretraining_trace.schema.json",
        "posttraining_trace.": "posttraining_trace.schema.json",
    }
    for prefix, schema_name in prefix_to_schema.items():
        if name.startswith(prefix):
            return SCHEMAS_DIR / schema_name

    tuple_type_to_schema = {
        "CONTRACT": "contract.schema.json",
        "DCT": "dct.schema.json",
        "DCTX": "dctx.schema.json",
        "EVIDENCE": "evidence.schema.json",
        "ATTEST": "attest.schema.json",
        "SYSTEM": "system.schema.json",
        "BASE_PROFILE_ISSUED": "base_profile_issued.schema.json",
        "BIO_ACTION_AUTHORIZED": "bio_action_authorized.schema.json",
        "BIO_ACTION_BLOCKED": "bio_action_blocked.schema.json",
        "BIO_ADAPTATION_EXECUTED": "bio_adaptation_executed.schema.json",
        "BIO_ADAPTATION_PROPOSED": "bio_adaptation_proposed.schema.json",
        "BIO_HARM_SIGNAL": "bio_harm_signal.schema.json",
        "BIO_OUTCOME_OBSERVED": "bio_outcome_observed.schema.json",
        "BIO_OVERRIDE": "bio_override.schema.json",
        "BIO_SIGNAL_CAPTURED": "bio_signal_captured.schema.json",
        "CONTROL_MODE_SET": "control_mode_set.schema.json",
        "REGISTRY_VERSION_PINNED": "registry_version_pinned.schema.json",
        "EXPERIMENT_RUN_ASSIGNED": "experiment_run_assigned.schema.json",
        "TRANSFORMATION_CANDIDATE": "transformation_candidate.schema.json",
        "TRANSFORMATION_SELECTED": "transformation_selected.schema.json",
        "MODEL_CANDIDATE": "model_candidate.schema.json",
        "MODEL_SELECTED": "model_selected.schema.json",
        "HITL_OVERRIDE": "hitl_override.schema.json",
        "PROMOTION_RECEIPT": "promotion_receipt.schema.json",
        "REVOCATION": "revocation.schema.json",
        "READINESS_INFERRED": "readiness_inferred.schema.json",
        "REASONING_PATH": "reasoning_path.schema.json",
        "STRAIN_FLAGGED": "strain_flagged.schema.json",
        "PATH_COMPARISON": "path_comparison.schema.json",
        "TRACE_EVIDENCE": "trace_evidence_tuple.schema.json",
        "SYSTEM": "system.schema.json",
        "WORKLOAD_INFERRED": "workload_inferred.schema.json",
        "MM_APPLIED": "experimental/mm_applied.schema.json",
        "OBSERVATION_EVENT": "extensions/world_model/observation_event.schema.json",
        "STATE_ASSERTION": "extensions/world_model/state_assertion.schema.json",
        "STATE_TRANSITION": "extensions/world_model/state_transition.schema.json",
        "MODEL_PROPOSAL": "extensions/world_model/model_proposal.schema.json",
        "PREDICTION_EVENT": "extensions/world_model/prediction_event.schema.json",
        "COUNTERFACTUAL_EVENT": "extensions/world_model/counterfactual_event.schema.json",
        "CONTRADICTION_EVENT": "extensions/world_model/contradiction_event.schema.json",
        "ACTION_SELECTION": "extensions/world_model/action_selection.schema.json",
        "OUTCOME_OBSERVATION": "extensions/world_model/outcome_observation.schema.json",
        "MODEL_REVISION": "extensions/world_model/model_revision.schema.json",
        "MODEL_RETRACTION": "extensions/world_model/model_retraction.schema.json",
        "CONSENT_CHANGE": "extensions/world_model/consent_change.schema.json",
        "VISIBILITY_CHANGE": "extensions/world_model/visibility_change.schema.json",
        "ACTION_AUTHORIZED": "extensions/multi_actor/action_authorized.schema.json",
        "ACTION_DENIED": "extensions/multi_actor/action_denied.schema.json",
        "ACTION_EXECUTED": "extensions/multi_actor/action_executed.schema.json",
        "ACTION_PROPOSED": "extensions/multi_actor/action_proposed.schema.json",
        "AGENT_CALIBRATION_UPDATED": "extensions/multi_actor/agent_calibration_updated.schema.json",
        "AGENT_CHALLENGE": "extensions/multi_actor/agent_challenge.schema.json",
        "AGENT_DISSENT": "extensions/multi_actor/agent_dissent.schema.json",
        "AGENT_INFERENCE": "extensions/multi_actor/agent_inference.schema.json",
        "AGENT_MODEL_PROPOSAL": "extensions/multi_actor/agent_model_proposal.schema.json",
        "AGENT_OBSERVATION": "extensions/multi_actor/agent_observation.schema.json",
        "AGENT_QUARANTINED": "extensions/multi_actor/agent_quarantined.schema.json",
        "AGENT_REBOUND": "extensions/multi_actor/agent_rebound.schema.json",
        "AGENT_REGISTERED": "extensions/multi_actor/agent_registered.schema.json",
        "AGENT_ROLE_ASSIGNED": "extensions/multi_actor/agent_role_assigned.schema.json",
        "AGENT_ROLE_EXPIRED": "extensions/multi_actor/agent_role_expired.schema.json",
        "AGENT_VERSION_CHANGED": "extensions/multi_actor/agent_version_changed.schema.json",
        "COALITION_DISSOLVED": "extensions/multi_actor/coalition_dissolved.schema.json",
        "COALITION_FORMED": "extensions/multi_actor/coalition_formed.schema.json",
        "COALITION_MEMBERSHIP_CHANGED": "extensions/multi_actor/coalition_membership_changed.schema.json",
        "DELEGATION_GRANTED": "extensions/multi_actor/delegation_granted.schema.json",
        "DELEGATION_REVOKED": "extensions/multi_actor/delegation_revoked.schema.json",
        "HANDOFF_EVENT": "extensions/multi_actor/handoff_event.schema.json",
        "MODEL_FORK": "extensions/multi_actor/model_fork.schema.json",
        "MODEL_MERGE_ACCEPTED": "extensions/multi_actor/model_merge_accepted.schema.json",
        "MODEL_MERGE_PROPOSAL": "extensions/multi_actor/model_merge_proposal.schema.json",
        "MODEL_MERGE_REJECTED": "extensions/multi_actor/model_merge_rejected.schema.json",
        "ORG_RATIFICATION": "extensions/multi_actor/org_ratification.schema.json",
        "ORG_REJECTION": "extensions/multi_actor/org_rejection.schema.json",
        "TOOL_RESULT_ADMITTED": "extensions/multi_actor/tool_result_admitted.schema.json",
        "TOOL_RESULT_PROPOSED": "extensions/multi_actor/tool_result_proposed.schema.json",
        "USER_RATIFICATION": "extensions/multi_actor/user_ratification.schema.json",
        "USER_REJECTION": "extensions/multi_actor/user_rejection.schema.json",
    }

    data = json.loads(example_path.read_text(encoding="utf-8"))
    tuple_type = data.get("tuple_type")
    schema_name = tuple_type_to_schema.get(tuple_type)
    if schema_name is None:
        return None
    return SCHEMAS_DIR / schema_name


def validate_example(example_path: Path) -> None:
    schema_path = _schema_for_example(example_path)
    if schema_path is None:
        raise ValidationError(f"{example_path.name}: could not determine schema")
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    data = json.loads(example_path.read_text(encoding="utf-8"))
    _check_schema_features(schema)
    _validate(data, schema)


def main() -> int:
    failures: list[str] = []
    examples = sorted(
        p for p in EXAMPLES_DIR.rglob("*.json")
        if "invalid" not in p.parts
    )
    for example in examples:
        try:
            validate_example(example)
            print(f"OK  {example.relative_to(REPO_ROOT)}")
        except Exception as exc:
            failures.append(f"FAIL {example.relative_to(REPO_ROOT)}: {exc}")

    if failures:
        for failure in failures:
            print(failure, file=sys.stderr)
        print(f"{len(failures)} validation failure(s)", file=sys.stderr)
        return 1

    print(f"Validated {len(examples)} example file(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
