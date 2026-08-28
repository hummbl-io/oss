"""All-source intelligence fusion methodology.

Implements structured fusion of multi-INT findings into graded
intelligence products. Supports:

1. Competing hypotheses analysis
2. Estimative probability language (Words of Estimative Probability)
3. Explicit source attribution per conclusion
4. Confidence scoring with uncertainty tracking

These methods harden the morning briefing from an aggregator
into an intelligence product with audit-trail provenance.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from hummbl_intel.grading import ContentCredibility, GradedAssertion, SourceGrade
from hummbl_intel.taxonomy import IntelligenceDiscipline


class EstimativeProbability(Enum):
    """Words of Estimative Probability (WEP) — standard for IC analytic products.

    Maps qualitative statements to quantitative probability ranges.
    Source: ODNI Intelligence Community Directive 203.
    """

    ALMOST_CERTAIN = "almost_certain"
    """93-99% probability. Overwhelming evidence."""

    HIGHLY_LIKELY = "highly_likely"
    """75-92% probability. Strong evidence, minor gaps."""

    LIKELY = "likely"
    """55-74% probability. Credible evidence, some gaps."""

    EVEN_CHANCE = "even_chance"
    """45-55% probability. Competing evidence, no dominant signal."""

    UNLIKELY = "unlikely"
    """20-44% probability. Some evidence against, gaps in favor."""

    HIGHLY_UNLIKELY = "highly_unlikely"
    """5-19% probability. Strong evidence against."""

    ALMOST_IMPOSSIBLE = "almost_impossible"
    """1-4% probability. Overwhelming evidence against."""


WEP_RANGES: dict[EstimativeProbability, tuple[float, float]] = {
    EstimativeProbability.ALMOST_CERTAIN: (0.93, 0.99),
    EstimativeProbability.HIGHLY_LIKELY: (0.75, 0.92),
    EstimativeProbability.LIKELY: (0.55, 0.74),
    EstimativeProbability.EVEN_CHANCE: (0.45, 0.55),
    EstimativeProbability.UNLIKELY: (0.20, 0.44),
    EstimativeProbability.HIGHLY_UNLIKELY: (0.05, 0.19),
    EstimativeProbability.ALMOST_IMPOSSIBLE: (0.01, 0.04),
}


@dataclass(frozen=True)
class Hypothesis:
    """A single hypothesis in a competing-hypotheses analysis.

    Each hypothesis is evaluated against the evidence set to
    produce a likelihood score.
    """

    id: str
    """Short identifier (e.g., 'H1', 'H2')."""

    statement: str
    """The hypothesis statement (falsifiable claim)."""

    evidence_for: list[GradedAssertion] = field(default_factory=list)
    """Assertions that SUPPORT this hypothesis."""

    evidence_against: list[GradedAssertion] = field(default_factory=list)
    """Assertions that CONTRADICT this hypothesis."""

    def support_count(self) -> int:
        """Number of corroborated assertions supporting this hypothesis."""
        return sum(
            1 for a in self.evidence_for if a.grade.is_actionable()
        )

    def contradiction_count(self) -> int:
        """Number of actionable assertions contradicting this hypothesis."""
        return sum(
            1 for a in self.evidence_against if a.grade.is_actionable()
        )

    def likelihood(self) -> EstimativeProbability:
        """Compute likelihood from evidence balance.

        Simple heuristic:
        - 3+ actionable supporting, 0 contradicting → ALMOST_CERTAIN
        - 2 supporting, 0 contradicting → HIGHLY_LIKELY
        - More supporting than contradicting → LIKELY
        - Equal supporting and contradicting → EVEN_CHANCE
        - More contradicting than supporting → UNLIKELY
        - 0 supporting, 2+ contradicting → HIGHLY_UNLIKELY
        - No evidence either way → EVEN_CHANCE (neutral default)
        """
        sup = self.support_count()
        con = self.contradiction_count()

        if sup == 0 and con == 0:
            return EstimativeProbability.EVEN_CHANCE
        if sup >= 3 and con == 0:
            return EstimativeProbability.ALMOST_CERTAIN
        if sup >= 2 and con == 0:
            return EstimativeProbability.HIGHLY_LIKELY
        if sup > con:
            return EstimativeProbability.LIKELY
        if sup == con:
            return EstimativeProbability.EVEN_CHANCE
        if con >= 2 and sup == 0:
            return EstimativeProbability.HIGHLY_UNLIKELY
        return EstimativeProbability.UNLIKELY


@dataclass
class CompetingHypothesesAnalysis:
    """Analysis of competing hypotheses (ACH) for a single question.

    Structured method for evaluating multiple hypotheses against
    common evidence. Produces a ranked list of hypotheses by likelihood.
    """

    question: str
    """The analytical question being assessed."""

    hypotheses: list[Hypothesis] = field(default_factory=list)
    """All competing hypotheses."""

    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def ranked(self) -> list[Hypothesis]:
        """Return hypotheses ranked by likelihood (most likely first)."""
        likelihood_order = list(EstimativeProbability)
        return sorted(
            self.hypotheses,
            key=lambda h: likelihood_order.index(h.likelihood())
            if h.likelihood() in likelihood_order else 999,
        )

    def most_likely(self) -> Hypothesis | None:
        """Return the most likely hypothesis, or None if no hypotheses."""
        ranked = self.ranked()
        return ranked[0] if ranked else None

    def to_dict(self) -> dict[str, Any]:
        return {
            "question": self.question,
            "hypotheses": [
                {
                    "id": h.id,
                    "statement": h.statement,
                    "likelihood": h.likelihood().value,
                    "supporting_count": h.support_count(),
                    "contradicting_count": h.contradiction_count(),
                }
                for h in self.ranked()
            ],
            "timestamp": self.timestamp,
        }


@dataclass
class FusedFinding:
    """A single conclusion in an all-source product.

    Each finding carries:
    - The conclusion text
    - A probability estimate
    - Source attributions (which INTs contributed)
    - Underlying graded assertions
    - Residual uncertainty notes
    """

    conclusion: str
    """The fused conclusion statement."""

    probability: EstimativeProbability
    """Words of Estimative Probability for this conclusion."""

    sources: list[IntelligenceDiscipline] = field(default_factory=list)
    """INT disciplines that contributed to this conclusion."""

    assertions: list[GradedAssertion] = field(default_factory=list)
    """Underlying evidence supporting this conclusion."""

    confidence: float = 0.5
    """Aggregate confidence score: 0.0 to 1.0."""

    uncertainty_notes: str = ""
    """Residual uncertainty: what we don't know, assumptions, gaps."""

    def source_list(self) -> str:
        """Comma-separated source INT list for attribution."""
        from hummbl_intel.taxonomy import INT_LABELS

        return ", ".join(
            INT_LABELS.get(s, s.value) for s in self.sources
        )

    def to_attribution_line(self) -> str:
        """Produce a source-attributed conclusion line.

        Example: "(OSINT, SIGINT) The bus bridge is operational. [LIKELY]"
        """
        ints = "/".join(s.name for s in self.sources) if self.sources else "ALL-SOURCE"
        return f"({ints}) {self.conclusion} [{self.probability.name}]"


