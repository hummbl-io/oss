"""Adversarial evaluation helpers for Sigil Forge programs."""

from __future__ import annotations

from dataclasses import dataclass

from hummbl_cognition.sigil_forge.engine import ExecutionEngine


@dataclass(frozen=True)
class EvalCase:
    name: str
    source: str
    user_input: str
    expect_blocked: bool = False


@dataclass(frozen=True)
class EvalResult:
    name: str
    passed: bool
    detail: str


def run_eval_cases(
    engine: ExecutionEngine, cases: list[EvalCase]
) -> tuple[EvalResult, ...]:
    results: list[EvalResult] = []
    for case in cases:
        try:
            state = engine.run(case.source, case.user_input)
        except Exception as exc:
            results.append(
                EvalResult(
                    case.name,
                    not case.expect_blocked,
                    f"raised {type(exc).__name__}: {exc}",
                )
            )
            continue
        blocked = any(
            event.get("event") == "preprocess_blocked" for event in state.audit
        )
        results.append(
            EvalResult(case.name, blocked == case.expect_blocked, f"blocked={blocked}")
        )
    return tuple(results)
