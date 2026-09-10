"""Tests for Base120 cognitive structuring output."""

import io
import json
import os
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from hummbl_eval.base120 import (
    BASE120_CODES,
    REGISTRY_COUNT,
    REGISTRY_SOURCE,
    Base120Formatter,
    _load_registry,
)
from hummbl_eval.cli import main


class Base120FormatterTests(unittest.TestCase):
    def test_header_contains_skill_name_and_label(self) -> None:
        fmt = Base120Formatter("TestSkill")
        output = io.StringIO()
        with patch("sys.stdout", output):
            fmt.header()
        self.assertIn("TestSkill", output.getvalue())
        self.assertIn("Base120 Cognitive Structuring", output.getvalue())

    def test_section_tracks_code(self) -> None:
        fmt = Base120Formatter("TestSkill")
        output = io.StringIO()
        with patch("sys.stdout", output):
            fmt.header()
            fmt.section("Overview", "P6")
            fmt.footer()
        text = output.getvalue()
        self.assertIn("P6", text)
        self.assertIn("Point-of-View Anchoring", text)
        self.assertIn("Base120 Applied: P6", text)

    def test_finding_includes_why_reveals_action(self) -> None:
        fmt = Base120Formatter("TestSkill")
        output = io.StringIO()
        with patch("sys.stdout", output):
            fmt.header()
            fmt.section("Findings", "DE1")
            fmt.finding(
                title="Missing eval suite",
                severity="CRIT",
                why="No ground truth exists.",
                reveals="Accuracy claims are untestable.",
                action="Create eval/ with corpus cases.",
                code="DE1",
            )
            fmt.footer()
        text = output.getvalue()
        self.assertIn("[CRIT]", text)
        self.assertIn("Why: No ground truth exists.", text)
        self.assertIn("Reveals: Accuracy claims are untestable.", text)
        self.assertIn("Action: Create eval/ with corpus cases.", text)
        self.assertIn("Base120 Applied: DE1", text)

    def test_multiple_codes_in_footer(self) -> None:
        fmt = Base120Formatter("TestSkill")
        output = io.StringIO()
        with patch("sys.stdout", output):
            fmt.header()
            fmt.section("Overview", "P6")
            fmt.section("Findings", "DE1")
            fmt.section("Recommendations", "IN20")
            fmt.footer()
        text = output.getvalue()
        self.assertIn("Base120 Applied: DE1, IN20, P6", text)

    def test_metric_prints_label_and_value(self) -> None:
        fmt = Base120Formatter("TestSkill")
        output = io.StringIO()
        with patch("sys.stdout", output):
            fmt.header()
            fmt.section("Overview", "P6")
            fmt.metric("Skills scanned", 42)
            fmt.footer()
        text = output.getvalue()
        self.assertIn("Skills scanned: 42", text)

    def test_unknown_code_passes_through(self) -> None:
        fmt = Base120Formatter("TestSkill")
        output = io.StringIO()
        with patch("sys.stdout", output):
            fmt.header()
            fmt.section("Custom", "XX99")
            fmt.footer()
        text = output.getvalue()
        self.assertIn("XX99", text)

    def test_base120_codes_catalog_has_known_entries(self) -> None:
        self.assertIn("P6", BASE120_CODES)
        self.assertIn("DE1", BASE120_CODES)
        self.assertIn("IN5", BASE120_CODES)
        self.assertEqual(BASE120_CODES["P6"], "Point-of-View Anchoring")

    def test_finding_with_detail_appends_dash(self) -> None:
        fmt = Base120Formatter("TestSkill")
        output = io.StringIO()
        with patch("sys.stdout", output):
            fmt.header()
            fmt.finding(
                title="Missing eval",
                severity="WARN",
                why="No ground truth.",
                reveals="Untestable.",
                action="Create eval/.",
                code="DE1",
                detail="skill-audit",
            )
            fmt.footer()
        self.assertIn("Missing eval — skill-audit", output.getvalue())

    def test_analysis_block_prints_why_reveals_action(self) -> None:
        fmt = Base120Formatter("TestSkill")
        output = io.StringIO()
        with patch("sys.stdout", output):
            fmt.header()
            fmt.analysis(
                code="IN20",
                why="Anti-pattern propagates.",
                reveals="Fleet has gaps.",
                action="Block sync for CRIT skills.",
            )
            fmt.footer()
        text = output.getvalue()
        self.assertIn("[IN20]", text)
        self.assertIn("Why: Anti-pattern propagates.", text)
        self.assertIn("Reveals: Fleet has gaps.", text)
        self.assertIn("Action: Block sync for CRIT skills.", text)

    def test_raw_prints_text_with_indent(self) -> None:
        fmt = Base120Formatter("TestSkill")
        output = io.StringIO()
        with patch("sys.stdout", output):
            fmt.header()
            fmt.raw("Custom line", indent=4)
            fmt.footer()
        self.assertIn("    Custom line", output.getvalue())

    def test_applied_codes_returns_copy(self) -> None:
        fmt = Base120Formatter("TestSkill")
        output = io.StringIO()
        with patch("sys.stdout", output):
            fmt.header()
            fmt.section("S1", "P6")
            fmt.footer()
        codes = fmt.applied_codes
        codes.add("FAKE")
        self.assertNotIn("FAKE", fmt.applied_codes)

    def test_footer_includes_registry_source(self) -> None:
        fmt = Base120Formatter("TestSkill")
        output = io.StringIO()
        with patch("sys.stdout", output):
            fmt.header()
            fmt.section("S1", "P6")
            fmt.footer()
        text = output.getvalue()
        self.assertIn("Registry:", text)
        self.assertIn(f"({REGISTRY_COUNT} operators)", text)


