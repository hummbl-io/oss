#!/usr/bin/env python3
"""Track PyPI download stats for HUMMBL OSS packages.

Scrapes pypistats.org daily, appends to a CSV log, and flags when the
baseline download rate deviates from the established dogfooding pattern.

Stdlib-only — no third-party dependencies. Uses urllib for HTTP and
csv/json for data handling.

Usage:
    python tools/scripts/pypi_download_tracker.py          # append today's stats
    python tools/scripts/pypi_download_tracker.py --report  # print trend report
    python tools/scripts/pypi_download_tracker.py --check   # flag anomalies (exit 1 if found)

Data file: tools/data/pypi-downloads.csv
"""
from __future__ import annotations

import argparse
import csv
import datetime
import json
import os
import statistics
import sys
import urllib.request
from pathlib import Path

# ─── Configuration ───────────────────────────────────────────────────────────

PACKAGES = [
    "hummbl-governance",
    "hummbl-bus",
    "hummbl-cognition",
    "hummbl-tuples",
    "hummbl-bif",
    "base120",
    "governed-compression",
    "hummbl",
    "hummbl-kernel",
]

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DATA_FILE = DATA_DIR / "pypi-downloads.csv"

PYPISTATS_RECENT = "https://pypistats.org/api/packages/{pkg}/recent"
PYPISTATS_OVERALL = "https://pypistats.org/api/packages/{pkg}/overall?mirrors=false"

REQUEST_TIMEOUT = 15
RATE_LIMIT_SLEEP = 1.5  # seconds between API calls

CSV_HEADERS = [
    "date",
    "package",
    "downloads_7day",
    "downloads_30day",
    "downloads_total",
]

# ─── HTTP ────────────────────────────────────────────────────────────────────


def _fetch_json(url: str) -> dict:
    """Fetch JSON from a URL using stdlib urllib."""
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "hummbl-oss-pypi-tracker/1.0"},
    )
    with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
        return json.loads(resp.read())


def fetch_recent(pkg: str) -> tuple[int, int]:
    """Return (7-day, 30-day) download counts for a package."""
    data = _fetch_json(PYPISTATS_RECENT.format(pkg=pkg))
    d = data.get("data", {})
    return d.get("last_week", 0), d.get("last_month", 0)


def fetch_total(pkg: str) -> int:
    """Return total all-time downloads for a package.

    The pypistats overall endpoint returns a list of {category, date, downloads}
    objects. We sum the downloads field.
    """
    try:
        data = _fetch_json(PYPISTATS_OVERALL.format(pkg=pkg))
        entries = data.get("data", [])
        if isinstance(entries, list):
            return sum(e.get("downloads", 0) for e in entries)
        elif isinstance(entries, int):
            return entries
        return 0
    except Exception:
        return -1  # unknown


# ─── CSV I/O ─────────────────────────────────────────────────────────────────


def ensure_data_file() -> None:
    """Create data dir and CSV with headers if they don't exist."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not DATA_FILE.exists():
        with open(DATA_FILE, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_HEADERS)
            writer.writeheader()


def append_row(date: str, package: str, d7: int, d30: int, total: int) -> None:
    """Append a single row to the CSV."""
    with open(DATA_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_HEADERS)
        writer.writerow(
            {
                "date": date,
                "package": package,
                "downloads_7day": d7,
                "downloads_30day": d30,
                "downloads_total": total,
            }
        )


def read_all_rows() -> list[dict]:
    """Read all rows from the CSV."""
    if not DATA_FILE.exists():
        return []
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def today_str() -> str:
    return datetime.date.today().isoformat()


def has_today_entry(rows: list[dict], package: str) -> bool:
    today = today_str()
    return any(r["date"] == today and r["package"] == package for r in rows)


# ─── Collection ──────────────────────────────────────────────────────────────


def collect_today() -> None:
    """Fetch and append today's stats for all packages."""
    ensure_data_file()
    rows = read_all_rows()
    today = today_str()

    for pkg in PACKAGES:
        if has_today_entry(rows, pkg):
            print(f"  {pkg}: already have today's entry, skipping")
            continue

        try:
            d7, d30 = fetch_recent(pkg)
            print(f"  {pkg}: 7d={d7}, 30d={d30}", end="")
        except Exception as e:
            print(f"  {pkg}: ERROR fetching recent stats: {e}")
            d7, d30 = -1, -1

        # Rate limit pause before total fetch
        import time

        time.sleep(RATE_LIMIT_SLEEP)

        try:
            total = fetch_total(pkg)
            print(f", total={total}")
        except Exception as e:
            print(f", total=ERROR: {e}")
            total = -1

        append_row(today, pkg, d7, d30, total)

        time.sleep(RATE_LIMIT_SLEEP)

    print(f"\nData appended to {DATA_FILE}")


# ─── Reporting ───────────────────────────────────────────────────────────────


