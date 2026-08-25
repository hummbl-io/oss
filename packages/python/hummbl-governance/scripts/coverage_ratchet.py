"""Coverage matrix ratchet gate — prevents regression in evidence validation.

Compares current evidence validation results against a frozen baseline.
Fails if the validated row count regresses below the baseline, or if a
previously-validated row identity is no longer passing (row-identity ratchet).

The baseline file (docs/coverage/ratchet-baseline.json) is a committed artifact.
It can only be raised by an explicit baseline-update commit; CI never lowers it.

Ratchet policy (two layers):
  1. Count ratchet: current_validated < baseline_validated → FAIL
  2. Row-identity ratchet: if baseline includes validated_rows, each baseline
     row identity (matrix + control_id) must still have status=pass in the
     current report. A baseline row that is missing or failing → FAIL even
     if the total count is stable or higher.

Promotion threshold:
  When validated_pct >= PROMOTION_THRESHOLD (default 50%), the CI job
  should flip continue-on-error to false. This script prints a promotion
  notice when the threshold is reached but does not auto-promote.

Exit codes:
  0 — ratchet passes (count >= baseline AND all baseline rows still validate)
  1 — ratchet fails (count regression OR row-identity regression)
  2 — baseline file missing or invalid

Usage:
  python scripts/coverage_ratchet.py [--baseline docs/coverage/ratchet-baseline.json]
                                     [--report docs/coverage/EVIDENCE_VALIDATION.json]
                                     [--promote-threshold 50]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def _load_baseline(path: Path) -> dict:
    """Load the ratchet baseline file."""
    if not path.exists():
        print(f"ERROR: Baseline file not found: {path}", file=sys.stderr)
        print("Create it with: python scripts/coverage_ratchet.py --init-baseline", file=sys.stderr)
        sys.exit(2)
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if "validated_count" not in data:
        print(f"ERROR: Baseline file missing 'validated_count' key: {path}", file=sys.stderr)
        sys.exit(2)
    return data


def _load_report(path: Path) -> dict:
    """Load the evidence validation JSON report."""
    if not path.exists():
        print(f"ERROR: Validation report not found: {path}", file=sys.stderr)
        print("Run: python scripts/build_evidence_validation_report.py", file=sys.stderr)
        sys.exit(2)
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _compute_current(report: dict) -> dict:
    """Compute aggregate stats from the validation report."""
    total_ful = sum(d["totals"]["fulfilled"] for d in report.values())
    total_validated = sum(d["fulfilled_validation"]["rows_passed"] for d in report.values())
    total_failed = sum(d["fulfilled_validation"]["rows_failed"] for d in report.values())
    pct = round(100.0 * total_validated / total_ful, 1) if total_ful else 0.0
    return {
        "fulfilled_count": total_ful,
        "validated_count": total_validated,
        "failed_count": total_failed,
        "validated_pct": pct,
    }


def _extract_validated_rows(report: dict) -> list[dict]:
    """Extract validated row identities (matrix + control_id) from the report.

    Only rows with status=pass are included. Line numbers are intentionally
    excluded — they shift on matrix edits and are not stable identifiers.
    """
    identities: list[dict] = []
    for matrix_name, matrix_data in report.items():
        rows = matrix_data.get("rows", [])
        for row in rows:
            if row.get("status") == "pass":
                identities.append({
                    "matrix": matrix_name,
                    "control_id": row.get("control_id"),
                })
    return identities


def _check_row_identities(
    baseline_rows: list[dict], report: dict
) -> tuple[list[dict], list[dict]]:
    """Check that all baseline row identities still validate.

    Returns (preserved, lost) where:
      preserved = list of baseline rows that still pass
      lost = list of baseline rows that are missing or failing
    """
    # Build a lookup of current passing rows: (matrix, control_id) -> row
    current_passing: dict[tuple[str, str], dict] = {}
    for matrix_name, matrix_data in report.items():
        for row in matrix_data.get("rows", []):
            if row.get("status") == "pass":
                key = (matrix_name, row.get("control_id", ""))
                current_passing[key] = row

    preserved: list[dict] = []
    lost: list[dict] = []
    for baseline_row in baseline_rows:
        key = (baseline_row.get("matrix", ""), baseline_row.get("control_id", ""))
        if key in current_passing:
            preserved.append(baseline_row)
        else:
            lost.append(baseline_row)
    return preserved, lost


def main() -> int:
    parser = argparse.ArgumentParser(description="Coverage matrix ratchet gate")
    parser.add_argument(
        "--baseline", type=str, default="docs/coverage/ratchet-baseline.json",
        help="Path to ratchet baseline file",
    )
    parser.add_argument(
        "--report", type=str, default="docs/coverage/EVIDENCE_VALIDATION.json",
        help="Path to evidence validation JSON report",
    )
    parser.add_argument(
        "--promote-threshold", type=float, default=50.0,
        help="Validated %% at which the CI job should flip to blocking (default: 50)",
    )
    parser.add_argument(
        "--init-baseline", action="store_true",
        help="Initialize or raise the baseline to current validated count",
    )
    parser.add_argument(
        "--force-lower", action="store_true",
        help="Allow --init-baseline to LOWER the baseline (requires --reason)",
    )
    parser.add_argument(
        "--reason", type=str, default="",
        help="Justification string required when using --force-lower",
    )
    args = parser.parse_args()

    baseline_path = Path(args.baseline)
    report_path = Path(args.report)

    report = _load_report(report_path)
    current = _compute_current(report)

    if args.init_baseline:
        validated_rows = _extract_validated_rows(report)

        # Baseline-lowering protection: check if existing baseline exists
        # and would be lowered by this init.
        if baseline_path.exists():
            with baseline_path.open("r", encoding="utf-8") as f:
                existing = json.load(f)
            existing_count = existing.get("validated_count", 0)
            if current["validated_count"] < existing_count:
                if not args.force_lower:
                    new_count = current['validated_count']
                    print(
                        f"::error::REFUSED: --init-baseline would lower baseline "
                        f"from {existing_count} to {new_count}"
                    )
                    print("::error::Use --force-lower --reason \"...\" to override with justification.")
                    print("::error::Lowering the baseline allows regressions to pass the ratchet silently.")
                    return 1
                if not args.reason:
                    print("::error::REFUSED: --force-lower requires --reason \"...\" justification string.")
                    return 1
                new_count = current['validated_count']
                print(f"::warning::BASELINE LOWERED with --force-lower: {existing_count} -> {new_count}")
                print(f"::warning::Reason: {args.reason}")

        baseline_data: dict = {
            "validated_count": current["validated_count"],
            "fulfilled_count": current["fulfilled_count"],
            "validated_pct": current["validated_pct"],
            "validated_rows": validated_rows,
            "description": (
                "Frozen baseline for coverage-matrix ratchet. CI fails if "
                "validated_count drops below this value OR if any validated_rows "
                "identity is no longer passing. Raise by re-running "
                "--init-baseline after improving evidence coverage."
            ),
        }
        if args.force_lower and args.reason:
            baseline_data["lower_reason"] = args.reason
        baseline_path.parent.mkdir(parents=True, exist_ok=True)
        with baseline_path.open("w", encoding="utf-8") as f:
            json.dump(baseline_data, f, indent=2, ensure_ascii=False)
            f.write("\n")
        print(f"BASELINE SET: {baseline_path}")
        print(f"  validated_count: {current['validated_count']}")
        print(f"  fulfilled_count: {current['fulfilled_count']}")
        print(f"  validated_pct: {current['validated_pct']}%")
        print(f"  validated_rows: {len(validated_rows)} identities captured")
        return 0

    baseline = _load_baseline(baseline_path)
    baseline_count = baseline["validated_count"]
    current_count = current["validated_count"]
    baseline_rows = baseline.get("validated_rows", [])

    print("RATCHET CHECK")
    print(f"  baseline validated: {baseline_count}")
    print(f"  current validated:  {current_count}")
    print(f"  current fulfilled:  {current['fulfilled_count']}")
    print(f"  current pct:        {current['validated_pct']}%")
    if baseline_rows:
        print(f"  baseline row identities: {len(baseline_rows)}")

    # Layer 1: Count ratchet
    count_failed = False
    if current_count < baseline_count:
        print(f"\n::error::RATCHET FAILED: validated count regressed from {baseline_count} to {current_count}")
        reg = baseline_count - current_count
        print(f"::error::Regression of {reg} validated rows. Fix the broken evidence refs or restore the baseline.")
        count_failed = True

    # Layer 2: Row-identity ratchet
    row_identity_failed = False
    if baseline_rows:
        preserved, lost = _check_row_identities(baseline_rows, report)
        if lost:
            print(f"\n::error::ROW IDENTITY FAILED: {len(lost)} baseline row(s) no longer validate")
            for lost_row in lost:
                cid = lost_row.get("control_id", "?")
                mtx = lost_row.get("matrix", "?")
                print(f"::error::  LOST: {mtx} / {cid}")
            row_identity_failed = True
        else:
            print(f"\n::notice::Row identity check: all {len(preserved)} baseline rows still validate")

    if count_failed or row_identity_failed:
        return 1

    if current_count > baseline_count:
        delta = current_count - baseline_count
        print(f"\n::notice::RATCHET PASSED with improvement: +{delta} validated rows above baseline")
        print("::notice::To raise the baseline, run: python scripts/coverage_ratchet.py --init-baseline")
    else:
        print(f"\n::notice::RATCHET PASSED: validated count matches baseline ({current_count})")

    # Promotion threshold check
    if current["validated_pct"] >= args.promote_threshold:
        pct = current['validated_pct']
        print(f"\n::warning::PROMOTION THRESHOLD REACHED: {pct}% >= {args.promote_threshold}%")
        print("::warning::Consider flipping continue-on-error to false in .github/workflows/ci.yml")
    else:
        gap = args.promote_threshold - current["validated_pct"]
        print(f"\n  promotion threshold: {args.promote_threshold}% (gap: {gap:.1f}pp)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
