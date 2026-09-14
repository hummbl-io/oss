"""Tests for generate_article_variants.py — pure-CPU helpers.

Covers strip_decoratives, ascii_punctuation, breadcrumb_headings,
extract_summary/topic/title, count_words, make_meta_json,
make_schema_jsonld, make_reflection_md, and the full process_dir
pipeline against a synthetic outputs tree under tmp_path.
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import generate_article_variants as gav

# ---- text transforms --------------------------------------------------- #

def test_strip_decoratives_removes_known():
    text = "This is a powerful and robust solution for cutting-edge problems."
    out = gav.strip_decoratives(text)
    assert "powerful" not in out.lower()
    assert "robust" not in out.lower()


def test_strip_decoratives_preserves_other_words():
    text = "A simple direct sentence."
    assert gav.strip_decoratives(text) == text


def test_ascii_punctuation_smart_quotes():
    text = "He said “hello” and ‘world’."
    out = gav.ascii_punctuation(text)
    assert "“" not in out and "”" not in out
    assert '"hello"' in out
    assert "'world'" in out


def test_ascii_punctuation_em_dash():
    assert gav.ascii_punctuation("a—b") == "a--b"


def test_ascii_punctuation_ellipsis():
    assert gav.ascii_punctuation("wait…") == "wait..."


def test_breadcrumb_headings_prepends_title():
    md = "## Summary\nSome text\n## Synthesis\nMore text"
    out = gav.breadcrumb_headings(md, "My Article")
    assert "## My Article > Summary" in out
    assert "## My Article > Synthesis" in out


def test_breadcrumb_headings_skips_already_prefixed():
    md = "## My Article > Summary\nText"
    out = gav.breadcrumb_headings(md, "My Article")
    # Should not double-prefix
    assert "## My Article > My Article" not in out


def test_breadcrumb_headings_leaves_h1_alone():
    md = "# Title\n## Summary"
    out = gav.breadcrumb_headings(md, "Title")
    assert "# Title" in out
    assert "## Title > Summary" in out


def test_strip_generation_marker_removes_footer():
    md = "Some content\n\n---\n\n*Generated 2026-04-24T00:00:00Z via something*"
    out = gav.strip_generation_marker(md)
    assert "*Generated" not in out


def test_strip_generation_marker_no_change_when_absent():
    md = "Some content with no marker."
    assert gav.strip_generation_marker(md) == md


def test_make_article_llm_combines_transforms():
    md = ("# Title\n\n**Topic:** X\n\n"
          "## Summary\n\nA powerful and robust solution.\n\n"
          "He said “yes”.")
    out = gav.make_article_llm(md, "Title")
    assert "## Title > Summary" in out
    assert "powerful" not in out.lower()
    assert '"yes"' in out


# ---- extractors -------------------------------------------------------- #

def test_extract_topic_from_marker():
    md = "# Title\n\n**Topic:** Rate limiters\n\nText"
    assert gav.extract_topic(md, "fallback") == "Rate limiters"


def test_extract_topic_falls_back_to_slug():
    md = "# No topic marker\n\nText"
    assert gav.extract_topic(md, "rate-limiters-on-edge") == \
        "rate limiters on edge"


def test_extract_title_from_h1():
    md = "# My Title\n\nText"
    assert gav.extract_title(md, "topic") == "My Title"


def test_extract_title_falls_back_to_topic():
    md = "no h1\n\ntext"
    assert gav.extract_title(md, "the topic") == "the topic"


def test_extract_summary_from_synthesis():
    synthesis = {"parsed": {"summary": "  A clean summary.  "}}
    s = gav.extract_summary(synthesis, "...", "...")
    assert s == "A clean summary."


def test_extract_summary_falls_back_to_first_paragraph():
    synthesis = {"parsed": {}}
    md = "# Title\n\n**Topic:** X\n\nFirst real paragraph here.\n\nNext."
    s = gav.extract_summary(synthesis, md, "X")
    assert "First real paragraph" in s


def test_extract_summary_unparseable_synthesis():
    synthesis = {"parsed": "not a dict"}
    s = gav.extract_summary(synthesis, "## H\nContent.", "topic")
    assert s == "topic" or "Content" in s


def test_count_words():
    assert gav.count_words("one two three") == 3
    assert gav.count_words("") == 0
    assert gav.count_words("hyphen-word counts as one") == 4


# ---- meta + schema ----------------------------------------------------- #

def test_make_meta_json_has_required_fields():
    meta = gav.make_meta_json(
        slug="my-slug", title="Title", topic="Topic",
        summary="Summary.", perspectives=["yarvin"],
        word_count=100, reading_time_min=1,
        synthesis={"parsed": {"confidence_score": 0.7, "tags": ["a", "b"]}},
        paideia_vector="1-2-3-2-0-2-1-1-1")
    assert meta["slug"] == "my-slug"
    assert meta["title"] == "Title"
    assert meta["paideia_vector"] == "1-2-3-2-0-2-1-1-1"
    assert meta["paideia_version"] == "paideia-score-v0.1"
    assert meta["synthesis_confidence"] == 0.7
    assert meta["tags"] == ["a", "b"]
    assert meta["license"].startswith("CC")


def test_make_meta_json_no_paideia_when_none():
    meta = gav.make_meta_json(
        slug="s", title="T", topic="T", summary="S",
        perspectives=[], word_count=0, reading_time_min=0,
        synthesis={"parsed": {}}, paideia_vector=None)
    assert "paideia_vector" not in meta
    assert "paideia_version" not in meta


def test_make_schema_jsonld_minimal_structure():
    meta = {
        "title": "T", "summary": "S", "date": "2026-04-24",
        "tags": [], "canonical_url": "https://example/", "word_count": 0,
    }
    schema = gav.make_schema_jsonld(meta)
    assert schema["@context"] == "https://schema.org"
    assert schema["@type"] == "TechArticle"
    assert schema["headline"] == "T"
    assert schema["url"] == "https://example/"


# ---- reflection -------------------------------------------------------- #

def test_make_reflection_uses_live_questions_when_present():
    synth = {"parsed": {"live_questions": ["Q1?", "Q2?", "Q3?"]}}
    md = gav.make_reflection_md("topic", synth)
    assert "Q1?" in md
    assert "Q2?" in md
    assert "Q3?" in md


def test_make_reflection_falls_back_when_no_questions():
    synth = {"parsed": {}}
    md = gav.make_reflection_md("topic", synth)
    # Generic prompts include the topic
    assert "topic" in md.lower()
    # Should have at least 3 numbered prompts
    assert "1." in md and "2." in md and "3." in md


def test_make_reflection_caps_at_5():
    synth = {"parsed": {"live_questions": [f"Q{i}?" for i in range(10)]}}
    md = gav.make_reflection_md("t", synth)
    # Should not show Q5 or later (0-indexed first 5: Q0..Q4)
    assert "Q5?" not in md
    assert "Q9?" not in md


# ---- process_dir ------------------------------------------------------- #

SAMPLE_ARTICLE = """# A Test Title

