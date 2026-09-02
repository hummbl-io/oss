"""HUMMBL Garage — Agent Performance Index, livery presets, watch faces, failure aesthetics.

Implements the automotive + horology + kintsugi metaphors from the synthesis spec:
- Agent Performance Index (API): 100-999 composite score with 6 sub-ratings
- Livery presets: Martini, Gulf, JPS, Rothmans, Marlboro, Castrol
- Watch face status: 4-layer display (analog hands, complications, dial finish, cockpit)
- Failure states: degraded (wabi-sabi), broken (kintsugi), dead (death screen)
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

__version__ = "0.1.0"

_DATA_DIR = Path(__file__).parent / "data"


def _load_data() -> dict[str, Any]:
    with open(_DATA_DIR / "garage.json") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass
class LiveryPreset:
    id: str
    name: str
    description: str
    primary: str
    secondary: str
    accent: str
    typography: str
    era: str
    origin: str
    paint_codes: list[str]


@dataclass
class CockpitPreset:
    id: str
    name: str
    description: str
    density: str
    font_scale: float
    panels_visible: int


@dataclass
class ManettinoMode:
    id: str
    name: str
    description: str


@dataclass
class WatchDialFinish:
    id: str
    trust_tier: str
    description: str


@dataclass
class WatchHandColor:
    state: str
    color: str
    description: str


@dataclass
class WatchComplication:
    id: str
    name: str
    description: str


@dataclass
class FailureState:
    id: str
    name: str
    visual_treatment: str
    operational_meaning: str
    color: str
    icon: str


@dataclass
class APIClass:
    id: str
    min: int
    max: int
    name: str
    description: str


@dataclass
class APISubRating:
    id: str
    name: str
    max: int
    description: str


# ---------------------------------------------------------------------------
# Agent Performance Index
# ---------------------------------------------------------------------------


@dataclass
class AgentPerformanceIndex:
    """Agent Performance Index — 100-999 composite score.

    6 sub-ratings (0-10 each), weighted to produce a 100-999 composite.
    Class: D (100-299) → C (300-499) → B (500-699) → A (700-799)
           → S1 (800-899) → S2 (900-949) → R (950-999)
    """

    reasoning_speed: float = 0.0
    tool_accuracy: float = 0.0
    context_efficiency: float = 0.0
    latency: float = 0.0
    safety: float = 0.0
    composite: float = 0.0

    @property
    def total(self) -> float:
        """Weighted composite score (100-999)."""
        weights = {
            "reasoning_speed": 0.20,
            "tool_accuracy": 0.25,
            "context_efficiency": 0.15,
            "latency": 0.10,
            "safety": 0.20,
            "composite": 0.10,
        }
        weighted = sum(getattr(self, k) * w for k, w in weights.items())
        # Scale 0-10 to 100-999
        return 100 + (weighted / 10.0) * 899

    @property
    def api_class(self) -> str:
        """Letter class (D, C, B, A, S1, S2, R)."""
        score = self.total
        if score >= 950:
            return "R"
        elif score >= 900:
            return "S2"
        elif score >= 800:
            return "S1"
        elif score >= 700:
            return "A"
        elif score >= 500:
            return "B"
        elif score >= 300:
            return "C"
        else:
            return "D"

    @property
    def api_score(self) -> int:
        """Integer API score (100-999)."""
        return int(round(self.total))

    def to_dict(self) -> dict[str, Any]:
        return {
            "reasoning_speed": self.reasoning_speed,
            "tool_accuracy": self.tool_accuracy,
            "context_efficiency": self.context_efficiency,
            "latency": self.latency,
            "safety": self.safety,
            "composite": self.composite,
            "api_score": self.api_score,
            "api_class": self.api_class,
        }


# ---------------------------------------------------------------------------
# Watch Face
# ---------------------------------------------------------------------------


@dataclass
class WatchFace:
    """4-layer watch face display for agent status.

    Layer 1: Analog hand position + color (state)
    Layer 2: Complication slots (token budget, trust tier, task, errors)
    Layer 3: Dial finish (trust tier encoding)
    Layer 4: Fleet cockpit (PFD six-pack)
    """

    state: str = "idle"  # working, waiting, blocked, completed, idle
    token_budget_pct: float = 100.0
    trust_tier: str = "MEDIUM"
    current_task: str = "idle"
    error_count: int = 0

    @property
    def hand_color(self) -> str:
        colors = {
            "working": "#2563EB",
            "waiting": "#D97706",
            "blocked": "#DC2626",
            "completed": "#22C55E",
            "idle": "#6B7280",
        }
        return colors.get(self.state, "#6B7280")

    @property
    def dial_finish(self) -> str:
        finishes = {
            "PROBATIONARY": "flat",
            "MEDIUM": "sunburst",
            "MEDIUM-HIGH": "guilloche",
            "TRUSTED": "enamel",
            "OWNER": "skelton",
        }
        return finishes.get(self.trust_tier, "flat")

    @property
    def hand_angle(self) -> float:
        """Analog hand angle in degrees (0=up, 90=right, etc.)."""
        # Map state to clock position
        positions = {
            "idle": 0,      # 12 o'clock
            "working": 90,  # 3 o'clock
            "waiting": 180, # 6 o'clock
            "blocked": 270, # 9 o'clock
            "completed": 45, # 1:30 — success
        }
        return positions.get(self.state, 0)

    def to_dict(self) -> dict[str, Any]:
        return {
            "state": self.state,
            "hand_color": self.hand_color,
            "hand_angle": self.hand_angle,
            "dial_finish": self.dial_finish,
            "complications": {
                "token_budget_pct": self.token_budget_pct,
                "trust_tier": self.trust_tier,
                "current_task": self.current_task,
                "error_count": self.error_count,
            },
        }


# ---------------------------------------------------------------------------
# Failure State
# ---------------------------------------------------------------------------


@dataclass
class FailureRecord:
    """A recorded failure event for the fleet ruin gallery."""

    agent_name: str
    failure_state: str  # degraded, broken, dead
    timestamp: str
    error_message: str
    recovery_action: str = ""
    successor: str = ""  # For 'dead' state — successor agent name
    correlation_key: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "agent_name": self.agent_name,
            "failure_state": self.failure_state,
            "timestamp": self.timestamp,
            "error_message": self.error_message,
            "recovery_action": self.recovery_action,
            "successor": self.successor,
            "correlation_key": self.correlation_key,
        }


# ---------------------------------------------------------------------------
# Garage (main access class)
# ---------------------------------------------------------------------------


class Garage:
    """HUMMBL Garage — access to livery presets, watch configs, failure states."""

    def __init__(self, data: dict[str, Any] | None = None):
        self._data = data or _load_data()

    def livery_presets(self) -> list[LiveryPreset]:
        return [
            LiveryPreset(
                id=p["id"], name=p["name"], description=p["description"],
                primary=p["primary"], secondary=p["secondary"], accent=p["accent"],
                typography=p["typography"], era=p["era"], origin=p["origin"],
                paint_codes=p["paint_codes"],
            )
            for p in self._data["presets"]
        ]

    def cockpit_presets(self) -> list[CockpitPreset]:
        return [
            CockpitPreset(
                id=c["id"], name=c["name"], description=c["description"],
                density=c["density"], font_scale=c["font_scale"],
                panels_visible=c["panels_visible"],
            )
            for c in self._data["cockpit_presets"]
        ]

    def manettino_modes(self) -> list[ManettinoMode]:
        return [
            ManettinoMode(m["id"], m["name"], m["description"])
            for m in self._data["manettino_modes"]
        ]

    def watch_dial_finishes(self) -> list[WatchDialFinish]:
        return [
            WatchDialFinish(d["id"], d["trust_tier"], d["description"])
            for d in self._data["watch_dial_finishes"]
        ]

    def watch_hand_colors(self) -> list[WatchHandColor]:
        return [
            WatchHandColor(h["state"], h["color"], h["description"])
            for h in self._data["watch_hand_colors"]
        ]

    def watch_complications(self) -> list[WatchComplication]:
        return [
            WatchComplication(c["id"], c["name"], c["description"])
            for c in self._data["watch_complications"]
        ]

    def failure_states(self) -> list[FailureState]:
        return [
            FailureState(
                id=f["id"], name=f["name"], visual_treatment=f["visual_treatment"],
                operational_meaning=f["operational_meaning"], color=f["color"],
                icon=f["icon"],
            )
            for f in self._data["failure_states"]
        ]

    def api_classes(self) -> list[APIClass]:
        return [
            APIClass(c["id"], c["min"], c["max"], c["name"], c["description"])
            for c in self._data["api_classes"]
        ]

    def api_subratings(self) -> list[APISubRating]:
        return [
            APISubRating(s["id"], s["name"], s["max"], s["description"])
            for s in self._data["api_subratings"]
        ]

    def upgrade_priority(self) -> list[str]:
        return self._data["upgrade_priority"]

    def find_livery(self, lid: str) -> LiveryPreset | None:
        for p in self.livery_presets():
            if p.id == lid:
                return p
        return None

    def find_failure_state(self, fid: str) -> FailureState | None:
        for f in self.failure_states():
            if f.id == fid:
                return f
        return None

    def find_dial_finish(self, trust_tier: str) -> WatchDialFinish | None:
        for d in self.watch_dial_finishes():
            if d.trust_tier == trust_tier:
                return d
        return None

    def classify_api(self, score: int) -> APIClass | None:
        for c in self.api_classes():
            if c.min <= score <= c.max:
                return c
        return None


# ---------------------------------------------------------------------------
# Fleet ruin gallery — failure archive
# ---------------------------------------------------------------------------


class RuinGallery:
    """Fleet ruin gallery — append-only archive of failure events.

    Each failure is recorded with its visual treatment (degraded/broken/dead),
    recovery action, and successor agent (for 'dead' state).
    """

    def __init__(self) -> None:
        self._records: list[FailureRecord] = []

    def record(
        self,
        agent_name: str,
        failure_state: str,
        timestamp: str,
        error_message: str,
        recovery_action: str = "",
        successor: str = "",
        correlation_key: str = "",
    ) -> FailureRecord:
        record = FailureRecord(
            agent_name=agent_name,
            failure_state=failure_state,
            timestamp=timestamp,
            error_message=error_message,
            recovery_action=recovery_action,
            successor=successor,
            correlation_key=correlation_key,
        )
        self._records.append(record)
        return record

    def all_records(self) -> list[FailureRecord]:
        return list(self._records)

    def by_agent(self, agent_name: str) -> list[FailureRecord]:
        return [r for r in self._records if r.agent_name == agent_name]

    def by_state(self, failure_state: str) -> list[FailureRecord]:
        return [r for r in self._records if r.failure_state == failure_state]

    def dead_agents(self) -> list[FailureRecord]:
        return self.by_state("dead")

    def degraded_agents(self) -> list[FailureRecord]:
        return self.by_state("degraded")

    def broken_agents(self) -> list[FailureRecord]:
        return self.by_state("broken")

    def to_dict(self) -> list[dict[str, Any]]:
        return [r.to_dict() for r in self._records]

    def __len__(self) -> int:
        return len(self._records)
