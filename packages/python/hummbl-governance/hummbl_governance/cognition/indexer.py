# Copyright 2024-2026 HUMMBL, LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# SPDX-License-Identifier: Apache-2.0

"""BM25 full-text index over the Cognitive Ledger.

The index is a JSON document at ``<root>/_state/cognition/index.json``.
``reindex`` rebuilds it from the ledger; ``search`` scores entries with
Okapi BM25 (k1=1.5, b=0.75).

stdlib-only.
"""

from __future__ import annotations

import json
import math
import re
from datetime import datetime, timezone
from pathlib import Path

from hummbl_governance.cognition.ledger_writer import resolve_root

__all__ = ["build_index", "index_path", "load_index", "search_index"]

_K1 = 1.5
_B = 0.75
_TOKEN_RE = re.compile(r"[a-z0-9_]{2,}")


def index_path(root: Path | None = None) -> Path:
    """Return the index JSON path under *root* (default: :func:`resolve_root`)."""
    return (root or resolve_root()) / "_state" / "cognition" / "index.json"


def _tokenize(text: str) -> list[str]:
    return _TOKEN_RE.findall(text.lower())


def _doc_text(entry: dict) -> str:
    tags = " ".join(entry.get("tags", []))
    return " ".join(
        str(entry.get(field, "")) for field in ("content", "evidence")
    ) + " " + tags


def build_index(entries: list[dict]) -> dict:
    """Build a BM25 index document from *entries*."""
    docs: dict[str, dict] = {}
    df: dict[str, int] = {}
    total_len = 0
    for entry in entries:
        doc_id = str(entry.get("id", ""))
        counts: dict[str, int] = {}
        for token in _tokenize(_doc_text(entry)):
            counts[token] = counts.get(token, 0) + 1
        for term in counts:
            df[term] = df.get(term, 0) + 1
        docs[doc_id] = {"terms": counts, "len": sum(counts.values())}
        total_len += docs[doc_id]["len"]
    n = len(docs)
    avgdl = (total_len / n) if n else 0.0
    return {
        "version": 1,
        "built_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "n_docs": n,
        "avgdl": avgdl,
        "df": df,
        "docs": docs,
    }


def save_index(index: dict, root: Path | None = None) -> Path:
    """Persist *index* to disk and return its path."""
    path = index_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(index, ensure_ascii=False), encoding="utf-8")
    return path


def load_index(root: Path | None = None) -> dict | None:
    """Load the index document, or ``None`` if absent/corrupt."""
    path = index_path(root)
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def search_index(
    query: str,
    entries: list[dict],
    index: dict,
    top_k: int = 10,
) -> list[tuple[dict, float]]:
    """Return the ``(entry, score)`` pairs for *query*, best first."""
    if not index.get("docs") or index.get("n_docs", 0) == 0:
        return []
    by_id = {str(e.get("id", "")): e for e in entries}
    q_terms = _tokenize(query)
    if not q_terms:
        return []
    n = index["n_docs"]
    avgdl = index["avgdl"] or 1.0
    df: dict[str, int] = index.get("df", {})
    scores: dict[str, float] = {}
    for doc_id, doc in index["docs"].items():
        dl = doc["len"] or 1
        norm = _K1 * (1 - _B + _B * dl / avgdl)
        score = 0.0
        for term in q_terms:
            tf = doc["terms"].get(term, 0)
            if not tf:
                continue
            idf = math.log((n - df.get(term, 0) + 0.5) / (df.get(term, 0) + 0.5) + 1)
            score += idf * (tf * (_K1 + 1)) / (tf + norm)
        if score > 0:
            scores[doc_id] = score
    ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)[:top_k]
    return [(by_id[doc_id], score) for doc_id, score in ranked if doc_id in by_id]


def reindex(entries: list[dict], root: Path | None = None) -> Path:
    """Rebuild and persist the index from *entries*; return the index path."""
    return save_index(build_index(entries), root)


# Keep ledger_path importable from this module for callers that treat the
# indexer as the read-side surface (query + search + reindex).
__all__.append("ledger_path")
