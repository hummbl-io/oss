#!/usr/bin/env python3
"""Tests for package_parity.py -- run with:

    python -m unittest discover -s .github/scripts -p 'test_package_parity.py' -v
"""

from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import package_parity as pp

DOC_TEMPLATE = """# Packages
## 1. PyPI (Python)
### Live
| Package | Tree | Notes |
|---------|------|-------|
{live}### In-tree
| Package | Tree | Notes |
|---------|------|-------|
{intree}### Excluded (not ours)
| Package | Owner |
|---------|-------|
{excluded}---
## 2. npm
| Package | Tree |
|---------|------|
| `@hummbl/mcp-base120` | 0.1.0-canary.0 |
"""

PYPROJECT = """[project]
name = "{name}"
version = "0.1.0"
requires-python = ">=3.11"
{deps}
"""


def deps_block(deps: list[str]) -> str:
    if not deps:
        return ""
    inner = "\n".join(f'    "{d}",' for d in deps)
    return f"dependencies = [\n{inner}\n]"


class ParityFixture(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / "packages" / "python").mkdir(parents=True)
        (self.root / "docs" / "architecture").mkdir(parents=True)
        self._write_doc(live=["alpha"], intree=["beta"], excluded=["crab"])

    def _write_doc(self, live=(), intree=(), excluded=()) -> None:
        def rows(names):
            return "".join(f"| `{n}` | 0.1.0 | x |\n" for n in names)

        doc = DOC_TEMPLATE.format(
            live=rows(live), intree=rows(intree), excluded=rows(excluded)
        )
        (self.root / pp.PACKAGES_DOC_REL).write_text(doc, encoding="utf-8")

    def _pkg(self, name: str, deps: list[str] | None = None, rp: str = ">=3.11") -> Path:
        d = self.root / "packages" / "python" / name
        d.mkdir(parents=True)
        (d / "pyproject.toml").write_text(
            PYPROJECT.format(name=name, deps=deps_block(deps or [])), encoding="utf-8"
        )
        return d

    def _stamp_lock(self, pkg_dir: Path, pins: list[str], rp: str, deps: list[str]) -> None:
        body = "".join(f"{p}\n" for p in pins)
        body += f"{pp.INPUTS_HASH_PREFIX}{pp.inputs_digest(rp, deps)}\n"
        (pkg_dir / pp.LOCK_NAME).write_text(body, encoding="utf-8")

    def _check(self, *names: str) -> int:
        return pp.main(["check", *names, "--root", str(self.root)])


class TestCheck(ParityFixture):
    def test_clean_tree_passes(self) -> None:
        self._pkg("alpha", deps=["dep-one>=1.0"])
        self._stamp_lock(
            self.root / "packages" / "python" / "alpha",
            ["dep-one==1.2.3"],
            ">=3.11",
            ["dep-one>=1.0"],
        )
        self._pkg("beta")  # stdlib-only, no lock needed
        self.assertEqual(self._check(), 0)

    def test_package_missing_from_doc_fails(self) -> None:
        self._pkg("ghost")
        self.assertEqual(self._check(), 1)

    def test_deps_without_lock_fails(self) -> None:
        self._pkg("beta", deps=["dep-one>=1.0"])
        self.assertEqual(self._check("beta"), 1)

    def test_stale_lock_fails(self) -> None:
        pkg = self._pkg("alpha", deps=["dep-one>=2.0"])
        self._stamp_lock(pkg, ["dep-one==1.2.3"], ">=3.11", ["dep-one>=1.0"])
        self.assertEqual(self._check("alpha"), 1)

    def test_lock_missing_declared_pin_fails(self) -> None:
        pkg = self._pkg("alpha", deps=["dep-one>=1.0"])
        self._stamp_lock(pkg, ["unrelated==9.9"], ">=3.11", ["dep-one>=1.0"])
        self.assertEqual(self._check("alpha"), 1)

    def test_unstamped_lock_fails(self) -> None:
        pkg = self._pkg("alpha", deps=["dep-one>=1.0"])
        (pkg / pp.LOCK_NAME).write_text("dep-one==1.2.3\n", encoding="utf-8")
        self.assertEqual(self._check("alpha"), 1)

    def test_excluded_table_does_not_count_as_documented(self) -> None:
        self._pkg("crab")  # only present in the Excluded table
        self.assertEqual(self._check("crab"), 1)

    def test_lock_without_deps_is_still_verified(self) -> None:
        pkg = self._pkg("beta")  # no deps, but a lock exists
        (pkg / pp.LOCK_NAME).write_text("# comment only\n", encoding="utf-8")
        self.assertEqual(self._check("beta"), 1)
        self._stamp_lock(pkg, [], ">=3.11", [])
        self.assertEqual(self._check("beta"), 0)

    def test_requires_python_change_stales_lock(self) -> None:
        pkg = self._pkg("alpha", deps=["dep-one>=1.0"])
        self._stamp_lock(pkg, ["dep-one==1.2.3"], ">=3.11", ["dep-one>=1.0"])
        (pkg / "pyproject.toml").write_text(
            PYPROJECT.format(name="alpha", deps=deps_block(["dep-one>=1.0"])).replace(
                '>=3.11', '>=3.12'
            ),
            encoding="utf-8",
        )
        self.assertEqual(self._check("alpha"), 1)


class TestLockMode(ParityFixture):
    @unittest.skipUnless(shutil.which("uv"), "uv not on PATH")
    def test_lock_generates_stamped_lock(self) -> None:
        pkg = self._pkg("beta", deps=["packaging>=23.0"])
        self.assertEqual(pp.main(["lock", "beta", "--root", str(self.root)]), 0)
        lock = (pkg / pp.LOCK_NAME).read_text(encoding="utf-8")
        self.assertIn("packaging==", lock)
        self.assertIn(pp.INPUTS_HASH_PREFIX, lock)
        self.assertEqual(self._check("beta"), 0)


if __name__ == "__main__":
    unittest.main()
