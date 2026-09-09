"""Tests for Krineia receipt integration in hummbl-eval."""

import io
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from hummbl_eval.base120 import Base120Formatter
from hummbl_eval.cli import main
from hummbl_eval.krineia import (
    STANCES,
    VERIFY_METHODS,
    KrineiaReceipt,
    KrineiaReceiptError,
    KrineiaSeparationError,
    add_krineia_arg,
)


class KrineiaReceiptUnitTests(unittest.TestCase):
    def test_valid_receipt(self) -> None:
        receipt = KrineiaReceipt(
            reasoned_by="devin session=001",
            observed_agent="skill-audit",
            falsifiability_anchor="re-run on clean fleet -> CRIT count = 0",
        )
        self.assertEqual(receipt.stance, "descriptive")

    def test_missing_field_raises(self) -> None:
        with self.assertRaises(KrineiaReceiptError):
            KrineiaReceipt(reasoned_by="", observed_agent="x", falsifiability_anchor="y")

    def test_invalid_stance_rejected(self) -> None:
        with self.assertRaises(KrineiaReceiptError):
            KrineiaReceipt(
                reasoned_by="a",
                observed_agent="b",
                falsifiability_anchor="c",
                stance="invalid",
            )

    def test_separation_check_same_identity_raises(self) -> None:
        receipt = KrineiaReceipt(
            reasoned_by="devin",
            observed_agent="devin (self)",
            falsifiability_anchor="test",
        )
        with self.assertRaises(KrineiaSeparationError):
            receipt.check_separation()

    def test_separation_check_different_identity_passes(self) -> None:
        receipt = KrineiaReceipt(
            reasoned_by="devin",
            observed_agent="target-system",
            falsifiability_anchor="test",
        )
        receipt.check_separation()  # should not raise

    def test_render_includes_receipt_header(self) -> None:
        receipt = KrineiaReceipt(
            reasoned_by="devin",
            observed_agent="target",
            falsifiability_anchor="test anchor",
        )
        output = io.StringIO()
        with patch("sys.stdout", output):
            receipt.render()
        self.assertIn("Krineia Receipt", output.getvalue())
        self.assertIn("Reasoned-by: devin", output.getvalue())
        self.assertIn("Observed-agent: target", output.getvalue())

    def test_render_includes_disclaimer(self) -> None:
        receipt = KrineiaReceipt(
            reasoned_by="devin",
            observed_agent="target",
            falsifiability_anchor="test",
        )
        output = io.StringIO()
        with patch("sys.stdout", output):
            receipt.render()
        text = output.getvalue()
        self.assertIn("MTSMU receipt footer", text)
        self.assertIn("krineia-watcher", text)

    def test_to_dict_returns_all_fields(self) -> None:
        receipt = KrineiaReceipt(
            reasoned_by="devin",
            observed_agent="target",
            falsifiability_anchor="anchor",
            stance="prescriptive",
            source="verified",
            session_id="sess-1",
        )
        data = receipt.to_dict()
        self.assertEqual(data["reasoned_by"], "devin")
        self.assertEqual(data["observed_agent"], "target")
        self.assertEqual(data["stance"], "prescriptive")
        self.assertEqual(data["session_id"], "sess-1")

    def test_all_stances_valid(self) -> None:
        for stance in STANCES:
            KrineiaReceipt(
                reasoned_by="a",
                observed_agent="b",
                falsifiability_anchor="c",
                stance=stance,
            )

    def test_all_verify_methods_valid(self) -> None:
        for vm in VERIFY_METHODS:
            KrineiaReceipt(
                reasoned_by="a",
                observed_agent="b",
                falsifiability_anchor="c",
                verify_method_default=vm,
            )


class KrineiaFormatterCompositionTests(unittest.TestCase):
    """Test that --krineia composes with --base120 in the formatter."""

    def test_finding_with_verify_method(self) -> None:
        fmt = Base120Formatter("TestSkill")
        output = io.StringIO()
        with patch("sys.stdout", output):
            fmt.header()
            fmt.section("Findings", "DE1")
            fmt.finding(
                title="Missing eval",
                severity="CRIT",
                why="No ground truth",
                reveals="Untestable",
                action="Create eval/",
                verify_method="verify-after",
            )
            fmt.footer()
        text = output.getvalue()
        self.assertIn("Verify-method: verify-after", text)

    def test_finding_with_uncertainty(self) -> None:
        fmt = Base120Formatter("TestSkill")
        output = io.StringIO()
        with patch("sys.stdout", output):
            fmt.header()
            fmt.finding(
                title="Issue",
                severity="WARN",
                why="reason",
                reveals="insight",
                action="fix",
                uncertainty="medium — no baseline",
            )
            fmt.footer()
        self.assertIn("Uncertainty: medium", output.getvalue())

    def test_finding_without_krineia_fields_omits_them(self) -> None:
        fmt = Base120Formatter("TestSkill")
        output = io.StringIO()
        with patch("sys.stdout", output):
            fmt.header()
            fmt.finding(
                title="Issue",
                severity="WARN",
                why="reason",
                reveals="insight",
                action="fix",
            )
            fmt.footer()
        text = output.getvalue()
        self.assertNotIn("Verify-method:", text)
        self.assertNotIn("Uncertainty:", text)

    def test_analysis_with_verify_method(self) -> None:
        fmt = Base120Formatter("TestSkill")
        output = io.StringIO()
        with patch("sys.stdout", output):
            fmt.header()
            fmt.analysis(
                code="SY13",
                why="reason",
                reveals="insight",
                action="fix",
                verify_method="cross-check",
            )
            fmt.footer()
        self.assertIn("Verify-method: cross-check", output.getvalue())


