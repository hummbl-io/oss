#!/usr/bin/env python3
"""MCP Server for the Cognitive Ledger Protocol (CLP).

Exposes the 505-entry cognitive ledger, BM25 search, boot context,
and ledger write operations as MCP tools via stdio JSON-RPC.

Zero third-party dependencies. Uses only Python stdlib + hummbl_cognition.

Tools:
    ledger_search    - BM25 full-text search across all ledger entries
    ledger_query     - Query by agent, type, scope, tags, or time range
    ledger_post      - Append a new entry to the ledger
    ledger_stats     - Entry count, agent breakdown, type breakdown, index health
    boot_context     - Get session boot context (recent high-value entries)
    memory_search    - Unified search across 5 memory pools (ledger, bus, briefings, findings, MEMORY.md)
    reindex          - Rebuild the BM25 index from ledger
"""

from __future__ import annotations

import json
import os
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Ensure hummbl_cognition is importable (repo root = grandparent of this file)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from hummbl_cognition.indexer import BM25Index
from hummbl_cognition.ledger_writer import DEFAULT_COGNITION_DIR, post_entry
from hummbl_cognition.models import LedgerEntry
from hummbl_cognition.query import query_entries

SERVER_NAME = "cognitive-ledger"
SERVER_VERSION = "0.1.0"
PROTOCOL_VERSION = "2024-11-05"

LEDGER_DIR = Path(
    os.environ.get(
        "CLP_STATE_DIR",
        DEFAULT_COGNITION_DIR,
    )
)
LEDGER_FILE = LEDGER_DIR / "ledger.jsonl"
INDEX_FILE = LEDGER_DIR / "index.json"

# ---------------------------------------------------------------------------
# Singleton instances
# ---------------------------------------------------------------------------
_indexer = None
_index_dirty = False


def get_indexer() -> BM25Index:
    global _indexer, _index_dirty
    if _indexer is None:
        _indexer = BM25Index(str(INDEX_FILE))
        if INDEX_FILE.exists():
            _indexer.load()
    if _index_dirty:
        _rebuild_index(_indexer)
        _index_dirty = False
    else:
        # Check on every access, not only singleton construction. External
        # batch ingestion may update the ledger while this process is alive.
        _check_and_rebuild_if_stale(_indexer)
    return _indexer


def _rebuild_index(indexer: BM25Index) -> None:
    """Rebuild and persist the derived index from the canonical ledger."""
    indexer.build(ledger_path=str(LEDGER_FILE))
    indexer.save(str(INDEX_FILE))


def _check_and_rebuild_if_stale(indexer: BM25Index) -> None:
    """Rebuild the index if the ledger is newer than the index build time."""
    if not LEDGER_FILE.exists():
        return
    built_at = indexer.built_at
    if not built_at or not isinstance(built_at, str):
        # No build timestamp or invalid type — rebuild
        _rebuild_index(indexer)
        return
    from datetime import datetime

    try:
        built_dt = datetime.fromisoformat(built_at.replace("Z", "+00:00")).timestamp()
    except ValueError:
        # Malformed build timestamp — index is corrupt/untrustworthy.
        # Rebuild rather than silently serving a stale index (PR #1533 regression).
        _rebuild_index(indexer)
        return
    try:
        ledger_stat = LEDGER_FILE.stat()
        index_stat = INDEX_FILE.stat()
    except OSError:
        _rebuild_index(indexer)
        return

    # The persisted index mtime preserves subsecond ordering; ``built_at``
    # does not.  Use both signals so a copied/touched stale index is caught
    # without rebuilding forever when ledger and build share one ISO second.
    ledger_mtime_ns = ledger_stat.st_mtime_ns
    if ledger_mtime_ns is None:
        ledger_mtime_ns = int(ledger_stat.st_mtime * 1_000_000_000)
    index_mtime_ns = index_stat.st_mtime_ns
    if index_mtime_ns is None:
        index_mtime_ns = int(index_stat.st_mtime * 1_000_000_000)
    ledger_is_newer_file = ledger_mtime_ns > index_mtime_ns
    ledger_is_newer_build = ledger_stat.st_mtime >= built_dt + 1.0
    if ledger_is_newer_file or ledger_is_newer_build:
        _rebuild_index(indexer)


