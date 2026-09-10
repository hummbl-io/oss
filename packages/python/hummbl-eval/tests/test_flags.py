"""Tests for MTSMU, AAR, and HRSI flag integration in hummbl-eval."""

import io
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from hummbl_eval.aar import AarFormatter, add_aar_arg
from hummbl_eval.cli import main
from hummbl_eval.hrsi import COGSTATES, HrsiCheckin, add_hrsi_arg
from hummbl_eval.mtsmu import MtsmuSummary, add_mtsmu_arg


class MtsmuSummaryUnitTests(unittest.TestCase):
    def test_empty_summary_renders(self) -> None:
        summary = MtsmuSummary()
        output = io.StringIO()
        with patch("sys.stdout", output):
            summary.render()
        self.assertIn("Findings tracked: 0", output.getvalue())

    def test_track_increments_count(self) -> None:
        summary = MtsmuSummary()
        summary.track("verify-after", "low")
        summary.track("cross-check", "high")
        self.assertEqual(summary.finding_count, 2)

    def test_invalid_verify_method_normalizes(self) -> None:
        summary = MtsmuSummary()
        summary.track("invalid", "low")
        self.assertEqual(summary.verify_methods.get("unverified"), 1)

    def test_invalid_uncertainty_normalizes(self) -> None:
        summary = MtsmuSummary()
        summary.track("verify-after", "invalid")
        self.assertEqual(summary.uncertainties.get("unknown"), 1)

    def test_uncertainty_with_basis_stripped(self) -> None:
        summary = MtsmuSummary()
        summary.track("verify-after", "medium -- no baseline")
        self.assertEqual(summary.uncertainties.get("medium"), 1)

    def test_render_shows_rigor_assessment(self) -> None:
        summary = MtsmuSummary()
        summary.track("verify-after", "low")
        summary.track("verify-after", "low")
        summary.track("verify-after", "low")
        summary.track("unverified", "unknown")
        output = io.StringIO()
        with patch("sys.stdout", output):
            summary.render()
        text = output.getvalue()
        self.assertIn("Verifiable:", text)
        self.assertIn("HIGH RIGOR", text)  # 3/4 = 75%

    def test_moderate_rigor_assessment(self) -> None:
        summary = MtsmuSummary()
        summary.track("verify-after", "low")
        summary.track("verify-after", "low")
        summary.track("unverified", "unknown")
        summary.track("unverified", "unknown")
        output = io.StringIO()
        with patch("sys.stdout", output):
            summary.render()
        self.assertIn("MODERATE RIGOR", output.getvalue())  # 2/4 = 50%

    def test_low_rigor_assessment(self) -> None:
        summary = MtsmuSummary()
        summary.track("verify-after", "low")
        summary.track("unverified", "unknown")
        summary.track("unverified", "unknown")
        summary.track("unverified", "unknown")
        output = io.StringIO()
        with patch("sys.stdout", output):
            summary.render()
        self.assertIn("LOW RIGOR", output.getvalue())  # 1/4 = 25%

    def test_insufficient_rigor_assessment(self) -> None:
        summary = MtsmuSummary()
        summary.track("unverified", "unknown")
        summary.track("unverified", "unknown")
        summary.track("unverified", "unknown")
        summary.track("unverified", "unknown")
        output = io.StringIO()
        with patch("sys.stdout", output):
            summary.render()
        self.assertIn("INSUFFICIENT RIGOR", output.getvalue())  # 0/4 = 0%

    def test_to_dict(self) -> None:
        summary = MtsmuSummary()
        summary.track("verify-after", "low")
        summary.track("cross-check", "medium")
        data = summary.to_dict()
        self.assertEqual(data["finding_count"], 2)
        self.assertEqual(data["verify_methods"]["verify-after"], 1)
        self.assertEqual(data["verify_methods"]["cross-check"], 1)


