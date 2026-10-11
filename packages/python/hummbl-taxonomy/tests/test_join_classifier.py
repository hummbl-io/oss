import unittest

from hummbl_taxonomy import JoinInput, classify_join


class JoinClassifierTests(unittest.TestCase):
    def test_ungoverned_analogy_classifies_as_share_l0_must_stop(self) -> None:
        result = classify_join(
            JoinInput(
                operator="SHARE",
                altitude="L0",
            )
        )

        self.assertEqual(result.operator, "SHARE")
        self.assertEqual(result.altitude, "L0")
        self.assertEqual(result.join_status, "ungoverned")
        self.assertTrue(result.can_join)
        self.assertFalse(result.may_join)
        self.assertTrue(result.must_stop)

    def test_governed_boundary_object_may_join(self) -> None:
        result = classify_join(
            JoinInput(
                operator="SHARE",
                altitude="L4",
                language="none",
                identities_separate=True,
                mission_authority=True,
                evidence_receipts=True,
                independent_review=True,
                stop_or_rollback=True,
            )
        )

        self.assertEqual(result.operator, "SHARE")
        self.assertEqual(result.altitude, "L4")
        self.assertEqual(result.join_status, "governed")
        self.assertTrue(result.may_join)
        self.assertTrue(result.should_continue)
        self.assertFalse(result.must_stop)

    def test_translate_at_ontology_without_review_is_altitude_sneak(self) -> None:
        result = classify_join(
            JoinInput(
                operator="TRANSLATE",
                altitude="L3",
                language="pidgin",
                mission_authority=True,
                evidence_receipts=True,
                independent_review=False,
                stop_or_rollback=True,
            )
        )

        self.assertEqual(result.operator, "TRANSLATE")
        self.assertIn("altitude_sneak", result.reason_codes)
        self.assertTrue(result.must_stop)
        self.assertFalse(result.may_join)

    def test_consil_without_independence_at_l3_is_wilsonization(self) -> None:
        result = classify_join(
            JoinInput(
                operator="CONSIL",
                altitude="L3",
                evidence_independent=False,
                mission_authority=True,
                evidence_receipts=True,
                independent_review=True,
                stop_or_rollback=True,
            )
        )

        self.assertIn("independence_unproven", result.reason_codes)
        self.assertIn("wilsonization", result.reason_codes)
        self.assertTrue(result.must_stop)

    def test_superpose_without_named_levels_is_mashup(self) -> None:
        result = classify_join(
            JoinInput(
                operator="SUPERPOSE",
                altitude="L5",
                levels_named=False,
                mission_authority=True,
                evidence_receipts=True,
                independent_review=True,
                stop_or_rollback=True,
            )
        )

        self.assertIn("mashup", result.reason_codes)
        self.assertTrue(result.must_stop)

    def test_unknown_operator_classifies_conservatively_as_share(self) -> None:
        result = classify_join(
            JoinInput(
                operator="ANALOGIZE",
                altitude="L2",
            )
        )

        self.assertEqual(result.operator, "SHARE")
        self.assertIn("unknown_operator", result.reason_codes)
        self.assertIn("classified_conservatively", result.reason_codes)

    def test_claimed_higher_altitude_is_sneak(self) -> None:
        result = classify_join(
            JoinInput(
                operator="COMPOSE",
                altitude="L1",
                claimed_altitude="L3",
                identities_separate=True,
                language="contract",
                mission_authority=True,
                evidence_receipts=True,
                independent_review=True,
                stop_or_rollback=True,
            )
        )

        self.assertEqual(result.altitude, "L1")
        self.assertIn("altitude_sneak", result.reason_codes)
        self.assertTrue(result.must_stop)

    def test_compose_without_separate_identities_is_reduction_risk(self) -> None:
        result = classify_join(
            JoinInput(
                operator="COMPOSE",
                altitude="L1",
                identities_separate=False,
                mission_authority=True,
                evidence_receipts=True,
                independent_review=True,
                stop_or_rollback=True,
            )
        )
        self.assertIn("reduction_risk", result.reason_codes)
        self.assertTrue(result.must_stop)

    def test_translate_with_promoted_language(self) -> None:
        result = classify_join(
            JoinInput(
                operator="TRANSLATE",
                altitude="L1",
                language="contract",
                mission_authority=True,
                evidence_receipts=True,
                independent_review=True,
                stop_or_rollback=True,
            )
        )
        self.assertIn("language_promoted", result.reason_codes)

    def test_unknown_altitude_classifies_as_l0(self) -> None:
        result = classify_join(
            JoinInput(
                operator="SHARE",
                altitude="INVALID_ALTITUDE",
            )
        )
        self.assertEqual(result.altitude, "L0")
        self.assertIn("unknown_altitude", result.reason_codes)


if __name__ == "__main__":
    unittest.main()
