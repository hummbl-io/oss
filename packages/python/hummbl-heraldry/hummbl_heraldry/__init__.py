"""HUMMBL Procedural Heraldic Identity System.

Generates deterministic heraldic arms from agent names using SHA-256.
Implements the 7-layer identity system from the heraldry research synthesis.

Layer 0: Fleet/host heraldry (manually designed, fixed)
Layer 1: Base arms (SHA-256(agent_name) → shield, tincture, division, ordinary, charge)
Layer 2: Trust tier cadency mark
Layer 3: Role badge
Layer 4: Host patch
Layer 5: Skill tabs (append-only)
Layer 6: Runtime status (ephemeral)
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

__version__ = "0.1.0"

_DATA_DIR = Path(__file__).parent / "data"


def _load_grammar() -> dict[str, Any]:
    """Load the heraldic grammar vocabulary."""
    with open(_DATA_DIR / "grammar.json") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass
class Tincture:
    id: str
    name: str
    category: str  # metal, color, fur
    hex: str
    description: str


@dataclass
class HeraldicElement:
    id: str
    name: str
    blazon: str
    description: str


@dataclass
class Charge:
    id: str
    name: str
    blazon: str
    description: str


@dataclass
class CadencyMark:
    id: str
    trust_tier: str
    blazon: str
    description: str


@dataclass
class RoleBadge:
    id: str
    role: str
    icon: str
    description: str


@dataclass
class HostPatch:
    id: str
    name: str
    description: str


@dataclass
class ICSFlag:
    bus_type: str
    ics_letter: str | None
    ics_name: str
    color_scheme: str


@dataclass
class AgentArms:
    """Complete heraldic achievement for an agent."""

    agent_name: str
    shield: HeraldicElement
    field_tincture: Tincture
    division: HeraldicElement
    division_tincture: Tincture | None
    ordinary: HeraldicElement
    ordinary_tincture: Tincture | None
    charge: Charge
    charge_tincture: Tincture | None
    cadency: CadencyMark | None = None
    role_badge: RoleBadge | None = None
    host_patch: HostPatch | None = None
    skill_tabs: list[str] = field(default_factory=list)
    blazon: str = ""
    hash: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary for JSON output."""
        return {
            "agent_name": self.agent_name,
            "hash": self.hash,
            "shield": self.shield.id,
            "field_tincture": self.field_tincture.id,
            "division": self.division.id,
            "division_tincture": self.division_tincture.id if self.division_tincture else None,
            "ordinary": self.ordinary.id,
            "ordinary_tincture": self.ordinary_tincture.id if self.ordinary_tincture else None,
            "charge": self.charge.id,
            "charge_tincture": self.charge_tincture.id if self.charge_tincture else None,
            "cadency": self.cadency.id if self.cadency else None,
            "role_badge": self.role_badge.id if self.role_badge else None,
            "host_patch": self.host_patch.id if self.host_patch else None,
            "skill_tabs": self.skill_tabs,
            "blazon": self.blazon,
        }


# ---------------------------------------------------------------------------
# Grammar access
# ---------------------------------------------------------------------------


class Grammar:
    """Heraldic grammar vocabulary loaded from JSON."""

    def __init__(self, data: dict[str, Any] | None = None):
        self._data = data or _load_grammar()

    def shield_shapes(self) -> list[HeraldicElement]:
        return [
            HeraldicElement(s["id"], s["name"], "", s["description"])
            for s in self._data["shield_shapes"]
        ]

    def tinctures(self) -> list[Tincture]:
        return [
            Tincture(t["id"], t["name"], t["category"], t["hex"], t["description"])
            for t in self._data["tinctures"]
        ]

    def divisions(self) -> list[HeraldicElement]:
        return [
            HeraldicElement(d["id"], d["name"], d["blazon"], d["description"])
            for d in self._data["divisions"]
        ]

    def ordinaries(self) -> list[HeraldicElement]:
        return [
            HeraldicElement(o["id"], o["name"], o["blazon"], o["description"])
            for o in self._data["ordinaries"]
        ]

    def charges(self) -> list[Charge]:
        return [
            Charge(c["id"], c["name"], c["blazon"], c["description"])
            for c in self._data["charges"]
        ]

    def cadency_marks(self) -> list[CadencyMark]:
        return [
            CadencyMark(c["id"], c["trust_tier"], c["blazon"], c["description"])
            for c in self._data["cadency_marks"]
        ]

    def role_badges(self) -> list[RoleBadge]:
        return [
            RoleBadge(r["id"], r["role"], r["icon"], r["description"])
            for r in self._data["role_badges"]
        ]

    def host_patches(self) -> list[HostPatch]:
        return [
            HostPatch(h["id"], h["name"], h["description"])
            for h in self._data["host_patches"]
        ]

    def ics_flags(self) -> list[ICSFlag]:
        return [
            ICSFlag(f["bus_type"], f["ics_letter"], f["ics_name"], f["color_scheme"])
            for f in self._data["ics_flags"]
        ]

    def fleet_arms(self) -> dict[str, Any]:
        return self._data["fleet_arms"]

    def find_tincture(self, tid: str) -> Tincture | None:
        for t in self.tinctures():
            if t.id == tid:
                return t
        return None

    def find_cadency(self, trust_tier: str) -> CadencyMark | None:
        for c in self.cadency_marks():
            if c.trust_tier == trust_tier:
                return c
        return None

    def find_role_badge(self, role: str) -> RoleBadge | None:
        for r in self.role_badges():
            if r.role == role:
                return r
        return None

    def find_host_patch(self, host_id: str) -> HostPatch | None:
        for h in self.host_patches():
            if h.id == host_id:
                return h
        return None


