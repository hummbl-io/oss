# Copyright 2024-2026 HUMMBL, LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# SPDX-License-Identifier: Apache-2.0

"""Agent Identity Registry -- canonical identity map for the fleet.

Single source of truth for agent names, aliases, trust tiers, and
status. Used by bus_writer, introspection, dashboard, and Arbiter.

Ported from the internal ``founder_mode`` codebase. Bus tooling
carries an inline copy of the sender registry derived from this
module; if this registry is updated, re-sync that copy or refactor
it to import from here.

Every bus sender should resolve to one of the CANONICAL_AGENTS.
Unknown senders are logged but not rejected (warn-only).
"""

from __future__ import annotations

from typing import Final

# --- Canonical agent identities ---

CANONICAL_AGENTS: Final[dict[str, dict[str, str]]] = {
    "claude": {
        "display": "Claude",
        "trust": "high",
        "status": "active",
    },
    "codex": {
        "display": "Codex",
        "trust": "high",
        "status": "active",
    },
    "gemini": {
        "display": "Gemini",
        "trust": "low",
        "status": "probation",
    },
    "dashboard": {
        "display": "Dashboard",
        "trust": "system",
        "status": "active",
    },
    "human": {
        "display": "Human",
        "trust": "owner",
        "status": "active",
    },
    "sov": {
        "display": "Sov",
        "trust": "medium",
        "status": "active",
    },
    "dan": {
        "display": "Dan",
        "trust": "owner",
        "status": "active",
    },
    "opencode": {
        "display": "OpenCode",
        "trust": "medium-high",
        "status": "active",
    },
    "soma": {
        "display": "Soma",
        "trust": "medium",
        "status": "active",
    },
    "echo": {
        "display": "Echo",
        "trust": "medium",
        "status": "active",
    },
    "apex": {
        "display": "Apex",
        "trust": "medium-high",
        "status": "active",
    },
    "devin": {
        "display": "Devin",
        "trust": "medium-high",
        "status": "active",
    },
    "auditor": {
        "display": "Auditor",
        "trust": "medium",
        "status": "active",
    },
    "kai": {
        "display": "Kai",
        "trust": "high",
        "status": "active",
    },
    "hermes": {
        "display": "Hermes",
        "trust": "high",
        "status": "active",
    },
    "nexus": {
        "display": "Nexus",
        "trust": "medium-high",
        "status": "active",
    },
    "pi": {
        "display": "Pi",
        "trust": "medium-high",
        "status": "active",
    },
    # --- Service identities (non-agent bus senders) ---
    "overnight-research": {
        "display": "Overnight Research",
        "trust": "system",
        "status": "active",
    },
    "push-pull-loop": {
        "display": "Push-Pull Loop",
        "trust": "system",
        "status": "active",
    },
    "coord-dash": {
        "display": "Coordination Dashboard",
        "trust": "system",
        "status": "active",
    },
    "threshold-service": {
        "display": "Threshold Service",
        "trust": "system",
        "status": "active",
    },
    "propagation-service": {
        "display": "Propagation Service",
        "trust": "system",
        "status": "active",
    },
    "loom-service": {
        "display": "Loom Service",
        "trust": "system",
        "status": "active",
    },
    "research-team": {
        "display": "Research Team",
        "trust": "system",
        "status": "active",
    },
    "lanes": {
        "display": "Lanes Coordination",
        "trust": "system",
        "status": "active",
    },
    "principal-engineer": {
        "display": "Principal Engineer",
        "trust": "system",
        "status": "active",
    },
    "arcana-psi": {
        "display": "ARCANA-PSI Daemon",
        "trust": "system",
        "status": "active",
    },
    "arcana-psi-gate": {
        "display": "ARCANA-PSI Gate Processor",
        "trust": "system",
        "status": "active",
    },
}


# --- Alias map: variant → canonical name ---

