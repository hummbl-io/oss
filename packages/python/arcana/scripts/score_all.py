"""Score every article under outputs/ and append history for drift detection.

Walks outputs/YYYY-MM-DD/<slug>/article.md, runs score_paideia on each,
writes the per-article score JSON to paideia/scores/<slug>.json, and
appends one row per score to paideia/history.tsv. The history file
accumulates across runs so you can spot drift when the scorer version
or underlying prompts change.

CPU-only. No Ollama calls.

Usage:
    python score_all.py
    python score_all.py --since 2026-04-24
    python score_all.py --only-new   # skip articles that already have a score JSON
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import _gen_common as gc
import ecosystem_contracts as ec
import score_paideia as sp

HERE = Path(__file__).resolve().parent
OUTPUTS_ROOT = HERE / "outputs"
PAIDEIA_DIR = HERE / "paideia"
SCORES_DIR = PAIDEIA_DIR / "scores"
HISTORY_LOG = PAIDEIA_DIR / "history.tsv"
HISTORY_COLUMNS = [
    "timestamp_utc", "slug", "date", "paideia_version", "instructional_intent",
    *ec.PAIDEIA_AXES, "signature",
]


def discover_articles() -> list[tuple[Path, str]]:
    """Return list of (article_dir, date_string) for every slug dir with article.md."""
    results = []
    if not OUTPUTS_ROOT.exists():
        return results
    for date_dir in sorted(OUTPUTS_ROOT.iterdir()):
        if not date_dir.is_dir() or not re.match(r"\d{4}-\d{2}-\d{2}", date_dir.name):
            continue
        for slug_dir in sorted(date_dir.iterdir()):
            if not slug_dir.is_dir():
                continue
            if slug_dir.name.startswith(("smoke", "test-")):
                continue
            if (slug_dir / "article.md").exists():
                results.append((slug_dir, date_dir.name))
    return results


def score_and_log(slug_dir: Path, date: str, only_new: bool = False) -> dict:
    slug = slug_dir.name
    score_path = SCORES_DIR / f"{slug}.json"
    if only_new and score_path.exists():
        return {"slug": slug, "status": "skipped", "reason": "already scored"}

    text = (slug_dir / "article.md").read_text(encoding="utf-8")
    # Detect instructional_intent from frontmatter if present; default True
    intent = True
    meta_path = slug_dir / "meta.json"
    if meta_path.exists():
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            if "instructional_intent" in meta:
                intent = bool(meta["instructional_intent"])
        except json.JSONDecodeError as e:
            print(f"WARN: skipping corrupt {meta_path}: {e}", file=sys.stderr)

    result = sp.score_content(text, instructional_intent=intent)
    result["_source"] = str(slug_dir / "article.md")
    result["_scored_at"] = gc.now_utc_iso()

    SCORES_DIR.mkdir(parents=True, exist_ok=True)
    score_path.write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8")

    return {
        "slug": slug,
        "date": date,
        "status": "scored",
        "signature": result["signature"],
        "vector": result["vector"],
        "paideia_version": result.get("prompt_version", "?"),
        "instructional_intent": intent,
    }


def _archive_legacy_history() -> None:
    """If history.tsv exists with a v0.1 (9-axis) header, archive it to
    history.v0.1.tsv so v0.2 rows start a clean 10-column file. Lazy and
    non-destructive: the v0.1 data is preserved (renamed, not rewritten),
    per docs/paideia-9-v0.2-draft.md "v0.1 scores kept as-is". No-op if the
    file is absent or already has the v0.2 header.
    """
    if not HISTORY_LOG.exists():
        return
    expected = "\t".join(HISTORY_COLUMNS) + "\n"
    with HISTORY_LOG.open("r", encoding="utf-8") as fh:
        first = fh.readline()
    if first == expected:
        return
    archive = HISTORY_LOG.with_suffix(".v0.1.tsv")
    HISTORY_LOG.rename(archive)
    print(f"archived v0.1 history -> {archive} (header mismatch; starting "
          f"fresh v0.2 {HISTORY_LOG.name})", file=sys.stderr)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--since", default=None,
                   help="only score articles dated >= this (YYYY-MM-DD)")
    p.add_argument("--only-new", action="store_true",
                   help="skip articles that already have a score JSON")
    p.add_argument("--dry-run", action="store_true",
                   help="print plan, don't write")
    args = p.parse_args(argv)

    articles = discover_articles()
    if args.since:
        articles = [(d, date) for d, date in articles if date >= args.since]

    print(f"discovered {len(articles)} article(s)", file=sys.stderr)

    results = []
    for slug_dir, date in articles:
        if args.dry_run:
            print(f"  [dry-run] would score {slug_dir.name}", file=sys.stderr)
            continue
        try:
            r = score_and_log(slug_dir, date, only_new=args.only_new)
            results.append(r)
        except Exception as e:
            print(f"  FAILED {slug_dir.name}: {type(e).__name__}: {e}",
                  file=sys.stderr)

    if args.dry_run or not results:
        return 0

    scored = [r for r in results if r["status"] == "scored"]

    # Append historical log (archive v0.1 history first if header mismatches)
    _archive_legacy_history()
    log = gc.TsvLog(HISTORY_LOG, HISTORY_COLUMNS)
    rows = [{
        "timestamp_utc": gc.now_utc_iso(),
        "slug": r["slug"],
        "date": r["date"],
        "paideia_version": r["paideia_version"],
        "instructional_intent": str(r["instructional_intent"]).lower(),
        **r["vector"],
        "signature": r["signature"],
    } for r in scored]
    log.append(rows)

    print(f"\nScored {len(scored)} article(s); "
          f"skipped {len(results) - len(scored)}", file=sys.stderr)
    print(f"Appended {len(rows)} row(s) to {HISTORY_LOG}", file=sys.stderr)

    # Brief summary
    print(f"\n{'slug':60s}  signature", file=sys.stderr)
    print("-" * 80, file=sys.stderr)
    for r in scored:
        print(f"{r['slug'][:60]:60s}  {r['signature']}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
