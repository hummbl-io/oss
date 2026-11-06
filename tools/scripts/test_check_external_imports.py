"""Unit tests for check_external_imports.py."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from check_external_imports import check_external_imports, _simple_validate

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent


class TestCheckExternalImports(unittest.TestCase):
    def _make_repository(self, tmp_dir):
        """Build a small valid import with separate fixture and license directories."""
        repo = Path(tmp_dir) / "repo"
        schema_dir = repo / "schemas" / "public"
        schema_dir.mkdir(parents=True)
        shutil.copy2(
            _REPO_ROOT / "schemas" / "public" / "external-import-record-v1.schema.json",
            schema_dir,
        )
        record = json.loads(
            (_REPO_ROOT / "packages/python/hummbl-contracts/provenance/json-schema-test-suite.import.json")
            .read_text(encoding="utf-8")
        )
        fixture = repo / "fixtures" / "sample.json"
        fixture.parent.mkdir()
        content = b"{}"
        fixture.write_bytes(content)
        license_file = repo / "licenses" / "LICENSE"
        license_file.parent.mkdir()
        license_file.write_text("Example attribution", encoding="utf-8")
        record["identity_and_selection"]["destination_paths"] = ["fixtures/sample.json"]
        record["integrity"]["file_count"] = 1
        record["integrity"]["inventory"] = [{
            "filename": "sample.json",
            "source_path": "sample.json",
            "destination_path": "fixtures/sample.json",
            "bytes": len(content),
            "sha256": hashlib.sha256(content).hexdigest(),
            "git_blob_sha": hashlib.sha1(b"blob 2\x00" + content).hexdigest(),
        }]
        record["rights"]["license_files"] = ["licenses/LICENSE"]
        record["rights"]["attributions"] = ["Example attribution"]
        record_file = repo / "packages" / "example" / "provenance" / "example.import.json"
        record_file.parent.mkdir(parents=True)
        record_file.write_text(json.dumps(record), encoding="utf-8")
        return repo, record_file, record

    def test_declared_schema_constraints_reject_invalid_records(self):
        cases = [
            (("record_id",), "INVALID ID", "pattern"),
            (("identity_and_selection", "immutable_source_revision"), "not-a-commit", "pattern"),
            (("identity_and_selection", "upstream_repository"), "", "minLength"),
            (("identity_and_selection", "selected_source_paths"), [], "minItems"),
            (("identity_and_selection", "selected_source_paths", 0), "", "minLength"),
            (("integrity", "file_count"), 0, "minimum"),
            (("integrity", "inventory"), [], "minItems"),
            (("integrity", "inventory", 0, "bytes"), -1, "minimum"),
            (("integrity", "inventory", 0, "sha256"), "x" * 64, "pattern"),
            (("integrity", "inventory", 0, "git_blob_sha"), "a" * 39, "pattern"),
            (("rights", "license_files"), [], "minItems"),
            (("rights", "attributions"), [], "minItems"),
            (("rights", "declared_licenses"), [], "minItems"),
        ]
        for keys, invalid, keyword in cases:
            with self.subTest(field=keys), tempfile.TemporaryDirectory() as tmp_dir:
                repo, record_file, record = self._make_repository(tmp_dir)
                target = record
                for key in keys[:-1]:
                    target = target[key]
                target[keys[-1]] = invalid
                record_file.write_text(json.dumps(record), encoding="utf-8")
                code, errors = check_external_imports(repo)
                self.assertEqual(code, 1)
                self.assertTrue(any(keyword in error for error in errors), errors)

    def test_schema_constraint_boundaries_and_pattern_search(self):
        self.assertEqual(_simple_validate("\U0001f600x", {"minLength": 2}), [])
        self.assertEqual(_simple_validate([1, 2], {"minItems": 2}), [])
        self.assertEqual(_simple_validate(0, {"minimum": 0}), [])
        self.assertEqual(_simple_validate("a needle here", {"pattern": "needle"}), [])
        self.assertEqual(_simple_validate(False, {"minimum": 1}), [])
        self.assertTrue(_simple_validate(True, {"type": "integer", "minimum": 0}))

    def test_clean_small_repository_passes_with_relative_root(self):
        with tempfile.TemporaryDirectory(dir=_REPO_ROOT) as tmp_dir:
            repo, _, _ = self._make_repository(tmp_dir)
            relative_root = Path(os.path.relpath(repo))
            code, errors = check_external_imports(relative_root)
            self.assertEqual((code, errors), (0, []))

    def test_escaping_paths_are_rejected_before_file_reads(self):
        for field in ("destination_path", "license_files"):
            for path_kind in ("absolute", "traversal", "windows_absolute", "windows_drive_relative",
                              "windows_rooted", "unc", "windows_traversal"):
                with self.subTest(field=field, kind=path_kind), tempfile.TemporaryDirectory() as tmp_dir:
                    repo, record_file, record = self._make_repository(tmp_dir)
                    outside = Path(tmp_dir) / "outside.txt"
                    outside.write_text("Example attribution", encoding="utf-8")
                    paths = {
                        "absolute": str(outside.resolve()),
                        "traversal": "../outside.txt",
                        "windows_absolute": "C:/outside.txt",
                        "windows_drive_relative": "C:outside.txt",
                        "windows_rooted": "\\outside.txt",
                        "unc": "\\\\server\\share\\outside.txt",
                        "windows_traversal": "fixtures\\..\\..\\outside.txt",
                    }
                    if field == "destination_path":
                        record["integrity"]["inventory"][0][field] = paths[path_kind]
                    else:
                        record["rights"][field] = [paths[path_kind]]
                    record_file.write_text(json.dumps(record), encoding="utf-8")
                    self._assert_no_outside_read(repo, outside)

    def _assert_no_outside_read(self, repo, outside):
        read_bytes, read_text = Path.read_bytes, Path.read_text

        def guarded_bytes(path, *args, **kwargs):
            self.assertNotEqual(path.resolve(), outside.resolve(), "Read escaped repository")
            return read_bytes(path, *args, **kwargs)

        def guarded_text(path, *args, **kwargs):
            self.assertNotEqual(path.resolve(), outside.resolve(), "Read escaped repository")
            return read_text(path, *args, **kwargs)

        with patch.object(Path, "read_bytes", guarded_bytes), patch.object(Path, "read_text", guarded_text):
            code, errors = check_external_imports(repo)
        self.assertEqual(code, 1)
        self.assertTrue(any("unsafe" in error and "path" in error for error in errors), errors)

    def test_symlink_escapes_are_rejected_before_file_reads(self):
        for field in ("destination_path", "license_files", "record", "schema"):
            with self.subTest(field=field), tempfile.TemporaryDirectory() as tmp_dir:
                repo, record_file, record = self._make_repository(tmp_dir)
                outside = Path(tmp_dir) / "outside.txt"
                outside.write_text(json.dumps(record), encoding="utf-8")
                if field == "record":
                    link = record_file
                elif field == "schema":
                    link = repo / "schemas" / "public" / "external-import-record-v1.schema.json"
                else:
                    link = repo / "outside-link"
                if field in ("record", "schema"):
                    link.unlink()
                try:
                    link.symlink_to(outside)
                except OSError as exc:
                    self.skipTest(f"Symlink creation unavailable: {exc}")
                if field == "destination_path":
                    record["integrity"]["inventory"][0][field] = "outside-link"
                elif field == "license_files":
                    record["rights"][field] = ["outside-link"]
                if field != "record":
                    record_file.write_text(json.dumps(record), encoding="utf-8")
                self._assert_no_outside_read(repo, outside)

    def test_parent_directory_symlink_escapes_are_rejected(self):
        for field in ("destination_path", "license_files"):
            with self.subTest(field=field), tempfile.TemporaryDirectory() as tmp_dir:
                repo, record_file, record = self._make_repository(tmp_dir)
                outside_dir = Path(tmp_dir) / "repo-sibling"
                outside_dir.mkdir()
                outside = outside_dir / "outside.txt"
                outside.write_text("Example attribution", encoding="utf-8")
                try:
                    (repo / "linked-directory").symlink_to(outside_dir, target_is_directory=True)
                except OSError as exc:
                    self.skipTest(f"Symlink creation unavailable: {exc}")
                if field == "destination_path":
                    record["integrity"]["inventory"][0][field] = "linked-directory/outside.txt"
                else:
                    record["rights"][field] = ["linked-directory/outside.txt"]
                record_file.write_text(json.dumps(record), encoding="utf-8")
                self._assert_no_outside_read(repo, outside)

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
