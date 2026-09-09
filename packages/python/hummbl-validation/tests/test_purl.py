"""Tests for PURL parsing, normalization, and identity semantics.

The kill condition from the design doc: 'If Package URL normalization
silently equates identities that are semantically different across
ecosystems (e.g., same name in npm and PyPI), the normalization is a
false equivalence.' These tests enforce that.
"""

import pytest
from hummbl_validation.purl import PURL, parse, normalize


class TestParse:
    def test_basic_pypi(self):
        p = parse("pkg:pypi/django@5.0")
        assert p.type == "pypi"
        assert p.name == "django"
        assert p.version == "5.0"
        assert p.namespace is None

    def test_github_with_namespace(self):
        p = parse("pkg:github/hummbl-io/oss@main")
        assert p.type == "github"
        assert p.namespace == "hummbl-io"
        assert p.name == "oss"
        assert p.version == "main"

    def test_npm_scoped(self):
        p = parse("pkg:npm/@types/node@20.0.0")
        assert p.type == "npm"
        assert p.namespace == "@types"
        assert p.name == "node"
        assert p.version == "20.0.0"

    def test_type_lowercased(self):
        p = parse("pkg:PyPI/Django@5.0")
        assert p.type == "pypi"

    def test_no_version(self):
        p = parse("pkg:pypi/django")
        assert p.version is None
        assert p.identity == "pkg:pypi/django"

    def test_qualifiers(self):
        p = parse("pkg:pypi/django@5.0?arch=x86_64&os=linux")
        assert p.qualifiers == {"arch": "x86_64", "os": "linux"}

    def test_subpath(self):
        p = parse("pkg:github/hummbl-io/oss#src/main.py")
        assert p.subpath == "src/main.py"


class TestNormalize:
    def test_pypi_case_normalized(self):
        assert normalize("pkg:PyPI/Django@5.0") == "pkg:pypi/django@5.0"

    def test_github_case_normalized(self):
        assert normalize("pkg:GitHub/Hummbl-IO/OSS@main") == "pkg:github/hummbl-io/oss@main"

    def test_npm_case_preserved(self):
        # npm names are case-sensitive
        assert normalize("pkg:npm/LeftPad@1.0") == "pkg:npm/LeftPad@1.0"

    def test_idempotent(self):
        purl = "pkg:pypi/django@5.0"
        assert normalize(normalize(purl)) == normalize(purl)


class TestIdentity:
    def test_different_types_are_different(self):
        """Kill condition: same name in npm and PyPI are NOT equal."""
        npm = parse("pkg:npm/django")
        pypi = parse("pkg:pypi/django")
        assert npm != pypi

    def test_pypi_case_insensitive_identity(self):
        a = parse("pkg:pypi/Django")
        b = parse("pkg:pypi/django")
        assert a == b

    def test_github_case_insensitive_identity(self):
        a = parse("pkg:github/Hummbl-IO/OSS")
        b = parse("pkg:github/hummbl-io/oss")
        assert a == b

    def test_npm_case_sensitive_identity(self):
        a = parse("pkg:npm/LeftPad")
        b = parse("pkg:npm/leftpad")
        assert a != b

    def test_version_affects_identity(self):
        a = parse("pkg:pypi/django@4.0")
        b = parse("pkg:pypi/django@5.0")
        assert a != b

    def test_qualifiers_not_in_identity(self):
        a = parse("pkg:pypi/django@5.0?arch=x86_64")
        b = parse("pkg:pypi/django@5.0?arch=arm64")
        assert a == b  # same identity, different qualifiers

    def test_subpath_not_in_identity(self):
        a = parse("pkg:github/hummbl-io/oss#src/a.py")
        b = parse("pkg:github/hummbl-io/oss#src/b.py")
        assert a == b  # same identity, different subpath


class TestErrors:
    def test_empty_string(self):
        with pytest.raises(ValueError, match="empty"):
            parse("")

    def test_missing_scheme(self):
        with pytest.raises(ValueError, match="pkg:"):
            parse("pypi/django")

    def test_missing_name(self):
        with pytest.raises(ValueError, match="name"):
            parse("pkg:pypi/")

    def test_missing_type(self):
        with pytest.raises(ValueError, match="type"):
            parse("pkg:/django")

    def test_non_string(self):
        with pytest.raises(TypeError):
            parse(123)  # type: ignore[arg-type]