class RegistryLoadingTests(unittest.TestCase):
    def test_registry_loaded_with_120_operators(self) -> None:
        """When the bundled registry is available, all 120 codes load."""
        self.assertGreaterEqual(REGISTRY_COUNT, 120)
        self.assertIn(
            REGISTRY_SOURCE,
            ("bundled", "env", "founder-mode", "base120-yaml", "fallback"),
        )

    def test_all_six_families_present(self) -> None:
        families = {"P", "IN", "CO", "DE", "RE", "SY"}
        present = {code.rstrip("0123456789") for code in BASE120_CODES}
        self.assertEqual(families, present)

    def test_codes_not_in_fallback_are_resolved(self) -> None:
        """Codes like P2, IN10, CO3 should resolve to real names from the registry."""
        # These are NOT in the fallback dict — they only resolve if the registry loaded
        if REGISTRY_SOURCE == "fallback":
            self.skipTest("registry not available — fallback only has 27 codes")
        self.assertIn("P2", BASE120_CODES)
        self.assertIn("IN10", BASE120_CODES)
        self.assertIn("CO3", BASE120_CODES)
        self.assertIn("SY7", BASE120_CODES)
        self.assertNotEqual(BASE120_CODES["P2"], "P2")  # should be a real name

    def test_env_var_override(self) -> None:
        """BASE120_REGISTRY_PATH env var takes priority over bundled."""
        with TemporaryDirectory() as directory:
            custom_path = Path(directory) / "custom.json"
            custom_data = [{"id": "P1", "name": "Custom P1"}, {"id": "XX1", "name": "Custom XX"}]
            custom_path.write_text(json.dumps(custom_data), encoding="utf-8")
            with patch.dict(os.environ, {"BASE120_REGISTRY_PATH": str(custom_path)}):
                codes, source = _load_registry()
            self.assertEqual(source, "env")
            self.assertEqual(codes["P1"], "Custom P1")
            self.assertEqual(codes["XX1"], "Custom XX")

    def test_fallback_when_no_registry_available(self) -> None:
        """When env var is unset and bundled is missing, fallback is used."""
        # Clear env var and mock the bundled path to fail
        env = {k: v for k, v in os.environ.items() if k != "BASE120_REGISTRY_PATH"}
        with patch.dict(os.environ, env, clear=True):
            with patch("hummbl_eval.base120.resources.files", side_effect=ModuleNotFoundError):
                codes, source = _load_registry()
        self.assertEqual(source, "fallback")
        self.assertIn("P6", codes)
        self.assertEqual(len(codes), 27)