def report() -> None:
    """Print a trend report from the collected data."""
    rows = read_all_rows()
    if not rows:
        print("No data yet. Run without --report first to collect stats.")
        return

    print(f"{'Package':30s} {'Latest 7d':>10s} {'Latest 30d':>11s} {'Total':>10s} {'Entries':>8s} {'30d Trend':>10s}")
    print("-" * 85)

    # Group by package
    by_pkg: dict[str, list[dict]] = {}
    for r in rows:
        by_pkg.setdefault(r["package"], []).append(r)

    for pkg in PACKAGES:
        pkg_rows = by_pkg.get(pkg, [])
        if not pkg_rows:
            print(f"{pkg:30s} {'no data':>10s}")
            continue

        latest = pkg_rows[-1]
        d7 = latest["downloads_7day"]
        d30 = latest["downloads_30day"]
        total = latest["downloads_total"]
        entries = len(pkg_rows)

        # Calculate 30-day trend: compare last entry vs first entry
        if len(pkg_rows) >= 2:
            first_d30 = int(pkg_rows[0]["downloads_30day"])
            last_d30 = int(d30)
            if first_d30 > 0:
                pct = ((last_d30 - first_d30) / first_d30) * 100
                trend = f"{pct:+.0f}%"
            else:
                trend = "new"
        else:
            trend = "—"

        print(f"{pkg:30s} {d7:>10s} {d30:>11s} {total:>10s} {entries:>8d} {trend:>10s}")

    # Summary
    total_30d = sum(int(r["downloads_30day"]) for r in rows if r["date"] == rows[-1]["date"])
    print(f"\nTotal 30-day downloads (latest snapshot): {total_30d}")
    print(f"Data file: {DATA_FILE}")
    print(f"Entries: {len(rows)} rows across {len(by_pkg)} packages")


# ─── Anomaly Detection ───────────────────────────────────────────────────────


def check_anomalies() -> int:
    """Flag when baseline deviates from the dogfooding pattern.

    Returns exit code: 0 = no anomalies, 1 = anomalies detected.

    Detection rules:
    1. Sudden spike: 7-day count is >3x the rolling average of previous 7-day counts
    2. Sustained growth: 30-day count increased >50% over a 7-day window
    3. New package activity: package that had <10 downloads suddenly gets >50
    """
    rows = read_all_rows()
    if not rows:
        print("No data to analyze.")
        return 0

    by_pkg: dict[str, list[dict]] = {}
    for r in rows:
        by_pkg.setdefault(r["package"], []).append(r)

    anomalies: list[str] = []

    for pkg, pkg_rows in by_pkg.items():
        if len(pkg_rows) < 3:
            continue

        # Get 7-day counts as integers
        d7_values = [int(r["downloads_7day"]) for r in pkg_rows if r["downloads_7day"] != "-1"]
        d30_values = [int(r["downloads_30day"]) for r in pkg_rows if r["downloads_30day"] != "-1"]

        if len(d7_values) < 3:
            continue

        latest_d7 = d7_values[-1]

        # Rule 1: Sudden spike (>3x rolling average of previous entries)
        if len(d7_values) >= 4:
            prior_avg = statistics.mean(d7_values[:-1])
            if prior_avg > 0 and latest_d7 > prior_avg * 3:
                anomalies.append(
                    f"SPIKE: {pkg} 7-day={latest_d7} vs prior avg={prior_avg:.0f} "
                    f"({latest_d7 / prior_avg:.1f}x)"
                )

        # Rule 2: Sustained growth (30-day increased >50% over available window)
        if len(d30_values) >= 7:
            week_ago_d30 = d30_values[-7]
            latest_d30 = d30_values[-1]
            if week_ago_d30 > 0 and latest_d30 > week_ago_d30 * 1.5:
                pct = ((latest_d30 - week_ago_d30) / week_ago_d30) * 100
                anomalies.append(
                    f"GROWTH: {pkg} 30-day went from {week_ago_d30} to {latest_d30} "
                    f"({pct:+.0f}% in 7 days)"
                )

        # Rule 3: New package activity (was <10, now >50)
        if len(d7_values) >= 2:
            early_avg = statistics.mean(d7_values[:max(1, len(d7_values) // 3)])
            if early_avg < 10 and latest_d7 > 50:
                anomalies.append(
                    f"NEW ACTIVITY: {pkg} was ~{early_avg:.0f}/week, now {latest_d7}/week"
                )

    if anomalies:
        print("ANOMALIES DETECTED:")
        for a in anomalies:
            print(f"  ⚠ {a}")
        return 1
    else:
        print("No anomalies detected. Baseline is stable.")
        return 0


# ─── Main ────────────────────────────────────────────────────────────────────


def main() -> int:
    parser = argparse.ArgumentParser(description="Track PyPI download stats for HUMMBL OSS packages.")
    parser.add_argument("--report", action="store_true", help="Print trend report from collected data")
    parser.add_argument("--check", action="store_true", help="Flag anomalies in download patterns")
    parser.add_argument("--collect", action="store_true", help="Collect today's stats (default action)")
    args = parser.parse_args()

    if args.report:
        report()
        return 0
    elif args.check:
        return check_anomalies()
    else:
        collect_today()
        return 0


if __name__ == "__main__":
    sys.exit(main())
