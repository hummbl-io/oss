"""Test fixtures for hummbl-gitops tests."""

import json
import os
import subprocess
import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def tmp_git_repo(tmp_path: Path) -> Path:
    """Create a temporary git repo with a basic Python package structure."""
    repo = tmp_path / "test-repo"
    repo.mkdir()

    # Initialize git on main so tests do not depend on the runner's
    # default initial branch name.
    subprocess.run(["git", "init", "--initial-branch=main"], cwd=repo, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=repo, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, capture_output=True)

    # Create a basic Python file
    src_dir = repo / "src"
    src_dir.mkdir()
    (src_dir / "__init__.py").write_text("")
    (src_dir / "main.py").write_text("def main():\n    return 'hello'\n")

    # Create a test file
    test_dir = repo / "tests"
    test_dir.mkdir()
    (test_dir / "__init__.py").write_text("")
    (test_dir / "test_main.py").write_text(
        "from src.main import main\n\ndef test_main():\n    assert main() == 'hello'\n"
    )

    # Create a CI contract
    ci_dir = repo / "ci"
    ci_dir.mkdir()
    contract = {
        "schema_version": "hummbl.ci.contract.v1",
        "project_id": "test/test-repo",
        "docs_only": {"directories": ["docs"], "suffixes": [".md"]},
        "checks": [
            {
                "id": "test",
                "authority": "required",
                "commands": [["{python}", "-m", "pytest", "tests/", "-x", "-q"]],
                "timeout_seconds": 60,
            },
            {
                "id": "lint",
                "authority": "required",
                "commands": [["{python}", "-m", "ruff", "check", "."]],
                "timeout_seconds": 30,
            },
            {
                "id": "install-smoke",
                "authority": "required",
                "commands": [["{python}", "-c", "print('smoke')"]],
                "timeout_seconds": 30,
            },
        ],
    }
    (ci_dir / "contract.v1.json").write_text(json.dumps(contract, indent=2))

    # Create a docs file
    docs_dir = repo / "docs"
    docs_dir.mkdir()
    (docs_dir / "README.md").write_text("# Test Repo\n")

    # Initial commit
    subprocess.run(["git", "add", "."], cwd=repo, capture_output=True)
    subprocess.run(["git", "commit", "-m", "initial"], cwd=repo, capture_output=True)

    return repo


@pytest.fixture
def tmp_git_repo_with_docs_only(tmp_git_repo: Path) -> Path:
    """A git repo where the only changes are docs-only."""
    # Add a docs-only change
    (tmp_git_repo / "docs" / "NEW.md").write_text("# New doc\n")
    subprocess.run(["git", "add", "."], cwd=tmp_git_repo, capture_output=True)
    subprocess.run(["git", "commit", "-m", "docs only"], cwd=tmp_git_repo, capture_output=True)
    return tmp_git_repo


@pytest.fixture
def tmp_git_repo_with_python_changes(tmp_git_repo: Path) -> Path:
    """A git repo with Python source changes."""
    # Modify a Python file
    (tmp_git_repo / "src" / "main.py").write_text(
        "def main():\n    return 'hello world'\n\ndef new_func():\n    return 42\n"
    )
    subprocess.run(["git", "add", "."], cwd=tmp_git_repo, capture_output=True)
    subprocess.run(["git", "commit", "-m", "python changes"], cwd=tmp_git_repo, capture_output=True)
    return tmp_git_repo
