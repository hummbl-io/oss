#!/usr/bin/env python3
"""Local usage and spend-telemetry collector for agent tooling.

This script does not call external billing APIs.
It aggregates observable local artifacts and exposes a normalized "finops pulse"
that can be used for ad-hoc triage.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass
class PulseMetric:
    name: str
    value: float
    unit: str
    note: str = ""


def run(cmd: list[str], cwd: str | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )


def find_receipt_files(root: Path) -> list[Path]:
    candidates = list(root.glob("_receipts/**/*"))
    candidates.extend(root.glob("**/*.receipt"))
    candidates.extend(root.glob("**/*.tsv"))
    candidates.extend(root.glob("**/*.jsonl"))
    return [item for item in candidates if item.is_file()]


def collect_files_metrics(root: Path) -> list[PulseMetric]:
    files = find_receipt_files(root)
    total_size = 0
    oldest = None
    newest = None
    for item in files:
        try:
            stat = item.stat()
        except OSError:
            continue
        total_size += stat.st_size
        if oldest is None or stat.st_mtime < oldest:
            oldest = stat.st_mtime
        if newest is None or stat.st_mtime > newest:
            newest = stat.st_mtime
    return [
        PulseMetric("receipt_file_count", float(len(files)), "count"),
        PulseMetric("receipt_total_bytes", float(total_size), "bytes"),
        PulseMetric(
            "receipt_age_days",
            (dt.datetime.now(dt.timezone.utc).timestamp() - newest) / 86400 if newest else 0.0,
            "days",
            "age of latest file",
        ),
        PulseMetric(
            "receipt_retention_window_days",
            (newest - oldest) / 86400 if oldest and newest else 0.0,
            "days",
            "span between oldest/latest",
        ),
    ]


def collect_git_metrics(root: Path) -> list[PulseMetric]:
    metrics: list[PulseMetric] = []
    commits_proc = run(["git", "rev-list", "--count", "HEAD"], cwd=str(root))
    commits = float(commits_proc.stdout.strip()) if commits_proc.returncode == 0 else 0.0
    metrics.append(PulseMetric("commit_count", commits, "count"))

    since = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=7)
    since_txt = since.strftime("%Y-%m-%d")
    recent_proc = run(["git", "rev-list", "--count", f"--since={since_txt}", "HEAD"], cwd=str(root))
    recent = float(recent_proc.stdout.strip()) if recent_proc.returncode == 0 else 0.0
    metrics.append(PulseMetric("commits_7d", recent, "count"))
    metrics.append(PulseMetric("commits_7d_ratio", (recent / 7.0) if commits else 0.0, "per-day"))
    return metrics


def normalize_cost_index(metrics: list[PulseMetric]) -> float:
    file_pressure = metrics[0].value / 1024.0
    recent_commits = next(
        (m for m in metrics if m.name == "commits_7d"),
        PulseMetric("commits_7d", 0.0, "count"),
    ).value
    return round(file_pressure * 0.01 + recent_commits * 0.4 + 2.0, 4)


def summarize(root: Path) -> dict[str, object]:
    file_metrics = collect_files_metrics(root)
    git_metrics = collect_git_metrics(root)
    all_metrics = file_metrics + git_metrics

    score = normalize_cost_index(file_metrics + git_metrics)
    return {
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "repo": str(root),
        "platform": os.name,
        "metrics": [
            {"name": metric.name, "value": metric.value, "unit": metric.unit, "note": metric.note}
            for metric in all_metrics
        ],
        "estimated_finops_score": score,
        "status": (
            "green" if score < 12 else ("yellow" if score < 24 else "amber")
        ),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Emit local spend/usage pulse metrics")
    parser.add_argument("--repo", default=".", help="Repository path")
    parser.add_argument("--json", action="store_true", help="Emit JSON summary")
    parser.add_argument("--raw", action="store_true", help="Emit compact raw metrics only")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = Path(args.repo).resolve()
    if not root.exists():
        raise SystemExit(f"repo path not found: {root}")
    payload = summarize(root)
    if args.raw:
        print(json.dumps(payload["metrics"], indent=2))
        return 0
    if args.json:
        print(json.dumps(payload, indent=2))
        return 0
    print(f"Repo: {payload['repo']}")
    print(f"Estimated finops score: {payload['estimated_finops_score']:.2f}")
    print(f"Status: {payload['status']}")
    for item in payload["metrics"]:
        print(f"- {item['name']}: {item['value']} {item['unit']} {item['note']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
