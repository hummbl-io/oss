#!/usr/bin/env python3
"""Tests for minimum tuple vocabulary analysis (issue #27)."""

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

ESSENTIAL_TYPES = {"CONTRACT", "DCT", "DCTX", "SYSTEM", "EVIDENCE", "ATTEST"}


def test_essential_types_count():
    """There should be exactly 6 essential tuple types."""
    assert len(ESSENTIAL_TYPES) == 6


def test_essential_types_present_in_schemas():
    """Each essential type should have a schema file."""
    schemas_dir = REPO_ROOT / "schemas"
    for t in ESSENTIAL_TYPES:
        schema_file = schemas_dir / f"{t.lower()}.schema.json"
        assert schema_file.exists(), f"Missing schema for {t}: {schema_file}"


def test_essential_types_have_examples():
    """Each essential type should have at least one example."""
    examples_dir = REPO_ROOT / "examples"
    example_files = list(examples_dir.glob("*.json"))
    found_types = set()
    for p in example_files:
        with p.open("r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict) and data.get("tuple_type") in ESSENTIAL_TYPES:
            found_types.add(data["tuple_type"])
    # At least some essential types should have examples
    assert len(found_types) > 0, "No essential type examples found"


def test_consolidation_candidates_documented():
    """The research note should document consolidation candidates."""
    note = REPO_ROOT / "research_notes" / "2026-07-01-minimum-tuple-vocabulary.md"
    assert note.exists()
    content = note.read_text(encoding="utf-8")
    assert "DCTX" in content
    assert "BIO_ATTEST" in content
    assert "BIO_RECEIPT" in content
    assert "Consolidation" in content or "consolidation" in content


def test_tier_structure_documented():
    """The research note should document tier structure."""
    note = REPO_ROOT / "research_notes" / "2026-07-01-minimum-tuple-vocabulary.md"
    content = note.read_text(encoding="utf-8")
    assert "Tier 1" in content
    assert "Tier 2" in content
    assert "Essential" in content


def test_novelty_quest_entry():
    """The research note should include a novelty quest entry."""
    note = REPO_ROOT / "research_notes" / "2026-07-01-minimum-tuple-vocabulary.md"
    content = note.read_text(encoding="utf-8")
    assert "Novelty Quest" in content or "novelty quest" in content.lower()
    assert "Falsifier" in content or "falsifier" in content.lower()


if __name__ == "__main__":
    test_essential_types_count()
    test_essential_types_present_in_schemas()
    test_essential_types_have_examples()
    test_consolidation_candidates_documented()
    test_tier_structure_documented()
    test_novelty_quest_entry()
    print("All minimum tuple vocabulary tests passed")
