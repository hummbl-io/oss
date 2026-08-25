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

"""Tests for mcp_physical.py — KinematicGovernor and pHRISafetyMonitor MCP server."""

import importlib
import json
import subprocess
import sys
from pathlib import Path


MCP_PATH = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(MCP_PATH))

import mcp_physical as mcp  # noqa: E402


def fresh_module():
    import mcp_physical
    importlib.reload(mcp_physical)
    return mcp_physical


# ---------------------------------------------------------------------------
# KinematicGovernor tools
# ---------------------------------------------------------------------------

class TestKinematicCheckMotion:
    def test_within_limits(self):
        result = mcp.handle_tool("kinematic_check_motion", {
            "velocity": 0.5,
            "force": 20.0,
            "jerk": 2.0,
        })
        assert result["allowed"] is True
        assert "Within kinematic limits" in result["reason"]

    def test_velocity_exceeded(self):
        result = mcp.handle_tool("kinematic_check_motion", {"velocity": 999.0})
        assert result["allowed"] is False
        assert "Velocity" in result["reason"]

    def test_force_exceeded(self):
        result = mcp.handle_tool("kinematic_check_motion", {"force": 10000.0})
        assert result["allowed"] is False
        assert "Force" in result["reason"]

    def test_jerk_exceeded(self):
        result = mcp.handle_tool("kinematic_check_motion", {"jerk": 9999.0})
        assert result["allowed"] is False
        assert "Jerk" in result["reason"]

    def test_velocity_at_limit(self):
        # Exactly at limit should be allowed
        result = mcp.handle_tool("kinematic_check_motion", {"velocity": 1.0})
        assert result["allowed"] is True

    def test_velocity_just_over_limit(self):
        result = mcp.handle_tool("kinematic_check_motion", {"velocity": 1.001})
        assert result["allowed"] is False

    def test_single_param_velocity(self):
        result = mcp.handle_tool("kinematic_check_motion", {"velocity": 0.1})
        assert result["allowed"] is True

    def test_no_params(self):
        result = mcp.handle_tool("kinematic_check_motion", {})
        assert "error" in result

    def test_limits_returned(self):
        result = mcp.handle_tool("kinematic_check_motion", {"velocity": 0.5})
        assert "limits" in result
        assert result["limits"]["max_velocity"] == 1.0
        assert result["limits"]["max_force"] == 50.0


class TestKinematicGetLimits:
    def test_limits_structure(self):
        result = mcp.handle_tool("kinematic_get_limits", {})
        assert "max_velocity" in result
        assert "max_force" in result
        assert "max_jerk" in result
        assert "caution_scale" in result
        assert "caution_velocity" in result
        assert "emergency_velocity" in result

    def test_emergency_velocity_zero(self):
        result = mcp.handle_tool("kinematic_get_limits", {})
        assert result["emergency_velocity"] == 0.0

    def test_caution_velocity_scaled(self):
        result = mcp.handle_tool("kinematic_get_limits", {})
        expected = result["max_velocity"] * result["caution_scale"]
        assert abs(result["caution_velocity"] - expected) < 1e-9


class TestKinematicScaledVel:
    def test_normal_mode(self):
        result = mcp.handle_tool("kinematic_scaled_vel", {"mode": "normal"})
        assert result["effective_velocity"] == 1.0
        assert result["reduction_factor"] == 1.0

    def test_caution_mode(self):
        result = mcp.handle_tool("kinematic_scaled_vel", {"mode": "caution"})
        assert result["effective_velocity"] < 1.0
        assert result["effective_velocity"] > 0.0

    def test_emergency_mode(self):
        result = mcp.handle_tool("kinematic_scaled_vel", {"mode": "emergency"})
        assert result["effective_velocity"] == 0.0

    def test_unknown_mode(self):
        result = mcp.handle_tool("kinematic_scaled_vel", {"mode": "turbo"})
        assert "error" in result

    def test_missing_mode(self):
        # Default should work (normal is default)
        result = mcp.handle_tool("kinematic_scaled_vel", {})
        # "normal" is the default in the handler
        assert result["effective_velocity"] >= 0.0


# ---------------------------------------------------------------------------
# pHRISafetyMonitor tools
# ---------------------------------------------------------------------------

