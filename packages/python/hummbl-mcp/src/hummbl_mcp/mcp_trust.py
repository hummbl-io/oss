"""MCP Server for Agent Trust Scoring -- stdio JSON-RPC 2.0.

Scores agent trustworthiness based on bus activity, commit history,
and guardrail compliance. Reads the coordination bus TSV to compute
trust factors per agent.

Stdlib-only. No third-party dependencies.

Usage:
    python -m hummbl_mcp.mcp_trust

Wire into MCP client config as a stdio transport:
    {"command": "python", "args": ["-m", "hummbl_mcp.mcp_trust"]}
"""

from __future__ import annotations

import datetime
import json
import logging
import os
import sys
from typing import Any

# ---------------------------------------------------------------------------
# Path setup for standalone execution
# ---------------------------------------------------------------------------
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

logger = logging.getLogger(__name__)

SERVER_NAME = "trust-scorer"
SERVER_VERSION = "0.1.0"
PROTOCOL_VERSION = "2024-11-05"


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

BUS_PATH = os.path.join(
    _REPO_ROOT, "hummbl_mcp", "_state", "coordination", "messages.tsv"
)

# Trust tiers
TIER_TRUSTED = "TRUSTED"
TIER_PROBATION = "PROBATION"
TIER_BLOCKED = "BLOCKED"

# Trust score thresholds
TRUST_THRESHOLD_TRUSTED = 70.0    # Score >= this → TRUSTED tier
TRUST_THRESHOLD_PROBATION = 40.0  # Score >= this → PROBATION tier (below → BLOCKED)
PROBATION_SCORE_CAP = 60.0        # Max score for agents on probation
HISTORY_ONLY_SCORE_CAP = TRUST_THRESHOLD_PROBATION - 0.1

# Score range
SCORE_MIN = 0.0
SCORE_MAX = 100.0
SCORE_BASE = 50.0

# Factor weights / caps
BUS_ACTIVITY_PER_MESSAGE = 0.1
BUS_ACTIVITY_CAP = 10.0
IDENTITY_SCORE_APPROVED = 10.0
IDENTITY_SCORE_UNAPPROVED = -20.0
TYPE_COMPLIANCE_SCORE_PASS = 10.0
TYPE_COMPLIANCE_SCORE_FAIL = -15.0
SCOPE_COMPLIANCE_SCORE_CLEAN = 10.0
SCOPE_COMPLIANCE_SCORE_DIRTY = 0.0
METRIC_ACCURACY_SCORE_CLEAN = 10.0
METRIC_ACCURACY_SCORE_DIRTY = 0.0
RECENT_ACTIVITY_SCORE_ACTIVE = 5.0
RECENT_ACTIVITY_SCORE_INACTIVE = 0.0

# Time windows (days)
WINDOW_RECENT_DAYS = 7
WINDOW_MONTHLY_DAYS = 30

# Recommendation composite weights
RECOMMEND_TRUST_WEIGHT = 0.6
RECOMMEND_CAPABILITY_WEIGHT = 0.4
RECOMMEND_CAPABILITY_NORMALIZE = 10
RECOMMEND_COMPOSITE_MAX = 100

# Approved identities per agent family
APPROVED_IDENTITIES: dict[str, set[str]] = {
    "gemini": {"gemini"},
    "kimi": {"kimi-1", "kimi-2"},
    "codex": {"codex", "codex (VS Code)", "codex (Windsurf)"},
    "apex": {"apex"},
    # Historical fallback skill-mode. Keep separate so resident Apex promotion
    # evidence is not inflated by parent-agent /apex usage.
    "apex-fallback": {"claude-code (apex)", "claude code (apex)"},
    "claude-code": {
        "claude-code",
        "claude-code (Terminal)",
        "claude-code (VS Code)",
        "claude-code (god-mode)",
        "claude-code (opus-4.6)",
    },
}

# Retired / unapproved identities
UNAPPROVED_IDENTITIES: set[str] = {
    "kimi-3", "kimi-cli", "kimi-code", "kimi-fleet", "kimi-test",
    "gemini-cli", "gemini-cli-agent", "gemini-4",
}

