"""Unit tests for check_scripts_inventory validator."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from check_scripts_inventory import (
    discover_repo_scripts,
    validate_inventory,
)


class CheckScriptsInventoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def _write_script(self, rel_path: str, content: str = "#!/usr/bin/env python3\npass\n") -> Path:
        p = self.root / rel_path
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        return p

    def _write_inventory(self, scripts: list[dict], schema_version: str = "hummbl.repository-scripts.v1") -> Path:
        inv = self.root / "tools" / "scripts-inventory.json"
        inv.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "schema_version": schema_version,
            "updated_at": "2026-09-22",
            "scripts": scripts,
        }
        inv.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return inv

    def test_discover_scripts_filters_tests_and_cache(self) -> None:
        self._write_script("tools/scripts/run.py")
        self._write_script("tools/scripts/test_run.py")
        self._write_script("tools/scripts/__pycache__/run.cpython-311.pyc")
        self._write_script("tools/scripts/helper.mjs")
        self._write_script(".github/scripts/ci_check.sh")

        discovered = discover_repo_scripts(self.root)
        self.assertEqual(
            discovered,
            {"tools/scripts/run.py", "tools/scripts/helper.mjs", ".github/scripts/ci_check.sh"},
        )

    def test_valid_inventory_passes(self) -> None:
        self._write_script("tools/scripts/run.py")
        inv = self._write_inventory([
            {
                "path": "tools/scripts/run.py",
                "classification": "maintain",
                "owner": "architecture",
                "invocation_contract": "python tools/scripts/run.py",
                "system_boundary": "read-only; zero egress",
                "failure_behavior": "exit 0 on success; exit 1 on error",
                "test_path": "tools/scripts/test_run.py",
            }
        ])

        errors, warnings = validate_inventory(self.root, inv)
        self.assertEqual(errors, [])

    def test_uncataloged_script_fails(self) -> None:
        self._write_script("tools/scripts/run.py")
        self._write_script("tools/scripts/rogue.py")
        inv = self._write_inventory([
            {
                "path": "tools/scripts/run.py",
                "classification": "maintain",
                "owner": "architecture",
                "invocation_contract": "python tools/scripts/run.py",
                "system_boundary": "read-only",
                "failure_behavior": "exit 0",
                "test_path": "tools/scripts/test_run.py",
            }
        ])

        errors, warnings = validate_inventory(self.root, inv)
        self.assertTrue(any("Unregistered executable script" in e and "rogue.py" in e for e in errors))

    def test_missing_script_on_disk_fails(self) -> None:
        inv = self._write_inventory([
            {
                "path": "tools/scripts/ghost.py",
                "classification": "maintain",
                "owner": "architecture",
                "invocation_contract": "python tools/scripts/ghost.py",
                "system_boundary": "read-only",
                "failure_behavior": "exit 0",
                "test_path": "tools/scripts/test_ghost.py",
            }
        ])

        errors, warnings = validate_inventory(self.root, inv)
        self.assertTrue(any("does not exist on disk" in e and "ghost.py" in e for e in errors))

    def test_invalid_classification_fails(self) -> None:
        self._write_script("tools/scripts/run.py")
        inv = self._write_inventory([
            {
                "path": "tools/scripts/run.py",
                "classification": "experimental",
                "owner": "architecture",
                "invocation_contract": "python tools/scripts/run.py",
                "system_boundary": "read-only",
                "failure_behavior": "exit 0",
                "test_path": "tools/scripts/test_run.py",
            }
        ])

        errors, warnings = validate_inventory(self.root, inv)
        self.assertTrue(any("invalid classification 'experimental'" in e for e in errors))

    def test_missing_required_field_fails(self) -> None:
        self._write_script("tools/scripts/run.py")
        inv = self._write_inventory([
            {
                "path": "tools/scripts/run.py",
                "classification": "maintain",
                "owner": "architecture",
                "invocation_contract": "python tools/scripts/run.py",
                "system_boundary": "",
                "failure_behavior": "exit 0",
                "test_path": "tools/scripts/test_run.py",
            }
        ])

        errors, warnings = validate_inventory(self.root, inv)
        self.assertTrue(any("missing or empty required field 'system_boundary'" in e for e in errors))

    def test_secret_in_inventory_metadata_fails(self) -> None:
        self._write_script("tools/scripts/run.py")
        inv = self._write_inventory([
            {
                "path": "tools/scripts/run.py",
                "classification": "maintain",
                "owner": "architecture",
                "invocation_contract": "python tools/scripts/run.py --token 192.168.1.100",
                "system_boundary": "read-only",
                "failure_behavior": "exit 0",
                "test_path": "tools/scripts/test_run.py",
            }
        ])

        errors, warnings = validate_inventory(self.root, inv)
        self.assertTrue(any("potential secret or unredacted boundary pattern" in e for e in errors))


if __name__ == "__main__":
    unittest.main()