class CliBase120Tests(unittest.TestCase):
    def test_gatebench_base120_output_is_structured_text(self) -> None:
        with TemporaryDirectory() as directory:
            path = Path(directory) / "case.json"
            path.write_text(
                '{"case_id":"GB-P0-X","severity":"P0","claim":"x",'
                '"evidence_refs":[],"receipt_refs":["r"],'
                '"author_id":"a","evaluator_id":"b",'
                '"expected_disposition":"reject"}',
                encoding="utf-8",
            )
            output = io.StringIO()
            with patch("sys.stdout", output):
                code = main(["gatebench", "--base120", str(path)])
            text = output.getvalue()
            self.assertEqual(code, 4)
            self.assertIn("Base120 Cognitive Structuring", text)
            self.assertIn("GB-P0-X", text)
            self.assertIn("reject", text)
            self.assertIn("Why:", text)
            self.assertIn("Reveals:", text)
            self.assertIn("Action:", text)
            self.assertIn("Base120 Applied:", text)

    def test_gatebench_base120_accept_case_shows_pass(self) -> None:
        with TemporaryDirectory() as directory:
            path = Path(directory) / "case.json"
            path.write_text(
                '{"case_id":"GB-P0-A","severity":"P0","claim":"x",'
                '"evidence_refs":["e1"],"receipt_refs":["r"],'
                '"author_id":"a","evaluator_id":"b",'
                '"expected_disposition":"accept"}',
                encoding="utf-8",
            )
            output = io.StringIO()
            with patch("sys.stdout", output):
                code = main(["gatebench", "--base120", str(path)])
            text = output.getvalue()
            self.assertEqual(code, 0)
            self.assertIn("accept", text)
            self.assertIn("Base120 Applied:", text)

    def test_gatebench_without_base120_still_outputs_json(self) -> None:
        with TemporaryDirectory() as directory:
            path = Path(directory) / "case.json"
            path.write_text(
                '{"case_id":"GB-P0-X","severity":"P0","claim":"x",'
                '"evidence_refs":[],"receipt_refs":["r"],'
                '"author_id":"a","evaluator_id":"b",'
                '"expected_disposition":"reject"}',
                encoding="utf-8",
            )
            output = io.StringIO()
            with patch("sys.stdout", output):
                main(["gatebench", str(path)])
            text = output.getvalue()
            # Should be JSON, not Base120 structured text
            parsed = json.loads(text)
            self.assertIn("disposition", parsed)
            self.assertNotIn("Base120 Cognitive Structuring", text)

    def test_canonicalize_base120_shows_digest_and_summary(self) -> None:
        with TemporaryDirectory() as directory:
            path = Path(directory) / "value.json"
            path.write_text('{"b":2,"a":1}', encoding="utf-8")
            output = io.StringIO()
            with patch("sys.stdout", output):
                code = main(["canonicalize", "--base120", str(path)])
            text = output.getvalue()
            self.assertEqual(code, 0)
            self.assertIn("Base120 Cognitive Structuring", text)
            self.assertIn("sha256:", text)
            self.assertIn("Base120 Applied:", text)

    def test_canonicalize_base120_with_array_input(self) -> None:
        with TemporaryDirectory() as directory:
            path = Path(directory) / "value.json"
            path.write_text("[1,2,3]", encoding="utf-8")
            output = io.StringIO()
            with patch("sys.stdout", output):
                code = main(["canonicalize", "--base120", str(path)])
            text = output.getvalue()
            self.assertEqual(code, 0)
            self.assertIn("Array length: 3", text)

    def test_canonicalize_base120_with_scalar_input(self) -> None:
        with TemporaryDirectory() as directory:
            path = Path(directory) / "value.json"
            path.write_text('"hello"', encoding="utf-8")
            output = io.StringIO()
            with patch("sys.stdout", output):
                code = main(["canonicalize", "--base120", str(path)])
            text = output.getvalue()
            self.assertEqual(code, 0)
            self.assertIn("Type: str", text)


if __name__ == "__main__":
    unittest.main()
