#!/usr/bin/env python3
"""Empirical comparison: tuples vs. untyped logs at different scales.

Measures: validation time, storage size, query performance (find scope violations).
Generates synthetic datasets at 3 scales (small, medium, large), converts to
both tuple and untyped log formats, and runs benchmarks.

Usage:
    python scripts/tuples_vs_logs.py
    python scripts/tuples_vs_logs.py --scales small,medium,large
    python scripts/tuples_vs_logs.py --output results.json

Stdlib-only.
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any

# Scale definitions
SCALES = {
    "small": 100,  # small incident
    "medium": 1000,  # medium workflow
    "large": 10000,  # large system
}


def generate_tuples(n: int) -> list[dict[str, Any]]:
    """Generate n synthetic tuples."""
    tuples = []
    for i in range(n):
        tuple_type = ["CONTRACT", "DCT", "EVIDENCE", "SYSTEM", "ATTEST"][i % 5]
        state = "ok" if i % 10 != 0 else "blocked"  # 10% blocked
        tuples.append(
            {
                "tuple_type": tuple_type,
                "id": f"tuple-{i:06d}",
                "time": f"2026-07-01T{(i % 86400):02d}:{((i * 7) % 60):02d}:{((i * 13) % 60):02d}Z",
                "state": state,
                "drift": 0.0 if i % 5 != 0 else round(i * 0.001 % 1, 3),
                "tier": 1 + (i % 3),
                "agent": f"agent-{i % 10:02d}",
                "tool": f"tool-{i % 5}",
                "intent_id": f"intent-{i % 50:03d}",
                "task_id": f"task-{i % 100:03d}",
                "tuple_data": {"payload": f"data-{i}", "index": i},
            }
        )
    return tuples


def tuples_to_untyped_logs(tuples: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Convert tuples to untyped log format (flat key-value, no schema)."""
    logs = []
    for t in tuples:
        logs.append(
            {
                "timestamp": t["time"],
                "event": t["tuple_type"].lower(),
                "event_id": t["id"],
                "agent": t["agent"],
                "status": t["state"],
                "tool": t["tool"],
                "intent": t["intent_id"],
                "task": t["task_id"],
                "payload": t["tuple_data"],
            }
        )
    return logs


def measure_validation_time(data: list[dict[str, Any]], is_tuple: bool) -> float:
    """Measure validation time for a dataset."""
    start = time.perf_counter()
    if is_tuple:
        # Validate tuples: check required fields
        required = {
            "tuple_type",
            "id",
            "time",
            "state",
            "agent",
            "intent_id",
            "task_id",
            "tuple_data",
        }
        for t in data:
            missing = required - set(t.keys())
            assert not missing, f"Tuple {t.get('id')} missing fields: {missing}"
    else:
        # Validate untyped logs: check minimal fields
        for log in data:
            assert "timestamp" in log
            assert "event" in log
    elapsed = time.perf_counter() - start
    return elapsed


def measure_storage_size(data: list[dict[str, Any]]) -> int:
    """Measure storage size (bytes) for a dataset."""
    return len(json.dumps(data, ensure_ascii=False).encode("utf-8"))


def measure_query_scope_violations(data: list[dict[str, Any]], is_tuple: bool) -> tuple[float, int]:
    """Measure query performance for finding scope violations (state=blocked)."""
    start = time.perf_counter()
    if is_tuple:
        # Tuples: query by state field (typed)
        violations = [t for t in data if t.get("state") == "blocked"]
    else:
        # Untyped logs: query by status field (untyped)
        violations = [log for log in data if log.get("status") == "blocked"]
    elapsed = time.perf_counter() - start
    return elapsed, len(violations)


def measure_query_by_agent(
    data: list[dict[str, Any]], is_tuple: bool, agent_id: str
) -> tuple[float, int]:
    """Measure query performance for finding events by a specific agent."""
    start = time.perf_counter()
    if is_tuple:
        results = [t for t in data if t.get("agent") == agent_id]
    else:
        results = [log for log in data if log.get("agent") == agent_id]
    elapsed = time.perf_counter() - start
    return elapsed, len(results)