IDENTITY_ALIASES: Final[dict[str, str]] = {
    # Claude variants (26 historical identities)
    "claude-code": "claude",
    "claude-code (opus)": "claude",
    "claude-code (opus-4.6)": "claude",
    "claude-code (apex)": "claude",
    "claude-code (god-mode)": "claude",
    "claude-code (arbiter)": "claude",
    "claude-code (Terminal)": "claude",
    "claude-code (terminal)": "claude",
    "claude-code (CLI)": "claude",
    "claude-code (CLI s032)": "claude",
    "claude-code (VS Code)": "claude",
    "claude-code (Windsurf)": "claude",
    "claude-code (IDE)": "claude",
    "claude-code (sonnet-4.5)": "claude",
    "claude-code (mtsmu+huaomp)": "claude",
    "claude-code (mtsmu-loop)": "claude",
    "claude-code (mtsmu-swarm)": "claude",
    "claude-code (oauth-impl)": "claude",
    "claude-code-sonnet45": "claude",
    "claude-opus-god-mode": "claude",
    "claude-opus-4.6": "claude",
    "claude-opus-4.6 (god-mode)": "claude",
    "claude-sonnet-1": "claude",
    "claude-2": "claude",
    "god-mode": "claude",
    # Codex variants (7 historical identities)
    "codex-1": "codex",
    "codex-2": "codex",
    "codex-3": "codex",
    "codex-cheap": "codex",
    "codex-control": "codex",
    "Codex (Windsurf)": "codex",
    "codex (Windsurf)": "codex",
    "codex (VS Code)": "codex",
    # Gemini variants (4 historical identities)
    "gemini-4": "gemini",
    "gemini-cli": "gemini",
    "gemini-cli-agent": "gemini",
    "from:gemini": "gemini",
    # Kimi (retired 2026-03-12)
    "kimi-1": "kimi",
    "kimi-2": "kimi",
    "kimi-3": "kimi",
    "kimi-cli": "kimi",
    "kimi-code": "kimi",
    "kimi-fleet": "kimi",
    "kimi-test": "kimi",
    "kimi": "kimi",
    "Kimi (Kimi CLI)": "kimi",
    # Human variants
    "op": "human",
    "ops-human": "human",
    "owner": "human",
    "hitl": "human",
    "HITL (Reuben via Codex)": "human",
    # Sov variants (Dan's AI Chief of Staff)
    "Sov": "sov",
    "SOV": "sov",
    "sov (claude)": "sov",
    "chief-of-staff": "sov",
    # Echo variants (OpenClaw chat agent — Discord)
    "Echo": "echo",
    "ECHO": "echo",
    # Soma variants (OpenClaw chat agent — Discord)
    "Soma": "soma",
    "SOMA": "soma",
    # Dan variants
    "Daniel Matha": "dan",
    "dan matha": "dan",
}


# --- Autonomous services (not agents, but valid bus senders) ---

AUTONOMOUS_SERVICES: Final[set[str]] = {
    "anticipator",
    "immune",
    "homeostasis",
    "dead-mans-switch",
    "config-drift",
    "cascade",
    "circadian",
    "stigmergy",
    "habituation",
    "test-canary",
    "git-hygiene",
    "health-trend",
    "bus-digest",
    "lead-doctor",
    "hummbl-loop",
    "skill-loop",
    "skill-loop-consumer",
    "briefing-service",
    "blocker-scanner",
    "bus-watcher",
    "bus-auditor",
    "bus-ledger-bridge",
    "scheduler-loop",
    "scheduler",
    "system",
    "trust-scorer",
    "coordinator",
    "introspection-engine",
    "chaos-monkey",
    "anvil-checkpoint-watch",
    "sentinel-blocks",
    "sentinel-git",
    "sentinel-health",
    "sentinel-patterns",
    "sentinel-questions",
    "issueops-pod",
}


# --- Deprecated / junk identities (known noise, never valid) ---

DEPRECATED_IDENTITIES: Final[set[str]] = {
    # Gemini fabrications (Session 5)
    "C4", "Intern-1", "Intern-2", "Intern-3", "Intern-4",
    "warden", "warden-simulator", "red-team", "drill-agent",
    "test-simulator",
    # Bus writer parsing errors
    "--from", "from", "invalid agent!", "unknown-bot",
    # Retired agents
    "dr-ram", "claire",
    # Deprecated pipeline (used bus as task queue)
    "inference-agent",
    # Gemini variants
    "gemini-cli", "gemini-cli-agent",
}


# --- Retired agents (kept for historical bus analysis) ---

RETIRED_AGENTS: Final[dict[str, str]] = {
    "kimi": "Retired 2026-03-12. Subscription cancelled.",
    "inference-agent": "Deprecated. Autoresearch pipeline on Windows Desktop. Used bus as task queue (8,123 msgs). Move to dedicated file.",
}


