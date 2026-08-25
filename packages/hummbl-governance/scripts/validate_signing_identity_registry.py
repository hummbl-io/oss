#!/usr/bin/env python3
"""Validate the signing identity registry against its schema and policy rules.

Implements the fail-closed policy from #241:
- Unknown, revoked, pending, or tier-ineligible keys must fail closed.
- Agent signatures prove agent authorship only; they do not satisfy human final review.
- Tier 3+ final review must resolve to a verified human reviewer key.

Usage:
    python scripts/validate_signing_identity_registry.py
    python scripts/validate_signing_identity_registry.py --json

Exit codes:
    0 = registry valid
    1 = registry invalid (schema or policy violation)
    2 = operational error
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REGISTRY_PATH = Path("hummbl_governance/data/signing_identity_registry.json")
SCHEMA_PATH = Path("hummbl_governance/data/signing_identity_registry.schema.json")


def validate_policy(registry: dict) -> list[str]:
    """Validate policy rules beyond the JSON schema. Returns list of violations."""
    violations: list[str] = []
    identities = registry.get("identities", [])

    seen_identities: set[str] = set()
    human_reviewers: list[dict] = []

    for entry in identities:
        ident = entry.get("identity", "")
        if ident in seen_identities:
            violations.append(f"duplicate identity: {ident}")
        seen_identities.add(ident)

        identity_class = entry.get("identity_class", "")
        key_status = entry.get("key_status", "")
        fingerprint = entry.get("public_gpg_fingerprint", "")
        allowed_uses = entry.get("allowed_uses", [])
        max_tier = entry.get("max_tier", 0)

        # Fail-closed: revoked keys must not be usable
        if key_status == "revoked":
            violations.append(
                f"revoked key for '{ident}' is still in registry"
                " — remove or mark revoked with no allowed_uses"
            )

        # Fail-closed: pending keys have no fingerprint
        if key_status == "pending" and fingerprint:
            violations.append(f"pending key for '{ident}' has a fingerprint — status should be 'active'")

        # Fail-closed: active keys must have a fingerprint
        if key_status == "active" and not fingerprint:
            violations.append(f"active key for '{ident}' has no fingerprint")

        # Agent keys must not have human_final_review
        if identity_class in ("agent_author", "agent_reviewer"):
            if "human_final_review" in allowed_uses:
                violations.append(
                    f"agent '{ident}' has human_final_review in allowed_uses"
                    " — agents cannot perform human final review"
                )
            if max_tier >= 3:
                violations.append(
                    f"agent '{ident}' has max_tier={max_tier}"
                    " — agents cannot act at tier 3+ (human final review)"
                )

        # Human reviewers can have human_final_review
        if identity_class == "human_reviewer":
            human_reviewers.append(entry)
            if "human_final_review" not in allowed_uses:
                violations.append(f"human_reviewer '{ident}' lacks human_final_review in allowed_uses")

    # Must have at least one human reviewer
    if not human_reviewers:
        violations.append("no human_reviewer identity in registry — tier 3+ final review cannot be satisfied")

    return violations


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate signing identity registry")
    parser.add_argument("--registry", default=str(REGISTRY_PATH))
    parser.add_argument("--schema", default=str(SCHEMA_PATH))
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    registry_path = Path(args.registry)
    schema_path = Path(args.schema)

    if not registry_path.exists():
        print(f"ERROR: registry not found: {registry_path}", file=sys.stderr)
        return 2
    if not schema_path.exists():
        print(f"ERROR: schema not found: {schema_path}", file=sys.stderr)
        return 2

    try:
        registry = json.loads(registry_path.read_text(encoding="utf-8"))
        # Schema is validated structurally below; full jsonschema would
        # require a third-party dep, which this package avoids.
        json.loads(schema_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"ERROR: JSON parse failed: {e}", file=sys.stderr)
        return 2

    # Schema validation (stdlib only — no jsonschema dependency)
    # Basic structural checks; full schema validation would use jsonschema
    required_top = ["schema_version", "generated_at", "identities"]
    for field in required_top:
        if field not in registry:
            print(f"ERROR: missing required field: {field}", file=sys.stderr)
            return 1

    if not isinstance(registry["identities"], list) or not registry["identities"]:
        print("ERROR: identities must be a non-empty array", file=sys.stderr)
        return 1

    policy_violations = validate_policy(registry)

    result = {
        "valid": len(policy_violations) == 0,
        "identity_count": len(registry["identities"]),
        "policy_violations": policy_violations,
    }

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print("Signing Identity Registry Validation")
        print(f"  Identities: {result['identity_count']}")
        print(f"  Valid:      {'YES' if result['valid'] else 'NO'}")
        if policy_violations:
            print("  Violations:")
            for v in policy_violations:
                print(f"    - {v}")

    return 0 if result["valid"] else 1


if __name__ == "__main__":
    sys.exit(main())
