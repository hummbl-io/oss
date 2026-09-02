"""Tests for the Atlas reader — markdown ledger parser and count differ."""

import json
from pathlib import Path

from hummbl_axis.atlas_reader import (
    diff_counts,
    extract_claimed_counts,
    load_json_inventory,
    parse_ledger_markdown,
    scan_ledger_directory,
)


# ─────────────────────────────────────────────────────────────
# Markdown ledger parser
# ─────────────────────────────────────────────────────────────

SAMPLE_LEDGER = """\
# HUMMBL Atlas — Atomic Reconciliation Ledger

## AR-LIFE-002

- **Scope:** Archived and forked repository lifecycle flags
- **Direct observation:** bif, agent-governance-demo are archived. T3MP3ST is a non-archived fork.
- **Inference:** Platform archival and fork flags identify lifecycle states.
- **Contradiction:** Archived bif retains recent maintenance evidence; the fork remains active despite being outside the canonical set.
- **Verdict:** Keep all classifications separate.
- **Confidence:** High for metadata; medium for ownership.
- **Volatility:** Medium-high.

## AR-DEPLOY-002

- **Scope:** Tier 0/1 deployment object refresh
- **Direct observation:** Successful latest deployments for mcp-server and hummbl-governance.
- **Inference:** Deployment state remains consistent.
- **Contradiction:** Successful deployment status coexists with an older docs revision.
- **Verdict:** Preserve deployment success as deployment-layer evidence only.
- **Confidence:** High for deployment IDs; low for runtime health.
- **Volatility:** High.

## AR-COV-001

- **Scope:** Organization census
- **Direct observation:** 204 deduplicated stable objects.
- **Inference:** Census is stable.
- **Contradiction:** None.
- **Verdict:** No action needed.
- **Confidence:** High.
- **Volatility:** Low.
"""


class TestParseLedgerMarkdown:
    def test_extracts_contradictions(self, tmp_path: Path):
        path = tmp_path / "hummbl-atlas-test.md"
        path.write_text(SAMPLE_LEDGER, encoding="utf-8")
        contradictions = parse_ledger_markdown(path)
        # AR-COV-001 has "Contradiction: None" → should be excluded
        assert len(contradictions) == 2

    def test_skips_none_contradictions(self, tmp_path: Path):
        path = tmp_path / "hummbl-atlas-test.md"
        path.write_text(SAMPLE_LEDGER, encoding="utf-8")
        contradictions = parse_ledger_markdown(path)
        scopes = [c.scope for c in contradictions]
        assert "Organization census" not in scopes

    def test_extracts_scope_and_observation(self, tmp_path: Path):
        path = tmp_path / "hummbl-atlas-test.md"
        path.write_text(SAMPLE_LEDGER, encoding="utf-8")
        contradictions = parse_ledger_markdown(path)
        c = contradictions[0]
        assert "lifecycle" in c.scope.lower()
        assert "archived" in c.observation.lower()

    def test_parses_confidence_high(self, tmp_path: Path):
        path = tmp_path / "hummbl-atlas-test.md"
        path.write_text(SAMPLE_LEDGER, encoding="utf-8")
        contradictions = parse_ledger_markdown(path)
        c = contradictions[0]
        assert c.confidence == 0.9  # "High"

    def test_parses_volatility(self, tmp_path: Path):
        path = tmp_path / "hummbl-atlas-test.md"
        path.write_text(SAMPLE_LEDGER, encoding="utf-8")
        contradictions = parse_ledger_markdown(path)
        volatilities = [c.volatility for c in contradictions]
        # "Medium-high" and "High" both contain "high" → parsed as "high"
        assert "high" in volatilities
        assert all(v == "high" for v in volatilities)

    def test_nonexistent_file_returns_empty(self, tmp_path: Path):
        result = parse_ledger_markdown(tmp_path / "nonexistent.md")
        assert result == []

    def test_scan_directory(self, tmp_path: Path):
        (tmp_path / "hummbl-atlas-a.md").write_text(SAMPLE_LEDGER, encoding="utf-8")
        (tmp_path / "hummbl-atlas-b.md").write_text(SAMPLE_LEDGER, encoding="utf-8")
        (tmp_path / "other.md").write_text("not an atlas file", encoding="utf-8")
        contradictions = scan_ledger_directory(tmp_path)
        assert len(contradictions) == 4  # 2 per file


