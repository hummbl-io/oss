"""Enforce that every docs/*.md (except README.md itself) has a row in the
docs/README.md nav index. Prevents silent drift where a new doc lands but is
never indexed. Pure stdlib, no network.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
README = DOCS / "README.md"


def _indexed_docs(readme_text: str) -> set[str]:
    """Filenames that appear as a markdown link [x](x) in the nav table."""
    return {m.group(1) for m in re.finditer(r"\]\(([^)]+\.md)\)", readme_text)}


def test_every_doc_is_indexed_in_readme():
    if not README.exists():
        raise AssertionError("docs/README.md nav index is missing")
    readme_text = README.read_text(encoding="utf-8")
    indexed = _indexed_docs(readme_text)
    missing: list[str] = []
    for p in sorted(DOCS.glob("*.md")):
        if p.name == "README.md":
            continue
        if p.name not in indexed:
            missing.append(p.name)
    assert not missing, (
        f"docs not indexed in docs/README.md nav table: {missing}. "
        f"Add a row for each in the | Doc | What it is | table."
    )
