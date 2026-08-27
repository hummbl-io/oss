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

"""Tests for structured authority policy validation (gap-9)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.validate_authority_policy import validate_policy

POLICY_PATH = Path(__file__).parent.parent / "hummbl_governance" / "data" / "authority_policy.json"


@pytest.fixture
def policy() -> dict:
    """Load the actual authority policy."""
    with open(POLICY_PATH, encoding="utf-8") as f:
        return json.load(f)


class TestAuthorityPolicyValidation:
    def test_policy_is_valid(self, policy: dict) -> None:
        """The shipped policy must be valid."""
        violations = validate_policy(policy)
        assert violations == [], f"Policy violations: {violations}"

    def test_policy_has_all_roles(self, policy: dict) -> None:
        roles = policy["roles"]
        expected = {"operator", "devin", "codex", "claude-code", "opencode", "gemini"}
        assert set(roles.keys()) == expected

    def test_operator_has_no_receipt_requirement(self, policy: dict) -> None:
        operator = policy["roles"]["operator"]
        for auth in operator["authorities"].values():
            assert not auth["requires_receipt"], "Operator should not require receipts"

    def test_agents_require_receipt_for_github_mutation(self, policy: dict) -> None:
        for role_id, role in policy["roles"].items():
            if role["identity_class"] != "agent_author":
                continue
            github_auth = role["authorities"].get("github_mutation")
            assert github_auth is not None, f"{role_id} missing github_mutation authority"
            assert github_auth["requires_receipt"], (
                f"{role_id} github_mutation must require receipt (two-person rule)"
            )

    def test_agent_max_severity_is_high(self, policy: dict) -> None:
        """Agents can go up to HIGH (not CRITICAL) for github_mutation."""
        for role_id, role in policy["roles"].items():
            if role["identity_class"] != "agent_author":
                continue
            github_auth = role["authorities"]["github_mutation"]
            assert github_auth["max_severity"] == "HIGH", (
                f"{role_id} github_mutation max_severity should be HIGH, got {github_auth['max_severity']}"
            )

    def test_operator_max_severity_is_critical(self, policy: dict) -> None:
        operator = policy["roles"]["operator"]
        assert operator["authorities"]["github_mutation"]["max_severity"] == "CRITICAL"


class TestPolicyValidatorRules:
    def test_missing_schema_version_fails(self) -> None:
        violations = validate_policy({"roles": {}})
        assert any("schema_version" in v for v in violations)

    def test_invalid_severity_fails(self) -> None:
        policy = {
            "schema_version": "1.0.0",
            "roles": {
                "test": {
                    "trust_tier": 2,
                    "identity_class": "agent_author",
                    "authorities": {
                        "github_mutation": {
                            "scope": "test",
                            "limit": "test",
                            "max_severity": "INVALID",
                            "requires_receipt": True,
                            "revoked": False,
                        }
                    },
                }
            },
        }
        violations = validate_policy(policy)
        assert any("invalid max_severity" in v for v in violations)

    def test_agent_without_receipt_fails(self) -> None:
        policy = {
            "schema_version": "1.0.0",
            "roles": {
                "test": {
                    "trust_tier": 2,
                    "identity_class": "agent_author",
                    "authorities": {
                        "github_mutation": {
                            "scope": "test",
                            "limit": "test",
                            "max_severity": "HIGH",
                            "requires_receipt": False,
                            "revoked": False,
                        }
                    },
                }
            },
        }
        violations = validate_policy(policy)
        assert any("requires_receipt=true" in v for v in violations)

    def test_missing_authority_field_fails(self) -> None:
        policy = {
            "schema_version": "1.0.0",
            "roles": {
                "test": {
                    "trust_tier": 2,
                    "identity_class": "agent_author",
                    "authorities": {
                        "github_mutation": {
                            "scope": "test",
                            "limit": "test",
                            "max_severity": "HIGH",
                            "requires_receipt": True,
                        }
                    },
                }
            },
        }
        violations = validate_policy(policy)
        assert any("missing fields" in v for v in violations)