# ---------------------------------------------------------------------------
# Rule of tincture
# ---------------------------------------------------------------------------

_METAL_CATEGORIES = {"metal", "fur"}


def _is_metal(tincture: Tincture) -> bool:
    """Metals and furs can go on colors and vice versa."""
    return tincture.category in _METAL_CATEGORIES


def _pick_contrasting(
    field_tincture: Tincture,
    tinctures: list[Tincture],
    seed_byte: int,
) -> Tincture:
    """Pick a tincture that obeys the rule of tincture.

    Metal on color, color on metal. Furs are exempt (can go on either).
    If the field is a fur, pick any non-fur tincture.
    """
    field_is_metal = _is_metal(field_tincture)

    # Filter tinctures that obey the rule
    if field_tincture.category == "fur":
        # Furs can take any charge — pick from metals and colors
        candidates = [t for t in tinctures if t.category in ("metal", "color")]
    else:
        # Metal field → color charge; color field → metal charge
        candidates = [
            t for t in tinctures
            if t.category != "fur" and _is_metal(t) != field_is_metal
        ]

    if not candidates:
        # Fallback: if no valid candidates (shouldn't happen), use any
        candidates = tinctures

    return candidates[seed_byte % len(candidates)]


# ---------------------------------------------------------------------------
# Generator
# ---------------------------------------------------------------------------


