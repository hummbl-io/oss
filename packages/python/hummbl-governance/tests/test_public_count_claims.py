"""README tree versions must be backed by complete, valid package metadata."""

from pathlib import Path

import pytest

from scripts import check_public_count_claims as claims


HEADER = "| Package | Tree | PyPI | Status |\n|---|---|---|---|\n"
ROW = "| `example` | 1.2.3 | Live 9.9.9 | Example package |\n"


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    package = tmp_path / "packages/python/example"
    package.mkdir(parents=True)
    (package / "pyproject.toml").write_text(
        '[tool.example]\nversion = "unrelated"\n[project]\n'
        'name = "example"\nversion = "1.2.3"\n',
        encoding="utf-8",
    )
    (tmp_path / "README.md").write_text(HEADER + ROW, encoding="utf-8")
    return tmp_path


def test_project_version_used_and_registry_version_ignored(repo):
    assert claims.check_package_table_versions(repo) == []


@pytest.mark.parametrize(
    ("table", "message"),
    [
        ("No package table", "expected exactly one"),
        (HEADER + ROW + HEADER + ROW, "expected exactly one"),
        (HEADER.replace("|---|---|---|---|", "|invalid|") + ROW, "separator"),
        (HEADER, "missing package row: example"),
        (HEADER + ROW + ROW, "duplicate package row"),
        (HEADER + ROW.replace("1.2.3", "1.2.4"), "table says"),
        (HEADER + ROW.replace("1.2.3", ""), "table says"),
        (HEADER + ROW.replace("1.2.3", "latest"), "table says"),
        (HEADER + ROW.replace("`example`", "`removed`"), "unknown Python package"),
        (HEADER + "| `example` | 1.2.3 |\n", "malformed package row"),
    ],
)
def test_missing_or_malformed_rows_fail_closed(repo, table, message):
    (repo / "README.md").write_text(table, encoding="utf-8")
    assert any(message in problem for problem in claims.check_package_table_versions(repo))


@pytest.mark.parametrize(
    "manifest",
    [
        "[project",
        '[tool.example]\nversion = "1.2.3"\n',
        '[project]\nversion = 123\n',
        '[project]\ndynamic = ["version"]\n',
        '[project]\nversion = ""\n',
    ],
)
def test_bad_manifest_does_not_pass_silently(repo, manifest):
    (repo / "packages/python/example/pyproject.toml").write_text(manifest, encoding="utf-8")
    assert claims.check_package_table_versions(repo)


def test_missing_readme_fails_closed(repo):
    (repo / "README.md").unlink()
    assert claims.check_package_table_versions(repo)


def test_empty_package_inventory_fails_closed(tmp_path):
    assert claims.check_package_table_versions(tmp_path)
    (tmp_path / "packages/python").mkdir(parents=True)
    assert claims.check_package_table_versions(tmp_path)


def test_node_table_is_not_treated_as_python_package_rows(repo):
    with (repo / "README.md").open("a", encoding="utf-8") as stream:
        stream.write("Node packages:\n| Package | Tree | npm | Status |\n|---|---|---|---|\n")
        stream.write("| `@example/node` | 0.1.0 | Private | Canary |\n")
    assert claims.check_package_table_versions(repo) == []


def test_new_package_requires_its_own_row(repo):
    package = repo / "packages/python/new"
    package.mkdir()
    (package / "pyproject.toml").write_text('[project]\nversion = "0.1.0"\n', encoding="utf-8")
    assert any("missing package row: new" in p for p in claims.check_package_table_versions(repo))


def test_cli_returns_failure_for_table_version_drift(repo, monkeypatch, capsys):
    (repo / "README.md").write_text(HEADER + ROW.replace("1.2.3", "0.0.0"), encoding="utf-8")
    monkeypatch.setattr(claims, "build_checks", lambda root: [])
    monkeypatch.setattr("sys.argv", ["check_public_count_claims.py", "--repo-root", str(repo)])
    assert claims.main() == 1
    assert "table says '0.0.0'" in capsys.readouterr().out
