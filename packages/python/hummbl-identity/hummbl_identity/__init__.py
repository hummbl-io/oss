"""HUMMBL Identity — unified agent identity facade.

Integrates hummbl-design-tokens (colors), hummbl-heraldry (arms), and
hummbl-garage (performance/livery) into a single AgentIdentity object.

All three dependencies are optional — the module degrades gracefully if
any are missing, using fallback defaults.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

__version__ = "0.1.0"

try:
    from hummbl_design_tokens import TokenSystem
    _HAS_TOKENS = True
except ImportError:
    _HAS_TOKENS = False
    TokenSystem = None  # type: ignore

try:
    from hummbl_heraldry import ArmsGenerator
    _HAS_HERALDRY = True
except ImportError:
    _HAS_HERALDRY = False
    ArmsGenerator = None  # type: ignore

try:
    from hummbl_garage import Garage, AgentPerformanceIndex
    _HAS_GARAGE = True
except ImportError:
    _HAS_GARAGE = False
    Garage = None  # type: ignore
    AgentPerformanceIndex = None  # type: ignore

_FALLBACK_AGENTS = {
    "devin":       {"hex_dark": "#D63041", "role": "Primary Principal AI Agent",     "trust_tier": "MEDIUM-HIGH",  "monaspace_voice": "Neon"},
    "codex":       {"hex_dark": "#3B5BCC", "role": "Engineer / design partner",       "trust_tier": "TRUSTED",      "monaspace_voice": "Krypton"},
    "opencode":    {"hex_dark": "#A8C52E", "role": "Engineer parity",                 "trust_tier": "MEDIUM-HIGH",  "monaspace_voice": "Krypton"},
    "claude-code": {"hex_dark": "#D6306B", "role": "Memory, synthesis, coordination", "trust_tier": "TRUSTED",      "monaspace_voice": "Xenon"},
    "apex":        {"hex_dark": "#2E8AC9", "role": "Strategic assessor",              "trust_tier": "MEDIUM-HIGH",  "monaspace_voice": "Krypton"},
    "nexus":       {"hex_dark": "#2EC964", "role": "Canonical-surface scanner",       "trust_tier": "MEDIUM-HIGH",  "monaspace_voice": "Argon"},
    "hermes":      {"hex_dark": "#C530AD", "role": "Engineering, execution",          "trust_tier": "TRUSTED",      "monaspace_voice": "Krypton"},
    "pi":          {"hex_dark": "#C5A82E", "role": "Ops/remediation executor",         "trust_tier": "MEDIUM-HIGH",  "monaspace_voice": "Neon"},
    "kai":         {"hex_dark": "#D6583B", "role": "Reuben's AICOS",                  "trust_tier": "MEDIUM",       "monaspace_voice": "Xenon"},
    "gemini":      {"hex_dark": "#4D3BC9", "role": "Research lane (AIP)",             "trust_tier": "PROBATIONARY", "monaspace_voice": "Argon"},
    "agy":         {"hex_dark": "#68C52E", "role": "Antigravity CLI candidate",       "trust_tier": "MEDIUM",       "monaspace_voice": "Radon"},
}

_FALLBACK_TRUST_COLORS = {
    "OWNER": "#1E3A8A", "TRUSTED": "#15803D", "MEDIUM-HIGH": "#B45309",
    "MEDIUM": "#B45309", "PROBATIONARY": "#DC2626",
}


@dataclass
class AgentIdentity:
    name: str
    color: str = ""
    role: str = ""
    trust_tier: str = ""
    monaspace_voice: str = "Neon"
    blazon: str = ""
    shield_shape: str = ""
    field_tincture: str = ""
    api_score: int = 0
    api_class: str = ""
    watch_state: str = "idle"
    dial_finish: str = "flat"
    livery_preset: str = ""
    _raw: dict[str, Any] = field(default_factory=dict, repr=False)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name, "color": self.color, "role": self.role,
            "trust_tier": self.trust_tier, "monaspace_voice": self.monaspace_voice,
            "blazon": self.blazon, "shield_shape": self.shield_shape,
            "field_tincture": self.field_tincture, "api_score": self.api_score,
            "api_class": self.api_class, "watch_state": self.watch_state,
            "dial_finish": self.dial_finish, "livery_preset": self.livery_preset,
        }


class IdentitySystem:
    """Unified identity system — the spine connecting all design packages."""

    def __init__(self, tokens_path: str | Path | None = None):
        self._tokens = None
        self._heraldry_gen = None
        self._garage = None

        if _HAS_TOKENS:
            try:
                self._tokens = TokenSystem(tokens_path) if tokens_path else TokenSystem()
            except Exception:
                self._tokens = None

        if _HAS_HERALDRY:
            try:
                self._heraldry_gen = ArmsGenerator()
            except Exception:
                self._heraldry_gen = None

        if _HAS_GARAGE:
            try:
                self._garage = Garage()
            except Exception:
                self._garage = None

    def agent_names(self) -> list[str]:
        if self._tokens:
            return self._tokens.agent_names()
        return sorted(_FALLBACK_AGENTS.keys())

    def get_agent(self, name: str) -> AgentIdentity:
        if self._tokens:
            try:
                agent_data = self._tokens.agents[name]
                color = agent_data["hex_dark"]
                role = agent_data["role"]
                trust_tier = agent_data["trust_tier"]
                voice = agent_data.get("monaspace_voice", "Neon")
            except KeyError:
                agent_data = _FALLBACK_AGENTS.get(name, {})
                color = agent_data.get("hex_dark", "#6B7280")
                role = agent_data.get("role", "Unknown")
                trust_tier = agent_data.get("trust_tier", "PROBATIONARY")
                voice = agent_data.get("monaspace_voice", "Neon")
        else:
            agent_data = _FALLBACK_AGENTS.get(name, {})
            color = agent_data.get("hex_dark", "#6B7280")
            role = agent_data.get("role", "Unknown")
            trust_tier = agent_data.get("trust_tier", "PROBATIONARY")
            voice = agent_data.get("monaspace_voice", "Neon")

        identity = AgentIdentity(
            name=name, color=color, role=role,
            trust_tier=trust_tier, monaspace_voice=voice,
        )

        if self._heraldry_gen:
            try:
                arms = self._heraldry_gen.generate(name)
                identity.blazon = arms.blazon
                identity.shield_shape = arms.shield.name if hasattr(arms.shield, 'name') else str(arms.shield)
                identity.field_tincture = arms.field_tincture.name if hasattr(arms.field_tincture, 'name') else str(arms.field_tincture)
            except Exception:
                pass

        if self._garage:
            try:
                finish = self._garage.find_dial_finish(trust_tier)
                if finish:
                    identity.dial_finish = finish.id
            except Exception:
                pass

        return identity

    def get_agent_with_performance(
        self, name: str,
        reasoning_speed: float = 0, tool_accuracy: float = 0,
        context_efficiency: float = 0, latency: float = 0,
        safety: float = 0, composite: float = 0,
    ) -> AgentIdentity:
        identity = self.get_agent(name)
        if _HAS_GARAGE and AgentPerformanceIndex:
            api = AgentPerformanceIndex(
                reasoning_speed=reasoning_speed, tool_accuracy=tool_accuracy,
                context_efficiency=context_efficiency, latency=latency,
                safety=safety, composite=composite,
            )
            identity.api_score = api.api_score
            identity.api_class = api.api_class
        return identity

    def all_agents(self) -> list[AgentIdentity]:
        return [self.get_agent(name) for name in self.agent_names()]

    def trust_tier_color(self, tier: str) -> str:
        if self._tokens:
            try:
                return self._tokens.trust_tier_color(tier)
            except KeyError:
                pass
        return _FALLBACK_TRUST_COLORS.get(tier, "#6B7280")

    def agent_color(self, name: str) -> str:
        if self._tokens:
            try:
                return self._tokens.agent_color(name)
            except KeyError:
                pass
        return _FALLBACK_AGENTS.get(name, {}).get("hex_dark", "#6B7280")

    def to_json(self) -> str:
        return json.dumps([a.to_dict() for a in self.all_agents()], indent=2)

    @property
    def has_tokens(self) -> bool:
        return self._tokens is not None

    @property
    def has_heraldry(self) -> bool:
        return self._heraldry_gen is not None

    @property
    def has_garage(self) -> bool:
        return self._garage is not None

    @property
    def integration_status(self) -> dict[str, bool]:
        return {
            "design_tokens": self.has_tokens,
            "heraldry": self.has_heraldry,
            "garage": self.has_garage,
        }