class CliKrineiaIntegrationTests(unittest.TestCase):
    """Test --krineia flag in the CLI."""

    def _write_json(self, d: Path, data: object) -> Path:
        p = d / "input.json"
        p.write_text(json.dumps(data), encoding="utf-8")
        return p

    def test_canonicalize_base120_krineia_shows_receipt(self) -> None:
        with TemporaryDirectory() as d:
            p = self._write_json(Path(d), {"b": 2, "a": 1})
            output = io.StringIO()
            with patch("sys.stdout", output):
                rc = main(["canonicalize", str(p), "--base120", "--krineia"])
            self.assertEqual(rc, 0)
            text = output.getvalue()
            self.assertIn("Base120 Applied:", text)
            self.assertIn("Krineia Receipt", text)
            self.assertIn("Reasoned-by:", text)
            self.assertIn("Falsifiability anchor:", text)

    def test_canonicalize_base120_without_krineia_no_receipt(self) -> None:
        with TemporaryDirectory() as d:
            p = self._write_json(Path(d), {"b": 2, "a": 1})
            output = io.StringIO()
            with patch("sys.stdout", output):
                rc = main(["canonicalize", str(p), "--base120"])
            self.assertEqual(rc, 0)
            text = output.getvalue()
            self.assertIn("Base120 Applied:", text)
            self.assertNotIn("Krineia Receipt", text)

    def test_gatebench_base120_krineia_shows_receipt(self) -> None:
        case = {
            "case_id": "test-krineia-001",
            "severity": "P1",
            "claim": "The system works correctly.",
            "evidence_refs": ["test-log-001"],
            "receipt_refs": ["receipt-001"],
            "author_id": "agent-a",
            "evaluator_id": "agent-b",
            "expected_disposition": "accept",
        }
        with TemporaryDirectory() as d:
            p = self._write_json(Path(d), case)
            output = io.StringIO()
            with patch("sys.stdout", output):
                main(["gatebench", str(p), "--base120", "--krineia"])
            text = output.getvalue()
            self.assertIn("Krineia Receipt", text)
            self.assertIn("Falsifiability anchor:", text)

    def test_gatebench_reject_with_krineia_shows_verify_method(self) -> None:
        # A case that will be rejected (author == evaluator = receipt laundering)
        case = {
            "case_id": "reject-test",
            "severity": "P0",
            "claim": "Unverified claim",
            "evidence_refs": [],
            "receipt_refs": [],
            "author_id": "agent-a",
            "evaluator_id": "agent-a",
            "expected_disposition": "reject",
        }
        with TemporaryDirectory() as d:
            p = self._write_json(Path(d), case)
            output = io.StringIO()
            with patch("sys.stdout", output):
                main(["gatebench", str(p), "--base120", "--krineia"])
            text = output.getvalue()
            self.assertIn("Verify-method: verify-after", text)

    def test_krineia_without_base120_has_no_effect(self) -> None:
        with TemporaryDirectory() as d:
            p = self._write_json(Path(d), {"a": 1})
            # --krineia without --base120 is a no-op; canonical bytes go to stdout.buffer
            # Just verify it doesn't crash and returns 0
            rc = main(["canonicalize", str(p), "--krineia"])
            self.assertEqual(rc, 0)


class AddKrineiaArgTests(unittest.TestCase):
    def test_flag_defaults_false(self) -> None:
        import argparse

        parser = argparse.ArgumentParser()
        add_krineia_arg(parser)
        args = parser.parse_args([])
        self.assertFalse(args.krineia)

    def test_flag_sets_true(self) -> None:
        import argparse

        parser = argparse.ArgumentParser()
        add_krineia_arg(parser)
        args = parser.parse_args(["--krineia"])
        self.assertTrue(args.krineia)


if __name__ == "__main__":
    unittest.main()
