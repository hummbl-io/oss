"""CLI entry point for the Cognitive Ledger.

Usage:
    python -m hummbl_cognition <command> [options]

Commands:
    post      Write a new ledger entry
    post-verified  Write a verified ledger entry with evidence + confidence
    query     Query ledger with filters
    search    Open Brain: semantic search across all memory pools
    validate  Validate ledger integrity
    state     Show current shared state
    boot      Generate boot context for agent injection
    startup   Generate startup context with cognition plus recent inbox
    reindex   Rebuild the Open Brain search index from ledger
    batch-ingest  Bulk-import JSONL file of ledger entries with dedup
    belonging-check  HRSI Gap 1 — daily belonging baseline (safety/mattering/connection)
    hrsi-checkin     HRSI Gap 2 — unified daily cycle (cogstate+belonging+HULE+lens+delta)
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from hummbl_cognition.boot_context import build_boot_context
from hummbl_cognition.ledger_writer import (
    post_entry,
    read_entries,
    scan_pii,
    validate_integrity,
    validate_integrity_report,
)
from hummbl_cognition.models import (
    CANONICAL_LEDGER_SCOPES,
    CANONICAL_LEDGER_TYPES,
    VALID_COLOR_TEAMS,
    VALID_INTEL_TYPES,
    VALID_VENDORS,
    LedgerEntry,
    LedgerEntryType,
    LedgerScope,
)
from hummbl_cognition.startup_context import (
    build_startup_context,
    write_startup_context,
)
from hummbl_cognition.verified_writer import post_verified_entry


def _build_claim(args: argparse.Namespace) -> dict[str, Any] | None:
    """Build JSON-LD schema:Claim from CLI args if any claim fields are present."""
    if not any([
        getattr(args, "claim_status", None),
        getattr(args, "expires", None),
        getattr(args, "supersedes_entry", None),
    ]):
        return None
    claim: dict[str, Any] = {
        "@context": {
            "schema": "https://schema.org/",
            "hummbl": "https://hummbl.dev/ontology#",
        },
        "@type": ["schema:Claim", "hummbl:AgentClaim"],
    }
    if args.claim_status:
        claim["hummbl:epistemicStatus"] = f"hummbl:Epistemic{args.claim_status.capitalize()}"
    if getattr(args, "expires", None):
        claim["schema:expires"] = args.expires
    if getattr(args, "supersedes_entry", None):
        claim["hummbl:supersededByClaim"] = args.supersedes_entry
    return claim


def cmd_post(args: argparse.Namespace) -> int:
    """Post a new ledger entry."""
    try:
        entry = LedgerEntry.create(
            agent=args.agent,
            vendor=args.vendor,
            model=args.model,
            entry_type=args.type,
            scope=args.scope,
            content=args.content,
            evidence=args.evidence,
            confidence=args.confidence,
            supersedes=args.supersedes,
            tags=tuple(args.tags) if args.tags else (),
            assurance_level=args.assurance_level,
            claim=_build_claim(args),
        )
    except ValueError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1

    try:
        written = post_entry(entry, ledger_path=args.ledger)
    except (ValueError, OSError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1

    print(f"Posted: {written.id} ({written.type}/{written.scope})")
    return 0


def cmd_query(args: argparse.Namespace) -> int:
    """Query ledger entries."""
    entries = read_entries(
        ledger_path=args.ledger,
        since=args.since,
        entry_type=args.type,
        scope=args.scope,
        agent=args.agent,
        tags=args.tags,
        limit=args.limit,
    )

    if not entries:
        print("No entries found.")
        return 0

    if args.json:
        for entry in entries:
            print(entry.to_jsonl())
    else:
        for entry in entries:
            tags_str = f" [{', '.join(entry.tags)}]" if entry.tags else ""
            sup_str = f" (supersedes {entry.supersedes})" if entry.supersedes else ""
            print(
                f"[{entry.timestamp}] ({entry.agent}) "
                f"{entry.type.upper()}/{entry.scope}: "
                f"{entry.content[:120]}"
                f"{tags_str}{sup_str}"
            )

    print(f"\n--- {len(entries)} entries ---")
    return 0


def cmd_post_verified(args: argparse.Namespace) -> int:
    """Post a verified ledger entry with required evidence and confidence."""
    # Validate intel types (argparse nargs cannot enforce choices)
    # Dedup + canonicalize order (sorted) for deterministic serialization.
    raw_consumed = args.intel_types_consumed if args.intel_types_consumed else []
    raw_produced = args.intel_types_produced if args.intel_types_produced else []
    for it in raw_consumed:
        if it not in VALID_INTEL_TYPES:
            print(
                f"ERROR: Invalid --intel-types-consumed entry: {it!r} "
                f"(expected one of {sorted(VALID_INTEL_TYPES)})",
                file=sys.stderr,
            )
            return 1
    for it in raw_produced:
        if it not in VALID_INTEL_TYPES:
            print(
                f"ERROR: Invalid --intel-types-produced entry: {it!r} "
                f"(expected one of {sorted(VALID_INTEL_TYPES)})",
                file=sys.stderr,
            )
            return 1
    # Dedup + sort for canonical (deterministic) serialization order
    intel_consumed = tuple(sorted(set(raw_consumed))) if raw_consumed else ()
    intel_produced = tuple(sorted(set(raw_produced))) if raw_produced else ()
    # Validate exercise_role (bounded free-form — max 64 chars, alphanumeric + dash/underscore)
    if args.exercise_role:
        role = args.exercise_role
        if len(role) > 64 or not all(c.isalnum() or c in "-_" for c in role):
            print(
                f"ERROR: Invalid --exercise-role: {role!r} "
                f"(max 64 chars, alphanumeric + dash/underscore only)",
                file=sys.stderr,
            )
            return 1
    try:
        written = post_verified_entry(
            agent=args.agent,
            vendor=args.vendor,
            model=args.model,
            entry_type=args.type,
            scope=args.scope,
            content=args.content,
            evidence=args.evidence,
            confidence=args.confidence,
            supersedes=args.supersedes,
            tags=tuple(args.tags) if args.tags else (),
            assurance_level=args.assurance_level,
            ledger_path=args.ledger,
            claim=_build_claim(args),
            color_team=args.color_team,
            intel_types_consumed=intel_consumed,
            intel_types_produced=intel_produced,
            exercise_role=args.exercise_role,
        )
    except ValueError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1
    except OSError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1

    color_suffix = f" color_team={written.color_team}" if written.color_team else ""
    print(
        f"Posted verified: {written.id} "
        f"({written.type}/{written.scope}) evidence={written.evidence}"
        f"{color_suffix}"
    )
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    """Validate ledger integrity."""
    if getattr(args, "report", False):
        return cmd_report(args)

    valid, errors = validate_integrity(ledger_path=args.ledger)

    if errors:
        for err in errors:
            print(f"  ERROR: {err}", file=sys.stderr)
        print(f"\nValidation: {valid} valid, {len(errors)} errors")
        return 1

    print(f"Validation: {valid} entries, all OK")
    return 0


def cmd_report(args: argparse.Namespace) -> int:
    """Generate a structured CLP validation report."""
    report = validate_integrity_report(ledger_path=args.ledger)

    if getattr(args, "json", False):
        json.dump(report, sys.stdout, indent=2, default=str)
        sys.stdout.write("\n")
        return 0

    # Markdown output
    errors = report["errors"]
    by_class = errors["by_class"]
    remediation = report["remediation"]

    print(f"# CLP Validation Report\n")
    print(f"- Ledger: `{report['ledger_path']}`")
    print(f"- Total lines: {report['total_lines']}")
    print(f"- Valid entries: {report['valid_entries']}")
    print(f"- Validation errors: {errors['total']}")
    print()

    if errors['total'] == 0:
        print("All entries valid.")
        return 0

    print("## Errors by Class\n")
    for cls_name in ("signature_mismatch", "content_hash_mismatch", "parse_error", "other"):
        data = by_class.get(cls_name, {})
        count = data.get("count", 0)
        if count == 0:
            continue
        ranges = data.get("line_ranges", "")
        print(f"### {cls_name} ({count} errors)")
        if ranges:
            print(f"\n**Line ranges:** {ranges}\n")
        samples = data.get("samples", [])
        if samples:
            print("**Sample errors:**")
            for s in samples:
                print(f"- `{s}`")
            print()
        rem = remediation.get(cls_name, "")
        if rem:
            print(f"**Remediation:** {rem}\n")

    return 0


def cmd_state(args: argparse.Namespace) -> int:
    """Show current shared state."""
    state_path = args.state
    if state_path is None:
        # Default path relative to ledger
        ledger_path = args.ledger or "_state/cognition/ledger.jsonl"
        state_path = str(Path(ledger_path).parent / "state.json")

    path = Path(state_path)
    if not path.exists():
        print("No shared state file found.")
        print(f"Expected at: {path}")
        return 0

    try:
        from hummbl_cognition.models import SharedState

        data = json.loads(path.read_text(encoding="utf-8"))
        state = SharedState.from_dict(data)
    except (json.JSONDecodeError, KeyError, ValueError) as e:
        print(f"ERROR: failed to parse state: {e}", file=sys.stderr)
        return 1

    print(f"Version: {state.version}")
    print(f"Updated: {state.updated_at} by {state.updated_by}")

    if state.active_agents:
        print(f"\nActive Agents ({len(state.active_agents)}):")
        for agent_id, info in state.active_agents.items():
            status = info.get("status", "unknown")
            print(f"  {agent_id}: {status}")

    if state.claimed_files:
        print(f"\nClaimed Files ({len(state.claimed_files)}):")
        for filepath, info in state.claimed_files.items():
            agent = info.get("agent", "unknown")
            print(f"  {filepath} -> {agent}")

    if state.sprint:
        print(f"\nSprint: {state.sprint.get('name', 'unnamed')}")

    if state.flags:
        print(f"\nFlags: {json.dumps(state.flags)}")

    return 0


def cmd_boot(args: argparse.Namespace) -> int:
    """Generate boot context for agent injection."""
    cognition_dir = Path(args.ledger).parent if args.ledger else None
    content = build_boot_context(
        cognition_dir=cognition_dir,
        max_entries=args.max_entries,
        max_age_days=args.max_age_days,
    )
    try:
        print(content)
    except UnicodeEncodeError:
        sys.stdout.buffer.write(content.encode("utf-8", errors="replace") + b"\n")
    return 0


def cmd_startup(args: argparse.Namespace) -> int:
    """Generate startup context from cognition and coordination inbox."""
    cognition_dir = Path(args.ledger).parent if args.ledger else None

    if args.output:
        output_path = write_startup_context(
            args.agent,
            agent_aliases=args.agent_alias,
            cognition_dir=cognition_dir,
            bus_path=args.bus,
            output_path=args.output,
            max_entries=args.max_entries,
            max_age_days=args.max_age_days,
            max_bus_messages=args.max_bus_messages,
        )
        print(output_path)
        if args.print_context:
            print("")
            print(output_path.read_text(encoding="utf-8"))
    else:
        print(
            build_startup_context(
                args.agent,
                agent_aliases=args.agent_alias,
                cognition_dir=cognition_dir,
                bus_path=args.bus,
                max_entries=args.max_entries,
                max_age_days=args.max_age_days,
                max_bus_messages=args.max_bus_messages,
            )
        )
    return 0


def cmd_search(args: argparse.Namespace) -> int:
    """Open Brain: search across all memory pools."""
    from hummbl_cognition.retriever import OpenBrainRetriever

    retriever = OpenBrainRetriever()
    results = retriever.search(
        args.query,
        token_budget=args.budget,
        scope=args.scope,
        entry_type=args.type,
        since=args.since,
        sources=args.sources,
        agent="cli",
        limit=args.limit,
    )

    if not results:
        print("No results found.")
        return 0

    if args.json:
        for r in results:
            print(json.dumps(r.to_dict(), separators=(",", ":")))
    else:
        for i, r in enumerate(results, 1):
            source_tag = f"[{r.source}]"
            score_str = f"{r.score:.3f}"
            meta = r.metadata
            agent_str = f" ({meta.get('agent', '')})" if meta.get("agent") else ""
            ts_str = f" {meta.get('timestamp', '')[:10]}" if meta.get("timestamp") else ""
            print(f"{i:2d}. {source_tag:12s} score={score_str}{agent_str}{ts_str}")
            # Wrap content to ~80 chars
            content = r.content.replace("\n", " ")[:200]
            print(f"    {content}")
            if meta.get("tags"):
                print(f"    tags: {', '.join(meta['tags'])}")
            print()

    total_tokens = sum(r.tokens for r in results)
    print(f"--- {len(results)} results, ~{total_tokens} tokens ---")
    return 0


def cmd_batch_ingest(args: argparse.Namespace) -> int:
    """Bulk-import a JSONL file of ledger entries with deduplication."""
    source = Path(args.source)
    if not source.exists():
        print(f"ERROR: source file not found: {source}", file=sys.stderr)
        return 1

    dry_run: bool = args.dry_run

    # Build set of existing content hashes for dedup
    existing_entries = read_entries(ledger_path=args.ledger, limit=999_999)
    existing_hashes: set[str] = {e.content_hash for e in existing_entries}

    total = 0
    ingested = 0
    skipped_dup = 0
    skipped_invalid = 0

    with open(source, encoding="utf-8") as fh:
        for line_num, raw_line in enumerate(fh, 1):
            raw_line = raw_line.strip()
            if not raw_line:
                continue
            total += 1

            # Parse JSON
            try:
                data = json.loads(raw_line)
            except json.JSONDecodeError as exc:
                print(
                    f"SKIP line {line_num}: invalid JSON: {exc}",
                    file=sys.stderr,
                )
                skipped_invalid += 1
                continue

            # Build LedgerEntry from dict or via create()
            try:
                if "content_hash" in data and "id" in data and "timestamp" in data:
                    # Full entry -- use from_dict
                    entry = LedgerEntry.from_dict(data)
                else:
                    # Partial entry -- use create() to generate id/ts/hash
                    entry = LedgerEntry.create(
                        agent=data["agent"],
                        vendor=data["vendor"],
                        model=data["model"],
                        entry_type=data["type"],
                        scope=data["scope"],
                        content=data["content"],
                        evidence=data.get("evidence"),
                        confidence=data.get("confidence", 0.9),
                        supersedes=data.get("supersedes"),
                        tags=tuple(data.get("tags", [])),
                        assurance_level=data.get("assurance_level"),
                        links=tuple(data.get("links", [])),
                    )
            except (KeyError, ValueError, TypeError) as exc:
                print(
                    f"SKIP line {line_num}: validation error: {exc}",
                    file=sys.stderr,
                )
                skipped_invalid += 1
                continue

            # Dedup check
            if entry.content_hash in existing_hashes:
                skipped_dup += 1
                continue

            if dry_run:
                # PII pre-scan: report PII in dry-run so authors can fix before real ingest
                pii_hits = scan_pii(entry.content)
                if pii_hits:
                    pii_types = ", ".join(t for t, _ in pii_hits)
                    print(
                        f"PII line {line_num}: {pii_types} in content",
                        file=sys.stderr,
                    )
                ingested += 1
                existing_hashes.add(entry.content_hash)
                continue

            # Write
            try:
                post_entry(entry, ledger_path=args.ledger)
                existing_hashes.add(entry.content_hash)
                ingested += 1
            except (ValueError, OSError) as exc:
                print(
                    f"SKIP line {line_num}: write error: {exc}",
                    file=sys.stderr,
                )
                skipped_invalid += 1

    prefix = "[DRY RUN] " if dry_run else ""
    print(
        f"{prefix}Ingested {ingested}/{total} entries "
        f"({skipped_dup} skipped: already present, "
        f"{skipped_invalid} skipped: invalid)"
    )
    return 0


def cmd_reindex(args: argparse.Namespace) -> int:
    """Rebuild the Open Brain search index."""
    from hummbl_cognition.indexer import BM25Index

    index = BM25Index()
    count = index.build(ledger_path=args.ledger)
    path = index.save()
    print(f"Indexed {count} entries -> {path}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser."""
    parser = argparse.ArgumentParser(
        prog="python -m hummbl_cognition",
        description="Cognitive Ledger Protocol -- vendor-agnostic shared agent memory",
    )
    parser.add_argument(
        "--ledger",
        help="Override ledger file path",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # post
    p_post = subparsers.add_parser("post", help="Write a new ledger entry")
    p_post.add_argument("--agent", required=True, help="Agent identifier")
    p_post.add_argument(
        "--vendor",
        required=True,
        choices=sorted(VALID_VENDORS),
        help="Vendor identifier",
    )
    p_post.add_argument("--model", required=True, help="Model identifier")
    p_post.add_argument(
        "--type",
        required=True,
        choices=[entry_type.value for entry_type in LedgerEntryType if entry_type.value in CANONICAL_LEDGER_TYPES],
        help="Entry type (canonical only; historical aliases rejected for new writes)",
    )
    p_post.add_argument(
        "--scope",
        required=True,
        choices=[scope.value for scope in LedgerScope if scope.value in CANONICAL_LEDGER_SCOPES],
        help="Entry scope (canonical only; historical aliases rejected for new writes)",
    )
    p_post.add_argument("--content", required=True, help="Knowledge content")
    p_post.add_argument("--evidence", help="Link to supporting artifact")
    p_post.add_argument(
        "--confidence", type=float, default=0.9, help="Confidence 0.0-1.0"
    )
    p_post.add_argument("--supersedes", help="ID of entry to correct")
    p_post.add_argument("--tags", nargs="*", default=[], help="Tags")
    p_post.add_argument(
        "--assurance-level",
        choices=["SELF", "PEER", "VERIFIED"],
        help="Trust level",
    )
    p_post.add_argument(
        "--claim-status",
        choices=["observed", "hypothesized", "supported", "contested", "falsified", "deprecated", "canonical"],
        help="Epistemic status for the claim (ADR-FM-048)",
    )
    p_post.add_argument(
        "--expires",
        help="ISO 8601 expiration for the claim (ADR-FM-048)",
    )
    p_post.add_argument(
        "--supersedes-entry",
        help="CLP ID of entry superseded by this claim (ADR-FM-048)",
    )

    # query
    p_query = subparsers.add_parser("query", help="Query ledger entries")
    p_query.add_argument("--since", help="ISO 8601 timestamp filter")
    p_query.add_argument(
        "--type",
        choices=[e.value for e in LedgerEntryType],
        help="Filter by type",
    )
    p_query.add_argument(
        "--scope",
        choices=[e.value for e in LedgerScope],
        help="Filter by scope",
    )
    p_query.add_argument("--agent", help="Filter by agent (substring)")
    p_query.add_argument("--tags", nargs="*", help="Filter by tags (all must match)")
    p_query.add_argument("--limit", type=int, default=20, help="Max entries")
    p_query.add_argument("--json", action="store_true", help="Output as JSONL")

    # post-verified
    p_post_verified = subparsers.add_parser(
        "post-verified",
        help="Write a verified ledger entry with evidence + confidence",
    )
    p_post_verified.add_argument("--agent", help="Agent identifier or COGNITION_AGENT")
    p_post_verified.add_argument(
        "--vendor",
        choices=sorted(VALID_VENDORS),
        help="Vendor identifier or COGNITION_VENDOR",
    )
    p_post_verified.add_argument(
        "--model",
        help="Model identifier or COGNITION_MODEL",
    )
    p_post_verified.add_argument(
        "--type",
        required=True,
        choices=[entry_type.value for entry_type in LedgerEntryType if entry_type.value in CANONICAL_LEDGER_TYPES],
        help="Entry type (canonical only; historical aliases rejected for new writes)",
    )
    p_post_verified.add_argument(
        "--scope",
        required=True,
        choices=[scope.value for scope in LedgerScope if scope.value in CANONICAL_LEDGER_SCOPES],
        help="Entry scope (canonical only; historical aliases rejected for new writes)",
    )
    p_post_verified.add_argument("--content", required=True, help="Knowledge content")
    p_post_verified.add_argument(
        "--evidence",
        required=True,
        help="Supporting artifact or verification receipt",
    )
    p_post_verified.add_argument(
        "--confidence",
        required=True,
        type=float,
        help="Explicit confidence 0.0-1.0",
    )
    p_post_verified.add_argument("--supersedes", help="ID of entry to correct")
    p_post_verified.add_argument("--tags", nargs="*", default=[], help="Tags")
    p_post_verified.add_argument(
        "--assurance-level",
        choices=["SELF", "PEER", "VERIFIED"],
        help="Trust level",
    )
    p_post_verified.add_argument(
        "--claim-status",
        choices=["observed", "hypothesized", "supported", "contested", "falsified", "deprecated", "canonical"],
        help="Epistemic status for the claim (ADR-FM-048)",
    )
    p_post_verified.add_argument(
        "--expires",
        help="ISO 8601 expiration for the claim (ADR-FM-048)",
    )
    p_post_verified.add_argument(
        "--supersedes-entry",
        help="CLP ID of entry superseded by this claim (ADR-FM-048)",
    )
    # Color team extension (v1.1.0)
    p_post_verified.add_argument(
        "--color-team",
        choices=sorted(VALID_COLOR_TEAMS),
        default=None,
        help="Security exercise color team attribution (e.g., 'red', 'lavender', 'amber')",
    )
    p_post_verified.add_argument(
        "--intel-types-consumed",
        nargs="+",
        default=[],
        help="INT types consumed during exercise (e.g., CYBINT TECHINT CODEINT). At least one value required when flag is used.",
    )
    p_post_verified.add_argument(
        "--intel-types-produced",
        nargs="+",
        default=[],
        help="INT types produced as findings (e.g., CYBINT TECHINT). At least one value required when flag is used.",
    )
    p_post_verified.add_argument(
        "--exercise-role",
        default=None,
        help="Role from color registry (e.g., 'offense', 'defense', 'referee')",
    )

    # search (Open Brain)
    p_search = subparsers.add_parser(
        "search", help="Open Brain: semantic search across all memory pools"
    )
    p_search.add_argument("query", help="Search query (natural language)")
    p_search.add_argument(
        "--budget", type=int, default=2000, help="Token budget for results"
    )
    p_search.add_argument(
        "--scope",
        choices=[e.value for e in LedgerScope],
        help="Filter by scope",
    )
    p_search.add_argument(
        "--type",
        choices=[e.value for e in LedgerEntryType],
        help="Filter by type",
    )
    p_search.add_argument("--since", help="ISO 8601 timestamp filter")
    p_search.add_argument("--limit", type=int, default=20, help="Max results")
    p_search.add_argument(
        "--sources",
        nargs="*",
        choices=["ledger", "bus", "briefings", "findings", "memory_md"],
        help="Memory pools to search (default: all)",
    )
    p_search.add_argument("--json", action="store_true", help="Output as JSON")

    # batch-ingest
    p_batch = subparsers.add_parser(
        "batch-ingest",
        help="Bulk-import JSONL file of ledger entries with dedup",
    )
    p_batch.add_argument(
        "source",
        help="Path to JSONL file containing ledger entries",
    )
    p_batch.add_argument(
        "--dry-run",
        action="store_true",
        help="Parse, validate, and PII-scan without writing to ledger",
    )

    # reindex (Open Brain)
    subparsers.add_parser("reindex", help="Rebuild the Open Brain search index")

    # validate
    p_validate = subparsers.add_parser("validate", help="Validate ledger integrity")
    p_validate.add_argument("--report", action="store_true", help="Generate structured report")

    # report
    p_report = subparsers.add_parser("report", help="Generate structured CLP validation report (JSON/Markdown)")
    p_report.add_argument("--json", action="store_true", help="Output as JSON instead of Markdown")

    # state & status alias
    p_state = subparsers.add_parser("state", help="Show shared state")
    p_state.add_argument("--state", help="Override state.json path")
    p_status = subparsers.add_parser("status", help="Show shared state (alias for state)")
    p_status.add_argument("--state", help="Override state.json path")

    # boot
    p_boot = subparsers.add_parser("boot", help="Generate boot context")
    p_boot.add_argument(
        "--boot-limit",
        "--max-entries",
        dest="max_entries",
        type=int,
        default=20,
        help="Max ledger entries in boot context",
    )
    p_boot.add_argument(
        "--max-age-days",
        type=int,
        default=14,
        help="Only include ledger entries newer than this many days",
    )

    # belonging-check (HRSI Gap 1)
    subparsers.add_parser(
        "belonging-check",
        help="HRSI Gap 1 — daily belonging baseline (safety/mattering/connection)",
        add_help=False,  # belonging_check.run_cli handles its own --help
    )

    # hrsi-checkin (HRSI Gap 2)
    subparsers.add_parser(
        "hrsi-checkin",
        help="HRSI Gap 2 — unified daily cycle (cogstate+belonging+HULE+lens+delta)",
        add_help=False,  # hrsi_checkin.run_cli handles its own --help
    )

    # startup
    p_startup = subparsers.add_parser(
        "startup",
        help="Generate startup context with cognition plus recent inbox",
    )
    p_startup.add_argument("--agent", required=True, help="Agent identifier")
    p_startup.add_argument(
        "--agent-alias",
        action="append",
        default=[],
        help="Optional additional bus target token for this agent",
    )
    p_startup.add_argument(
        "--max-entries",
        type=int,
        default=20,
        help="Max ledger entries in startup context",
    )
    p_startup.add_argument(
        "--max-age-days",
        type=int,
        default=14,
        help="Only include ledger entries newer than this many days",
    )
    p_startup.add_argument(
        "--max-bus-messages",
        type=int,
        default=5,
        help="Max recent coordination messages to include",
    )
    p_startup.add_argument(
        "--bus",
        help="Override coordination bus path",
    )
    p_startup.add_argument(
        "--output",
        help="Write startup context to this file and print the path",
    )
    p_startup.add_argument(
        "--print-context",
        action="store_true",
        help="When used with --output, also print the rendered context",
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""
    parser = build_parser()
    args, _ = parser.parse_known_args(argv)

    if not args.command:
        parser.print_help()
        return 2

    if args.command == "belonging-check":
        from hummbl_cognition.belonging_check import run_cli as bc_run_cli
        # Pass remaining argv after the subcommand
        idx = (argv or sys.argv[1:]).index("belonging-check") + 1
        remaining = (argv or sys.argv[1:])[idx:]
        return bc_run_cli(remaining)

    if args.command == "hrsi-checkin":
        from hummbl_cognition.hrsi_checkin import run_cli as hc_run_cli
        idx = (argv or sys.argv[1:]).index("hrsi-checkin") + 1
        remaining = (argv or sys.argv[1:])[idx:]
        return hc_run_cli(remaining)

    handlers = {
        "post": cmd_post,
        "post-verified": cmd_post_verified,
        "query": cmd_query,
        "search": cmd_search,
        "reindex": cmd_reindex,
        "validate": cmd_validate,
        "state": cmd_state,
        "status": cmd_state,
        "boot": cmd_boot,
        "startup": cmd_startup,
        "batch-ingest": cmd_batch_ingest,
        "report": cmd_report,
    }

    handler = handlers.get(args.command)
    if handler is None:
        parser.print_help()
        return 2

    return handler(args)


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
