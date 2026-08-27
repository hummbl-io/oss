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

"""Tests for GitHub Auth Provider abstraction (gap-3)."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

import pytest

from hummbl_governance.kernel.auth_provider import (
    AgentCredential,
    AuthProvider,
    EnvVarAuthProvider,
    GitHubAppAuthProvider,
    PATAuthProvider,
    create_auth_provider,
)


class TestAgentCredential:
    def test_mask_long_token(self) -> None:
        cred = AgentCredential(agent_id="devin", token="gho_abcdef1234567890", token_type="pat")
        assert cred.mask() == "gho_...7890"

    def test_mask_short_token(self) -> None:
        cred = AgentCredential(agent_id="devin", token="short", token_type="pat")
        assert cred.mask() == "***"

    def test_default_scopes_empty(self) -> None:
        cred = AgentCredential(agent_id="devin", token="token", token_type="pat")
        assert cred.scopes == []


class TestEnvVarAuthProvider:
    def test_resolve_existing_agent(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("GITHUB_TOKEN_DEVIN", "gho_test_token_123")
        provider = EnvVarAuthProvider()
        cred = provider.resolve("devin")
        assert cred is not None
        assert cred.agent_id == "devin"
        assert cred.token == "gho_test_token_123"
        assert cred.token_type == "env_var"

    def test_resolve_missing_agent(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("GITHUB_TOKEN_DEVIN", raising=False)
        provider = EnvVarAuthProvider()
        cred = provider.resolve("devin")
        assert cred is None

    def test_resolve_hyphenated_agent(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("GITHUB_TOKEN_CLAUDE_CODE", "gho_claude_token")
        provider = EnvVarAuthProvider()
        cred = provider.resolve("claude-code")
        assert cred is not None
        assert cred.token == "gho_claude_token"

    def test_list_configured_agents(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("GITHUB_TOKEN_DEVIN", "token1")
        monkeypatch.setenv("GITHUB_TOKEN_CODEX", "token2")
        monkeypatch.setenv("GITHUB_TOKEN_CLAUDE_CODE", "token3")
        provider = EnvVarAuthProvider()
        agents = provider.list_configured_agents()
        assert "devin" in agents
        assert "codex" in agents
        assert "claude-code" in agents


class TestPATAuthProvider:
    def test_resolve_existing_agent(self, tmp_path: Path) -> None:
        config = {
            "devin": {"token": "github_pat_devin_123", "scopes": ["repo"]},
            "codex": {"token": "github_pat_codex_456", "scopes": ["repo"]},
        }
        config_path = tmp_path / "pat-config.json"
        config_path.write_text(json.dumps(config))

        provider = PATAuthProvider(str(config_path))
        cred = provider.resolve("devin")
        assert cred is not None
        assert cred.token == "github_pat_devin_123"
        assert cred.token_type == "pat"
        assert "repo" in cred.scopes

    def test_resolve_missing_agent(self, tmp_path: Path) -> None:
        config_path = tmp_path / "pat-config.json"
        config_path.write_text("{}")

        provider = PATAuthProvider(str(config_path))
        cred = provider.resolve("devin")
        assert cred is None

    def test_list_configured_agents(self, tmp_path: Path) -> None:
        config = {
            "devin": {"token": "tok1"},
            "gemini": {"token": "tok2"},
        }
        config_path = tmp_path / "pat-config.json"
        config_path.write_text(json.dumps(config))

        provider = PATAuthProvider(str(config_path))
        agents = provider.list_configured_agents()
        assert set(agents) == {"devin", "gemini"}

    def test_missing_config_file(self) -> None:
        provider = PATAuthProvider("/nonexistent/path/config.json")
        cred = provider.resolve("devin")
        assert cred is None
        assert provider.list_configured_agents() == []


class TestGitHubAppAuthProvider:
    def test_resolve_missing_agent(self, tmp_path: Path) -> None:
        config_path = tmp_path / "app-config.json"
        config_path.write_text("{}")

        provider = GitHubAppAuthProvider(str(config_path))
        cred = provider.resolve("devin")
        assert cred is None

    def test_list_configured_agents(self, tmp_path: Path) -> None:
        config = {
            "devin": {"app_id": 123, "installation_id": 456, "private_key_path": "/tmp/key.pem"},
        }
        config_path = tmp_path / "app-config.json"
        config_path.write_text(json.dumps(config))

        provider = GitHubAppAuthProvider(str(config_path))
        agents = provider.list_configured_agents()
        assert agents == ["devin"]

    def test_missing_config_file(self) -> None:
        provider = GitHubAppAuthProvider("/nonexistent/path/config.json")
        assert provider.resolve("devin") is None
        assert provider.list_configured_agents() == []


class TestAuthProviderFactory:
    def test_create_env_var_provider(self) -> None:
        provider = create_auth_provider("env_var")
        assert isinstance(provider, EnvVarAuthProvider)

    def test_create_pat_provider(self, tmp_path: Path) -> None:
        config_path = tmp_path / "config.json"
        config_path.write_text("{}")
        provider = create_auth_provider("pat", str(config_path))
        assert isinstance(provider, PATAuthProvider)

    def test_create_github_app_provider(self, tmp_path: Path) -> None:
        config_path = tmp_path / "config.json"
        config_path.write_text("{}")
        provider = create_auth_provider("github_app", str(config_path))
        assert isinstance(provider, GitHubAppAuthProvider)

    def test_unknown_provider_type_raises(self) -> None:
        with pytest.raises(ValueError, match="Unknown auth provider type"):
            create_auth_provider("invalid")

    def test_pat_without_config_path_raises(self) -> None:
        with pytest.raises(ValueError, match="config_path"):
            create_auth_provider("pat")

    def test_github_app_without_config_path_raises(self) -> None:
        with pytest.raises(ValueError, match="config_path"):
            create_auth_provider("github_app")


class TestPluggableSwap:
    """Verify operators can swap providers without code changes."""

    def test_env_var_to_pat_swap(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        # Start with env_var provider
        monkeypatch.setenv("GITHUB_TOKEN_DEVIN", "env_token")
        env_provider = create_auth_provider("env_var")
        cred_env = env_provider.resolve("devin")
        assert cred_env is not None
        assert cred_env.token == "env_token"

        # Swap to PAT provider (operator creates PATs, updates config)
        config = {"devin": {"token": "pat_token", "scopes": ["repo"]}}
        config_path = tmp_path / "pat-config.json"
        config_path.write_text(json.dumps(config))

        pat_provider = create_auth_provider("pat", str(config_path))
        cred_pat = pat_provider.resolve("devin")
        assert cred_pat is not None
        assert cred_pat.token == "pat_token"
        assert cred_pat.token_type == "pat"
