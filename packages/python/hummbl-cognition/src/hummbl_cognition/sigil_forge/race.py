"""Clean-room model/prompt race harness for Sigil Forge."""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass

Scorer = Callable[[str, str], float]
RaceAdapter = Callable[[str], str]


@dataclass(frozen=True)
class RaceCandidate:
    name: str
    adapter: RaceAdapter
    prompt_prefix: str = ""


@dataclass(frozen=True)
class RaceResult:
    name: str
    output: str
    score: float
    duration_ms: int
    success: bool
    error: str | None = None


@dataclass(frozen=True)
class RaceReport:
    prompt: str
    results: tuple[RaceResult, ...]

    @property
    def winner(self) -> RaceResult | None:
        successful = [result for result in self.results if result.success]
        if not successful:
            return None
        return max(successful, key=lambda result: result.score)


def run_race(
    *,
    prompt: str,
    candidates: list[RaceCandidate],
    scorer: Scorer | None = None,
) -> RaceReport:
    score_fn = scorer or default_scorer
    results: list[RaceResult] = []
    for candidate in candidates:
        started = time.monotonic()
        try:
            candidate_prompt = "\n".join(part for part in (candidate.prompt_prefix, prompt) if part)
            output = candidate.adapter(candidate_prompt)
            score = score_fn(prompt, output)
            results.append(
                RaceResult(
                    name=candidate.name,
                    output=output,
                    score=score,
                    duration_ms=_elapsed_ms(started),
                    success=True,
                )
            )
        except Exception as exc:
            results.append(
                RaceResult(
                    name=candidate.name,
                    output="",
                    score=0.0,
                    duration_ms=_elapsed_ms(started),
                    success=False,
                    error=f"{type(exc).__name__}: {exc}",
                )
            )
    return RaceReport(prompt=prompt, results=tuple(results))


def default_scorer(prompt: str, output: str) -> float:
    """Score an output without external judges.

    This intentionally rewards simple baseline qualities: non-empty output,
    direct lexical overlap, and moderate length. Production callers should
    inject a task-specific rubric or model judge.
    """
    if not output.strip():
        return 0.0
    prompt_terms = {term.lower() for term in prompt.split() if len(term) > 3}
    output_terms = {term.lower().strip(".,:;!?") for term in output.split()}
    overlap = len(prompt_terms & output_terms) / max(len(prompt_terms), 1)
    length_score = min(len(output.split()) / 80, 1.0)
    return round((0.6 * overlap) + (0.4 * length_score), 4)


def _elapsed_ms(started: float) -> int:
    return int((time.monotonic() - started) * 1000)
