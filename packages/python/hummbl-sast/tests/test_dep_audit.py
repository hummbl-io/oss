"""Tests for the dependency audit module."""
import pathlib
import tempfile
import textwrap
from unittest.mock import patch, MagicMock

from hummbl_sast.dep_audit import (
    parse_pyproject_toml,
    parse_requirements_txt,
    parse_package_json,
    parse_go_mod,
    _parse_pep508,
    audit_dependency,
    Dependency,
    find_dep_files,
)


def test_parse_pep508_exact():
    assert _parse_pep508("foo==1.2.3") == ("foo", "1.2.3")


def test_parse_pep508_lower_bound():
    assert _parse_pep508("foo>=1.0") == ("foo", "1.0")


def test_parse_pep508_compatible():
    assert _parse_pep508("foo~=1.2.0") == ("foo", "1.2.0")


def test_parse_pep508_bare_name():
    assert _parse_pep508("foo") == ("foo", "")


def test_parse_pep508_with_extras():
    assert _parse_pep508("foo[bar,baz]==1.0") == ("foo", "1.0")


def test_parse_pep508_with_env_marker():
    assert _parse_pep508("foo==1.0; python_version<'3.8'") == ("foo", "1.0")


def test_parse_pyproject_toml():
    with tempfile.TemporaryDirectory() as tmp:
        fpath = pathlib.Path(tmp) / "pyproject.toml"
        fpath.write_text(textwrap.dedent("""
            [project]
            name = "test-pkg"
            dependencies = ["requests>=2.0", "click~=8.0"]
            [project.optional-dependencies]
            test = ["pytest>=7.0"]
        """))
        deps = parse_pyproject_toml(fpath)
        names = {d.name for d in deps}
        assert "requests" in names
        assert "click" in names
        assert "pytest" in names


def test_parse_requirements_txt():
    with tempfile.TemporaryDirectory() as tmp:
        fpath = pathlib.Path(tmp) / "requirements.txt"
        fpath.write_text(textwrap.dedent("""
            # Comment
            requests==2.31.0
            flask>=2.0
            -e .
            # Another comment
            pytest~=7.0
        """))
        deps = parse_requirements_txt(fpath)
        names = {d.name for d in deps}
        assert "requests" in names
        assert "flask" in names
        assert "pytest" in names
        assert "-e" not in names


def test_parse_package_json():
    with tempfile.TemporaryDirectory() as tmp:
        fpath = pathlib.Path(tmp) / "package.json"
        fpath.write_text(textwrap.dedent("""
            {
                "dependencies": {"express": "^4.18.0"},
                "devDependencies": {"jest": "29.0.0"}
            }
        """))
        deps = parse_package_json(fpath)
        names = {d.name for d in deps}
        assert "express" in names
        assert "jest" in names
        # Check version stripping
        express = next(d for d in deps if d.name == "express")
        assert express.version == "4.18.0"
        assert express.ecosystem == "npm"


def test_parse_go_mod():
    with tempfile.TemporaryDirectory() as tmp:
        fpath = pathlib.Path(tmp) / "go.mod"
        fpath.write_text(textwrap.dedent("""
            module example.com/test

            go 1.21

            require (
                github.com/gin-gonic/gin v1.9.0
                github.com/stretchr/testify v1.8.0
            )

            require golang.org/x/text v0.12.0
        """))
        deps = parse_go_mod(fpath)
        names = {d.name for d in deps}
        assert "github.com/gin-gonic/gin" in names
        assert "github.com/stretchr/testify" in names
        assert "golang.org/x/text" in names


def test_find_dep_files():
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = pathlib.Path(tmp)
        (tmp_path / "pyproject.toml").write_text("[project]")
        (tmp_path / "sub").mkdir()
        (tmp_path / "sub" / "package.json").write_text("{}")
        (tmp_path / "sub" / "node_modules").mkdir()
        (tmp_path / "sub" / "node_modules" / "package.json").write_text("{}")

        files = find_dep_files(tmp_path)
        names = {f.name for f in files}
        assert "pyproject.toml" in names
        assert "package.json" in names
        # node_modules should be excluded
        assert sum(1 for f in files if "node_modules" in str(f)) == 0


def test_audit_dependency_with_mock():
    """Test audit_dependency with mocked OSV API response."""
    mock_vuln = {
        "id": "GHSA-test-1234",
        "summary": "Test vulnerability",
        "severity": [{"type": "CVSS_V3", "score": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H"}],
        "affected": [{
            "package": {"name": "test-pkg", "ecosystem": "PyPI"},
            "ranges": [{"events": [{"introduced": "0"}, {"fixed": "2.0.0"}]}],
        }],
        "references": [{"type": "ADVISORY", "url": "https://example.com/advisory"}],
    }

    dep = Dependency(name="test-pkg", version="1.0.0", ecosystem="PyPI", source_file="test")

    with patch("hummbl_sast.dep_audit.query_osv", return_value=[mock_vuln]):
        findings = audit_dependency(dep)
        assert len(findings) == 1
        assert findings[0].vuln_id == "GHSA-test-1234"
        assert findings[0].severity == "HIGH"
        assert "2.0.0" in findings[0].fixed_versions


def test_audit_dependency_clean_with_mock():
    """Test audit_dependency with no vulnerabilities."""
    dep = Dependency(name="clean-pkg", version="1.0.0", ecosystem="PyPI", source_file="test")

    with patch("hummbl_sast.dep_audit.query_osv", return_value=[]):
        findings = audit_dependency(dep)
        assert len(findings) == 0


def test_audit_dependency_no_version_skipped():
    """Dependencies without a version should be skipped."""
    dep = Dependency(name="no-version", version="", ecosystem="PyPI", source_file="test")

    with patch("hummbl_sast.dep_audit.query_osv", return_value=[]):
        findings = audit_dependency(dep)
        assert len(findings) == 0