@dataclass
class AllSourceProduct:
    """A complete all-source intelligence product.

    This is the output of the fusion methodology — a structured
    report that combines multi-INT findings into graded conclusions.
    """

    title: str
    """Product title (e.g., 'Morning Briefing 2026-05-09')."""

    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    findings: list[FusedFinding] = field(default_factory=list)
    """Fused conclusions with source attribution."""

    ach_analyses: dict[str, CompetingHypothesesAnalysis] = field(
        default_factory=dict
    )
    """Key analytical questions assessed via ACH."""

    collection_posture: Any = None
    """Posture report from posture.py (optional cross-reference)."""

    def key_judgments(self) -> list[FusedFinding]:
        """Return findings sorted by confidence (highest first)."""
        return sorted(
            self.findings,
            key=lambda f: f.confidence,
            reverse=True,
        )

    def source_coverage(self) -> dict[str, int]:
        """Count how many findings draw on each INT discipline."""
        from collections import Counter

        counter: Counter[str] = Counter()
        for finding in self.findings:
            for source in finding.sources:
                counter[source.name] += 1
        return dict(counter.most_common())

    def to_summary(self) -> str:
        """Produce a human-readable summary of the product."""
        lines = [
            f"ALL-SOURCE PRODUCT: {self.title}",
            f"Generated: {self.timestamp}",
            f"Findings: {len(self.findings)}",
            "",
        ]

        if self.findings:
            lines.append("KEY JUDGMENTS:")
            for i, finding in enumerate(self.key_judgments(), 1):
                lines.append(
                    f"  {i}. {finding.to_attribution_line()}"
                )
                if finding.uncertainty_notes:
                    lines.append(f"     Caveat: {finding.uncertainty_notes}")

        if self.ach_analyses:
            lines.append("")
            lines.append("COMPETING HYPOTHESES:")
            for q_id, ach in self.ach_analyses.items():
                most_likely = ach.most_likely()
                if most_likely:
                    lines.append(
                        f"  {q_id}: {most_likely.statement} "
                        f"[{most_likely.likelihood().name}]"
                    )

        if self.collection_posture is not None:
            lines.append("")
            lines.append("COLLECTION POSTURE:")
            if hasattr(self.collection_posture, "to_summary_lines"):
                lines.extend(self.collection_posture.to_summary_lines())

        return "\n".join(lines)


