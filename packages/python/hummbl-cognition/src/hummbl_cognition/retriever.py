"""Open Brain Retriever -- unified search across all memory pools.

Queries ledger index, the local bus cache, briefings, autoresearch findings,
MEMORY.md, hummbl-bibliography, and session claims/ledgers.
Returns ranked results within a token budget.

This is the primary query interface for the Open Brain.
"""

from __future__ import annotations

import json
import logging
import os
import stat
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from hummbl_cognition.feedback_tracker import log_retrieval
from hummbl_cognition.indexer import BM25Index, tokenize

logger = logging.getLogger(__name__)

# Approximate tokens per character (conservative estimate for English)
_CHARS_PER_TOKEN = 4

# The bus pool is a bounded view of cached evidence, never a live bus query.
_BUS_CACHE_MAX_BYTES = 1024 * 1024
_BUS_CACHE_MAX_LINES = 200

# Tier 1: time-decay and retrieval-decay defaults for the retriever.
# The retriever turns decay ON by default (the indexer keeps it OFF for
# backward compat). Override via env vars for testing or tuning.
_DEFAULT_TIME_DECAY = os.environ.get(
    "COGNITION_RETRIEVER_TIME_DECAY", "1"
).strip().lower() not in ("0", "false", "no", "off")
_DEFAULT_RETRIEVAL_DECAY = os.environ.get(
    "COGNITION_RETRIEVER_RETRIEVAL_DECAY", "1"
).strip().lower() not in ("0", "false", "no", "off")


def _estimate_tokens(text: str) -> int:
    """Estimate token count from text length."""
    return max(1, len(text) // _CHARS_PER_TOKEN)


def _resolve_state_dirs(override: str | Path | None = None) -> list[Path]:
    """Resolve all valid state directories."""
    dirs = []
    if override:
        dirs.append(Path(override))

    env_path = os.environ.get("HUMMBL_COGNITION_STATE")
    if env_path:
        dirs.append(Path(env_path))

    try:
        import subprocess

        root = subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"],
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=5,
        ).strip()
        if root:
            root_path = Path(root)
            # 1. Project-level root state
            root_state = root_path / "_state"
            if root_state.exists():
                dirs.append(root_state)

            # 2. Package-level internal state
            internal_state = root_path / "src" / "hummbl_cognition" / "_state"
            if internal_state.exists() and internal_state not in dirs:
                dirs.append(internal_state)
    except (
        subprocess.CalledProcessError,
        FileNotFoundError,
        subprocess.TimeoutExpired,
    ):
        pass

    # Fallback
    if not dirs:
        dirs.append(Path("_state"))

    return dirs


def _resolve_bibliography_path(override: str | Path | None = None) -> Path | None:
    """Resolve hummbl-bibliography unified-bibliography.json path."""
    if override is not None:
        return Path(override)

    env_path = os.environ.get("HUMMBL_BIBLIOGRAPHY_PATH")
    if env_path:
        p = Path(env_path)
        if p.exists():
            return p

    # Standard home/projects location
    home_path = Path.home() / "PROJECTS" / "hummbl-bibliography" / "dist" / "unified-bibliography.json"
    if home_path.exists():
        return home_path

    # Relative to git root / current working directory
    try:
        import subprocess

        root = subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"],
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=5,
        ).strip()
        if root:
            candidate = Path(root).parent / "hummbl-bibliography" / "dist" / "unified-bibliography.json"
            if candidate.exists():
                return candidate
    except (
        subprocess.CalledProcessError,
        FileNotFoundError,
        subprocess.TimeoutExpired,
    ):
        pass

    return None


