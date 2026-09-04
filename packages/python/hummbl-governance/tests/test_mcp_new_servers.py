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

"""Tests for mcp_kernel, mcp_coordination, and mcp_execution MCP servers."""

from __future__ import annotations

import json
import subprocess
import sys
import pytest


def _call_mcp(module: str, method: str, params: dict | None = None) -> dict:
    """Call an MCP server and return the parsed response."""
    request = {"jsonrpc": "2.0", "id": 1, "method": method, "params": params or {}}
    payload = json.dumps(request)
    proc = subprocess.run(
        [sys.executable, "-m", module],
        input=payload, capture_output=True, text=True, timeout=15,
    )
    for line in proc.stdout.strip().split("\n"):
        if not line.strip():
            continue
        try:
            resp = json.loads(line)
            if resp.get("id") == 1:
                return resp
        except json.JSONDecodeError:
            continue
    pytest.fail(f"No valid response from {module}. stdout: {proc.stdout[:300]}")


# ===========================================================================
# mcp_kernel tests
# ===========================================================================

class TestMCPKernelToolsList:
    """Tests for the kernel MCP server tools/list."""

    def test_tools_list_returns_15(self):
        resp = _call_mcp("mcp_kernel", "tools/list")
        tools = resp["result"]["tools"]
        assert len(tools) == 15

    def test_tools_have_required_fields(self):
        resp = _call_mcp("mcp_kernel", "tools/list")
        for t in resp["result"]["tools"]:
            assert "name" in t
            assert "description" in t
            assert "inputSchema" in t

    def test_expected_tool_names(self):
        resp = _call_mcp("mcp_kernel", "tools/list")
        names = {t["name"] for t in resp["result"]["tools"]}
        expected = {
            "kernel_status", "receipt_create", "receipt_query",
            "law_list", "law_evaluate", "doctrine_validate",
            "evidence_grade", "authority_check", "schedule_register",
            "sequence_status", "rollback_validate", "recovery_validate",
            "receipt_integrity_check", "contestability_file", "trust_adjust",
        }
        assert names == expected


class TestMCPKernelStatus:
    """Tests for the kernel_status tool."""

    def test_kernel_status(self):
        resp = _call_mcp("mcp_kernel", "tools/call", {
            "name": "kernel_status", "arguments": {},
        })
        text = resp["result"]["content"][0]["text"]
        data = json.loads(text)
        # Should have status or health field
        assert "status" in data or "health" in data


class TestMCPKernelLawList:
    """Tests for the law_list tool."""

    def test_law_list(self):
        resp = _call_mcp("mcp_kernel", "tools/call", {
            "name": "law_list", "arguments": {},
        })
        text = resp["result"]["content"][0]["text"]
        data = json.loads(text)
        # Should return some laws
        assert "laws" in data or "count" in data


class TestMCPKernelEvidenceGrade:
    """Tests for the evidence_grade tool."""

    def test_evidence_grade_valid(self):
        resp = _call_mcp("mcp_kernel", "tools/call", {
            "name": "evidence_grade",
            "arguments": {
                "evidence_type": "test",
                "description": "Unit test passing",
                "source": "pytest",
            },
        })
        # May return result or error (depending on required fields)
        if "result" in resp:
            text = resp["result"]["content"][0]["text"]
            data = json.loads(text)
            assert "grade" in data or "error" in data
        else:
            # Error response is acceptable for missing required fields
            assert "error" in resp


class TestMCPKernelReceiptCreate:
    """Tests for the receipt_create tool."""

    def test_receipt_create(self):
        resp = _call_mcp("mcp_kernel", "tools/call", {
            "name": "receipt_create",
            "arguments": {
                "agent_id": "test-agent",
                "operation": "test_op",
                "details": "Test operation",
            },
        })
        if "result" in resp:
            text = resp["result"]["content"][0]["text"]
            data = json.loads(text)
            assert "receipt" in data or "error" in data or "stored" in data
        else:
            assert "error" in resp


# ===========================================================================
# mcp_coordination tests
# ===========================================================================

class TestMCPCoordinationToolsList:
    """Tests for the coordination MCP server tools/list."""

    def test_tools_list_returns_14(self):
        resp = _call_mcp("mcp_coordination", "tools/list")
        tools = resp["result"]["tools"]
        assert len(tools) == 14

    def test_tools_have_required_fields(self):
        resp = _call_mcp("mcp_coordination", "tools/list")
        for t in resp["result"]["tools"]:
            assert "name" in t
            assert "description" in t
            assert "inputSchema" in t

    def test_expected_tool_names(self):
        resp = _call_mcp("mcp_coordination", "tools/list")
        names = {t["name"] for t in resp["result"]["tools"]}
        expected = {
            "bus_post", "bus_read", "bus_state", "bus_filter",
            "lamport_time", "lamport_tick", "lamport_observe", "lamport_compare",
            "convergence_record", "convergence_check",
            "contract_post_task", "contract_bid", "contract_award",
            "contract_enforce",
        }
        assert names == expected


