#!/usr/bin/env python3
"""Tests for the Research Integrity Artifact Maturity validator."""

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from validate import validate_record

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"


def load_fixture(name: str) -> dict:
    with open(FIXTURES_DIR / name, encoding="utf-8") as f:
        return json.load(f)


class TestValidRecords(unittest.TestCase):
    def test_valid_internal_report(self):
        errors = validate_record(load_fixture("valid-internal-report.json"))
        self.assertEqual(errors, [], f"Expected no errors: {errors}")


class TestInvalidRecords(unittest.TestCase):
    def test_invalid_novelty_overclaim(self):
        """Novelty claims with R1/R2 FAIL and no prior-art review."""
        errors = validate_record(load_fixture("invalid-novelty-overclaim.json"))
        self.assertTrue(len(errors) > 0, f"Expected errors: {errors}")
        self.assertTrue(any("prior_art_review" in e for e in errors),
                        f"Expected prior_art_review error: {errors}")
        self.assertTrue(any("R1" in e for e in errors),
                        f"Expected R1 error: {errors}")

    def test_invalid_ai_undisclosed(self):
        """R7 FAIL with no material assistance listed."""
        errors = validate_record(load_fixture("invalid-ai-undisclosed.json"))
        self.assertTrue(any("R7" in e for e in errors),
                        f"Expected R7 error: {errors}")

    def test_invalid_skip_maturity(self):
        """PEER_REVIEWED without review completed or reproducibility."""
        errors = validate_record(load_fixture("invalid-skip-maturity.json"))
        self.assertTrue(any("PEER_REVIEWED" in e for e in errors),
                        f"Expected PEER_REVIEWED error: {errors}")
        self.assertTrue(any("review_completed" in e for e in errors),
                        f"Expected review_completed error: {errors}")
        self.assertTrue(any("methods" in e for e in errors),
                        f"Expected methods error: {errors}")


class TestSemanticRules(unittest.TestCase):
    def _base_record(self) -> dict:
        return {
            "schema_version": "research_integrity_artifact.v0.1",
            "artifact_id": "test-001",
            "title": "Test Artifact",
            "maturity_state": "IDEA",
            "claim_postures": [],
            "risk_checks": [],
            "authorship": {
                "human_authors": [{"name": "Test", "responsibility": "all", "orcid": None}],
                "agent_contributions": []
            },
            "ai_use_disclosure": {
                "material_assistance": [],
                "citation_fabrication_check": True
            },
            "independent_review": {
                "reviewer_not_author": False,
                "review_completed": False,
                "reviewer_disagreements": [],
                "unresolved_objections": []
            },
            "reproducibility_manifest": {
                "methods_preserved": False,
                "versions_preserved": False,
                "negative_results_preserved": False
            },
            "correction_contact": "test@example.com",
            "version_history": [
                {"version": "0.1.0", "date": "2026-07-10", "change": "initial"}
            ]
        }

    def test_preprint_requires_reproducibility(self):
        r = self._base_record()
        r["maturity_state"] = "PREPRINT_CANDIDATE"
        errors = validate_record(r)
        self.assertTrue(any("methods_preserved" in e for e in errors))

    def test_preprint_requires_independent_review(self):
        r = self._base_record()
        r["maturity_state"] = "PREPRINT_CANDIDATE"
        r["reproducibility_manifest"]["methods_preserved"] = True
        r["reproducibility_manifest"]["versions_preserved"] = True
        r["reproducibility_manifest"]["negative_results_preserved"] = True
        errors = validate_record(r)
        self.assertTrue(any("review_completed" in e for e in errors))

    def test_novelty_claim_without_prior_art_fails(self):
        r = self._base_record()
        r["claim_postures"] = [
            {"claim": "novel approach", "posture": "NOVELTY_CLAIM", "evidence_ref": None}
        ]
        errors = validate_record(r)
        self.assertTrue(any("prior_art_review" in e for e in errors))

    def test_agent_contribs_without_disclosure_fails(self):
        r = self._base_record()
        r["authorship"]["agent_contributions"] = [
            {"agent": "Codex", "role": "assistant", "scope": "drafting"}
        ]
        errors = validate_record(r)
        self.assertTrue(any("material_assistance" in e for e in errors))

    def test_idea_state_passes_with_minimal_checks(self):
        r = self._base_record()
        errors = validate_record(r)
        self.assertEqual(errors, [], f"Expected no errors for IDEA state: {errors}")


if __name__ == "__main__":
    unittest.main()
