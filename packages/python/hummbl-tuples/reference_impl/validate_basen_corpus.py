#!/usr/bin/env python3
"""Validate BaseN JSONL corpora for structural and semantic drift.

Stdlib-only validator intended for early BaseN corpora. It focuses on the
failure modes already observed in March 2026:

- protocol-family leakage
- missing/empty steps
- step-count mismatch
- placeholder content
- duplicate step content

Usage:
    python3 reference_impl/validate_basen_corpus.py path/to/corpus.jsonl
    python3 reference_impl/validate_basen_corpus.py path/to/corpus.jsonl --summary out.json
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

VALIDATED = "VALIDATED"
QUARANTINED = "QUARANTINED"
REJECTED = "REJECTED"

PROTOCOL_STEPS = {
    "ScientificMethod": ["[OBSERVATION]", "[HYPOTHESIS]", "[ACTION]", "[RESULT]", "[EVALUATION]"],
    "WickednessAudit": ["[WICKEDNESS]", "[READINESS]", "[BKI_SCORE]", "[CLASSIFICATION]"],
    "Inversion": ["Goal", "Obstacle", "InvertedPerspective", "Prevention", "RobustPlan"],
    "PerspectiveShift": ["ObserverA", "ObserverB", "Conflict", "Resolution", "UnifiedModel"],
}

SCIENTIFIC_LEAK_MARKERS = (
    "[WICKEDNESS]",
    "[READINESS]",
    "[BKI",
    "contestation=",
    "authority=",
)

RUBRIC_LEAK_MARKERS = (
    "Observation",
    "Hypothesis",
    "Experiment",
    "Result",
    "Evaluation",
)

PLACEHOLDER_MARKERS = (
    "Error generating response",
    "Request error",
    "Generation fallback",
    "status=error",
)


def detect_protocol_family(protocol_id: str) -> str:
    if protocol_id == "WickednessAudit":
        return "RUBRIC_TRACE"
    if protocol_id in {"ScientificMethod", "Inversion", "PerspectiveShift"}:
        return "PROTOCOL_TRACE"
    return "UNKNOWN"


def analyze_trace(row_id: int, trace: dict) -> dict:
    result = {
        "row_id": row_id,
        "status": VALIDATED,
        "protocol_id": trace.get("protocol"),
        "protocol_family": detect_protocol_family(str(trace.get("protocol", ""))),
        "error_codes": [],
        "warning_codes": [],
    }

    if not isinstance(trace, dict):
        result["status"] = REJECTED
        result["error_codes"].append("NOT_OBJECT")
        return result

    for key in ("task", "protocol", "steps"):
        if key not in trace:
            result["status"] = REJECTED
            result["error_codes"].append(f"MISSING_{key.upper()}")

    steps = trace.get("steps")
    if not isinstance(steps, list) or not steps:
        result["status"] = REJECTED
        result["error_codes"].append("INVALID_STEPS")
        return result

    protocol_id = str(trace.get("protocol", ""))
    expected_steps = PROTOCOL_STEPS.get(protocol_id)
    if expected_steps is None:
        result["warning_codes"].append("UNKNOWN_PROTOCOL")
    elif len(steps) != len(expected_steps):
        result["status"] = QUARANTINED if result["status"] == VALIDATED else result["status"]
        result["error_codes"].append("STEP_COUNT_MISMATCH")

    seen_contents: Counter[str] = Counter()
    for idx, step in enumerate(steps):
        if not isinstance(step, dict):
            result["status"] = REJECTED
            result["error_codes"].append("STEP_NOT_OBJECT")
            continue
        step_type = step.get("type")
        content = step.get("content")
        if step_type is None:
            result["status"] = REJECTED
            result["error_codes"].append("MISSING_STEP_TYPE")
        if content is None:
            result["status"] = REJECTED
            result["error_codes"].append("MISSING_STEP_CONTENT")
            continue
        if not isinstance(content, str):
            result["status"] = REJECTED
            result["error_codes"].append("NON_STRING_CONTENT")
            continue

        normalized = content.strip()
        if not normalized:
            result["status"] = QUARANTINED if result["status"] == VALIDATED else result["status"]
            result["error_codes"].append("EMPTY_CONTENT")
        if any(marker in normalized for marker in PLACEHOLDER_MARKERS):
            result["status"] = QUARANTINED if result["status"] == VALIDATED else result["status"]
            result["error_codes"].append("PLACEHOLDER_CONTENT")

        seen_contents[normalized] += 1

        if expected_steps is not None and idx < len(expected_steps):
            if step_type != expected_steps[idx]:
                result["status"] = QUARANTINED if result["status"] == VALIDATED else result["status"]
                result["error_codes"].append("STEP_TYPE_MISMATCH")

        if protocol_id == "ScientificMethod" and any(marker in normalized for marker in SCIENTIFIC_LEAK_MARKERS):
            result["status"] = QUARANTINED if result["status"] == VALIDATED else result["status"]
            result["error_codes"].append("PROTOCOL_LEAKAGE")

        if protocol_id == "WickednessAudit" and any(marker in normalized for marker in RUBRIC_LEAK_MARKERS):
            result["status"] = QUARANTINED if result["status"] == VALIDATED else result["status"]
            result["error_codes"].append("PROTOCOL_LEAKAGE")

        if protocol_id == "WickednessAudit" and len(normalized) > 220:
            result["warning_codes"].append("RUBRIC_TOO_VERBOSE")

    if any(count > 1 for count in seen_contents.values()):
        result["status"] = QUARANTINED if result["status"] == VALIDATED else result["status"]
        result["warning_codes"].append("DUPLICATE_STEP_CONTENT")

    result["error_codes"] = sorted(set(result["error_codes"]))
    result["warning_codes"] = sorted(set(result["warning_codes"]))
    return result


def validate_corpus(path: Path) -> tuple[list[dict], dict]:
    reports: list[dict] = []
    status_counts: Counter[str] = Counter()
    error_counts: Counter[str] = Counter()
    warning_counts: Counter[str] = Counter()

    with path.open("r", encoding="utf-8") as handle:
        for row_id, raw in enumerate(handle, start=1):
            raw = raw.strip()
            if not raw:
                report = {
                    "row_id": row_id,
                    "status": REJECTED,
                    "protocol_id": None,
                    "protocol_family": "UNKNOWN",
                    "error_codes": ["EMPTY_LINE"],
                    "warning_codes": [],
                }
            else:
                try:
                    trace = json.loads(raw)
                except json.JSONDecodeError:
                    report = {
                        "row_id": row_id,
                        "status": REJECTED,
                        "protocol_id": None,
                        "protocol_family": "UNKNOWN",
                        "error_codes": ["INVALID_JSON"],
                        "warning_codes": [],
                    }
                else:
                    report = analyze_trace(row_id, trace)

            reports.append(report)
            status_counts[report["status"]] += 1
            for code in report["error_codes"]:
                error_counts[code] += 1
            for code in report["warning_codes"]:
                warning_counts[code] += 1

    summary = {
        "corpus": str(path),
        "total_rows": len(reports),
        "status_counts": dict(status_counts),
        "error_counts": dict(error_counts),
        "warning_counts": dict(warning_counts),
    }
    return reports, summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("corpus", help="Path to a BaseN JSONL corpus")
    parser.add_argument("--summary", help="Optional JSON summary output path")
    parser.add_argument("--report", help="Optional JSONL per-row report output path")
    args = parser.parse_args()

    corpus_path = Path(args.corpus)
    if not corpus_path.exists():
        print(f"missing corpus: {corpus_path}", file=sys.stderr)
        return 1

    reports, summary = validate_corpus(corpus_path)

    if args.report:
        report_path = Path(args.report)
        with report_path.open("w", encoding="utf-8") as handle:
            for row in reports:
                handle.write(json.dumps(row, ensure_ascii=False) + "\n")

    if args.summary:
        summary_path = Path(args.summary)
        summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
