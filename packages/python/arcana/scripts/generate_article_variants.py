"""Post-process an ARCANA article.md into agent-optimized + metadata variants.

For a given output directory containing article.md + synthesis.json +
perspective_*.json, produces:
  - article.llm.md      — token-optimized companion per docs/llm-content-templates.md
  - meta.json           — flat metadata object
  - schema.jsonld       — schema.org TechArticle
  - summary.txt         — 3-sentence TL;DR (extracted from synthesis)
  - reflection.md       — intrapersonal prompts (PAIDEIA axis C)

CPU-only. No LLM calls (extracts from already-generated content).

Usage:
    python generate_article_variants.py --dir outputs/2026-04-24/<slug>
    python generate_article_variants.py --all   # process every dir under outputs/
    python generate_article_variants.py --dir ... --dry-run
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

HERE = Path(__file__).resolve().parent
OUTPUTS_ROOT = HERE / "outputs"

DECORATIVE_ADJECTIVES = {
    "powerful", "robust", "cutting-edge", "seamless", "innovative",
    "groundbreaking", "revolutionary", "world-class", "state-of-the-art",
    "paradigm-shifting", "game-changing", "next-generation", "deeply",
}

SMART_QUOTES = str.maketrans({
    "‘": "'", "’": "'",  # single curly quotes
    "“": '"', "”": '"',  # double curly quotes
    "–": "-",  # en-dash
    "—": "--",  # em-dash
    "…": "...",  # ellipsis
})


def strip_decoratives(text: str) -> str:
    """Remove decorative adjectives that carry no propositional content."""
    for adj in DECORATIVE_ADJECTIVES:
        # Match as whole word, case-insensitive, with following space
        text = re.sub(rf"\b{adj}\s+", "", text, flags=re.IGNORECASE)
    return text


def ascii_punctuation(text: str) -> str:
    return text.translate(SMART_QUOTES)


def breadcrumb_headings(text: str, title: str) -> str:
    """Prefix each H2 heading with the article title for chunk-friendly breadcrumbs.

    Before:  ## Summary
    After:   ## <title> > Summary

    Idempotent: if a heading already starts with `<title> > `, leaves it alone.
    """
    title_prefix = f"{title} > "
    lines = text.splitlines()
    out = []
    for line in lines:
        m = re.match(r"^## (.+)$", line)
        if m:
            section = m.group(1).strip()
            if section.startswith(title_prefix):
                out.append(line)  # already prefixed
            else:
                out.append(f"## {title} > {section}")
        else:
            out.append(line)
    return "\n".join(out)


def strip_generation_marker(text: str) -> str:
    """Remove the 'Generated ... via overnight_v0.py' footer that adds no LLM value."""
    return re.sub(
        r"---\s*\n\s*\*Generated[^*]+\*\s*$",
        "", text, flags=re.MULTILINE)


def make_article_llm(article_md: str, title: str) -> str:
    """Produce the agent-optimized variant."""
    out = article_md
    out = ascii_punctuation(out)
    out = strip_decoratives(out)
    out = strip_generation_marker(out)
    out = breadcrumb_headings(out, title)
    # Collapse multiple blank lines
    out = re.sub(r"\n{3,}", "\n\n", out)
    return out.strip() + "\n"


def extract_summary(synthesis: dict, article_md: str, topic: str) -> str:
    """3-sentence TL;DR. Prefer synthesis.parsed.summary, else first paragraph."""
    parsed = synthesis.get("parsed") or {}
    if isinstance(parsed, dict):
        summary = parsed.get("summary")
        if isinstance(summary, str) and summary.strip():
            return summary.strip()
    # Fall back to first non-heading paragraph
    for para in article_md.split("\n\n"):
        stripped = para.strip()
        if stripped and not stripped.startswith("#") and not stripped.startswith("**"):
            return stripped[:500]
    return topic


def extract_topic(article_md: str, slug: str) -> str:
    m = re.search(r"\*\*Topic:\*\* (.+)", article_md)
    return m.group(1).strip() if m else slug.replace("-", " ")


def extract_title(article_md: str, topic: str) -> str:
    m = re.match(r"^# (.+)$", article_md, re.MULTILINE)
    return m.group(1).strip() if m else topic


def count_words(text: str) -> int:
    return len(re.findall(r"\S+", text))


def detect_perspectives(dir_path: Path) -> list[str]:
    return sorted(
        p.stem.replace("perspective_", "")
        for p in dir_path.glob("perspective_*.json")
    )


def make_meta_json(slug: str, title: str, topic: str, summary: str,
                   perspectives: list[str], word_count: int,
                   reading_time_min: int, synthesis: dict,
                   paideia_vector: str | None) -> dict:
    meta = {
        "title": title,
        "slug": slug,
        "topic": topic,
        "date": dt.datetime.now(dt.UTC).date().isoformat(),
        "authors": ["arcana-overnight"],
        "perspectives": perspectives,
        "synthesist": "default",
        "summary": summary,
        "word_count": word_count,
        "reading_time_min": reading_time_min,
        "evidence_tier": "synthesized",
        "license": "CC-BY-4.0",
        "canonical_url": f"https://arcana.hummbl.io/{slug}/",
    }
    if paideia_vector:
        meta["paideia_vector"] = paideia_vector
        meta["paideia_version"] = "paideia-score-v0.1"
    # Pull confidence if the synthesist emitted it
    parsed = synthesis.get("parsed") or {}
    if isinstance(parsed, dict):
        if parsed.get("confidence_score") is not None:
            meta["synthesis_confidence"] = parsed["confidence_score"]
        if parsed.get("tags"):
            meta["tags"] = parsed["tags"]
    return meta


def make_schema_jsonld(meta: dict) -> dict:
    return {
        "@context": "https://schema.org",
        "@type": "TechArticle",
        "headline": meta["title"],
        "description": meta["summary"],
        "author": {"@type": "Organization", "name": "HUMMBL / arcana"},
        "datePublished": meta["date"],
        "license": "https://creativecommons.org/licenses/by/4.0/",
        "keywords": meta.get("tags", []),
        "url": meta["canonical_url"],
        "wordCount": meta["word_count"],
    }


def make_reflection_md(topic: str, synthesis: dict) -> str:
    """Intrapersonal prompts (PAIDEIA axis C). Generic if synthesis lacks live_questions."""
    parsed = synthesis.get("parsed") or {}
    questions = []
    if isinstance(parsed, dict):
        live = parsed.get("live_questions")
        if isinstance(live, list):
            questions = [q for q in live if isinstance(q, str) and q.strip()]
    if len(questions) < 3:
        # Fall back to generic metacognitive prompts that work for any governance topic
        questions = (questions + [
            f"Which lens's framing of {topic} feels most alien to you — and why?",
            "What is one claim in this article you would bet against? What evidence would change your mind?",
            "If you had to hand this topic to a successor in 6 months, what context would you include that this article leaves out?",
        ])[:5]
    lines = [f"# Reflection prompts — {topic}", "",
             "Use these before reading, after reading, or both. Write 2-3 sentences each.",
             ""]
    for i, q in enumerate(questions[:5], 1):
        lines.append(f"{i}. {q}")
        lines.append("")
    return "\n".join(lines)


def process_dir(out_dir: Path, dry_run: bool = False) -> dict:
    """Process a single output dir. Returns summary dict."""
    article_path = out_dir / "article.md"
    synth_path = out_dir / "synthesis.json"
    if not article_path.exists():
        return {"slug": out_dir.name, "status": "skipped", "reason": "no article.md"}
    if not synth_path.exists():
        return {"slug": out_dir.name, "status": "skipped", "reason": "no synthesis.json"}

    article_md = article_path.read_text(encoding="utf-8")
    synthesis = json.loads(synth_path.read_text(encoding="utf-8"))
    slug = out_dir.name
    topic = extract_topic(article_md, slug)
    title = extract_title(article_md, topic)
    summary = extract_summary(synthesis, article_md, topic)
    perspectives = detect_perspectives(out_dir)
    word_count = count_words(article_md)
    reading_time_min = max(1, round(word_count / 225))  # avg adult reading

    # Check for paideia score sidecar
    paideia_vector = None
    paideia_score_path = HERE.parent / "scripts" / "paideia" / "scores" / f"{slug}.json"
    if paideia_score_path.exists():
        try:
            pscore = json.loads(paideia_score_path.read_text(encoding="utf-8"))
            paideia_vector = pscore.get("signature")
        except json.JSONDecodeError as e:
            print(f"WARN: skipping corrupt {paideia_score_path}: {e}", file=sys.stderr)

    article_llm = make_article_llm(article_md, title)
    meta = make_meta_json(slug, title, topic, summary, perspectives,
                          word_count, reading_time_min, synthesis, paideia_vector)
    schema = make_schema_jsonld(meta)
    reflection = make_reflection_md(topic, synthesis)

    outputs = {
        "article.llm.md": article_llm,
        "meta.json": json.dumps(meta, indent=2, ensure_ascii=False) + "\n",
        "schema.jsonld": json.dumps(schema, indent=2, ensure_ascii=False) + "\n",
        "summary.txt": summary + "\n",
        "reflection.md": reflection,
    }

    if dry_run:
        print(f"[dry-run] {slug}: would write {list(outputs.keys())}", file=sys.stderr)
        return {"slug": slug, "status": "dry_run", "files": list(outputs.keys())}

    for name, content in outputs.items():
        (out_dir / name).write_text(content, encoding="utf-8")

    return {"slug": slug, "status": "ok", "files": list(outputs.keys()),
            "word_count": word_count, "paideia_vector": paideia_vector}


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    src = p.add_mutually_exclusive_group(required=True)
    src.add_argument("--dir", help="single output dir to process")
    src.add_argument("--all", action="store_true",
                     help="process every outputs/YYYY-MM-DD/<slug>/ dir with article.md")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args(argv)

    if args.dir:
        out_dir = Path(args.dir).resolve()
        if not out_dir.is_dir():
            print(f"error: {out_dir} is not a directory", file=sys.stderr)
            return 1
        result = process_dir(out_dir, dry_run=args.dry_run)
        print(json.dumps(result, indent=2))
        return 0 if result["status"] in ("ok", "dry_run") else 2

    # --all
    results = []
    for date_dir in sorted(OUTPUTS_ROOT.iterdir()):
        if not date_dir.is_dir() or not re.match(r"\d{4}-\d{2}-\d{2}", date_dir.name):
            continue
        for slug_dir in sorted(date_dir.iterdir()):
            if not slug_dir.is_dir():
                continue
            # Skip smoke/test dirs
            if slug_dir.name.startswith(("smoke", "test-")):
                continue
            results.append(process_dir(slug_dir, dry_run=args.dry_run))
    ok = sum(1 for r in results if r["status"] == "ok")
    skipped = sum(1 for r in results if r["status"] == "skipped")
    print(f"\nProcessed {len(results)}: {ok} ok, {skipped} skipped", file=sys.stderr)
    for r in results:
        if r["status"] == "ok":
            print(f"  {r['slug']:60s}  {r.get('word_count', '?')} words  "
                  f"paideia={r.get('paideia_vector', '-')}")
        elif r["status"] == "skipped":
            print(f"  {r['slug']:60s}  SKIPPED: {r.get('reason', '?')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
