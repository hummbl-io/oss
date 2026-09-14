"""Tests for B1: CI watcher."""

from __future__ import annotations

from hummbl_gitops.protocol import CICompletion
from hummbl_gitops.return_.ci_watcher import (
    PRCheckState,
    WatchResult,
    detect_transition,
)


class TestDetectTransition:
    def test_first_poll_complete_reports_transition(self) -> None:
        current = PRCheckState(
            pr_number=1,
            checks_total=5,
            checks_completed=5,
            checks_passed=5,
            checks_failed=0,
            in_progress=False,
            last_result="PASS",
        )
        result = detect_transition(None, current)
        assert result.transitioned
        assert result.completion is not None
        assert result.completion.result == "PASS"

    def test_first_poll_in_progress_no_transition(self) -> None:
        current = PRCheckState(
            pr_number=1,
            checks_total=5,
            checks_completed=2,
            checks_passed=2,
            checks_failed=0,
            in_progress=True,
        )
        result = detect_transition(None, current)
        assert not result.transitioned
        assert result.completion is None

    def test_running_to_complete_transition(self) -> None:
        previous = PRCheckState(
            pr_number=1,
            checks_total=5,
            checks_completed=2,
            checks_passed=2,
            checks_failed=0,
            in_progress=True,
        )
        current = PRCheckState(
            pr_number=1,
            checks_total=5,
            checks_completed=5,
            checks_passed=3,
            checks_failed=2,
            in_progress=False,
            last_result="FAIL",
        )
        result = detect_transition(previous, current)
        assert result.transitioned
        assert result.completion.result == "FAIL"
        assert result.completion.checks_failed == 2

    def test_result_change_transition(self) -> None:
        previous = PRCheckState(
            pr_number=1,
            checks_total=5,
            checks_completed=5,
            checks_passed=3,
            checks_failed=2,
            in_progress=False,
            last_result="FAIL",
        )
        current = PRCheckState(
            pr_number=1,
            checks_total=5,
            checks_completed=5,
            checks_passed=5,
            checks_failed=0,
            in_progress=False,
            last_result="PASS",
        )
        result = detect_transition(previous, current)
        assert result.transitioned
        assert result.completion.result == "PASS"

    def test_no_change_no_transition(self) -> None:
        previous = PRCheckState(
            pr_number=1,
            checks_total=5,
            checks_completed=5,
            checks_passed=5,
            checks_failed=0,
            in_progress=False,
            last_result="PASS",
        )
        current = PRCheckState(
            pr_number=1,
            checks_total=5,
            checks_completed=5,
            checks_passed=5,
            checks_failed=0,
            in_progress=False,
            last_result="PASS",
        )
        result = detect_transition(previous, current)
        assert not result.transitioned


class TestCICompletion:
    def test_to_bus_message(self) -> None:
        completion = CICompletion(
            pr_number=42,
            result="PASS",
            checks_total=8,
            checks_passed=8,
            checks_failed=0,
            host="test-host",
            repo="hummbl-io/hummbl-governance",
        )
        msg = completion.to_bus_message()
        assert "pr=42" in msg
        assert "result=PASS" in msg
        assert "checks=8/8" in msg
        assert "host=test-host" in msg
        assert "repo=hummbl-io/hummbl-governance" in msg

    def test_to_bus_message_no_repo(self) -> None:
        completion = CICompletion(
            pr_number=42,
            result="FAIL",
            checks_total=8,
            checks_passed=5,
            checks_failed=3,
            host="test-host",
        )
        msg = completion.to_bus_message()
        assert "repo=" not in msg
        assert "failed=3" in msg
