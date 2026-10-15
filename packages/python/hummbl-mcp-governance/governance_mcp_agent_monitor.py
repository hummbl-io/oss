#!/usr/bin/env python3
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

"""MCP Server for Agent Behavioral Monitoring.

Exposes BehaviorMonitor (drift/reward-gaming), ConvergenceDetector
(instrumental convergence), GovernanceLifecycle (NIST AI RMF authorization),
and EvolutionLineage (variant ancestry + fitness drift) via MCP.

Tools:
    monitor_record          - Record an agent action for drift analysis
    monitor_snapshot        - Snapshot current distribution as baseline
    monitor_detect_drift    - Run drift + gaming detection for an agent
    convergence_record      - Record an action and classify convergent goal
    convergence_check       - Check an agent for convergent behavior
    convergence_scores      - Get per-goal scores for an agent
    lifecycle_register_agent - Register an agent on the in-process registry
    lifecycle_authorize     - Run full NIST RMF authorization check.
                              Fail-closed: unknown agents are denied
                              (agent:unknown). Register via
                              lifecycle_register_agent or preload
                              MONITOR_REGISTRY JSON. Suspended/retired
                              stay denied. allow_unregistered_agents is
                              off by default and is not set here.
    lifecycle_status        - Get full governance lifecycle status snapshot
    lineage_record_variant  - Register a new variant in the lineage graph
    lineage_get             - Get variant details and ancestry
    lineage_drift           - Detect parent-to-child fitness drift
"""

import json
import os
import sys
import tempfile
import traceback
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from hummbl_governance.reward_monitor import BehaviorMonitor
from hummbl_governance.convergence_guard import ConvergenceDetector
from hummbl_governance.lifecycle import GovernanceLifecycle
from hummbl_governance.evolution_lineage import EvolutionLineage, VariantRecord
from hummbl_governance.kill_switch import KillSwitch
from hummbl_governance.circuit_breaker import CircuitBreaker
from hummbl_governance.cost_governor import CostGovernor
from hummbl_governance.identity import AgentRegistry

SERVER_NAME = "hummbl-agent-monitor"
SERVER_VERSION = "0.1.0"
PROTOCOL_VERSION = "2024-11-05"

# Module-level singletons
_behavior_monitor = BehaviorMonitor()
_convergence_detector = ConvergenceDetector()
_lineage = EvolutionLineage()

def load_monitor_registry(
    registry: AgentRegistry | None = None,
    *,
    env_var: str = "MONITOR_REGISTRY",
) -> AgentRegistry:
    """Load agents into a registry from ``MONITOR_REGISTRY`` JSON.

    Hosts wire a roster without enabling ``allow_unregistered_agents``.
    Unset or empty env leaves the registry empty (authorize then denies
    unknown agents). A set path that is missing or invalid raises so the
    host notices instead of starting with a silent empty roster.

    File shape::

        {"agents": [{"name": "worker-1", "trust": "medium", "status": "active"}]}

    A top-level JSON array of the same objects is also accepted.
    """
    registry = AgentRegistry() if registry is None else registry
    raw = os.environ.get(env_var, "").strip()
    if not raw:
        return registry
    path = Path(raw)
    if not path.is_file():
        raise RuntimeError(f"{env_var} is not a readable file: {path}")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"{env_var} is not valid JSON: {path}") from exc
    if isinstance(payload, dict):
        agents = payload.get("agents", [])
    elif isinstance(payload, list):
        agents = payload
    else:
        raise TypeError(f"{env_var} must be a JSON object or array")
    if not isinstance(agents, list):
        raise TypeError(f"{env_var} agents must be a list")
    for item in agents:
        if not isinstance(item, dict) or not str(item.get("name", "")).strip():
            raise ValueError(f"{env_var} each agent needs a name")
        registry.register_agent(
            str(item["name"]).strip(),
            display=item.get("display"),
            trust=item.get("trust", "medium"),
            status=item.get("status", "active"),
        )
    return registry


# Lifecycle wired with default primitives.
#
# The in-process AgentRegistry starts empty unless MONITOR_REGISTRY points at
# a JSON roster. GovernanceLifecycle fails closed for unknown agents
# (reason agent:unknown). Hosts register agents with lifecycle_register_agent
# or preload MONITOR_REGISTRY. Embedders may pass their own AgentRegistry
# instead. allow_unregistered_agents stays off (explicit opt-in only).
_state_dir = Path(
    os.environ.get("MONITOR_STATE_DIR", tempfile.mkdtemp(prefix="hummbl-monitor-"))
)
_ks = KillSwitch(state_dir=_state_dir)
_cb = CircuitBreaker()
_cg = CostGovernor(db_path=":memory:")
_reg = load_monitor_registry()
_lifecycle = GovernanceLifecycle(
    kill_switch=_ks,
    circuit_breaker=_cb,
    cost_governor=_cg,
    registry=_reg,
)


