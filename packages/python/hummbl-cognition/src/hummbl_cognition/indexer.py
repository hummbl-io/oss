"""Open Brain Indexer -- BM25 inverted term index over the cognitive ledger.

Builds a searchable index from ledger.jsonl using stdlib-only BM25 scoring.
The index is a derived artifact -- always rebuildable from the source ledger.

Storage: _state/cognition/index.json
"""

from __future__ import annotations

import contextlib
import json
import logging
import math
import os
import re
import tempfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from hummbl_cognition.ledger_writer import DEFAULT_COGNITION_DIR, read_entries

logger = logging.getLogger(__name__)

DEFAULT_INDEX_PATH = DEFAULT_COGNITION_DIR / "index.json"

# BM25 tuning parameters
BM25_K1 = 1.5
BM25_B = 0.75

# Time-decay parameters (Tier 1: inverted-retrieval fix)
# Entries older than the half-life get scored lower via exponential decay.
# Configurable via env vars; defaults chosen to not aggressively penalize
# durable knowledge — 90 days for content age, 30 days for retrieval freshness
# (matching the peer_review.py Beta-decay half-life at services/peer_review.py:252).
TIME_DECAY_HALF_LIFE_DAYS = float(
    os.environ.get("COGNITION_TIME_DECAY_HALF_LIFE_DAYS", "90")
)
RETRIEVAL_DECAY_HALF_LIFE_DAYS = float(
    os.environ.get("COGNITION_RETRIEVAL_DECAY_HALF_LIFE_DAYS", "30")
)

# Stopwords for English (minimal set -- keeps index small without a dep)
_STOPWORDS = frozenset({
    "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "is", "it", "be", "as", "was", "were",
    "are", "been", "being", "have", "has", "had", "do", "does", "did",
    "will", "would", "could", "should", "may", "might", "can", "this",
    "that", "these", "those", "not", "no", "so", "if", "then", "than",
    "too", "very", "just", "about", "also", "into", "over", "after",
})

_TOKEN_RE = re.compile(r"[a-z0-9_]+(?:\.[a-z0-9_]+)*")


def tokenize(text: str) -> list[str]:
    """Tokenize text into lowercase terms, filtering stopwords."""
    tokens = _TOKEN_RE.findall(text.lower())
    return [t for t in tokens if t not in _STOPWORDS and len(t) > 1]


def _resolve_index_path(override: str | Path | None = None) -> Path:
    """Resolve the index file path.

    Priority: explicit override > COGNITION_INDEX env > package-relative default.

    Note: we deliberately do NOT use ``git rev-parse --show-toplevel`` because
    the ``.git`` directory may live at the workspace root (e.g. when the repo
    is a subdirectory of a larger workspace), which would resolve to the wrong
    directory. Instead we resolve relative to this file's location, which is
    robust against CWD drift and workspace nesting.
    """
    if override:
        return Path(override)
    env_path = os.environ.get("COGNITION_INDEX")
    if env_path:
        return Path(env_path)
    return DEFAULT_INDEX_PATH


