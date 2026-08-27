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

"""GitHub Auth Provider - pluggable per-agent authentication (gap-3).

Replaces the shared hummbl-dev token with per-agent authentication.
Operator decision (2026-08-27): build abstraction, decide later.

The abstraction supports three provider types:
- EnvVarAuthProvider: reads per-agent tokens from environment variables
  (default, works today with existing PATs)
- GitHubAppAuthProvider: uses GitHub App installation tokens (operator
  creates Apps per agent, better attribution and scoping)
- PATAuthProvider: uses fine-grained PATs per agent (faster to create)

All providers implement the same interface, so swapping is a config
change, not a code change. The pre-mutation gate (gap-1) uses the
resolved identity to attribute mutations to specific agents.

NIST 800-53 IA-2 (Identification and Authentication), AC-3 (Access
Enforcement), AU-2 (Audit Events).
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Protocol


@dataclass
class AgentCredential:
    """Credential for a specific agent's GitHub API access."""

    agent_id: str
    token: str
    token_type: str  # "pat", "github_app", "env_var"
    scopes: list[str] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.scopes is None:
            self.scopes = []

    def mask(self) -> str:
        """Return a masked version of the token for logging."""
        if len(self.token) <= 8:
            return "***"
        return f"{self.token[:4]}...{self.token[-4:]}"


class AuthProvider(Protocol):
    """Pluggable auth provider interface.

    All providers implement this interface. The gate calls resolve()
    to get the agent's credential before making GitHub API calls.
    """

    def resolve(self, agent_id: str) -> AgentCredential | None:
        """Resolve credentials for an agent.

        Returns AgentCredential if the agent has valid credentials,
        None if not found or not configured.
        """
        ...

    def list_configured_agents(self) -> list[str]:
        """List all agents that have credentials configured."""
        ...


class EnvVarAuthProvider:
    """Default auth provider ΓÇö reads per-agent tokens from env vars.

    Reads GITHUB_TOKEN_<AGENT_ID> from the environment. Agent IDs are
    uppercased and hyphens replaced with underscores.

    Example: agent_id="devin" -> GITHUB_TOKEN_DEVIN
             agent_id="claude-code" -> GITHUB_TOKEN_CLAUDE_CODE

    This is the simplest provider and works with existing PATs. The
    operator can set per-agent env vars without creating GitHub Apps.
    """

    def __init__(self, prefix: str = "GITHUB_TOKEN") -> None:
        self._prefix = prefix

    def _env_var_name(self, agent_id: str) -> str:
        return f"{self._prefix}_{agent_id.upper().replace('-', '_')}"

    def resolve(self, agent_id: str) -> AgentCredential | None:
        env_var = self._env_var_name(agent_id)
        token = os.environ.get(env_var, "")
        if not token:
            return None
        return AgentCredential(
            agent_id=agent_id,
            token=token,
            token_type="env_var",
            scopes=[],
        )

    def list_configured_agents(self) -> list[str]:
        agents: list[str] = []
        prefix = f"{self._prefix}_"
        for key in os.environ:
            if key.startswith(prefix) and key != prefix.rstrip("_"):
                # Convert env var name back to agent_id
                agent_id = key[len(prefix):].lower().replace("_", "-")
                agents.append(agent_id)
        return agents


class PATAuthProvider:
    """Fine-grained PAT auth provider ΓÇö reads from a config file.

    Reads a JSON config file mapping agent_ids to PATs. The operator
    creates fine-grained PATs per agent and places them in the config.

    Config format:
    {
      "devin": {"token": "github_pat_...", "scopes": ["repo"]},
      "codex": {"token": "github_pat_...", "scopes": ["repo"]}
    }
    """

    def __init__(self, config_path: str) -> None:
        import json
        from pathlib import Path

        self._config: dict[str, dict] = {}
        path = Path(config_path)
        if path.exists():
            with open(path, encoding="utf-8") as f:
                self._config = json.load(f)

    def resolve(self, agent_id: str) -> AgentCredential | None:
        entry = self._config.get(agent_id)
        if not entry or not entry.get("token"):
            return None
        return AgentCredential(
            agent_id=agent_id,
            token=entry["token"],
            token_type="pat",
            scopes=entry.get("scopes", []),
        )

    def list_configured_agents(self) -> list[str]:
        return list(self._config.keys())


