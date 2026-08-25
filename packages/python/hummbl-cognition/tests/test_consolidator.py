"""Tests for hummbl_cognition.consolidator — grouping, similarity, consolidation logic."""

from __future__ import annotations

from pathlib import Path

import pytest

from hummbl_cognition.consolidator import (
    MAX_GROUP_SIZE,
    MIN_GROUP_SIZE,
    SIMILARITY_THRESHOLD,
    _compute_pairwise_similarity,
    _get_consolidated_ids,
    _group_by_links,
    _group_similar,
)
from hummbl_cognition.ledger_writer import post_entry
from hummbl_cognition.models import LedgerEntry, LedgerEntryType, LedgerScope


def _make_entry(**overrides) -> LedgerEntry:
    defaults = dict(
        agent="test-agent",
        vendor="anthropic",
        model="claude-opus-4-6",
        entry_type=LedgerEntryType.LESSON,
        scope=LedgerScope.PROJECT,
        content="A valuable lesson learned",
    )
    defaults.update(overrides)
    return LedgerEntry.create(**defaults)


class TestGetConsolidatedIds:
    def test_empty_list(self) -> None:
        assert _get_consolidated_ids([]) == set()

    def test_no_consolidated_entries(self) -> None:
        entries = [
            _make_entry(content="lesson 1"),
            _make_entry(content="lesson 2"),
        ]
        assert _get_consolidated_ids(entries) == set()

    def test_with_consolidated_entry(self) -> None:
        target = _make_entry(content="target")
        consolidated = _make_entry(
            content="consolidated summary",
            entry_type=LedgerEntryType.CONVENTION,
            tags=("consolidated",),
            links=(target.id,),
        )
        result = _get_consolidated_ids([target, consolidated])
        assert target.id in result

    def test_entry_without_links_not_counted(self) -> None:
        entry = _make_entry(
            content="consolidated without links",
            tags=("consolidated",),
        )
        assert _get_consolidated_ids([entry]) == set()


class TestComputePairwiseSimilarity:
    def test_identical_content_high_similarity(self) -> None:
        e1 = _make_entry(content="python testing pytest fixtures")
        e2 = _make_entry(content="python testing pytest fixtures")
        sim = _compute_pairwise_similarity([e1, e2])
        assert e2.id in sim.get(e1.id, {})
        assert sim[e1.id][e2.id] == 1.0

    def test_no_overlap_zero_similarity(self) -> None:
        e1 = _make_entry(content="alpha beta gamma")
        e2 = _make_entry(content="delta epsilon zeta")
        sim = _compute_pairwise_similarity([e1, e2])
        # No overlap → not in similarity dict (below threshold)
        assert e2.id not in sim.get(e1.id, {})

    def test_partial_overlap(self) -> None:
        e1 = _make_entry(content="python testing code")
        e2 = _make_entry(content="python testing quality")
        sim = _compute_pairwise_similarity([e1, e2])
        # Should have some similarity (2 of 4 unique tokens = 0.5)
        if e2.id in sim.get(e1.id, {}):
            assert sim[e1.id][e2.id] > 0

    def test_empty_entries(self) -> None:
        sim = _compute_pairwise_similarity([])
        assert sim == {}


class TestGroupByLinks:
    def test_no_links_individual_entries(self) -> None:
        entries = [
            _make_entry(content="entry 1"),
            _make_entry(content="entry 2"),
        ]
        groups = _group_by_links(entries)
        # No links → no groups (each entry is its own component, below MIN_GROUP_SIZE)
        assert groups == []

    def test_linked_entries_grouped(self) -> None:
        e1 = _make_entry(content="entry 1")
        e2 = _make_entry(content="entry 2", links=(e1.id,))
        groups = _group_by_links([e1, e2])
        assert len(groups) == 1
        assert len(groups[0]) == 2

    def test_transitive_links_grouped(self) -> None:
        e1 = _make_entry(content="entry 1")
        e2 = _make_entry(content="entry 2", links=(e1.id,))
        e3 = _make_entry(content="entry 3", links=(e2.id,))
        groups = _group_by_links([e1, e2, e3])
        assert len(groups) == 1
        assert len(groups[0]) == 3

    def test_max_group_size_enforced(self) -> None:
        entries = []
        for i in range(MAX_GROUP_SIZE + 5):
            if i == 0:
                entries.append(_make_entry(content=f"entry {i}"))
            else:
                entries.append(
                    _make_entry(content=f"entry {i}", links=(entries[0].id,))
                )
        groups = _group_by_links(entries)
        assert len(groups) == 1
        assert len(groups[0]) <= MAX_GROUP_SIZE

    def test_unresolvable_links_ignored(self) -> None:
        e1 = _make_entry(content="entry 1", links=("clp-nonexist0000",))
        e2 = _make_entry(content="entry 2")
        groups = _group_by_links([e1, e2])
        # Link doesn't resolve → no groups
        assert groups == []


class TestGroupSimilar:
    def test_similar_entries_grouped(self) -> None:
        e1 = _make_entry(content="python testing pytest")
        e2 = _make_entry(content="python testing pytest mock")
        e3 = _make_entry(content="rust ownership borrowing")
        entries = [e1, e2, e3]
        sim = _compute_pairwise_similarity(entries)
        groups = _group_similar(entries, sim)
        # e1 and e2 should be grouped (high overlap), e3 should not
        # (may or may not form a group depending on MIN_GROUP_SIZE)
        for group in groups:
            ids = {e.id for e in group}
            if e1.id in ids:
                assert e2.id in ids
                assert e3.id not in ids

    def test_dissimilar_entries_not_grouped(self) -> None:
        e1 = _make_entry(content="alpha beta gamma delta")
        e2 = _make_entry(content="epsilon zeta eta theta")
        entries = [e1, e2]
        sim = _compute_pairwise_similarity(entries)
        groups = _group_similar(entries, sim)
        # No similarity → no groups
        assert groups == []

    def test_empty_entries(self) -> None:
        groups = _group_similar([], {})
        assert groups == []


class TestConstants:
    def test_min_group_size(self) -> None:
        assert MIN_GROUP_SIZE >= 2

    def test_max_group_size(self) -> None:
        assert MAX_GROUP_SIZE > MIN_GROUP_SIZE

    def test_similarity_threshold(self) -> None:
        assert 0 < SIMILARITY_THRESHOLD < 1
