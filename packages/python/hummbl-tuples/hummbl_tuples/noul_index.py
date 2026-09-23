"""NoulIndex: Content-addressed index & calibration tracker for NoulTuples.

Provides:
1. O(1) memoization & evaluation caching: (state_hash, proposition) -> NoulTuple.
2. Contradiction & collision detection: flags conflicting decisions on identical states.
3. Calibration analysis: computes live Expected Calibration Error (ECE) and Brier scores.
4. Probabilistic query filtering (e.g. all alarms, all abstentions).
"""
from __future__ import annotations

import math
from collections import defaultdict
from typing import Dict, Iterator, List, Optional, Tuple

from .noul import NoulTuple


class NoulIndex:
    """In-memory content-addressed index for Noul decision tuples."""

    def __init__(self):
        # Primary content-addressed index: (state_hash, proposition) -> list of NoulTuples
        self._by_state_prop: Dict[Tuple[str, str], List[NoulTuple]] = defaultdict(list)
        # Inverted index by proposition
        self._by_proposition: Dict[str, List[NoulTuple]] = defaultdict(list)
        # Inverted index by domain
        self._by_domain: Dict[str, List[NoulTuple]] = defaultdict(list)
        # All tuples in arrival order
        self._all: List[NoulTuple] = []

    def record(self, noul: NoulTuple) -> None:
        """Insert a NoulTuple into the index."""
        key = (noul.state_hash, noul.proposition)
        self._by_state_prop[key].append(noul)
        self._by_proposition[noul.proposition].append(noul)
        self._by_domain[noul.domain].append(noul)
        self._all.append(noul)

    def lookup(self, state_hash: str, proposition: str) -> Optional[NoulTuple]:
        """Return the most recent cached NoulTuple for the state and proposition, or None."""
        entries = self._by_state_prop.get((state_hash, proposition))
        if entries:
            return entries[-1]
        return None

    def detect_contradictions(self, state_hash: str, proposition: str) -> List[Tuple[NoulTuple, NoulTuple]]:
        """Detect if multiple evaluations for the same state and proposition diverged."""
        entries = self._by_state_prop.get((state_hash, proposition), [])
        contradictions = []
        for i in range(len(entries)):
            for j in range(i + 1, len(entries)):
                t1, t2 = entries[i], entries[j]
                if t1.decision != t2.decision or abs(t1.p_true - t2.p_true) > 0.35:
                    contradictions.append((t1, t2))
        return contradictions

    def query_alarms(self, domain: Optional[str] = None) -> List[NoulTuple]:
        """Return all nouls where is_alarm is True."""
        source = self._by_domain[domain] if domain else self._all
        return [n for n in source if n.is_alarm]

    def query_abstentions(self, lower: float = 0.35, upper: float = 0.65) -> List[NoulTuple]:
        """Return all nouls whose probability falls within the ambiguous abstention band."""
        return [n for n in self._all if n.in_abstention_band(lower, upper)]

    def calibration_stats(self, proposition: Optional[str] = None, n_bins: int = 10) -> Dict[str, float]:
        """Compute calibration metrics: Brier score, ECE (Expected Calibration Error).

        Only evaluates entries where `ground_truth` is not None.
        """
        source = self._by_proposition[proposition] if proposition else self._all
        evaluated = [n for n in source if n.ground_truth is not None]
        if not evaluated:
            return {"count": 0, "brier_score": 0.0, "ece": 0.0}

        # 1. Mean Brier score
        brier_sum = sum(n.brier_score() for n in evaluated if n.brier_score() is not None)
        mean_brier = brier_sum / len(evaluated)

        # 2. Expected Calibration Error (ECE)
        bins: Dict[int, List[NoulTuple]] = defaultdict(list)
        for n in evaluated:
            b_idx = min(int(n.p_true * n_bins), n_bins - 1)
            bins[b_idx].append(n)

        ece = 0.0
        n_total = len(evaluated)
        for b_idx, b_items in bins.items():
            if not b_items:
                continue
            mean_pred = sum(item.p_true for item in b_items) / len(b_items)
            mean_actual = sum(1.0 if item.ground_truth else 0.0 for item in b_items) / len(b_items)
            weight = len(b_items) / n_total
            ece += weight * abs(mean_pred - mean_actual)

        return {
            "count": len(evaluated),
            "brier_score": round(mean_brier, 4),
            "ece": round(ece, 4),
        }

    def __len__(self) -> int:
        return len(self._all)

    def __iter__(self) -> Iterator[NoulTuple]:
        return iter(self._all)
