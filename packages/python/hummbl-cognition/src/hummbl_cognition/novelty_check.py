"""Novelty check -- nearest-neighbor evidence for novelty claims.

A novelty claim is a negative existential ("nothing like this exists") and
cannot be proven absolutely -- only bounded: "novel within corpus C under
metric M at distance D as of time T". This module checks the *internal*
corpus (the Open Brain memory pools) and returns the nearest-neighbor
evidence: the entries closest to the claim, which claim terms each neighbor
shares, and which claim terms the ledger index has never seen at all.

Design rules (self-imposed):

- The neighbor list IS the evidence. A bare score is not a verdict; report
  the actual nearest entries so a reviewer can judge whether lexical
  proximity is conceptual proximity.
- BM25 scores measure lexical overlap, not conceptual distance. A
  lexically-close neighbor can be conceptually far (e.g., a shared generic
  term like "escalation"), and a lexically-distant neighbor can be a real
  duplicate in different words.
- External scopes (academic literature, market prior art) are out of scope
  for this module; a report grades itself "internal" only, and says so.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from hummbl_cognition.indexer import tokenize
from hummbl_cognition.retriever import MemoryResult, OpenBrainRetriever

SCHEMA_VERSION = "novelty-check.v0.1"
METRIC = "bm25-topk"
CORPUS_SCOPE = ("internal",)

_DEFAULT_SNIPPET_CHARS = 200

_CAVEATS_BASE: tuple[str, ...] = (
    "bm25-topk scores measure lexical overlap, not conceptual distance -- "
    "judge proximity from neighbor content, not the score alone.",
    "corpus_scope=internal only; academic-literature and market prior art "
    "are unchecked -- a standing novelty claim needs external adversarial "
    "search before external use.",
    "unseen_terms reflects the ledger index vocabulary only; terms absent "
    "from the index may still exist in unindexed artifacts.",
    "receipts decay: recheck before external reliance and after the "
    "underlying corpus changes materially.",
)

_CAVEAT_NO_NEIGHBORS = (
    "zero neighbors returned -- this means no indexed near-neighbors, which "
    "is weak evidence; it can also mean the index is empty, stale, or the "
    "claim is lexically disjoint."
)

_CAVEAT_MASKED = (
    "entries were masked from retrieval for this check -- distances reflect "
    "the corpus MINUS the masked ids (blind rediscovery context), not the "
    "full corpus."
)


class NoveltyNeighbor:
    """A single nearest-neighbor hit with the claim terms it shares."""

    __slots__ = ("source", "entry_id", "score", "timestamp", "content", "matched_terms")

    def __init__(
        self,
        *,
        source: str,
        entry_id: str,
        score: float,
        timestamp: str,
        content: str,
        matched_terms: list[str],
    ) -> None:
        self.source = source
        self.entry_id = entry_id
        self.score = score
        self.timestamp = timestamp
        self.content = content
        self.matched_terms = matched_terms

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "entry_id": self.entry_id,
            "score": round(self.score, 4),
            "timestamp": self.timestamp,
            "matched_terms": self.matched_terms,
            "content": self.content,
        }


class NoveltyReport:
    """Bounded novelty evidence for one claim against the internal corpus."""

    __slots__ = (
        "claim",
        "sources",
        "checked_at",
        "top_score",
        "nearest_neighbors",
        "unseen_terms",
        "masked_ids",
        "caveats",
    )

    def __init__(
        self,
        *,
        claim: str,
        sources: tuple[str, ...],
        checked_at: str,
        top_score: float | None,
        nearest_neighbors: tuple[NoveltyNeighbor, ...],
        unseen_terms: tuple[str, ...],
        caveats: tuple[str, ...],
        masked_ids: tuple[str, ...] = (),
    ) -> None:
        self.claim = claim
        self.sources = sources
        self.checked_at = checked_at
        self.top_score = top_score
        self.nearest_neighbors = nearest_neighbors
        self.unseen_terms = unseen_terms
        self.caveats = caveats
        self.masked_ids = masked_ids

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": SCHEMA_VERSION,
            "claim": self.claim,
            "corpus_scope": list(CORPUS_SCOPE),
            "metric": METRIC,
            "sources": list(self.sources),
            "checked_at": self.checked_at,
            "top_score": None if self.top_score is None else round(self.top_score, 4),
            "nearest_neighbors": [n.to_dict() for n in self.nearest_neighbors],
            "unseen_terms": list(self.unseen_terms),
            "masked_ids": list(self.masked_ids),
            "caveats": list(self.caveats),
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)


def _matched_terms(claim_tokens: set[str], neighbor_content: str) -> list[str]:
    """Claim terms present in the neighbor's content.

    Surfaces lexicon collisions directly: a neighbor that matches only on a
    generic shared term is visibly different from one matching the claim's
    distinctive terms.
    """
    return sorted(claim_tokens & set(tokenize(neighbor_content)))


def novelty_check(
    claim: str,
    *,
    state_dir: str | None = None,
    retriever: OpenBrainRetriever | None = None,
    limit: int = 5,
    sources: list[str] | None = None,
    agent: str = "novelty-check",
    exclude_ids: set[str] | None = None,
) -> NoveltyReport:
    """Measure a claim's nearest neighbors in the internal corpus.

    Parameters
    ----------
    claim : str
        The claim text to check for internal novelty.
    state_dir : str | None
        Override Open Brain state dir resolution (contains cognition/ subdir).
    retriever : OpenBrainRetriever | None
        Inject a retriever (e.g., pre-loaded or a test double). If omitted,
        one is constructed over state_dir and its index ensured.
    limit : int
        Max nearest neighbors to report.
    sources : list[str] | None
        Memory pools to search ("ledger", "bus", "briefings", "findings",
        "memory_md"). None = all pools.
    agent : str
        Agent identifier for retrieval feedback tracking.
    exclude_ids : set[str] | None
        Ledger entry ids masked from results (blind rediscovery evaluation).

    Returns
    -------
    NoveltyReport
        Neighbor evidence + unseen_terms + caveats. Never a bare verdict.
    """
    if retriever is None:
        retriever = OpenBrainRetriever(state_dir=state_dir)
    retriever.ensure_index()

    results: list[MemoryResult] = retriever.search(
        claim,
        token_budget=8000,
        sources=sources,
        agent=agent,
        limit=limit,
        exclude_ids=exclude_ids,
    )

    claim_tokens = set(tokenize(claim))

    neighbors = tuple(
        NoveltyNeighbor(
            source=r.source,
            entry_id=r.entry_id,
            score=r.score,
            timestamp=str(r.metadata.get("timestamp", "")),
            content=r.content[:_DEFAULT_SNIPPET_CHARS],
            matched_terms=_matched_terms(claim_tokens, r.content),
        )
        for r in results
    )

    # Terms the ledger index has literally never indexed -- the strongest
    # vocabulary-level novelty signal available internally.
    unseen = tuple(
        sorted(t for t in claim_tokens if t not in retriever.index.inverted_index)
    )

    caveats: list[str] = list(_CAVEATS_BASE)
    if not results:
        caveats.insert(0, _CAVEAT_NO_NEIGHBORS)
    if exclude_ids:
        caveats.insert(0, _CAVEAT_MASKED)

    return NoveltyReport(
        claim=claim,
        sources=tuple(sources) if sources else (
            "ledger", "bus", "briefings", "findings", "memory_md",
        ),
        checked_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        top_score=results[0].score if results else None,
        nearest_neighbors=neighbors,
        unseen_terms=unseen,
        caveats=tuple(caveats),
        masked_ids=tuple(sorted(exclude_ids)) if exclude_ids else (),
    )


def format_report_text(report: NoveltyReport) -> str:
    """Human-readable rendering for CLI output."""
    lines: list[str] = []
    lines.append(
        f"Novelty check | corpus_scope=internal | metric={METRIC} "
        f"| checked_at={report.checked_at}"
    )
    lines.append(f"Claim: {report.claim}")
    lines.append("")

    if report.top_score is None:
        lines.append("No near-neighbors returned.")
    else:
        lines.append(
            f"Top neighbor score: {report.top_score:.3f} "
            f"({len(report.nearest_neighbors)} neighbors)"
        )
    if report.unseen_terms:
        lines.append(
            "Unseen terms (absent from ledger index): "
            + ", ".join(report.unseen_terms)
        )
    lines.append("")

    if report.nearest_neighbors:
        lines.append("Nearest neighbors:")
        for i, n in enumerate(report.nearest_neighbors, 1):
            ts = f" {n.timestamp[:10]}" if n.timestamp else ""
            lines.append(f"  {i}. [{n.source}] {n.score:.3f} {n.entry_id}{ts}")
            if n.matched_terms:
                lines.append(f"     matched_terms: {', '.join(n.matched_terms)}")
            snippet = n.content.replace("\n", " ")[:160]
            if snippet:
                lines.append(f"     {snippet}")
        lines.append("")

    lines.append("Caveats:")
    for c in report.caveats:
        lines.append(f"  - {c}")
    return "\n".join(lines)
