"""Tests for the Contradiction model and CycleState loop tracking."""

import json
from pathlib import Path

from hummbl_axis.contradiction import Contradiction, CycleState, prioritize


# ─────────────────────────────────────────────────────────────
# Contradiction
# ─────────────────────────────────────────────────────────────

class TestContradiction:
    def test_id_is_deterministic(self):
        c = Contradiction(
            scope="count:skills",
            claim="declared: 360",
            observation="observed: 547",
            severity="P2",
            confidence=0.85,
            volatility="medium",
            evidence_source="atlas.json",
            claim_source="manifest.json",
        )
        c2 = Contradiction(
            scope="count:skills",
            claim="declared: 360",
            observation="observed: 547",
            severity="P2",
            confidence=0.85,
            volatility="medium",
            evidence_source="atlas.json",
            claim_source="manifest.json",
        )
        assert c.id == c2.id
        assert c.id.startswith("AX-")
        assert len(c.id) == 15  # "AX-" + 12 hex chars

    def test_id_differs_on_different_scope(self):
        c1 = Contradiction("scope-a", "claim", "obs", "P2", 0.5, "low", "", "")
        c2 = Contradiction("scope-b", "claim", "obs", "P2", 0.5, "low", "", "")
        assert c1.id != c2.id

    def test_id_differs_on_different_observation(self):
        c1 = Contradiction("scope", "claim", "obs-a", "P2", 0.5, "low", "", "")
        c2 = Contradiction("scope", "claim", "obs-b", "P2", 0.5, "low", "", "")
        assert c1.id != c2.id

    def test_to_dict_includes_id(self):
        c = Contradiction("scope", "claim", "obs", "P2", 0.5, "low", "src", "claim")
        d = c.to_dict()
        assert d["id"] == c.id
        assert d["scope"] == "scope"
        assert d["claim"] == "claim"

    def test_skill_count_contradiction(self):
        """The v0 target: 547 actual vs 360 manifest vs 126 lean-set."""
        c = Contradiction(
            scope="count:skills",
            claim="declared: 360",
            observation="observed: 547",
            severity="P2",
            confidence=0.85,
            volatility="medium",
            evidence_source="atlas-inventory.json",
            claim_source="skill-manifest.json",
        )
        assert c.scope == "count:skills"
        assert "360" in c.claim
        assert "547" in c.observation


# ─────────────────────────────────────────────────────────────
# Prioritization
# ─────────────────────────────────────────────────────────────

class TestPrioritize:
    def test_p0_before_p2(self):
        c_p0 = Contradiction("s", "c", "o", "P0", 0.5, "low", "", "")
        c_p2 = Contradiction("s", "c", "o", "P2", 0.9, "low", "", "")
        result = prioritize([c_p2, c_p0])
        assert result[0] == c_p0

    def test_higher_confidence_first_within_same_severity(self):
        c_low = Contradiction("s", "c", "o", "P2", 0.3, "low", "", "")
        c_high = Contradiction("s", "c", "o", "P2", 0.9, "low", "", "")
        result = prioritize([c_low, c_high])
        assert result[0] == c_high


# ─────────────────────────────────────────────────────────────
# CycleState — loop tracking and exit conditions
# ─────────────────────────────────────────────────────────────

class TestCycleState:
    def test_first_cycle_sets_unchanged_to_zero(self):
        state = CycleState()
        c = Contradiction("s", "c", "o", "P2", 0.5, "low", "", "")
        results = state.update([c])
        assert state.cycle == 1
        assert results[0][1] == 0  # unchanged = 0 on first sight

    def test_same_contradiction_increments_unchanged(self):
        state = CycleState()
        c = Contradiction("s", "c", "o", "P2", 0.5, "low", "", "")
        state.update([c])
        state.update([c])
        state.update([c])
        assert state.seen[c.id] == 2  # seen 3 times, unchanged 2

    def test_exit_when_stuck_3_cycles(self):
        state = CycleState()
        c = Contradiction("s", "c", "o", "P2", 0.5, "low", "", "")
        # 4 cycles with same contradiction
        for _ in range(4):
            state.update([c])
        should_exit, reason = state.should_exit()
        assert should_exit
        assert "stuck" in reason

    def test_exit_when_healthy_0_new_for_3_cycles(self):
        state = CycleState()
        # Cycle 1: one contradiction, then it gets resolved
        c = Contradiction("s", "c", "o", "P2", 0.5, "low", "", "")
        state.update([c])
        # Cycles 2-4: no contradictions (resolved)
        state.update([])
        state.update([])
        state.update([])
        should_exit, reason = state.should_exit()
        assert should_exit
        assert "healthy" in reason

    def test_no_exit_when_new_contradictions_appear(self):
        state = CycleState()
        c1 = Contradiction("s1", "c", "o", "P2", 0.5, "low", "", "")
        state.update([c1])
        c2 = Contradiction("s2", "c", "o", "P2", 0.5, "low", "", "")
        state.update([c2])
        should_exit, _ = state.should_exit()
        assert not should_exit

    def test_stale_contradictions_marked_not_deleted(self):
        state = CycleState()
        c = Contradiction("s", "c", "o", "P2", 0.5, "low", "", "")
        state.update([c])
        state.update([])  # c not seen → stale
        assert state.seen[c.id] == -1  # stale, not deleted

    def test_save_and_load_roundtrip(self, tmp_path: Path):
        state = CycleState()
        c = Contradiction("s", "c", "o", "P2", 0.5, "low", "", "")
        state.update([c])
        state.update([c])

        path = tmp_path / "state.json"
        state.save(path)
        loaded = CycleState.load(path)

        assert loaded.cycle == state.cycle
        assert loaded.seen == state.seen
        assert loaded.history == state.history

    def test_load_nonexistent_returns_fresh(self, tmp_path: Path):
        state = CycleState.load(tmp_path / "nonexistent.json")
        assert state.cycle == 0
        assert state.seen == {}
