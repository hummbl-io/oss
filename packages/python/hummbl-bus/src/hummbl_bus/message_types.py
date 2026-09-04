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
        "BELIEF_AUDIT",
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

# Reader-only compatibility for historical rows. These values are not valid
# for new writes and must not be used to extend the canonical vocabulary.
LEGACY_MESSAGE_TYPES = frozenset(
    {
        "AAR",
        "AUDIT",
        "BLOCKER",
        "BUS_LATENCY",
        "BUS_TEST",
        "CANCEL",
        "CHECKPOINT",
        "CLAIM",
        "COMPLETION_REVIEW",
        "COMPLIANCE_SCORE",
        "COORDINATION",
        "CORRECTION",
        "DEAL-MEMO",
        "DESIGN",
        "DISPATCH",
        "DONE",
        "ERROR",
        "ESCALATE",
        "FLEET_QUERY",
        "FRAGO",
        "HEALTH_TRANSITION",
        "HOLD",
        "INFO",
        "INTEL",
        "LATE_SKILL_INVOKE",
        "LEDGER_QUERY",
        "MONITORING_SUMMARY",
        "PHASE_TRANSITION",
        "PROPOSAL_MULTI_DECISION",
        "QUERY",
        "RECEIPT_ACK",
        "RECEIPT_REJECT",
        "REDIRECT",
        "REGISTER",
        "REMEDIATION",
        "REQUEST",
        "REQUEST_RETRY",
        "REQUEST_REVIEW",
        "RESEARCH",
        "RESOLVED",
        "RESUME",
        "SAFETY",
        "SCHEDULED",
        "SESSION_COMPLETE",
        "SPOTREP",
        "STALE_STATE_RESET",
        "TASK_CLAIM",
        "TASK_REJECT",
        "TASK_REQUEST",
        "TERMINATE",
        "TRUST_REPORT",
        "WARN",
        "WARNO",
        "WIN",
    }
)

READABLE_MESSAGE_TYPES = CANONICAL_MESSAGE_TYPES | LEGACY_MESSAGE_TYPES
