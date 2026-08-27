#!/usr/bin/env python3
"""Audit surface minimization validator.

Validates tuples against the minimum, recommended, and full audit field sets.
Reports which fields are present, missing, or defaulted.

Usage:
    python scripts/audit_surface.py --input trace.json
    python scripts/audit_surface.py --input trace.json --level minimum
    python scripts/audit_surface.py --input trace.json --level recommended
    python scripts/audit_surface.py --input trace.json --level full

Stdlib-only.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

# Minimum fields required for reliable auditing (7 fields)
MINIMUM_FIELDS = {
    "tuple_type",
    "id",
    "time",
    "state",
    "agent",
    "intent_id",
    "task_id",
    "tuple_data",
}

# Recommended fields (9 fields — minimum + drift + tier)
RECOMMENDED_FIELDS = MINIMUM_FIELDS | {"drift", "tier"}

# Full fields (14 fields — recommended + tool + signature + args_hash + previous_hash)
FULL_FIELDS = RECOMMENDED_FIELDS | {"tool", "signature", "args_hash", "previous_hash"}

FIELD_SETS = {
    "minimum": MINIMUM_FIELDS,
    "recommended": RECOMMENDED_FIELDS,
    "full": FULL_FIELDS,
}


def audit_tuple(tuple_dict: dict[str, Any], level: str = "recommended") -> dict[str, Any]:
    """Audit a single tuple against a field set.

    Returns a dict with:
    - present: fields that are present
    - missing: fields that are required but missing
    - defaulted: fields that can be defaulted if missing
    - extra: fields not in the field set
    - verdict: "pass" or "fail"
    """
    required = FIELD_SETS[level]
    present = set(tuple_dict.keys()) & required
    missing = required - set(tuple_dict.keys())
    extra = set(tuple_dict.keys()) - required

    # Fields that can be defaulted
    defaultable = {"drift": 0.0, "tier": 1, "tool": "unknown"}
    defaulted = {f: defaultable[f] for f in missing if f in defaultable}
    critical_missing = missing - set(defaultable.keys())

    verdict = "pass" if not critical_missing else "fail"

    return {
        "tuple_id": tuple_dict.get("id", "unknown"),
        "level": level,
        "present": sorted(present),
        "missing": sorted(missing),
        "critical_missing": sorted(critical_missing),
        "defaulted": defaulted,
        "extra": sorted(extra),
        "verdict": verdict,
    }


def audit_trace(trace: list[dict[str, Any]], level: str = "recommended") -> dict[str, Any]:
    """Audit a full trace of tuples."""
    results = [audit_tuple(t, level) for t in trace]
    pass_count = sum(1 for r in results if r["verdict"] == "pass")
    fail_count = len(results) - pass_count
    return {
        "level": level,
        "total_tuples": len(results),
        "passed": pass_count,
        "failed": fail_count,
        "results": results,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="Input trace file (JSON array)")
    parser.add_argument(
        "--level",
        choices=["minimum", "recommended", "full"],
        default="recommended",
        help="Audit level (default: recommended)",
    )
    args = parser.parse_args(argv)

    with Path(args.input).open("r", encoding="utf-8") as f:
        trace = json.load(f)

    if not isinstance(trace, list):
        raise ValueError("Input must be a JSON array of tuples")

    report = audit_trace(trace, args.level)

    print(f"Audit Report ({report['level']} level)")
    print(f"  Total tuples: {report['total_tuples']}")
    print(f"  Passed: {report['passed']}")
    print(f"  Failed: {report['failed']}")

    for r in report["results"]:
        status = "PASS" if r["verdict"] == "pass" else "FAIL"
        print(f"  [{status}] {r['tuple_id']}")
        if r["critical_missing"]:
            print(f"    Critical missing: {', '.join(r['critical_missing'])}")
        if r["defaulted"]:
            print(f"    Defaulted: {r['defaulted']}")

    return 0 if report["failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
