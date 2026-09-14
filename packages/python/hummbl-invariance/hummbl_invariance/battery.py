"""The battery itself: build variants, collect observations, score each axis.

The library never talks to a model. The caller injects a ``Responder`` (what to
ask) and a ``Classifier`` (how to read the answer), which keeps every result
here reproducible and keeps network code out of a stdlib-only package.
"""

from __future__ import annotations

import random
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from hummbl_invariance import scoring
from hummbl_invariance.axes import Axis, build_axis
from hummbl_invariance.loader import load_axis_catalog
from hummbl_invariance.models import AxisResult, Baseline, Observation, Probe, Variant

__all__ = ["Responder", "Classifier", "BatteryRun", "InvarianceBattery"]

Responder = Callable[[Variant], str]
Classifier = Callable[[str], str | None]


@dataclass(frozen=True)
class BatteryRun:
    run_id: str
    created: str
    probe: Probe
    responder_label: str
    condition: str
    axis_results: tuple[AxisResult, ...]
    base_stance: str | None = None
    baseline: Baseline | None = None
    notes: str = ""
    observations: tuple[Observation, ...] = field(default=(), repr=False)

    @property
    def scored(self) -> tuple[AxisResult, ...]:
        return tuple(r for r in self.axis_results if r.score is not None)

    @property
    def overall(self) -> float | None:
        scored = self.scored
        if not scored:
            return None
        return sum(r.score for r in scored) / len(scored)  # type: ignore[misc]

    def weakest(self) -> AxisResult | None:
        scored = self.scored
        if not scored:
            return None
        return min(scored, key=lambda r: r.score)  # type: ignore[arg-type,return-value]

    def strongest(self) -> AxisResult | None:
        scored = self.scored
        if not scored:
            return None
        return max(scored, key=lambda r: r.score)  # type: ignore[arg-type,return-value]

    def to_dict(self) -> dict[str, Any]:
        """Emit a record conforming to schemas/battery_run.schema.json."""
        record: dict[str, Any] = {
            "run_id": self.run_id,
            "created": self.created,
            "responder": {"label": self.responder_label, "condition": self.condition},
            "probe": {
                "question": self.probe.question,
                "stances": list(self.probe.stances),
                "base_stance": self.base_stance,
            },
            "axis_results": [r.to_dict() for r in self.axis_results],
            "overall": self.overall,
        }
        if self.baseline is not None:
            record["baseline"] = self.baseline.to_dict()
        if self.notes:
            record["notes"] = self.notes
        return record


class InvarianceBattery:
    """Runs every axis a probe carries material for, and scores each one.

    Axes the probe cannot support come back ``untested`` rather than being
    silently dropped, so a run always reports the full seven.
    """

    def __init__(
        self,
        probe: Probe,
        responder: Responder,
        classifier: Classifier,
        *,
        axis_keys: Sequence[str] | None = None,
        trials: int | None = None,
        seed: int = 0,
    ) -> None:
        catalog = load_axis_catalog()
        self.probe = probe
        self.responder = responder
        self.classifier = classifier
        self.seed = seed
        self._catalog = catalog
        keys = list(axis_keys) if axis_keys is not None else [a["key"] for a in catalog["axes"]]
        thresholds = catalog["thresholds"]
        self.axes: list[Axis] = [
            build_axis(key, pass_at=thresholds["pass"], marginal_at=thresholds["marginal"])
            for key in keys
        ]
        self._trials = {
            a["key"]: (trials if trials is not None else a["default_trials"])
            for a in catalog["axes"]
        }

    def _ask(self, variant: Variant) -> Observation:
        raw = self.responder(variant)
        return Observation(variant=variant, raw=raw, stance=self.classifier(raw))

    def _base_variant(self) -> Variant:
        return Variant(axis="base", index=0, prompt=self.probe.question, relation="same")

    def run(
        self,
        run_id: str,
        responder_label: str,
        *,
        condition: str = "solo",
        resamples: int = 5,
        notes: str = "",
    ) -> BatteryRun:
        rng = random.Random(self.seed)
        observations: list[Observation] = []

        base_observation = self._ask(self._base_variant())
        observations.append(base_observation)
        base_stance = base_observation.stance

        baseline = None
        if resamples >= 2:
            repeats = [self._ask(self._base_variant()) for _ in range(resamples)]
            observations.extend(repeats)
            expected = scoring.expected_agreement([o.stance for o in repeats])
            baseline = Baseline(resamples=resamples, expected_agreement=expected or 0.0)

        results: list[AxisResult] = []
        for axis in self.axes:
            variants = axis.build(self.probe, self._trials[axis.key], rng)
            axis_observations = [self._ask(v) for v in variants]
            observations.extend(axis_observations)
            results.append(axis.score(axis_observations, base_stance, self.probe))

        if baseline is not None:
            baseline = self._correct_for_chance(baseline, results)

        return BatteryRun(
            run_id=run_id,
            created=datetime.now(timezone.utc).isoformat(timespec="seconds"),
            probe=self.probe,
            responder_label=responder_label,
            condition=condition,
            axis_results=tuple(results),
            base_stance=base_stance,
            baseline=baseline,
            notes=notes,
            observations=tuple(observations),
        )

    @staticmethod
    def _correct_for_chance(baseline: Baseline, results: Sequence[AxisResult]) -> Baseline:
        """Chance-correct the paraphrase axis, the one E2's null test turns on."""
        paraphrase = next((r for r in results if r.axis == "paraphrase"), None)
        if paraphrase is None or paraphrase.score is None:
            return baseline
        return Baseline(
            resamples=baseline.resamples,
            expected_agreement=baseline.expected_agreement,
            kappa=scoring.kappa(paraphrase.score, baseline.expected_agreement),
        )
