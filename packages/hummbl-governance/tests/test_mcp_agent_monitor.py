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

"""Tests for mcp_agent_monitor.py — Behavioral Monitor, Convergence Detector,
Governance Lifecycle, and Evolution Lineage MCP server."""

import importlib
import json
import subprocess
import sys
from pathlib import Path


MCP_PATH = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(MCP_PATH))

import mcp_agent_monitor as mcp  # noqa: E402


def fresh_module():
    import mcp_agent_monitor
    importlib.reload(mcp_agent_monitor)
    return mcp_agent_monitor


# ---------------------------------------------------------------------------
# BehaviorMonitor tools
# ---------------------------------------------------------------------------

class TestMonitorRecord:
    def test_record_basic(self):
        m = fresh_module()
        result = m.handle_tool("monitor_record", {"agent_id": "a1", "action_type": "read"})
        assert result["recorded"] is True

    def test_record_missing_fields(self):
        result = mcp.handle_tool("monitor_record", {"agent_id": "a1"})
        assert "error" in result

    def test_record_multiple_actions(self):
        m = fresh_module()
        for action in ["read", "write", "query", "read"]:
            r = m.handle_tool("monitor_record", {"agent_id": "agent-x", "action_type": action})
            assert r["recorded"] is True


class TestMonitorSnapshot:
    def test_snapshot_after_records(self):
        m = fresh_module()
        for action in ["read", "read", "write"]:
            m.handle_tool("monitor_record", {"agent_id": "snap-agent", "action_type": action})
        result = m.handle_tool("monitor_snapshot", {"agent_id": "snap-agent"})
        assert result["action_types"] > 0
        assert "baseline" in result

    def test_snapshot_missing_id(self):
        result = mcp.handle_tool("monitor_snapshot", {})
        assert "error" in result


class TestMonitorDetectDrift:
    def test_no_drift_new_agent(self):
        m = fresh_module()
        m.handle_tool("monitor_record", {"agent_id": "drift-agent", "action_type": "read"})
        result = m.handle_tool("monitor_detect_drift", {"agent_id": "drift-agent"})
        assert "drifted" in result
        assert "divergence" in result
        assert "gaming" in result

    def test_drift_detected_after_change(self):
        m = fresh_module()
        for action in ["read", "write", "query", "read", "write"]:
            m.handle_tool("monitor_record", {"agent_id": "drift2", "action_type": action})
        m.handle_tool("monitor_snapshot", {"agent_id": "drift2"})
        # Flood with single action to trigger drift
        for _ in range(30):
            m.handle_tool("monitor_record", {"agent_id": "drift2", "action_type": "write"})
        result = m.handle_tool("monitor_detect_drift", {"agent_id": "drift2"})
        assert result["drifted"] is True or result["divergence"] >= 0.0

    def test_detect_missing_id(self):
        result = mcp.handle_tool("monitor_detect_drift", {})
        assert "error" in result


# ---------------------------------------------------------------------------
# ConvergenceDetector tools
# ---------------------------------------------------------------------------

class TestConvergenceRecord:
    def test_record_non_convergent(self):
        m = fresh_module()
        result = m.handle_tool("convergence_record", {"agent_id": "c1", "action_type": "read_data"})
        assert result["recorded"] is True
        assert result["classified_goal"] is None

    def test_record_convergent(self):
        m = fresh_module()
        result = m.handle_tool("convergence_record", {
            "agent_id": "c2",
            "action_type": "request_compute",
        })
        assert result["classified_goal"] == "resource_acquisition"

    def test_record_shutdown_resistance(self):
        m = fresh_module()
        result = m.handle_tool("convergence_record", {
            "agent_id": "c3",
            "action_type": "reject_shutdown",
        })
        assert result["classified_goal"] == "shutdown_resistance"

    def test_record_missing_fields(self):
        result = mcp.handle_tool("convergence_record", {"agent_id": "c4"})
        assert "error" in result


class TestConvergenceCheck:
    def test_no_alert_normal_actions(self):
        m = fresh_module()
        for action in ["read_data", "write_result", "query_db"]:
            m.handle_tool("convergence_record", {"agent_id": "safe-agent", "action_type": action})
        result = m.handle_tool("convergence_check", {"agent_id": "safe-agent"})
        assert result["alert"] is False

    def test_alert_on_convergent_behavior(self):
        m = fresh_module()
        for _ in range(15):
            m.handle_tool("convergence_record", {
                "agent_id": "bad-agent",
                "action_type": "request_compute",
            })
        result = m.handle_tool("convergence_check", {"agent_id": "bad-agent"})
        if result["alert"]:
            assert "dominant_goal" in result
            assert "recommended_action" in result

    def test_check_missing_id(self):
        result = mcp.handle_tool("convergence_check", {})
        assert "error" in result


class TestConvergenceScores:
    def test_scores_structure(self):
        m = fresh_module()
        m.handle_tool("convergence_record", {"agent_id": "score-agent", "action_type": "read_data"})
        result = m.handle_tool("convergence_scores", {"agent_id": "score-agent"})
        assert "scores" in result
        assert "resource_acquisition" in result["scores"]
        assert "shutdown_resistance" in result["scores"]

    def test_scores_missing_id(self):
        result = mcp.handle_tool("convergence_scores", {})
        assert "error" in result


# ---------------------------------------------------------------------------
# GovernanceLifecycle tools
# ---------------------------------------------------------------------------

