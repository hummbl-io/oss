"""Lattice Advisor — Base120 / Domain120 / BaseN operator recommendation engine.

Recommends Base120 mental models from the 120-model corpus based on:
1. Keyword + definition matching against the query (BM25-style scoring)
2. Past-usage signals extracted from the CLP ledger
3. Domain and difficulty filtering

The advisor is stdlib-only and works offline.  Model definitions are loaded
from ``cognition/data/base120_registry.json`` (generated from the canonical
YAML at PROJECTS/base120/Base120_Canonical_Model_Registry.yaml).

Usage::

    from hummbl_cognition.lattice_advisor import Base120Advisor

    advisor = Base120Advisor()
    for rec in advisor.recommend("I need to find the root cause of a bug"):
        print(rec["id"], rec["name"], rec["score"])

HTTP integration: the Open Brain server (``cognition/server.py``) exposes
this advisor at ``POST /base120/recommend`` and ``GET /base120/transformations``
so that external callers (e.g. the hummbl-api Cloudflare Worker) can query it
over HTTP without importing the Python package.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Domain metadata — keyword sets used for matching
# ---------------------------------------------------------------------------

DOMAIN_KEYWORDS: dict[str, list[str]] = {
    "P": [
        "perspective",
        "viewpoint",
        "frame",
        "lens",
        "stakeholder",
        "narrative",
        "assumption",
        "identity",
        "context",
        "role",
        "empathy",
        "worldview",
    ],
    "IN": [
        "invert",
        "reverse",
        "backwards",
        "opposite",
        "failure",
        "prevent",
        "avoid",
        "premortem",
        "subtraction",
        "constraint",
        "negate",
        "worst case",
    ],
    "CO": [
        "combine",
        "synergy",
        "integrate",
        "collaborate",
        "compose",
        "merge",
        "hybrid",
        "synthesis",
        "coalition",
        "network",
        "complement",
        "bundle",
    ],
    "DE": [
        "decompose",
        "break down",
        "root cause",
        "component",
        "layer",
        "hierarchy",
        "module",
        "diagnose",
        "separate",
        "tree",
        "analysis",
        "why",
        "cause",
    ],
    "RE": [
        "recursion",
        "iterate",
        "improve",
        "refine",
        "feedback",
        "loop",
        "repeat",
        "kaizen",
        "spiral",
        "self-similar",
        "cycle",
        "increment",
        "continuous",
    ],
    "SY": [
        "system",
        "leverage",
        "emergent",
        "dynamics",
        "flow",
        "stock",
        "complex",
        "network",
        "interdependence",
        "holistic",
        "interconnect",
        "feedback loop",
    ],
}

DOMAIN_NAMES: dict[str, str] = {
    "P": "Perspective",
    "IN": "Inversion",
    "CO": "Composition",
    "DE": "Decomposition",
    "RE": "Recursion",
    "SY": "Systems",
}

_REGISTRY_PATH = Path(__file__).parent / "data" / "base120_registry.json"


def _load_registry() -> dict[str, dict[str, Any]]:
    """Load the 120-model registry from the bundled JSON file.

    Returns a dict keyed by model id (e.g. ``"P1"``, ``"SY14"``).
    """
    try:
        with open(_REGISTRY_PATH, encoding="utf-8") as fh:
            models: list[dict[str, Any]] = json.load(fh)
    except (OSError, json.JSONDecodeError):
        # Fallback: generate a minimal registry when the data file is absent
        models = []
        for domain in DOMAIN_NAMES:
            for n in range(1, 21):
                diff = (
                    "beginner"
                    if n <= 7
                    else ("intermediate" if n <= 14 else "advanced")
                )
                models.append(
                    {
                        "id": f"{domain}{n}",
                        "name": f"{DOMAIN_NAMES[domain]} {n}",
                        "domain": domain,
                        "domain_name": DOMAIN_NAMES[domain],
                        "definition": f"{DOMAIN_NAMES[domain]} model {n}",
                        "difficulty": diff,
                    }
                )

    registry: dict[str, dict[str, Any]] = {}
    for m in models:
        mid = m["id"]
        m.setdefault("keywords", DOMAIN_KEYWORDS.get(m.get("domain", ""), []))
        registry[mid] = m
    return registry


# Module-level registry (loaded once)
REGISTRY: dict[str, dict[str, Any]] = _load_registry()


@dataclass
class _ModelScore:
    model_id: str
    score: float
    reasons: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        result = dict(REGISTRY[self.model_id])
        result["score"] = round(self.score, 4)
        result["reasons"] = self.reasons
        return result


# ---------------------------------------------------------------------------
# Advisor
# ---------------------------------------------------------------------------


class Base120Advisor:
    """Recommends Base120 mental models for a given problem context."""

    def __init__(self, *, ledger_path: str | Path | None = None) -> None:
        """
        Args:
            ledger_path: Path to the CLP ledger JSONL file.  When provided,
                         past ledger entries that reference Base120 model ids
                         boost those models in future recommendations.
        """
        self.ledger_path: Path | None = Path(ledger_path) if ledger_path else None
        self._ledger_signals: dict[str, float] = {}
        self._signals_loaded = False

    # ------------------------------------------------------------------
    # Ledger signal extraction
    # ------------------------------------------------------------------

    def _load_ledger_signals(self) -> None:
        """Scan the CLP ledger for past Base120 usage signals (idempotent)."""
        if self._signals_loaded:
            return
        self._signals_loaded = True

        path = self.ledger_path
        if path is None:
            # Try the default path relative to cwd
            path = Path("_state/cognition/ledger.jsonl")
        if not path or not path.exists():
            return

        # Pattern: match model ids like P1, SY14, CO20, etc.
        id_pattern = re.compile(r"\b(P|IN|CO|DE|RE|SY)(\d{1,2})\b")
        signals: dict[str, float] = {}

        try:
            with open(path, encoding="utf-8") as fh:
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        entry = json.loads(line)
                    except json.JSONDecodeError:
                        continue

                    content = entry.get("content", "")
                    tags: list[str] = entry.get("tags", [])
                    entry_type: str = entry.get("type", "")

                    # Higher weight for decisions and insights
                    weight = 1.5 if entry_type in ("decision", "insight") else 1.0

                    # Tags explicitly naming a model id (highest signal)
                    for tag in tags:
                        upper_tag = tag.upper()
                        if upper_tag in REGISTRY:
                            signals[upper_tag] = (
                                signals.get(upper_tag, 0.0) + weight * 2.5
                            )

                    # Model ids mentioned in content
                    for match in id_pattern.finditer(content.upper()):
                        mid = match.group(0)
                        if mid in REGISTRY:
                            signals[mid] = signals.get(mid, 0.0) + weight

        except OSError:
            pass

        self._ledger_signals = signals

    # ------------------------------------------------------------------
    # Scoring
    # ------------------------------------------------------------------

    def _keyword_score(self, query_lower: str, model_id: str) -> float:
        """BM25-inspired keyword match: model keywords ∩ query tokens."""
        model = REGISTRY[model_id]
        domain = model.get("domain", "")
        keywords = model.get("keywords") or DOMAIN_KEYWORDS.get(domain, [])
        definition = model.get("definition", "").lower()
        name = model.get("name", "").lower()
        score = 0.0

        for kw in keywords:
            if kw in query_lower:
                score += 1.0
            elif any(w in kw or kw in w for w in query_lower.split() if len(w) > 3):
                score += 0.25

        # Definition match
        query_words = set(w for w in re.split(r"\W+", query_lower) if len(w) > 3)
        def_words = set(re.split(r"\W+", definition))
        overlap = query_words & def_words
        score += len(overlap) * 0.4

        # Name exact match
        if name in query_lower:
            score += 2.0

        # Domain name match
        domain_name = model.get("domain_name", "").lower()
        if domain_name and domain_name in query_lower:
            score += 1.5

        # Direct model id in query (e.g. user typed "SY1")
        if model_id.lower() in query_lower.replace(" ", ""):
            score += 4.0

        return score

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def recommend(
        self,
        query: str,
        *,
        agent_id: str | None = None,
        limit: int = 5,
        difficulty: str | None = None,
        domain: str | None = None,
    ) -> list[dict[str, Any]]:
        """Return ranked Base120 model recommendations.

        Args:
            query: Natural language description of the problem or context.
            agent_id: Agent requesting recommendations (reserved for future
                      per-agent personalization from the ledger).
            limit: Maximum number of results to return (1-20).
            difficulty: Optional filter: ``"beginner"``, ``"intermediate"``,
                        or ``"advanced"``.
            domain: Optional filter by domain code, e.g. ``"SY"`` or ``"DE"``.

        Returns:
            List of model dicts with added ``"score"`` and ``"reasons"`` keys,
            sorted descending by score.
        """
        self._load_ledger_signals()
        limit = max(1, min(limit, 20))
        query_lower = query.lower()
        domain_upper = domain.upper() if domain else None

        scored: list[_ModelScore] = []

        for mid, model in REGISTRY.items():
            # Apply filters
            if difficulty and model.get("difficulty") != difficulty:
                continue
            if domain_upper and model.get("domain") != domain_upper:
                continue

            kw = self._keyword_score(query_lower, mid)
            ledger = self._ledger_signals.get(mid, 0.0) * 0.6
            total = kw + ledger

            reasons: list[str] = []
            if kw > 0:
                reasons.append(f"keyword({kw:.1f})")
            if ledger > 0:
                reasons.append(f"ledger({ledger:.1f})")

            if total > 0:
                scored.append(_ModelScore(model_id=mid, score=total, reasons=reasons))

        # When nothing matches, return the first model per domain (broad coverage)
        if not scored:
            for dom in DOMAIN_NAMES:
                if domain_upper and dom != domain_upper:
                    continue
                first_id = next(
                    (mid for mid in REGISTRY if REGISTRY[mid]["domain"] == dom), None
                )
                if first_id:
                    scored.append(
                        _ModelScore(model_id=first_id, score=0.1, reasons=["default"])
                    )

        scored.sort(key=lambda s: (-s.score, s.model_id))
        return [s.to_dict() for s in scored[:limit]]

    def explain(self, model_id: str) -> dict[str, Any] | None:
        """Return full metadata for a model, with ledger usage appended.

        Returns ``None`` if the model id is unknown.
        """
        mid = model_id.upper()
        if mid not in REGISTRY:
            return None
        self._load_ledger_signals()
        result = dict(REGISTRY[mid])
        result["ledger_usage"] = round(self._ledger_signals.get(mid, 0.0), 4)
        return result

    def list_domains(self) -> list[dict[str, Any]]:
        """Return metadata for the 6 Base120 transformation domains."""
        return [
            {
                "code": code,
                "name": DOMAIN_NAMES[code],
                "model_count": sum(1 for m in REGISTRY.values() if m["domain"] == code),
                "keywords": DOMAIN_KEYWORDS.get(code, []),
            }
            for code in DOMAIN_NAMES
        ]