class MemoryResult:
    """A single result from the Open Brain retriever."""

    __slots__ = (
        "source",
        "entry_id",
        "score",
        "content",
        "metadata",
        "tokens",
        "content_window",
    )

    def __init__(
        self,
        *,
        source: str,
        entry_id: str,
        score: float,
        content: str,
        metadata: dict[str, Any],
        tokens: int = 0,
        content_window: str = "",
    ) -> None:
        self.source = source
        self.entry_id = entry_id
        self.score = score
        self.content = content
        self.metadata = metadata
        self.tokens = tokens or _estimate_tokens(content)
        self.content_window = content_window or content

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "entry_id": self.entry_id,
            "score": round(self.score, 4),
            "content": self.content,
            "content_window": self.content_window,
            "metadata": self.metadata,
            "tokens": self.tokens,
        }


class OpenBrainRetriever:
    """Unified retriever across all memory pools.

    Memory pools:
      1. Cognitive Ledger (ledger.jsonl via BM25 index)
      2. Local bus cache (~/.cache/bus/messages.tsv; not live authority)
      3. Briefings (<state-sibling>/state/briefings/*.md)
      4. Autoresearch findings (_state/autoresearch/findings_*.json)
      5. MEMORY.md (Claude Code auto-memory)
      6. Bibliography (hummbl-bibliography unified index / dist)
      7. Session surfaces (cognition/session-claims/*, cognition/session-ledgers/*)
    """

    def __init__(
        self,
        *,
        state_dir: str | Path | None = None,
        index: BM25Index | None = None,
        bibliography_path: str | Path | None = None,
        bus_cache_path: str | Path | None = None,
    ) -> None:
        self.state_dirs = _resolve_state_dirs(state_dir)
        # Primary state dir for saving index/logs (usually the first one)
        self.primary_state_dir = self.state_dirs[0]
        self.index = index or BM25Index()
        self._index_loaded = False
        self.bibliography_path = _resolve_bibliography_path(bibliography_path)
        self._bibliography_cache: list[dict[str, Any]] | None = None
        self._bibliography_mtime: float = 0.0
        self.bus_cache_path = bus_cache_path
        # Diagnostics for the most recent search, including pools with no hits.
        self.source_diagnostics: dict[str, dict[str, Any]] = {}

    def ensure_index(self, ledger_path: str | Path | None = None) -> None:
        """Load or build the index."""
        if self._index_loaded:
            return
        index_path = self.primary_state_dir / "cognition" / "index.json"
        if not self.index.load(index_path):
            if index_path.exists():
                # An existing-but-unloadable index is corrupted or transiently
                # locked state, NOT absent state. Rebuilding from a possibly
                # wrong default ledger and saving over it once stomped a
                # healthy index (2026-09-25: 2549 -> 3 docs mid-session).
                # Never auto-repair shared state; the explicit `reindex`
                # command is the repair path. The index stays empty for this
                # session; the file is left untouched for the next reader.
                logger.warning(
                    "Index at %s exists but failed to load; refusing to "
                    "rebuild over it (run 'reindex' to repair)",
                    index_path,
                )
                self._index_loaded = True
                return
            self.index.build(ledger_path)
            try:
                self.index.save(index_path)
            except (OSError, RuntimeError) as e:
                logger.warning("Could not save index: %s", e)
        self._index_loaded = True

    def search(
        self,
        query: str,
        *,
        token_budget: int = 8000,
        scope: str | None = None,
        entry_type: str | None = None,
        since: str | None = None,
        sources: list[str] | None = None,
        agent: str = "unknown",
        limit: int = 50,
        time_decay: bool | None = None,
        retrieval_decay: bool | None = None,
        exclude_ids: set[str] | None = None,
    ) -> list[MemoryResult]:
        """Search all memory pools and return ranked results within token budget.

        Parameters
        ----------
        query : str
            Natural language query.
        token_budget : int
            Maximum estimated tokens in returned results.
        scope : str | None
            Filter ledger entries by scope.
        entry_type : str | None
            Filter ledger entries by type.
        since : str | None
            ISO timestamp — only return entries after this time.
        sources : list[str] | None
            Which memory pools to search. Default: all.
            Options: "ledger", "bus", "briefings", "findings", "memory_md",
            "bibliography", "session"
        agent : str
            Agent making the query (for feedback tracking).
        limit : int
            Maximum number of results before budget filtering.
        time_decay : bool | None
            Apply exponential time decay to ledger BM25 scores based on
            entry age. None = use module default (True unless
            COGNITION_RETRIEVER_TIME_DECAY=0).
        retrieval_decay : bool | None
            Apply exponential decay to retrieval counts based on time
            since last retrieval. None = use module default (True unless
            COGNITION_RETRIEVER_RETRIEVAL_DECAY=0).
        exclude_ids : set[str] | None
            Ledger entry ids to mask from results (blind rediscovery
            evaluation). Applies to the ledger pool only; other pools are
            unaffected.

        Returns:
        -------
        list[MemoryResult]
            Ranked results within token budget.
        """
        if time_decay is None:
            time_decay = _DEFAULT_TIME_DECAY
        if retrieval_decay is None:
            retrieval_decay = _DEFAULT_RETRIEVAL_DECAY

        all_sources = sources or [
            "ledger",
            "bus",
            "briefings",
            "findings",
            "session",
            "memory_md",
            "bibliography",
        ]

        self.source_diagnostics = {}
        results: list[MemoryResult] = []

        if "ledger" in all_sources:
            results.extend(
                self._search_ledger(
                    query,
                    scope=scope,
                    entry_type=entry_type,
                    since=since,
                    limit=limit,
                    time_decay=time_decay,
                    retrieval_decay=retrieval_decay,
                    exclude_ids=exclude_ids,
                )
            )

        if "bus" in all_sources:
            results.extend(self._search_bus_cache(query, since=since, limit=limit))

        if "briefings" in all_sources:
            for s_dir in self.state_dirs:
                # Also check siblings of state dirs if 'state' folder exists
                brief_dir = s_dir.parent / "state" / "briefings"
                results.extend(
                    self._search_text_pool(
                        query,
                        pool_name="briefings",
                        search_dir=brief_dir,
                        glob_pattern="*.md",
                        since=since,
                        limit=limit // 4,
                    )
                )

        if "findings" in all_sources:
            for s_dir in self.state_dirs:
                results.extend(
                    self._search_findings(
                        query,
                        search_dir=s_dir / "autoresearch",
                        since=since,
                        limit=limit // 4,
                    )
                )

        if "session" in all_sources:
            results.extend(
                self._search_session(query, since=since, limit=limit // 4)
            )

        if "memory_md" in all_sources:
            results.extend(self._search_memory_md(query, limit=limit // 4))

        if "bibliography" in all_sources:
            results.extend(self._search_bibliography(query, limit=limit // 4))

        # Sort all results by score
        results.sort(key=lambda r: r.score, reverse=True)

        # Apply token budget
        budgeted: list[MemoryResult] = []
        remaining = token_budget
        for result in results:
            if result.tokens <= remaining:
                budgeted.append(result)
                remaining -= result.tokens
            elif remaining > 0:
                # Truncate content to fit remaining budget
                chars = remaining * _CHARS_PER_TOKEN
                truncated = MemoryResult(
                    source=result.source,
                    entry_id=result.entry_id,
                    score=result.score,
                    content=result.content[:chars] + "...",
                    metadata=result.metadata,
                    tokens=remaining,
                )
                budgeted.append(truncated)
                remaining = 0
                break

        # Log retrieval for feedback tracking
        retrieved_ids = [r.entry_id for r in budgeted if r.entry_id.startswith("clp-")]
        if retrieved_ids:
            try:
                log_retrieval(
                    query=query,
                    entry_ids=retrieved_ids,
                    agent=agent,
                    log_path=self.primary_state_dir
                    / "cognition"
                    / "retrieval_log.jsonl",
                )
                # Update index retrieval counts
                for eid in retrieved_ids:
                    self.index.record_retrieval(eid)
            except OSError:
                pass  # Non-critical

        # Sentence-window expansion: for ledger results, fetch full entry text
        # as the content window (the content field is a preview snippet).
        self._expand_windows(budgeted)

        return budgeted

    def _search_bus_cache(
        self, query: str, *, since: str | None, limit: int
    ) -> list[MemoryResult]:
        """Search complete rows in a bounded cache tail without refreshing it."""
        observed = datetime.now(timezone.utc)
        diagnostics: dict[str, Any] = {
            "source_kind": "local_bus_cache",
            "live_verified": False,
            "freshness": "cache_only_unverified",
            "observed_at": observed.isoformat(),
            "since": since,
            "max_bytes": _BUS_CACHE_MAX_BYTES,
            "max_rows": _BUS_CACHE_MAX_LINES,
        }
        self.source_diagnostics["bus"] = diagnostics
        configured = self.bus_cache_path
        selection = "argument"
        if configured is None:
            configured = os.environ.get("HUMMBL_BUS_CACHE_PATH")
            selection = "environment"
        if configured is None:
            configured = Path.home() / ".cache" / "bus" / "messages.tsv"
            selection = "default"
        diagnostics["source_selection"] = selection
        raw_path = str(configured)
        path = Path(raw_path)
        # Do not interpret relative paths, URLs, UNC paths, or device paths as
        # local cache configuration. Invalid overrides never fall back.
        if (
            not raw_path
            or "\x00" in raw_path
            or "://" in raw_path
            or raw_path.replace("\\", "/").startswith("//")
            or not path.is_absolute()
        ):
            diagnostics["status"] = "invalid_cache_path"
            return []
        diagnostics["path"] = str(path)
        since_timestamp: datetime | None = None
        if since is not None:
            try:
                since_timestamp = datetime.fromisoformat(since.replace("Z", "+00:00"))
                # Date-only and naive datetime lower bounds mean UTC.
                if since_timestamp.tzinfo is None:
                    since_timestamp = since_timestamp.replace(tzinfo=timezone.utc)
                since_timestamp = since_timestamp.astimezone(timezone.utc)
            except (AttributeError, TypeError, ValueError, OverflowError):
                diagnostics["status"] = "invalid_since"
                return []
        diagnostics["since_utc"] = since_timestamp.isoformat() if since_timestamp else None
        try:
            if not stat.S_ISREG(path.stat().st_mode):
                diagnostics["status"] = "not_regular_file"
                return []
            # Avoid BufferedReader read-ahead past the captured file length.
            with path.open("rb", buffering=0) as cache:
                before = os.fstat(cache.fileno())
                if not stat.S_ISREG(before.st_mode):
                    diagnostics["status"] = "not_regular_file"
                    return []
                start = max(0, before.st_size - _BUS_CACHE_MAX_BYTES)
                cache.seek(max(0, start - 1))
                previous = cache.read(1) if start else b"\n"
                data = cache.read(min(before.st_size, _BUS_CACHE_MAX_BYTES))
                after = os.fstat(cache.fileno())
        except FileNotFoundError:
            diagnostics["status"] = "missing"
            return []
        except OSError as exc:
            diagnostics.update(status="unreadable", error_type=type(exc).__name__)
            return []

        diagnostics.update(
            file_bytes=before.st_size,
            bytes_read=len(data) + bool(start),
            cache_mtime=datetime.fromtimestamp(before.st_mtime, timezone.utc).isoformat(),
            cache_mtime_age_seconds=round(observed.timestamp() - before.st_mtime, 3),
            changed_during_read=(
                before.st_size != after.st_size or before.st_mtime_ns != after.st_mtime_ns
            ),
            byte_tail_truncated=bool(start),
            partial_first_row_discarded=bool(start and previous != b"\n"),
            partial_last_row_discarded=bool(data and not data.endswith(b"\n")),
            latest_valid_timestamp=None,
            latest_valid_timestamp_scope="scanned_rows",
            latest_message_age_seconds=None,
        )
        if start and previous != b"\n":
            _, _, data = data.partition(b"\n")
        if data and not data.endswith(b"\n"):
            data = data.rpartition(b"\n")[0]
        rows = data.splitlines()
        diagnostics["row_tail_truncated"] = len(rows) > _BUS_CACHE_MAX_LINES
        rows = rows[-_BUS_CACHE_MAX_LINES:]
        diagnostics["rows_scanned"] = len(rows)
        diagnostics["coverage"] = (
            "partial_cache"
            if any(diagnostics[key] for key in (
                "byte_tail_truncated", "row_tail_truncated",
                "partial_first_row_discarded", "partial_last_row_discarded",
                "changed_during_read",
            ))
            else "complete_cache"
        )
        messages: list[str] = []
        latest: datetime | None = None
        malformed_rows = 0
        valid_rows = 0
        for row in rows:
            try:
                fields = row.decode("utf-8").split("\t", 4)
                if len(fields) != 5:
                    raise ValueError("Expected five TSV columns")
                timestamp = datetime.fromisoformat(fields[0].replace("Z", "+00:00"))
                if timestamp.tzinfo is None:
                    raise ValueError("Expected a timezone-aware timestamp")
                timestamp = timestamp.astimezone(timezone.utc)
            except (UnicodeError, ValueError, OverflowError):
                malformed_rows += 1
                continue
            valid_rows += 1
            latest = max(latest, timestamp) if latest else timestamp
            # Inclusive lower bound, independent of ISO spelling or offset.
            if since_timestamp is not None and timestamp < since_timestamp:
                continue
            messages.append(f"{fields[0]} {fields[1]} {fields[3]} {fields[4]}")
        diagnostics.update(
            valid_rows=valid_rows, malformed_rows=malformed_rows,
            rows_after_since=len(messages),
        )
        if latest is not None:
            diagnostics.update(
                latest_valid_timestamp=latest.astimezone(timezone.utc).isoformat(),
                latest_message_age_seconds=round((observed - latest).total_seconds(), 3),
            )
        text = "\n".join(messages)
        query_tokens = set(tokenize(query))
        overlap = query_tokens & set(tokenize(text)) if query_tokens else set()
        diagnostics["status"] = (
            "empty" if before.st_size == 0 else
            "no_valid_rows" if not valid_rows else
            "no_rows_after_since" if not messages else
            "no_match" if not overlap else
            "available"
        )
        if not overlap or limit <= 0:
            return []
        return [MemoryResult(
            source="bus",
            entry_id=f"bus:{path.name}",
            score=len(overlap) / len(query_tokens) * 0.7,
            content=_extract_snippet(
                text, query_tokens, max_chars=500, search_chars=len(text)
            ),
            content_window=_extract_snippet(
                text, query_tokens, max_chars=1500, search_chars=len(text)
            ),
            metadata={"file": path.name, **diagnostics},
        )]

    def _expand_windows(self, results: list[MemoryResult]) -> None:
        """Expand content_window for each result with surrounding context.

        For ledger entries: fetch the full entry text from the index if it
        exposes ``get_entry()``. Older index implementations may not — in
        that case this is a no-op for ledger results and ``content_window``
        falls back to ``content`` per ``MemoryResult.__init__``.

        For text-pool entries: expand snippet by fetching more context
        from the source file.
        """
        get_entry = getattr(self.index, "get_entry", None)
        for result in results:
            if result.source == "bus":
                # Bus producers supply bounded context; never reread their paths.
                continue
            if result.source == "ledger" and get_entry is not None:
                # Fetch full entry from index if the producer side supports it
                try:
                    full = get_entry(result.entry_id)
                except (AttributeError, KeyError):
                    continue
                if full and len(full) > len(result.content):
                    result.content_window = full
            elif result.source in ("bus_digest", "briefings", "session"):
                # Text pool results: try to fetch more context from source
                src_file = result.metadata.get("path") or result.metadata.get(
                    "file", ""
                )
                if src_file:
                    try:
                        path = Path(src_file)
                        text = path.read_text(encoding="utf-8", errors="replace")
                        if path.suffix == ".tsv":
                            text = _extract_tsv_messages(text)
                        # Extract a larger snippet around the match
                        needle = result.content.strip()
                        if needle.startswith("..."):
                            needle = needle[3:].lstrip()
                        if needle.endswith("..."):
                            needle = needle[:-3].rstrip()
                        idx = text.find(needle[:80])
                        if idx >= 0:
                            start = max(0, idx - 500)
                            end = min(len(text), idx + len(result.content) + 500)
                            result.content_window = text[start:end]
                    except OSError:
                        pass

    def _search_ledger(
        self,
        query: str,
        *,
        scope: str | None = None,
        entry_type: str | None = None,
        since: str | None = None,
        limit: int = 20,
        time_decay: bool = False,
        retrieval_decay: bool = False,
        exclude_ids: set[str] | None = None,
    ) -> list[MemoryResult]:
        """Search the cognitive ledger via BM25 index."""
        self.ensure_index()

        mask_kw = {"exclude_ids": exclude_ids} if exclude_ids else {}
        hits = self.index.search(
            query,
            limit=limit,
            scope=scope,
            entry_type=entry_type,
            since=since,
            time_decay=time_decay,
            retrieval_decay=retrieval_decay,
            **mask_kw,
        )

        results = []
        for hit in hits:
            meta = hit["meta"]
            results.append(
                MemoryResult(
                    source="ledger",
                    entry_id=hit["id"],
                    score=hit["score"],
                    content=meta.get("content_preview", ""),
                    metadata={
                        "type": meta.get("type"),
                        "scope": meta.get("scope"),
                        "agent": meta.get("agent"),
                        "timestamp": meta.get("timestamp"),
                        "confidence": meta.get("confidence"),
                        "tags": meta.get("tags", []),
                    },
                )
            )
        return results

    def _search_text_pool(
        self,
        query: str,
        *,
        pool_name: str,
        search_dir: Path,
        glob_pattern: str,
        since: str | None = None,
        limit: int = 5,
    ) -> list[MemoryResult]:
        """Search a directory of text files using simple term matching.

        For TSV files (bus), extracts the message column (col 5) for
        semantic matching rather than treating raw TSV as plain text.
        """
        if not search_dir.exists():
            return []

        query_tokens = set(tokenize(query))
        if not query_tokens:
            return []

        results = []
        try:
            files = sorted(search_dir.glob(glob_pattern), reverse=True)
        except OSError:
            return []

        for filepath in files[:20]:  # Cap file scan
            try:
                text = filepath.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue

            # TSV-aware: extract message column for bus files
            if filepath.suffix == ".tsv":
                text = _extract_tsv_messages(text, since=since)

            # Simple term overlap scoring
            file_tokens = set(tokenize(text[:5000]))  # Cap per file
            overlap = query_tokens & file_tokens
            if not overlap:
                continue

            score = len(overlap) / len(query_tokens)

            # Extract relevant snippet
            snippet = _extract_snippet(text, query_tokens, max_chars=500)

            results.append(
                MemoryResult(
                    source=pool_name,
                    entry_id=f"{pool_name}:{filepath.name}",
                    score=score * 0.7,  # Discount vs ledger BM25
                    content=snippet,
                    metadata={
                        "file": filepath.name,
                        "path": str(filepath),
                    },
                )
            )

        results.sort(key=lambda r: r.score, reverse=True)
        return results[:limit]

    def _search_findings(
        self,
        query: str,
        *,
        search_dir: Path | None = None,
        since: str | None = None,
        limit: int = 5,
    ) -> list[MemoryResult]:
        """Search autoresearch distillation findings."""
        findings_dir = search_dir or (self.primary_state_dir / "autoresearch")
        if not findings_dir.exists():
            return []

        query_tokens = set(tokenize(query))
        if not query_tokens:
            return []

        results = []
        for filepath in findings_dir.glob("findings_*.json"):
            try:
                data = json.loads(filepath.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                continue

            findings = data if isinstance(data, list) else data.get("findings", [])
            for finding in findings:
                claim = finding.get("claim", "")
                tokens = set(tokenize(claim))
                overlap = query_tokens & tokens
                if not overlap:
                    continue

                score = len(overlap) / len(query_tokens) * 0.8
                results.append(
                    MemoryResult(
                        source="findings",
                        entry_id=finding.get("id", f"finding:{filepath.name}"),
                        score=score,
                        content=claim,
                        metadata={
                            "source_file": finding.get("source", ""),
                            "confidence": finding.get("confidence", 0),
                            "category": finding.get("category", ""),
                        },
                    )
                )

        results.sort(key=lambda r: r.score, reverse=True)
        return results[:limit]

    def _search_session(
        self,
        query: str,
        *,
        since: str | None = None,
        limit: int = 5,
    ) -> list[MemoryResult]:
        """Search session claims and session ledgers.

        Session surfaces live under each cognition dir as
        ``session-claims/`` and ``session-ledgers/`` (``.md`` and
        ``.jsonl`` files). A cognition dir is resolved relative to each
        state dir as ``<state>/cognition`` or the state dir itself when
        it already is one; the sibling ``state/cognition`` layout and
        the conventional ``~/.agents/state/cognition`` location are
        also checked (mirroring the memory_md pool's home-relative
        convention).
        """
        bases: list[Path] = []
        for d in self.state_dirs:
            bases.append(d / "cognition")
            bases.append(d.parent / "state" / "cognition")
            bases.append(d)
        bases.append(Path.home() / ".agents" / "state" / "cognition")

        results: list[MemoryResult] = []
        seen: set[str] = set()
        for base in bases:
            for sub in ("session-claims", "session-ledgers"):
                search_dir = base / sub
                try:
                    key = str(search_dir.resolve())
                except OSError:
                    key = str(search_dir)
                if key in seen or not search_dir.is_dir():
                    continue
                seen.add(key)
                for pattern in ("*.md", "*.jsonl"):
                    results.extend(
                        self._search_text_pool(
                            query,
                            pool_name="session",
                            search_dir=search_dir,
                            glob_pattern=pattern,
                            since=since,
                            limit=limit,
                        )
                    )

        results.sort(key=lambda r: r.score, reverse=True)
        return results[:limit]

    def _search_memory_md(
        self,
        query: str,
        *,
        limit: int = 3,
    ) -> list[MemoryResult]:
        """Search Claude Code MEMORY.md files."""
        memory_dir = Path.home() / ".claude" / "projects"
        if not memory_dir.exists():
            return []

        query_tokens = set(tokenize(query))
        if not query_tokens:
            return []

        results = []
        # Search memory files in project memory directories
        try:
            for memory_file in memory_dir.rglob("memory/*.md"):
                try:
                    text = memory_file.read_text(encoding="utf-8", errors="replace")
                except OSError:
                    continue

                file_tokens = set(tokenize(text[:3000]))
                overlap = query_tokens & file_tokens
                if not overlap:
                    continue

                score = len(overlap) / len(query_tokens) * 0.6
                snippet = _extract_snippet(text, query_tokens, max_chars=300)

                results.append(
                    MemoryResult(
                        source="memory_md",
                        entry_id=f"memory:{memory_file.name}",
                        score=score,
                        content=snippet,
                        metadata={"file": str(memory_file)},
                    )
                )
        except OSError:
            pass

        results.sort(key=lambda r: r.score, reverse=True)
        return results[:limit]

    def _load_bibliography_entries(self) -> list[dict[str, Any]]:
        """Load bibliography entries with cached in-memory representation."""
        if not self.bibliography_path or not self.bibliography_path.exists():
            return []
        try:
            mtime = self.bibliography_path.stat().st_mtime
            if (
                self._bibliography_cache is not None
                and self._bibliography_mtime == mtime
            ):
                return self._bibliography_cache
            data = json.loads(self.bibliography_path.read_text(encoding="utf-8"))
            entries = data.get("entries", [])
            self._bibliography_cache = entries
            self._bibliography_mtime = mtime
            return entries
        except (json.JSONDecodeError, OSError):
            return []

    def _search_bibliography(
        self,
        query: str,
        *,
        limit: int = 5,
        tier: str | None = None,
    ) -> list[MemoryResult]:
        """Search hummbl-bibliography unified index.

        Scores matching entries based on token overlap in ID, title, author,
        abstract, keywords, and transformations.
        """
        entries = self._load_bibliography_entries()
        if not entries:
            return []

        query_tokens = set(tokenize(query))
        if not query_tokens:
            return []

        results = []
        for entry in entries:
            if tier and entry.get("tier") != tier:
                continue

            entry_id = entry.get("id", "")
            title = entry.get("title", "")
            author = entry.get("author", "")
            abstract = entry.get("abstract", "")
            keywords = " ".join(entry.get("keywords") or [])
            search_text = f"{entry_id} {title} {author} {abstract} {keywords}"
            tokens = set(tokenize(search_text))
            overlap = query_tokens & tokens
            if not overlap:
                continue

            title_tokens = set(tokenize(f"{entry_id} {title}"))
            title_overlap = query_tokens & title_tokens

            # Base score proportional to query coverage (up to 0.75)
            score = (len(overlap) / len(query_tokens)) * 0.75
            if title_overlap:
                score = min(1.0, score + 0.20 * (len(title_overlap) / len(query_tokens)))

            tier_str = entry.get("tier", "")
            year_str = str(entry.get("year", ""))
            content_text = f"[{tier_str}] {title} - {author} ({year_str}): {abstract}"
            if len(content_text) > 400:
                content_text = content_text[:397] + "..."

            transformations = entry.get("transformations", [])
            trans_str = (
                ", ".join(transformations)
                if isinstance(transformations, list)
                else str(transformations)
            )

            full_window = (
                f"[{tier_str} - {entry.get('tier_name', '')}] {title}\n"
                f"Authors: {author} ({year_str})\n"
                f"Journal: {entry.get('journal', '')}\n"
                f"URL: {entry.get('url', '')}\n"
                f"Transformations: {trans_str}\n\n"
                f"Abstract:\n{abstract}"
            )

            results.append(
                MemoryResult(
                    source="bibliography",
                    entry_id=f"bib:{entry_id}",
                    score=score,
                    content=content_text,
                    content_window=full_window,
                    metadata={
                        "citation_id": entry_id,
                        "tier": tier_str,
                        "tier_name": entry.get("tier_name"),
                        "author": author,
                        "year": year_str,
                        "transformations": transformations,
                        "url": entry.get("url"),
                    },
                )
            )

        results.sort(key=lambda r: r.score, reverse=True)
        return results[:limit]


def _extract_tsv_messages(
    text: str,
    *,
    since: str | None = None,
    max_lines: int = 200,
) -> str:
    r"""Extract message column from TSV bus format.

    Bus format: timestamp\\tfrom\\tto\\ttype\\tmessage
    Returns the message text (col 5) from recent lines, which is the
    semantically meaningful content for search.
    """
    lines = text.strip().split("\n")
    # Take last max_lines (most recent)
    lines = lines[-max_lines:]
    messages = []
    for line in lines:
        parts = line.split("\t")
        if len(parts) < 5:
            continue
        ts = parts[0]
        if since and ts < since:
            continue
        # Include from + type + message for context
        messages.append(f"{parts[1]} {parts[3]} {parts[4]}")
    return "\n".join(messages)


def _extract_snippet(
    text: str,
    query_tokens: set[str],
    max_chars: int = 500,
    *,
    search_chars: int = 5000,
) -> str:
    """Extract the most relevant snippet from text around query term matches."""
    text_lower = text.lower()
    best_pos = 0
    best_score = 0

    # Slide a window and find the position with most query term overlap
    window = max_chars
    for i in range(0, min(len(text), search_chars), 100):
        chunk = text_lower[i : i + window]
        chunk_tokens = set(tokenize(chunk))
        score = len(query_tokens & chunk_tokens)
        if score > best_score:
            best_score = score
            best_pos = i

    snippet = text[best_pos : best_pos + max_chars].strip()
    if best_pos > 0:
        snippet = "..." + snippet
    if best_pos + max_chars < len(text):
        snippet = snippet + "..."

    return snippet
