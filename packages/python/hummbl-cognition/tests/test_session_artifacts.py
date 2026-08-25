"""Tests for session artifact register."""

import pytest
from hummbl_cognition.session_artifacts import (
    SessionArtifact,
    clear,
    count,
    get,
    has,
    list_all,
    list_by_skill,
    list_by_type,
    register,
    summary,
)


@pytest.fixture(autouse=True)
def clean_registry():
    """Clear the registry before and after each test."""
    clear()
    yield
    clear()


class TestRegister:
    def test_register_returns_artifact(self):
        a = register("test_output", "A test artifact", "/test-skill")
        assert isinstance(a, SessionArtifact)
        assert a.name == "test_output"
        assert a.summary == "A test artifact"
        assert a.source_skill == "/test-skill"

    def test_register_with_path_and_type(self):
        a = register(
            "dashboard_url",
            "Deployed at dashboard.hummbl.io",
            "/deploy-canary",
            artifact_path="https://dashboard.hummbl.io",
            artifact_type="deployment",
        )
        assert a.artifact_path == "https://dashboard.hummbl.io"
        assert a.artifact_type == "deployment"

    def test_register_sets_timestamp(self):
        a = register("ts_test", "Check timestamp", "/test")
        assert a.timestamp is not None
        assert "T" in a.timestamp  # ISO format

    def test_register_increments_count(self):
        assert count() == 0
        register("a", "first", "/s1")
        assert count() == 1
        register("b", "second", "/s2")
        assert count() == 2


class TestGet:
    def test_get_returns_artifact(self):
        register("my_finding", "Found something", "/arcana")
        a = get("my_finding")
        assert a is not None
        assert a.name == "my_finding"

    def test_get_returns_none_for_missing(self):
        assert get("nonexistent") is None

    def test_get_returns_most_recent_on_duplicate_names(self):
        register("output", "First version", "/v1")
        register("output", "Second version", "/v2")
        a = get("output")
        assert a.summary == "Second version"
        assert a.source_skill == "/v2"


class TestListAll:
    def test_list_all_empty(self):
        assert list_all() == []

    def test_list_all_preserves_order(self):
        register("a", "first", "/s1")
        register("b", "second", "/s2")
        register("c", "third", "/s3")
        names = [a.name for a in list_all()]
        assert names == ["a", "b", "c"]

    def test_list_all_returns_copy(self):
        register("x", "test", "/s")
        result = list_all()
        result.clear()
        assert count() == 1  # original unaffected


class TestListBySkill:
    def test_filters_by_skill(self):
        register("a", "from arcana", "/arcana")
        register("b", "from build", "/build")
        register("c", "also arcana", "/arcana")
        arcana = list_by_skill("/arcana")
        assert len(arcana) == 2
        assert all(a.source_skill == "/arcana" for a in arcana)


class TestListByType:
    def test_filters_by_type(self):
        register("a", "code", "/build", artifact_type="code")
        register("b", "doc", "/signal", artifact_type="document")
        register("c", "more code", "/build", artifact_type="code")
        code = list_by_type("code")
        assert len(code) == 2


class TestHas:
    def test_has_true(self):
        register("exists", "yes", "/s")
        assert has("exists") is True

    def test_has_false(self):
        assert has("nope") is False


class TestSummary:
    def test_summary_empty(self):
        assert "No session artifacts" in summary()

    def test_summary_with_artifacts(self):
        register("arcana_synthesis", "14 hypotheses", "/arcana")
        register("dashboard_url", "dashboard.hummbl.io", "/deploy-canary", artifact_path="https://dashboard.hummbl.io")
        s = summary()
        assert "arcana_synthesis" in s
        assert "dashboard_url" in s
        assert "dashboard.hummbl.io" in s
        assert "(2)" in s


class TestClear:
    def test_clear_returns_count(self):
        register("a", "x", "/s")
        register("b", "y", "/s")
        n = clear()
        assert n == 2
        assert count() == 0

    def test_clear_empty(self):
        assert clear() == 0


class TestFrozen:
    def test_artifact_is_immutable(self):
        a = register("frozen_test", "should not change", "/test")
        with pytest.raises(AttributeError):
            a.name = "hacked"
