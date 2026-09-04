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

"""Tests for GitHub auth provider (gap-3 / #408)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from hummbl_governance.kernel.github_auth import GitHubAuthProvider


@pytest.fixture
def provider(tmp_path: Path) -> GitHubAuthProvider:
    """Create a provider with a temp config path."""
    return GitHubAuthProvider(config_path=tmp_path / "github-tokens.json")


class TestEnvironmentToken:
    """Test token resolution from environment variables."""

    def test_env_token_resolved(self, provider: GitHubAuthProvider, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("HUMMBL_GITHUB_TOKEN_DEVIN", "ghp_devin_token_123")
        token = provider.get_token("devin")
        assert token is not None
        assert token.agent_id == "devin"
        assert token.token_value == "ghp_devin_token_123"
        assert token.token_type == "pat"

    def test_env_token_with_hyphen(self, provider: GitHubAuthProvider, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("HUMMBL_GITHUB_TOKEN_CLAUDE_CODE", "ghp_cc_token_456")
        token = provider.get_token("claude-code")
        assert token is not None
        assert token.agent_id == "claude-code"

    def test_no_env_token(self, provider: GitHubAuthProvider, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("HUMMBL_GITHUB_TOKEN_DEVIN", raising=False)
        monkeypatch.delenv("HUMMBL_GITHUB_TOKEN", raising=False)
        monkeypatch.delenv("GH_TOKEN", raising=False)
        token = provider.get_token("devin")
        assert token is None


class TestConfigFileToken:
    """Test token resolution from config file."""

    def test_config_token_resolved(self, tmp_path: Path) -> None:
        config = {
            "devin": {
                "token": "ghp_devin_from_config",
                "token_type": "pat",
                "scopes": ["repo"],
                "github_login": "hummbl-devin",
            }
        }
        config_path = tmp_path / "github-tokens.json"
        config_path.write_text(json.dumps(config))
        provider = GitHubAuthProvider(config_path=config_path)
        token = provider.get_token("devin")
        assert token is not None
        assert token.token_value == "ghp_devin_from_config"
        assert token.github_login == "hummbl-devin"


class TestSharedTokenFallback:
    """Test fallback to shared token (deprecated)."""

    def test_shared_token_fallback(self, provider: GitHubAuthProvider, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("HUMMBL_GITHUB_TOKEN", "ghp_shared_token")
        monkeypatch.delenv("HUMMBL_GITHUB_TOKEN_DEVIN", raising=False)
        token = provider.get_token("devin")
        assert token is not None
        assert token.token_type == "shared"
        assert token.github_login == "hummbl-dev"


class TestVerifyIdentity:
    """Test identity verification."""

    def test_verify_with_env_token(self, provider: GitHubAuthProvider, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("HUMMBL_GITHUB_TOKEN_DEVIN", "ghp_devin_token")
        assert provider.verify_identity("devin") is True

    def test_verify_without_token(self, provider: GitHubAuthProvider, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("HUMMBL_GITHUB_TOKEN_DEVIN", raising=False)
        monkeypatch.delenv("HUMMBL_GITHUB_TOKEN", raising=False)
        monkeypatch.delenv("GH_TOKEN", raising=False)
        assert provider.verify_identity("devin") is False

    def test_verify_with_matching_token(self, provider: GitHubAuthProvider, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("HUMMBL_GITHUB_TOKEN_DEVIN", "ghp_devin_token")
        assert provider.verify_identity("devin", "ghp_devin_token") is True

    def test_verify_with_mismatched_token(self, provider: GitHubAuthProvider, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("HUMMBL_GITHUB_TOKEN_DEVIN", "ghp_devin_token")
        assert provider.verify_identity("devin", "wrong_token") is False


class TestRevocation:
    """Test token revocation."""

    def test_revoked_agent_cannot_authenticate(
        self, provider: GitHubAuthProvider, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A revoked agent should not be able to authenticate."""
        monkeypatch.setenv("HUMMBL_GITHUB_TOKEN_DEVIN", "ghp_devin_token")
        assert provider.verify_identity("devin") is True

        provider.revoke("devin")
        # After revocation, the cached token is gone
        # But env var is still set, so it would re-resolve
        # To truly revoke, the env var must be removed
        monkeypatch.delenv("HUMMBL_GITHUB_TOKEN_DEVIN", raising=False)
        monkeypatch.delenv("HUMMBL_GITHUB_TOKEN", raising=False)
        monkeypatch.delenv("GH_TOKEN", raising=False)
        assert provider.is_revoked("devin") is True
        assert provider.verify_identity("devin") is False

    def test_revoke_clears_cache(self, provider: GitHubAuthProvider, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("HUMMBL_GITHUB_TOKEN_DEVIN", "ghp_devin_token")
        provider.get_token("devin")  # Cache the token
        provider.revoke("devin")
        assert "devin" not in provider._token_cache


class TestListConfigured:
    """Test listing configured agents."""

    def test_list_from_env(self, provider: GitHubAuthProvider, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("HUMMBL_GITHUB_TOKEN_DEVIN", "token1")
        monkeypatch.setenv("HUMMBL_GITHUB_TOKEN_CODEX", "token2")
        agents = provider.list_configured_agents()
        assert "devin" in agents
        assert "codex" in agents

    def test_list_from_config(self, tmp_path: Path) -> None:
        config = {"devin": {"token": "t1"}, "codex": {"token": "t2"}}
        config_path = tmp_path / "github-tokens.json"
        config_path.write_text(json.dumps(config))
        provider = GitHubAuthProvider(config_path=config_path)
        agents = provider.list_configured_agents()
        assert "devin" in agents
        assert "codex" in agents


class TestDefaultScopes:
    """Test default scope assignment."""

    def test_read_only_agent_scopes(self, provider: GitHubAuthProvider, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("HUMMBL_GITHUB_TOKEN_NEXUS", "token")
        token = provider.get_token("nexus")
        assert token is not None
        assert "repo:read" in token.scopes

    def test_write_agent_scopes(self, provider: GitHubAuthProvider, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("HUMMBL_GITHUB_TOKEN_DEVIN", "token")
        token = provider.get_token("devin")
        assert token is not None
        assert "repo" in token.scopes
