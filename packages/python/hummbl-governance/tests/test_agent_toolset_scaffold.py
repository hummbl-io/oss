"""Tests for the agent toolset scaffold helper."""

from pathlib import Path

import pytest
import scripts.agent_toolset_scaffold as scaffold


def _write_git_config(repo: Path, remote_url: str) -> None:
    git_dir = repo / ".git"
    git_dir.mkdir(parents=True)
    (git_dir / "config").write_text(
        f'[remote "origin"]\n\turl = {remote_url}\n',
        encoding="utf-8",
    )


@pytest.mark.parametrize(
    ("remote_url", "expected"),
    [
        ("https://github.com/hummbl-io/hummbl-governance.git", "hummbl-io/hummbl-governance"),
        ("ssh://git@github.com/hummbl-io/hummbl-governance.git", "hummbl-io/hummbl-governance"),
        ("git@github.com:hummbl-io/hummbl-governance.git", "hummbl-io/hummbl-governance"),
    ],
)
def test_repo_default_name_accepts_github_remote_forms(tmp_path: Path, remote_url: str, expected: str) -> None:
    _write_git_config(tmp_path, remote_url)

    assert scaffold.repo_default_name(tmp_path) == expected


@pytest.mark.parametrize(
    "remote_url",
    [
        "https://evil.example/github.com/hummbl-io/hummbl-governance.git",
        "https://github.com@evil.example/hummbl-io/hummbl-governance.git",
        "https://github.com.evil.example/hummbl-io/hummbl-governance.git",
        "https://evilgithub.com/hummbl-io/hummbl-governance.git",
        "ssh://git@evil.example/github.com/hummbl-io/hummbl-governance.git",
        "git@github.com.evil.example:hummbl-io/hummbl-governance.git",
    ],
)
def test_repo_default_name_rejects_github_substring_bypasses(tmp_path: Path, remote_url: str) -> None:
    _write_git_config(tmp_path, remote_url)

    assert scaffold.repo_default_name(tmp_path) == "<owner>/<repo>"


def test_find_repo_root_climbs_from_nested_directory(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    nested = repo / "docs" / "operations"
    nested.mkdir(parents=True)
    (repo / ".git").mkdir()

    assert scaffold.find_repo_root(nested) == repo


def test_status_uses_detected_repo_root_for_nested_input(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    nested = repo / "docs" / "operations"
    nested.mkdir(parents=True)
    (repo / ".git").mkdir()
    present_file = repo / "scripts" / "pr_census.py"
    present_file.parent.mkdir()
    present_file.write_text("# placeholder\n", encoding="utf-8")

    repo_root = scaffold.find_repo_root(nested)
    status = scaffold.status_for_repo(repo_root)

    assert repo_root == repo
    assert any(item["path"] == "scripts/pr_census.py" for item in status["present"])


def test_resolve_template_source_falls_back_to_script_repo_root(tmp_path: Path) -> None:
    source_repo = tmp_path / "source"
    target_repo = tmp_path / "target"
    script_root = source_repo / "scripts"
    template = source_repo / "docs" / "operations" / "AGENT_TOOLSET_STARTER.md"
    script_root.mkdir(parents=True)
    template.parent.mkdir(parents=True)
    target_repo.mkdir()
    (source_repo / ".git").mkdir()
    template.write_text("# starter\n", encoding="utf-8")

    assert scaffold.resolve_template_source(target_repo, script_root).samefile(template)


def test_resolve_template_source_checks_script_root_docs_casing(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    script_root = tmp_path / "external_scripts"
    template = script_root / "DOCS" / "operations" / "AGENT_TOOLSET_STARTER.md"
    repo.mkdir()
    script_root.mkdir()
    template.parent.mkdir(parents=True)
    template.write_text("# starter\n", encoding="utf-8")

    assert template in scaffold.template_candidates(repo, script_root)
    assert scaffold.resolve_template_source(repo, script_root).samefile(template)


def test_resolve_template_source_exits_when_template_missing(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    script_root = tmp_path / "scripts"
    repo.mkdir()
    script_root.mkdir()

    assert scaffold.template_candidates(repo, script_root)
    with pytest.raises(SystemExit, match="AGENT_TOOLSET_STARTER.md template not found"):
        scaffold.resolve_template_source(repo, script_root)
