"""Unit tests for Sigil Forge adversarial evaluation runner."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from hummbl_cognition.sigil_forge.evals import EvalCase, run_eval_cases


@dataclass
class _StubState:
    audit: list[dict[str, Any]] = field(default_factory=list)


class _StubEngine:
    """Minimal ExecutionEngine double for testing run_eval_cases."""

    def __init__(self, behavior: dict[str, _StubState | Exception]) -> None:
        self._behavior = behavior

    def run(self, source: str, user_input: str) -> _StubState:
        outcome = self._behavior[source]
        if isinstance(outcome, Exception):
            raise outcome
        return outcome


def test_exception_never_passes_eval_case() -> None:
    """Unhandled exceptions must fail whether expect_blocked is False or True."""
    engine = _StubEngine(
        {
            "crash_normal": RuntimeError("boom"),
            "crash_blocked": ValueError("parse error"),
        }
    )
    cases = [
        EvalCase(
            name="normal-crash",
            source="crash_normal",
            user_input="hello",
            expect_blocked=False,
        ),
        EvalCase(
            name="blocked-crash",
            source="crash_blocked",
            user_input="attack",
            expect_blocked=True,
        ),
    ]

    results = run_eval_cases(engine, cases)  # type: ignore[arg-type]

    assert len(results) == 2
    assert results[0].passed is False
    assert "RuntimeError: boom" in results[0].detail
    assert results[1].passed is False
    assert "ValueError: parse error" in results[1].detail


def test_normal_and_blocked_outcomes_match_expectation() -> None:
    """Normal execution evaluates preprocess_blocked against expect_blocked."""
    engine = _StubEngine(
        {
            "ok": _StubState(audit=[{"event": "complete"}]),
            "blocked": _StubState(audit=[{"event": "preprocess_blocked"}]),
        }
    )
    cases = [
        EvalCase(name="pass-ok", source="ok", user_input="hi", expect_blocked=False),
        EvalCase(
            name="pass-blocked",
            source="blocked",
            user_input="bad",
            expect_blocked=True,
        ),
        EvalCase(
            name="fail-unexpected-block",
            source="blocked",
            user_input="hi",
            expect_blocked=False,
        ),
    ]

    results = run_eval_cases(engine, cases)  # type: ignore[arg-type]

    assert [r.passed for r in results] == [True, True, False]