# ---------------------------------------------------------------------------
# Tool definitions
# ---------------------------------------------------------------------------
TOOLS = [
    {
        "name": "ledger_search",
        "description": "Full-text BM25 search across all cognitive ledger entries. Returns ranked results with relevance scores.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query (natural language or keywords)",
                },
                "limit": {
                    "type": "integer",
                    "description": "Max results (default: 10)",
                    "default": 10,
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "ledger_query",
        "description": "Query ledger entries by structured filters: agent, type, scope, tags, or time range.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "agent": {"type": "string", "description": "Filter by agent ID"},
                "entry_type": {
                    "type": "string",
                    "description": "Filter by type (observation, decision, convention, question, finding)",
                },
                "scope": {"type": "string", "description": "Filter by scope"},
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Filter by tags (AND logic)",
                },
                "limit": {
                    "type": "integer",
                    "description": "Max results (default: 20)",
                    "default": 20,
                },
            },
            "required": [],
        },
    },
    {
        "name": "ledger_post",
        "description": "Append a new entry to the cognitive ledger. Returns the entry ID.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Entry title"},
                "content": {
                    "type": "string",
                    "description": "Entry content (the knowledge to persist)",
                },
                "entry_type": {
                    "type": "string",
                    "enum": [
                        "lesson",
                        "decision",
                        "discovery",
                        "correction",
                        "convention",
                    ],
                    "description": "Entry type (canonical LedgerEntryType)",
                },
                "agent": {
                    "type": "string",
                    "description": "Agent ID (default: mcp-client)",
                    "default": "mcp-client",
                },
                "vendor": {
                    "type": "string",
                    "description": "Vendor (anthropic|openai|google|moonshot|local|human). If omitted, resolves from COGNITION_VENDOR env var; missing both → error.",
                },
                "model": {
                    "type": "string",
                    "description": "Model identifier. If omitted, resolves from COGNITION_MODEL env var; missing both → error.",
                },
                "confidence": {
                    "type": "number",
                    "description": "Confidence 0.0-1.0 (default: 0.7)",
                    "default": 0.7,
                },
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Tags for categorization (max 10)",
                },
                "scope": {
                    "type": "string",
                    "enum": ["project", "module", "file", "convention", "process"],
                    "description": "Scope (default: project)",
                    "default": "project",
                },
            },
            "required": ["title", "content", "entry_type"],
        },
    },
    {
        "name": "ledger_stats",
        "description": "Get ledger statistics: entry count, agent breakdown, type breakdown, index health.",
        "inputSchema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "boot_context",
        "description": "Get session boot context — high-value recent entries for agent initialization. Returns the most relevant entries for starting a new work session.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "max_entries": {
                    "type": "integer",
                    "description": "Max entries to return (default: 15)",
                    "default": 15,
                },
            },
            "required": [],
        },
    },
    {
        "name": "reindex",
        "description": "Rebuild the BM25 full-text index from the ledger. Run after bulk imports or if search quality degrades.",
        "inputSchema": {"type": "object", "properties": {}, "required": []},
    },
]


