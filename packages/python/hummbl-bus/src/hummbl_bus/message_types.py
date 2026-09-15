"""Canonical coordination-bus message vocabulary.

New writes use ``CANONICAL_MESSAGE_TYPES``. Readers use
``READABLE_MESSAGE_TYPES`` so append-only historical rows remain parseable.

Promoted from hummbl-governance/bus/message_types.py 2026-08-15.
"""

from __future__ import annotations

CANONICAL_MESSAGE_TYPES = frozenset(
    {
        "ACK",
        "ALERT",
        "APPROVE",
        "BLOCKED",
        "COMPLETE",
        "DECISION",
        "DIRECTIVE",
        "HANDOFF",
        "HEARTBEAT",
        "HRSI_CHECKIN",
        "MILESTONE",
        "PROPOSAL",
        "QUESTION",
        "RECEIPT",
        "REJECT",
        "REVIEW",
        "SITREP",
        "SKILL_INVOKE",
        "STATUS",
        "TASK_COMPLETE",
        "VERIFY",
        "VETO",
        "WIP_END",
        "WIP_START",
    }
)

# Readers accept exactly the canonical vocabulary.  Legacy types were removed
# (ponytail-review cut); historical rows with retired types are now treated as
# drift by the auditor rather than silently accepted.
READABLE_MESSAGE_TYPES = CANONICAL_MESSAGE_TYPES