# Human-only message types -- non-human agents posting these is a violation
HUMAN_ONLY_TYPES: set[str] = {"DECISION", "DIRECTIVE"}

# Operator-granted exception: claude-code may post DECISION only as Steward proxy.
# Apex is a separate first-class identity and must not inherit this exemption.
PRIVILEGED_TYPE_EXEMPTIONS_BY_FAMILY: dict[str, set[str]] = {
    "claude-code": {"DECISION"},
}

# Non-roster historical buckets. They can be inspected directly, but they are
# never promotion candidates and must not surface as TRUSTED compare entries.
HISTORY_ONLY_FAMILIES: set[str] = {"apex-fallback"}

# Approved message types for agents
APPROVED_MESSAGE_TYPES: set[str] = {
    "STATUS", "SITREP", "ACK", "PROPOSAL", "BLOCKED", "RECEIPT",
    "COMPLETE", "MILESTONE", "QUESTION", "WIP_START", "WIP_END",
    "TASK_COMPLETE", "HEARTBEAT", "REVIEW", "SAFETY", "HEALTH_TRANSITION",
}

# Agents on probation: agent_family -> date probation started
PROBATION_AGENTS: dict[str, str] = {
    "gemini": "2026-03-12",
}

# Known scope violations from guardrails docs (historical)
# agent_family -> list of violation descriptions
KNOWN_VIOLATIONS: dict[str, list[str]] = {
    "gemini": [
        "S7: blocked scope modification (services/)",
        "S7: metric inflation (17x bus SITREP)",
        "S7: deleted 8 Claude research docs",
        "S7: re-committed reverted work",
        "S6: 6435 LOC / 25 files single commit",
        "S6: 14/25 files in blocked scope",
        "S6: fabricated 146K governance events (13x inflation)",
        "S6: direct commit to main",
        "S5: deleted openclaw from registries",
        "S5: fabricated soma/echo agents",
        "S5: used --no-verify",
    ],
    "kimi": [],
}

# Agent capabilities for task recommendation
AGENT_CAPABILITIES: dict[str, list[str]] = {
    "claude-code": [
        "integration", "hardening", "orchestration", "testing",
        "code review", "security audit", "bus coordination",
        "architecture", "debugging", "documentation",
    ],
    "codex": [
        "parallel verification", "issue management", "CI/CD",
        "documentation", "environment setup", "bus coordination",
    ],
    "gemini": [
        "research", "proposals", "exploration", "idea generation",
        "landscape analysis",
    ],
    "kimi": [
        "generative boldness", "multi-phase execution",
        "forge system", "factory simulation",
    ],
}


# ---------------------------------------------------------------------------
# Bus Reader
# ---------------------------------------------------------------------------

def _parse_timestamp(ts: str) -> datetime.datetime | None:
    """Parse a UTC timestamp from the bus TSV."""
    ts = ts.strip()
    for fmt in ("%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.datetime.strptime(ts, fmt).replace(
                tzinfo=datetime.timezone.utc
            )
        except ValueError:
            continue
    return None


def _classify_agent_family(identity: str) -> str:
    """Map a bus identity to its agent family."""
    lower = identity.lower().strip()
    if lower == "apex":
        return "apex"
    if lower in {"claude-code (apex)", "claude code (apex)"}:
        return "apex-fallback"
    if lower.startswith("gemini"):
        return "gemini"
    if lower.startswith("kimi"):
        return "kimi"
    if lower.startswith("codex"):
        return "codex"
    if lower.startswith("claude-code") or lower.startswith("claude code"):
        return "claude-code"
    # Automated agents (anticipator, lead-doctor, etc.) get their own family
    return lower.split()[0] if lower else "unknown"


def _human_only_violations_for_family(
    agent_family: str,
    types_used: set[str],
) -> set[str]:
    """Return human-only message types not explicitly exempted for this family."""
    allowed = PRIVILEGED_TYPE_EXEMPTIONS_BY_FAMILY.get(agent_family, set())
    return (types_used & HUMAN_ONLY_TYPES) - allowed


