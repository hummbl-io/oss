"""Tests for score_all.py — discovery + scoring + history log.

Pure CPU; no Ollama. Builds a synthetic outputs tree under tmp_path and
exercises the scoring pipeline end-to-end.
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import score_all

SAMPLE_ARTICLE = """# A Test Article

**Topic:** Testing

## Summary
A short summary with at least one image ![alt](img.png) and some code:

```python
def f():
    return 1
```

## Perspectives

### yarvin (ARCANA / NRx-formalism)

Some prose content with a reflection prompt: why is this the case?

**Key claims:**
- First claim
- Second claim

**Blind spots:** None.
"""


def _build_outputs_tree(root: Path, slug: str = "test-topic",
                        date: str = "2026-04-24") -> Path:
    """Build a minimal outputs/<date>/<slug>/ directory with article.md + meta."""
    slug_dir = root / date / slug
    slug_dir.mkdir(parents=True, exist_ok=True)
    (slug_dir / "article.md").write_text(SAMPLE_ARTICLE, encoding="utf-8")
    return slug_dir


def test_discover_articles_finds_valid(tmp_path, monkeypatch):
    outputs = tmp_path / "outputs"
    _build_outputs_tree(outputs, "topic-a")
    _build_outputs_tree(outputs, "topic-b", date="2026-04-23")
    monkeypatch.setattr(score_all, "OUTPUTS_ROOT", outputs)
    results = score_all.discover_articles()
    slugs = sorted(r[0].name for r in results)
    assert slugs == ["topic-a", "topic-b"]


def test_discover_skips_smoke_and_test_prefixes(tmp_path, monkeypatch):
    outputs = tmp_path / "outputs"
    _build_outputs_tree(outputs, "real-topic")
    _build_outputs_tree(outputs, "smoke-test-topic")
    _build_outputs_tree(outputs, "test-scratch")
    monkeypatch.setattr(score_all, "OUTPUTS_ROOT", outputs)
    results = score_all.discover_articles()
    slugs = {r[0].name for r in results}
    assert slugs == {"real-topic"}


def test_discover_skips_non_date_dirs(tmp_path, monkeypatch):
    outputs = tmp_path / "outputs"
    _build_outputs_tree(outputs, "topic", date="2026-04-24")
    # non-date parent
    bogus = outputs / "not-a-date" / "slug"
    bogus.mkdir(parents=True)
    (bogus / "article.md").write_text("x", encoding="utf-8")
    monkeypatch.setattr(score_all, "OUTPUTS_ROOT", outputs)
    results = score_all.discover_articles()
    assert len(results) == 1
    assert results[0][0].name == "topic"


def test_discover_requires_article_md(tmp_path, monkeypatch):
    outputs = tmp_path / "outputs"
    empty = outputs / "2026-04-24" / "empty-slug"
    empty.mkdir(parents=True)
    # no article.md
    monkeypatch.setattr(score_all, "OUTPUTS_ROOT", outputs)
    results = score_all.discover_articles()
    assert results == []


def test_score_and_log_produces_sidecar(tmp_path, monkeypatch):
    outputs = tmp_path / "outputs"
    scores = tmp_path / "scores"
    slug_dir = _build_outputs_tree(outputs, "topic-x")
    monkeypatch.setattr(score_all, "SCORES_DIR", scores)
    result = score_all.score_and_log(slug_dir, "2026-04-24")
    assert result["status"] == "scored"
    assert result["slug"] == "topic-x"
    assert "signature" in result
    assert (scores / "topic-x.json").exists()
    data = json.loads((scores / "topic-x.json").read_text(encoding="utf-8"))
    assert "vector" in data
    assert "signature" in data


def test_score_and_log_respects_only_new(tmp_path, monkeypatch):
    outputs = tmp_path / "outputs"
    scores = tmp_path / "scores"
    scores.mkdir()
    slug_dir = _build_outputs_tree(outputs, "already-scored")
    # Pre-create the score file
    (scores / "already-scored.json").write_text("{}", encoding="utf-8")
    monkeypatch.setattr(score_all, "SCORES_DIR", scores)
    result = score_all.score_and_log(slug_dir, "2026-04-24", only_new=True)
    assert result["status"] == "skipped"


def test_score_and_log_honors_meta_intent(tmp_path, monkeypatch):
    outputs = tmp_path / "outputs"
    scores = tmp_path / "scores"
    slug_dir = _build_outputs_tree(outputs, "non-instructional")
    # Write meta.json with instructional_intent: false
    (slug_dir / "meta.json").write_text(
        json.dumps({"instructional_intent": False}), encoding="utf-8")
    monkeypatch.setattr(score_all, "SCORES_DIR", scores)
    score_all.score_and_log(slug_dir, "2026-04-24")
    data = json.loads((scores / "non-instructional.json").read_text(encoding="utf-8"))
    assert data["instructional_intent"] is False
    assert data.get("content_type_warning")


def test_scores_sidecar_pattern_is_ignored():
    root = Path(__file__).resolve().parents[1]
    gitignore = root / ".gitignore"
    lines = gitignore.read_text(encoding="utf-8").splitlines()
    assert "scripts/paideia/scores/*.json" in lines


def _simple_monkeypatch():
    """Drop-in monkeypatch for standalone running."""
    class _M:
        _orig: dict = {}
        def setattr(self, obj, name, value):
            self._orig.setdefault(id(obj), {})[name] = getattr(obj, name)
            setattr(obj, name, value)
        def undo(self):
            for target_id, attrs in self._orig.items():
                # Can't resolve target_id back to obj cleanly; rely on caller
                pass
    return _M()


def _run_standalone():
    import inspect
    fns = [(n, f) for n, f in globals().items()
           if n.startswith("test_") and callable(f)]
    fails = 0
    for name, fn in fns:
        try:
            sig = inspect.signature(fn)
            kwargs = {}
            cleanup_targets = []
            if "tmp_path" in sig.parameters or "monkeypatch" in sig.parameters:
                td = tempfile.mkdtemp()
                kwargs["tmp_path"] = Path(td)
            if "monkeypatch" in sig.parameters:
                mp = _simple_monkeypatch()
                cleanup_targets.append(mp)
                kwargs["monkeypatch"] = mp
            fn(**kwargs)
            # Undo any attrs we set on score_all so subsequent tests are clean
            import importlib as _imp
            _imp.reload(score_all)
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