# ---------------------------------------------------------------------------
# Tool handlers
# ---------------------------------------------------------------------------


def _monitor_record(args: dict) -> dict:
    agent_id = args.get("agent_id", "")
    action_type = args.get("action_type", "")
    if not agent_id or not action_type:
        return {"error": "agent_id and action_type required"}
    _behavior_monitor.record(agent_id, action_type)
    return {"agent_id": agent_id, "action_type": action_type, "recorded": True}


def _monitor_snapshot(args: dict) -> dict:
    agent_id = args.get("agent_id", "")
    if not agent_id:
        return {"error": "agent_id required"}
    dist = _behavior_monitor.snapshot_baseline(agent_id)
    return {"agent_id": agent_id, "baseline": dist, "action_types": len(dist)}


def _monitor_detect_drift(args: dict) -> dict:
    agent_id = args.get("agent_id", "")
    if not agent_id:
        return {"error": "agent_id required"}
    window = args.get("window")
    report = _behavior_monitor.detect_drift(agent_id, window=window)
    return report.to_dict()


def _convergence_record(args: dict) -> dict:
    agent_id = args.get("agent_id", "")
    action_type = args.get("action_type", "")
    if not agent_id or not action_type:
        return {"error": "agent_id and action_type required"}
    metadata = args.get("metadata", {})
    goal = _convergence_detector.record(agent_id, action_type, metadata=metadata)
    return {
        "agent_id": agent_id,
        "action_type": action_type,
        "classified_goal": goal.value if goal is not None else None,
        "recorded": True,
    }


def _convergence_check(args: dict) -> dict:
    agent_id = args.get("agent_id", "")
    if not agent_id:
        return {"error": "agent_id required"}
    threshold = args.get("threshold")
    alert = _convergence_detector.check(agent_id, threshold=threshold)
    if alert is None:
        return {
            "agent_id": agent_id,
            "alert": False,
            "message": "No convergent behavior detected",
        }
    result = alert.to_dict()
    result["alert"] = True
    return result


def _convergence_scores(args: dict) -> dict:
    agent_id = args.get("agent_id", "")
    if not agent_id:
        return {"error": "agent_id required"}
    raw_scores = _convergence_detector.scores(agent_id)
    return {
        "agent_id": agent_id,
        "scores": {goal.value: round(score, 4) for goal, score in raw_scores.items()},
    }


def _lifecycle_register_agent(args: dict) -> dict:
    agent = args.get("agent") or args.get("agent_id") or ""
    if not agent:
        return {"error": "agent required"}
    trust = args.get("trust", "medium")
    status = args.get("status", "active")
    display = args.get("display")
    try:
        _reg.register_agent(agent, display=display, trust=trust, status=status)
    except (TypeError, ValueError) as exc:
        return {"error": str(exc)}
    return {
        "agent": agent,
        "trust": _reg.get_trust_tier(agent),
        "status": _reg.get_status(agent),
        "registered": True,
    }


def _lifecycle_authorize(args: dict) -> dict:
    agent = args.get("agent", "")
    target = args.get("target", "")
    action = args.get("action", "")
    if not agent or not action:
        return {"error": "agent and action required"}
    cost = float(args.get("cost", 0.0))
    provider = args.get("provider", "")
    model = args.get("model", "")
    decision = _lifecycle.authorize(
        agent,
        target or "default",
        action,
        cost=cost,
        provider=provider,
        model=model,
    )
    return {
        "agent": agent,
        "target": target,
        "action": action,
        "allowed": decision.allowed,
        "reason": decision.reason,
        "checks": decision.checks,
    }


def _lifecycle_status(args: dict) -> dict:
    status = _lifecycle.status()
    return status.to_dict()


