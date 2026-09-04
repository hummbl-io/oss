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

"""Tests for the structured authority policy (gap-9 / #414).

Verifies that the AuthorityEngine reads the structured JSON policy
instead of scraping markdown charters, and that the policy correctly
classifies mutations and enforces role-based authorization.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from hummbl_governance.kernel.authority_engine import AuthorityEngine


@pytest.fixture
def policy_file(tmp_path: Path) -> Path:
    """Create a minimal structured policy file."""
    policy = {
        "schema_version": "1.0.0",
        "mutation_classes": {
            "LOW": {
                "examples": ["bus_post", "receipt_create"],
                "requires_authority_check": False,
            },
            "MEDIUM": {
                "examples": ["commit", "file_write"],
                "requires_authority_check": True,
            },
            "HIGH": {
                "examples": ["archive_repo", "force_push"],
                "requires_authority_check": True,
            },
            "CRITICAL": {
                "examples": ["key_rotation", "production_deploy"],
                "requires_authority_check": True,
            },
        },
        "roles": {
            "operator": {
                "trust_tier": "OWNER",
                "can_authorize": ["LOW", "MEDIUM", "HIGH", "CRITICAL"],
                "scope": "unlimited",
                "limits": [],
            },
            "codex": {
                "trust_tier": "TRUSTED",
                "can_authorize": ["LOW", "MEDIUM", "HIGH"],
                "scope": "all_repos",
                "limits": [
                    "cannot authorize CRITICAL without operator DECISION receipt"
                ],
            },
            "devin": {
                "trust_tier": "MEDIUM-HIGH",
                "can_authorize": ["LOW", "MEDIUM"],
                "scope": "assigned_repos",
                "limits": [
                    "cannot authorize HIGH without operator DECISION receipt",
                    "cannot authorize CRITICAL",
                ],
            },
            "gemini": {
                "trust_tier": "PROBATIONARY",
                "can_authorize": ["LOW"],
                "scope": "research_docs_only",
                "limits": ["cannot authorize MEDIUM, HIGH, or CRITICAL"],
            },
        },
    }
    path = tmp_path / "authority_policy.json"
    path.write_text(json.dumps(policy))
    return path


@pytest.fixture
def engine(tmp_path: Path, policy_file: Path) -> AuthorityEngine:
    """Create an authority engine wired to the structured policy."""
    return AuthorityEngine(state_dir=tmp_path, policy_path=policy_file)


class TestStructuredPolicy:
    """Test that the engine reads structured JSON policy."""

    def test_policy_loaded(self, engine: AuthorityEngine) -> None:
        policy = engine._load_policy()
        assert policy is not None
        assert policy["schema_version"] == "1.0.0"

    def test_falls_back_when_no_policy(self, tmp_path: Path) -> None:
        """When no policy file exists, engine falls back to charter mode."""
        engine = AuthorityEngine(state_dir=tmp_path, policy_path=tmp_path / "nonexistent.json")
        policy = engine._load_policy()
        assert policy is None


class TestRoleAuthorization:
    """Test role-based authorization via structured policy."""

    def test_operator_can_authorize_critical(self, engine: AuthorityEngine) -> None:
        result = engine.check(
            agent_id="human",
            role_id="operator",
            authority="key_rotation",
            context={},
        )
        assert result.permitted is True

    def test_codex_can_authorize_high(self, engine: AuthorityEngine) -> None:
        result = engine.check(
            agent_id="codex",
            role_id="codex",
            authority="archive_repo",
            context={},
        )
        assert result.permitted is True

    def test_codex_cannot_authorize_critical(self, engine: AuthorityEngine) -> None:
        result = engine.check(
            agent_id="codex",
            role_id="codex",
            authority="key_rotation",
            context={},
        )
        assert result.permitted is False
        assert "cannot authorize CRITICAL" in result.reason

    def test_devin_can_authorize_medium(self, engine: AuthorityEngine) -> None:
        result = engine.check(
            agent_id="devin",
            role_id="devin",
            authority="commit",
            context={},
        )
        assert result.permitted is True

    def test_devin_cannot_authorize_high(self, engine: AuthorityEngine) -> None:
        result = engine.check(
            agent_id="devin",
            role_id="devin",
            authority="archive_repo",
            context={},
        )
        assert result.permitted is False
        assert "cannot authorize HIGH" in result.reason

    def test_gemini_can_authorize_low(self, engine: AuthorityEngine) -> None:
        result = engine.check(
            agent_id="gemini",
            role_id="gemini",
            authority="bus_post",
            context={},
        )
        assert result.permitted is True

    def test_gemini_cannot_authorize_medium(self, engine: AuthorityEngine) -> None:
        result = engine.check(
            agent_id="gemini",
            role_id="gemini",
            authority="commit",
            context={},
        )
        assert result.permitted is False
        assert "cannot authorize MEDIUM" in result.reason


class TestMutationClassification:
    """Test mutation type → class classification."""

    def test_bus_post_is_low(self, engine: AuthorityEngine) -> None:
        assert engine._classify_authority("bus_post", engine._load_policy()["mutation_classes"]) == "LOW"

    def test_commit_is_medium(self, engine: AuthorityEngine) -> None:
        assert engine._classify_authority("commit", engine._load_policy()["mutation_classes"]) == "MEDIUM"

    def test_archive_repo_is_high(self, engine: AuthorityEngine) -> None:
        assert engine._classify_authority("archive_repo", engine._load_policy()["mutation_classes"]) == "HIGH"

    def test_key_rotation_is_critical(self, engine: AuthorityEngine) -> None:
        assert engine._classify_authority("key_rotation", engine._load_policy()["mutation_classes"]) == "CRITICAL"

    def test_unknown_authority_returns_none(self, engine: AuthorityEngine) -> None:
        assert engine._classify_authority("unknown_mutation", engine._load_policy()["mutation_classes"]) is None


class TestUnknownRole:
    """Test behavior when role is not in policy."""

    def test_unknown_role_rejected(self, engine: AuthorityEngine) -> None:
        result = engine.check(
            agent_id="unknown",
            role_id="unknown_role",
            authority="commit",
            context={},
        )
        assert result.permitted is False
        assert "not defined in authority policy" in result.reason


class TestLimitEnforcement:
    """Test structured limit enforcement."""

    def test_limit_with_operator_decision_not_met(self, engine: AuthorityEngine) -> None:
        """codex limit: 'cannot authorize CRITICAL without operator DECISION receipt'."""
        result = engine.check(
            agent_id="codex",
            role_id="codex",
            authority="key_rotation",
            context={},  # No operator_decision_receipt
        )
        assert result.permitted is False
        # codex can't authorize CRITICAL at all, so this hits the can_authorize check first
        assert "cannot authorize CRITICAL" in result.reason

    def test_devin_high_without_decision_blocked(self, engine: AuthorityEngine) -> None:
        """devin limit: 'cannot authorize HIGH without operator DECISION receipt'."""
        result = engine.check(
            agent_id="devin",
            role_id="devin",
            authority="archive_repo",
            context={},  # No operator_decision_receipt
        )
        assert result.permitted is False
        # devin can't authorize HIGH at all (can_authorize=["LOW","MEDIUM"])
        assert "cannot authorize HIGH" in result.reason


class TestDefaultPolicyPath:
    """Test that the default policy path points to the shipped policy."""

    def test_default_policy_exists(self) -> None:
        """The shipped authority_policy.json should exist at the default path."""
        from hummbl_governance.kernel.authority_engine import AuthorityEngine
        assert AuthorityEngine._DEFAULT_POLICY_PATH.exists()

    def test_default_policy_is_valid_json(self) -> None:
        """The shipped policy should be valid JSON with expected structure."""
        from hummbl_governance.kernel.authority_engine import AuthorityEngine
        policy = json.loads(AuthorityEngine._DEFAULT_POLICY_PATH.read_text())
        assert "mutation_classes" in policy
        assert "roles" in policy
        assert "operator" in policy["roles"]
        assert "codex" in policy["roles"]
        assert "devin" in policy["roles"]