# ---------------------------------------------------------------------------
# Tool dispatch
# ---------------------------------------------------------------------------
def handle_tool(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    global _index_dirty
    if name == "ledger_search":
        query_text = arguments.get("query")
        if not query_text:
            return {"error": "Missing required argument: query"}
        indexer = get_indexer()
        limit = arguments.get("limit", 10)
        try:
            # BM25Index.search returns list[dict] with keys {id, score, meta}.
            # The kwarg is `limit`, not `k` (the old `k=` call was stale post-
            # refactor and raised TypeError before reaching the engine).
            results = indexer.search(query_text, limit=limit)
            return {
                "query": query_text,
                "count": len(results),
                "results": [
                    {
                        "doc_id": r.get("id", ""),
                        "score": round(r.get("score", 0.0), 4),
                        "meta": r.get("meta", {}),
                    }
                    for r in results
                ],
            }
        except Exception as e:
            return {"error": f"Search failed: {e}. Try running reindex first."}

    elif name == "ledger_query":
        kwargs = {}
        if arguments.get("agent"):
            kwargs["agent"] = arguments["agent"]
        if arguments.get("entry_type"):
            kwargs["entry_type"] = arguments["entry_type"]
        if arguments.get("scope"):
            kwargs["scope"] = arguments["scope"]
        if arguments.get("tags"):
            kwargs["tags"] = arguments["tags"]
        limit = arguments.get("limit", 20)
        try:
            entries = list(query_entries(ledger_path=str(LEDGER_FILE), **kwargs))[
                :limit
            ]
            return {
                "count": len(entries),
                "entries": [
                    {
                        "id": getattr(e, "id", ""),
                        "title": getattr(e, "title", ""),
                        "content": str(getattr(e, "content", ""))[:500],
                        "agent": getattr(e, "agent", ""),
                        "type": getattr(e, "entry_type", getattr(e, "type", "")),
                        "timestamp": str(getattr(e, "timestamp", "")),
                        "confidence": getattr(e, "confidence", 0),
                        "tags": getattr(e, "tags", []),
                    }
                    for e in entries
                ],
            }
        except Exception as e:
            return {"error": f"Query failed: {e}"}

    elif name == "ledger_post":
        # Validate required args explicitly so missing fields surface as a
        # clear schema error rather than a confusing 'Post failed: <key>'.
        missing = [k for k in ("content", "entry_type") if not arguments.get(k)]
        if missing:
            return {"error": f"Missing required argument(s): {', '.join(missing)}"}
        try:
            title = (arguments.get("title") or "").strip()
            body = arguments["content"]
            # Fold title into content (LedgerEntry has no title field).
            # NOTE: this shifts content_hash for any entry with a non-empty
            # title; legacy entries without titles remain hash-stable.
            combined_content = f"# {title}\n\n{body}" if title else body
            # Resolve vendor/model from args → env vars → error.
            # Hardcoding "anthropic" would corrupt provenance (any agent may
            # call this MCP). LedgerEntry rejects vendor not in VALID_VENDORS
            # (anthropic/openai/google/moonshot/local/human), so a missing
            # identity must surface as a clear schema error, not "Invalid
            # vendor: 'unknown'".
            vendor = arguments.get("vendor") or os.environ.get("COGNITION_VENDOR")
            model = arguments.get("model") or os.environ.get("COGNITION_MODEL")
            missing_identity = [
                k for k, v in (("vendor", vendor), ("model", model)) if not v
            ]
            if missing_identity:
                return {
                    "error": (
                        f"Missing required identity: {', '.join(missing_identity)}. "
                        "Supply via arguments or set COGNITION_VENDOR / "
                        "COGNITION_MODEL env vars. Valid vendors: "
                        "anthropic, openai, google, moonshot, local, human."
                    )
                }
            entry = LedgerEntry.create(
                agent=arguments.get("agent", "mcp-client"),
                vendor=vendor,
                model=model,
                entry_type=arguments["entry_type"],
                scope=arguments.get("scope", "project"),
                content=combined_content,
                confidence=arguments.get("confidence", 0.7),
                tags=tuple(str(t) for t in arguments.get("tags", [])),
            )
            written = post_entry(entry, ledger_path=str(LEDGER_FILE))
            _index_dirty = True
            return {
                "posted": True,
                "id": written.id,
                "title": title,
                "type": written.type,
            }
        except Exception as e:
            return {"error": f"Post failed: {e}"}

    elif name == "ledger_stats":
        try:
            entries = []
            if LEDGER_FILE.exists():
                with open(LEDGER_FILE, encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            try:
                                entries.append(json.loads(line))
                            except json.JSONDecodeError:
                                pass

            agents = {}
            types = {}
            for e in entries:
                ag = e.get("agent", "unknown")
                agents[ag] = agents.get(ag, 0) + 1
                et = e.get("entry_type", e.get("type", "unknown"))
                types[et] = types.get(et, 0) + 1

            index_exists = INDEX_FILE.exists()
            index_size = INDEX_FILE.stat().st_size if index_exists else 0

            return {
                "total_entries": len(entries),
                "agents": dict(sorted(agents.items(), key=lambda x: -x[1])),
                "types": dict(sorted(types.items(), key=lambda x: -x[1])),
                "index": {
                    "exists": index_exists,
                    "size_bytes": index_size,
                    "status": "healthy" if index_exists else "missing — run reindex",
                },
                "ledger_file": str(LEDGER_FILE),
                "last_modified": str(
                    datetime.fromtimestamp(LEDGER_FILE.stat().st_mtime, tz=timezone.utc)
                )
                if LEDGER_FILE.exists()
                else "n/a",
            }
        except Exception as e:
            return {"error": f"Stats failed: {e}"}

    elif name == "boot_context":
        try:
            from hummbl_cognition.boot_context import build_boot_context

            max_entries = arguments.get("max_entries", 15)
            # build_boot_context takes `cognition_dir` (positional), not
            # `ledger_path`/`index_path`. The function resolves both files
            # from that directory. Old handler signature was stale post-
            # refactor of boot_context (same class as the PR #790 ledger_post
            # title-arg drift).
            context = build_boot_context(
                cognition_dir=str(LEDGER_DIR),
                max_entries=max_entries,
            )
            return {"boot_context": context}
        except ImportError:
            # Fallback: return recent entries
            entries = []
            if LEDGER_FILE.exists():
                with open(LEDGER_FILE, encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            try:
                                entries.append(json.loads(line))
                            except json.JSONDecodeError:
                                pass
            limit = arguments.get("max_entries", 15)
            recent = entries[-limit:]
            return {
                "count": len(recent),
                "entries": [
                    {
                        "title": e.get("title", ""),
                        "content": str(e.get("content", ""))[:300],
                    }
                    for e in recent
                ],
            }
        except Exception as e:
            return {"error": f"Boot context failed: {e}"}

    elif name == "reindex":
        try:
            idx = BM25Index(str(INDEX_FILE))
            # Reset state for fresh reindex
            idx.inverted_index = {}
            idx.doc_lengths = {}
            idx.doc_meta = {}
            idx.total_docs = 0
            idx.avg_doc_length = 0.0
            idx.entry_count = 0

            entries = []
            if LEDGER_FILE.exists():
                with open(LEDGER_FILE, encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            try:
                                entries.append(json.loads(line))
                            except json.JSONDecodeError:
                                pass
            for i, e in enumerate(entries):
                text = f"{e.get('title', '')} {e.get('content', '')} {' '.join(e.get('tags', []))}"
                idx.add_document(str(i), text)
            idx.save()
            global _indexer
            _indexer = idx
            return {
                "reindexed": True,
                "entries_indexed": len(entries),
                "index_file": str(INDEX_FILE),
            }
        except Exception as e:
            return {"error": f"Reindex failed: {e}"}

    else:
        return {"error": f"Unknown tool: {name}"}


# ---------------------------------------------------------------------------
# JSON-RPC protocol
# ---------------------------------------------------------------------------
def send_response(msg_id: Any, result: Any) -> None:
    response = {"jsonrpc": "2.0", "id": msg_id, "result": result}
    sys.stdout.write(json.dumps(response) + "\n")
    sys.stdout.flush()


def send_error(msg_id: Any, code: int, message: str) -> None:
    response = {
        "jsonrpc": "2.0",
        "id": msg_id,
        "error": {"code": code, "message": message},
    }
    sys.stdout.write(json.dumps(response) + "\n")
    sys.stdout.flush()


def main() -> None:
    LEDGER_DIR.mkdir(parents=True, exist_ok=True)

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            continue

        msg_id = msg.get("id")
        method = msg.get("method", "")
        params = msg.get("params", {})

        try:
            if method == "initialize":
                send_response(
                    msg_id,
                    {
                        "protocolVersion": PROTOCOL_VERSION,
                        "capabilities": {"tools": {}},
                        "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
                    },
                )
            elif method == "notifications/initialized":
                pass
            elif method == "tools/list":
                send_response(msg_id, {"tools": TOOLS})
            elif method == "tools/call":
                tool_name = params.get("name", "")
                arguments = params.get("arguments", {})
                result = handle_tool(tool_name, arguments)
                send_response(
                    msg_id,
                    {
                        "content": [
                            {
                                "type": "text",
                                "text": json.dumps(result, indent=2, default=str),
                            }
                        ],
                    },
                )
            elif method == "ping":
                send_response(msg_id, {})
            else:
                send_error(msg_id, -32601, f"Method not found: {method}")
        except Exception as e:
            send_error(msg_id, -32603, f"Internal error: {e}\n{traceback.format_exc()}")


if __name__ == "__main__":  # pragma: no cover
    main()