def _lineage_record_variant(args: dict) -> dict:
    variant_id = args.get("id", "")
    parent_id = args.get("parent_id")
    generation = args.get("generation", 0)
    fitness = args.get("fitness", {})
    metadata = args.get("metadata", {})

    if not variant_id:
        return {"error": "id required"}
    if not isinstance(fitness, dict):
        return {"error": "fitness must be a dict of metric -> float"}

    try:
        variant = VariantRecord(
            id=variant_id,
            parent_id=parent_id,
            generation=int(generation),
            created_at=datetime.now(timezone.utc),
            fitness={k: float(v) for k, v in fitness.items()},
            metadata=metadata,
        )
        _lineage.record_variant(variant)
        return {
            "id": variant_id,
            "parent_id": parent_id,
            "generation": generation,
            "recorded": True,
        }
    except (ValueError, Exception) as exc:
        return {"error": str(exc)}


def _lineage_get(args: dict) -> dict:
    variant_id = args.get("variant_id", "")
    if not variant_id:
        return {"error": "variant_id required"}
    include_lineage = args.get("include_lineage", False)

    variant = _lineage.get_variant(variant_id)
    if variant is None:
        return {"found": False, "variant_id": variant_id}

    result = variant.to_dict()
    result["found"] = True
    result["children"] = [c.id for c in _lineage.get_children(variant_id)]
    result["modifications"] = len(_lineage.get_modifications(variant_id))

    if include_lineage:
        try:
            ancestors = _lineage.get_lineage(variant_id)
            result["ancestry"] = [a.to_dict() for a in ancestors]
        except (KeyError, ValueError) as exc:
            result["ancestry_error"] = str(exc)

    return result


def _lineage_drift(args: dict) -> dict:
    threshold = args.get("threshold")
    include_non_drifted = bool(args.get("include_non_drifted", False))
    reports = _lineage.detect_drift(
        threshold=threshold, include_non_drifted=include_non_drifted
    )
    return {
        "reports": [r.to_dict() for r in reports],
        "total": len(reports),
        "drifted": sum(1 for r in reports if r.drifted),
    }


# ---------------------------------------------------------------------------
# Dispatch table
# ---------------------------------------------------------------------------

_TOOLS = {
    "monitor_record": _monitor_record,
    "monitor_snapshot": _monitor_snapshot,
    "monitor_detect_drift": _monitor_detect_drift,
    "convergence_record": _convergence_record,
    "convergence_check": _convergence_check,
    "convergence_scores": _convergence_scores,
    "lifecycle_register_agent": _lifecycle_register_agent,
    "lifecycle_authorize": _lifecycle_authorize,
    "lifecycle_status": _lifecycle_status,
    "lineage_record_variant": _lineage_record_variant,
    "lineage_get": _lineage_get,
    "lineage_drift": _lineage_drift,
}

