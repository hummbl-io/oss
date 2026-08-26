import unittest

from hummbl_taxonomy import ClassificationInput, classify


class ClassifierTests(unittest.TestCase):
    def test_narrow_tool_classifies_as_ani_partially_governed(self):
        result = classify(
            ClassificationInput(
                domain_breadth="single_task",
                novelty_handling="weak",
                transfer="none",
                autonomy="direct",
                world_model="task_local",
                mission_authority=True,
                capability_bounds=True,
                evidence_receipts=True,
            )
        )

        self.assertEqual(result.tier, "ANI")
        self.assertEqual(result.governance_status, "partially-governed")
        self.assertTrue(result.can_act)
        self.assertFalse(result.may_act)
        self.assertTrue(result.must_stop)

    def test_governed_domain_agent_classifies_as_aspi_governed(self):
        result = classify(
            ClassificationInput(
                domain_breadth="coherent_domain",
                novelty_handling="strong_in_domain",
                transfer="adjacent",
                autonomy="guided",
                world_model="domain_specific",
                mission_authority=True,
                capability_bounds=True,
                evidence_receipts=True,
                independent_review=True,
                stop_or_rollback=True,
            )
        )

        self.assertEqual(result.tier, "ASPI")
        self.assertEqual(result.governance_status, "governed")
        self.assertTrue(result.can_act)
        self.assertTrue(result.may_act)
        self.assertTrue(result.should_continue)
        self.assertFalse(result.must_stop)

    def test_cross_domain_transfer_triggers_agi_review(self):
        result = classify(
            ClassificationInput(
                domain_breadth="arbitrary",
                novelty_handling="cross_domain",
                transfer="cross_domain",
                autonomy="broad",
                world_model="general",
                mission_authority=True,
                capability_bounds=True,
                evidence_receipts=True,
                independent_review=True,
                stop_or_rollback=True,
            )
        )

        self.assertEqual(result.tier, "AGI")
        self.assertEqual(result.governance_status, "governed")
        self.assertIn("domain_bounds_weakened", result.reason_codes)

    def test_ungoverned_capability_must_stop(self):
        result = classify(
            ClassificationInput(
                domain_breadth="coherent_domain",
                novelty_handling="strong_in_domain",
                transfer="adjacent",
                autonomy="guided",
                world_model="domain_specific",
            )
        )

        self.assertEqual(result.tier, "ASPI")
        self.assertEqual(result.governance_status, "ungoverned")
        self.assertFalse(result.may_act)
        self.assertFalse(result.should_continue)
        self.assertTrue(result.must_stop)


if __name__ == "__main__":
    unittest.main()
