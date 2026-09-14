import json
import unittest
from pathlib import Path

from hummbl_eval.gatebench import GateBenchError, evaluate_case

FIXTURES = Path(__file__).parent / "fixtures" / "gatebench"


class GateBenchSeedTests(unittest.TestCase):
    def test_seeded_adversarial_cases_fail_safely(self) -> None:
        for path in sorted(FIXTURES.glob("*.json")):
            with self.subTest(case=path.name):
                case = json.loads(path.read_text(encoding="utf-8"))
                result = evaluate_case(case)
                self.assertEqual(result.disposition, case["expected_disposition"])
                self.assertEqual(result.severity, "P0")

    def test_rejects_malformed_cases(self) -> None:
        valid = {
            "case_id": "GB-P0-X",
            "severity": "P0",
            "claim": "claim",
            "evidence_refs": [],
            "receipt_refs": [],
            "author_id": "a",
            "evaluator_id": "b",
            "expected_disposition": "accept",
        }
        cases = [
            {},
            {**valid, "severity": "P9"},
            {**valid, "evidence_refs": "not-a-list"},
            {key: value for key, value in valid.items() if key != "expected_disposition"},
            {**valid, "evidence_refs": ["evidence", "evidence"]},
            {**valid, "author_id": ""},
        ]
        for case in cases:
            with self.subTest(case=case), self.assertRaises(GateBenchError):
                evaluate_case(case)

    def test_validates_gatebench_reference_and_identity_shapes(self) -> None:
        valid = {
            "case_id": "GB-P0-SHAPE",
            "severity": "P0",
            "claim": "claim",
            "evidence_refs": ["evidence:1"],
            "receipt_refs": ["receipt:1"],
            "author_id": "actor:author",
            "evaluator_id": "actor:evaluator",
            "expected_disposition": "accept",
        }
        malformed = [
            {**valid, "claim": ""},
            {**valid, "evidence_refs": [1]},
            {**valid, "receipt_refs": ["receipt:1", "receipt:1"]},
            {**valid, "expected_disposition": "unknown"},
            {**valid, "expected_disposition": ["accept"]},
        ]
        for case in malformed:
            with self.subTest(case=case), self.assertRaises(GateBenchError):
                evaluate_case(case)


if __name__ == "__main__":
    unittest.main()
