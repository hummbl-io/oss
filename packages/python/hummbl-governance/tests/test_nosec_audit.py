"""Tests for the nosec audit scanner (scripts/nosec_audit.py).

Verifies:
1. Scanner finds nosec comments with rule codes and justifications
2. Scanner flags unjustified nosec comments
3. Scanner skips test files
4. Scanner produces correct registry JSON
5. Scanner handles files with no nosec comments
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "nosec_audit.py"


def _run_audit(package: str, *extra: str) -> tuple[int, str]:
    """Run the nosec audit script and return (exit_code, stdout)."""
    cmd = [sys.executable, str(SCRIPT), "--package", str(package), *extra]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode, result.stdout + result.stderr


def _make_package(tmp_path: Path) -> Path:
    """Create a minimal package structure with nosec comments."""
    pkg = tmp_path / "test_pkg"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    return pkg


class TestNosecAuditScan:
    def test_finds_justified_nosec(self, tmp_path):
        """Scanner finds nosec with rule code and justification."""
        pkg = _make_package(tmp_path)
        (pkg / "module.py").write_text(
            'TOKEN = "abc123"  # nosec B105 — error code, not a password\n',
            encoding="utf-8",
        )
        rc, output = _run_audit(str(pkg))
        assert rc == 0
        assert "Total suppressions: 1" in output
        assert "Justified:          1" in output
        assert "B105" in output
        assert "error code, not a password" in output

    def test_flags_unjustified_nosec(self, tmp_path):
        """Scanner flags nosec without justification."""
        pkg = _make_package(tmp_path)
        (pkg / "module.py").write_text(
            'x = random.random()  # nosec\n',
            encoding="utf-8",
        )
        rc, output = _run_audit(str(pkg), "--strict")
        assert rc == 1
        assert "Unjustified:        1" in output
        assert "MISSING" in output

    def test_unjustified_warns_without_strict(self, tmp_path):
        """Without --strict, unjustified nosec warns but exits 0."""
        pkg = _make_package(tmp_path)
        (pkg / "module.py").write_text(
            'x = random.random()  # nosec\n',
            encoding="utf-8",
        )
        rc, output = _run_audit(str(pkg))
        assert rc == 0
        assert "Unjustified:        1" in output

    def test_skips_test_files(self, tmp_path):
        """Scanner skips test_*.py files."""
        pkg = _make_package(tmp_path)
        (pkg / "module.py").write_text(
            'x = random.random()  # nosec B311 — statistical use\n',
            encoding="utf-8",
        )
        (pkg / "test_module.py").write_text(
            'y = random.random()  # nosec B311 — test file should be skipped\n',
            encoding="utf-8",
        )
        rc, output = _run_audit(str(pkg))
        assert rc == 0
        assert "Total suppressions: 1" in output
        assert "test_module" not in output

    def test_no_nosec_found(self, tmp_path):
        """Scanner handles files with no nosec comments."""
        pkg = _make_package(tmp_path)
        (pkg / "module.py").write_text(
            'x = 1\ny = 2\n',
            encoding="utf-8",
        )
        rc, output = _run_audit(str(pkg))
        assert rc == 0
        assert "Total suppressions: 0" in output
        assert "no nosec suppressions found" in output

    def test_multiple_nosec_in_one_file(self, tmp_path):
        """Scanner finds multiple nosec comments in the same file."""
        pkg = _make_package(tmp_path)
        (pkg / "module.py").write_text(
            'a = random.random()  # nosec B311 — statistical\n'
            'b = random.choice(x)  # nosec B311 — statistical\n'
            'c = "password"  # nosec B105 — not a password\n',
            encoding="utf-8",
        )
        rc, output = _run_audit(str(pkg))
        assert rc == 0
        assert "Total suppressions: 3" in output
        assert "Justified:          3" in output


class TestNosecAuditRegistry:
    def test_registry_json_output(self, tmp_path):
        """--registry writes a valid JSON registry file."""
        pkg = _make_package(tmp_path)
        (pkg / "module.py").write_text(
            'x = random.random()  # nosec B311 — statistical use\n',
            encoding="utf-8",
        )
        registry_path = tmp_path / "nosec-registry.json"
        rc, output = _run_audit(str(pkg), "--registry", str(registry_path))
        assert rc == 0
        assert registry_path.exists()
        data = json.loads(registry_path.read_text())
        assert data["total"] == 1
        assert data["justified"] == 1
        assert data["unjustified"] == 0
        assert len(data["suppressions"]) == 1
        s = data["suppressions"][0]
        assert s["rule"] == "B311"
        assert s["has_justification"] is True
        assert "statistical use" in s["justification"]

    def test_json_flag_outputs_json(self, tmp_path):
        """--json outputs JSON to stdout."""
        pkg = _make_package(tmp_path)
        (pkg / "module.py").write_text(
            'x = random.random()  # nosec B311 — statistical\n',
            encoding="utf-8",
        )
        rc, output = _run_audit(str(pkg), "--json")
        assert rc == 0
        data = json.loads(output)
        assert len(data) == 1
        assert data[0]["rule"] == "B311"


class TestNosecAuditJustificationFormats:
    def test_em_dash_justification(self, tmp_path):
        """Scanner parses em-dash separated justifications."""
        pkg = _make_package(tmp_path)
        (pkg / "module.py").write_text(
            'x = 1  # nosec B105 — em dash justification\n',
            encoding="utf-8",
        )
        rc, output = _run_audit(str(pkg))
        assert rc == 0
        assert "em dash justification" in output

    def test_colon_justification(self, tmp_path):
        """Scanner parses colon-separated justifications."""
        pkg = _make_package(tmp_path)
        (pkg / "module.py").write_text(
            'x = 1  # nosec B105: colon justification\n',
            encoding="utf-8",
        )
        rc, output = _run_audit(str(pkg))
        assert rc == 0
        assert "colon justification" in output

    def test_hyphen_justification(self, tmp_path):
        """Scanner parses hyphen-separated justifications."""
        pkg = _make_package(tmp_path)
        (pkg / "module.py").write_text(
            'x = 1  # nosec B105 - hyphen justification\n',
            encoding="utf-8",
        )
        rc, output = _run_audit(str(pkg))
        assert rc == 0
        assert "hyphen justification" in output