**Topic:** A Test Topic

## Summary

This is the summary paragraph.

## Synthesis

A synthesis essay.
"""

SAMPLE_SYNTHESIS = json.dumps({
    "parsed": {
        "title": "A Test Title",
        "summary": "Test summary, three sentences for real this time. " * 3,
        "convergences": ["c1", "c2"],
        "divergences": ["d1"],
        "synthesis": "An essay.",
        "live_questions": ["q1?"],
        "tags": ["test"],
        "confidence_score": 0.5,
    }
})


def _build_outputs_tree(root: Path, slug: str = "test-topic") -> Path:
    slug_dir = root / "2026-04-24" / slug
    slug_dir.mkdir(parents=True, exist_ok=True)
    (slug_dir / "article.md").write_text(SAMPLE_ARTICLE, encoding="utf-8")
    (slug_dir / "synthesis.json").write_text(SAMPLE_SYNTHESIS, encoding="utf-8")
    (slug_dir / "perspective_yarvin.json").write_text("{}", encoding="utf-8")
    (slug_dir / "perspective_foucault.json").write_text("{}", encoding="utf-8")
    return slug_dir


def test_process_dir_writes_all_artifacts(tmp_path):
    slug_dir = _build_outputs_tree(tmp_path)
    result = gav.process_dir(slug_dir, dry_run=False)
    assert result["status"] == "ok"
    assert (slug_dir / "article.llm.md").exists()
    assert (slug_dir / "meta.json").exists()
    assert (slug_dir / "schema.jsonld").exists()
    assert (slug_dir / "summary.txt").exists()
    assert (slug_dir / "reflection.md").exists()


def test_process_dir_meta_has_perspectives(tmp_path):
    slug_dir = _build_outputs_tree(tmp_path)
    gav.process_dir(slug_dir, dry_run=False)
    meta = json.loads((slug_dir / "meta.json").read_text(encoding="utf-8"))
    assert sorted(meta["perspectives"]) == ["foucault", "yarvin"]


def test_process_dir_dry_run_writes_nothing(tmp_path):
    slug_dir = _build_outputs_tree(tmp_path)
    result = gav.process_dir(slug_dir, dry_run=True)
    assert result["status"] == "dry_run"
    assert not (slug_dir / "article.llm.md").exists()


def test_process_dir_skips_when_no_article(tmp_path):
    slug_dir = tmp_path / "2026-04-24" / "no-article"
    slug_dir.mkdir(parents=True)
    (slug_dir / "synthesis.json").write_text("{}", encoding="utf-8")
    result = gav.process_dir(slug_dir, dry_run=False)
    assert result["status"] == "skipped"


def test_process_dir_skips_when_no_synthesis(tmp_path):
    slug_dir = tmp_path / "2026-04-24" / "no-synthesis"
    slug_dir.mkdir(parents=True)
    (slug_dir / "article.md").write_text("# T", encoding="utf-8")
    result = gav.process_dir(slug_dir, dry_run=False)
    assert result["status"] == "skipped"


def _run_standalone():
    import inspect
    fns = [(n, f) for n, f in globals().items()
           if n.startswith("test_") and callable(f)]
    fails = 0
    for name, fn in fns:
        try:
            sig = inspect.signature(fn)
            if "tmp_path" in sig.parameters:
                with tempfile.TemporaryDirectory() as td:
                    fn(Path(td))
            else:
                fn()
            print(f"OK    {name}")
        except AssertionError as e:
            fails += 1
            print(f"FAIL  {name}: {e}")
        except Exception as e:
            fails += 1
            print(f"ERROR {name}: {type(e).__name__}: {e}")
    print(f"\n{len(fns) - fails}/{len(fns)} passed")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    raise SystemExit(_run_standalone())