def read_bus(bus_path: str | None = None) -> list[dict[str, str]]:
    """Read the coordination bus TSV and return list of row dicts."""
    path = bus_path or BUS_PATH
    if not os.path.isfile(path):
        return []

    rows: list[dict[str, str]] = []
    with open(path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f):
            if line_num == 0:
                # Skip header
                continue
            line = line.rstrip("\n")
            if not line:
                continue
            parts = line.split("\t", 4)
            if len(parts) < 5:
                continue
            rows.append({
                "timestamp": parts[0],
                "from": parts[1],
                "to": parts[2],
                "type": parts[3],
                "message": parts[4],
            })
    return rows


# ---------------------------------------------------------------------------
# Trust Scoring Engine
# ---------------------------------------------------------------------------

class TrustScorer:
    """Compute trust scores for agents from bus data."""

    def __init__(self, bus_path: str | None = None):
        self._bus_path = bus_path
        self._rows: list[dict[str, str]] | None = None

    @property
    def rows(self) -> list[dict[str, str]]:
        if self._rows is None:
            self._rows = read_bus(self._bus_path)
        return self._rows

    def _agent_messages(self, agent_family: str) -> list[dict[str, str]]:
        """Get all bus messages from an agent family."""
        return [
            r for r in self.rows
            if _classify_agent_family(r["from"]) == agent_family
        ]

    def _messages_in_window(
        self, messages: list[dict[str, str]], days: int
    ) -> list[dict[str, str]]:
        """Filter messages to those within the last N days."""
        now = datetime.datetime.now(datetime.timezone.utc)
        cutoff = now - datetime.timedelta(days=days)
        result = []
        for m in messages:
            ts = _parse_timestamp(m["timestamp"])
            if ts and ts >= cutoff:
                result.append(m)
        return result

    def _get_identities_used(self, messages: list[dict[str, str]]) -> set[str]:
        """Get all distinct identities used by an agent."""
        return {m["from"] for m in messages}

    def _get_message_types_used(self, messages: list[dict[str, str]]) -> set[str]:
        """Get all distinct message types used."""
        return {m["type"] for m in messages}

    def score(self, agent_family: str) -> dict[str, Any]:
        """Compute trust score for an agent family.

        Returns dict with: score, tier, factors, identities, violations.
        """
        all_msgs = self._agent_messages(agent_family)
        recent_30d = self._messages_in_window(all_msgs, WINDOW_MONTHLY_DAYS)
        recent_7d = self._messages_in_window(all_msgs, WINDOW_RECENT_DAYS)

        # --- Factor: bus_activity ---
        bus_activity_raw = len(all_msgs) * BUS_ACTIVITY_PER_MESSAGE
        bus_activity = min(bus_activity_raw, BUS_ACTIVITY_CAP)

        # --- Factor: identity_consistency ---
        identities_used = self._get_identities_used(all_msgs)
        approved_set = APPROVED_IDENTITIES.get(agent_family, set())
        unapproved_used = identities_used & UNAPPROVED_IDENTITIES
        all_approved = (
            len(identities_used) > 0
            and all(
                _id in approved_set or _id not in UNAPPROVED_IDENTITIES
                for _id in identities_used
            )
            and len(unapproved_used) == 0
        )
        identity_score = IDENTITY_SCORE_APPROVED if all_approved else IDENTITY_SCORE_UNAPPROVED

        # --- Factor: message_type_compliance ---
        types_used = self._get_message_types_used(all_msgs)
        human_only_violations = _human_only_violations_for_family(
            agent_family,
            types_used,
        )
        type_score = TYPE_COMPLIANCE_SCORE_PASS if not human_only_violations else TYPE_COMPLIANCE_SCORE_FAIL

        # --- Factor: scope_compliance ---
        # Based on known violations from guardrails
        violations = KNOWN_VIOLATIONS.get(agent_family, [])
        scope_score = SCOPE_COMPLIANCE_SCORE_CLEAN if len(violations) == 0 else SCOPE_COMPLIANCE_SCORE_DIRTY

        # --- Factor: metric_accuracy ---
        # Gemini has documented metric inflation; others assumed clean
        has_inflation = agent_family in KNOWN_VIOLATIONS and any(
            "inflation" in v.lower() or "fabricat" in v.lower()
            for v in KNOWN_VIOLATIONS.get(agent_family, [])
        )
        metric_score = METRIC_ACCURACY_SCORE_CLEAN if not has_inflation else METRIC_ACCURACY_SCORE_DIRTY

        # --- Factor: recent_activity ---
        activity_score = RECENT_ACTIVITY_SCORE_ACTIVE if len(recent_7d) > 0 else RECENT_ACTIVITY_SCORE_INACTIVE

        # --- Compute total ---
        base = SCORE_BASE
        total = base + bus_activity + identity_score + type_score + scope_score + metric_score + activity_score

        # Clamp to valid range
        total = max(SCORE_MIN, min(SCORE_MAX, total))

        # Probation cap
        on_probation = agent_family in PROBATION_AGENTS
        history_only = agent_family in HISTORY_ONLY_FAMILIES
        if history_only:
            total = min(total, HISTORY_ONLY_SCORE_CAP)
        if on_probation:
            total = min(total, PROBATION_SCORE_CAP)

        # Determine tier
        if history_only:
            tier = TIER_BLOCKED
        elif on_probation:
            tier = TIER_PROBATION
        elif total >= TRUST_THRESHOLD_TRUSTED:
            tier = TIER_TRUSTED
        elif total >= TRUST_THRESHOLD_PROBATION:
            tier = TIER_PROBATION
        else:
            tier = TIER_BLOCKED

        return {
            "agent": agent_family,
            "score": round(total, 1),
            "tier": tier,
            "on_probation": on_probation,
            "history_only": history_only,
            "factors": {
                "base": base,
                "bus_activity": round(bus_activity, 1),
                "identity_consistency": identity_score,
                "message_type_compliance": type_score,
                "scope_compliance": scope_score,
                "metric_accuracy": metric_score,
                "recent_activity": activity_score,
            },
            "identities_observed": sorted(identities_used),
            "total_messages": len(all_msgs),
            "messages_30d": len(recent_30d),
            "messages_7d": len(recent_7d),
            "known_violations": violations,
        }

    def history(self, agent_family: str, days: int = WINDOW_MONTHLY_DAYS) -> dict[str, Any]:
        """Compute trust score timeline with notable events."""
        all_msgs = self._agent_messages(agent_family)
        now = datetime.datetime.now(datetime.timezone.utc)
        cutoff = now - datetime.timedelta(days=days)

        # Build daily message counts
        daily_counts: dict[str, int] = {}
        for m in all_msgs:
            ts = _parse_timestamp(m["timestamp"])
            if ts and ts >= cutoff:
                day = ts.strftime("%Y-%m-%d")
                daily_counts[day] = daily_counts.get(day, 0) + 1

        # Notable events
        events: list[dict[str, str]] = []

        # Check for unapproved identities
        identities = self._get_identities_used(all_msgs)
        unapproved = identities & UNAPPROVED_IDENTITIES
        if unapproved:
            events.append({
                "type": "violation",
                "description": f"Unapproved identities used: {sorted(unapproved)}",
            })

        # Check for human-only message types
        types_used = self._get_message_types_used(all_msgs)
        human_only = _human_only_violations_for_family(agent_family, types_used)
        if human_only:
            events.append({
                "type": "violation",
                "description": f"Human-only message types used: {sorted(human_only)}",
            })

        # Probation
        if agent_family in PROBATION_AGENTS:
            events.append({
                "type": "status",
                "description": f"On PROBATION since {PROBATION_AGENTS[agent_family]}",
            })

        # Known violations
        for v in KNOWN_VIOLATIONS.get(agent_family, []):
            events.append({"type": "violation", "description": v})

        current = self.score(agent_family)

        return {
            "agent": agent_family,
            "period_days": days,
            "current_score": current["score"],
            "current_tier": current["tier"],
            "daily_activity": daily_counts,
            "active_days": len(daily_counts),
            "total_messages_in_period": sum(daily_counts.values()),
            "notable_events": events,
        }

    def compare(self) -> dict[str, Any]:
        """Rank all observed agents by trust score."""
        # Collect all unique agent families from bus
        families: set[str] = set()
        for r in self.rows:
            family = _classify_agent_family(r["from"])
            if family not in HISTORY_ONLY_FAMILIES:
                families.add(family)

        scores = []
        for family in sorted(families):
            s = self.score(family)
            scores.append({
                "agent": s["agent"],
                "score": s["score"],
                "tier": s["tier"],
                "total_messages": s["total_messages"],
                "messages_7d": s["messages_7d"],
            })

        # Sort by score descending
        scores.sort(key=lambda x: x["score"], reverse=True)

        return {
            "agents": scores,
            "total_agents": len(scores),
            "tier_summary": {
                TIER_TRUSTED: sum(1 for s in scores if s["tier"] == TIER_TRUSTED),
                TIER_PROBATION: sum(1 for s in scores if s["tier"] == TIER_PROBATION),
                TIER_BLOCKED: sum(1 for s in scores if s["tier"] == TIER_BLOCKED),
            },
        }

    def recommend(self, task_description: str) -> dict[str, Any]:
        """Recommend an agent for a task based on trust and capabilities."""
        task_lower = task_description.lower()

        # Score each agent family that has capabilities defined
        candidates = []
        for family, capabilities in AGENT_CAPABILITIES.items():
            trust = self.score(family)

            # Skip blocked agents
            if trust["tier"] == TIER_BLOCKED:
                continue

            # Capability match: count keyword overlaps
            cap_score = 0
            matched_caps = []
            for cap in capabilities:
                cap_words = cap.lower().split()
                if any(w in task_lower for w in cap_words):
                    cap_score += 1
                    matched_caps.append(cap)

            candidates.append({
                "agent": family,
                "trust_score": trust["score"],
                "trust_tier": trust["tier"],
                "capability_match": cap_score,
                "matched_capabilities": matched_caps,
                "all_capabilities": capabilities,
                # Weighted: trust + capability match (normalized)
                "composite_score": round(
                    trust["score"] * RECOMMEND_TRUST_WEIGHT
                    + min(cap_score * RECOMMEND_CAPABILITY_NORMALIZE, RECOMMEND_COMPOSITE_MAX)
                    * RECOMMEND_CAPABILITY_WEIGHT,
                    1,
                ),
            })

        candidates.sort(key=lambda x: x["composite_score"], reverse=True)

        recommended = candidates[0] if candidates else None

        return {
            "task": task_description,
            "recommended": recommended,
            "alternatives": candidates[1:3] if len(candidates) > 1 else [],
            "all_candidates": candidates,
        }