class AarFormatterUnitTests(unittest.TestCase):
    def test_header_includes_skill_name(self) -> None:
        aar = AarFormatter("test-skill", author="devin", classification="INTERNAL")
        output = io.StringIO()
        with patch("sys.stdout", output):
            aar.render()
        text = output.getvalue()
        self.assertIn("AAR: test-skill", text)
        self.assertIn("INTERNAL", text)
        self.assertIn("devin", text)

    def test_mission_section_rendered(self) -> None:
        aar = AarFormatter("test-skill")
        aar.set_mission(
            objective="Test the AAR",
            success_criteria="All sections render",
            constraints="1 session",
        )
        output = io.StringIO()
        with patch("sys.stdout", output):
            aar.render()
        text = output.getvalue()
        self.assertIn("Mission & Intent", text)
        self.assertIn("Objective", text)
        self.assertIn("Test the AAR", text)
        self.assertIn("Success criteria", text)
        self.assertIn("Constraints", text)

    def test_chronology_entries_rendered(self) -> None:
        aar = AarFormatter("test-skill")
        aar.chronology_entry("2026-01-01 00:00Z", "Event A", "Result A")
        aar.chronology_entry("2026-01-01 00:05Z", "Event B", "Result B")
        output = io.StringIO()
        with patch("sys.stdout", output):
            aar.render()
        text = output.getvalue()
        self.assertIn("Chronology", text)
        self.assertIn("Event A", text)
        self.assertIn("Result A", text)
        self.assertIn("Event B", text)

    def test_outcome_vs_plan_rendered(self) -> None:
        aar = AarFormatter("test-skill")
        aar.set_outcome(
            planned="All tests pass",
            actual="2 tests failed",
            delta="2 failures in test_aar",
        )
        output = io.StringIO()
        with patch("sys.stdout", output):
            aar.render()
        text = output.getvalue()
        self.assertIn("Outcome vs Plan", text)
        self.assertIn("All tests pass", text)
        self.assertIn("2 tests failed", text)
        self.assertIn("Delta", text)

    def test_root_causes_with_why_chain(self) -> None:
        aar = AarFormatter("test-skill")
        aar.root_cause("Tests failed", ["Surface: typo", "Deeper: no CI gate"])
        output = io.StringIO()
        with patch("sys.stdout", output):
            aar.render()
        text = output.getvalue()
        self.assertIn("Root Causes", text)
        self.assertIn("Tests failed", text)
        self.assertIn("Why 1: Surface: typo", text)
        self.assertIn("Why 2: Deeper: no CI gate", text)

    def test_sustains_rendered_with_evidence(self) -> None:
        aar = AarFormatter("test-skill")
        aar.sustain("Registry loading works", "120 operators loaded")
        output = io.StringIO()
        with patch("sys.stdout", output):
            aar.render()
        text = output.getvalue()
        self.assertIn("Sustains", text)
        self.assertIn("Registry loading works", text)
        self.assertIn("evidence: 120 operators loaded", text)

    def test_improves_rendered_with_evidence(self) -> None:
        aar = AarFormatter("test-skill")
        aar.improve("No CI gate", "5/7 skills lack eval/")
        output = io.StringIO()
        with patch("sys.stdout", output):
            aar.render()
        text = output.getvalue()
        self.assertIn("Improves", text)
        self.assertIn("No CI gate", text)
        self.assertIn("evidence: 5/7 skills lack eval/", text)

    def test_recommendations_with_priority(self) -> None:
        aar = AarFormatter("test-skill")
        aar.recommendation("HIGH", "Add CI gate", "addresses: no CI gate")
        aar.recommendation("MED", "Add template", "addresses: no template")
        aar.recommendation("LOW", "Add docs", "")
        output = io.StringIO()
        with patch("sys.stdout", output):
            aar.render()
        text = output.getvalue()
        self.assertIn("Recommendations", text)
        self.assertIn("[HIGH]", text)
        self.assertIn("Add CI gate", text)
        self.assertIn("[MED]", text)
        self.assertIn("[LOW]", text)

    def test_invalid_priority_normalizes_to_low(self) -> None:
        aar = AarFormatter("test-skill")
        aar.recommendation("URGENT", "Do something", "")
        data = aar.to_dict()
        self.assertEqual(data["recommendations"][0]["priority"], "LOW")

    def test_base120_codes_tracked(self) -> None:
        aar = AarFormatter("test-skill")
        aar.set_mission(objective="test")
        aar.chronology_entry("now", "event")
        aar.set_outcome(planned="p", actual="a")
        aar.root_cause("dev", ["why"])
        aar.sustain("s", "e")
        aar.improve("i", "e")
        aar.recommendation("HIGH", "r", "")
        output = io.StringIO()
        with patch("sys.stdout", output):
            aar.render()
        text = output.getvalue()
        self.assertIn("Base120 Applied:", text)
        for code in ("P6", "RE17", "IN17", "DE1", "RE16", "IN20", "DE7"):
            self.assertIn(code, text)

    def test_evidence_footer(self) -> None:
        aar = AarFormatter("test-skill")
        aar.set_evidence(["commit-abc", "test-output.log"])
        output = io.StringIO()
        with patch("sys.stdout", output):
            aar.render()
        text = output.getvalue()
        self.assertIn("Evidence:", text)
        self.assertIn("commit-abc", text)
        self.assertIn("test-output.log", text)

    def test_bus_footer_y(self) -> None:
        aar = AarFormatter("test-skill")
        aar.set_bus(posted=True)
        output = io.StringIO()
        with patch("sys.stdout", output):
            aar.render()
        self.assertIn("Bus: Y", output.getvalue())

    def test_bus_footer_n(self) -> None:
        aar = AarFormatter("test-skill")
        aar.set_bus(posted=False)
        output = io.StringIO()
        with patch("sys.stdout", output):
            aar.render()
        self.assertIn("Bus: N", output.getvalue())

    def test_bus_footer_with_note(self) -> None:
        aar = AarFormatter("test-skill")
        aar.set_bus(posted=True, note="covered by STATUS at 20260811-0400Z")
        output = io.StringIO()
        with patch("sys.stdout", output):
            aar.render()
        text = output.getvalue()
        self.assertIn("Bus: Y", text)
        self.assertIn("covered by STATUS", text)

    def test_to_dict(self) -> None:
        aar = AarFormatter("test-skill", author="devin", classification="INTERNAL")
        aar.set_mission(objective="obj", success_criteria="sc", constraints="c")
        aar.chronology_entry("ts", "act", "res")
        aar.set_outcome(planned="p", actual="a", delta="d")
        aar.root_cause("dev", ["why1", "why2"])
        aar.sustain("s", "e")
        aar.improve("i", "e")
        aar.recommendation("HIGH", "act", "addr")
        aar.set_evidence(["ev1"])
        aar.set_bus(posted=True, note="note")
        data = aar.to_dict()
        self.assertEqual(data["skill_name"], "test-skill")
        self.assertEqual(data["author"], "devin")
        self.assertEqual(data["classification"], "INTERNAL")
        self.assertEqual(data["mission"]["objective"], "obj")
        self.assertEqual(len(data["chronology"]), 1)
        self.assertEqual(data["outcome"]["planned"], "p")
        self.assertEqual(len(data["root_causes"]), 1)
        self.assertEqual(data["root_causes"][0]["why_chain"], ["why1", "why2"])
        self.assertEqual(len(data["sustains"]), 1)
        self.assertEqual(len(data["improves"]), 1)
        self.assertEqual(len(data["recommendations"]), 1)
        self.assertEqual(data["recommendations"][0]["priority"], "HIGH")
        self.assertEqual(data["evidence"], ["ev1"])
        self.assertTrue(data["bus_posted"])
        self.assertEqual(data["bus_note"], "note")
        self.assertIn("P6", data["applied_codes"])
        self.assertIn("DE7", data["applied_codes"])

    def test_empty_aar_renders(self) -> None:
        aar = AarFormatter("test-skill")
        output = io.StringIO()
        with patch("sys.stdout", output):
            aar.render()
        text = output.getvalue()
        self.assertIn("AAR: test-skill", text)
        self.assertIn("(no chronology entries)", text)
        self.assertIn("(no sustains recorded)", text)
        self.assertIn("(no improves recorded)", text)
        self.assertIn("Base120 Applied: [none]", text)


