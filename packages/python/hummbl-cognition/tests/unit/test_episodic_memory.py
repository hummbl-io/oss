"""Tests for Episodic Memory Grouping in Consolidator."""

from __future__ import annotations

from hummbl_cognition.consolidator import MAX_GROUP_SIZE, _group_by_links
from hummbl_cognition.models import LedgerEntry, LedgerEntryType, LedgerScope


def _make_entry(links: tuple[str, ...] = ()) -> LedgerEntry:
    """Create a minimal LedgerEntry with auto-generated ID."""
    return LedgerEntry.create(
        agent="test-agent",
        vendor="local",
        model="test-model",
        entry_type=LedgerEntryType.DISCOVERY,
        scope=LedgerScope.PROJECT,
        content="test content",
        links=links,
    )


def test_group_by_links_simple_chain():
    """A -> B -> C forms one episode."""
    a = _make_entry()
    b = _make_entry(links=(a.id,))
    c = _make_entry(links=(b.id,))
    # Back-link a to b so the chain is connected
    a = LedgerEntry(**{**a.__dict__, "links": (b.id,)})

    groups = _group_by_links([a, b, c])

    assert len(groups) == 1
    assert {e.id for e in groups[0]} == {a.id, b.id, c.id}


def test_group_by_links_multiple_episodes():
    """Two disjoint pairs + one isolated entry = 2 episodes."""
    a = _make_entry()
    b = _make_entry(links=(a.id,))
    a = LedgerEntry(**{**a.__dict__, "links": (b.id,)})

    c = _make_entry()
    d = _make_entry(links=(c.id,))
    c = LedgerEntry(**{**c.__dict__, "links": (d.id,)})

    isolated = _make_entry()

    groups = _group_by_links([a, b, c, d, isolated])

    assert len(groups) == 2
    ids = [{e.id for e in g} for g in groups]
    assert {a.id, b.id} in ids
    assert {c.id, d.id} in ids


def test_group_by_links_max_size_limit():
    """A chain longer than MAX_GROUP_SIZE is truncated."""
    entries = []
    for i in range(MAX_GROUP_SIZE + 5):
        links = (entries[-1].id,) if entries else ()
        entries.append(_make_entry(links=links))
    # Back-link first to second so BFS starts connected
    entries[0] = LedgerEntry(**{**entries[0].__dict__, "links": (entries[1].id,)})

    groups = _group_by_links(entries)

    assert len(groups) == 1
    assert len(groups[0]) == MAX_GROUP_SIZE


def test_group_by_links_broken_ref():
    """Links to IDs not in the input set are ignored gracefully."""
    a = _make_entry(links=("clp-doesnotexist",))
    b = _make_entry(links=(a.id,))

    groups = _group_by_links([a, b])

    assert len(groups) == 1
    assert {e.id for e in groups[0]} == {a.id, b.id}


def test_group_by_links_no_links():
    """Entries with no links form no episodes."""
    entries = [_make_entry() for _ in range(5)]

    groups = _group_by_links(entries)

    assert len(groups) == 0


def test_group_by_links_empty_input():
    """Empty input returns empty output."""
    assert _group_by_links([]) == []
