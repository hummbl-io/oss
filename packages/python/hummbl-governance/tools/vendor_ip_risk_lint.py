#!/usr/bin/env python3
"""Validate the AI Vendor IP Risk Register.

The register is Markdown for human review, but the vendor table is structured
enough to gate the main policy invariants:

- risk is RED, YELLOW, or GREEN
- every row has sources or REVIEW_REQUIRED
- RED vendors are not allowed for T2/T3
- YELLOW vendors make T2/T3 conditional in notes / allowed-tier language
- last_reviewed dates are ISO dates
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path


ALLOWED_RISKS = {"RED", "YELLOW", "GREEN"}
SENSITIVE_TIERS = {"T2", "T3"}
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
URL_RE = re.compile(r"https?://")


@dataclass(frozen=True)
class Finding:
    row: int
    rule: str
    message: str


@dataclass(frozen=True)
class VendorRow:
    row: int
    vendor: str
    product: str
    risk: str
    output_ownership: str
    training_default: str
    human_review: str
    allowed_tiers: str
    source_urls: str
    last_reviewed: str
    notes: str


def _split_markdown_row(line: str) -> list[str]:
    stripped = line.strip()
    if not stripped.startswith("|") or not stripped.endswith("|"):
        return []
    return [cell.strip() for cell in stripped.strip("|").split("|")]


def parse_vendor_rows(markdown: str) -> list[VendorRow]:
    rows: list[VendorRow] = []
    in_register = False
    header_seen = False

    for line_no, line in enumerate(markdown.splitlines(), start=1):
        if line.strip() == "## Vendor register":
            in_register = True
            continue
        if in_register and line.startswith("## ") and line.strip() != "## Vendor register":
            break
        if not in_register:
            continue

        cells = _split_markdown_row(line)
        if not cells:
            continue
        if cells[0] == "Vendor":
            header_seen = True
            continue
        if set(cells[0]) <= {"-"}:
            continue
        if not header_seen:
            continue
        if len(cells) != 10:
            rows.append(
                VendorRow(
                    row=line_no,
                    vendor=cells[0] if cells else "",
                    product="",
                    risk="",
                    output_ownership="",
                    training_default="",
                    human_review="",
                    allowed_tiers="",
                    source_urls="",
                    last_reviewed="",
                    notes=f"MALFORMED_CELL_COUNT:{len(cells)}",
                )
            )
            continue
        rows.append(VendorRow(line_no, *cells))

    return rows


def _tier_set(allowed_tiers: str) -> set[str]:
    return set(re.findall(r"\bT[0-3]\b", allowed_tiers))


def lint_rows(rows: list[VendorRow]) -> list[Finding]:
    findings: list[Finding] = []
    if not rows:
        return [Finding(0, "missing-register", "no vendor rows found")]

    for row in rows:
        if row.notes.startswith("MALFORMED_CELL_COUNT"):
            findings.append(Finding(row.row, "malformed-row", row.notes))
            continue

        if row.risk not in ALLOWED_RISKS:
            findings.append(
                Finding(row.row, "invalid-risk", f"{row.vendor}: risk={row.risk!r}")
            )

        if not row.source_urls or (
            row.source_urls != "REVIEW_REQUIRED" and not URL_RE.search(row.source_urls)
        ):
            findings.append(
                Finding(row.row, "missing-source", f"{row.vendor}: missing source URL")
            )

        if not DATE_RE.match(row.last_reviewed):
            findings.append(
                Finding(
                    row.row,
                    "invalid-date",
                    f"{row.vendor}: last_reviewed={row.last_reviewed!r}",
                )
            )
        else:
            try:
                date.fromisoformat(row.last_reviewed)
            except ValueError:
                findings.append(
                    Finding(
                        row.row,
                        "invalid-date",
                        f"{row.vendor}: last_reviewed={row.last_reviewed!r}",
                    )
                )

        tiers = _tier_set(row.allowed_tiers)
        if row.risk == "RED" and tiers & SENSITIVE_TIERS:
            findings.append(
                Finding(
                    row.row,
                    "red-sensitive-tier",
                    f"{row.vendor}: RED row allows {sorted(tiers & SENSITIVE_TIERS)}",
                )
            )

        if row.risk == "YELLOW" and tiers & SENSITIVE_TIERS:
            if "owner approval" not in (row.allowed_tiers + " " + row.notes).lower():
                findings.append(
                    Finding(
                        row.row,
                        "yellow-sensitive-without-approval",
                        f"{row.vendor}: YELLOW T2/T3 row lacks owner approval language",
                    )
                )

    return findings


def lint_markdown(markdown: str) -> list[Finding]:
    return lint_rows(parse_vendor_rows(markdown))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "path",
        nargs="?",
        default="docs/standards/AI_VENDOR_IP_RISK_REGISTER.md",
    )
    args = parser.parse_args(argv)

    text = Path(args.path).read_text(encoding="utf-8")
    findings = lint_markdown(text)
    if not findings:
        return 0

    print("ERROR: AI vendor IP risk register validation failed", file=sys.stderr)
    for finding in findings:
        print(
            f"  row {finding.row}: {finding.rule}: {finding.message}",
            file=sys.stderr,
        )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
