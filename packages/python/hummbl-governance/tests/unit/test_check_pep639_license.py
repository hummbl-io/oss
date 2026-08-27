"""Tests for scripts.validation.check_pep639_license."""

from __future__ import annotations

import sys
import textwrap
from pathlib import Path

# Make scripts importable when running from repo root.
REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.validation.check_pep639_license import (  # noqa: E402
    check_file,
    iter_pyproject,
    main,
)


def _write_pyproject(path: Path, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(body), encoding="utf-8")


# ---------------------------------------------------------------------------
# check_file
# ---------------------------------------------------------------------------


def test_clean_spdx_only(tmp_path: Path):
    f = tmp_path / "pyproject.toml"
    _write_pyproject(
        f,
        """
        [project]
        name = "x"
        version = "0.1.0"
        license = "Apache-2.0"
        classifiers = ["Development Status :: 3 - Alpha"]
    """,
    )
    assert check_file(f) == []


def test_clean_classifier_only(tmp_path: Path):
    """Legacy form: no SPDX expression, only classifier — still accepted."""
    f = tmp_path / "pyproject.toml"
    _write_pyproject(
        f,
        """
        [project]
        name = "x"
        version = "0.1.0"
        license = {text = "MIT"}
        classifiers = ["License :: OSI Approved :: MIT License"]
    """,
    )
    assert check_file(f) == []


def test_conflict_spdx_and_classifier(tmp_path: Path):
    f = tmp_path / "pyproject.toml"
    _write_pyproject(
        f,
        """
        [project]
        name = "x"
        version = "0.1.0"
        license = "Apache-2.0"
        classifiers = [
            "Development Status :: 3 - Alpha",
            "License :: OSI Approved :: Apache Software License",
        ]
    """,
    )
    errors = check_file(f)
    assert len(errors) == 1
    assert "PEP 639 conflict" in errors[0]
    assert "Apache Software License" in errors[0]


def test_no_license_field(tmp_path: Path):
    f = tmp_path / "pyproject.toml"
    _write_pyproject(
        f,
        """
        [project]
        name = "x"
        version = "0.1.0"
    """,
    )
    assert check_file(f) == []


def test_missing_file(tmp_path: Path):
    errors = check_file(tmp_path / "nope.toml")
    assert len(errors) == 1
    assert "not found" in errors[0]


# ---------------------------------------------------------------------------
# iter_pyproject
# ---------------------------------------------------------------------------


def test_iter_pyproject_finds_nested(tmp_path: Path):
    a = tmp_path / "a" / "pyproject.toml"
    b = tmp_path / "b" / "c" / "pyproject.toml"
    _write_pyproject(a, '[project]\nname = "a"\nversion = "0"\n')
    _write_pyproject(b, '[project]\nname = "b"\nversion = "0"\n')
    found = iter_pyproject([tmp_path])
    assert a in found
    assert b in found


def test_iter_pyproject_explicit_file(tmp_path: Path):
    f = tmp_path / "pyproject.toml"
    _write_pyproject(f, '[project]\nname = "x"\nversion = "0"\n')
    assert iter_pyproject([f]) == [f]


# ---------------------------------------------------------------------------
# main (CLI)
# ---------------------------------------------------------------------------


def test_main_clean_returns_0(tmp_path: Path, capsys):
    f = tmp_path / "pyproject.toml"
    _write_pyproject(
        f,
        """
        [project]
        name = "x"
        version = "0.1.0"
        license = "Apache-2.0"
    """,
    )
    rc = main(["prog", str(tmp_path)])
    assert rc == 0


def test_main_conflict_returns_1(tmp_path: Path, capsys):
    f = tmp_path / "pyproject.toml"
    _write_pyproject(
        f,
        """
        [project]
        name = "x"
        version = "0.1.0"
        license = "Apache-2.0"
        classifiers = ["License :: OSI Approved :: Apache Software License"]
    """,
    )
    rc = main(["prog", str(tmp_path)])
    assert rc == 1
    captured = capsys.readouterr()
    assert "PEP 639 conflict" in captured.err


def test_main_no_files_returns_0(tmp_path: Path):
    rc = main(["prog", str(tmp_path)])
    assert rc == 0
