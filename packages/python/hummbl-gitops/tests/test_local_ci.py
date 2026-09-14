"""Tests for L2a: local CI contract runner."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from hummbl_gitops.forward.local_ci import (
    CheckResult,
    LocalCIResult,
    _is_docs_only,
    get_diff_files,
    load_contract,
    run_local_ci,
    scope_checks,
)


class TestLoadContract:
    def test_loads_contract_from_repo(self, tmp_git_repo: Path) -> None:
        contract = load_contract(tmp_git_repo)
        assert contract is not None
        assert contract["schema_version"] == "hummbl.ci.contract.v1"
        assert len(contract["checks"]) == 3

    def test_returns_none_when_no_contract(self, tmp_path: Path) -> None:
        contract = load_contract(tmp_path)
        assert contract is None


class TestScopeChecks:
    def test_docs_only_skips_all(self, tmp_git_repo: Path) -> None:
        contract = load_contract(tmp_git_repo)
        scoped = scope_checks(contract, ["docs/README.md"])
        assert scoped == []

    def test_python_changes_run_test_and_lint(self, tmp_git_repo: Path) -> None:
        contract = load_contract(tmp_git_repo)
        scoped = scope_checks(contract, ["src/main.py"])
        check_ids = [c["id"] for c in scoped]
        assert "test" in check_ids
        assert "lint" in check_ids

    def test_install_smoke_skipped_by_default(self, tmp_git_repo: Path) -> None:
        contract = load_contract(tmp_git_repo)
        scoped = scope_checks(contract, ["src/main.py"])
        check_ids = [c["id"] for c in scoped]
        assert "install-smoke" not in check_ids

    def test_empty_diff_skips_all(self, tmp_git_repo: Path) -> None:
        contract = load_contract(tmp_git_repo)
        scoped = scope_checks(contract, [])
        assert scoped == []  # empty diff = no checks to run


class TestGetDiffFiles:
    def test_head_scopes_to_merge_base_not_origin_main_tip(
        self, tmp_git_repo: Path
    ) -> None:
        repo = tmp_git_repo
        subprocess.run(["git", "add", "-A"], cwd=repo, capture_output=True)
        subprocess.run(["git", "commit", "-m", "init"], cwd=repo, capture_output=True)

        # Branch off and add a docs-only change.
        subprocess.run(
            ["git", "checkout", "-b", "feature"], cwd=repo, capture_output=True
        )
        (repo / "docs").mkdir(exist_ok=True)
        (repo / "docs" / "README.md").write_text("# hi\n")
        subprocess.run(["git", "add", "-A"], cwd=repo, capture_output=True)
        subprocess.run(["git", "commit", "-m", "docs"], cwd=repo, capture_output=True)
        head = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=repo, capture_output=True, text=True
        ).stdout.strip()

        # Advance main (simulated origin/main) with an unrelated python change.
        subprocess.run(["git", "checkout", "main"], cwd=repo, capture_output=True)
        (repo / "src" / "extra.py").write_text("x = 1\n")
        subprocess.run(["git", "add", "-A"], cwd=repo, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "unrelated python"], cwd=repo, capture_output=True
        )
        main_tip = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=repo, capture_output=True, text=True
        ).stdout.strip()
        subprocess.run(
            ["git", "update-ref", "refs/remotes/origin/main", main_tip], cwd=repo
        )

        # Diff scoped to the pushed branch head must show only the branch's own
        # doc file, not the unrelated python file that landed on main later.
        files = get_diff_files(repo, head=head)
        assert files == ["docs/README.md"], files


class TestRunLocalCI:
    def test_docs_only_returns_pass_with_no_checks(self, tmp_git_repo_with_docs_only: Path) -> None:
        result = run_local_ci(tmp_git_repo_with_docs_only)
        assert result.all_passed
        assert len(result.checks_run) == 0

    def test_python_changes_run_scoped_checks(self, tmp_git_repo_with_python_changes: Path) -> None:
        # Test scoping directly since get_diff_files needs origin/main
        contract = load_contract(tmp_git_repo_with_python_changes)
        scoped = scope_checks(contract, ["src/main.py"])
        check_ids = [c["id"] for c in scoped]
        # test and lint should run; install-smoke should be skipped
        assert "test" in check_ids
        assert "lint" in check_ids
        assert "install-smoke" not in check_ids

    def test_full_contract_runs_all(self, tmp_git_repo_with_python_changes: Path) -> None:
        result = run_local_ci(tmp_git_repo_with_python_changes, full_contract=True)
        check_ids = [c.check_id for c in result.checks_run]
        assert "install-smoke" in check_ids

    def test_no_contract_falls_back_to_basic(self, tmp_path: Path) -> None:
        # Create a minimal repo without ci/contract.v1.json
        import subprocess
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True)
        subprocess.run(["git", "config", "user.email", "t@t.com"], cwd=tmp_path, capture_output=True)
        subprocess.run(["git", "config", "user.name", "T"], cwd=tmp_path, capture_output=True)
        (tmp_path / "README.md").write_text("# init\n")
        subprocess.run(["git", "add", "."], cwd=tmp_path, capture_output=True)
        subprocess.run(["git", "commit", "-m", "init"], cwd=tmp_path, capture_output=True)
        # Create uncommitted Python change so get_diff_files sees it
        (tmp_path / "test.py").write_text("x = 1\n")
        subprocess.run(["git", "add", "test.py"], cwd=tmp_path, capture_output=True)

        result = run_local_ci(tmp_path)
        # Should have attempted test and lint (may fail if no pytest/ruff installed)
        assert len(result.checks_run) >= 1

    def test_no_contract_docs_only_skips_tests(self, tmp_path: Path) -> None:
        """Docs-only push on a repo without ci/contract.v1.json should skip pytest."""
        import subprocess
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True)
        subprocess.run(["git", "config", "user.email", "t@t.com"], cwd=tmp_path, capture_output=True)
        subprocess.run(["git", "config", "user.name", "T"], cwd=tmp_path, capture_output=True)
        (tmp_path / "README.md").write_text("# init\n")
        subprocess.run(["git", "add", "."], cwd=tmp_path, capture_output=True)
        subprocess.run(["git", "commit", "-m", "init"], cwd=tmp_path, capture_output=True)
        # Create uncommitted docs-only change so get_diff_files sees it
        (tmp_path / "docs").mkdir()
        (tmp_path / "docs" / "guide.md").write_text("# Guide\n")
        subprocess.run(["git", "add", "docs/"], cwd=tmp_path, capture_output=True)

        result = run_local_ci(tmp_path)
        assert result.all_passed
        assert len(result.checks_run) == 0
        assert "test" in result.skipped
        assert "lint" in result.skipped


class TestCheckResult:
    def test_required_passed_property(self) -> None:
        result = LocalCIResult(repo="test")
        result.checks_run.append(CheckResult("test", "required", passed=True))
        result.checks_run.append(CheckResult("lint", "required", passed=False))
        assert not result.required_passed

    def test_advisory_failure_does_not_block(self) -> None:
        result = LocalCIResult(repo="test")
        result.checks_run.append(CheckResult("test", "required", passed=True))
        result.checks_run.append(CheckResult("coverage", "advisory", passed=False))
        assert result.required_passed


class TestIsDocsOnly:
    def test_pure_markdown_is_docs(self) -> None:
        assert _is_docs_only(["README.md", "docs/guide.md"])

    def test_python_is_not_docs(self) -> None:
        assert not _is_docs_only(["README.md", "src/main.py"])

    def test_github_workflows_is_docs(self) -> None:
        assert _is_docs_only([".github/workflows/ci.yml", ".github/ISSUE_TEMPLATE/bug.md"])

    def test_license_and_changelog_are_docs(self) -> None:
        assert _is_docs_only(["LICENSE", "CHANGELOG"])

    def test_images_are_docs(self) -> None:
        assert _is_docs_only(["docs/diagram.png", "logo.svg"])

    def test_empty_list_is_docs(self) -> None:
        assert _is_docs_only([])

    def test_mixed_py_and_md_is_not_docs(self) -> None:
        assert not _is_docs_only(["docs/api.md", "packages/python/hummbl/__init__.py"])

    def test_internal_dir_is_docs(self) -> None:
        assert _is_docs_only(["_internal/draft.md", "_internal/notes.txt"])
