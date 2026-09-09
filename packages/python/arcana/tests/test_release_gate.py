"""Tests for the read-only ARCANA RELEASE gate."""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from RELEASE import gate  # noqa: E402


def _article(tmp: Path, text: str) -> Path:
    path = tmp / "article.md"
    path.write_text(text, encoding="utf-8")
    return path


def test_release_gate_passes_clean_internal_article():
    with tempfile.TemporaryDirectory() as d:
        path = _article(
            Path(d),
            "# Test Article\n\nThis production case study includes an example "
            "and asks the reader to reflect on what would happen next.",
        )
        bundle = gate.build_release_gate_bundle(path)
    assert bundle["schema_version"] == "release-gate-v0.1"
    assert bundle["release"]["decision"] == "pass"
    assert bundle["release"]["read_only"] is True
    assert bundle["receipts"]["lingua"]["status"] == "pass"
    assert bundle["receipts"]["nomos"]["status"] == "pass"


def test_release_gate_holds_for_editorial_markers():
    with tempfile.TemporaryDirectory() as d:
        path = _article(Path(d), "# Draft\n\nTODO: citation needed before release.")
        bundle = gate.build_release_gate_bundle(path)
    assert bundle["release"]["decision"] == "hold"
    assert "lingua:editorial-placeholder" in bundle["release"]["reasons"]
    assert "lingua:citation-needed-marker" in bundle["release"]["reasons"]


def test_release_gate_holds_for_external_target_without_nomos_mapping():
    with tempfile.TemporaryDirectory() as d:
        path = _article(Path(d), "# External\n\nA clean internal article.")
        bundle = gate.build_release_gate_bundle(path, external_target=True)
    assert bundle["release"]["decision"] == "hold"
    assert "nomos:external-target-requires-standards-mapping" in bundle["release"]["reasons"]


def test_release_gate_blocks_empty_artifact():
    with tempfile.TemporaryDirectory() as d:
        path = _article(Path(d), "")
        bundle = gate.build_release_gate_bundle(path)
    assert bundle["release"]["decision"] == "blocked"
    assert bundle["release"]["reasons"] == ["empty-artifact"]


def test_release_gate_outputs_json_and_markdown():
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        path = _article(root, "# Test\n\nA short article with an example.")
        bundle = gate.build_release_gate_bundle(path)
        json_path, md_path = gate.write_outputs(bundle, root / "gate")
        loaded = json.loads(json_path.read_text(encoding="utf-8"))
        summary = md_path.read_text(encoding="utf-8")
    assert loaded["release"]["decision"] == bundle["release"]["decision"]
    assert "# ARCANA Release Gate Summary" in summary


def _run_standalone():
    fns = [(n, f) for n, f in globals().items()
           if n.startswith("test_") and callable(f)]
    fails = 0
    for name, fn in fns:
        try:
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
