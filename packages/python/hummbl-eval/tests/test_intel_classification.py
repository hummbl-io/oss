import tempfile
import unittest
from pathlib import Path

from scripts.validate_intel_classification import TERMS, validate


class IntelClassificationTests(unittest.TestCase):
    def test_supported_terms_include_standard_and_custom_lanes(self) -> None:
        self.assertTrue({"TECHINT", "MASINT", "REGINT", "OPSINT", "GITINT"}.issubset(TERMS))

    def test_valid_boundary_metadata_passes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "finding.md"
            path.write_text(
                "---\nintel_type: TECHINT|GITINT\nintel_source: repo\nintel_confidence: 0.9\n---\n",
                encoding="utf-8",
            )
            self.assertEqual(validate(path), [])

    def test_missing_metadata_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "finding.md"
            path.write_text("# Finding\n", encoding="utf-8")
            self.assertEqual(validate(path), ["missing intel_type"])

    def test_geoint_topology_pairing_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "finding.md"
            path.write_text(
                "---\nintel_type: GEOINT\n---\nRepository topology finding\n",
                encoding="utf-8",
            )
            self.assertIn("use TOPOINT", validate(path)[0])


if __name__ == "__main__":
    unittest.main()
