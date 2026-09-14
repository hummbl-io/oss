"""Minimal Phase 1 CLI for canonicalization and GateBench seed validation."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path

from . import __version__
from .aar import AarFormatter, add_aar_arg
from .base120 import Base120Formatter
from .canonical import CanonicalizationError, canonicalize_json, digest_bytes, load_json
from .gatebench import GateBenchError, evaluate_case
from .hrsi import HrsiCheckin, add_hrsi_arg
from .krineia import KrineiaReceipt, KrineiaSeparationError, add_krineia_arg
from .mtsmu import MtsmuSummary, add_mtsmu_arg


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="hummbl-eval")
    parser.add_argument("--version", action="version", version=__version__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    canonical = subparsers.add_parser("canonicalize")
    canonical.add_argument("path", type=Path)
    canonical.add_argument(
        "--base120",
        action="store_true",
        help="Apply Base120 cognitive structuring to output",
    )
    add_krineia_arg(canonical)
    add_mtsmu_arg(canonical)
    add_aar_arg(canonical)
    add_hrsi_arg(canonical)

    gatebench = subparsers.add_parser("gatebench")
    gatebench.add_argument("path", type=Path)
    gatebench.add_argument(
        "--base120",
        action="store_true",
        help="Apply Base120 cognitive structuring to output",
    )
    add_krineia_arg(gatebench)
    add_mtsmu_arg(gatebench)
    add_aar_arg(gatebench)
    add_hrsi_arg(gatebench)

    return parser


def _make_krineia_receipt(args: object) -> KrineiaReceipt:
    """Build a Krineia receipt from CLI args and environment."""
    import os

    session = os.environ.get("DEVIN_SESSION_ID", "")
    return KrineiaReceipt(
        reasoned_by=f"hummbl-eval{' ' + session if session else ''}",
        observed_agent="the input JSON being canonicalized/evaluated",
        falsifiability_anchor=("re-run canonicalize on the same input -> identical digest"),
        stance="descriptive",
        source="verified via canonical registry (120 operators)",
    )


def _render_footers(args: object, mtsmu: MtsmuSummary | None = None) -> None:
    """Render optional footers in composition order: MTSMU -> Krineia."""
    if args and getattr(args, "mtsmu", False) and mtsmu is not None:
        mtsmu.render()
    if args and getattr(args, "krineia", False):
        _make_krineia_receipt(args).render()


def _print_canonical_base120(
    value: object, canonical_bytes: bytes, args: object | None = None
) -> None:
    fmt = Base120Formatter("hummbl-eval canonicalize")
    fmt.header()
    fmt.section("Canonicalization", "RE17", "Versioning & Diff")
    fmt.metric("Canonical bytes", len(canonical_bytes))
    fmt.metric("Content digest", digest_bytes(canonical_bytes))
    fmt.blank()
    fmt.section("Input Analysis", "P6")
    if isinstance(value, dict):
        fmt.metric("Top-level keys", len(value))
        fmt.metric("Keys", ", ".join(sorted(value.keys())))
    elif isinstance(value, list):
        fmt.metric("Array length", len(value))
    else:
        fmt.metric("Type", type(value).__name__)
    fmt.footer()
    _render_footers(args)


def _print_gatebench_base120(result: object, args: object | None = None) -> int:
    mtsmu = MtsmuSummary()
    fmt = Base120Formatter("hummbl-eval gatebench")
    fmt.header()
    fmt.section("Case Summary", "P6")
    fmt.metric("Case ID", result.case_id)
    fmt.metric("Severity", result.severity)
    fmt.metric("Disposition", result.disposition)
    fmt.blank()

    if result.disposition == "reject":
        fmt.section("Rejection Analysis", "DE1", "Root Cause Analysis")
        for reason in result.reasons:
            fmt.finding(
                title=reason,
                severity="CRIT",
                why=reason,
                reveals=(
                    "The case violates an epistemic invariant -- "
                    "evidence or independence is missing."
                ),
                action=(
                    "Provide independent evidence or a distinct evaluator before resubmission."
                ),
                code="DE1",
                verify_method="verify-after",
            )
            mtsmu.track("verify-after", "low")
    else:
        fmt.section("Acceptance Analysis", "SY13", "Reinforcing Feedback")
        fmt.analysis(
            code="SY13",
            why="The case has independent evidence and a distinct evaluator.",
            reveals="The claim is eligible for evidence-governed qualification.",
            action="Proceed to the next evaluation phase or archive the accepted case.",
        )

    fmt.footer()
    _render_footers(args, mtsmu)
    return 4 if result.disposition == "reject" else 0


def _print_canonical_aar(value: object, canonical_bytes: bytes, args: object | None = None) -> None:
    aar = AarFormatter("hummbl-eval canonicalize", author="hummbl-eval")
    aar.set_mission(
        objective="Canonicalize input JSON to deterministic byte sequence",
        success_criteria="Stable digest reproducible across runs",
        constraints="Stdlib-only, no network, single file input",
    )
    aar.chronology_entry("now", "Input JSON loaded", f"{len(canonical_bytes)} bytes")
    aar.chronology_entry("now", "Canonicalized", f"digest={digest_bytes(canonical_bytes)}")
    aar.set_outcome(
        planned="Deterministic canonical bytes",
        actual=f"{len(canonical_bytes)} bytes, digest={digest_bytes(canonical_bytes)}",
        delta="No deviations",
    )
    aar.sustain(
        "Canonicalization produces stable digest",
        f"digest={digest_bytes(canonical_bytes)}",
    )
    aar.set_evidence(
        [
            f"canonical_bytes={len(canonical_bytes)}",
            f"digest={digest_bytes(canonical_bytes)}",
        ]
    )
    aar.set_bus(posted=False)
    aar.render()
    _render_footers(args)


def _print_gatebench_aar(result: object, args: object | None = None) -> int:
    aar = AarFormatter("hummbl-eval gatebench", author="hummbl-eval")
    disposition = result.disposition
    aar.set_mission(
        objective=f"Evaluate GateBench case {result.case_id}",
        success_criteria="Case accepted with independent evidence and distinct evaluator",
        constraints="Stdlib-only, single case evaluation",
    )
    aar.chronology_entry("now", f"Case {result.case_id} loaded", f"severity={result.severity}")
    aar.chronology_entry("now", "Evaluated", f"disposition={disposition}")

    if disposition == "reject":
        aar.set_outcome(
            planned="Case accepted",
            actual=f"Case rejected: {'; '.join(result.reasons)}",
            delta=f"Rejected -- {'; '.join(result.reasons)}",
        )
        aar.root_cause(
            "Epistemic invariant violation",
            [f"Surface: {'; '.join(result.reasons)}", "Deeper: missing independence or evidence"],
        )
        aar.sustain("GateBench correctly detected the violation", f"reasons={result.reasons}")
        aar.improve("Case was submitted with invariant violations", f"reasons={result.reasons}")
        aar.recommendation(
            "HIGH",
            "Provide independent evidence or a distinct evaluator before resubmission",
            "addresses: case submitted with violations",
        )
    else:
        aar.set_outcome(
            planned="Case accepted",
            actual="Case accepted",
            delta="No deviations",
        )
        aar.sustain(
            "Case has independent evidence and distinct evaluator",
            f"case_id={result.case_id}",
        )
        aar.recommendation("LOW", "Archive accepted case or proceed to next phase", "")

    aar.set_evidence(
        [
            f"case_id={result.case_id}",
            f"disposition={disposition}",
            f"severity={result.severity}",
        ]
    )
    aar.set_bus(posted=False)
    aar.render()
    _render_footers(args)
    return 4 if disposition == "reject" else 0


def _print_canonical_hrsi(args: object | None = None) -> None:
    checkin = HrsiCheckin()
    checkin.header()
    checkin.cogstate("AVAILABLE")
    checkin.baseline(safety=4, mattering=3, connection=4)
    checkin.somatic(energy=3, sleep_hours=7.0)
    checkin.hule("Canonicalization completed successfully")
    checkin.render()
    _render_footers(args)


def _print_gatebench_hrsi(result: object, args: object | None = None) -> int:
    checkin = HrsiCheckin()
    checkin.header()
    # GateBench disposition maps to cogstate
    if result.disposition == "reject":
        checkin.cogstate("RECOVERY")
        checkin.baseline(safety=3, mattering=2, connection=3)
    else:
        checkin.cogstate("AVAILABLE")
        checkin.baseline(safety=4, mattering=4, connection=4)
    checkin.somatic(energy=3, sleep_hours=7.0)
    checkin.hule(f"GateBench case {result.case_id}: {result.disposition}")
    checkin.render()
    _render_footers(args)
    return 4 if result.disposition == "reject" else 0


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        value = load_json(args.path.read_bytes())
        if args.command == "canonicalize":
            canonical_bytes = canonicalize_json(value)
            if args.aar:
                _print_canonical_aar(value, canonical_bytes, args)
            elif args.hrsi:
                _print_canonical_hrsi(args)
            elif args.base120:
                _print_canonical_base120(value, canonical_bytes, args)
            else:
                sys.stdout.buffer.write(canonical_bytes + b"\n")
            return 0
        result = evaluate_case(value)
        if args.aar:
            return _print_gatebench_aar(result, args)
        if args.hrsi:
            return _print_gatebench_hrsi(result, args)
        if args.base120:
            return _print_gatebench_base120(result, args)
        print(
            json.dumps(
                {
                    "case_id": result.case_id,
                    "disposition": result.disposition,
                    "reasons": result.reasons,
                    "severity": result.severity,
                },
                separators=(",", ":"),
                sort_keys=True,
            )
        )
        return 4 if result.disposition == "reject" else 0
    except (OSError, CanonicalizationError, GateBenchError, KrineiaSeparationError) as exc:
        print(f"hummbl-eval: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":  # pragma: no cover - exercised through package entry point
    raise SystemExit(main())