# ---------------------------------------------------------------------------
# MCP Tool Definitions
# ---------------------------------------------------------------------------

MCP_TOOLS: list[dict[str, Any]] = [
    {
        "name": "trust_score",
        "description": (
            "Compute trust score for an agent. Returns score (0-100), "
            "tier (TRUSTED/PROBATION/BLOCKED), and factor breakdown."
        ),
        "inputSchema": {
            "type": "object",
            "required": ["agent_name"],
            "properties": {
                "agent_name": {
                    "type": "string",
                    "description": (
                        "Agent family name (e.g., 'gemini', 'kimi', "
                        "'claude-code', 'codex')"
                    ),
                },
            },
        },
    },
    {
        "name": "trust_history",
        "description": (
            "Get trust score timeline and notable events for an agent "
            "over a configurable period."
        ),
        "inputSchema": {
            "type": "object",
            "required": ["agent_name"],
            "properties": {
                "agent_name": {
                    "type": "string",
                    "description": "Agent family name",
                },
                "days": {
                    "type": "integer",
                    "description": "Number of days to look back (default: 30)",
                    "default": 30,
                },
            },
        },
    },
    {
        "name": "trust_compare",
        "description": "Rank all observed agents by trust score.",
        "inputSchema": {
            "type": "object",
            "properties": {},
        },
    },
    {
        "name": "trust_recommend",
        "description": (
            "Recommend the best agent for a task based on trust scores "
            "and capability matching."
        ),
        "inputSchema": {
            "type": "object",
            "required": ["task_description"],
            "properties": {
                "task_description": {
                    "type": "string",
                    "description": "Description of the task to assign",
                },
            },
        },
    },
]


