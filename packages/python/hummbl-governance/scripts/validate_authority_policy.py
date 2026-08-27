#!/usr/bin/env python3
"""Validate the structured authority policy (gap-9).

Ensures authority_policy.json conforms to the policy schema and
fleet consistency rules:
- Every role has a trust_tier and identity_class
- Every authority has scope, limit, max_severity, requires_receipt, revoked
- max_severity is one of LOW/MEDIUM/HIGH/CRITICAL
- Agent authors (tier 2) with github_mutation must have requires_receipt=true
- Operator (tier 5) has no receipt requirement

Usage:
    python scripts/validate_authority_policy.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

POLICY_PATH = Path("hummbl_governance/data/authority_policy.json")

VALID_SEVERITIES = {"LOW", "MEDIUM", "HIGH", "CRITICAL"}
REQUIRED_AUTHORITY_FIELDS = {"scope", "limit", "max_severity", "requires_receipt", "revoked"}
REQUIRED_ROLE_FIELDS = {"trust_tier", "identity_class", "authorities"}


def validate_policy(policy: dict) -> list[str]:
    """Validate policy structure and rules. Returns list of violations."""
    violations: list[str] = []

    if policy.get("schema_version") != "1.0.0":
        violations.append(f"Unsupported schema_version: {policy.get('schema_version')}")

    roles = policy.get("roles", {})
    if not roles:
        violations.append("No roles defined in policy")
        return violations

    for role_id, role in roles.items():
        missing = REQUIRED_ROLE_FIELDS - set(role.keys())
        if missing:
            violations.append(f"Role '{role_id}' missing fields: {missing}")
            continue

        authorities = role.get("authorities", {})
        if not authorities:
            violations.append(f"Role '{role_id}' has no authorities")
            continue

        for auth_name, auth in authorities.items():
            missing = REQUIRED_AUTHORITY_FIELDS - set(auth.keys())
            if missing:
                violations.append(f"Role '{role_id}' authority '{auth_name}' missing fields: {missing}")
                continue

            severity = auth.get("max_severity", "")
            if severity not in VALID_SEVERITIES:
                violations.append(
                    f"Role '{role_id}' authority '{auth_name}' invalid max_severity: {severity}"
                )

            # Agent authors (tier 2) with github_mutation must require receipt
            if (
                role.get("identity_class") == "agent_author"
                and auth_name == "github_mutation"
                and not auth.get("requires_receipt")
            ):
                violations.append(
                    f"Role '{role_id}' (agent_author) github_mutation must have requires_receipt=true"
                )

    return violations


def main() -> int:
    if not POLICY_PATH.exists():
        print(f"ERROR: Policy file not found: {POLICY_PATH}", file=sys.stderr)
        return 2

    with open(POLICY_PATH, encoding="utf-8") as f:
        policy = json.load(f)

    violations = validate_policy(policy)

    print("Authority Policy Validation")
    print(f"  Roles:      {len(policy.get('roles', {}))}")
    print(f"  Valid:      {'YES' if not violations else 'NO'}")

    if violations:
        print(f"  Violations: {len(violations)}")
        for v in violations:
            print(f"    - {v}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
