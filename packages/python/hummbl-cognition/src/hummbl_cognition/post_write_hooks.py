"""Post-write hooks for the Cognitive Ledger Protocol.

Fires automatically after a ledger entry is successfully appended. Turns
prior-art discovery and open-question extraction from pull (agent must ask)
into push (happens automatically when a discovery or decision lands).

Hooks enqueue research queries to the research_processor's queue file
(_state/cognition/research_queue.json). The existing research_processor
cron (every 2 hours on nodezero) picks them up, runs them through Ollama,
and posts results back to the ledger as discovery entries linked to the
trigger entry via the links field.

Architecture:
    post_entry() appends to ledger
      -> fire_post_write_hooks(entry)
         -> prior_art_hook      (for discovery + decision)
         -> open_question_hook  (for discovery only)
         -> each builds a query, appends to research queue
         -> (existing cron) research_processor runs query via Ollama
         -> result posted to ledger with links=[trigger_entry_id]

Env vars (opt-out):
    CLP_POST_WRITE_HOOKS=off    -> disable all hooks
    CLP_HOOK_PRIOR_ART=off      -> disable prior_art hook only
    CLP_HOOK_OPEN_QUESTION=off  -> disable open_question hook only

Stdlib only. Zero third-party dependencies.
"""

from __future__ import annotations

import logging
import os
import threading
from typing import Any

from hummbl_cognition.models import LedgerEntry
from hummbl_cognition.research_processor import (
    DEFAULT_QUEUE_FILE,
    load_research_queue,
    save_research_queue,
)

logger = logging.getLogger(__name__)

# Entry types that trigger hooks.
PRIOR_ART_TRIGGER_TYPES: frozenset[str] = frozenset({"discovery", "decision"})
OPEN_QUESTION_TRIGGER_TYPES: frozenset[str] = frozenset({"discovery"})

# Tier mapping: discovery=1 (high priority), decision=2.
_TIER_BY_TYPE: dict[str, int] = {"discovery": 1, "decision": 2}

# Max content chars to include in the query prompt (keep Ollama context small).
_MAX_CONTENT_CHARS = 500

# Serializes queue file load+check+save so concurrent posts don't lose updates.
_QUEUE_LOCK = threading.Lock()


def _truncate(text: str, limit: int = _MAX_CONTENT_CHARS) -> str:
    """Truncate text to limit chars, appending ellipsis if cut."""
    if len(text) <= limit:
        return text
    return text[:limit].rsplit(" ", 1)[0] + "..."


def _tags_to_focus(tags: tuple[str, ...]) -> str:
    """Convert tags tuple to a human-readable focus string."""
    if not tags:
        return "general"
    return ", ".join(tags)


def build_prior_art_query(entry: LedgerEntry) -> dict[str, Any]:
    """Build a prior-art research query from a ledger entry.

    The query asks Ollama to find existing research that supports,
    contradicts, or precedes the entry's content.
    """
    content = _truncate(entry.content)
    focus = _tags_to_focus(entry.tags)
    query = (
        f"Find prior art and existing research related to the following "
        f"{entry.type}:\n\n"
        f'"{content}"\n\n'
        f"Focus areas: {focus}\n\n"
        f"Identify:\n"
        f"1. Existing published research that supports this finding\n"
        f"2. Existing research that contradicts or complicates this finding\n"
        f"3. Key prior work that this finding builds on\n"
        f"4. Citation relationships (who cites whom)\n\n"
        f"Provide specific paper titles, authors, and venues where possible."
    )
    return {
        "id": f"PA-{entry.id}",
        "domain": "prior-art-discovery",
        "query": query,
        "tier": _TIER_BY_TYPE.get(entry.type, 2),
        "recurrence": "once",
        "hook": "prior_art",
        "trigger_entry_id": entry.id,
    }


def build_open_question_query(entry: LedgerEntry) -> dict[str, Any]:
    """Build an open-question research query from a ledger entry.

    The query asks Ollama to surface unsolved problems, gaps, and future
    work directions revealed by the entry's content.
    """
    content = _truncate(entry.content)
    focus = _tags_to_focus(entry.tags)
    query = (
        f"Identify open research questions and gaps related to the following "
        f"{entry.type}:\n\n"
        f'"{content}"\n\n'
        f"Focus areas: {focus}\n\n"
        f"Surface:\n"
        f"1. What unsolved problems does this discovery reveal?\n"
        f"2. What limitations does this work acknowledge?\n"
        f"3. What future work does this suggest?\n"
        f"4. What contradictions in the literature remain unresolved?\n\n"
        f"Provide specific, actionable research questions."
    )
    return {
        "id": f"OQ-{entry.id}",
        "domain": "open-question-discovery",
        "query": query,
        "tier": _TIER_BY_TYPE.get(entry.type, 2),
        "recurrence": "once",
        "hook": "open_question",
        "trigger_entry_id": entry.id,
    }


def _append_to_queue(
    query: dict[str, Any],
    queue_path: str | os.PathLike[str] | None = None,
) -> bool:
    """Append a query to the research queue. Returns True on success.

    Idempotent: if a query with the same id already exists, skip.
    Thread-safe: serializes load+check+save under _QUEUE_LOCK so concurrent
    posts don't lose updates.
    """
    try:
        with _QUEUE_LOCK:
            queue = load_research_queue(queue_path)
            # Skip if already enqueued (same id)
            existing_ids = {q.get("id") for q in queue}
            if query["id"] in existing_ids:
                logger.debug("Query %s already in queue, skipping", query["id"])
                return True
            queue.append(query)
            save_research_queue(queue, queue_path)
        logger.info("Enqueued research query: %s", query["id"])
        return True
    except Exception as exc:
        # Hooks must never break the post. Log and swallow.
        logger.warning("Failed to enqueue query %s: %s", query.get("id"), exc)
        return False


def fire_post_write_hooks(
    entry: LedgerEntry,
    *,
    queue_path: str | os.PathLike[str] | None = None,
) -> list[str]:
    """Fire post-write hooks for a newly appended ledger entry.

    Returns a list of hook names that fired (empty if none).

    Env vars:
        CLP_POST_WRITE_HOOKS=off    -> disable all hooks
        CLP_HOOK_PRIOR_ART=off      -> disable prior_art hook only
        CLP_HOOK_OPEN_QUESTION=off  -> disable open_question hook only
    """
    # Global opt-out
    if os.environ.get("CLP_POST_WRITE_HOOKS", "on").lower() == "off":
        logger.debug("Post-write hooks globally disabled")
        return []

    fired: list[str] = []

    # Prior art hook (discovery + decision)
    if (
        entry.type in PRIOR_ART_TRIGGER_TYPES
        and os.environ.get("CLP_HOOK_PRIOR_ART", "on").lower() != "off"
    ):
        query = build_prior_art_query(entry)
        if _append_to_queue(query, queue_path):
            fired.append("prior_art")

    # Open question hook (discovery only)
    if (
        entry.type in OPEN_QUESTION_TRIGGER_TYPES
        and os.environ.get("CLP_HOOK_OPEN_QUESTION", "on").lower() != "off"
    ):
        query = build_open_question_query(entry)
        if _append_to_queue(query, queue_path):
            fired.append("open_question")

    return fired
