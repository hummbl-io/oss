"""Tests for NoulTuple and NoulIndex in hummbl_tuples."""
import unittest

from hummbl_tuples.noul import NoulTuple, SystemOneTuple
from hummbl_tuples.noul_index import NoulIndex


class TestNoulTupleAndIndex(unittest.TestCase):
    def test_noul_tuple_creation_and_canonical_json(self):
        noul = NoulTuple(
            proposition="is_destructive_operation",
            state_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            decision=True,
            p_true=0.92,
            p_false=0.08,
            confidence=0.92,
            alarm_threshold=0.40,
            is_alarm=True,
            domain="security",
            evaluator_agent="agy",
        )

        self.assertEqual(noul.tuple_type, "NOUL")
        self.assertTrue(noul.is_alarm)
        self.assertFalse(noul.in_abstention_band())

        # Canonical JSON serialization check
        json_str = noul.to_json()
        self.assertIn('"is_destructive_operation"', json_str)
        self.assertIn('"tuple_type":"NOUL"', json_str)
        self.assertIsNotNone(noul.content_hash)

    def test_from_jev_response_constructor(self):
        raw_jev = {
            "choice": "true",
            "confidence": 0.88,
            "probabilities": {"true": 0.88, "false": 0.12},
        }
        noul = NoulTuple.from_jev_response(
            proposition="needs_human",
            state_hash="abc123hash",
            jev_answer=raw_jev,
            alarm_threshold=0.50,
            evaluator_agent="devin",
        )

        self.assertTrue(noul.decision)
        self.assertEqual(noul.p_true, 0.88)
        self.assertTrue(noul.is_alarm)

    def test_noul_index_caching_and_lookup(self):
        idx = NoulIndex()
        noul = NoulTuple(
            proposition="is_spec_compliant",
            state_hash="state_hash_001",
            decision=True,
            p_true=0.95,
            p_false=0.05,
            confidence=0.95,
        )
        idx.record(noul)

        cached = idx.lookup("state_hash_001", "is_spec_compliant")
        self.assertIsNotNone(cached)
        self.assertEqual(cached.id, noul.id)

        # Missing lookup returns None
        self.assertIsNone(idx.lookup("state_hash_missing", "is_spec_compliant"))

    def test_noul_index_contradiction_detection(self):
        idx = NoulIndex()
        t1 = NoulTuple(
            proposition="is_malicious",
            state_hash="identical_state",
            decision=True,
            p_true=0.90,
            evaluator_agent="agent_alpha",
        )
        t2 = NoulTuple(
            proposition="is_malicious",
            state_hash="identical_state",
            decision=False,
            p_true=0.10,
            evaluator_agent="agent_beta",
        )
        idx.record(t1)
        idx.record(t2)

        contradictions = idx.detect_contradictions("identical_state", "is_malicious")
        self.assertEqual(len(contradictions), 1)
        self.assertEqual(contradictions[0], (t1, t2))

    def test_calibration_metrics(self):
        idx = NoulIndex()
        # Record calibrated predictions with ground truth
        n1 = NoulTuple(proposition="p", state_hash="s1", p_true=0.9, ground_truth=True)
        n2 = NoulTuple(proposition="p", state_hash="s2", p_true=0.8, ground_truth=True)
        n3 = NoulTuple(proposition="p", state_hash="s3", p_true=0.1, ground_truth=False)
        idx.record(n1)
        idx.record(n2)
        idx.record(n3)

        stats = idx.calibration_stats("p")
        self.assertEqual(stats["count"], 3)
        self.assertLess(stats["brier_score"], 0.05)
        self.assertLess(stats["ece"], 0.20)


if __name__ == "__main__":
    unittest.main()
