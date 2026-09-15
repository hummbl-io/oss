"""Tests for protocol constants and dataclasses."""

from __future__ import annotations

from hummbl_gitops.protocol import (
    CI_COMPLETED,
    CICompletion,
    MAIN_MOVED,
    MainMoved,
    REVIEW_ASPECTS,
    REVIEW_CLAIMED,
    ReviewClaim,
    validate_aspect,
)


class TestReviewAspects:
    def test_security_is_valid(self) -> None:
        assert validate_aspect("security")

    def test_unknown_aspect_invalid(self) -> None:
        assert not validate_aspect("unknown-aspect")

    def test_all_aspects_present(self) -> None:
        expected = {"security", "logic", "tests", "docs", "style", "ci", "performance", "breaking"}
        assert REVIEW_ASPECTS == expected


class TestReviewClaim:
    def test_to_bus_message(self) -> None:
        claim = ReviewClaim(pr_number=42, aspect="security", agent="devin", host="test-host")
        msg = claim.to_bus_message()
        assert "pr=42" in msg
        assert "aspect=security" in msg
        assert "agent=devin" in msg
        assert "host=test-host" in msg


class TestCICompletion:
    def test_to_bus_message_with_repo(self) -> None:
        c = CICompletion(
            pr_number=42, result="PASS", checks_total=5,
            checks_passed=5, checks_failed=0, host="test-host",
            repo="hummbl-io/hummbl-governance",
        )
        assert "repo=hummbl-io/hummbl-governance" in c.to_bus_message()


class TestMainMoved:
    def test_to_bus_message_with_stale(self) -> None:
        m = MainMoved(
            local_sha="abc", remote_sha="def", commits_behind=3,
            stale_branches=("feat/a", "feat/b"), host="test-host",
        )
        msg = m.to_bus_message()
        assert "behind=3" in msg
        assert "stale_branches=feat/a,feat/b" in msg

    def test_to_bus_message_no_stale(self) -> None:
        m = MainMoved(
            local_sha="abc", remote_sha="abc", commits_behind=0,
            stale_branches=(), host="test-host",
        )
        msg = m.to_bus_message()
        assert "stale_branches=none" in msg


class TestMessageTypes:
    def test_types_are_strings(self) -> None:
        assert isinstance(CI_COMPLETED, str)
        assert isinstance(MAIN_MOVED, str)
        assert isinstance(REVIEW_CLAIMED, str)
