"""Tests for write_boundary enforcer module."""

import json

import pytest
from hummbl_cognition.write_boundary import (
    BoundaryResult,
    WriteBoundaryEnforcer,
    WriteBoundaryError,
)


class TestWriteBoundaryEnforcer:
    """Tests for WriteBoundaryEnforcer class."""

    def test_default_authorized_repos(self):
        enforcer = WriteBoundaryEnforcer()
        assert "hummbl-io/arbiter" in enforcer._authorized
        assert len(enforcer._authorized) == 5

    def test_custom_authorized_repos(self):
        enforcer = WriteBoundaryEnforcer(authorized_repos=["hummbl-io/test"])
        assert enforcer.check_repo("hummbl-io/test").authorized is True
        assert enforcer.check_repo("hummbl-io/other").authorized is False

    def test_empty_authorized_repos_raises(self):
        with pytest.raises(WriteBoundaryError, match="must not be empty"):
            WriteBoundaryEnforcer(authorized_repos=[])

    def test_check_authorized_repo(self):
        enforcer = WriteBoundaryEnforcer()
        result = enforcer.check_repo("hummbl-io/arbiter")
        assert result.authorized is True
        assert result.reason == ""

    def test_check_unauthorized_repo(self):
        enforcer = WriteBoundaryEnforcer()
        result = enforcer.check_repo("hummbl-io/unknown")
        assert result.authorized is False
        assert "not in authorized" in result.reason

    def test_check_empty_repo(self):
        enforcer = WriteBoundaryEnforcer()
        result = enforcer.check_repo("")
        assert result.authorized is False
        assert "invalid" in result.reason

    def test_check_none_repo(self):
        enforcer = WriteBoundaryEnforcer()
        result = enforcer.check_repo(None)  # type: ignore[arg-type]
        assert result.authorized is False
        assert "invalid" in result.reason

    def test_check_strips_whitespace(self):
        enforcer = WriteBoundaryEnforcer()
        result = enforcer.check_repo("  hummbl-io/arbiter  ")
        assert result.authorized is True

    def test_from_config_file(self, tmp_path):
        config = {"authorized_repos": ["hummbl-io/test-repo"]}
        config_path = tmp_path / "config.json"
        config_path.write_text(json.dumps(config))
        enforcer = WriteBoundaryEnforcer.from_config(config_path)
        assert enforcer.check_repo("hummbl-io/test-repo").authorized is True

    def test_from_config_missing_file(self, tmp_path):
        with pytest.raises(WriteBoundaryError, match="not found"):
            WriteBoundaryEnforcer.from_config(tmp_path / "missing.json")

    def test_from_config_invalid_format(self, tmp_path):
        config_path = tmp_path / "config.json"
        config_path.write_text(json.dumps({"wrong_key": []}))
        with pytest.raises(WriteBoundaryError, match="authorized_repos"):
            WriteBoundaryEnforcer.from_config(config_path)

    def test_filter_candidates_authorized(self):
        enforcer = WriteBoundaryEnforcer()
        candidates = [
            {"repo": "hummbl-io/arbiter", "title": "test"},
            {"repo": "hummbl-io/hummbl-governance", "title": "test2"},
        ]
        result = enforcer.filter_candidates(candidates)
        assert len(result.authorized) == 2
        assert len(result.skipped) == 0
        assert result.total == 2

    def test_filter_candidates_mixed(self):
        enforcer = WriteBoundaryEnforcer()
        candidates = [
            {"repo": "hummbl-io/arbiter", "title": "test"},
            {"repo": "hummbl-io/unknown", "title": "test2"},
        ]
        result = enforcer.filter_candidates(candidates)
        assert len(result.authorized) == 1
        assert len(result.skipped) == 1
        assert result.skipped[0]["_skip_reason"] != ""

    def test_filter_candidates_empty(self):
        enforcer = WriteBoundaryEnforcer()
        result = enforcer.filter_candidates([])
        assert len(result.authorized) == 0
        assert len(result.skipped) == 0
        assert result.total == 0

    def test_filter_candidates_missing_repo(self):
        enforcer = WriteBoundaryEnforcer()
        candidates = [{"title": "no repo field"}]
        result = enforcer.filter_candidates(candidates)
        assert len(result.authorized) == 0
        assert len(result.skipped) == 1


class TestEnforcerMethodShortcuts:
    """Tests that instantiate the enforcer and delegate (replaces removed convenience functions)."""

    def test_check_repo_via_enforcer(self):
        enforcer = WriteBoundaryEnforcer()
        result = enforcer.check_repo("hummbl-io/arbiter")
        assert result.authorized is True

    def test_check_repo_via_enforcer_unauthorized(self):
        enforcer = WriteBoundaryEnforcer()
        result = enforcer.check_repo("hummbl-io/unknown")
        assert result.authorized is False

    def test_filter_candidates_via_enforcer(self):
        enforcer = WriteBoundaryEnforcer()
        candidates = [{"repo": "hummbl-io/arbiter", "title": "test"}]
        result = enforcer.filter_candidates(candidates)
        assert len(result.authorized) == 1


class TestBoundaryResult:
    """Tests for BoundaryResult dataclass."""

    def test_to_dict(self):
        r = BoundaryResult(repo="hummbl-io/test", authorized=True)
        d = r.to_dict()
        assert d == {"repo": "hummbl-io/test", "authorized": True, "reason": ""}

    def test_to_dict_with_reason(self):
        r = BoundaryResult(
            repo="hummbl-io/test", authorized=False, reason="not allowed"
        )
        d = r.to_dict()
        assert d["reason"] == "not allowed"
