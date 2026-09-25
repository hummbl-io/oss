"""Test fixtures for hummbl-gitops tests."""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

_GIT_ENV_VARS = (
    "GIT_ALTERNATE_OBJECT_DIRECTORIES",
    "GIT_CONFIG",
    "GIT_CONFIG_PARAMETERS",
    "GIT_CONFIG_COUNT",
    "GIT_OBJECT_DIRECTORY",
    "GIT_DIR",
    "GIT_WORK_TREE",
    "GIT_IMPLICIT_WORK_TREE",
    "GIT_GRAFT_FILE",
    "GIT_INDEX_FILE",
    "GIT_NO_REPLACE_OBJECTS",
    "GIT_REPLACE_REF_BASE",
    "GIT_PREFIX",
    "GIT_SHALLOW_FILE",
    "GIT_COMMON_DIR",
    "GIT_QUARANTINE_PATH",
)


def _remove_git_env(environ):
    """Remove repository-local Git variables and return their prior values."""
    return {var: environ.pop(var) for var in _GIT_ENV_VARS if var in environ}


def _restore_git_env(environ, saved):
    """Restore the exact pre-session state for repository-local Git variables."""
    for var in _GIT_ENV_VARS:
        environ.pop(var, None)
    environ.update(saved)


@pytest.fixture(autouse=True, scope="session")
def _strip_git_env():
    """Keep subprocess Git commands isolated from the invoking worktree and hooks."""
    import shutil

    saved = _remove_git_env(os.environ)
    os.environ["GIT_CONFIG_PARAMETERS"] = "'core.hooksPath='"
    prior_pythonpath = os.environ.get("PYTHONPATH")
    os.environ["PYTHONPATH"] = str(ROOT)

    orig_popen = subprocess.Popen

    def _wrapped_popen(args, *pargs, **kwargs):
        if sys.platform == "win32" and isinstance(args, (list, tuple)) and args:
            target = Path(args[0])
            try:
                if target.is_file() and target.suffix.lower() not in (".exe", ".cmd", ".bat"):
                    with open(target, "rb") as f:
                        if f.read(2) == b"#!":
                            git_bash = r"C:\Program Files\Git\bin\bash.exe"
                            bash = git_bash if os.path.exists(git_bash) else (shutil.which("bash") or "bash")
                            args = [bash, str(target).replace("\\", "/"), *args[1:]]
            except (OSError, UnicodeDecodeError):
                pass
        if sys.platform == "win32" and "env" in kwargs and kwargs["env"] is not None:
            env = kwargs["env"]
            if env.get("PATH") == "/usr/bin:/bin":
                git_bin = r"C:\Program Files\Git\usr\bin;C:\Program Files\Git\bin"
                env["PATH"] = git_bin
        return orig_popen(args, *pargs, **kwargs)

    subprocess.Popen = _wrapped_popen

    try:
        yield
    finally:
        subprocess.Popen = orig_popen
        _restore_git_env(os.environ, saved)
        if prior_pythonpath is None:
            os.environ.pop("PYTHONPATH", None)
        else:
            os.environ["PYTHONPATH"] = prior_pythonpath


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