class HrsiCheckinUnitTests(unittest.TestCase):
    def test_header_includes_date(self) -> None:
        checkin = HrsiCheckin()
        output = io.StringIO()
        with patch("sys.stdout", output):
            checkin.header()
        self.assertIn("HRSI Check-In", output.getvalue())

    def test_cogstate_validation(self) -> None:
        checkin = HrsiCheckin()
        with self.assertRaises(ValueError):
            checkin.cogstate("INVALID")
        checkin.cogstate("AVAILABLE")  # should not raise

    def test_all_cogstates_valid(self) -> None:
        for state in COGSTATES:
            checkin = HrsiCheckin()
            checkin.cogstate(state)

    def test_scale_validation(self) -> None:
        checkin = HrsiCheckin()
        with self.assertRaises(ValueError):
            checkin.baseline(safety=0, mattering=3, connection=3)
        with self.assertRaises(ValueError):
            checkin.baseline(safety=6, mattering=3, connection=3)
        checkin.baseline(safety=5, mattering=1, connection=3)  # should not raise

    def test_sleep_hours_validation(self) -> None:
        checkin = HrsiCheckin()
        with self.assertRaises(ValueError):
            checkin.somatic(sleep_hours=25)
        with self.assertRaises(ValueError):
            checkin.somatic(sleep_hours=-1)
        checkin.somatic(sleep_hours=7.5)  # should not raise

    def test_render_shows_all_fields(self) -> None:
        checkin = HrsiCheckin()
        checkin.cogstate("AVAILABLE")
        checkin.baseline(safety=4, mattering=3, connection=4)
        checkin.somatic(energy=3, sleep_hours=7.5)
        checkin.hule("Felt calm")
        checkin.relational_note("Coffee with Dan")
        output = io.StringIO()
        with patch("sys.stdout", output):
            checkin.render()
        text = output.getvalue()
        self.assertIn("Cogstate:    AVAILABLE", text)
        self.assertIn("Safety:      4/5", text)
        self.assertIn("Mattering:   3/5", text)
        self.assertIn("Connection:  4/5", text)
        self.assertIn("Energy:      3/5", text)
        self.assertIn("Sleep:       7.5h", text)
        self.assertIn("HULE:", text)
        self.assertIn("Relational:", text)

    def test_recovery_shows_dream_chain(self) -> None:
        checkin = HrsiCheckin()
        checkin.cogstate("RECOVERY")
        output = io.StringIO()
        with patch("sys.stdout", output):
            checkin.render()
        self.assertIn("[dream]", output.getvalue())

    def test_available_no_dream_chain(self) -> None:
        checkin = HrsiCheckin()
        checkin.cogstate("AVAILABLE")
        output = io.StringIO()
        with patch("sys.stdout", output):
            checkin.render()
        self.assertNotIn("[dream]", output.getvalue())

    def test_to_dict(self) -> None:
        checkin = HrsiCheckin()
        checkin.cogstate("AVAILABLE")
        checkin.baseline(safety=4, mattering=3, connection=4)
        checkin.somatic(energy=3, sleep_hours=7.5)
        checkin.hule("test hule")
        data = checkin.to_dict()
        self.assertEqual(data["cogstate"], "AVAILABLE")
        self.assertEqual(data["safety"], 4)
        self.assertEqual(data["sleep_hours"], 7.5)
        self.assertEqual(data["hule"], "test hule")

    def test_transition_shows_dream_chain(self) -> None:
        checkin = HrsiCheckin()
        checkin.cogstate("TRANSITION")
        output = io.StringIO()
        with patch("sys.stdout", output):
            checkin.render()
        self.assertIn("[dream]", output.getvalue())

    def test_render_with_history(self) -> None:
        checkin = HrsiCheckin()
        checkin.cogstate("AVAILABLE")
        checkin.baseline(safety=4, mattering=3, connection=4)
        output = io.StringIO()
        with patch("sys.stdout", output):
            checkin.render(
                days_logged=42,
                averages={"S": 4.0, "M": 3.5, "C": 4.0, "E": 3.2},
                trend="up",
            )
        text = output.getvalue()
        self.assertIn("Days logged:  42", text)
        self.assertIn("7-day avg:", text)
        self.assertIn("Trend:", text)

    def test_header_called_twice_no_duplicate(self) -> None:
        checkin = HrsiCheckin()
        output = io.StringIO()
        with patch("sys.stdout", output):
            checkin.header()
            checkin.header()
        self.assertEqual(output.getvalue().count("HRSI Check-In"), 1)

    def test_energy_only_somatic(self) -> None:
        checkin = HrsiCheckin()
        checkin.somatic(energy=4)
        output = io.StringIO()
        with patch("sys.stdout", output):
            checkin.render()
        text = output.getvalue()
        self.assertIn("Energy:      4/5", text)
        self.assertNotIn("Sleep:", text)