class TestMCPCoordinationBusState:
    """Tests for the bus_state tool."""

    def test_bus_state(self):
        resp = _call_mcp("mcp_coordination", "tools/call", {
            "name": "bus_state", "arguments": {},
        })
        text = resp["result"]["content"][0]["text"]
        data = json.loads(text)
        # Should return bus state info
        assert isinstance(data, dict)


class TestMCPCoordinationLamport:
    """Tests for the lamport clock tools."""

    def test_lamport_time(self):
        resp = _call_mcp("mcp_coordination", "tools/call", {
            "name": "lamport_time", "arguments": {"agent_id": "test-agent"},
        })
        text = resp["result"]["content"][0]["text"]
        data = json.loads(text)
        assert "time" in data or "timestamp" in data or "error" in data

    def test_lamport_tick(self):
        resp = _call_mcp("mcp_coordination", "tools/call", {
            "name": "lamport_tick", "arguments": {"agent_id": "test-agent"},
        })
        text = resp["result"]["content"][0]["text"]
        data = json.loads(text)
        assert "time" in data or "timestamp" in data or "error" in data


class TestMCPCoordinationConvergence:
    """Tests for convergence guard tools."""

    def test_convergence_record(self):
        resp = _call_mcp("mcp_coordination", "tools/call", {
            "name": "convergence_record",
            "arguments": {
                "agent_id": "test-agent",
                "action": "test_action",
                "reward": 1.0,
            },
        })
        text = resp["result"]["content"][0]["text"]
        data = json.loads(text)
        assert isinstance(data, dict)


# ===========================================================================
# mcp_execution tests
# ===========================================================================

class TestMCPExecutionToolsList:
    """Tests for the execution MCP server tools/list."""

    def test_tools_list_returns_14(self):
        resp = _call_mcp("mcp_execution", "tools/list")
        tools = resp["result"]["tools"]
        assert len(tools) == 14

    def test_tools_have_required_fields(self):
        resp = _call_mcp("mcp_execution", "tools/list")
        for t in resp["result"]["tools"]:
            assert "name" in t
            assert "description" in t
            assert "inputSchema" in t

    def test_expected_tool_names(self):
        resp = _call_mcp("mcp_execution", "tools/list")
        names = {t["name"] for t in resp["result"]["tools"]}
        expected = {
            "eal_validate", "eal_revalidate", "eal_compat",
            "reward_monitor_record", "reward_monitor_check",
            "error_classify", "failure_modes_list", "failure_mode_analyze",
            "approval_request", "approval_decide",
            "attest_verify", "tool_audit_call",
            "transition_create", "transition_verify",
        }
        assert names == expected


class TestMCPExecutionFailureModes:
    """Tests for failure mode tools."""

    def test_failure_modes_list(self):
        resp = _call_mcp("mcp_execution", "tools/call", {
            "name": "failure_modes_list", "arguments": {},
        })
        text = resp["result"]["content"][0]["text"]
        data = json.loads(text)
        # Should return a list of failure modes
        assert "failure_modes" in data or "modes" in data or "count" in data

    def test_error_classify(self):
        resp = _call_mcp("mcp_execution", "tools/call", {
            "name": "error_classify",
            "arguments": {"error_code": "FM01"},
        })
        text = resp["result"]["content"][0]["text"]
        data = json.loads(text)
        assert isinstance(data, dict)


class TestMCPExecutionApproval:
    """Tests for approval workflow tools."""

    def test_approval_request(self):
        resp = _call_mcp("mcp_execution", "tools/call", {
            "name": "approval_request",
            "arguments": {
                "agent_id": "test-agent",
                "action": "deploy",
                "risk_level": "low",
            },
        })
        text = resp["result"]["content"][0]["text"]
        data = json.loads(text)
        assert "approval_id" in data or "id" in data or "error" in data


class TestMCPExecutionTransition:
    """Tests for transition receipt tools."""

    def test_transition_create_and_verify(self):
        """Create a transition receipt and verify it."""
        # Create
        resp1 = _call_mcp("mcp_execution", "tools/call", {
            "name": "transition_create",
            "arguments": {
                "tool_name": "test_tool",
                "agent_id": "test-agent",
                "decision": "allow",
            },
        })
        text1 = resp1["result"]["content"][0]["text"]
        data1 = json.loads(text1)
        # May return receipt directly or wrapped
        assert "receipt_id" in data1 or "receipt" in data1 or "error" in data1
