"""CLI entry point for hummbl-gitops.

Usage:
    hummbl-gitops pre-push [--repo .] [--full-contract]
    hummbl-gitops ci-watch [--pr <n>] [--interval 60] [--max-polls <n>] [--repo <owner/repo>]
    hummbl-gitops main-moved [--repo .]
    hummbl-gitops auto-rebase [--repo .] [--branch <name>] [--execute]
    hummbl-gitops receipt-sync [--repo .] [--pr <n>]
    hummbl-gitops review-claim <pr> [--aspect <aspect>] [--agent <name>]
    hummbl-gitops review-coverage <pr>
    hummbl-gitops meta-review <pr>
    hummbl-gitops adaptive-ci [--repo .] [--diff <ref>]
"""

from __future__ import annotations

import argparse
import os
import socket
import sys
from pathlib import Path
from typing import Optional


def _resolve_host() -> str:
    """Resolve canonical host tag from the live machine."""
    machine_id = os.environ.get("MACHINE_ID", "")
    if machine_id:
        return machine_id
    return socket.gethostname()


def cmd_pre_push(args: argparse.Namespace) -> int:
    """Run CI contract locally before push."""
    from hummbl_gitops.forward.local_ci import run_local_ci

    repo = Path(args.repo).resolve()
    result = run_local_ci(
        repo, full_contract=args.full_contract, head=getattr(args, "head", None)
    )
    print(result.summary())
    return 0 if result.required_passed else 1


def cmd_ci_watch(args: argparse.Namespace) -> int:
    """Watch CI status for PRs, post to bus on completion."""
    from hummbl_gitops.return_.ci_watcher import get_open_pr_numbers, watch_prs
    from hummbl_gitops.protocol import CI_COMPLETED

    host = _resolve_host()

    if args.pr:
        pr_numbers = [args.pr]
    else:
        pr_numbers = get_open_pr_numbers(repo=args.repo)
        if not pr_numbers:
            print("No open PRs to watch.")
            return 0

    print(f"Watching CI for PRs: {', '.join(str(n) for n in pr_numbers)}")
    print(f"Interval: {args.interval}s, Max polls: {args.max_polls or 'infinite'}")

    def on_completion(completion):
        msg = completion.to_bus_message()
        print(f"[CI_COMPLETED] {msg}")
        # Bus post is handled by the caller (agent or skill), not the CLI directly.
        # The CLI prints the message; the skill layer posts it to the bus.

    results = watch_prs(
        pr_numbers=pr_numbers,
        interval_seconds=args.interval,
        max_polls=args.max_polls,
        repo=args.repo,
        host=host,
        on_completion=on_completion,
    )

    if not results:
        print("No CI completions detected during watch window.")
    return 0


def cmd_main_moved(args: argparse.Namespace) -> int:
    """Check if origin/main advanced relative to local."""
    from hummbl_gitops.return_.main_moved import check_main_moved

    repo = Path(args.repo).resolve()
    host = _resolve_host()
    result = check_main_moved(repo, host=host)
    if result is None:
        print("No remote tracking branch found.")
        return 0
    print(result.to_bus_message())
    return 0 if not result.stale_branches else 0  # awareness-only, not an error


def cmd_auto_rebase(args: argparse.Namespace) -> int:
    """Detect stale branches and optionally rebase."""
    from hummbl_gitops.return_.auto_rebase import check_stale_branches, rebase_branch

    repo = Path(args.repo).resolve()
    host = _resolve_host()
    stale = check_stale_branches(repo, host=host)

    if not stale:
        print("No stale branches.")
        return 0

    for branch_info in stale:
        if args.branch and branch_info.branch != args.branch:
            continue
        if branch_info.can_rebase:
            if args.execute:
                print(f"Rebasing {branch_info.branch}...")
                success = rebase_branch(repo, branch_info.branch)
                if success:
                    print(f"  REBASE_DONE: {branch_info.branch}")
                else:
                    print(f"  REBASE_FAILED: {branch_info.branch}")
                    return 1
            else:
                print(f"  REBASE_AVAILABLE: {branch_info.branch} (behind {branch_info.behind})")
        else:
            print(f"  REBASE_CONFLICTS: {branch_info.branch} (behind {branch_info.behind})")

    if not args.execute:
        print("\nUse --execute to rebase clean branches.")
    return 0


def cmd_receipt_sync(args: argparse.Namespace) -> int:
    """Pull and verify CI receipts (loose mode for MVP)."""
    from hummbl_gitops.return_.receipt_sync import sync_receipts

    repo = Path(args.repo).resolve()
    host = _resolve_host()
    result = sync_receipts(repo, pr_number=args.pr, host=host, tight=False)
    print(result.summary())
    return 0 if result.verified else 1