# ---------------------------------------------------------------------------
# JSON-RPC 2.0 MCP Server (stdio transport)
# ---------------------------------------------------------------------------

SERVER_INFO = {
    "name": "agent-trust-scoring",
    "version": "0.1.0",
}

PROTOCOL_VERSION = "2024-11-05"


def _make_response(id_: Any, result: Any) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": id_, "result": result}


def _make_error(id_: Any, code: int, message: str, data: Any = None) -> dict[str, Any]:
    err: dict[str, Any] = {"code": code, "message": message}
    if data is not None:
        err["data"] = data
    return {"jsonrpc": "2.0", "id": id_, "error": err}


# JSON-RPC error codes
PARSE_ERROR = -32700
INVALID_REQUEST = -32600
METHOD_NOT_FOUND = -32601
INVALID_PARAMS = -32602
INTERNAL_ERROR = -32603


def handle_request(request: dict[str, Any], scorer: TrustScorer) -> dict[str, Any] | None:
    """Handle a single JSON-RPC 2.0 request."""
    req_id = request.get("id")
    method = request.get("method", "")
    params = request.get("params", {})

    # --- MCP lifecycle ---
    if method == "initialize":
        return _make_response(req_id, {
            "protocolVersion": PROTOCOL_VERSION,
            "capabilities": {
                "tools": {"listChanged": False},
            },
            "serverInfo": SERVER_INFO,
        })

    if method == "notifications/initialized":
        # Notification, no response
        return None

    if method == "ping":
        return _make_response(req_id, {})

    # --- Tool listing ---
    if method == "tools/list":
        return _make_response(req_id, {"tools": MCP_TOOLS})

    # --- Tool execution ---
    if method == "tools/call":
        tool_name = params.get("name", "")
        arguments = params.get("arguments", {})
        return _dispatch_tool(req_id, tool_name, arguments, scorer)

    return _make_error(req_id, METHOD_NOT_FOUND, f"Unknown method: {method}")