class TestPhriCheckSafety:
    def test_normal_safe_distance(self):
        result = mcp.handle_tool("phri_check_safety", {"distance": 2.0})
        assert result["mode"] == "normal"
        assert result["safe"] is True

    def test_caution_zone(self):
        result = mcp.handle_tool("phri_check_safety", {"distance": 0.3})
        assert result["mode"] == "caution"
        assert result["safe"] is False

    def test_critical_proximity(self):
        result = mcp.handle_tool("phri_check_safety", {"distance": 0.05})
        assert result["mode"] == "emergency"
        assert result["safe"] is False

    def test_collision(self):
        result = mcp.handle_tool("phri_check_safety", {"collision": True})
        assert result["mode"] == "emergency"

    def test_collision_overrides_safe_distance(self):
        result = mcp.handle_tool("phri_check_safety", {
            "distance": 5.0,
            "collision": True,
        })
        assert result["mode"] == "emergency"

    def test_no_input_is_normal(self):
        result = mcp.handle_tool("phri_check_safety", {})
        assert result["mode"] == "normal"

    def test_reason_present(self):
        result = mcp.handle_tool("phri_check_safety", {"distance": 0.3})
        assert "reason" in result
        assert len(result["reason"]) > 0


class TestPhriGetConfig:
    def test_config_structure(self):
        result = mcp.handle_tool("phri_get_config", {})
        assert "min_distance" in result
        assert "critical_distance" in result
        assert "modes" in result

    def test_critical_less_than_min(self):
        result = mcp.handle_tool("phri_get_config", {})
        assert result["critical_distance"] < result["min_distance"]

    def test_modes_present(self):
        result = mcp.handle_tool("phri_get_config", {})
        assert "normal" in result["modes"]
        assert "caution" in result["modes"]
        assert "emergency" in result["modes"]


class TestPhriBatchCheck:
    def test_batch_all_safe(self):
        result = mcp.handle_tool("phri_batch_check", {
            "readings": [
                {"distance": 2.0},
                {"distance": 3.0},
                {"distance": 1.5},
            ],
        })
        assert result["total"] == 3
        assert result["emergency_count"] == 0
        assert result["any_emergency"] is False

    def test_batch_mixed(self):
        result = mcp.handle_tool("phri_batch_check", {
            "readings": [
                {"distance": 2.0},          # normal
                {"distance": 0.3},           # caution
                {"collision": True},          # emergency
            ],
        })
        assert result["total"] == 3
        assert result["emergency_count"] == 1
        assert result["caution_count"] == 1
        assert result["safe_count"] == 1
        assert result["any_emergency"] is True

    def test_batch_empty(self):
        result = mcp.handle_tool("phri_batch_check", {"readings": []})
        assert "error" in result

    def test_batch_missing_readings(self):
        result = mcp.handle_tool("phri_batch_check", {})
        assert "error" in result

    def test_batch_results_per_reading(self):
        result = mcp.handle_tool("phri_batch_check", {
            "readings": [{"distance": 1.0}, {"distance": 0.05}],
        })
        assert len(result["results"]) == 2
        assert result["results"][0]["index"] == 0
        assert result["results"][1]["index"] == 1


# ---------------------------------------------------------------------------
# Protocol-level tests
# ---------------------------------------------------------------------------

class TestProtocol:
    def _call(self, req_obj):
        proc = subprocess.run(
            [sys.executable, str(MCP_PATH / "mcp_physical.py")],
            input=json.dumps(req_obj) + "\n",
            capture_output=True,
            text=True,
            timeout=10,
        )
        return json.loads(proc.stdout.strip().split("\n")[0])

    def test_initialize(self):
        resp = self._call({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}})
        assert resp["result"]["serverInfo"]["name"] == "hummbl-physical"
        assert resp["result"]["protocolVersion"] == "2024-11-05"

    def test_tools_list(self):
        resp = self._call({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})
        tools = {t["name"] for t in resp["result"]["tools"]}
        assert "kinematic_check_motion" in tools
        assert "phri_check_safety" in tools
        assert "phri_batch_check" in tools
        assert len(tools) == 6

    def test_tools_call_get_limits(self):
        resp = self._call({
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {"name": "kinematic_get_limits", "arguments": {}},
        })
        content = json.loads(resp["result"]["content"][0]["text"])
        assert "max_velocity" in content

    def test_tools_call_phri_config(self):
        resp = self._call({
            "jsonrpc": "2.0",
            "id": 4,
            "method": "tools/call",
            "params": {"name": "phri_get_config", "arguments": {}},
        })
        content = json.loads(resp["result"]["content"][0]["text"])
        assert "min_distance" in content

    def test_unknown_method(self):
        resp = self._call({"jsonrpc": "2.0", "id": 5, "method": "bad_method", "params": {}})
        assert "error" in resp