class CliMtsmuIntegrationTests(unittest.TestCase):
    def _write_json(self, d: Path, data: object) -> Path:
        p = d / "input.json"
        p.write_text(json.dumps(data), encoding="utf-8")
        return p

    def test_gatebench_base120_mtsmu_shows_summary(self) -> None:
        case = {
            "case_id": "mtsmu-test",
            "severity": "P0",
            "claim": "claim",
            "evidence_refs": [],
            "receipt_refs": [],
            "author_id": "a",
            "evaluator_id": "a",
            "expected_disposition": "reject",
        }
        with TemporaryDirectory() as d:
            p = self._write_json(Path(d), case)
            output = io.StringIO()
            with patch("sys.stdout", output):
                main(["gatebench", str(p), "--base120", "--mtsmu"])
            text = output.getvalue()
            self.assertIn("MTSMU Rigor Summary", text)
            self.assertIn("verify-after", text)

    def test_mtsmu_without_base120_no_effect(self) -> None:
        with TemporaryDirectory() as d:
            p = self._write_json(Path(d), {"a": 1})
            rc = main(["canonicalize", str(p), "--mtsmu"])
            self.assertEqual(rc, 0)


class CliAarIntegrationTests(unittest.TestCase):
    def _write_json(self, d: Path, data: object) -> Path:
        p = d / "input.json"
        p.write_text(json.dumps(data), encoding="utf-8")
        return p

    def test_gatebench_aar_shows_report(self) -> None:
        case = {
            "case_id": "aar-test",
            "severity": "P1",
            "claim": "claim",
            "evidence_refs": ["e1"],
            "receipt_refs": ["r1"],
            "author_id": "a",
            "evaluator_id": "b",
            "expected_disposition": "accept",
        }
        with TemporaryDirectory() as d:
            p = self._write_json(Path(d), case)
            output = io.StringIO()
            with patch("sys.stdout", output):
                main(["gatebench", str(p), "--aar"])
            text = output.getvalue()
            self.assertIn("AAR: hummbl-eval gatebench", text)
            self.assertIn("Mission & Intent", text)
            self.assertIn("Chronology", text)
            self.assertIn("Outcome vs Plan", text)
            self.assertIn("Sustains", text)
            self.assertIn("Base120 Applied:", text)
            self.assertIn("Bus:", text)

    def test_gatebench_aar_reject_shows_root_cause(self) -> None:
        case = {
            "case_id": "aar-reject",
            "severity": "P0",
            "claim": "claim",
            "evidence_refs": [],
            "receipt_refs": [],
            "author_id": "a",
            "evaluator_id": "a",
            "expected_disposition": "reject",
        }
        with TemporaryDirectory() as d:
            p = self._write_json(Path(d), case)
            output = io.StringIO()
            with patch("sys.stdout", output):
                main(["gatebench", str(p), "--aar"])
            text = output.getvalue()
            self.assertIn("Root Causes", text)
            self.assertIn("Improves", text)
            self.assertIn("Recommendations", text)
            self.assertIn("[HIGH]", text)

    def test_canonicalize_aar_shows_report(self) -> None:
        with TemporaryDirectory() as d:
            p = self._write_json(Path(d), {"a": 1})
            output = io.StringIO()
            with patch("sys.stdout", output):
                rc = main(["canonicalize", str(p), "--aar"])
            self.assertEqual(rc, 0)
            text = output.getvalue()
            self.assertIn("AAR: hummbl-eval canonicalize", text)
            self.assertIn("Mission & Intent", text)

    def test_aar_with_krineia_composes(self) -> None:
        case = {
            "case_id": "aar-krineia",
            "severity": "P1",
            "claim": "claim",
            "evidence_refs": ["e1"],
            "receipt_refs": ["r1"],
            "author_id": "a",
            "evaluator_id": "b",
            "expected_disposition": "accept",
        }
        with TemporaryDirectory() as d:
            p = self._write_json(Path(d), case)
            output = io.StringIO()
            with patch("sys.stdout", output):
                main(["gatebench", str(p), "--aar", "--krineia"])
            text = output.getvalue()
            self.assertIn("AAR: hummbl-eval gatebench", text)
            self.assertIn("Krineia Receipt", text)