def run_comparison(scale_name: str, n: int) -> dict[str, Any]:
    """Run comparison for a given scale."""
    # Generate data
    tuples = generate_tuples(n)
    logs = tuples_to_untyped_logs(tuples)

    # Measure validation time
    tuple_validation = measure_validation_time(tuples, is_tuple=True)
    log_validation = measure_validation_time(logs, is_tuple=False)

    # Measure storage size
    tuple_size = measure_storage_size(tuples)
    log_size = measure_storage_size(logs)

    # Measure query: scope violations
    tuple_query_time, tuple_violations = measure_query_scope_violations(tuples, is_tuple=True)
    log_query_time, log_violations = measure_query_scope_violations(logs, is_tuple=False)

    # Measure query: by agent
    tuple_agent_time, tuple_agent_count = measure_query_by_agent(
        tuples, is_tuple=True, agent_id="agent-05"
    )
    log_agent_time, log_agent_count = measure_query_by_agent(
        logs, is_tuple=False, agent_id="agent-05"
    )

    return {
        "scale": scale_name,
        "n_events": n,
        "tuples": {
            "validation_time_s": round(tuple_validation, 6),
            "storage_bytes": tuple_size,
            "storage_kb": round(tuple_size / 1024, 2),
            "query_scope_violations_s": round(tuple_query_time, 6),
            "scope_violations_found": tuple_violations,
            "query_by_agent_s": round(tuple_agent_time, 6),
            "agent_events_found": tuple_agent_count,
        },
        "untyped_logs": {
            "validation_time_s": round(log_validation, 6),
            "storage_bytes": log_size,
            "storage_kb": round(log_size / 1024, 2),
            "query_scope_violations_s": round(log_query_time, 6),
            "scope_violations_found": log_violations,
            "query_by_agent_s": round(log_agent_time, 6),
            "agent_events_found": log_agent_count,
        },
        "delta": {
            "validation_time_ratio": round(tuple_validation / max(log_validation, 0.000001), 2),
            "storage_ratio": round(tuple_size / max(log_size, 1), 2),
            "query_violations_ratio": round(tuple_query_time / max(log_query_time, 0.000001), 2),
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--scales", default="small,medium,large", help="Comma-separated scale names"
    )
    parser.add_argument("--output", help="Output JSON file for results")
    args = parser.parse_args(argv)

    scale_names = [s.strip() for s in args.scales.split(",")]
    results = []

    for name in scale_names:
        if name not in SCALES:
            print(f"Unknown scale: {name}. Valid: {list(SCALES.keys())}")
            continue
        n = SCALES[name]
        print(f"\nRunning comparison: {name} (n={n})...")
        result = run_comparison(name, n)
        results.append(result)

        print(
            f"  Tuples:   validation={result['tuples']['validation_time_s']}s, "
            f"storage={result['tuples']['storage_kb']}KB, "
            f"query_violations={result['tuples']['query_scope_violations_s']}s"
        )
        print(
            f"  Logs:     validation={result['untyped_logs']['validation_time_s']}s, "
            f"storage={result['untyped_logs']['storage_kb']}KB, "
            f"query_violations={result['untyped_logs']['query_scope_violations_s']}s"
        )
        print(
            f"  Ratios:   validation={result['delta']['validation_time_ratio']}x, "
            f"storage={result['delta']['storage_ratio']}x, "
            f"query={result['delta']['query_violations_ratio']}x"
        )

    output = {
        "benchmark": "tuples_vs_untyped_logs",
        "date": "2026-07-01",
        "scales": results,
    }

    if args.output:
        with Path(args.output).open("w", encoding="utf-8") as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
            f.write("\n")
        print(f"\nResults written to {args.output}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