class BM25Index:
    """BM25 inverted term index over ledger entries.

    The index stores:
      - inverted_index: term -> list of (entry_id, term_frequency)
      - doc_lengths: entry_id -> number of tokens
      - doc_meta: entry_id -> {timestamp, agent, type, scope, confidence, content_preview}
      - stats: {total_docs, avg_doc_length, built_at, entry_count}
      - retrieval_counts: entry_id -> number of times retrieved (stigmergic ranking)
    """

    def __init__(self, index_path: str | Path | None = None) -> None:
        self.index_path = _resolve_index_path(index_path)
        self.inverted_index: dict[str, list[tuple[str, int]]] = {}
        self.doc_lengths: dict[str, int] = {}
        self.doc_meta: dict[str, dict[str, Any]] = {}
        self.retrieval_counts: dict[str, int] = {}
        self.retrieval_last_at: dict[str, str] = {}
        self.total_docs: int = 0
        self.avg_doc_length: float = 0.0
        self.built_at: str = ""
        self.entry_count: int = 0

    def build(self, ledger_path: str | Path | None = None) -> int:
        """Build index from ledger entries. Returns count of indexed entries."""
        entries = read_entries(ledger_path=ledger_path, limit=999_999)

        self.inverted_index.clear()
        self.doc_lengths.clear()
        self.doc_meta.clear()
        self.total_docs = len(entries)
        self.entry_count = len(entries)

        if not entries:
            self.avg_doc_length = 0.0
            self.built_at = datetime.now(timezone.utc).strftime(
                "%Y-%m-%dT%H:%M:%SZ"
            )
            return 0

        total_length = 0

        for entry in entries:
            # Build searchable text from all relevant fields
            text_parts = [
                entry.content,
                entry.type,
                entry.scope,
                entry.agent,
                " ".join(entry.tags),
            ]
            text = " ".join(text_parts)
            tokens = tokenize(text)
            doc_len = len(tokens)
            total_length += doc_len

            self.doc_lengths[entry.id] = doc_len

            # Store metadata for retrieval
            self.doc_meta[entry.id] = {
                "timestamp": entry.timestamp,
                "agent": entry.agent,
                "type": entry.type,
                "scope": entry.scope,
                "confidence": entry.confidence,
                "content_preview": entry.content[:200],
                "tags": list(entry.tags),
                "links": list(entry.links),
                "supersedes": entry.supersedes,
                "previous_hash": entry.previous_hash,
                "valid_time": entry.valid_time,
                "contests": entry.contests,
            }

            # Build inverted index
            term_counts = Counter(tokens)
            for term, count in term_counts.items():
                if term not in self.inverted_index:
                    self.inverted_index[term] = []
                self.inverted_index[term].append((entry.id, count))

        self.avg_doc_length = total_length / self.total_docs if self.total_docs else 0
        self.built_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        logger.info(
            "Built index: %d entries, %d terms, avg_doc_len=%.1f",
            self.total_docs, len(self.inverted_index), self.avg_doc_length,
        )
        return self.total_docs

    def search(
        self,
        query: str,
        *,
        limit: int = 20,
        scope: str | None = None,
        entry_type: str | None = None,
        since: str | None = None,
        boost_retrievals: bool = True,
        time_decay: bool = False,
        retrieval_decay: bool = False,
        now: str | None = None,
    ) -> list[dict[str, Any]]:
        """Search the index using BM25 scoring.

        Returns list of {id, score, meta} dicts sorted by score descending.

        Args:
            time_decay: If True, apply exponential time decay to BM25 scores
                based on entry age. Entries older than TIME_DECAY_HALF_LIFE_DAYS
                get scored lower. Default False for backward compatibility.
            retrieval_decay: If True, apply exponential decay to retrieval
                counts based on time since last retrieval. Old retrievals
                matter less than recent ones. Default False for backward
                compatibility.
            now: Optional UTC timestamp for decay computation (defaults to
                current time). Useful for deterministic testing.
        """
        query_tokens = tokenize(query)
        if not query_tokens:
            return []

        scores: dict[str, float] = {}

        for term in query_tokens:
            postings = self.inverted_index.get(term, [])
            if not postings:
                continue

            # IDF: log((N - n + 0.5) / (n + 0.5) + 1)
            n = len(postings)
            idf = math.log(
                (self.total_docs - n + 0.5) / (n + 0.5) + 1.0
            )

            for doc_id, tf in postings:
                doc_len = self.doc_lengths.get(doc_id, 0)
                # BM25 term score
                numerator = tf * (BM25_K1 + 1)
                denominator = tf + BM25_K1 * (
                    1 - BM25_B + BM25_B * doc_len / max(self.avg_doc_length, 1)
                )
                score = idf * numerator / denominator
                scores[doc_id] = scores.get(doc_id, 0.0) + score

        # Compute reference timestamp for decay
        if time_decay or retrieval_decay:
            ref_ts = now or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            ref_dt = datetime.fromisoformat(ref_ts.replace("Z", "+00:00"))
        else:
            ref_dt = None

        # Apply time decay: exponential decay based on entry age
        if time_decay and ref_dt is not None:
            time_lambda = 0.693 / TIME_DECAY_HALF_LIFE_DAYS
            for doc_id in scores:
                meta = self.doc_meta.get(doc_id)
                if not meta:
                    continue
                entry_ts = meta.get("timestamp", "")
                if not entry_ts:
                    continue
                try:
                    entry_dt = datetime.fromisoformat(
                        entry_ts.replace("Z", "+00:00")
                    )
                    age_days = max((ref_dt - entry_dt).total_seconds() / 86400.0, 0.0)
                    time_factor = math.exp(-time_lambda * age_days)
                    scores[doc_id] *= time_factor
                except (ValueError, TypeError):
                    pass  # Skip entries with unparseable timestamps

        # Apply retrieval frequency boost (stigmergic ranking)
        if boost_retrievals and self.retrieval_counts:
            if retrieval_decay and ref_dt is not None:
                # Decay retrieval counts based on time since last retrieval
                retr_lambda = 0.693 / RETRIEVAL_DECAY_HALF_LIFE_DAYS
                decayed_counts: dict[str, float] = {}
                for doc_id in scores:
                    raw_count = self.retrieval_counts.get(doc_id, 0)
                    if raw_count == 0:
                        continue
                    last_ts = self.retrieval_last_at.get(doc_id, "")
                    if not last_ts:
                        # No timestamp — use raw count (backward compat)
                        decayed_counts[doc_id] = float(raw_count)
                        continue
                    try:
                        last_dt = datetime.fromisoformat(
                            last_ts.replace("Z", "+00:00")
                        )
                        age_days = max((ref_dt - last_dt).total_seconds() / 86400.0, 0.0)
                        decayed_counts[doc_id] = raw_count * math.exp(-retr_lambda * age_days)
                    except (ValueError, TypeError):
                        decayed_counts[doc_id] = float(raw_count)
                max_retrievals = max(decayed_counts.values()) if decayed_counts else 1
                for doc_id in scores:
                    count = decayed_counts.get(doc_id, 0)
                    if count > 0:
                        boost = 1.0 + 0.2 * (count / max(max_retrievals, 1))
                        scores[doc_id] *= boost
            else:
                # Original behavior: no decay on retrieval counts
                max_retrievals = max(self.retrieval_counts.values()) if self.retrieval_counts else 1
                for doc_id in scores:
                    count = self.retrieval_counts.get(doc_id, 0)
                    if count > 0:
                        # Small boost: up to 20% for frequently retrieved entries
                        boost = 1.0 + 0.2 * (count / max(max_retrievals, 1))
                        scores[doc_id] *= boost

        # Filter by metadata
        filtered = []
        for doc_id, score in scores.items():
            meta = self.doc_meta.get(doc_id)
            if not meta:
                continue
            if scope and meta.get("scope") != scope:
                continue
            if entry_type and meta.get("type") != entry_type:
                continue
            if since and meta.get("timestamp", "") < since:
                continue
            filtered.append({"id": doc_id, "score": score, "meta": meta})

        # Sort by score descending
        filtered.sort(key=lambda x: x["score"], reverse=True)
        return filtered[:limit]

    def record_retrieval(self, entry_id: str, timestamp: str | None = None) -> None:
        """Record that an entry was retrieved (for stigmergic ranking).

        Args:
            entry_id: The ID of the retrieved entry.
            timestamp: Optional UTC timestamp (defaults to now). Stored in
                retrieval_last_at for retrieval-count decay.
        """
        self.retrieval_counts[entry_id] = (
            self.retrieval_counts.get(entry_id, 0) + 1
        )
        if timestamp is None:
            timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        self.retrieval_last_at[entry_id] = timestamp

    def add_document(self, doc_id: str, text: str, metadata: dict[str, Any] | None = None) -> None:
        """Add a single document to the index."""
        tokens = tokenize(text)
        doc_len = len(tokens)

        self.doc_lengths[doc_id] = doc_len
        if metadata:
            self.doc_meta[doc_id] = metadata

        term_counts = Counter(tokens)
        for term, count in term_counts.items():
            if term not in self.inverted_index:
                self.inverted_index[term] = []
            self.inverted_index[term].append((doc_id, count))

        self.total_docs += 1
        # Update avg_doc_length (incremental)
        total_len = self.avg_doc_length * (self.total_docs - 1) + doc_len
        self.avg_doc_length = total_len / self.total_docs
        self.entry_count += 1

    def save(self, path: str | Path | None = None) -> Path:
        """Save index to disk (crash-safe: temp + rename)."""
        index_path = _resolve_index_path(path or self.index_path)
        index_path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "stats": {
                "total_docs": self.total_docs,
                "avg_doc_length": self.avg_doc_length,
                "built_at": self.built_at,
                "entry_count": self.entry_count,
                "term_count": len(self.inverted_index),
            },
            "inverted_index": self.inverted_index,
            "doc_lengths": self.doc_lengths,
            "doc_meta": self.doc_meta,
            "retrieval_counts": self.retrieval_counts,
            "retrieval_last_at": self.retrieval_last_at,
        }

        # Crash-safe write: temp file + fsync + rename
        fd, tmp_path = tempfile.mkstemp(
            dir=str(index_path.parent),
            suffix=".tmp",
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(data, f, separators=(",", ":"))
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp_path, str(index_path))
        except BaseException:
            with contextlib.suppress(OSError):
                os.unlink(tmp_path)
            raise

        logger.info("Saved index to %s", index_path)
        return index_path

    def load(self, path: str | Path | None = None) -> bool:
        """Load index from disk. Returns True if loaded, False if not found."""
        index_path = _resolve_index_path(path or self.index_path)
        if not index_path.exists():
            return False

        try:
            data = json.loads(index_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as e:
            logger.warning("Failed to load index: %s", e)
            return False

        stats = data.get("stats", {})
        self.total_docs = stats.get("total_docs", 0)
        self.avg_doc_length = stats.get("avg_doc_length", 0.0)
        self.built_at = stats.get("built_at", "")
        self.entry_count = stats.get("entry_count", 0)

        # Inverted index: term -> list of [doc_id, tf]
        raw_idx = data.get("inverted_index", {})
        self.inverted_index = {
            term: [(item[0], item[1]) for item in postings]
            for term, postings in raw_idx.items()
        }

        self.doc_lengths = data.get("doc_lengths", {})
        self.doc_meta = data.get("doc_meta", {})
        self.retrieval_counts = data.get("retrieval_counts", {})
        self.retrieval_last_at = data.get("retrieval_last_at", {})

        logger.info(
            "Loaded index: %d entries, %d terms",
            self.total_docs, len(self.inverted_index),
        )
        return True