class GitHubAppAuthProvider:
    """GitHub App installation auth provider.

    Uses a GitHub App's private key to generate installation tokens per
    agent. Each agent maps to a GitHub App installation. The operator
    creates GitHub Apps per agent and provides the App ID, installation
    ID, and private key path.

    Config format:
    {
      "devin": {
        "app_id": 123456,
        "installation_id": 789012,
        "private_key_path": "/path/to/devin-app-private-key.pem"
      }
    }

    This provider generates short-lived installation tokens (1 hour),
    which is more secure than long-lived PATs. Requires PyJWT for JWT
    generation (installed on demand).
    """

    def __init__(self, config_path: str) -> None:
        import json
        from pathlib import Path

        self._config: dict[str, dict] = {}
        path = Path(config_path)
        if path.exists():
            with open(path, encoding="utf-8") as f:
                self._config = json.load(f)

    def resolve(self, agent_id: str) -> AgentCredential | None:
        entry = self._config.get(agent_id)
        if not entry:
            return None

        token = self._generate_installation_token(entry)
        if not token:
            return None

        return AgentCredential(
            agent_id=agent_id,
            token=token,
            token_type="github_app",
            scopes=entry.get("scopes", ["repo"]),
        )

    def _generate_installation_token(self, config: dict) -> str | None:
        """Generate a GitHub App installation token.

        Creates a JWT from the App's private key, then exchanges it for
        an installation token via the GitHub API.
        """
        try:
            import json
            import time
            import urllib.request
            from pathlib import Path

            # PyJWT is optional ΓÇö import here so the module loads without it
            import jwt  # type: ignore[import-not-found]
        except ImportError:
            return None

        app_id = config.get("app_id")
        installation_id = config.get("installation_id")
        key_path = config.get("private_key_path")

        if not all([app_id, installation_id, key_path]):
            return None

        if not Path(key_path).exists():
            return None

        with open(key_path, "rb") as f:
            private_key = f.read()

        # GitHub App JWT: 10-minute max expiry
        payload = {
            "iat": int(time.time()),
            "exp": int(time.time()) + 600,
            "iss": app_id,
        }
        app_jwt = jwt.encode(payload, private_key, algorithm="RS256")

        # Exchange JWT for installation token
        url = f"https://api.github.com/app/installations/{installation_id}/access_tokens"
        req = urllib.request.Request(
            url,
            method="POST",
            headers={
                "Authorization": f"Bearer {app_jwt}",
                "Accept": "application/vnd.github+json",
            },
            data=b"{}",
        )
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read())
                return data.get("token")
        except Exception:
            return None

    def list_configured_agents(self) -> list[str]:
        return list(self._config.keys())


# --- Provider factory -------------------------------------------------------


def create_auth_provider(provider_type: str, config_path: str | None = None) -> AuthProvider:
    """Create an auth provider by type.

    Args:
        provider_type: "env_var", "pat", or "github_app"
        config_path: Path to config file (for pat and github_app providers)

    Returns:
        AuthProvider instance

    Raises:
        ValueError: If provider_type is unknown
    """
    if provider_type == "env_var":
        return EnvVarAuthProvider()
    elif provider_type == "pat":
        if not config_path:
            raise ValueError("PATAuthProvider requires config_path")
        return PATAuthProvider(config_path)
    elif provider_type == "github_app":
        if not config_path:
            raise ValueError("GitHubAppAuthProvider requires config_path")
        return GitHubAppAuthProvider(config_path)
    else:
        raise ValueError(f"Unknown auth provider type: {provider_type}")
