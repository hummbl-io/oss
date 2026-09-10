"""Tests for Base120 quality GateBench evaluation."""

import json
import unittest
from pathlib import Path

from hummbl_eval.gatebench import (
    Base120CaseError,
    evaluate_base120_case,
)

FIXTURES = Path(__file__).parent / "fixtures" / "gatebench_base120"


class Base120GateBenchTests(unittest.TestCase):
    def test_valid_base120_output_accepts(self) -> None:
        case = {
            "case_id": "GB-B120-001",
            "severity": "P1",
            "skill_name": "test-skill",
            "base120_output": (
                "test-skill (Base120 Cognitive Structuring) | all | 2026-08-11\n"
                "=" * 70 + "\n\n"
                "## Overview (P6: Point-of-View Anchoring)\n"
                "  Count: 5\n\n"
                "## Findings (DE1: Root Cause Analysis)\n"
                "    [CRIT] Missing eval suite\n"
                "      [DE1] Why: No ground truth.\n"
                "      Reveals: Untestable claims.\n"
                "      Action: Create eval/.\n\n"
                "Base120 Applied: DE1, P6\n"
                "=" * 70
            ),
            "expected_disposition": "accept",
        }
        result = evaluate_base120_case(case)
        self.assertEqual(result.disposition, "accept")
        self.assertEqual(result.case_id, "GB-B120-001")

    def test_missing_why_reveals_action_rejects(self) -> None:
        case = {
            "case_id": "GB-B120-002",
            "severity": "P0",
            "skill_name": "test-skill",
            "base120_output": (
                "test-skill (Base120 Cognitive Structuring) | all | 2026-08-11\n"
                "=" * 70 + "\n\n"
                "## Overview (P6: Point-of-View Anchoring)\n"
                "  Count: 5\n\n"
                "Base120 Applied: P6\n"
                "=" * 70
            ),
            "expected_disposition": "reject",
        }
        result = evaluate_base120_case(case)
        self.assertEqual(result.disposition, "reject")
        self.assertTrue(any("Why" in r or "Reveals" in r or "Action" in r for r in result.reasons))

    def test_missing_footer_rejects(self) -> None:
        case = {
            "case_id": "GB-B120-003",
            "severity": "P0",
            "skill_name": "test-skill",
            "base120_output": (
                "test-skill (Base120 Cognitive Structuring) | all | 2026-08-11\n"
                "=" * 70 + "\n\n"
                "## Findings (DE1: Root Cause Analysis)\n"
                "    [CRIT] Issue\n"
                "      [DE1] Why: reason\n"
                "      Reveals: insight\n"
                "      Action: fix\n"
            ),
            "expected_disposition": "reject",
        }
        result = evaluate_base120_case(case)
        self.assertEqual(result.disposition, "reject")
        self.assertTrue(any("footer" in r.lower() for r in result.reasons))

    def test_missing_header_rejects(self) -> None:
        case = {
            "case_id": "GB-B120-004",
            "severity": "P0",
            "skill_name": "test-skill",
            "base120_output": "Just some plain text output without any structure.",
            "expected_disposition": "reject",
        }
        result = evaluate_base120_case(case)
        self.assertEqual(result.disposition, "reject")
        self.assertTrue(any("header" in r.lower() or "Base120" in r for r in result.reasons))

    def test_invalid_operator_code_rejects(self) -> None:
        case = {
            "case_id": "GB-B120-005",
            "severity": "P1",
            "skill_name": "test-skill",
            "base120_output": (
                "test-skill (Base120 Cognitive Structuring) | all | 2026-08-11\n"
                "=" * 70 + "\n\n"
                "## Overview (ZZ99: Fake Code)\n"
                "  Count: 5\n\n"
                "## Findings (DE1: Root Cause Analysis)\n"
                "    [CRIT] Issue\n"
                "      [DE1] Why: reason\n"
                "      Reveals: insight\n"
                "      Action: fix\n\n"
                "Base120 Applied: DE1, ZZ99\n"
                "=" * 70
            ),
            "expected_disposition": "reject",
        }
        result = evaluate_base120_case(case)
        self.assertEqual(result.disposition, "reject")
        self.assertTrue(any("ZZ99" in r or "invalid" in r.lower() for r in result.reasons))

    def test_rejects_malformed_cases(self) -> None:
        valid_output = (
            "test-skill (Base120 Cognitive Structuring) | all | 2026-08-11\n"
            "=" * 70 + "\n\n"
            "## Overview (P6: Point-of-View Anchoring)\n"
            "  Count: 5\n\n"
            "## Findings (DE1: Root Cause Analysis)\n"
            "    [CRIT] Issue\n"
            "      [DE1] Why: reason\n"
            "      Reveals: insight\n"
            "      Action: fix\n\n"
            "Base120 Applied: DE1, P6\n"
            "=" * 70
        )
        valid = {
            "case_id": "GB-B120-X",
            "severity": "P1",
            "skill_name": "test-skill",
            "base120_output": valid_output,
        }
        cases = [
            {},
            {**valid, "severity": "P9"},
            {**valid, "base120_output": 123},
        ]
        for case in cases:
            with self.subTest(case=case), self.assertRaises(Base120CaseError):
                evaluate_base120_case(case)

    def test_fixture_cases_match_expected_disposition(self) -> None:
        if not FIXTURES.is_dir():
            self.skipTest("fixture directory not yet created")
        for path in sorted(FIXTURES.glob("*.json")):
            with self.subTest(case=path.name):
                case = json.loads(path.read_text(encoding="utf-8"))
                result = evaluate_base120_case(case)
                self.assertEqual(result.disposition, case["expected_disposition"])


if __name__ == "__main__":
    unittest.main()
