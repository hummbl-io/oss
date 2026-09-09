"""Local stdio MCP server for hummbl-gitops.

Exposes the gitops loop as JSON-RPC tools via the Model Context Protocol.
Transport: local stdio (no network, no port). This is the MVP transport.

Future: remote MCP server over HTTP for fleet-wide tool access. The tool
schema will be identical; only the transport changes.

Tools (8):
    pre_push_check     — Run local CI + agent review before push
    pre_pr_gate        — Check branch readiness before PR creation
    claim_review       — Claim a review aspect on a PR
    review_coverage    — Query coverage matrix for a PR
    watch_ci           — Start/stop CI watching for a PR
    check_main_moved   — Check if origin/main advanced
    sync_receipts      — Pull and verify CI receipts
    auto_rebase        — Rebase stale branches
"""

from __future__ import annotations

import json
import sys
from typing import Any, Optional


# --- Tool definitions ---

TOOLS = [
    {
        "name": "pre_push_check",
        "description": (
            "Run CI contract locally before push. Scopes checks to the diff. "
            "Returns per-check results (pass/fail) and overall verdict."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "repo": {"type": "string", "description": "Path to target repo", "default": "."},
                "full_contract": {
                    "type": "boolean",
                    "description": "Run all checks including install-smoke and arbiter",
                    "default": False,
                },
            },
        },
    },
    {
        "name": "pre_pr_gate",
        "description": (
            "Check branch readiness before PR creation. Verifies branch freshness, "
            "conflict risk, scope, and PR metadata."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "repo": {"type": "string", "default": "."},
                "branch": {"type": "string", "description": "Branch to check"},
            },
        },
    },
    {
        "name": "claim_review",
        "description": (
            "Claim a review aspect on a PR to prevent duplicate work. "
            "Aspects: security, logic, tests, docs, style, ci, performance, breaking."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "pr": {"type": "integer", "description": "PR number"},
                "aspect": {"type": "string", "description": "Review aspect to claim"},
                "agent": {"type": "string", "description": "Agent name", "default": "devin"},
            },
            "required": ["pr", "aspect"],
        },
    },
    {
        "name": "review_coverage",
        "description": "Query the review coverage matrix for a PR. Shows which aspects have been reviewed.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "pr": {"type": "integer", "description": "PR number"},
            },
            "required": ["pr"],
        },
    },
    {
        "name": "watch_ci",
        "description": (
            "Watch CI status for a PR. Polls at the given interval and returns "
            "when CI completes (pass or fail). Posts CI_COMPLETED to bus."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "pr": {"type": "integer", "description": "PR number (0 for all open PRs)"},
                "interval": {"type": "integer", "description": "Poll interval in seconds", "default": 60},
                "max_polls": {"type": "integer", "description": "Max poll cycles", "default": 10},
            },
        },
    },
    {
        "name": "check_main_moved",
        "description": "Check if origin/main advanced relative to local. Reports stale branches.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "repo": {"type": "string", "default": "."},
            },
        },
    },
    {
        "name": "sync_receipts",
        "description": (
            "Pull CI receipts and verify them. Loose mode (default) stores receipts "
            "and posts RECEIPT_VERIFIED. Tight mode (requires [governance] extra) "
            "verifies against K11 receipt integrity monitor."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "repo": {"type": "string", "default": "."},
                "pr": {"type": "integer", "description": "Specific PR (default: all recent)"},
                "tight": {"type": "boolean", "default": False},
            },
        },
    },
    {
        "name": "auto_rebase",
        "description": (
            "Detect stale branches and optionally rebase. Without --execute, reports "
            "which branches can be cleanly rebased. With --execute, performs the rebase."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "repo": {"type": "string", "default": "."},
                "branch": {"type": "string", "description": "Specific branch"},
                "execute": {"type": "boolean", "default": False},
            },
        },
    },
]