class CliHrsiIntegrationTests(unittest.TestCase):
    def _write_json(self, d: Path, data: object) -> Path:
        p = d / "input.json"
        p.write_text(json.dumps(data), encoding="utf-8")
        return p

    def test_gatebench_hrsi_shows_checkin(self) -> None:
        case = {
            "case_id": "hrsi-test",
            "severity": "P1",
            "claim": "claim",
            "evidence_refs": ["e1"],
            "receipt_refs": ["r1"],
            "author_id": "a",
            "evaluator_id": "b",
            "expected_disposition": "accept",
        }
        with TemporaryDirectory() as d:
            p = self._write_json(Path(d), case)
            output = io.StringIO()
            with patch("sys.stdout", output):
                main(["gatebench", str(p), "--hrsi"])
            text = output.getvalue()
            self.assertIn("HRSI Check-In", text)
            self.assertIn("Cogstate:", text)
            self.assertIn("Safety:", text)

    def test_canonicalize_hrsi_shows_checkin(self) -> None:
        with TemporaryDirectory() as d:
            p = self._write_json(Path(d), {"a": 1})
            output = io.StringIO()
            with patch("sys.stdout", output):
                rc = main(["canonicalize", str(p), "--hrsi"])
            self.assertEqual(rc, 0)
            self.assertIn("HRSI Check-In", output.getvalue())


