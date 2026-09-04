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

"""CLI for the Cognitive Ledger: ``python -m hummbl_governance.cognition``.

Subcommands: post, query, search, reindex, boot, state.
Run from anywhere inside a hummbl-governance checkout; override the target
checkout with ``$HUMMBL_GOVERNANCE_ROOT``.

stdlib-only.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

from hummbl_governance.cognition.boot_context import build_boot_context
from hummbl_governance.cognition.indexer import (
    load_index,
    reindex,
    search_index,
)
from hummbl_governance.cognition.ledger_writer import (
    ENTRY_TYPES,
    MAX_TAGS,
    SCOPES,
    append_entry,
    ledger_path,
    load_entries,
    resolve_root,
)
from hummbl_governance.cognition.query import filter_entries, render
from hummbl_governance.cognition.scanner import ContentScanError

__all__ = ["main"]


def _add_post_parser(sub: argparse._SubParsersAction) -> None:  # noqa: SLF001
    p = sub.add_parser("post", help="append one entry to the ledger")
    p.add_argument("--vendor", default=None, help="model vendor (e.g. zai, xai)")
    p.add_argument("--model", default=None, help="model id actually running")
    p.add_argument("--type", default="lesson", choices=ENTRY_TYPES, help="entry type")
    p.add_argument("--scope", default="project", choices=SCOPES, help="entry scope")
    p.add_argument("--content", required=True, help="the knowledge to record")
    p.add_argument("--tags", default="", help="comma-separated tags (max %d)" % MAX_TAGS)
    p.add_argument("--agent", default=None, help="agent identity (default $AGENT_AGENT)")
    p.add_argument(
        "--confidence", type=float, default=0.8, help="confidence in [0.0, 1.0]"
    )
    p.add_argument("--evidence", default="", help="source/evidence citation")
    p.add_argument(
        "--assurance-level", default="SELF", help="assurance level (default SELF)"
    )


def build_parser() -> argparse.ArgumentParser:
    """Build the cognition CLI argument parser."""
    parser = argparse.ArgumentParser(
        prog="python -m hummbl_governance.cognition",
        description="Cognitive Ledger Protocol (CLP) CLI",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    _add_post_parser(sub)

    q = sub.add_parser("query", help="query recent entries with filters")
    q.add_argument("--type", dest="entry_type", default=None, choices=ENTRY_TYPES)
    q.add_argument("--scope", default=None, choices=SCOPES)
    q.add_argument("--agent", default=None)
    q.add_argument("--since", default=None, help="YYYY-MM-DD (UTC)")
    q.add_argument("--limit", type=int, default=20)

    s = sub.add_parser("search", help="BM25 full-text search (requires prior reindex)")
    s.add_argument("terms", help="search terms")
    s.add_argument("--limit", type=int, default=10)

    sub.add_parser("reindex", help="rebuild the BM25 index over all entries")
    sub.add_parser("boot", help="print the session boot context")
    sub.add_parser("state", help="ledger stats (counts, index freshness, last write)")
    return parser


def _resolve_agent_vendor(args: argparse.Namespace) -> tuple[str, str]:
    vendor = args.vendor or os.environ.get("AGENT_VENDOR")
    model = args.model or os.environ.get("AGENT_MODEL")
    if not vendor:
        raise SystemExit("error: set AGENT_VENDOR (or pass --vendor): vendor actually running")
    if not model:
        raise SystemExit("error: set AGENT_MODEL (or pass --model): model actually running")
    return vendor, model


def _cmd_post(args: argparse.Namespace) -> int:
    vendor, model = _resolve_agent_vendor(args)
    agent = args.agent or os.environ.get("AGENT_AGENT") or "unknown"
    tags = [t.strip() for t in args.tags.split(",") if t.strip()]
    record = append_entry(
        args.content,
        entry_type=args.type,
        scope=args.scope,
        tags=tags,
        agent=agent,
        vendor=vendor,
        model=model,
        confidence=args.confidence,
        evidence=args.evidence,
        assurance_level=args.assurance_level,
    )
    print(json.dumps({"posted": record["id"], "timestamp": record["timestamp"]}))
    return 0


def _cmd_query(args: argparse.Namespace) -> int:
    entries = filter_entries(
        load_entries(),
        entry_type=args.entry_type,
        scope=args.scope,
        agent=args.agent,
        since=args.since,
        limit=args.limit,
    )
    for entry in entries:
        print(render(entry))
    print(f"# {len(entries)} entry(ies)", file=sys.stderr)
    return 0


def _cmd_search(args: argparse.Namespace) -> int:
    entries = load_entries()
    index = load_index()
    if index is None:
        print("error: no index found; run 'reindex' first", file=sys.stderr)
        return 1
    results = search_index(args.terms, entries, index, top_k=args.limit)
    for entry, score in results:
        print(f"{score:7.3f}  {render(entry)}")
    print(f"# {len(results)} hit(s)", file=sys.stderr)
    return 0


def _cmd_reindex(args: argparse.Namespace) -> int:
    entries = load_entries()
    path = reindex(entries, root=resolve_root())
    print(json.dumps({"indexed": len(entries), "path": str(path)}))
    return 0


def _cmd_boot(args: argparse.Namespace) -> int:
    print(build_boot_context(load_entries()))
    return 0


def _cmd_state(args: argparse.Namespace) -> int:
    from hummbl_governance.cognition.indexer import index_path

    root = resolve_root()
    entries = load_entries()
    idx = index_path(root)
    last_ts = entries[-1]["timestamp"] if entries else "(empty)"
    print(json.dumps({
        "root": str(root),
        "ledger": str(ledger_path(root)),
        "entries": len(entries),
        "last_write": last_ts,
        "index_present": idx.is_file(),
        "index_path": str(idx),
    }))
    return 0


def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""
    parser = build_parser()
    args = parser.parse_args(argv)
    handlers = {
        "post": _cmd_post,
        "query": _cmd_query,
        "search": _cmd_search,
        "reindex": _cmd_reindex,
        "boot": _cmd_boot,
        "state": _cmd_state,
    }
    try:
        return handlers[args.command](args)
    except ContentScanError as exc:
        print("error: content scan rejected entry:", file=sys.stderr)
        for reason in exc.reasons:
            print(f"  - {reason}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