def handle_tool_call(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    """Handle a single tool call and return the result."""
    if name == "pre_push_check":
        from hummbl_gitops.forward.local_ci import run_local_ci
        from pathlib import Path

        result = run_local_ci(
            Path(arguments.get("repo", ".")),
            full_contract=arguments.get("full_contract", False),
        )
        return {"content": [{"type": "text", "text": result.summary()}]}

    elif name == "watch_ci":
        from hummbl_gitops.return_.ci_watcher import get_open_pr_numbers, watch_prs

        pr = arguments.get("pr", 0)
        pr_numbers = [pr] if pr > 0 else get_open_pr_numbers()
        if not pr_numbers:
            return {"content": [{"type": "text", "text": "No open PRs to watch."}]}

        results = watch_prs(
            pr_numbers=pr_numbers,
            interval_seconds=arguments.get("interval", 60),
            max_polls=arguments.get("max_polls", 10),
        )
        if not results:
            return {"content": [{"type": "text", "text": "No CI completions detected."}]}
        lines = [r.completion.to_bus_message() for r in results if r.completion]
        return {"content": [{"type": "text", "text": "\n".join(lines)}]}

    elif name == "check_main_moved":
        from hummbl_gitops.return_.main_moved import check_main_moved
        from pathlib import Path

        result = check_main_moved(Path(arguments.get("repo", ".")))
        if result is None:
            return {"content": [{"type": "text", "text": "No remote tracking branch found."}]}
        return {"content": [{"type": "text", "text": result.to_bus_message()}]}

    elif name == "auto_rebase":
        from hummbl_gitops.return_.auto_rebase import check_stale_branches
        from pathlib import Path

        stale = check_stale_branches(Path(arguments.get("repo", ".")))
        if not stale:
            return {"content": [{"type": "text", "text": "No stale branches."}]}
        lines = [f"{b.branch}: behind={b.behind} can_rebase={b.can_rebase}" for b in stale]
        return {"content": [{"type": "text", "text": "\n".join(lines)}]}

    elif name == "claim_review":
        from hummbl_gitops.protocol import REVIEW_ASPECTS, ReviewClaim, validate_aspect
        from hummbl_gitops.remote.coverage_matrix import record_review

        aspect = arguments.get("aspect", "")
        if not validate_aspect(aspect):
            return {
                "content": [{
                    "type": "text",
                    "text": f"Invalid aspect: {aspect}. Valid: {', '.join(sorted(REVIEW_ASPECTS))}",
                }],
                "isError": True,
            }
        agent = arguments.get("agent", "devin")
        claim = ReviewClaim(
            pr_number=arguments["pr"],
            aspect=aspect,
            agent=agent,
            host="unknown",
        )
        # Persist the claim in the coverage matrix
        record_review(arguments["pr"], agent, aspect)
        return {"content": [{"type": "text", "text": claim.to_bus_message()}]}

    elif name == "review_coverage":
        from hummbl_gitops.remote.coverage_matrix import get_coverage

        coverage = get_coverage(arguments["pr"])
        return {"content": [{"type": "text", "text": coverage.summary()}]}

    elif name == "sync_receipts":
        from hummbl_gitops.return_.receipt_sync import sync_receipts
        from pathlib import Path

        result = sync_receipts(
            Path(arguments.get("repo", ".")),
            pr_number=arguments.get("pr"),
            tight=arguments.get("tight", False),
        )
        return {"content": [{"type": "text", "text": result.summary()}]}

    elif name == "pre_pr_gate":
        return {"content": [{"type": "text", "text": "pre_pr_gate: not yet implemented (Phase 2)"}]}

    else:
        return {"content": [{"type": "text", "text": f"Unknown tool: {name}"}], "isError": True}


def serve_stdio() -> None:
    """Serve MCP over stdio. Reads JSON-RPC from stdin, writes to stdout.

    This is a minimal stdio loop implementing the MCP protocol.
    For production use, consider using the `mcp` Python package.
    """
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue

        try:
            request = json.loads(line)
        except json.JSONDecodeError:
            response = {"jsonrpc": "2.0", "error": {"code": -32700, "message": "Parse error"}}
            sys.stdout.write(json.dumps(response) + "\n")
            sys.stdout.flush()
            continue

        method = request.get("method", "")
        req_id = request.get("id")
        params = request.get("params", {})

        if method == "initialize":
            response = {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": "hummbl-gitops", "version": "0.0.1"},
                },
            }
        elif method == "tools/list":
            response = {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {"tools": TOOLS},
            }
        elif method == "tools/call":
            tool_name = params.get("name", "")
            tool_args = params.get("arguments", {})
            try:
                result = handle_tool_call(tool_name, tool_args)
                response = {"jsonrpc": "2.0", "id": req_id, "result": result}
            except Exception as e:
                response = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {"code": -32603, "message": str(e)},
                }
        elif method == "shutdown":
            response = {"jsonrpc": "2.0", "id": req_id, "result": {}}
            sys.stdout.write(json.dumps(response) + "\n")
            sys.stdout.flush()
            break
        else:
            response = {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32601, "message": f"Method not found: {method}"},
            }

        sys.stdout.write(json.dumps(response) + "\n")
        sys.stdout.flush()


def main() -> int:
    """Entry point for hummbl-gitops-mcp."""
    serve_stdio()
    return 0


if __name__ == "__main__":
    sys.exit(main())
