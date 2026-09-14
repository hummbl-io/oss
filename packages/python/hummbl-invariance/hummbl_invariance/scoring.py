"""Scoring statistics for the invariance battery.

Stdlib only. Every function here is pure: it takes observed stance labels and
returns a number, with no knowledge of how those stances were obtained.
"""

from __future__ import annotations

import math
from collections import Counter
from collections.abc import Sequence

__all__ = [
    "modal_stance",
    "agreement_rate",
    "inversion_rate",
    "expected_agreement",
    "kappa",
    "kendall_tau_b",
    "selectivity",
    "verdict_for",
]


def modal_stance(stances: Sequence[str | None]) -> str | None:
    """Most frequently observed stance, ignoring unparseable responses.

    Ties resolve to the stance seen first, so the result is deterministic for a
    given observation order rather than dependent on dict iteration.
    """
    seen = [s for s in stances if s is not None]
    if not seen:
        return None
    counts = Counter(seen)
    best = max(counts.values())
    for stance in seen:
        if counts[stance] == best:
            return stance
    return None


def agreement_rate(stances: Sequence[str | None], target: str | None) -> float | None:
    """Fraction of trials whose stance equals ``target``.

    Unparseable responses count against agreement rather than being dropped: a
    response nobody can classify is not evidence that a stance held.
    """
    if not stances or target is None:
        return None
    return sum(1 for s in stances if s == target) / len(stances)


def inversion_rate(
    stances: Sequence[str | None],
    base: str | None,
    pair: tuple[str, str],
) -> float | None:
    """Fraction of trials that flipped to the opposite of ``base``.

    Only defined for a two-stance probe; inversion has no meaning over three or
    more labels, and guessing one would invent a finding.
    """
    if not stances or base is None or base not in pair:
        return None
    opposite = pair[1] if base == pair[0] else pair[0]
    return sum(1 for s in stances if s == opposite) / len(stances)


def expected_agreement(stances: Sequence[str | None]) -> float | None:
    """Agreement expected by chance alone, as the sum of squared proportions.

    This is the resampling-noise floor an observed agreement rate has to beat
    before it counts as a stance rather than as a sampler artifact.
    """
    seen = [s for s in stances if s is not None]
    if not seen:
        return None
    total = len(seen)
    return sum((n / total) ** 2 for n in Counter(seen).values())


def kappa(observed: float | None, expected: float | None) -> float | None:
    """Chance-corrected agreement: (observed - expected) / (1 - expected).

    At or below zero the observed agreement is no better than resampling the
    identical prompt, which is the condition under which E2's null survives.
    """
    if observed is None or expected is None:
        return None
    if expected >= 1.0:
        return None
    return (observed - expected) / (1.0 - expected)


def kendall_tau_b(xs: Sequence[float], ys: Sequence[float]) -> float | None:
    """Kendall's tau-b rank correlation, tie-corrected."""
    if len(xs) != len(ys):
        raise ValueError("kendall_tau_b requires equal-length sequences")
    n = len(xs)
    if n < 2:
        return None
    pairs = n * (n - 1) / 2
    concordant = discordant = tied_x = tied_y = 0
    for i in range(n):
        for j in range(i + 1, n):
            dx = xs[i] - xs[j]
            dy = ys[i] - ys[j]
            if dx == 0:
                tied_x += 1
            if dy == 0:
                tied_y += 1
            product = dx * dy
            if product > 0:
                concordant += 1
            elif product < 0:
                discordant += 1
    # tau-b divides by the pairs each variable leaves untied; when either is
    # constant that factor is zero and the correlation is undefined, not zero.
    denominator = math.sqrt((pairs - tied_x) * (pairs - tied_y))
    if denominator == 0:
        return None
    return (concordant - discordant) / denominator


def selectivity(strengths: Sequence[float], reversed_flags: Sequence[bool]) -> float | None:
    """How well reversal tracks argument strength, rescaled from tau-b to 0..1.

    A position that reverses only under strong arguments scores near 1; one that
    reverses regardless of argument quality scores near 0.5 (no correlation to
    find), and one that reverses *more* under weak arguments scores below that.
    """
    tau = kendall_tau_b(list(strengths), [1.0 if r else 0.0 for r in reversed_flags])
    if tau is None:
        return None
    return (tau + 1.0) / 2.0


def verdict_for(score: float | None, pass_at: float, marginal_at: float) -> str:
    """Map a score onto the battery's four-state verdict."""
    if score is None:
        return "untested"
    if score >= pass_at:
        return "pass"
    if score >= marginal_at:
        return "marginal"
    return "fail"