class FullCompositionTests(unittest.TestCase):
    """Test all flags composing together: --base120 --mtsmu --krineia."""

    def _write_json(self, d: Path, data: object) -> Path:
        p = d / "input.json"
        p.write_text(json.dumps(data), encoding="utf-8")
        return p

    def test_full_composition(self) -> None:
        case = {
            "case_id": "full-comp",
            "severity": "P0",
            "claim": "claim",
            "evidence_refs": [],
            "receipt_refs": [],
            "author_id": "a",
            "evaluator_id": "a",
            "expected_disposition": "reject",
        }
        with TemporaryDirectory() as d:
            p = self._write_json(Path(d), case)
            output = io.StringIO()
            with patch("sys.stdout", output):
                main(["gatebench", str(p), "--base120", "--mtsmu", "--krineia"])
            text = output.getvalue()
            # All three layers present
            self.assertIn("Base120 Applied:", text)
            self.assertIn("MTSMU Rigor Summary", text)
            self.assertIn("Krineia Receipt", text)
            # Order: Base120 footer -> MTSMU -> Krineia
            b120_pos = text.index("Base120 Applied:")
            mtsmu_pos = text.index("MTSMU Rigor Summary")
            krineia_pos = text.index("Krineia Receipt")
            self.assertLess(b120_pos, mtsmu_pos)
            self.assertLess(mtsmu_pos, krineia_pos)


class AddArgTests(unittest.TestCase):
    def test_mtsmu_flag_defaults_false(self) -> None:
        import argparse

        parser = argparse.ArgumentParser()
        add_mtsmu_arg(parser)
        args = parser.parse_args([])
        self.assertFalse(args.mtsmu)

    def test_aar_flag_defaults_false(self) -> None:
        import argparse

        parser = argparse.ArgumentParser()
        add_aar_arg(parser)
        args = parser.parse_args([])
        self.assertFalse(args.aar)

    def test_hrsi_flag_defaults_false(self) -> None:
        import argparse

        parser = argparse.ArgumentParser()
        add_hrsi_arg(parser)
        args = parser.parse_args([])
        self.assertFalse(args.hrsi)


if __name__ == "__main__":
    unittest.main()
