"""Tests for scripts.validation.check_untracked_tests."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.validation.check_untracked_tests import (  # noqa: E402
    _is_test_file,
    check_repo,
    main,
)


def _git_init(repo: Path) -> None:
    """Initialize a git repo and make an initial commit so ls-files works."""
    subprocess.run(["git", "init", "-q"], cwd=str(repo), check=True)
    subprocess.run(["git", "config", "user.email", "t@t.com"], cwd=str(repo), check=True)
    subprocess.run(["git", "config", "user.name", "test"], cwd=str(repo), check=True)
    # Commit a placeholder so HEAD exists
    (repo / ".gitkeep").write_text("", encoding="utf-8")
    subprocess.run(["git", "add", "-A"], cwd=str(repo), check=True)
    subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=str(repo), check=True)


# ---------------------------------------------------------------------------
# _is_test_file
# ---------------------------------------------------------------------------

def test_is_test_file_test_prefix():
    assert _is_test_file(Path("test_foo.py")) is True

def test_is_test_file_test_suffix():
    assert _is_test_file(Path("foo_test.py")) is True

def test_is_test_file_not_a_test():
    assert _is_test_file(Path("foo.py")) is False

def test_is_test_file_conftest():
    assert _is_test_file(Path("conftest.py")) is False

def test_is_test_file_non_py():
    assert _is_test_file(Path("test_foo.txt")) is False


# ---------------------------------------------------------------------------
# check_repo
# ---------------------------------------------------------------------------

def test_check_repo_no_untracked(tmp_path: Path):
    _git_init(tmp_path)
    tests = tmp_path / "tests"
    tests.mkdir()
    (tests / "test_a.py").write_text("def test_a(): pass\n", encoding="utf-8")
    subprocess.run(["git", "add", "-A"], cwd=str(tmp_path), check=True)
    subprocess.run(["git", "commit", "-q", "-m", "add tests"], cwd=str(tmp_path), check=True)
    assert check_repo(tmp_path) == []


def test_check_repo_finds_untracked(tmp_path: Path):
    _git_init(tmp_path)
    tests = tmp_path / "tests"
    tests.mkdir()
    # Tracked file
    (tests / "test_tracked.py").write_text("def test_t(): pass\n", encoding="utf-8")
    subprocess.run(["git", "add", "-A"], cwd=str(tmp_path), check=True)
    subprocess.run(["git", "commit", "-q", "-m", "add tracked test"], cwd=str(tmp_path), check=True)
    # Untracked file
    (tests / "test_untracked.py").write_text("def test_u(): pass\n", encoding="utf-8")

    result = check_repo(tmp_path)
    assert len(result) == 1
    assert result[0].name == "test_untracked.py"


def test_check_repo_ignores_non_test_files(tmp_path: Path):
    _git_init(tmp_path)
    tests = tmp_path / "tests"
    tests.mkdir()
    (tests / "helper.py").write_text("# helper\n", encoding="utf-8")
    result = check_repo(tmp_path)
    assert result == []


def test_check_repo_ignores_files_outside_tests(tmp_path: Path):
    _git_init(tmp_path)
    (tmp_path / "test_stray.py").write_text("def test_s(): pass\n", encoding="utf-8")
    result = check_repo(tmp_path)
    assert result == []


def test_check_repo_not_a_git_repo(tmp_path: Path):
    assert check_repo(tmp_path) == []


# ---------------------------------------------------------------------------
# main (CLI)
# ---------------------------------------------------------------------------

def test_main_clean_returns_0(tmp_path: Path):
    _git_init(tmp_path)
    rc = main(["prog", str(tmp_path)])
    assert rc == 0


def test_main_untracked_returns_1(tmp_path: Path, capsys):
    _git_init(tmp_path)
    tests = tmp_path / "tests"
    tests.mkdir()
    (tests / "test_untracked.py").write_text("def test_u(): pass\n", encoding="utf-8")
    rc = main(["prog", str(tmp_path)])
    assert rc == 1
    captured = capsys.readouterr()
    assert "test_untracked.py" in captured.err


def test_main_nonexistent_path_returns_2(tmp_path: Path):
    rc = main(["prog", str(tmp_path / "nope")])
    assert rc == 2
