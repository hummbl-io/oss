#!/usr/bin/env python3
"""Generate the package adoption-signals report.

Reads committed data only (read-only, offline):
  - tools/data/pypi-downloads.csv       download time series (demand evidence)
  - docs/architecture/PACKAGES.md       tree vs PyPI release state
  - packages/**/product.json            product-admission manifests
  - tools/scripts/pypi_download_tracker.py PACKAGES list (tracked set)

Emits docs/architecture/ADOPTION-SIGNALS.md. Use --check to verify the
committed report is current (fails on drift, same contract as
script_contracts.py).

Nothing here builds analytics infrastructure: the report restates
already-committed data and labels every conclusion as evidence or
assumption per issue #215.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
DOC = ROOT / "docs" / "architecture" / "ADOPTION-SIGNALS.md"
CSV_FILE = ROOT / "tools" / "data" / "pypi-downloads.csv"
PACKAGES_MD = ROOT / "docs" / "architecture" / "PACKAGES.md"
TRACKER = ROOT / "tools" / "scripts" / "pypi_download_tracker.py"


def tracked_packages() -> list[str]:
    m = re.search(r"PACKAGES\s*=\s*\[([^\]]+)\]", TRACKER.read_text("utf-8"))
    return re.findall(r'"([^"]+)"', m.group(1)) if m else []


def download_rows() -> dict[str, dict]:
    """Latest valid snapshot per package plus series stats."""
    rows: dict[str, list[dict]] = {}
    with CSV_FILE.open(newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            rows.setdefault(r["package"], []).append(r)
    out: dict[str, dict] = {}
    for pkg, series in rows.items():
        valid = [r for r in series if r["downloads_30day"] != "-1"]
        latest = valid[-1] if valid else None
        out[pkg] = {
            "entries": len(series),
            "errors": len(series) - len(valid),
            "d7": int(latest["downloads_7day"]) if latest else None,
            "d30": int(latest["downloads_30day"]) if latest else None,
            "total": int(latest["downloads_total"]) if latest else None,
            "first_date": series[0]["date"],
            "last_date": series[-1]["date"],
        }
    return out


def release_state() -> dict[str, dict[str, str]]:
    """name -> {tree, pypi, live} parsed from PACKAGES.md tables."""
    state: dict[str, dict[str, str]] = {}
    live = False
    for line in PACKAGES_MD.read_text("utf-8").splitlines():
        if line.startswith("### "):
            live = "Live" in line and "none" not in line
        m = re.match(r"\| `([^`]+)` \| ([^|]+) \| ([^|]+) \|", line)
        if m:
            state[m.group(1)] = {
                "tree": m.group(2).strip(),
                "pypi": m.group(3).strip(),
                "live": live,
            }
    return state


def tree_versions() -> dict[str, str]:
    out = {}
    for pp in sorted(ROOT.glob("packages/*/*/pyproject.toml")):
        try:
            out[pp.parent.name] = tomllib.loads(pp.read_text("utf-8"))["project"]["version"]
        except Exception:
            continue
    return out


def product_manifests() -> dict[str, dict]:
    out = {}
    for pj in sorted(ROOT.glob("packages/*/*/product.json")):
        try:
            d = json.loads(pj.read_text("utf-8"))
            out[d.get("product_id", pj.parent.name)] = d
        except Exception:
            continue
    return out


def priority(live: bool, d30: int | None, lag: bool) -> tuple[str, str]:
    """Transparent heuristic — assumption, not evidence (see doc header)."""
    if not live:
        return "P3", "in-tree only; no release to maintain"
    if d30 is None:
        return "P2", "live but no valid download signal — collect before prioritizing"
    if lag:
        return "P1", "live with demand signal and unreleased tree changes"
    return "P1" if d30 >= 100 else "P2", ("live with demand signal" if d30 >= 100 else "live, low signal")


def render() -> str:
    tracked = tracked_packages()
    dl = download_rows()
    rel = release_state()
    versions = tree_versions()
    prods = product_manifests()
    data_date = max((v["last_date"] for v in dl.values()), default="no data")

    L = [
        "<!-- GENERATED FILE — regenerate with `python tools/scripts/adoption_signals.py`.",
        "Verify with `--check`; do not edit by hand. -->",
        "",
        "# Adoption signals — package activity and offering map",
        "",
        f"Data as of: {data_date} (issue #215). Read-only restatement of committed",
        "data. Download counts are **demand evidence**; priority classes and",
        "offering fit are **assumptions** and are labeled as such.",
        "",
        "## Canonical data sources",
        "",
        "| Source | Role |",
        "|--------|------|",
        "| `tools/data/pypi-downloads.csv` | download time series collected by `pypi_download_tracker.py` |",
        "| `docs/architecture/PACKAGES.md` | tree vs registry release state |",
        "| `packages/**/product.json` | product-admission manifests (`product-admission-v1` schema) |",
        "| `packages/*/pyproject.toml` | authoritative tree version |",
        "",
        "## Package activity and release state",
        "",
        "| Package | 30d downloads (latest) | Data points | Errors | Tree | PyPI | State |",
        "|---------|---------------------:|------------:|-------:|------|------|-------|",
    ]
    for pkg in tracked:
        d = dl.get(pkg, {})
        r = rel.get(pkg, {})
        live = "live" if r.get("live") else ("in-tree" if pkg in versions else "?")
        L.append(
            f"| `{pkg}` | {d.get('d30') if d.get('d30') is not None else 'no valid data'} "
            f"| {d.get('entries', 0)} | {d.get('errors', 0)} "
            f"| {versions.get(pkg, r.get('tree', '?'))} | {r.get('pypi', '—')} | {live} |"
        )
    untracked = [p for p in versions if p not in tracked]
    L += [
        "",
        f"Tracked for downloads: {len(tracked)} packages. In-tree but untracked:",
        f"{len(untracked)} (see `pypi_download_tracker.py` PACKAGES list).",
        "",
        "## Maintenance priority (ASSUMPTION — transparent heuristic, not demand)",
        "",
        "| Package | Priority | Rationale |",
        "|---------|----------|-----------|",
    ]
    for pkg in sorted(versions):
        d = dl.get(pkg, {})
        r = rel.get(pkg, {})
        lag = (
            bool(r)
            and versions.get(pkg) != r.get("pypi")
            and r.get("pypi")
            not in (
                "—",
                "",
            )
        )
        p, why = priority(bool(r.get("live")), d.get("d30"), lag)
        L.append(f"| `{pkg}` | {p} | {why} |")

    L += [
        "",
        "## Offering map",
        "",
        "Packages with a product-admission manifest (`product.json`) mapped to a",
        "documented offering:",
        "",
        "| Product | Source package | Lifecycle | Admission | Blockers |",
        "|---------|---------------|-----------|-----------|----------|",
    ]
    for pid, d in prods.items():
        adm = d.get("admission", {})
        L.append(
            f"| `{pid}` | `{d.get('canonical_source', {}).get('path', '?')}` "
            f"| {d.get('lifecycle', '?')} | {adm.get('decision', '?')} "
            f"| {', '.join(adm.get('blockers', [])) or '—'} |"
        )
    L += [
        "",
        f"**{len(prods)} of {len(versions)} packages have product manifests.** "
        "Every other package↔offering mapping is an assumption with no",
        "demand evidence behind it and is intentionally not asserted here.",
        "",
        "## Evidence vs assumptions",
        "",
        "**Evidence (from committed data):**",
        "- Download counts per tracked package (sparse: "
        f"{sum(v['entries'] for v in dl.values())} rows; treat trends as weak signal).",
        "- Tree vs PyPI version lag per PACKAGES.md.",
        "- Product-admission decisions and blockers per committed manifests.",
        "",
        "**Assumptions (labeled, not evidence):**",
        "- Priority classes above — a heuristic for attention, not measured demand.",
        "- Any claim that a package maps to a customer offering without a",
        "  `product.json` — no such mapping is asserted.",
        "- Interpretation of download counts as customer demand — dogfooding and",
        "  CI traffic are known confounders noted in `pypi_download_tracker.py`.",
        "",
    ]
    return "\n".join(L)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    out = render()
    if args.check:
        if DOC.exists() and DOC.read_text("utf-8") == out:
            print(f"adoption signals: OK ({len(tracked_packages())} tracked, {len(product_manifests())} products)")
            return 0
        print(f"FAIL {DOC} is stale — run the generator", file=sys.stderr)
        return 1
    DOC.write_text(out, "utf-8")
    print(f"wrote {DOC.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