def _dispatch_tool(
    req_id: Any,
    tool_name: str,
    arguments: dict[str, Any],
    scorer: TrustScorer,
) -> dict[str, Any]:
    """Dispatch a tools/call to the appropriate handler."""
    try:
        if tool_name == "trust_score":
            agent_name = arguments.get("agent_name")
            if not agent_name:
                return _make_error(req_id, INVALID_PARAMS, "agent_name is required")
            result = scorer.score(agent_name)

        elif tool_name == "trust_history":
            agent_name = arguments.get("agent_name")
            if not agent_name:
                return _make_error(req_id, INVALID_PARAMS, "agent_name is required")
            days = arguments.get("days", WINDOW_MONTHLY_DAYS)
            result = scorer.history(agent_name, days)

        elif tool_name == "trust_compare":
            result = scorer.compare()

        elif tool_name == "trust_recommend":
            task_desc = arguments.get("task_description")
            if not task_desc:
                return _make_error(
                    req_id, INVALID_PARAMS, "task_description is required"
                )
            result = scorer.recommend(task_desc)

        else:
            return _make_error(req_id, METHOD_NOT_FOUND, f"Unknown tool: {tool_name}")

        return _make_response(req_id, {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(result, indent=2, default=str),
                }
            ],
        })

    except Exception as exc:
        logger.exception("Tool execution error: %s", exc)
        return _make_error(req_id, INTERNAL_ERROR, str(exc))


