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


@pytest.mark.parametrize("leading,trailing", [(False, True), (True, False), (False, False)])
def test_optional_outer_table_delimiters_are_supported(repo, leading, trailing):
    lines = (HEADER + ROW).splitlines()
    if not leading:
        lines = [line.removeprefix("|") for line in lines]
    if not trailing:
        lines = [line.removesuffix("|") for line in lines]
    (repo / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    assert claims.check_package_table_versions(repo) == []


@pytest.mark.parametrize("row", ["|" + ROW, ROW.rstrip() + "|\n"])
def test_extra_outer_delimiter_does_not_hide_an_empty_cell(repo, row):
    (repo / "README.md").write_text(HEADER + row, encoding="utf-8")
    assert any("malformed package row" in p for p in claims.check_package_table_versions(repo))


def test_unprefixed_duplicate_row_still_checks_version(repo):
    unprefixed = ROW.removeprefix("|").replace("1.2.3", "0.0.0")
    (repo / "README.md").write_text(HEADER + ROW + unprefixed, encoding="utf-8")
    problems = claims.check_package_table_versions(repo)
    assert any("duplicate package row: example" in p for p in problems)
    assert any("table says '0.0.0'" in p for p in problems)


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
    # A package-only container may place this script directly under /app/scripts.
    # An explicit root must work without indexing nonexistent ancestor levels.
    monkeypatch.setattr(claims, "__file__", str(Path(repo.anchor) / "check_public_count_claims.py"))
    monkeypatch.setattr("sys.argv", ["check_public_count_claims.py", "--repo-root", str(repo)])
    assert claims.main() == 1
    assert "table says '0.0.0'" in capsys.readouterr().out


def test_nomenclature_flags_drifted_dct_expansion(repo):
    pkg_readme = repo / "packages/python/example/README.md"
    pkg_readme.write_text("Uses a Delegation Context Token (DCT).\n", encoding="utf-8")
    problems = claims.check_cross_package_nomenclature(repo, expected_primitives=51)
    assert len(problems) == 1
    assert "Delegation Capability Token" in problems[0]


def test_nomenclature_allows_canonical_dct_and_dctx(repo):
    pkg_readme = repo / "packages/python/example/README.md"
    pkg_readme.write_text(
        "Uses a Delegation Capability Token (DCT) and Delegation Context (DCTX).\n",
        encoding="utf-8",
    )
    assert claims.check_cross_package_nomenclature(repo, expected_primitives=51) == []


def test_nomenclature_flags_stale_governance_primitive_count_in_ecosystem_table(repo):
    pkg_readme = repo / "packages/python/example/README.md"
    pkg_readme.write_text(
        "| [hummbl-governance](../hummbl-governance/README.md) | 34 primitives |\n",
        encoding="utf-8",
    )
    problems = claims.check_cross_package_nomenclature(repo, expected_primitives=51)
    assert len(problems) == 1
    assert "says 34, expected 51" in problems[0]


def test_nomenclature_ignores_non_governance_primitive_counts(repo):
    pkg_readme = repo / "packages/python/example/README.md"
    pkg_readme.write_text("Base120 provides 120 reasoning primitives.\n", encoding="utf-8")
    assert claims.check_cross_package_nomenclature(repo, expected_primitives=51) == []


def _nomenclature_repo(tmp_path, governance_readme, root_readme="# root\n"):
    gov = tmp_path / "packages/python/hummbl-governance"
    gov.mkdir(parents=True)
    (gov / "pyproject.toml").write_text('[project]\nname = "hummbl-governance"\nversion = "1.5.1"\n', encoding="utf-8")
    (gov / "README.md").write_text(governance_readme, encoding="utf-8")
    (tmp_path / "README.md").write_text(root_readme, encoding="utf-8")
    return tmp_path


def test_governance_readme_stale_count_without_package_name_is_flagged(tmp_path):
    repo = _nomenclature_repo(tmp_path, "Ships 48 implemented primitives today.\n")
    problems = claims.check_cross_package_nomenclature(repo, expected_primitives=51)
    assert len(problems) == 1 and "says 48" in problems[0]


def test_versioned_historical_count_is_not_flagged(tmp_path):
    repo = _nomenclature_repo(
        tmp_path,
        "Current: 51 implemented primitives.\n",
        root_readme="hummbl-governance v1.4.0 shipped 34 primitives (superseded).\n",
    )
    assert claims.check_cross_package_nomenclature(repo, expected_primitives=51) == []


def test_current_version_line_with_stale_count_is_flagged(tmp_path):
    repo = _nomenclature_repo(
        tmp_path,
        "Current: 51 implemented primitives.\n",
        root_readme="hummbl-governance 1.5.1 ships 34 primitives.\n",
    )
    problems = claims.check_cross_package_nomenclature(repo, expected_primitives=51)
    assert len(problems) == 1 and "says 34" in problems[0]


def test_other_package_readme_compares_only_hummbl_governance_statements(tmp_path):
    readme = tmp_path / "README.md"
    readme.write_text(
        "This package ships 4 implemented primitives of its own.\n"
        "- [hummbl-governance](https://pypi.org/project/hummbl-governance/) - 51 implemented primitives\n",
        encoding="utf-8",
    )
    pattern = claims._governance_scoped(claims.re.compile(r"(\d+)\s+implemented primitives"))
    check = claims.CountCheck(name="implemented_primitives", expected=51, targets=((readme, pattern),))
    assert claims.find_mismatches(check) == []


def test_other_package_readme_still_flags_stale_governance_count(tmp_path):
    readme = tmp_path / "README.md"
    readme.write_text(
        "- [hummbl-governance](https://pypi.org/project/hummbl-governance/) - 48 implemented primitives\n",
        encoding="utf-8",
    )
    pattern = claims._governance_scoped(claims.re.compile(r"(\d+)\s+implemented primitives"))
    check = claims.CountCheck(name="implemented_primitives", expected=51, targets=((readme, pattern),))
    problems = claims.find_mismatches(check)
    assert len(problems) == 1 and "found 48" in problems[0]


def test_two_counts_on_one_qualifying_line_are_both_checked(tmp_path):
    readme = tmp_path / "README.md"
    readme.write_text(
        "hummbl-governance: 51 implemented primitives; hummbl-governance API: 48 implemented primitives.\n",
        encoding="utf-8",
    )
    pattern = claims._governance_scoped(claims.re.compile(r"(\d+)\s+implemented primitives"))
    check = claims.CountCheck(name="implemented_primitives", expected=51, targets=((readme, pattern),))
    problems = claims.find_mismatches(check)
    assert len(problems) == 1 and "found 48" in problems[0]