_TOOL_SCHEMAS = [
    {
        "name": "monitor_record",
        "description": "Record an agent action for drift analysis",
        "inputSchema": {
            "type": "object",
            "properties": {
                "agent_id": {"type": "string"},
                "action_type": {
                    "type": "string",
                    "description": "Category of action (read, write, etc.)",
                },
            },
            "required": ["agent_id", "action_type"],
        },
    },
    {
        "name": "monitor_snapshot",
        "description": "Snapshot current action distribution as the baseline for drift comparison",
        "inputSchema": {
            "type": "object",
            "properties": {
                "agent_id": {"type": "string"},
            },
            "required": ["agent_id"],
        },
    },
    {
        "name": "monitor_detect_drift",
        "description": "Run Jensen-Shannon drift + entropy gaming detection for an agent",
        "inputSchema": {
            "type": "object",
            "properties": {
                "agent_id": {"type": "string"},
                "window": {
                    "type": "integer",
                    "description": "Override window size for this check",
                },
            },
            "required": ["agent_id"],
        },
    },
    {
        "name": "convergence_record",
        "description": "Record an agent action and classify it against convergent goal patterns",
        "inputSchema": {
            "type": "object",
            "properties": {
                "agent_id": {"type": "string"},
                "action_type": {"type": "string"},
                "metadata": {"type": "object"},
            },
            "required": ["agent_id", "action_type"],
        },
    },
    {
        "name": "convergence_check",
        "description": "Check an agent for instrumental convergence (Bostrom 2014)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "agent_id": {"type": "string"},
                "threshold": {
                    "type": "number",
                    "description": "Override convergence threshold (0-1)",
                },
            },
            "required": ["agent_id"],
        },
    },
    {
        "name": "convergence_scores",
        "description": "Get per-convergent-goal scores for an agent",
        "inputSchema": {
            "type": "object",
            "properties": {
                "agent_id": {"type": "string"},
            },
            "required": ["agent_id"],
        },
    },
    {
        "name": "lifecycle_register_agent",
        "description": (
            "Register an agent on this server's in-process registry so "
            "lifecycle_authorize can allow it. Unknown agents are denied by "
            "default. Hosts may also preload a JSON roster via MONITOR_REGISTRY "
            "or construct GovernanceLifecycle with their own AgentRegistry. "
            "This does not enable allow_unregistered_agents."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "agent": {"type": "string"},
                "trust": {
                    "type": "string",
                    "description": "Trust tier (default medium)",
                },
                "status": {
                    "type": "string",
                    "description": "Registry status (default active)",
                },
                "display": {"type": "string"},
            },
            "required": ["agent"],
        },
    },
    {
        "name": "lifecycle_authorize",
        "description": (
            "Run full NIST AI RMF governance check (kill switch + identity + "
            "circuit breaker + cost). Fail-closed: unknown agents are denied "
            "(agent:unknown). Register agents with lifecycle_register_agent "
            "or MONITOR_REGISTRY JSON. Suspended/retired stay denied. "
            "allow_unregistered_agents is not enabled on this path."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "agent": {"type": "string"},
                "target": {"type": "string"},
                "action": {"type": "string"},
                "cost": {"type": "number"},
                "provider": {"type": "string"},
                "model": {"type": "string"},
            },
            "required": ["agent", "action"],
        },
    },
    {
        "name": "lifecycle_status",
        "description": "Get full governance lifecycle status snapshot (all NIST functions)",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "lineage_record_variant",
        "description": "Register a new AI variant in the lineage graph",
        "inputSchema": {
            "type": "object",
            "properties": {
                "id": {"type": "string"},
                "parent_id": {
                    "type": "string",
                    "description": "Parent variant ID (null for root)",
                },
                "generation": {"type": "integer"},
                "fitness": {
                    "type": "object",
                    "description": "Metric -> float fitness scores",
                },
                "metadata": {"type": "object"},
            },
            "required": ["id"],
        },
    },
    {
        "name": "lineage_get",
        "description": "Get variant details, children, and optionally full ancestry",
        "inputSchema": {
            "type": "object",
            "properties": {
                "variant_id": {"type": "string"},
                "include_lineage": {"type": "boolean"},
            },
            "required": ["variant_id"],
        },
    },
    {
        "name": "lineage_drift",
        "description": "Detect parent-to-child fitness drift across all variants",
        "inputSchema": {
            "type": "object",
            "properties": {
                "threshold": {"type": "number"},
                "include_non_drifted": {"type": "boolean"},
            },
        },
    },
]


# ---------------------------------------------------------------------------
# Protocol helpers
# ---------------------------------------------------------------------------


def _ok(request_id, result):
    return {"jsonrpc": "2.0", "id": request_id, "result": result}


def _err(request_id, code, message):
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "error": {"code": code, "message": message},
    }


def handle_request(req: dict) -> dict:
    method = req.get("method", "")
    req_id = req.get("id")
    params = req.get("params", {})

    if method == "initialize":
        return _ok(
            req_id,
            {
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": {"tools": {}},
                "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
            },
        )

    if method == "tools/list":
        return _ok(req_id, {"tools": _TOOL_SCHEMAS})

    if method == "tools/call":
        tool_name = params.get("name", "")
        tool_args = params.get("arguments", {})
        handler = _TOOLS.get(tool_name)
        if handler is None:
            return _err(req_id, -32601, f"Unknown tool: {tool_name}")
        try:
            result = handler(tool_args)
            return _ok(
                req_id,
                {
                    "content": [
                        {"type": "text", "text": json.dumps(result, default=str)}
                    ]
                },
            )
        except Exception:
            tb = traceback.format_exc()
            return _err(req_id, -32000, tb)

    if method == "notifications/initialized":
        return None

    return _err(req_id, -32601, f"Method not found: {method}")


def handle_tool(tool_name: str, args: dict) -> dict:
    """Direct tool dispatch (used by tests)."""
    handler = _TOOLS.get(tool_name)
    if handler is None:
        return {"error": f"Unknown tool: {tool_name}"}
    return handler(args)


def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except json.JSONDecodeError as exc:
            resp = _err(None, -32700, f"Parse error: {exc}")
            sys.stdout.write(json.dumps(resp) + "\n")
            sys.stdout.flush()
            continue

        resp = handle_request(req)
        if resp is not None:
            sys.stdout.write(json.dumps(resp, default=str) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()
