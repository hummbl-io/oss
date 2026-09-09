"""LLM-based detectors for the PAIDEIA-9 HARD axes (D, V, L).

The v0.1 score_paideia.py uses heuristic detectors for M, C, P (EASY) and
returns stub values for D, V, L (HARD). Per docs/paideia-9.md §9, HARD axes
are drift-prone under single-LLM scoring and require ensemble + variance
flagging (std > 0.75 -> low confidence).

This module provides one LLM-backed detector per HARD axis, each:

- Loads a versioned rubric prompt from prompts/paideia_detect_<axis>_v1.txt
- Runs N independent samples (default 3) against the configured Ollama
  endpoint, with seeds bumped per sample
- Computes mean score (rounded to nearest int) and population std
- Flags low-confidence results when std > FLAG_THRESHOLD
- Returns the same (score, note) tuple as the heuristic detectors so the
  drop-in to score_paideia.DETECTORS is mechanical

CPU-only when ollama_fn is a fake (used in tests). Production callers pass
gc.ollama_generate; tests pass a closure that returns canned OllamaResults.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _gen_common as gc

PROMPT_VERSION = "paideia-detect-v1"
HARD_AXES = ("D", "V", "L")
FLAG_THRESHOLD = 0.75   # spec §9: std above this flags low confidence
DEFAULT_N_RUNS = 3
DEFAULT_TIMEOUT = 600

_PROMPT_NAMES = {
    "D": "paideia_detect_depth",
    "V": "paideia_detect_motivation",
    "L": "paideia_detect_load",
}


def _load_axis_prompt(axis: str) -> tuple[str, gc._string.Template]:
    if axis not in _PROMPT_NAMES:
        raise ValueError(f"no LLM detector for axis {axis!r}; "
                         f"HARD axes are {HARD_AXES}")
    return gc.load_prompt(_PROMPT_NAMES[axis], "v1")


def _parse_one_score(parsed: dict | None) -> tuple[int | None, str]:
    """Pull (score, rationale) from a parsed LLM JSON. Returns (None, reason)
    on any validation failure."""
    if not isinstance(parsed, dict):
        return None, f"parsed not a dict: {type(parsed).__name__}"
    score = parsed.get("score")
    if not isinstance(score, int):
        # Some models return float; coerce if integral.
        if isinstance(score, float) and score.is_integer():
            score = int(score)
        else:
            return None, f"score missing or non-int: {score!r}"
    if not 0 <= score <= 4:
        return None, f"score out of range: {score}"
    rationale = parsed.get("rationale")
    if not isinstance(rationale, str) or not rationale.strip():
        rationale = "(no rationale)"
    return score, rationale.strip()


def _aggregate(samples: list[tuple[int, str]]) -> tuple[int, float]:
    """Mean rounded to nearest int + population std. Empty list -> (0, 0.0)."""
    if not samples:
        return 0, 0.0
    scores = [s for s, _ in samples]
    mean = sum(scores) / len(scores)
    var = sum((s - mean) ** 2 for s in scores) / len(scores)
    std = math.sqrt(var)
    return round(mean), round(std, 3)


def detect_axis_llm(
    axis: str,
    text: str,
    *,
    endpoint: dict,
    ollama_fn=None,
    n_runs: int = DEFAULT_N_RUNS,
    seed: int | None = None,
    timeout: int = DEFAULT_TIMEOUT,
) -> tuple[int, str]:
    """Score one HARD axis via N-run LLM ensemble.

    Returns (score, note) where note encodes the ensemble metadata:
      'D=3 (mean=2.67 std=0.47 n=3, 3/3 valid)'

    If no sample returns a valid score, returns (0, 'all_runs_invalid: <reasons>').
    The caller (score_paideia.score_content) treats the returned score the
    same as a heuristic detector's output; the variance flag is in the note.

    The endpoint dict must look like a gc.load_endpoint() return:
      {'name': str, 'model': str, 'url': str}.

    The ollama_fn parameter is the dependency-injection point for tests.
    Production passes None to use gc.ollama_generate.
    """
    if ollama_fn is None:
        ollama_fn = gc.ollama_generate
    system, user_tmpl = _load_axis_prompt(axis)

    samples: list[tuple[int, str]] = []
    invalid_reasons: list[str] = []
    for i in range(n_runs):
        run_seed = None if seed is None else seed + i
        user = user_tmpl.safe_substitute(content=text)
        result = ollama_fn(endpoint, system, user, seed=run_seed,
                           think=False, timeout=timeout)
        if not result.ok():
            invalid_reasons.append(f"run{i}:ollama:{result.parse_error}")
            continue
        score, rationale = _parse_one_score(result.parsed)
        if score is None:
            invalid_reasons.append(f"run{i}:{rationale}")
            continue
        samples.append((score, rationale))

    if not samples:
        return 0, ("all_runs_invalid: "
                   + "; ".join(invalid_reasons[:3]))

    final_score, std = _aggregate(samples)
    flag = " low_confidence" if std > FLAG_THRESHOLD else ""
    note = (f"{axis}={final_score} (mean={sum(s for s,_ in samples)/len(samples):.2f} "
            f"std={std} n={len(samples)}/{n_runs} valid){flag}")
    return final_score, note


def detect_hard_axes(
    text: str,
    *,
    endpoint: dict,
    ollama_fn=None,
    n_runs: int = DEFAULT_N_RUNS,
    seed: int | None = None,
    timeout: int = DEFAULT_TIMEOUT,
) -> dict[str, tuple[int, str]]:
    """Run all 3 HARD-axis LLM detectors. Returns {axis: (score, note)}.

    Convenience wrapper for score_paideia.score_content when --use-llm is on.
    Each axis seeds independently (seed, seed+1, seed+2 for axis-runs collide
    only at the within-axis level).
    """
    out: dict[str, tuple[int, str]] = {}
    for axis in HARD_AXES:
        out[axis] = detect_axis_llm(
            axis, text, endpoint=endpoint, ollama_fn=ollama_fn,
            n_runs=n_runs, seed=seed, timeout=timeout)
    return out
