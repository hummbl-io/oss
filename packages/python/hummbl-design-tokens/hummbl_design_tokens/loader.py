"""Token loader and system facade for HUMMBL design tokens.

Loads the canonical tokens.yaml and provides typed access to all token groups.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml

_DATA_DIR = Path(__file__).parent / "data"
_TOKENS_FILE = _DATA_DIR / "tokens.yaml"


def load_tokens(path: str | Path | None = None) -> dict[str, Any]:
    """Load the canonical tokens.yaml file.

    Args:
        path: Override path to a tokens file. If None, uses the bundled default.

    Returns:
        Parsed YAML as a nested dict.
    """
    p = Path(path) if path else _TOKENS_FILE
    with open(p) as f:
        return yaml.safe_load(f)


class TokenSystem:
    """High-level access to the HUMMBL design token system.

    Loads tokens on init and provides convenience properties for each token group.
    """

    def __init__(self, path: str | Path | None = None):
        self._tokens = load_tokens(path)
        self.meta = self._tokens["meta"]
        self.surfaces = self._tokens["surfaces"]
        self.agents = self._tokens["agents"]
        self.trust_tiers = self._tokens["trust_tiers"]
        self.bus_types = self._tokens["bus_types"]
        self.status = self._tokens["status"]
        self.typography = self._tokens["typography"]
        self.livery = self._tokens["livery"]
        self.heraldry = self._tokens["heraldry"]
        self.terminal = self._tokens["terminal"]
        self.accessibility = self._tokens["accessibility"]

    @property
    def version(self) -> str:
        return self.meta["version"]

    @property
    def canonical_surface(self) -> str:
        return self.meta["canonical_surface"]

    def agent_names(self) -> list[str]:
        """Return sorted list of agent names."""
        return sorted(self.agents.keys())

    def agent_color(self, name: str, dark: bool = True) -> str:
        """Get the hex color for an agent.

        Args:
            name: Agent name (e.g. 'devin').
            dark: If True, return dark-mode variant. Otherwise light-mode.
        """
        agent = self.agents[name]
        return agent["hex_dark"] if dark else agent["hex_light"]

    def agent_livery(self, name: str) -> dict[str, Any]:
        """Build a livery config dict for an agent."""
        agent = self.agents[name]
        return {
            "agent": name,
            "livery": {
                "base": self.livery["base"],
                "accent": agent["hex_dark"],
                "pattern": "solid",
                "finish": "matte",
                "insignia": {
                    "tier": agent["trust_tier"],
                    "color": self.trust_tiers[agent["trust_tier"]]["hex"],
                    "icon": "shield",
                },
                "heraldic_arms": agent.get("heraldic_arms", "generated"),
                "type_voice": agent.get("monaspace_voice", "Neon"),
            },
        }

    def bus_type(self, msg_type: str) -> dict[str, Any]:
        """Get the full visual encoding for a bus message type."""
        return self.bus_types[msg_type]

    def status_color(self, status_name: str) -> str:
        """Get the hex color for a status (HEALTHY/DEGRADED/CRITICAL)."""
        return self.status[status_name]["hex"]

    def trust_tier_color(self, tier: str) -> str:
        """Get the hex color for a trust tier."""
        return self.trust_tiers[tier]["hex"]
