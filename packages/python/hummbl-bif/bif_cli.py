#!/usr/bin/env python3
"""BIF CLI — command-line interface for the Batch Ingestion Framework.

Wraps the 5 MCP tool functions as argparse subcommands.
Zero third-party dependencies (stdlib only).

Usage:
    bif start <domain> [--batches N]
    bif status [session_id]
    bif template <phase> <batch>
    bif validate <file>
    bif templates
"""

import argparse
import json
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Import tool functions from mcp_server at repo root
# ---------------------------------------------------------------------------
_REPO_ROOT = Path(__file__).parent
sys.path.insert(0, str(_REPO_ROOT))

from mcp_server import (  # noqa: E402
    tool_bif_start_session,
    tool_bif_get_template,
    tool_bif_validate_batch,
    tool_bif_session_status,
    tool_bif_list_templates,
)


# ---------------------------------------------------------------------------
# Output helpers
# ---------------------------------------------------------------------------
def _die(msg: str) -> None:
    print(f"Error: {msg}", file=sys.stderr)
    sys.exit(1)


def _check_error(result: dict) -> None:
    if isinstance(result, dict) and "error" in result:
        _die(result["error"])


# ---------------------------------------------------------------------------
# Subcommand handlers
# ---------------------------------------------------------------------------
def cmd_start(args: argparse.Namespace) -> None:
    """bif start <domain> [--batches N]"""
    arguments: dict = {"domain": args.domain}
    if args.batches is not None:
        arguments["target_batches"] = args.batches

    result = tool_bif_start_session(arguments)
    _check_error(result)

    print(f"Session ID  : {result['session_id']}")
    print(f"Domain      : {result['domain']}")
    print(f"Target batch: {result['target_batches']}")
    print()
    print(result["phase_1_prompt"])
    print()
    print("Pre-ingestion checklist:")
    for i, item in enumerate(result.get("pre_ingestion_checklist", []), 1):
        print(f"  {i:2d}. {item}")


def cmd_status(args: argparse.Namespace) -> None:
    """bif status [session_id]"""
    arguments: dict = {}
    if args.session_id:
        arguments["session_id"] = args.session_id

    result = tool_bif_session_status(arguments)
    _check_error(result)

    if "sessions" in result:
        # List all sessions
        sessions = result["sessions"]
        count = result["count"]
        print(f"BIF Sessions ({count} total)")
        print("-" * 60)
        if not sessions:
            print("  No sessions found.")
            return
        print(f"  {'Session ID':<12}  {'Domain':<30}  {'Progress'}")
        print(f"  {'-'*12}  {'-'*30}  {'-'*10}")
        for s in sessions:
            progress = f"{s['completed']}/{s['target']}"
            print(f"  {s['session_id']:<12}  {s['domain']:<30}  {progress}")
    else:
        # Single session status
        print(f"Session     : {result['session_id']}")
        print(f"Domain      : {result['domain']}")
        print(f"Progress    : {result['completion']} ({result['percentage']}%)")
        print()
        print("Phase coverage:")
        for phase_name, cov in result.get("phase_coverage", {}).items():
            status = "DONE" if cov["exit_met"] else f"{cov['completed']}/{cov['total']}"
            remaining = cov["remaining"]
            rem_str = f"  remaining: {remaining}" if remaining else ""
            print(f"  {phase_name:<14} {status}{rem_str}")
        nb = result.get("next_batch")
        if nb:
            print()
            print(f"Next batch  : #{nb['batch_number']} — {nb['name']} (Phase {nb['phase']}: {nb['phase_name']})")
            print(f"Objective   : {nb['what_to_capture']}")


def cmd_template(args: argparse.Namespace) -> None:
    """bif template <phase> <batch>"""
    arguments = {"phase": args.phase, "batch_number": args.batch}

    result = tool_bif_get_template(arguments)
    _check_error(result)

    print(f"Phase {result['phase']}: {result['phase_name']} — {result['phase_description']}")
    print(f"Batch {result['batch_number']}: {result['batch_name']}")
    print(f"Priority    : {result['priority']}")
    print(f"File naming : {result['file_naming']}")
    print()
    print(result["prompt"])


def cmd_validate(args: argparse.Namespace) -> None:
    """bif validate <file>"""
    path = Path(args.file)
    if not path.exists():
        _die(f"File not found: {path}")

    content = path.read_text()
    arguments: dict = {"batch_content": content}

    result = tool_bif_validate_batch(arguments)
    _check_error(result)

    overall = result["overall"]
    score = result["score"]
    print(f"Result      : {overall}  ({score} checks passed)")
    print()
    print("Check details:")
    for check in result.get("checks", []):
        symbol = "PASS" if check["passed"] else "FAIL"
        print(f"  [{symbol}] {check['check']:<20} {check['detail']}")

    gaps = result.get("gaps", [])
    if gaps:
        print()
        print("Gaps to fix:")
        for gap in gaps:
            print(f"  - {gap}")


def cmd_templates(args: argparse.Namespace) -> None:  # noqa: ARG001
    """bif templates"""
    result = tool_bif_list_templates({})
    _check_error(result)

    templates = result.get("templates", [])
    print(f"Available domain templates ({len(templates)} found)")
    print("-" * 60)
    for tmpl in templates:
        tid = tmpl["template_id"]
        desc = tmpl["description"] or "(no description)"
        batches = tmpl.get("batch_count", 0)
        print(f"  {tid:<20}  batches: {batches:<4}  {desc}")


# ---------------------------------------------------------------------------
# Argument parser
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="bif",
        description="Batch Ingestion Framework CLI",
    )
    sub = parser.add_subparsers(dest="command", metavar="command")
    sub.required = True

    # start
    p_start = sub.add_parser("start", help="Start a new ingestion session")
    p_start.add_argument("domain", help="Domain to ingest (e.g. 'Anthropic')")
    p_start.add_argument("--batches", type=int, default=None,
                         dest="batches", metavar="N",
                         help="Target number of batches (default: 10)")

    # status
    p_status = sub.add_parser("status", help="Show session progress")
    p_status.add_argument("session_id", nargs="?", default=None,
                          help="Session ID (omit to list all sessions)")

    # template
    p_template = sub.add_parser("template", help="Get the prompt for a phase/batch")
    p_template.add_argument("phase", type=int, help="Phase number (1-4)")
    p_template.add_argument("batch", type=int, help="Batch number (1-15)")

    # validate
    p_validate = sub.add_parser("validate", help="Validate a batch markdown file")
    p_validate.add_argument("file", help="Path to the markdown file to validate")

    # templates
    sub.add_parser("templates", help="List available domain templates")

    return parser


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def main() -> None:
    # Support BIF_SESSIONS_DIR override for test isolation (applied before any
    # tool function is called so SESSIONS_DIR in mcp_server reflects it).
    import os
    _env_sessions = os.environ.get("BIF_SESSIONS_DIR")
    if _env_sessions:
        import mcp_server as _mcp
        _mcp.SESSIONS_DIR = Path(_env_sessions)

    parser = build_parser()
    args = parser.parse_args()

    dispatch = {
        "start": cmd_start,
        "status": cmd_status,
        "template": cmd_template,
        "validate": cmd_validate,
        "templates": cmd_templates,
    }
    handler = dispatch.get(args.command)
    if handler is None:
        parser.print_help()
        sys.exit(1)
    handler(args)


if __name__ == "__main__":
    main()
