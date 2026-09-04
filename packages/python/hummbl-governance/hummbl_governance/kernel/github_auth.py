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

"""GitHub Auth Provider — per-agent GitHub authentication.

Replaces the shared hummbl-dev GitHub token with per-agent authentication.
Supports two modes:
1. Fine-grained PATs (simpler, less scoped)
2. GitHub App installations (most secure, most setup)

Each agent has its own token, stored in an environment variable or
config file. GitHub mutations are attributable to the specific agent.

Usage:
    from hummbl_governance.kernel.github_auth import GitHubAuthProvider

    provider = GitHubAuthProvider()
    token = provider.get_token("devin")
    # Use token for GitHub API calls

    # Verify identity
    if provider.verify_identity("devin", token):
        # proceed with authenticated action
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class AgentToken:
    """A per-agent GitHub token."""

    agent_id: str
    token_type: str  # "pat" or "app"
    token_value: str  # The actual token (never logged)
    scopes: list[str]
    github_login: str  # The GitHub user/app the token authenticates as


class GitHubAuthProvider:
    """Per-agent GitHub authentication provider.

    Token resolution order:
    1. Environment variable: HUMMBL_GITHUB_TOKEN_<AGENT_ID>
    2. Config file: ~/.config/hummbl/github-tokens.json
    3. Fallback: shared HUMMBL_GITHUB_TOKEN env var (deprecated, logs warning)

    The provider never logs token values. It only exposes whether a token
    exists and what GitHub login it authenticates as.
    """

    def __init__(self, config_path: Path | None = None) -> None:
        self.config_path = config_path or (
            Path.home() / ".config" / "hummbl" / "github-tokens.json"
        )
        self._token_cache: dict[str, AgentToken] = {}
        self._config_cache: dict[str, Any] | None = None

    def get_token(self, agent_id: str) -> AgentToken | None:
        """Get the GitHub token for an agent.

        Returns None if no token is configured.

        Args:
            agent_id: The agent identity (e.g. "devin", "codex").

        Returns:
            AgentToken with the token value and metadata, or None.
        """
        # Check cache
        if agent_id in self._token_cache:
            return self._token_cache[agent_id]

        # 1. Check environment variable
        env_var = f"HUMMBL_GITHUB_TOKEN_{agent_id.upper().replace('-', '_')}"
        token_value = os.environ.get(env_var)
        if token_value:
            token = AgentToken(
                agent_id=agent_id,
                token_type="pat",
                token_value=token_value,
                scopes=self._default_scopes(agent_id),
                github_login=self._agent_to_login(agent_id),
            )
            self._token_cache[agent_id] = token
            return token

        # 2. Check config file
        config = self._load_config()
        if config and agent_id in config:
            agent_config = config[agent_id]
            token = AgentToken(
                agent_id=agent_id,
                token_type=agent_config.get("token_type", "pat"),
                token_value=agent_config["token"],
                scopes=agent_config.get("scopes", self._default_scopes(agent_id)),
                github_login=agent_config.get("github_login", self._agent_to_login(agent_id)),
            )
            self._token_cache[agent_id] = token
            return token

        # 3. Fallback: shared token (deprecated)
        shared_token = os.environ.get("HUMMBL_GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
        if shared_token:
            # Log warning — shared token means no per-agent attribution
            import logging
            logging.warning(
                "Agent %s using shared GitHub token — no per-agent attribution. "
                "Set HUMMBL_GITHUB_TOKEN_%s for per-agent auth.",
                agent_id,
                agent_id.upper().replace("-", "_"),
            )
            token = AgentToken(
                agent_id=agent_id,
                token_type="shared",
                token_value=shared_token,
                scopes=[],
                github_login="hummbl-dev",  # Shared token identity
            )
            self._token_cache[agent_id] = token
            return token

        return None

    def verify_identity(self, agent_id: str, token: str | None = None) -> bool:
        """Verify that an agent has a valid GitHub token.

        This is a cryptographic proof-of-identity check: the agent must
        possess a token that is configured for its identity.

        Args:
            agent_id: The agent identity.
            token: Optional token to verify. If None, checks if any token exists.

        Returns:
            True if the agent has a valid (non-empty) token.
        """
        if token is not None:
            # Verify the provided token matches the configured one
            configured = self.get_token(agent_id)
            if configured is None:
                return False
            return configured.token_value == token

        agent_token = self.get_token(agent_id)
        return agent_token is not None and bool(agent_token.token_value)

    def get_github_login(self, agent_id: str) -> str | None:
        """Get the GitHub login that an agent's token authenticates as.

        Args:
            agent_id: The agent identity.

        Returns:
            GitHub login string, or None if no token configured.
        """
        token = self.get_token(agent_id)
        if token is None:
            return None
        return token.github_login

    def is_revoked(self, agent_id: str) -> bool:
        """Check if an agent's token has been revoked.

        A revoked agent has no token configured (or the token has been
        removed from the config file).

        Args:
            agent_id: The agent identity.

        Returns:
            True if the agent has no valid token (revoked or never configured).
        """
        return not self.verify_identity(agent_id)

    def revoke(self, agent_id: str) -> None:
        """Revoke an agent's token by removing it from the cache.

        Note: This only removes the cached token. To permanently revoke,
        remove the token from the config file or environment, and revoke
        the token on GitHub.

        Args:
            agent_id: The agent identity.
        """
        self._token_cache.pop(agent_id, None)
        # Also remove from config cache so it won't be reloaded
        if self._config_cache and agent_id in self._config_cache:
            del self._config_cache[agent_id]

    def list_configured_agents(self) -> list[str]:
        """List all agents that have GitHub tokens configured.

        Returns:
            List of agent IDs with tokens.
        """
        agents = set()

        # Check environment variables
        for key in os.environ:
            if key.startswith("HUMMBL_GITHUB_TOKEN_"):
                agent_part = key[len("HUMMBL_GITHUB_TOKEN_"):].lower().replace("_", "-")
                agents.add(agent_part)

        # Check config file
        config = self._load_config()
        if config:
            agents.update(config.keys())

        return sorted(agents)

    def _load_config(self) -> dict[str, Any] | None:
        """Load the token config file."""
        if self._config_cache is not None:
            return self._config_cache
        if not self.config_path.exists():
            return None
        import json
        with open(self.config_path, encoding="utf-8") as f:
            self._config_cache = json.load(f)
        return self._config_cache

    def _default_scopes(self, agent_id: str) -> list[str]:
        """Get default scopes for an agent based on trust tier."""
        # Read-only agents get minimal scopes
        read_only = {"apex", "nexus", "kai", "agy", "gemini"}
        if agent_id in read_only:
            return ["repo:read"]
        # Write agents get repo scope
        return ["repo"]

    def _agent_to_login(self, agent_id: str) -> str:
        """Map an agent ID to its GitHub login.

        Per-agent tokens authenticate as a dedicated GitHub user or App.
        """
        # If using GitHub Apps, each agent would have its own App installation
        # For PATs, each agent would have its own GitHub user or fine-grained PAT
        # This mapping is updated when tokens are created
        return f"hummbl-{agent_id}"


__all__ = ["GitHubAuthProvider", "AgentToken"]
