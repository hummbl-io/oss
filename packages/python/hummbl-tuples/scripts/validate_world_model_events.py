#!/usr/bin/env python3
"""Validate world-model event tuples against their schemas.

Stdlib-only validation (no jsonschema dependency).
Checks required fields, type constraints, enum membership, and
adversarial conditions specific to world-model events.

Usage:
    python scripts/validate_world_model_events.py
"""

import json
import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCHEMA_DIR = os.path.join(
    REPO_ROOT, "schemas", "extensions", "world_model"
)
EXAMPLES_DIR = os.path.join(REPO_ROOT, "examples", "world_model")

CONTROL_MODE_ENUM = {"USER_DIRECT", "AI_PROPOSE_USER_CONFIRM", "AI_AUTONOMOUS"}

UNCERTAINTY_ENUM = {"low", "moderate", "high", "unknown"}

VISIBILITY_ENUM = {"private", "shared", "public"}

REQUIRED_ENVELOPE = [
    "tuple_type", "id", "time", "actor", "principal",
    "control_mode", "tuple_data",
]


def validate_event(event: dict, filename: str) -> list[str]:
    """Validate a single world-model event tuple. Returns list of errors."""
    errors = []
    eid = event.get("id", f"<{filename}>")
    ttype = event.get("tuple_type", "")

    # Check required envelope fields
    for field in REQUIRED_ENVELOPE:
        if field not in event:
            errors.append(f"[{eid}] Missing required field: {field}")

    # principal must be non-empty
    if not event.get("principal"):
        errors.append(f"[{eid}] principal must be non-empty")

    # control_mode enum
    if event.get("control_mode") not in CONTROL_MODE_ENUM:
        errors.append(f"[{eid}] control_mode invalid")

    # tuple_data must exist and be a dict
    td = event.get("tuple_data")
    if not isinstance(td, dict):
        errors.append(f"[{eid}] tuple_data must be an object")
        return errors

    # receipt_link required for all events
    if not td.get("receipt_link"):
        errors.append(f"[{eid}] tuple_data.receipt_link must be non-empty")

    # visibility_class enum (if present)
    vc = td.get("visibility_class")
    if vc is not None and vc not in VISIBILITY_ENUM:
        errors.append(f"[{eid}] visibility_class invalid")

    # uncertainty_posture enum (if present)
    up = td.get("uncertainty_posture")
    if up is not None and up not in UNCERTAINTY_ENUM:
        errors.append(f"[{eid}] uncertainty_posture invalid")

    # Type-specific adversarial checks
    if ttype == "STATE_TRANSITION":
        if event.get("control_mode") == "AI_AUTONOMOUS":
            if td.get("to_state") == "published":
                errors.append(
                    f"[{eid}] AI_AUTONOMOUS state transition to "
                    f"'published' without user authority"
                )

    if ttype == "MODEL_REVISION":
        if not td.get("receipt_link"):
            errors.append(
                f"[{eid}] MODEL_REVISION requires receipt_link — "
                f"durable event without receipt"
            )
        if event.get("control_mode") == "AI_AUTONOMOUS":
            if td.get("user_approval_posture") == "pending":
                errors.append(
                    f"[{eid}] MODEL_REVISION with AI_AUTONOMOUS "
                    f"control_mode and pending user approval — "
                    f"agent cannot autonomously revise without "
                    f"user approval or receipt"
                )

    if ttype == "CONTRADICTION_EVENT":
        claims = td.get("competing_claims", [])
        if isinstance(claims, list) and len(claims) < 2:
            errors.append(
                f"[{eid}] CONTRADICTION_EVENT requires at least "
                f"2 competing_claims"
            )

    return errors


def load_examples(directory: str) -> list[tuple[str, dict]]:
    """Load all JSON examples from a directory (recursive)."""
    examples = []
    if not os.path.isdir(directory):
        return examples
    for root, _dirs, files in sorted(os.walk(directory)):
        for name in sorted(files):
            if name.endswith(".json"):
                path = os.path.join(root, name)
                with open(path, encoding="utf-8") as f:
                    examples.append((name, json.load(f)))
    return examples


def main() -> int:
    """Run validation on all examples."""
    total_errors = 0
    valid_count = 0
    invalid_count = 0

    examples = load_examples(EXAMPLES_DIR)
    for name, event in examples:
        is_invalid_fixture = name.startswith(("09-", "10-"))
        errors = validate_event(event, name)
        if is_invalid_fixture:
            # Expect errors
            if not errors:
                print(f"FAIL: {name} — expected errors but got none")
                total_errors += 1
            else:
                print(f"PASS: {name} ({len(errors)} error(s))")
                for e in errors:
                    print(f"  {e}")
                invalid_count += 1
        else:
            # Expect no errors
            if errors:
                print(f"FAIL: {name}")
                for e in errors:
                    print(f"  {e}")
                total_errors += len(errors)
            else:
                print(f"PASS: {name}")
                valid_count += 1

    print(f"\n{'=' * 40}")
    print(f"Valid fixtures: {valid_count}, Invalid fixtures: {invalid_count}")
    if total_errors:
        print(f"VALIDATION FAILED: {total_errors} error(s)")
        return 1
    print("All fixtures validated correctly")
    return 0


if __name__ == "__main__":
    sys.exit(main())
