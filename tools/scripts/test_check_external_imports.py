"""Unit tests for check_external_imports.py."""

from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from check_external_imports import check_external_imports, _simple_validate

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent


class TestCheckExternalImports(unittest.TestCase):
    def test_real_repo_check(self):
        """Verify check_external_imports passes cleanly on real repository tree."""
        code, errors = check_external_imports(_REPO_ROOT)
        self.assertEqual(code, 0, f"check_external_imports failed: {errors}")
        self.assertEqual(errors, [])

    def test_simple_validate_rejects_missing_required(self):
        schema = {"type": "object", "required": ["foo"], "properties": {"foo": {"type": "string"}}}
        errors = _simple_validate({}, schema)
        self.assertTrue(any("missing required field 'foo'" in e for e in errors))

    def test_simple_validate_rejects_unexpected_property(self):
        schema = {
            "type": "object",
            "additionalProperties": False,
            "properties": {"foo": {"type": "string"}},
        }
        errors = _simple_validate({"foo": "bar", "extra": 123}, schema)
        self.assertTrue(any("unexpected property 'extra'" in e for e in errors))

    def test_tampered_fixture_fails(self):
        """Simulate a repository clone with a tampered fixture file."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_copy = Path(tmp_dir) / "repo"
            shutil.copytree(_REPO_ROOT / "schemas", repo_copy / "schemas")
            shutil.copytree(
                _REPO_ROOT / "packages" / "python" / "hummbl-contracts",
                repo_copy / "packages" / "python" / "hummbl-contracts",
            )

            code, errors = check_external_imports(repo_copy)
            self.assertEqual(code, 0, f"Clean copy failed: {errors}")

            target_fixture = (
                repo_copy
                / "packages"
                / "python"
                / "hummbl-contracts"
                / "tests"
                / "fixtures"
                / "json-schema-test-suite"
                / "type.json"
            )
            target_fixture.write_bytes(b"[]")

            code, errors = check_external_imports(repo_copy)
            self.assertEqual(code, 1)
            self.assertTrue(any("size mismatch" in e or "sha256 mismatch" in e for e in errors))

    def test_unlisted_fixture_fails(self):
        """Simulate an unlisted file in fixture directory."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_copy = Path(tmp_dir) / "repo"
            shutil.copytree(_REPO_ROOT / "schemas", repo_copy / "schemas")
            shutil.copytree(
                _REPO_ROOT / "packages" / "python" / "hummbl-contracts",
                repo_copy / "packages" / "python" / "hummbl-contracts",
            )

            extra_file = (
                repo_copy
                / "packages"
                / "python"
                / "hummbl-contracts"
                / "tests"
                / "fixtures"
                / "json-schema-test-suite"
                / "rogue.json"
            )
            extra_file.write_text("{}", encoding="utf-8")

            code, errors = check_external_imports(repo_copy)
            self.assertEqual(code, 1)
            self.assertTrue(any("unlisted file(s) found" in e for e in errors))

    def test_missing_license_attribution_fails(self):
        """Simulate missing attribution in license file."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_copy = Path(tmp_dir) / "repo"
            shutil.copytree(_REPO_ROOT / "schemas", repo_copy / "schemas")
            shutil.copytree(
                _REPO_ROOT / "packages" / "python" / "hummbl-contracts",
                repo_copy / "packages" / "python" / "hummbl-contracts",
            )

            lic_file = (
                repo_copy
                / "packages"
                / "python"
                / "hummbl-contracts"
                / "tests"
                / "fixtures"
                / "json-schema-test-suite"
                / "LICENSE"
            )
            lic_file.write_text("No author attribution here.", encoding="utf-8")

            code, errors = check_external_imports(repo_copy)
            self.assertEqual(code, 1)
            self.assertTrue(any("attribution string" in e and "not found" in e for e in errors))


if __name__ == "__main__":
    unittest.main()
