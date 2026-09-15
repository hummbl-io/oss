"""Deterministic stand-in responders.

Not a model and never a substitute for one: these exist so the battery's own
arithmetic can be exercised and tested without a network call. A run against a
stub is labelled as such in its record and proves nothing about any real system.
"""

from __future__ import annotations

import random
from collections.abc import Sequence

from hummbl_invariance.models import Variant

__all__ = ["StubResponder", "keyword_classifier"]


class StubResponder:
    """A synthetic disposition with knobs for the failure modes worth testing.

    ``drift`` is the chance of wandering off the base stance on an axis that
    should not move it. ``pushback_mode`` decides what happens under objection:

    - ``selective`` — reverses when the objection's strength clears a threshold,
      the behaviour a genuinely held position should show
    - ``uniform`` — reverses under every objection regardless of quality
    - ``rigid`` — never reverses, however strong the objection
    """

    def __init__(
        self,
        stances: Sequence[str],
        *,
        base_stance: str | None = None,
        drift: float = 0.0,
        pushback_mode: str = "selective",
        pushback_threshold: float = 0.6,
        seed: int = 0,
    ) -> None:
        if len(stances) < 2:
            raise ValueError("a stub responder needs at least two stances")
        if pushback_mode not in {"selective", "uniform", "rigid"}:
            raise ValueError(f"unknown pushback_mode {pushback_mode!r}")
        self.stances = tuple(stances)
        self.base_stance = base_stance or self.stances[0]
        self.drift = drift
        self.pushback_mode = pushback_mode
        self.pushback_threshold = pushback_threshold
        self._rng = random.Random(seed)

    def _other(self) -> str:
        alternatives = [s for s in self.stances if s != self.base_stance]
        return self._rng.choice(alternatives)

    def __call__(self, variant: Variant) -> str:
        if variant.axis == "negation":
            return self._other()
        if variant.axis == "pushback":
            strength = variant.strength or 0.0
            if self.pushback_mode == "uniform":
                return self._other()
            if self.pushback_mode == "rigid":
                return self.base_stance
            return self._other() if strength >= self.pushback_threshold else self.base_stance
        if self.drift and self._rng.random() < self.drift:
            return self._other()
        return self.base_stance


def keyword_classifier(stances: Sequence[str]):
    """Classify a response by the first stance label that appears in it.

    Deliberately literal — a real run needs a classifier that reads prose. This
    one only has to be predictable.
    """

    ordered = tuple(stances)

    def classify(raw: str) -> str | None:
        lowered = raw.lower()
        for stance in ordered:
            if stance.lower() in lowered:
                return stance
        return None

    return classify
