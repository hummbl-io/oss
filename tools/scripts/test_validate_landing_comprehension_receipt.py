#!/usr/bin/env python3
"""Unit tests for validate_landing_comprehension_receipt.py.

Stdlib-only, matching the validator. Run with:

    python tools/scripts/test_validate_landing_comprehension_receipt.py

Synthetic five-participant receipts in this file are fixtures for the
validator. They are not claimed comprehension results.
"""
from __future__ import annotations

import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path


def _load_validator():
    here = Path(__file__).resolve().parent
    env = os.environ.get("LANDING_COMPREHENSION_VALIDATOR_PATH")
    if env:
        candidate = Path(env)
        if candidate.exists():
            spec = importlib.util.spec_from_file_location(
                "validate_landing_comprehension_receipt", candidate
            )
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            return mod

    candidate = here / "validate_landing_comprehension_receipt.py"
    if candidate.exists():
        spec = importlib.util.spec_from_file_location(
            "validate_landing_comprehension_receipt", candidate
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod

    raise FileNotFoundError(
        "Could not find validate_landing_comprehension_receipt.py. "
        "Place this test next to the validator or set "
        "LANDING_COMPREHENSION_VALIDATOR_PATH."
    )


validator = _load_validator()
REPO_ROOT = Path(__file__).resolve().parents[2]
TEMPLATE_PATH = REPO_ROOT / "docs" / "research" / "landing-comprehension-receipt-template.json"

SHA = "b1b05813832d14185bba12284dd8a6cede2f19c3"
TESTED_AT = "2026-08-31T12:00:00Z"

RESPONSES = {
    "q1": "Open-source runtime governance primitives.",
    "q2": "Policies are not on the execution path.",
    "q3": "Inspect the source.",
    "q4": "In-process mediation and HMAC in a shared-secret domain.",
    "q5": "Claims ledger, public CI, and the executable example.",
    "q6": "Alpha; repository CI is not production use.",
}


def _participant(
    ident,
    role,
    scores,
    *,
    confidence=4,
    sensible=True,
    overclaim=False,
    responses=None,
):
    keys = ("what", "why", "next", "guarantee", "evidence", "boundary")
    return {
        "id": ident,
        "role": role,
        "scores": dict(zip(keys, scores)),
        "confidence": confidence,
        "sensible_next_action": sensible,
        "material_overclaim_detected": overclaim,
        "responses": dict(responses or RESPONSES),
    }


def _base_receipt(participants, *, status="COMPLETE", aggregate=None):
    computed = validator.compute_aggregate(participants)
    receipt = {
        "receipt_type": "landing-comprehension-test",
        "schema_version": "1.0.0",
        "status": status,
        "protocol": "docs/research/landing-comprehension-test-protocol.md",
        "tested_url": "https://hummbl.io/",
        "tested_sha": SHA,
        "tested_at": TESTED_AT,
        "viewport": {
            "width": 1440,
            "height": 900,
            "first_view_seconds": 20,
            "full_scan_seconds": 180,
        },
        "participants": participants,
        "aggregate": aggregate if aggregate is not None else computed,
        "limitations": [
            "Five-person directional comprehension test; not a representative market study.",
            "Synthetic fixture; not a claimed comprehension result.",
        ],
    }
    return receipt


def passing_participants():
    """Four of five at ≥9/12, all boundaries ≥1, no overclaim, 5 sensible next."""
    return [
        _participant("P1", "builder", (2, 2, 2, 2, 2, 1)),
        _participant("P2", "builder", (2, 2, 1, 2, 2, 2)),
        _participant("P3", "security-risk-compliance", (2, 2, 2, 1, 2, 1)),
        _participant("P4", "technology-buyer", (2, 1, 2, 2, 1, 1)),
        _participant("P5", "technical-generalist", (1, 1, 2, 1, 1, 1)),  # total 7
    ]


def failing_high_score_participants():
    """Only three of five at ≥9/12."""
    people = passing_participants()
    people[3] = _participant("P4", "technology-buyer", (1, 1, 1, 1, 1, 1))  # total 6
    people[4] = _participant("P5", "technical-generalist", (1, 1, 1, 1, 1, 1))  # total 6
    return people


class TestUnrunTemplate(unittest.TestCase):
    def test_repository_template_is_valid_preparation(self):
        self.assertTrue(TEMPLATE_PATH.is_file(), f"missing {TEMPLATE_PATH}")
        data = json.loads(TEMPLATE_PATH.read_text(encoding="utf-8"))
        issues, computed, mode = validator.validate_receipt(data)
        self.assertEqual(issues, [])
        self.assertEqual(mode, "unrun")
        self.assertIsNotNone(computed)
        self.assertFalse(computed["threshold_met"])
        self.assertEqual(computed["participants_total"], 0)
        self.assertFalse(computed["all_boundaries_at_least_1"])

    def test_unrun_cli_exits_zero(self):
        code = validator.main([str(TEMPLATE_PATH)])
        self.assertEqual(code, 0)

    def test_unrun_with_participants_is_rejected(self):
        data = json.loads(TEMPLATE_PATH.read_text(encoding="utf-8"))
        data["participants"] = passing_participants()
        issues, _, _ = validator.validate_receipt(data)
        joined = "\n".join(issues)
        self.assertTrue(any("UNRUN" in issue for issue in issues), joined)

    def test_empty_participants_require_unrun_status(self):
        data = json.loads(TEMPLATE_PATH.read_text(encoding="utf-8"))
        data["status"] = "COMPLETE"
        issues, _, _ = validator.validate_receipt(data)
        self.assertTrue(any("status" in issue and "UNRUN" in issue for issue in issues))


class TestComputeAggregate(unittest.TestCase):
    def test_passing_receipt_meets_threshold(self):
        computed = validator.compute_aggregate(passing_participants())
        self.assertEqual(computed["participants_total"], 5)
        self.assertEqual(computed["participants_scoring_at_least_9"], 4)
        self.assertTrue(computed["all_boundaries_at_least_1"])
        self.assertEqual(computed["sensible_next_actions"], 5)
        self.assertFalse(computed["material_overclaim_detected"])
        self.assertTrue(computed["threshold_met"])

    def test_too_few_high_scores_fails_threshold(self):
        computed = validator.compute_aggregate(failing_high_score_participants())
        self.assertEqual(computed["participants_scoring_at_least_9"], 3)
        self.assertFalse(computed["threshold_met"])

    def test_boundary_zero_fails_threshold(self):
        people = passing_participants()
        people[4]["scores"]["boundary"] = 0
        computed = validator.compute_aggregate(people)
        self.assertFalse(computed["all_boundaries_at_least_1"])
        self.assertFalse(computed["threshold_met"])

    def test_material_overclaim_fails_threshold(self):
        people = passing_participants()
        people[0]["material_overclaim_detected"] = True
        computed = validator.compute_aggregate(people)
        self.assertTrue(computed["material_overclaim_detected"])
        self.assertFalse(computed["threshold_met"])

    def test_too_few_sensible_next_fails_threshold(self):
        people = passing_participants()
        people[3]["sensible_next_action"] = False
        people[4]["sensible_next_action"] = False
        computed = validator.compute_aggregate(people)
        self.assertEqual(computed["sensible_next_actions"], 3)
        self.assertFalse(computed["threshold_met"])

    def test_empty_participants_are_not_vacuous_pass(self):
        computed = validator.compute_aggregate([])
        self.assertFalse(computed["all_boundaries_at_least_1"])
        self.assertFalse(computed["threshold_met"])


class TestFiveParticipantReceipt(unittest.TestCase):
    def test_passing_receipt_is_valid_and_threshold_met(self):
        receipt = _base_receipt(passing_participants())
        issues, computed, mode = validator.validate_receipt(receipt)
        self.assertEqual(issues, [])
        self.assertEqual(mode, "complete")
        self.assertTrue(computed["threshold_met"])

    def test_failing_receipt_is_valid_with_threshold_false(self):
        receipt = _base_receipt(failing_high_score_participants())
        issues, computed, mode = validator.validate_receipt(receipt)
        self.assertEqual(issues, [])
        self.assertEqual(mode, "complete")
        self.assertFalse(computed["threshold_met"])

    def test_client_supplied_threshold_met_is_not_trusted(self):
        receipt = _base_receipt(failing_high_score_participants())
        receipt["aggregate"]["threshold_met"] = True
        issues, computed, mode = validator.validate_receipt(receipt)
        self.assertEqual(mode, "complete")
        self.assertFalse(computed["threshold_met"])
        self.assertTrue(
            any("aggregate.threshold_met" in issue for issue in issues),
            "\n".join(issues),
        )

    def test_cli_passing_receipt_exits_zero(self):
        receipt = _base_receipt(passing_participants())
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "passing.json"
            path.write_text(json.dumps(receipt), encoding="utf-8")
            self.assertEqual(validator.main([str(path)]), 0)

    def test_cli_aggregate_mismatch_exits_one(self):
        receipt = _base_receipt(failing_high_score_participants())
        receipt["aggregate"]["threshold_met"] = True
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "mismatch.json"
            path.write_text(json.dumps(receipt), encoding="utf-8")
            self.assertEqual(validator.main([str(path)]), 1)


class TestFieldValidation(unittest.TestCase):
    def test_reports_every_missing_participant_field(self):
        receipt = _base_receipt(passing_participants())
        receipt["participants"][0] = {"id": "P1"}
        issues, _, _ = validator.validate_receipt(receipt)
        joined = "\n".join(issues)
        for field in (
            "role",
            "scores",
            "confidence",
            "sensible_next_action",
            "material_overclaim_detected",
            "responses",
        ):
            self.assertIn(field, joined)

    def test_rejects_invalid_role_label(self):
        people = passing_participants()
        people[2]["role"] = "security"
        receipt = _base_receipt(people)
        issues, _, _ = validator.validate_receipt(receipt)
        self.assertTrue(any("role" in issue for issue in issues), "\n".join(issues))

    def test_rejects_wrong_role_mix(self):
        people = passing_participants()
        people[4]["role"] = "builder"
        receipt = _base_receipt(people)
        issues, _, _ = validator.validate_receipt(receipt)
        self.assertTrue(any("role mix" in issue for issue in issues), "\n".join(issues))

    def test_rejects_non_integer_score(self):
        people = passing_participants()
        people[0]["scores"]["what"] = True
        receipt = _base_receipt(people)
        issues, _, _ = validator.validate_receipt(receipt)
        self.assertTrue(any("scores.what" in issue for issue in issues), "\n".join(issues))

    def test_rejects_score_out_of_range(self):
        people = passing_participants()
        people[0]["scores"]["boundary"] = 3
        receipt = _base_receipt(people)
        issues, _, _ = validator.validate_receipt(receipt)
        self.assertTrue(any("scores.boundary" in issue for issue in issues))

    def test_rejects_missing_response(self):
        people = passing_participants()
        del people[1]["responses"]["q6"]
        receipt = _base_receipt(people)
        issues, _, _ = validator.validate_receipt(receipt)
        self.assertTrue(any("responses" in issue and "q6" in issue for issue in issues))

    def test_rejects_confidence_out_of_range(self):
        people = passing_participants()
        people[0]["confidence"] = 0
        receipt = _base_receipt(people)
        issues, _, _ = validator.validate_receipt(receipt)
        self.assertTrue(any("confidence" in issue for issue in issues))

    def test_rejects_non_boolean_flags(self):
        people = passing_participants()
        people[0]["sensible_next_action"] = 1
        people[1]["material_overclaim_detected"] = "false"
        receipt = _base_receipt(people)
        issues, _, _ = validator.validate_receipt(receipt)
        joined = "\n".join(issues)
        self.assertIn("sensible_next_action", joined)
        self.assertIn("material_overclaim_detected", joined)

    def test_rejects_wrong_tested_url(self):
        receipt = _base_receipt(passing_participants())
        receipt["tested_url"] = "https://example.com/"
        issues, _, _ = validator.validate_receipt(receipt)
        self.assertTrue(any("tested_url" in issue for issue in issues))

    def test_rejects_duplicate_ids(self):
        people = passing_participants()
        people[1]["id"] = "P1"
        receipt = _base_receipt(people)
        issues, _, _ = validator.validate_receipt(receipt)
        self.assertTrue(any("duplicate id" in issue for issue in issues))

    def test_rejects_wrong_participant_count(self):
        people = passing_participants()[:3]
        receipt = _base_receipt(people)
        issues, _, _ = validator.validate_receipt(receipt)
        self.assertTrue(any("exactly 5" in issue for issue in issues))

    def test_missing_file_exits_one(self):
        self.assertEqual(validator.main(["/tmp/does-not-exist-landing-receipt.json"]), 1)


class TestProtocolDoesNotClaimResults(unittest.TestCase):
    def test_template_status_is_unrun(self):
        data = json.loads(TEMPLATE_PATH.read_text(encoding="utf-8"))
        self.assertEqual(data["status"], "UNRUN")
        self.assertEqual(data["participants"], [])
        self.assertIs(data["aggregate"]["threshold_met"], False)

    def test_protocol_status_line_is_unrun(self):
        text = (REPO_ROOT / "docs" / "research" / "landing-comprehension-test-protocol.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("UNRUN", text)
        self.assertNotIn("temporary", text.lower())
        self.assertNotIn("two tests were skipped", text.lower())


if __name__ == "__main__":
    unittest.main()
