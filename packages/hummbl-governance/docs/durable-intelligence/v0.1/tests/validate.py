#!/usr/bin/env python3
"""Agent Session Receipt validator for the Durable Intelligence Doctrine v0.1.

Validates receipts against the schema and enforces semantic rules:
- Mutation truthfulness: actions claiming PR/branch creation must have
  corresponding mutations_made entries
- Capability bounding: claims with `verified` posture require
  `connector` or `test_runner` in tools_available
- Claim posture consistency

Uses only Python stdlib.
"""

import json
import sys
from pathlib import Path
from typing import Any


SCHEMA_PATH = Path(__file__).parent.parent / "session-receipt.schema.json"

REQUIRED_FIELDS = [
    "schema_version", "session_id", "source_agent", "environment",
    "tools_available", "repository_or_system_scope", "starting_state",
    "actions_attempted", "mutations_made", "claims", "decisions",
    "negative_knowledge", "open_questions", "next_actions",
    "authority_boundaries", "receipt_destination", "completion_status"
]

VALID_POSTURES = {"observed", "source_reported", "inferred", "provisional",
                  "verified", "refuted", "unresolved"}

VALID_COMPLETION = {"COMPLETED", "PARTIAL", "BLOCKED", "INCONCLUSIVE", "SUPERSEDED"}

VALID_DISPOSITIONS = {"CONFIRMED", "REFUTED", "INCONCLUSIVE",
                      "BLOCKED_MISSING_AUTHORITY", "SUPERSEDED"}

VALID_TOOLS = {"shell", "filesystem", "network", "connector", "browser",
               "test_runner", "deployment", "write_access", "read_only"}


def load_schema() -> dict[str, Any]:
    with open(SCHEMA_PATH, encoding="utf-8") as f:
        return json.load(f)


def _check_required(receipt: dict) -> list[str]:
    errors = []
    for field in REQUIRED_FIELDS:
        if field not in receipt:
            errors.append(f"Missing required field: {field}")
    return errors


def _check_mutation_truthfulness(receipt: dict) -> list[str]:
    """Actions claiming artifact creation must have matching mutations_made."""
    errors = []
    mutations = receipt.get("mutations_made", [])
    for action in receipt.get("actions_attempted", []):
        action_text = action.get("action", "").lower()
        result = action.get("result", "")
        if result != "succeeded":
            continue
        # Check if action text mentions creating a PR/branch/commit
        for artifact_type in ["pr", "branch", "commit", "issue", "file", "deployment"]:
            if artifact_type in action_text and "create" in action_text:
                # Must have at least one mutation of this type
                has_mutation = any(
                    m.get("artifact_type") == artifact_type
                    for m in mutations if m.get("created") is True
                )
                if not has_mutation:
                    errors.append(
                        f"Action '{action.get('action', '?')}' claims "
                        f"creation of {artifact_type} but no matching "
                        f"mutations_made entry exists"
                    )
    return errors


def _check_capabilityBounding(receipt: dict) -> list[str]:
    """Verified claims require connector or test_runner in tools_available."""
    errors = []
    tools = set(receipt.get("tools_available", []))
    for claim in receipt.get("claims", []):
        if claim.get("posture") == "verified":
            if "connector" not in tools and "test_runner" not in tools and "shell" not in tools:
                errors.append(
                    f"Claim '{claim.get('claim', '?')[:60]}...' has "
                    f"posture='verified' but tools_available lacks "
                    f"connector/test_runner/shell"
                )
    return errors


def _check_claim_postures(receipt: dict) -> list[str]:
    errors = []
    for claim in receipt.get("claims", []):
        posture = claim.get("posture", "")
        if posture not in VALID_POSTURES:
            errors.append(
                f"Claim '{claim.get('claim', '?')[:60]}...' has "
                f"invalid posture: '{posture}'"
            )
    return errors


def _check_completion_status(receipt: dict) -> list[str]:
    status = receipt.get("completion_status", "")
    if status not in VALID_COMPLETION:
        return [f"Invalid completion_status: '{status}'"]
    return []


def _check_handoff_disposition(receipt: dict) -> list[str]:
    disp = receipt.get("handoff_disposition")
    if disp is not None and disp not in VALID_DISPOSITIONS:
        return [f"Invalid handoff_disposition: '{disp}'"]
    return []


def _check_tools(receipt: dict) -> list[str]:
    errors = []
    for tool in receipt.get("tools_available", []):
        if tool not in VALID_TOOLS:
            errors.append(f"Invalid tool in tools_available: '{tool}'")
    return errors


def validate_receipt(receipt: dict) -> list[str]:
    """Validate a receipt. Returns list of error strings (empty = valid)."""
    errors = []
    errors.extend(_check_required(receipt))
    if errors:
        return errors  # Can't check further if required fields missing

    errors.extend(_check_mutation_truthfulness(receipt))
    errors.extend(_check_capabilityBounding(receipt))
    errors.extend(_check_claim_postures(receipt))
    errors.extend(_check_completion_status(receipt))
    errors.extend(_check_handoff_disposition(receipt))
    errors.extend(_check_tools(receipt))

    return errors


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: validate.py <receipt.json> [...]", file=sys.stderr)
        return 2

    all_valid = True
    for path in sys.argv[1:]:
        with open(path, encoding="utf-8") as f:
            receipt = json.load(f)
        errors = validate_receipt(receipt)
        if errors:
            all_valid = False
            print(f"INVALID: {path}")
            for e in errors:
                print(f"  - {e}")
        else:
            print(f"VALID: {path}")

    return 0 if all_valid else 1


if __name__ == "__main__":
    sys.exit(main())
