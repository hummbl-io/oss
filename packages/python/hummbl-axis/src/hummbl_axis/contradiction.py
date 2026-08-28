"""Contradiction model — the atomic unit Axis produces and tracks.

A contradiction is a mismatch between a claimed state and an observed state,
extracted from Atlas evidence cuts. Each contradiction has:
  - A stable ID (so cycles can detect "unchanged")
  - A scope (what surface the claim is about)
  - The claim (what the system says is true)
  - The observation (what Atlas actually found)
  - A severity (P0-P3)
  - A confidence (0.0-1.0, from Atlas evidence grade)
  - A volatility (low/medium/high — how fast this changes)
  - A cycle state (first_seen, last_seen, unchanged_cycles)
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class Contradiction:
    """A single mismatch between claimed and observed state.

    The ID is deterministic — same scope+claim+observation always produces the
    same ID. This is how cycle tracking detects "unchanged for N cycles."
    """

    scope: str
    claim: str
    observation: str
    severity: str  # P0, P1, P2, P3
    confidence: float  # 0.0-1.0
    volatility: str  # low, medium, high
    evidence_source: str  # path or URL to the Atlas evidence cut
    claim_source: str  # path or URL to the claimed state

    @property
    def id(self) -> str:
        """Deterministic ID from scope + claim + observation."""
        raw = f"{self.scope}|{self.claim}|{self.observation}"
        return "AX-" + hashlib.sha256(raw.encode("utf-8")).hexdigest()[:12]

    def to_dict(self) -> dict:
        d = asdict(self)
        d["id"] = self.id
        return d


@dataclass
class CycleState:
    """Tracks contradiction persistence across cycles for exit-condition logic.

    The loop exits when:
      - contradiction_rate < threshold (healthy, reduce cadence), OR
      - same contradiction persists 3 cycles unchanged (stuck, escalate)
    """

    cycle: int = 0
    seen: dict[str, int] = field(default_factory=dict)  # id → unchanged_cycles
    history: list[dict] = field(default_factory=list)

    def update(self, contradictions: Iterable[Contradiction]) -> list[Contradiction]:
        """Advance one cycle. Returns the contradictions with unchanged count attached."""
        current_ids = set()
        results = []
        for c in contradictions:
            current_ids.add(c.id)
            if c.id in self.seen:
                self.seen[c.id] += 1
            else:
                self.seen[c.id] = 0
            results.append((c, self.seen[c.id]))

        # Decay: contradictions not seen this cycle get stale
        stale = [cid for cid in self.seen if cid not in current_ids]
        for cid in stale:
            self.seen[cid] = -1  # marked stale, not deleted (lattice decay)

        self.cycle += 1
        self.history.append({
            "cycle": self.cycle,
            "contradiction_count": len(current_ids),
            "stale_count": len(stale),
            "unchanged_3plus": sum(1 for v in self.seen.values() if v >= 3),
        })
        return results

    def should_exit(self, threshold: float = 0.0) -> tuple[bool, str]:
        """Check loop exit condition.

        Returns (should_exit, reason).
        """
        stuck = [cid for cid, count in self.seen.items() if count >= 3]
        if stuck:
            return True, f"stuck: {len(stuck)} contradiction(s) unchanged for 3+ cycles"
        if self.cycle > 0:
            rate = len([v for v in self.seen.values() if v == 0])  # new this cycle
            if self.cycle >= 3 and rate == 0:
                return True, f"healthy: 0 new contradictions for 3 consecutive cycles"
        return False, ""

    def to_dict(self) -> dict:
        return {
            "cycle": self.cycle,
            "seen": dict(self.seen),
            "history": self.history,
        }

    @classmethod
    def from_dict(cls, d: dict) -> CycleState:
        state = cls()
        state.cycle = d.get("cycle", 0)
        state.seen = dict(d.get("seen", {}))
        state.history = list(d.get("history", []))
        return state

    def save(self, path: Path) -> None:
        path.write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")

    @classmethod
    def load(cls, path: Path) -> CycleState:
        if not path.exists():
            return cls()
        return cls.from_dict(json.loads(path.read_text(encoding="utf-8")))


# Severity ordering for prioritization
_SEVERITY_ORDER = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}


def prioritize(contradictions: list[Contradiction]) -> list[Contradiction]:
    """Sort contradictions by severity (P0 first), then confidence (high first)."""
    return sorted(
        contradictions,
        key=lambda c: (_SEVERITY_ORDER.get(c.severity, 9), -c.confidence),
    )
