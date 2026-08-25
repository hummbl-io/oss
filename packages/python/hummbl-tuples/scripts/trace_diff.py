#!/usr/bin/env python3
"""Tuple trace diffing CLI for comparative analysis.

Given two traces (lists of tuples), identifies differences at the tuple
level. Outputs a structured diff showing divergence points, magnitude,
and causality hints.

Usage:
    python scripts/trace_diff.py --trace-a trace1.json --trace-b trace2.json
    python scripts/trace_diff.py --trace-a trace1.json --trace-b trace2.json --output diff.json
    python scripts/trace_diff.py --trace-a trace1.json --trace-b trace2.json --format summary

Stdlib-only.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def load_trace(path: str) -> list[dict[str, Any]]:
    """Load a trace file (JSON array of tuples)."""
    with Path(path).open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError(f"Trace file {path} must contain a JSON array")
    return data


def _tuple_key(t: dict[str, Any]) -> str:
    """Extract a stable key for matching tuples across traces.

    Uses tuple_type + id if available, otherwise tuple_type + time.
    """
    tt = t.get("tuple_type", "")
    tid = t.get("id", "")
    if tid:
        return f"{tt}:{tid}"
    return f"{tt}:{t.get('time', '')}"


def _tuple_fingerprint(t: dict[str, Any]) -> str:
    """Create a fingerprint of a tuple's content for equality checking.

    Excludes id and time (which may differ even for equivalent tuples).
    """
    d = dict(t)
    d.pop("id", None)
    d.pop("time", None)
    return json.dumps(d, sort_keys=True)


def diff_traces(
    trace_a: list[dict[str, Any]],
    trace_b: list[dict[str, Any]],
) -> dict[str, Any]:
    """Compute a structured diff between two traces.

    Returns a dict with:
    - only_in_a: tuples present only in trace A
    - only_in_b: tuples present only in trace B
    - modified: tuples present in both but with different content
    - matched: tuples present in both with identical content
    - divergence_points: list of indices where traces diverge
    - summary: counts and magnitude
    """
    keys_a = {_tuple_key(t): t for t in trace_a}
    keys_b = {_tuple_key(t): t for t in trace_b}

    set_a = set(keys_a.keys())
    set_b = set(keys_b.keys())

    only_in_a_keys = set_a - set_b
    only_in_b_keys = set_b - set_a
    common_keys = set_a & set_b

    only_in_a = [keys_a[k] for k in sorted(only_in_a_keys)]
    only_in_b = [keys_b[k] for k in sorted(only_in_b_keys)]

    modified = []
    matched = []
    for k in sorted(common_keys):
        fp_a = _tuple_fingerprint(keys_a[k])
        fp_b = _tuple_fingerprint(keys_b[k])
        if fp_a != fp_b:
            modified.append({
                "key": k,
                "trace_a": keys_a[k],
                "trace_b": keys_b[k],
                "diff_fields": _field_diff(keys_a[k], keys_b[k]),
            })
        else:
            matched.append({"key": k, "tuple": keys_a[k]})

    # Divergence points: indices where the traces differ in tuple_type or key
    divergence_points = []
    max_len = max(len(trace_a), len(trace_b))
    for i in range(max_len):
        if i >= len(trace_a):
            divergence_points.append({
                "index": i,
                "type": "extra_in_b",
                "tuple_b": trace_b[i],
            })
        elif i >= len(trace_b):
            divergence_points.append({
                "index": i,
                "type": "extra_in_a",
                "tuple_a": trace_a[i],
            })
        else:
            key_a = _tuple_key(trace_a[i])
            key_b = _tuple_key(trace_b[i])
            if key_a != key_b:
                divergence_points.append({
                    "index": i,
                    "type": "key_mismatch",
                    "tuple_a_key": key_a,
                    "tuple_b_key": key_b,
                })

    # Magnitude: how different are the traces (0.0 = identical, 1.0 = completely different)
    total = max(len(trace_a), len(trace_b), 1)
    different = len(only_in_a) + len(only_in_b) + len(modified)
    magnitude = different / total

    return {
        "only_in_a": only_in_a,
        "only_in_b": only_in_b,
        "modified": modified,
        "matched": matched,
        "divergence_points": divergence_points,
        "summary": {
            "trace_a_length": len(trace_a),
            "trace_b_length": len(trace_b),
            "matched_count": len(matched),
            "modified_count": len(modified),
            "only_in_a_count": len(only_in_a),
            "only_in_b_count": len(only_in_b),
            "divergence_point_count": len(divergence_points),
            "magnitude": round(magnitude, 4),
        },
    }


def _field_diff(a: dict[str, Any], b: dict[str, Any]) -> list[dict[str, Any]]:
    """Compute field-level differences between two tuples."""
    diffs = []
    all_keys = set(a.keys()) | set(b.keys())
    for k in sorted(all_keys):
        va = a.get(k)
        vb = b.get(k)
        if va != vb:
            diffs.append({
                "field": k,
                "value_a": va,
                "value_b": vb,
            })
    return diffs


def format_summary(diff: dict[str, Any]) -> str:
    """Format a diff as a human-readable summary."""
    s = diff["summary"]
    lines = [
        "Trace Diff Summary",
        "=" * 40,
        f"Trace A length:    {s['trace_a_length']}",
        f"Trace B length:    {s['trace_b_length']}",
        f"Matched:           {s['matched_count']}",
        f"Modified:          {s['modified_count']}",
        f"Only in A:         {s['only_in_a_count']}",
        f"Only in B:         {s['only_in_b_count']}",
        f"Divergence points: {s['divergence_point_count']}",
        f"Magnitude:         {s['magnitude']} (0.0=identical, 1.0=completely different)",
        "",
    ]

    if diff["modified"]:
        lines.append("Modified tuples:")
        for m in diff["modified"]:
            lines.append(f"  {m['key']}:")
            for fd in m["diff_fields"]:
                lines.append(f"    {fd['field']}: {fd['value_a']} -> {fd['value_b']}")
        lines.append("")

    if diff["only_in_a"]:
        lines.append(f"Only in A ({len(diff['only_in_a'])} tuples):")
        for t in diff["only_in_a"][:5]:
            lines.append(f"  {_tuple_key(t)}")
        if len(diff["only_in_a"]) > 5:
            lines.append(f"  ... and {len(diff['only_in_a']) - 5} more")
        lines.append("")

    if diff["only_in_b"]:
        lines.append(f"Only in B ({len(diff['only_in_b'])} tuples):")
        for t in diff["only_in_b"][:5]:
            lines.append(f"  {_tuple_key(t)}")
        if len(diff["only_in_b"]) > 5:
            lines.append(f"  ... and {len(diff['only_in_b']) - 5} more")
        lines.append("")

    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--trace-a", required=True, help="First trace file (JSON array)")
    parser.add_argument("--trace-b", required=True, help="Second trace file (JSON array)")
    parser.add_argument("--output", help="Output file for structured diff (JSON)")
    parser.add_argument("--format", choices=["summary", "json"], default="summary",
                        help="Output format (default: summary)")
    args = parser.parse_args(argv)

    trace_a = load_trace(args.trace_a)
    trace_b = load_trace(args.trace_b)

    diff = diff_traces(trace_a, trace_b)

    if args.format == "json" or args.output:
        output = json.dumps(diff, indent=2, ensure_ascii=False)
        if args.output:
            with Path(args.output).open("w", encoding="utf-8") as f:
                f.write(output)
                f.write("\n")
            print(f"Wrote diff to {args.output}")
        else:
            print(output)
    else:
        print(format_summary(diff))

    # Exit code: 0 if identical, 1 if different
    return 1 if diff["summary"]["magnitude"] > 0 else 0


if __name__ == "__main__":
    raise SystemExit(main())
