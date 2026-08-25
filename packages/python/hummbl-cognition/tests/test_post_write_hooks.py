"""Tests for hummbl_cognition.post_write_hooks — automatic prior-art and
open-question query enqueuing on ledger post.

Verifies:
- Query builders produce well-formed research prompts
- Hooks fire for the right entry types (discovery → both, decision → prior_art only)
- Hooks do NOT fire for non-trigger types (lesson, convention, correction)
- Hooks append to the research queue idempotently
- Hooks never break the post (exceptions swallowed)
- Env var opt-outs work
- Results link back to the trigger entry via trigger_entry_id
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from hummbl_cognition.models import (
    LedgerEntry,
    LedgerEntryType,
    LedgerScope,
)
from hummbl_cognition.post_write_hooks import (
    PRIOR_ART_TRIGGER_TYPES,
    OPEN_QUESTION_TRIGGER_TYPES,
    build_open_question_query,
    build_prior_art_query,
    fire_post_write_hooks,
)


def _make_entry(**overrides) -> LedgerEntry:
    defaults = dict(
        agent="test-agent",
        vendor="anthropic",
        model="claude-opus-4-6",
        entry_type=LedgerEntryType.DISCOVERY,
        scope=LedgerScope.PROJECT,
        content="RAG with citation grounding reduces hallucination by 40% in open-domain QA tasks.",
        tags=("rag", "hallucination", "citation-grounding"),
    )
    defaults.update(overrides)
    return LedgerEntry.create(**defaults)


def _empty_queue(path: Path) -> Path:
    """Pre-create an empty queue file so load_research_queue returns [] not DEFAULT_QUEUE."""
    path.write_text("[]", encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# Query builders
# ---------------------------------------------------------------------------

class TestBuildPriorArtQuery:
    def test_produces_well_formed_query(self) -> None:
        entry = _make_entry()
        q = build_prior_art_query(entry)
        assert q["id"] == f"PA-{entry.id}"
        assert q["domain"] == "prior-art-discovery"
        assert q["tier"] == 1  # discovery = tier 1
        assert q["recurrence"] == "once"
        assert q["hook"] == "prior_art"
        assert q["trigger_entry_id"] == entry.id
        # Query text should contain the content and focus areas
        assert "RAG with citation grounding" in q["query"]
        assert "rag" in q["query"]
        assert "supports" in q["query"]
        assert "contradicts" in q["query"]

    def test_decision_gets_tier_2(self) -> None:
        entry = _make_entry(entry_type=LedgerEntryType.DECISION)
        q = build_prior_art_query(entry)
        assert q["tier"] == 2

    def test_content_truncated(self) -> None:
        entry = _make_entry(content="x " * 500)
        q = build_prior_art_query(entry)
        # Query should not contain the full 1000-char content
        assert len(q["query"]) < 2000

    def test_empty_tags_uses_general(self) -> None:
        entry = _make_entry(tags=())
        q = build_prior_art_query(entry)
        assert "general" in q["query"]


class TestBuildOpenQuestionQuery:
    def test_produces_well_formed_query(self) -> None:
        entry = _make_entry()
        q = build_open_question_query(entry)
        assert q["id"] == f"OQ-{entry.id}"
        assert q["domain"] == "open-question-discovery"
        assert q["tier"] == 1
        assert q["recurrence"] == "once"
        assert q["hook"] == "open_question"
        assert q["trigger_entry_id"] == entry.id
        assert "unsolved problems" in q["query"]
        assert "future work" in q["query"]
        assert "rag" in q["query"]


# ---------------------------------------------------------------------------
# Hook dispatch
# ---------------------------------------------------------------------------

class TestFirePostWriteHooks:
    def test_discovery_fires_both_hooks(self, tmp_path: Path) -> None:
        queue_path = _empty_queue(tmp_path / "research_queue.json")
        entry = _make_entry(entry_type=LedgerEntryType.DISCOVERY)
        fired = fire_post_write_hooks(entry, queue_path=queue_path)
        assert set(fired) == {"prior_art", "open_question"}
        # Queue should have 2 items
        queue = json.loads(queue_path.read_text(encoding="utf-8"))
        assert len(queue) == 2
        ids = {q["id"] for q in queue}
        assert f"PA-{entry.id}" in ids
        assert f"OQ-{entry.id}" in ids

    def test_decision_fires_prior_art_only(self, tmp_path: Path) -> None:
        queue_path = _empty_queue(tmp_path / "research_queue.json")
        entry = _make_entry(entry_type=LedgerEntryType.DECISION)
        fired = fire_post_write_hooks(entry, queue_path=queue_path)
        assert fired == ["prior_art"]
        queue = json.loads(queue_path.read_text(encoding="utf-8"))
        assert len(queue) == 1
        assert queue[0]["hook"] == "prior_art"

    def test_lesson_does_not_fire(self, tmp_path: Path) -> None:
        queue_path = tmp_path / "research_queue.json"
        entry = _make_entry(entry_type=LedgerEntryType.LESSON)
        fired = fire_post_write_hooks(entry, queue_path=queue_path)
        assert fired == []
        # Queue file should not be created
        assert not queue_path.exists()

    def test_convention_does_not_fire(self, tmp_path: Path) -> None:
        queue_path = tmp_path / "research_queue.json"
        entry = _make_entry(entry_type=LedgerEntryType.CONVENTION)
        fired = fire_post_write_hooks(entry, queue_path=queue_path)
        assert fired == []

    def test_correction_does_not_fire(self, tmp_path: Path) -> None:
        queue_path = tmp_path / "research_queue.json"
        entry = _make_entry(entry_type=LedgerEntryType.CORRECTION)
        fired = fire_post_write_hooks(entry, queue_path=queue_path)
        assert fired == []

    def test_idempotent_same_entry_not_duplicated(self, tmp_path: Path) -> None:
        queue_path = _empty_queue(tmp_path / "research_queue.json")
        entry = _make_entry()
        fire_post_write_hooks(entry, queue_path=queue_path)
        fire_post_write_hooks(entry, queue_path=queue_path)
        queue = json.loads(queue_path.read_text(encoding="utf-8"))
        # Still only 2 items, not 4
        assert len(queue) == 2

    def test_global_opt_out(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("CLP_POST_WRITE_HOOKS", "off")
        queue_path = tmp_path / "research_queue.json"
        entry = _make_entry()
        fired = fire_post_write_hooks(entry, queue_path=queue_path)
        assert fired == []
        assert not queue_path.exists()

    def test_prior_art_opt_out(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("CLP_HOOK_PRIOR_ART", "off")
        queue_path = _empty_queue(tmp_path / "research_queue.json")
        entry = _make_entry()
        fired = fire_post_write_hooks(entry, queue_path=queue_path)
        assert fired == ["open_question"]
        queue = json.loads(queue_path.read_text(encoding="utf-8"))
        assert len(queue) == 1
        assert queue[0]["hook"] == "open_question"

    def test_open_question_opt_out(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("CLP_HOOK_OPEN_QUESTION", "off")
        queue_path = tmp_path / "research_queue.json"
        entry = _make_entry()
        fired = fire_post_write_hooks(entry, queue_path=queue_path)
        assert fired == ["prior_art"]


# ---------------------------------------------------------------------------
# Integration: post_entry fires hooks
# ---------------------------------------------------------------------------

class TestPostEntryHookIntegration:
    def test_post_entry_fires_hooks_for_discovery(
        self, tmp_ledger_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # Redirect queue to temp dir so we don't pollute real state.
        # Must patch research_processor.DEFAULT_QUEUE_FILE (the source)
        # AND post_write_hooks.DEFAULT_QUEUE_FILE (the re-export).
        tmp_queue = _empty_queue(tmp_ledger_path.parent / "research_queue.json")
        monkeypatch.setattr(
            "hummbl_cognition.research_processor.DEFAULT_QUEUE_FILE",
            str(tmp_queue),
        )
        monkeypatch.setattr(
            "hummbl_cognition.post_write_hooks.DEFAULT_QUEUE_FILE",
            str(tmp_queue),
        )
        from hummbl_cognition.ledger_writer import post_entry
        entry = _make_entry(entry_type=LedgerEntryType.DISCOVERY)
        post_entry(entry, ledger_path=tmp_ledger_path)
        # Hook fires in a daemon thread — wait for queue to be written.
        # Retry loop handles Windows file locking during temp+rename write.
        import time
        queue = []
        for _ in range(30):
            try:
                queue = json.loads(tmp_queue.read_text(encoding="utf-8"))
                if len(queue) >= 2:
                    break
            except (PermissionError, json.JSONDecodeError, OSError):
                pass
            time.sleep(0.1)
        assert len(queue) == 2

    def test_post_entry_does_not_fire_for_lesson(
        self, tmp_ledger_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        tmp_queue = tmp_ledger_path.parent / "research_queue.json"
        monkeypatch.setattr(
            "hummbl_cognition.research_processor.DEFAULT_QUEUE_FILE",
            str(tmp_queue),
        )
        monkeypatch.setattr(
            "hummbl_cognition.post_write_hooks.DEFAULT_QUEUE_FILE",
            str(tmp_queue),
        )
        from hummbl_cognition.ledger_writer import post_entry
        entry = _make_entry(entry_type=LedgerEntryType.LESSON)
        post_entry(entry, ledger_path=tmp_ledger_path)
        # No queue file should be created (lesson doesn't trigger hooks)
        assert not tmp_queue.exists()

    def test_hook_failure_does_not_break_post(
        self, tmp_ledger_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # Sabotage the hook to raise — post must still succeed
        def boom(*a, **kw):
            raise RuntimeError("hook exploded")
        monkeypatch.setattr(
            "hummbl_cognition.post_write_hooks.fire_post_write_hooks", boom
        )
        from hummbl_cognition.ledger_writer import post_entry
        entry = _make_entry()
        result = post_entry(entry, ledger_path=tmp_ledger_path)
        # Entry was still posted
        assert result.id == entry.id
        lines = tmp_ledger_path.read_text(encoding="utf-8").strip().split("\n")
        assert len(lines) == 1


# ---------------------------------------------------------------------------
# Trigger type constants
# ---------------------------------------------------------------------------

class TestTriggerTypes:
    def test_prior_art_triggers(self) -> None:
        assert "discovery" in PRIOR_ART_TRIGGER_TYPES
        assert "decision" in PRIOR_ART_TRIGGER_TYPES
        assert "lesson" not in PRIOR_ART_TRIGGER_TYPES

    def test_open_question_triggers(self) -> None:
        assert "discovery" in OPEN_QUESTION_TRIGGER_TYPES
        assert "decision" not in OPEN_QUESTION_TRIGGER_TYPES