class ArmsGenerator:
    """Procedural heraldic arms generator.

    Uses SHA-256(agent_name) to deterministically derive all heraldic
    parameters. Same name → same arms, forever.
    """

    def __init__(self, grammar: Grammar | None = None):
        self.grammar = grammar or Grammar()
        self._tinctures = self.grammar.tinctures()
        self._shapes = self.grammar.shield_shapes()
        self._divisions = self.grammar.divisions()
        self._ordinaries = self.grammar.ordinaries()
        self._charges = self.grammar.charges()

    def generate(
        self,
        agent_name: str,
        trust_tier: str | None = None,
        role: str | None = None,
        host: str | None = None,
        skill_tabs: list[str] | None = None,
    ) -> AgentArms:
        """Generate heraldic arms for an agent.

        Args:
            agent_name: The agent's canonical name (e.g. "devin")
            trust_tier: Trust tier for cadency (OWNER, TRUSTED, MEDIUM-HIGH, MEDIUM, PROBATIONARY)
            role: Agent role for badge (coordinator, engineer, memory, scanner, research, ops)
            host: Host ID for patch (delta, anvil, hummbl-vps, beachhead, slate)
            skill_tabs: List of earned skill qualifications

        Returns:
            AgentArms with all heraldic parameters and blazon string
        """
        # SHA-256 hash of agent name
        hash_bytes = hashlib.sha256(agent_name.encode("utf-8")).digest()
        hash_hex = hash_bytes.hex()

        # Layer 1: Base arms from hash bytes
        shield = self._shapes[hash_bytes[0] % len(self._shapes)]
        field_tincture = self._tinctures[hash_bytes[1] % len(self._tinctures)]
        division = self._divisions[hash_bytes[2] % len(self._divisions)]

        # Division tincture (if not solid) — must contrast with field
        if division.id != "solid":
            division_tincture = _pick_contrasting(
                field_tincture, self._tinctures, hash_bytes[3]
            )
        else:
            division_tincture = None

        ordinary = self._ordinaries[hash_bytes[4] % len(self._ordinaries)]

        # Ordinary tincture — must contrast with field
        if ordinary.id != "none":
            ordinary_tincture = _pick_contrasting(
                field_tincture, self._tinctures, hash_bytes[5]
            )
        else:
            ordinary_tincture = None

        # Charge — use 2 bytes for larger charge space
        charge_idx = (hash_bytes[6] << 8 | hash_bytes[7]) % len(self._charges)
        charge = self._charges[charge_idx]

        # Charge tincture — must contrast with field
        if charge.id != "none":
            charge_tincture = _pick_contrasting(
                field_tincture, self._tinctures, hash_bytes[8]
            )
        else:
            charge_tincture = None

        # Layer 2: Trust tier cadency
        cadency = None
        if trust_tier:
            cadency = self.grammar.find_cadency(trust_tier)

        # Layer 3: Role badge
        role_badge = None
        if role:
            role_badge = self.grammar.find_role_badge(role)

        # Layer 4: Host patch
        host_patch = None
        if host:
            host_patch = self.grammar.find_host_patch(host)

        # Layer 5: Skill tabs
        skill_tabs = skill_tabs or []

        # Generate blazon string
        blazon = self._build_blazon(
            field_tincture, division, division_tincture,
            ordinary, ordinary_tincture,
            charge, charge_tincture,
            cadency,
        )

        return AgentArms(
            agent_name=agent_name,
            shield=shield,
            field_tincture=field_tincture,
            division=division,
            division_tincture=division_tincture,
            ordinary=ordinary,
            ordinary_tincture=ordinary_tincture,
            charge=charge,
            charge_tincture=charge_tincture,
            cadency=cadency,
            role_badge=role_badge,
            host_patch=host_patch,
            skill_tabs=skill_tabs,
            blazon=blazon,
            hash=hash_hex,
        )

    def _build_blazon(
        self,
        field: Tincture,
        division: HeraldicElement,
        division_tincture: Tincture | None,
        ordinary: HeraldicElement,
        ordinary_tincture: Tincture | None,
        charge: Charge,
        charge_tincture: Tincture | None,
        cadency: CadencyMark | None,
    ) -> str:
        """Build a heraldic blazon string from the arms components.

        Format: "[Division] [Field Tincture], [Ordinary] [Ordinary Tincture],
                [Charge] [Charge Tincture] [Cadency]"
        """
        parts: list[str] = []

        # Field description
        if division.id == "solid":
            parts.append(field.name)
        else:
            # "per pale Azure and Argent" or "quarterly Or and Gules"
            if division_tincture and division_tincture.id != field.id:
                parts.append(f"{division.blazon} {field.name} and {division_tincture.name}")
            else:
                parts.append(f"{division.blazon} {field.name}")

        # Ordinary
        if ordinary.id != "none" and ordinary_tincture:
            parts.append(f"{ordinary.blazon} {ordinary_tincture.name}")

        # Charge
        if charge.id != "none" and charge_tincture:
            parts.append(f"{charge.blazon} {charge_tincture.name}")

        # Cadency
        if cadency and cadency.id != "none":
            parts.append(cadency.blazon)

        # Join with commas, capitalize first letter
        blazon = ", ".join(parts)
        if blazon:
            blazon = blazon[0].upper() + blazon[1:]

        return blazon


# ---------------------------------------------------------------------------
# Fleet roster — all 11 agents
# ---------------------------------------------------------------------------

# Agent metadata from the fleet roster
AGENTS = [
    {"name": "devin", "trust": "MEDIUM-HIGH", "role": "coordinator", "host": "delta"},
    {"name": "codex", "trust": "TRUSTED", "role": "engineer", "host": "delta"},
    {"name": "opencode", "trust": "MEDIUM-HIGH", "role": "engineer", "host": "delta"},
    {"name": "claude-code", "trust": "TRUSTED", "role": "memory", "host": "delta"},
    {"name": "apex", "trust": "MEDIUM-HIGH", "role": "scanner", "host": "delta"},
    {"name": "nexus", "trust": "MEDIUM-HIGH", "role": "scanner", "host": "delta"},
    {"name": "hermes", "trust": "TRUSTED", "role": "engineer", "host": "delta"},
    {"name": "pi", "trust": "MEDIUM-HIGH", "role": "ops", "host": "delta"},
    {"name": "kai", "trust": "MEDIUM", "role": "coordinator", "host": "delta"},
    {"name": "gemini", "trust": "PROBATIONARY", "role": "research", "host": "delta"},
    {"name": "agy", "trust": "MEDIUM", "role": "engineer", "host": "delta"},
]


def generate_all_arms() -> dict[str, AgentArms]:
    """Generate arms for all 11 fleet agents."""
    gen = ArmsGenerator()
    return {
        a["name"]: gen.generate(
            agent_name=a["name"],
            trust_tier=a["trust"],
            role=a["role"],
            host=a["host"],
        )
        for a in AGENTS
    }
