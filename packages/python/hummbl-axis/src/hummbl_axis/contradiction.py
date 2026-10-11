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
from collections.abc import Iterable
from dataclasses import asdict, dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class Contradiction:
    """A single mismatch between claimed and observed state.

    The ID is deterministic — same scope+claim+observation always produces the
    same ID. Uses JSON array serialization to prevent delimiter collision attacks.
    """

    scope: str
    claim: str
    observation: str
    severity: str  # P0, P1, P2, P3
    confidence: float  # 0.0-1.0
    volatility: str  # low, medium, high
    evidence_source: str  # path or URL to the Atlas evidence cut
    claim_source: str  # path or URL to the claimed state
    status: str = "ACTIVE"  # ACTIVE, EXPECTANT, ACCEPTED_DEBT

    @property
    def id(self) -> str:
        """Deterministic ID from scope + claim + observation via JSON array."""
        raw = json.dumps([self.scope, self.claim, self.observation], separators=(",", ":"))
        return "AX-" + hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]

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
    consecutive_healthy: int = 0
    flaps: dict[str, int] = field(default_factory=dict)  # id → flap penalty count

    def update(self, contradictions: Iterable[Contradiction]) -> list[tuple[Contradiction, int]]:
        """Advance one cycle. Returns the contradictions with unchanged count attached."""
        current_ids = set()
        results = []
        new_count = 0
        for c in contradictions:
            current_ids.add(c.id)
            if c.id in self.seen:
                if self.seen[c.id] == -1:
                    # Flapping re-appearance: was stale, now back
                    self.flaps[c.id] = self.flaps.get(c.id, 0) + 1
                    self.seen[c.id] = 1 + self.flaps[c.id]
                else:
                    self.seen[c.id] += 1
            else:
                self.seen[c.id] = 0
                new_count += 1
            results.append((c, self.seen[c.id]))

        # Decay: contradictions not seen this cycle get stale
        stale = [cid for cid in self.seen if cid not in current_ids and self.seen[cid] != -1]
        for cid in stale:
            self.seen[cid] = -1  # marked stale, not deleted (lattice decay)

        self.cycle += 1

        # Track consecutive healthy cycles (0 new and 0 active contradictions)
        if len(current_ids) == 0 or new_count == 0:
            self.consecutive_healthy += 1
        else:
            self.consecutive_healthy = 0

        self.history.append(
            {
                "cycle": self.cycle,
                "contradiction_count": len(current_ids),
                "stale_count": len(stale),
                "new_count": new_count,
                "consecutive_healthy": self.consecutive_healthy,
                "unchanged_3plus": sum(1 for v in self.seen.values() if v >= 3),
            }
        )
        return results

    def should_exit(self, threshold: float = 0.0) -> tuple[bool, str]:
        """Check loop exit condition.

        Returns (should_exit, reason).
        """
        stuck = [cid for cid, count in self.seen.items() if count >= 3]
        if stuck:
            return True, f"stuck: {len(stuck)} contradiction(s) unchanged for 3+ cycles"
        if self.cycle > 0 and self.consecutive_healthy >= 3:
            return True, "healthy: 0 new contradictions for 3 consecutive cycles"
        return False, ""

    def to_dict(self) -> dict:
        return {
            "cycle": self.cycle,
            "seen": dict(self.seen),
            "history": self.history,
            "consecutive_healthy": self.consecutive_healthy,
            "flaps": dict(self.flaps),
        }

    @classmethod
    def from_dict(cls, d: dict) -> CycleState:
        state = cls()
        state.cycle = d.get("cycle", 0)
        state.seen = dict(d.get("seen", {}))
        state.history = list(d.get("history", []))
        state.consecutive_healthy = d.get("consecutive_healthy", 0)
        state.flaps = dict(d.get("flaps", {}))
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
