from __future__ import annotations

import argparse
import json
import os
from collections import Counter
from pathlib import Path


def summarize_sarif(directory: Path) -> tuple[int, dict[str, int]]:
    sarif_paths = sorted(directory.rglob("*.sarif"))
    if not sarif_paths:
        raise FileNotFoundError(f"no SARIF files found under {directory}")

    rule_counts: Counter[str] = Counter()
    for path in sarif_paths:
        document = json.loads(path.read_text(encoding="utf-8"))
        for run in document.get("runs", []):
            for result in run.get("results", []):
                rule_counts[result.get("ruleId") or "unknown-rule"] += 1

    return len(sarif_paths), dict(sorted(rule_counts.items()))


def render_summary(file_count: int, rule_counts: dict[str, int]) -> str:
    finding_count = sum(rule_counts.values())
    lines = [
        "# CodeQL local SARIF gate",
        "",
        f"SARIF files: {file_count}",
        f"Findings: {finding_count}",
    ]
    if rule_counts:
        lines.extend(["", "## Rules"])
        lines.extend(f"- {rule_id}: {count}" for rule_id, count in rule_counts.items())
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Fail on CodeQL SARIF findings without printing result messages.",
    )
    parser.add_argument("directory", type=Path)
    args = parser.parse_args()

    try:
        file_count, rule_counts = summarize_sarif(args.directory)
    except (FileNotFoundError, json.JSONDecodeError, TypeError) as exc:
        print(f"CodeQL SARIF gate error: {exc}")
        return 2

    summary = render_summary(file_count, rule_counts)
    print(summary, end="")

    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_path:
        with Path(summary_path).open("a", encoding="utf-8") as handle:
            handle.write(summary)

    return 1 if rule_counts else 0


if __name__ == "__main__":
    raise SystemExit(main())