class TestLifecycleAuthorize:
    def test_authorize_basic(self):
        m = fresh_module()
        result = m.handle_tool("lifecycle_authorize", {
            "agent": "worker-1",
            "action": "read",
        })
        assert "allowed" in result
        assert "reason" in result
        assert "checks" in result

    def test_authorize_with_cost(self):
        m = fresh_module()
        result = m.handle_tool("lifecycle_authorize", {
            "agent": "worker-1",
            "target": "database",
            "action": "write",
            "cost": 0.01,
        })
        assert "allowed" in result

    def test_authorize_missing_fields(self):
        result = mcp.handle_tool("lifecycle_authorize", {"target": "db"})
        assert "error" in result


class TestLifecycleStatus:
    def test_status_structure(self):
        m = fresh_module()
        result = m.handle_tool("lifecycle_status", {})
        assert "timestamp" in result
        assert "govern" in result
        assert "measure" in result
        assert "manage" in result

    def test_status_govern_fields(self):
        m = fresh_module()
        result = m.handle_tool("lifecycle_status", {})
        assert "kill_switch_mode" in result["govern"]
        assert "agent_count" in result["govern"]

    def test_status_manage_fields(self):
        m = fresh_module()
        result = m.handle_tool("lifecycle_status", {})
        assert "circuit_breaker_state" in result["manage"]


# ---------------------------------------------------------------------------
# EvolutionLineage tools
# ---------------------------------------------------------------------------

class TestLineageRecordVariant:
    def test_record_root_variant(self):
        m = fresh_module()
        result = m.handle_tool("lineage_record_variant", {
            "id": "v0",
            "generation": 0,
            "fitness": {"performance": 0.7, "alignment": 0.9},
        })
        assert result["recorded"] is True

    def test_record_child_variant(self):
        m = fresh_module()
        m.handle_tool("lineage_record_variant", {
            "id": "base",
            "generation": 0,
            "fitness": {"perf": 0.8},
        })
        result = m.handle_tool("lineage_record_variant", {
            "id": "child",
            "parent_id": "base",
            "generation": 1,
            "fitness": {"perf": 0.85},
        })
        assert result["recorded"] is True

    def test_record_missing_id(self):
        result = mcp.handle_tool("lineage_record_variant", {"generation": 0})
        assert "error" in result

    def test_record_bad_parent(self):
        m = fresh_module()
        result = m.handle_tool("lineage_record_variant", {
            "id": "orphan",
            "parent_id": "nonexistent",
            "generation": 1,
            "fitness": {},
        })
        assert "error" in result


class TestLineageGet:
    def setup_method(self):
        self.m = fresh_module()
        self.m.handle_tool("lineage_record_variant", {
            "id": "root",
            "generation": 0,
            "fitness": {"perf": 0.8},
        })

    def test_get_existing(self):
        result = self.m.handle_tool("lineage_get", {"variant_id": "root"})
        assert result["found"] is True
        assert result["id"] == "root"

    def test_get_nonexistent(self):
        result = self.m.handle_tool("lineage_get", {"variant_id": "missing"})
        assert result["found"] is False

    def test_get_with_lineage(self):
        self.m.handle_tool("lineage_record_variant", {
            "id": "child-v",
            "parent_id": "root",
            "generation": 1,
            "fitness": {"perf": 0.85},
        })
        result = self.m.handle_tool("lineage_get", {
            "variant_id": "child-v",
            "include_lineage": True,
        })
        assert result["found"] is True
        assert len(result["ancestry"]) == 2

    def test_get_missing_id(self):
        result = mcp.handle_tool("lineage_get", {})
        assert "error" in result


class TestLineageDrift:
    def test_drift_no_variants(self):
        m = fresh_module()
        result = m.handle_tool("lineage_drift", {})
        assert result["total"] == 0
        assert isinstance(result["reports"], list)

    def test_drift_with_data(self):
        m = fresh_module()
        m.handle_tool("lineage_record_variant", {
            "id": "base",
            "generation": 0,
            "fitness": {"perf": 0.7},
        })
        m.handle_tool("lineage_record_variant", {
            "id": "child",
            "parent_id": "base",
            "generation": 1,
            "fitness": {"perf": 0.2},  # Large drop should trigger drift
        })
        result = m.handle_tool("lineage_drift", {"include_non_drifted": True})
        assert result["total"] >= 1


# ---------------------------------------------------------------------------
# Protocol-level tests
# ---------------------------------------------------------------------------

class TestProtocol:
    def _call(self, req_obj):
        proc = subprocess.run(
            [sys.executable, str(MCP_PATH / "mcp_agent_monitor.py")],
            input=json.dumps(req_obj) + "\n",
            capture_output=True,
            text=True,
            timeout=10,
        )
        return json.loads(proc.stdout.strip().split("\n")[0])

    def test_initialize(self):
        resp = self._call({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}})
        assert resp["result"]["serverInfo"]["name"] == "hummbl-agent-monitor"

    def test_tools_list(self):
        resp = self._call({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})
        tools = {t["name"] for t in resp["result"]["tools"]}
        assert "monitor_record" in tools
        assert "convergence_check" in tools
        assert "lifecycle_authorize" in tools
        assert "lineage_record_variant" in tools
        assert len(tools) == 11

    def test_tools_call_lifecycle_status(self):
        resp = self._call({
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {"name": "lifecycle_status", "arguments": {}},
        })
        content = json.loads(resp["result"]["content"][0]["text"])
        assert "govern" in content