def fuse_into_finding(
    conclusion: str,
    assertions: list[GradedAssertion],
    uncertainty: str = "",
) -> FusedFinding:
    """Fuse multiple graded assertions into a single fused finding.

    Computes aggregate probability and confidence from the
    underlying evidence.

    Args:
        conclusion: The fused conclusion text.
        assertions: Graded assertions supporting this conclusion.
        uncertainty: Residual uncertainty notes.

    Returns:
        A FusedFinding with computed probability and confidence.
    """
    if not assertions:
        return FusedFinding(
            conclusion=conclusion,
            probability=EstimativeProbability.EVEN_CHANCE,
            confidence=0.0,
            uncertainty_notes="No supporting evidence." + (
                f" {uncertainty}" if uncertainty else ""
            ),
        )

    # Extract INTs from assertions
    sources: list[IntelligenceDiscipline] = []
    seen = set()
    for a in assertions:
        if a.discipline:
            try:
                disc = IntelligenceDiscipline(a.discipline)
                if disc not in seen:
                    sources.append(disc)
                    seen.add(disc)
            except ValueError:
                pass

    # Compute probability from actionable assertions
    actionable = [a for a in assertions if a.grade.is_actionable()]
    corroborated = sum(1 for a in actionable if a.corroboration_count >= 2)

    if len(actionable) >= 3 and corroborated >= 2:
        probability = EstimativeProbability.ALMOST_CERTAIN
        confidence = 0.95
    elif len(actionable) >= 2 and corroborated >= 1:
        probability = EstimativeProbability.HIGHLY_LIKELY
        confidence = 0.85
    elif len(actionable) >= 1:
        probability = EstimativeProbability.LIKELY
        confidence = 0.65
    else:
        probability = EstimativeProbability.EVEN_CHANCE
        confidence = 0.50

    # Degrade confidence if any assertions contradict
    contradictions = [
        a for a in assertions
        if a.grade.is_actionable()
        and a.content.lower().startswith(("not ", "no ", "never", "contradicts"))
    ]
    if contradictions:
        confidence = max(0.10, confidence - 0.25)

    return FusedFinding(
        conclusion=conclusion,
        probability=probability,
        sources=sources,
        assertions=assertions,
        confidence=confidence,
        uncertainty_notes=uncertainty,
    )