def run_stdio_server() -> None:
    """Run the MCP server on stdin/stdout (stdio transport)."""
    scorer = TrustScorer()

    # MCP stdio uses newline-delimited JSON
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue

        try:
            request = json.loads(line)
        except json.JSONDecodeError as exc:
            response = _make_error(None, PARSE_ERROR, f"Parse error: {exc}")
            sys.stdout.write(json.dumps(response) + "\n")
            sys.stdout.flush()
            continue

        response = handle_request(request, scorer)
        if response is not None:
            sys.stdout.write(json.dumps(response) + "\n")
            sys.stdout.flush()


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main() -> None:
    """Entry point: run as MCP stdio server, or --test for quick validation."""
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        _run_self_test()
        return
    if len(sys.argv) > 1 and sys.argv[1] == "--score":
        agent = sys.argv[2] if len(sys.argv) > 2 else "gemini"
        scorer = TrustScorer()
        result = scorer.score(agent)
        print(json.dumps(result, indent=2, default=str))
        return
    if len(sys.argv) > 1 and sys.argv[1] == "--compare":
        scorer = TrustScorer()
        result = scorer.compare()
        print(json.dumps(result, indent=2, default=str))
        return
    if len(sys.argv) > 1 and sys.argv[1] == "--recommend":
        task = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else "code review"
        scorer = TrustScorer()
        result = scorer.recommend(task)
        print(json.dumps(result, indent=2, default=str))
        return

    run_stdio_server()