def cmd_review_claim(args: argparse.Namespace) -> int:
    """Claim a review aspect on a PR."""
    from hummbl_gitops.protocol import REVIEW_ASPECTS, ReviewClaim, validate_aspect
    from hummbl_gitops.remote.coverage_matrix import record_review

    if not validate_aspect(args.aspect):
        print(f"Invalid aspect: {args.aspect}")
        print(f"Valid aspects: {', '.join(sorted(REVIEW_ASPECTS))}")
        return 1

    host = _resolve_host()
    agent = args.agent or "devin"
    claim = ReviewClaim(
        pr_number=args.pr,
        aspect=args.aspect,
        agent=agent,
        host=host,
    )
    # Record the claim in the coverage matrix
    record_review(args.pr, agent, args.aspect)
    print(f"[REVIEW_CLAIMED] {claim.to_bus_message()}")
    return 0


def cmd_review_coverage(args: argparse.Namespace) -> int:
    """Show review coverage matrix for a PR."""
    from hummbl_gitops.remote.coverage_matrix import get_coverage

    coverage = get_coverage(args.pr)
    print(coverage.summary())
    return 0


def cmd_meta_review(args: argparse.Namespace) -> int:
    """Coordinate review-of-review for a PR."""
    print(f"[meta-review] PR #{args.pr} — not yet implemented (Phase 4)")
    return 0


def cmd_adaptive_ci(args: argparse.Namespace) -> int:
    """Scope CI contract to diff type."""
    print("[adaptive-ci] — not yet implemented (Phase 4)")
    return 0


def cmd_doctor(args: argparse.Namespace) -> int:
    """Verify hummbl-gitops environment health."""
    from hummbl_gitops.doctor import run_doctor
    from pathlib import Path

    repo = Path(args.repo) if args.repo != "." else None
    result = run_doctor(repo)
    print(result.summary())
    return 0 if result.all_passed else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="hummbl-gitops",
        description="Bidirectional multi-agent peer-review GitOps loop",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # pre-push
    pp = sub.add_parser("pre-push", help="Run CI contract locally before push")
    pp.add_argument("--repo", default=".", help="Path to target repo")
    pp.add_argument("--full-contract", action="store_true", help="Run all checks including expensive ones")
    pp.add_argument("--head", default=None, help="Commit being pushed (from git pre-push hook stdin)")
    pp.set_defaults(func=cmd_pre_push)

    # ci-watch
    cw = sub.add_parser("ci-watch", help="Watch CI status, post on completion")
    cw.add_argument("--pr", type=int, help="Specific PR to watch (default: all open PRs)")
    cw.add_argument("--interval", type=int, default=60, help="Poll interval in seconds")
    cw.add_argument("--max-polls", type=int, default=None, help="Max poll cycles (default: infinite)")
    cw.add_argument("--repo", default=None, help="Repo (owner/repo) for gh CLI")
    cw.set_defaults(func=cmd_ci_watch)

    # main-moved
    mm = sub.add_parser("main-moved", help="Check if origin/main advanced")
    mm.add_argument("--repo", default=".", help="Path to target repo")
    mm.set_defaults(func=cmd_main_moved)

    # auto-rebase
    ar = sub.add_parser("auto-rebase", help="Detect and optionally rebase stale branches")
    ar.add_argument("--repo", default=".", help="Path to target repo")
    ar.add_argument("--branch", default=None, help="Specific branch to rebase")
    ar.add_argument("--execute", action="store_true", help="Execute rebase (default: dry-run)")
    ar.set_defaults(func=cmd_auto_rebase)

    # receipt-sync
    rs = sub.add_parser("receipt-sync", help="Pull and verify CI receipts")
    rs.add_argument("--repo", default=".", help="Path to target repo")
    rs.add_argument("--pr", type=int, default=None, help="Specific PR")
    rs.set_defaults(func=cmd_receipt_sync)

    # review-claim
    rc = sub.add_parser("review-claim", help="Claim a review aspect on a PR")
    rc.add_argument("pr", type=int, help="PR number")
    rc.add_argument("--aspect", required=True, help="Review aspect (security, logic, tests, etc.)")
    rc.add_argument("--agent", default=None, help="Agent name (default: devin)")
    rc.set_defaults(func=cmd_review_claim)

    # review-coverage
    rco = sub.add_parser("review-coverage", help="Show review coverage matrix for a PR")
    rco.add_argument("pr", type=int, help="PR number")
    rco.set_defaults(func=cmd_review_coverage)

    # meta-review
    mr = sub.add_parser("meta-review", help="Coordinate review-of-review")
    mr.add_argument("pr", type=int, help="PR number")
    mr.set_defaults(func=cmd_meta_review)

    # adaptive-ci
    ac = sub.add_parser("adaptive-ci", help="Scope CI contract to diff type")
    ac.add_argument("--repo", default=".", help="Path to target repo")
    ac.add_argument("--diff", default=None, help="Diff ref (default: origin/main..HEAD)")
    ac.set_defaults(func=cmd_adaptive_ci)

    # doctor
    dr = sub.add_parser("doctor", help="Verify hummbl-gitops environment health")
    dr.add_argument("--repo", default=".", help="Path to target repo to check hook installation")
    dr.set_defaults(func=cmd_doctor)

    return parser


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
