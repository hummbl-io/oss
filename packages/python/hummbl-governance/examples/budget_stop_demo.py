# Copyright 2026 HUMMBL, LLC
# SPDX-License-Identifier: Apache-2.0
"""Offline example: a cooperative runner obeys CostGovernor's DENY decision.

Run from the package directory: python -m examples.budget_stop_demo
No provider calls, credentials, real charges, or persistent database.
"""

from __future__ import annotations

import argparse
import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

from hummbl_governance.cost_governor import CostGovernor


def run_demo(task: Callable[[int], None] | None = None) -> dict[str, Any]:
    """Run fixed-cost synthetic tasks; record the first denied task without calling it."""
    governor = CostGovernor(":memory:", soft_cap=0.5, hard_cap=1.0, currency="DEMO")
    completed: list[int] = []
    events: list[dict[str, Any]] = []
    blocked_task = None
    try:
        for task_id in range(1, 7):
            status = governor.check_budget_status()
            event = {"task": task_id, "decision": status.decision,
                     "spend_before": status.current_spend}
            if status.decision == "DENY":
                event["executed"] = False
                events.append(event)
                blocked_task = task_id
                break
            # WARN is advisory here. The runner, not the library, enforces DENY.
            if task is not None:
                task(task_id)
            completed.append(task_id)
            governor.record_usage("synthetic", "offline-task", 0, 0, 0.25)
            event.update(executed=True, spend_after=governor.get_daily_spend())
            events.append(event)
        return {
            "schema": "hummbl.demo.budget-stop.v1",
            "synthetic": True,
            "currency": "DEMO",
            "unit_cost": 0.25,
            "soft_cap": 0.5,
            "hard_cap": 1.0,
            "events": events,
            "completed_tasks": completed,
            "blocked_task": blocked_task,
            "recorded_spend": governor.get_daily_spend(),
            "limitations": [
                "Sequential cooperative runner; no OS isolation or forced process termination.",
                "Recorded usage is checked before the next task; no reservation of future costs.",
                "Variable costs or concurrent callers can overshoot; this example does not prevent that.",
                "Unsigned local run summary; not an authenticated receipt or proof of an external event.",
            ],
        }
    finally:
        # The current library has no public close() method for its in-memory connection.
        if governor._shared_conn is not None:
            governor._shared_conn.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, help="Write JSON to a NEW file; never overwrite")
    args = parser.parse_args()
    result = run_demo()
    if args.output is not None:
        with args.output.open("x", encoding="utf-8", newline="\n") as handle:
            json.dump(result, handle, indent=2, allow_nan=False)
            handle.write("\n")
    print("SYNTHETIC / OFFLINE / NO REAL CHARGES")
    print("Soft cap: 0.50 DEMO | Hard cap: 1.00 DEMO | Task cost: 0.25 DEMO")
    for event in result["events"]:
        outcome = "executed" if event["executed"] else "NOT EXECUTED"
        print(f"Task {event['task']}: {event['decision']:<5} | "
              f"recorded before: {event['spend_before']:.2f} | {outcome}")
    print(f"Completed: {len(result['completed_tasks'])} | "
          f"Blocked: task {result['blocked_task']} | Recorded: {result['recorded_spend']:.2f} DEMO")
    print("The runner enforces DENY. This does not reserve future or concurrent costs.")
    print("JSON output, when requested, is an unsigned local run summary.")


if __name__ == "__main__":
    main()