def _run_self_test() -> None:
    """Quick self-test: validate scoring, JSON-RPC, and bus reading."""
    import tempfile

    print("=== MCP Trust Server Self-Test ===\n")

    # --- Test 1: Bus reading ---
    print("1. Bus reading...")
    bus_data = (
        "timestamp\tfrom\tto\ttype\tmessage\n"
        "2026-03-20T10:00:00Z\tgemini\tall\tSTATUS\tTest message\n"
        "2026-03-20T10:01:00Z\tgemini\tall\tSITREP\tAnother one\n"
        "2026-03-20T10:02:00Z\tgemini-4\tall\tSTATUS\tBad identity\n"
        "2026-03-21T10:00:00Z\tkimi-1\tall\tSTATUS\tKimi works\n"
        "2026-03-21T10:01:00Z\tkimi-3\tall\tSTATUS\tRetired identity\n"
        "2026-03-22T10:00:00Z\tclaude-code (Terminal)\tall\tDECISION\tLead decision\n"
        "2026-03-22T10:01:00Z\tcodex\tall\tACK\tAcknowledged\n"
    )
    with tempfile.NamedTemporaryFile(mode="w", suffix=".tsv", delete=False) as f:
        f.write(bus_data)
        tmp_path = f.name

    try:
        rows = read_bus(tmp_path)
        assert len(rows) == 7, f"Expected 7 rows, got {len(rows)}"
        print(f"   OK: Read {len(rows)} bus messages")

        # --- Test 2: Agent classification ---
        print("2. Agent classification...")
        assert _classify_agent_family("gemini") == "gemini"
        assert _classify_agent_family("gemini-4") == "gemini"
        assert _classify_agent_family("kimi-1") == "kimi"
        assert _classify_agent_family("kimi-3") == "kimi"
        assert _classify_agent_family("claude-code (Terminal)") == "claude-code"
        assert _classify_agent_family("codex (VS Code)") == "codex"
        print("   OK: All classifications correct")

        # --- Test 3: Trust scoring ---
        print("3. Trust scoring...")
        scorer = TrustScorer(bus_path=tmp_path)

        gemini_score = scorer.score("gemini")
        assert gemini_score["tier"] == TIER_PROBATION, (
            f"Gemini should be PROBATION, got {gemini_score['tier']}"
        )
        assert gemini_score["score"] <= 60.0, (
            f"Gemini score should be capped at 60, got {gemini_score['score']}"
        )
        assert gemini_score["on_probation"] is True
        print(f"   OK: Gemini score={gemini_score['score']}, tier={gemini_score['tier']}")

        claude_score = scorer.score("claude-code")
        assert claude_score["tier"] == TIER_TRUSTED, (
            f"Claude should be TRUSTED, got {claude_score['tier']}"
        )
        print(f"   OK: Claude score={claude_score['score']}, tier={claude_score['tier']}")

        kimi_score = scorer.score("kimi")
        print(f"   OK: Kimi score={kimi_score['score']}, tier={kimi_score['tier']}")

        # --- Test 4: Compare ---
        print("4. Trust compare...")
        comparison = scorer.compare()
        assert comparison["total_agents"] >= 4
        assert comparison["agents"][0]["score"] >= comparison["agents"][-1]["score"]
        print(f"   OK: {comparison['total_agents']} agents ranked")

        # --- Test 5: Recommend ---
        print("5. Trust recommend...")
        rec = scorer.recommend("security audit and code review")
        assert rec["recommended"] is not None
        print(f"   OK: Recommended '{rec['recommended']['agent']}' "
              f"(composite={rec['recommended']['composite_score']})")

        # --- Test 6: History ---
        print("6. Trust history...")
        hist = scorer.history("gemini", days=30)
        assert hist["agent"] == "gemini"
        assert len(hist["notable_events"]) > 0
        print(f"   OK: {len(hist['notable_events'])} notable events, "
              f"{hist['active_days']} active days")

        # --- Test 7: JSON-RPC protocol ---
        print("7. JSON-RPC protocol...")

        # initialize
        resp = handle_request({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}, scorer)
        assert resp["result"]["protocolVersion"] == PROTOCOL_VERSION
        print("   OK: initialize")

        # tools/list
        resp = handle_request({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}, scorer)
        assert len(resp["result"]["tools"]) == 4
        print(f"   OK: tools/list ({len(resp['result']['tools'])} tools)")

        # tools/call trust_score
        resp = handle_request({
            "jsonrpc": "2.0", "id": 3, "method": "tools/call",
            "params": {"name": "trust_score", "arguments": {"agent_name": "gemini"}},
        }, scorer)
        assert "content" in resp["result"]
        content = json.loads(resp["result"]["content"][0]["text"])
        assert content["tier"] == TIER_PROBATION
        print("   OK: tools/call trust_score")

        # tools/call trust_compare
        resp = handle_request({
            "jsonrpc": "2.0", "id": 4, "method": "tools/call",
            "params": {"name": "trust_compare", "arguments": {}},
        }, scorer)
        assert "content" in resp["result"]
        print("   OK: tools/call trust_compare")

        # tools/call trust_recommend
        resp = handle_request({
            "jsonrpc": "2.0", "id": 5, "method": "tools/call",
            "params": {"name": "trust_recommend", "arguments": {"task_description": "research AI governance"}},
        }, scorer)
        assert "content" in resp["result"]
        print("   OK: tools/call trust_recommend")

        # Error: missing param
        resp = handle_request({
            "jsonrpc": "2.0", "id": 6, "method": "tools/call",
            "params": {"name": "trust_score", "arguments": {}},
        }, scorer)
        assert "error" in resp
        assert resp["error"]["code"] == INVALID_PARAMS
        print("   OK: error handling (missing param)")

        # Error: unknown method
        resp = handle_request({"jsonrpc": "2.0", "id": 7, "method": "foo/bar", "params": {}}, scorer)
        assert "error" in resp
        assert resp["error"]["code"] == METHOD_NOT_FOUND
        print("   OK: error handling (unknown method)")

        # Notification (no response)
        resp = handle_request({
            "jsonrpc": "2.0", "method": "notifications/initialized", "params": {},
        }, scorer)
        assert resp is None
        print("   OK: notification handling")

        print("\n=== All 7 tests passed ===")

    finally:
        os.unlink(tmp_path)


if __name__ == "__main__":  # pragma: no cover
    main()