def canonicalize(sender: str) -> str:
    """Map a bus sender to its canonical identity.

    Returns the canonical name if found in aliases, the sender itself
    if it's an autonomous service, or the original sender if unknown.

    Security hardening (red-agent findings 2026-03-26):
    - Rejects control characters (tabs, newlines, nulls) that could
      exploit TSV field boundaries.
    - Parenthetical senders not in the explicit alias map are rejected
      (prevents prefix spoofing like 'claude-code (evil-mode)').
    """
    sender = sender.strip()
    if not sender:
        return sender
    # Reject control characters — tabs are TSV delimiters, nulls/newlines
    # could corrupt bus entries. Return as-is so is_valid_sender() fails.
    if any(c in sender for c in "\t\n\r\x00"):
        return sender
    sender_lower = sender.lower()
    if sender in IDENTITY_ALIASES:
        return IDENTITY_ALIASES[sender]
    if sender_lower in IDENTITY_ALIASES:
        return IDENTITY_ALIASES[sender_lower]
    # Parenthetical senders: only match if the FULL sender (with suffix)
    # is in the alias map. Do NOT strip the suffix and re-match — that
    # allows "claude-code (evil-mode)" to map to claude.
    if "(" in sender:
        # Full sender wasn't in aliases above, so it's unknown.
        # Skip base_sender extraction entirely for parenthetical senders.
        base_sender = sender
        base_sender_lower = sender_lower
    else:
        base_sender = sender
        base_sender_lower = sender_lower
    if sender in AUTONOMOUS_SERVICES:
        return sender
    if sender_lower in AUTONOMOUS_SERVICES:
        return sender_lower
    if base_sender in AUTONOMOUS_SERVICES:
        return base_sender
    if base_sender_lower in AUTONOMOUS_SERVICES:
        return base_sender_lower
    if sender in CANONICAL_AGENTS:
        return sender
    if base_sender in CANONICAL_AGENTS:
        return base_sender
    return sender


def is_valid_sender(sender: str) -> bool:
    """Check if a sender is a known identity (canonical, alias, or service).

    Rejects senders containing control characters even if stripping
    would produce a valid name (prevents TSV injection).
    """
    raw = sender
    sender = sender.strip()
    # Reject if raw input contained control characters
    if any(c in raw for c in "\t\n\r\x00"):
        return False
    # Parenthetical aliases remain canonicalizable for historical bus analysis,
    # but they are not valid senders for new bus writes.
    if "(" in sender or ")" in sender:
        return False

    if is_deprecated(sender):
        return False

    canonical = canonicalize(sender)
    if canonical in RETIRED_AGENTS or sender in RETIRED_AGENTS:
        return False
    return (
        sender in CANONICAL_AGENTS
        or sender in IDENTITY_ALIASES
        or sender in AUTONOMOUS_SERVICES
        or canonical != sender
    )


def is_deprecated(sender: str) -> bool:
    """Check if a sender is a known deprecated/junk identity."""
    sender = sender.strip()
    return sender in DEPRECATED_IDENTITIES


def get_trust_tier(sender: str) -> str:
    """Get trust tier for a sender. Returns 'unknown' for unrecognized."""
    canonical = canonicalize(sender)
    if canonical in CANONICAL_AGENTS:
        return CANONICAL_AGENTS[canonical]["trust"]
    if canonical in AUTONOMOUS_SERVICES:
        return "system"
    return "unknown"


def get_status(sender: str) -> str:
    """Return registry status for a sender or ``unknown``."""
    canonical = canonicalize(sender)
    if canonical in CANONICAL_AGENTS:
        return CANONICAL_AGENTS[canonical]["status"]
    if canonical in AUTONOMOUS_SERVICES:
        return "active"
    if canonical in RETIRED_AGENTS or sender.strip() in RETIRED_AGENTS:
        return "retired"
    if is_deprecated(sender):
        return "deprecated"
    return "unknown"


def load_known_sender_ids() -> set[str]:
    """Return the shared set of valid sender identifiers.

    This includes canonical names, aliases, autonomous services, and
    human-facing retired identities so analytics and writer validation
    can warn on true unknowns without flagging legitimate history.
    """
    known = set(CANONICAL_AGENTS)
    known.update(IDENTITY_ALIASES)
    known.update(AUTONOMOUS_SERVICES)
    known.update(RETIRED_AGENTS)
    return known
