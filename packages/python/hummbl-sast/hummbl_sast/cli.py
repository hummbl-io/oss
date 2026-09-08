"""Unified CLI for hummbl-sast.

Modified by HUMMBL on 2026-09-08: narrow scope claims and report lookup errors.

Usage:
  python -m hummbl_sast sast <path>          # Static analysis heuristics
  python -m hummbl_sast secrets <path>       # Secret scanning
  python -m hummbl_sast deps <path>          # Dependency vulnerability lookups
  python -m hummbl_sast all <path>           # Run all three
  python -m hummbl_sast sast <path> --json   # JSON output
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys

from . import sast, secret_scan, dep_audit


def _cmd_sast(args: argparse.Namespace) -> int:
    root = pathlib.Path(args.path)
    if not root.exists():
        print(f"Error: {root} does not exist", file=sys.stderr)
        return 2

    if root.is_file():
        findings = sast.scan_file(root)
    else:
        findings = sast.scan_directory(
            root,
            exclude_patterns=args.exclude,
        )

    if args.json:
        data = {
            "scanner": "sast",
            "target": str(root),
            "summary": sast.summarize(findings),
            "findings": [f.__dict__ for f in findings],
        }
        print(json.dumps(data, indent=2, default=str))
    else:
        print(sast.format_report(findings, str(root)))

    # Exit code: 1 if HIGH findings, 0 otherwise
    high_count = sum(1 for f in findings if f.severity == "HIGH")
    return 1 if high_count > 0 else 0


def _cmd_secrets(args: argparse.Namespace) -> int:
    root = pathlib.Path(args.path)
    if not root.exists():
        print(f"Error: {root} does not exist", file=sys.stderr)
        return 2

    if root.is_file():
        findings = secret_scan.scan_file(root)
    else:
        findings = secret_scan.scan_directory(
            root,
            exclude_patterns=args.exclude,
        )

    if args.json:
        data = {
            "scanner": "secrets",
            "target": str(root),
            "summary": secret_scan.summarize(findings),
            "findings": [
                {k: v for k, v in f.__dict__.items() if k != "match"}
                for f in findings
            ],
        }
        print(json.dumps(data, indent=2, default=str))
    else:
        print(secret_scan.format_report(findings, str(root)))

    high_count = sum(1 for f in findings if f.severity == "HIGH")
    return 1 if high_count > 0 else 0


def _cmd_deps(args: argparse.Namespace) -> int:
    root = pathlib.Path(args.path)
    if not root.exists():
        print(f"Error: {root} does not exist", file=sys.stderr)
        return 2

    findings = dep_audit.audit_directory(
        root,
        timeout=args.timeout,
        rate_limit=args.rate_limit,
    )

    if args.json:
        data = {
            "scanner": "deps",
            "target": str(root),
            "summary": dep_audit.summarize(findings),
            "findings": [
                {
                    "vuln_id": f.vuln_id,
                    "severity": f.severity,
                    "summary": f.summary,
                    "package": f.dep.name,
                    "version": f.dep.version,
                    "ecosystem": f.dep.ecosystem,
                    "fixed_versions": f.fixed_versions,
                    "url": f.url,
                }
                for f in findings
            ],
        }
        print(json.dumps(data, indent=2))
    else:
        print(dep_audit.format_report(findings, str(root)))

    high_count = sum(1 for f in findings if f.severity == "HIGH")
    return 1 if high_count > 0 else 0


def _cmd_all(args: argparse.Namespace) -> int:
    root = pathlib.Path(args.path)
    if not root.exists():
        print(f"Error: {root} does not exist", file=sys.stderr)
        return 2

    if not root.is_dir():
        print(f"Error: {root} is not a directory (all mode requires a directory)", file=sys.stderr)
        return 2

    print("=" * 60)
    print(f"Combined Scanner Results — {root}")
    print("=" * 60)
    print()

    # SAST
    print(">>> Static Analysis (SAST)")
    sast_findings = sast.scan_directory(root, exclude_patterns=args.exclude)
    print(sast.format_report(sast_findings, str(root)))
    print()

    # Secrets
    print(">>> Secret Scanning")
    secret_findings = secret_scan.scan_directory(root, exclude_patterns=args.exclude)
    print(secret_scan.format_report(secret_findings, str(root)))
    print()

    # Deps
    print(">>> Dependency Audit")
    dep_findings = dep_audit.audit_directory(root, timeout=args.timeout, rate_limit=args.rate_limit)
    print(dep_audit.format_report(dep_findings, str(root)))
    print()

    # Summary
    sast_high = sum(1 for f in sast_findings if f.severity == "HIGH")
    secret_high = sum(1 for f in secret_findings if f.severity == "HIGH")
    dep_high = sum(1 for f in dep_findings if f.severity == "HIGH")
    total_high = sast_high + secret_high + dep_high

    print("=" * 60)
    print("SUMMARY")
    print(f"  SAST:      {len(sast_findings)} findings ({sast_high} HIGH)")
    print(f"  Secrets:   {len(secret_findings)} findings ({secret_high} HIGH)")
    print(f"  Deps:      {len(dep_findings)} findings ({dep_high} HIGH)")
    print(f"  TOTAL HIGH: {total_high}")
    print("=" * 60)

    return 1 if total_high > 0 else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="hummbl-sast",
        description="Python static analysis, secret-pattern scanning, and dependency lookups",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Common args helper
    def add_common(p):
        p.add_argument("path", help="File or directory to scan")
        p.add_argument("--json", action="store_true", help="Output as JSON")
        p.add_argument("--exclude", action="append", default=[],
                       help="Regex patterns to exclude (can repeat)")

    # sast
    p_sast = subparsers.add_parser("sast", help="Static analysis heuristics")
    add_common(p_sast)
    p_sast.set_defaults(func=_cmd_sast)

    # secrets
    p_secrets = subparsers.add_parser("secrets", help="Secret scanning")
    add_common(p_secrets)
    p_secrets.set_defaults(func=_cmd_secrets)

    # deps
    p_deps = subparsers.add_parser("deps", help="Dependency vulnerability lookups")
    add_common(p_deps)
    p_deps.add_argument("--timeout", type=float, default=10.0, help="API timeout (seconds)")
    p_deps.add_argument("--rate-limit", type=float, default=0.5, help="Delay between API calls (seconds)")
    p_deps.set_defaults(func=_cmd_deps)

    # all
    p_all = subparsers.add_parser("all", help="Run all scanners")
    add_common(p_all)
    p_all.add_argument("--timeout", type=float, default=10.0, help="API timeout (seconds)")
    p_all.add_argument("--rate-limit", type=float, default=0.5, help="Delay between API calls (seconds)")
    p_all.set_defaults(func=_cmd_all)

    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except dep_audit.DependencyAuditError as exc:
        if args.json and args.command != "all":
            print(json.dumps({
                "scanner": args.command,
                "target": args.path,
                "status": "incomplete",
                "error": str(exc),
            }))
        else:
            print(f"Dependency audit incomplete: {exc}", file=sys.stderr)
        return 2



if __name__ == "__main__":
    sys.exit(main())