# ─────────────────────────────────────────────────────────────
# JSON inventory
# ─────────────────────────────────────────────────────────────

class TestJsonInventory:
    def test_load_json_inventory(self, tmp_path: Path):
        data = {"name": "test", "stats": {"skills": 360, "agents": 76}}
        path = tmp_path / "inventory.json"
        path.write_text(json.dumps(data), encoding="utf-8")
        result = load_json_inventory(path)
        assert result["stats"]["skills"] == 360

    def test_load_nonexistent_returns_empty(self, tmp_path: Path):
        result = load_json_inventory(tmp_path / "nonexistent.json")
        assert result == {}

    def test_extract_claimed_counts_from_stats(self):
        inventory = {"stats": {"skills": 360, "agents": 76, "models": 120}}
        counts = extract_claimed_counts(inventory)
        assert counts["skills"] == 360
        assert counts["agents"] == 76
        assert counts["models"] == 120

    def test_extract_claimed_counts_from_top_level(self):
        inventory = {"skills": 360, "agents": 76}
        counts = extract_claimed_counts(inventory)
        assert counts["skills"] == 360

    def test_extract_skips_non_numeric(self):
        inventory = {"stats": {"skills": 360, "name": "test"}}
        counts = extract_claimed_counts(inventory)
        assert "skills" in counts
        assert "name" not in counts


# ─────────────────────────────────────────────────────────────
# Count diff — the skill-count contradiction (547/360/126)
# ─────────────────────────────────────────────────────────────

class TestDiffCounts:
    def test_skill_count_contradiction_547_vs_360(self):
        """The v0 target: 547 actual vs 360 manifest."""
        claimed = {"skills": 360}
        observed = {"skills": 547}
        contradictions = diff_counts(claimed, observed, "atlas.json", "manifest.json")
        assert len(contradictions) == 1
        c = contradictions[0]
        assert c.scope == "count:skills"
        assert "360" in c.claim
        assert "547" in c.observation

    def test_large_mismatch_gets_p1(self):
        """>20% mismatch → P1 severity."""
        claimed = {"skills": 360}
        observed = {"skills": 547}  # 52% over
        contradictions = diff_counts(claimed, observed)
        assert contradictions[0].severity == "P1"

    def test_small_mismatch_gets_p2(self):
        """<20% mismatch → P2 severity."""
        claimed = {"skills": 360}
        observed = {"skills": 370}  # 2.8% over
        contradictions = diff_counts(claimed, observed)
        assert contradictions[0].severity == "P2"

    def test_matching_counts_no_contradiction(self):
        claimed = {"skills": 360}
        observed = {"skills": 360}
        contradictions = diff_counts(claimed, observed)
        assert len(contradictions) == 0

    def test_claimed_but_not_observed(self):
        claimed = {"skills": 360}
        observed = {}
        contradictions = diff_counts(claimed, observed)
        assert len(contradictions) == 1
        assert "not observed" in contradictions[0].observation

    def test_observed_but_not_claimed(self):
        claimed = {}
        observed = {"skills": 547}
        contradictions = diff_counts(claimed, observed)
        assert len(contradictions) == 1
        assert "not declared" in contradictions[0].claim

    def test_multiple_counts(self):
        claimed = {"skills": 360, "agents": 76, "models": 120}
        observed = {"skills": 547, "agents": 76, "models": 120}
        contradictions = diff_counts(claimed, observed)
        assert len(contradictions) == 1  # only skills differ
        assert contradictions[0].scope == "count:skills"
