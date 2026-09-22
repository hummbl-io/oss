#!/usr/bin/env python3
import tempfile
import unittest
from pathlib import Path

from tools.scripts.check_monorepo_parity import (
    check_agents_md_parity,
    check_ci_matrix_parity,
    check_docs_packages_parity,
    check_lockfile_presence,
    get_actual_packages,
    run_all_checks,
)


class MonorepoParityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.pkg_dir = self.root / "packages" / "python"
        self.pkg_dir.mkdir(parents=True)
        self.docs_dir = self.root / "docs"
        self.docs_dir.mkdir(parents=True)
        self.ci_dir = self.root / ".github" / "workflows"
        self.ci_dir.mkdir(parents=True)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_detects_missing_from_docs(self) -> None:
        (self.pkg_dir / "pkg_a").mkdir()
        (self.docs_dir / "PACKAGES.md").write_text("# Packages\n", encoding="utf-8")
        errors = check_docs_packages_parity(self.root, {"pkg_a"})
        self.assertTrue(any("Package 'pkg_a' is absent" in e for e in errors))

    def test_passes_when_present_in_docs(self) -> None:
        (self.pkg_dir / "pkg_a").mkdir()
        (self.docs_dir / "PACKAGES.md").write_text("# Packages\n| `pkg_a` | 0.1.0 |\n", encoding="utf-8")
        errors = check_docs_packages_parity(self.root, {"pkg_a"})
        self.assertEqual([], errors)

    def test_detects_missing_lockfile_when_dependencies_declared(self) -> None:
        pkg = self.pkg_dir / "pkg_with_deps"
        pkg.mkdir()
        (pkg / "pyproject.toml").write_text(
            '[project]\nname = "pkg_with_deps"\ndependencies = ["requests>=2.0"]\n',
            encoding="utf-8",
        )
        errors = check_lockfile_presence(self.root, {"pkg_with_deps"})
        self.assertTrue(any("lacks requirements.lock" in e for e in errors))

    def test_passes_when_lockfile_exists(self) -> None:
        pkg = self.pkg_dir / "pkg_with_deps"
        pkg.mkdir()
        (pkg / "pyproject.toml").write_text(
            '[project]\nname = "pkg_with_deps"\ndependencies = ["requests>=2.0"]\n',
            encoding="utf-8",
        )
        (pkg / "requirements.lock").write_text("requests==2.31.0\n", encoding="utf-8")
        errors = check_lockfile_presence(self.root, {"pkg_with_deps"})
        self.assertEqual([], errors)

    def test_detects_missing_ci_matrix_package(self) -> None:
        (self.pkg_dir / "pkg_a").mkdir()
        (self.ci_dir / "ci.yml").write_text(
            'jobs:\n  test:\n    strategy:\n      matrix:\n        package: [other_pkg]\n',
            encoding="utf-8",
        )
        errors = check_ci_matrix_parity(self.root, {"pkg_a"})
        self.assertTrue(any("missing from .github/workflows/ci.yml" in e for e in errors))


if __name__ == "__main__":
    unittest.main()
