"""Tests for ARCANA RSI modules: gap_analysis + prompt_refiner.

Pure stdlib. No Ollama, no network.
"""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import gap_analysis as ga
import prompt_refiner as pr


class TestGapAnalysis(unittest.TestCase):
    def test_parse_signature_valid(self):
        sig = "1-2-3-2-2-2-1-0-1"
        vec = ga.parse_signature(sig)
        self.assertIsNotNone(vec)
        self.assertEqual(vec["M"], 1)
        self.assertEqual(vec["D"], 2)
        self.assertEqual(vec["A"], 1)

    def test_parse_signature_invalid(self):
        self.assertIsNone(ga.parse_signature("1-2-3"))
        self.assertIsNone(ga.parse_signature("a-b-c-d-e-f-g-h-i"))

    def test_compute_axis_gaps_empty(self):
        gaps = ga.compute_axis_gaps([], [])
        self.assertTrue(all(len(gaps[a]) == 0 for a in ga.AXES))

    def test_attribute_root_cause_prompt_weakness(self):
        cause, fix, conf = ga.attribute_root_cause(
            "M", mean_gap=2.0, sample_size=5,
            plan_targets=[3, 3, 3], actual_scores=[1, 1, 1],
        )
        self.assertEqual(cause, "prompt_weakness")
        self.assertIn("Strengthen", fix)
        self.assertGreater(conf, 0.5)

    def test_attribute_root_cause_insufficient_data(self):
        cause, _fix, conf = ga.attribute_root_cause(
            "L", mean_gap=2.5, sample_size=1,
            plan_targets=[2], actual_scores=[0],
        )
        self.assertEqual(cause, "insufficient_data")
        self.assertLess(conf, 0.5)

    def test_parse_signature_version_aware(self):
        # v0.2: 10-element signature parses to all 10 axes incl Em
        v02 = ga.parse_signature("1-2-3-2-0-2-1-1-2-3")
        self.assertIsNotNone(v02)
        self.assertEqual(v02["Em"], 3)
        self.assertEqual(len(v02), 10)
        # v0.1: 9-element signature parses to the 9 legacy axes (no Em)
        v01 = ga.parse_signature("1-2-3-2-0-2-1-1-2")
        self.assertIsNotNone(v01)
        self.assertNotIn("Em", v01)
        self.assertEqual(len(v01), 9)
        self.assertEqual(v01["A"], 2)
        # Bad length / non-integer -> None
        self.assertIsNone(ga.parse_signature("1-2-3"))
        self.assertIsNone(ga.parse_signature("1-2-x-4-5-6-7-8-9"))

    def test_analyze_with_mock_data(self):
        with tempfile.TemporaryDirectory() as tmp:
            plans_dir = Path(tmp) / "plans"
            plans_dir.mkdir()
            plan = {
                "target_vector": {"M": 3, "D": 3, "E": 3, "V": 3, "C": 3,
                                   "L": 2, "S": 3, "P": 3, "A": 4},
                "_provenance": {"topic": "Test topic"},
            }
            (plans_dir / "plan-test.json").write_text(
                json.dumps(plan), encoding="utf-8")

            history_path = Path(tmp) / "history.tsv"
            history_path.write_text(
                "timestamp_utc\tslug\tdate\tpaideia_version\t"
                "instructional_intent\tM\tD\tE\tV\tC\tL\tS\tP\tA\tsignature\n"
                "2026-05-01T00:00:00Z\ttest-topic\t2026-05-01\t"
                "paideia-score-v0.1\ttrue\t1\t2\t3\t2\t1\t2\t1\t1\t2\t"
                "1-2-3-2-1-2-1-1-2\n",
                encoding="utf-8",
            )

            report = ga.analyze(plans_dir, history_path)
            self.assertEqual(report["plans_loaded"], 1)
            self.assertEqual(report["history_rows_loaded"], 1)
            self.assertGreater(report["matched_pairs"], 0)
            # M gap should be 3-1=2
            m_gap = next((r for r in report["axis_gaps"] if r["axis"] == "M"), None)
            self.assertIsNotNone(m_gap)
            self.assertEqual(m_gap["mean_gap"], 2.0)


class TestPromptRefiner(unittest.TestCase):
    def test_compute_prompt_version(self):
        p = Path("paideia_plan_v1.txt")
        self.assertEqual(pr.compute_prompt_version(p), "v2")
        p2 = Path("paideia_plan_v2.txt")
        self.assertEqual(pr.compute_prompt_version(p2), "v3")

    def test_propose_edits_empty(self):
        edits = pr.propose_edits({"axis_gaps": []})
        self.assertEqual(len(edits), 0)

    def test_generate_trial_prompt_no_edits(self):
        with tempfile.TemporaryDirectory() as tmp:
            prompt_path = Path(tmp) / "paideia_plan_v1.txt"
            prompt_path.write_text("M MODALITY: ...", encoding="utf-8")
            result = pr.generate_trial_prompt(prompt_path, [], dry_run=False)
            self.assertIsNone(result)

    def test_render_proposal(self):
        edits = [pr.PromptEdit(
            axis="M", original_snippet="old", proposed_snippet="new",
            rationale="test", confidence=0.8,
        )]
        text = pr.render_proposal(edits, Path("trial.txt"), dry_run=True)
        self.assertIn("M", text)
        self.assertIn("old", text)
        self.assertIn("new", text)

    def test_edit_patterns_cover_all_axes(self):
        """Every PAIDEIA axis has an edit pattern defined."""
        for axis in ga.AXES:
            self.assertIn(axis, pr.EDIT_PATTERNS,
                          f"Missing EDIT_PATTERNS for axis {axis}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
