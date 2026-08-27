"""Structured critique parsing for Sigil Forge."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class CritiqueResult:
    score: float
    issues: tuple[str, ...] = ()
    contradictions: tuple[str, ...] = ()
    missing_evidence: tuple[str, ...] = ()
    recommendation: str = "review"
    raw: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "contradictions": list(self.contradictions),
            "issues": list(self.issues),
            "missing_evidence": list(self.missing_evidence),
            "raw": self.raw,
            "recommendation": self.recommendation,
            "score": self.score,
        }


@dataclass(frozen=True)
class CritiqueConfig:
    default_score: float = 0.5
    issue_penalty: float = 0.1
    contradiction_penalty: float = 0.2
    missing_evidence_penalty: float = 0.1
    minimum_score: float = 0.0


def parse_critique(
    text: str, *, config: CritiqueConfig | None = None
) -> CritiqueResult:
    cfg = config or CritiqueConfig()
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        score = _coerce_score(text, default=cfg.default_score)
        return CritiqueResult(score=score, raw=text)

    if isinstance(data, int | float):
        return CritiqueResult(
            score=_clamp_score(float(data), default=cfg.default_score), raw=text
        )
    if not isinstance(data, dict):
        return CritiqueResult(score=cfg.default_score, raw=text)

    issues = _tuple_of_strings(data.get("issues", ()))
    contradictions = _tuple_of_strings(data.get("contradictions", ()))
    missing = _tuple_of_strings(data.get("missing_evidence", ()))
    score_value = data.get("score")
    if score_value is None:
        score = max(
            cfg.minimum_score,
            1.0
            - (len(issues) * cfg.issue_penalty)
            - (len(contradictions) * cfg.contradiction_penalty)
            - (len(missing) * cfg.missing_evidence_penalty),
        )
    else:
        score = _coerce_score(str(score_value), default=cfg.default_score)
    return CritiqueResult(
        score=score,
        issues=issues,
        contradictions=contradictions,
        missing_evidence=missing,
        recommendation=str(data.get("recommendation", "review")),
        raw=text,
    )


def _tuple_of_strings(value: object) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        return (value,)
    if isinstance(value, list | tuple):
        return tuple(str(item) for item in value)
    return (str(value),)


def _coerce_score(text: str, *, default: float) -> float:
    for token in text.replace(",", " ").split():
        try:
            value = float(token)
        except ValueError:
            continue
        if 0.0 <= value <= 1.0:
            return value
    return default


def _clamp_score(value: float, *, default: float) -> float:
    if 0.0 <= value <= 1.0:
        return value
    return default
