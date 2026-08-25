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

"""Tests for mcp_identity.py — Identity, Delegation, and Lamport Clock MCP server."""

import importlib
import json
import subprocess
import sys
from pathlib import Path


# Import the module under test directly
MCP_PATH = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(MCP_PATH))

import mcp_identity as mcp  # noqa: E402


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def fresh_module():
    """Re-import to get a clean server state between test classes."""
    import mcp_identity
    importlib.reload(mcp_identity)
    return mcp_identity


# ---------------------------------------------------------------------------
# Identity tools
# ---------------------------------------------------------------------------

class TestIdentityRegister:
    def test_register_basic(self):
        m = fresh_module()
        result = m.handle_tool("identity_register", {"agent_id": "agent-1", "trust_tier": "high"})
        assert result["registered"] is True
        assert result["agent_id"] == "agent-1"
        assert result["trust_tier"] == "high"

    def test_register_with_aliases(self):
        m = fresh_module()
        result = m.handle_tool("identity_register", {
            "agent_id": "agent-2",
            "trust_tier": "medium",
            "aliases": ["a2", "worker"],
        })
        assert result["registered"] is True
        assert result["aliases"] == ["a2", "worker"]

    def test_register_missing_agent_id(self):
        result = mcp.handle_tool("identity_register", {})
        assert "error" in result

    def test_register_default_trust_tier(self):
        m = fresh_module()
        result = m.handle_tool("identity_register", {"agent_id": "agent-3"})
        assert result["trust_tier"] == "low"


class TestIdentityLookup:
    def setup_method(self):
        self.m = fresh_module()
        self.m.handle_tool("identity_register", {"agent_id": "agent-lookup", "trust_tier": "high"})

    def test_lookup_existing(self):
        result = self.m.handle_tool("identity_lookup", {"agent_id": "agent-lookup"})
        assert result["found"] is True
        assert result["trust_tier"] == "high"

    def test_lookup_missing(self):
        result = self.m.handle_tool("identity_lookup", {"agent_id": "nonexistent"})
        assert result["found"] is False

    def test_lookup_no_id(self):
        result = self.m.handle_tool("identity_lookup", {})
        assert "error" in result


class TestIdentityList:
    def test_list_empty(self):
        m = fresh_module()
        result = m.handle_tool("identity_list", {})
        assert "count" in result
        assert "agents" in result
        assert isinstance(result["agents"], list)

    def test_list_with_agents(self):
        m = fresh_module()
        m.handle_tool("identity_register", {"agent_id": "a1", "trust_tier": "high"})
        m.handle_tool("identity_register", {"agent_id": "a2", "trust_tier": "low"})
        result = m.handle_tool("identity_list", {})
        assert result["count"] >= 2
        ids = [a["agent_id"] for a in result["agents"]]
        assert "a1" in ids
        assert "a2" in ids


class TestIdentityValidate:
    def test_valid_sender(self):
        m = fresh_module()
        m.handle_tool("identity_register", {"agent_id": "sender-1"})
        result = m.handle_tool("identity_validate", {"agent_id": "sender-1"})
        assert result["valid_sender"] is True

    def test_unregistered_sender(self):
        m = fresh_module()
        result = m.handle_tool("identity_validate", {"agent_id": "unknown-agent"})
        assert result["valid_sender"] is False

    def test_validate_no_id(self):
        result = mcp.handle_tool("identity_validate", {})
        assert "error" in result


# ---------------------------------------------------------------------------
# Delegation tools
# ---------------------------------------------------------------------------

class TestDelegationCreate:
    def setup_method(self):
        self.m = fresh_module()

    def test_create_basic(self):
        result = self.m.handle_tool("delegation_create", {
            "issuer": "orchestrator",
            "subject": "worker",
            "ops_allowed": ["read", "write"],
            "task_id": "task-1",
            "contract_id": "contract-1",
        })
        assert "token_id" in result
        assert result["issuer"] == "orchestrator"
        assert result["subject"] == "worker"
        assert "read" in result["ops_allowed"]
        assert "signature" in result
        assert "..." in result["signature"]  # truncated

    def test_create_missing_issuer(self):
        result = self.m.handle_tool("delegation_create", {
            "subject": "worker",
            "ops_allowed": ["read"],
            "task_id": "task-1",
            "contract_id": "contract-1",
        })
        assert "error" in result

    def test_create_missing_binding(self):
        result = self.m.handle_tool("delegation_create", {
            "issuer": "orch",
            "subject": "worker",
            "ops_allowed": ["read"],
        })
        assert "error" in result

    def test_create_empty_ops(self):
        result = self.m.handle_tool("delegation_create", {
            "issuer": "orch",
            "subject": "worker",
            "ops_allowed": [],
            "task_id": "t1",
            "contract_id": "c1",
        })
        assert "error" in result

    def test_create_stores_token(self):
        result = self.m.handle_tool("delegation_create", {
            "issuer": "orch",
            "subject": "worker",
            "ops_allowed": ["execute"],
            "task_id": "t1",
            "contract_id": "c1",
        })
        token_id = result["token_id"]
        assert token_id in self.m._tokens


class TestDelegationValidate:
    def setup_method(self):
        self.m = fresh_module()
        result = self.m.handle_tool("delegation_create", {
            "issuer": "orch",
            "subject": "worker",
            "ops_allowed": ["read"],
            "task_id": "t1",
            "contract_id": "c1",
        })
        self.token_id = result["token_id"]

    def test_validate_valid_token(self):
        result = self.m.handle_tool("delegation_validate", {"token_id": self.token_id})
        assert result["valid"] is True
        assert result["error_code"] is None

    def test_validate_nonexistent_token(self):
        result = self.m.handle_tool("delegation_validate", {"token_id": "nonexistent"})
        assert result["valid"] is False
        assert "error" in result

    def test_validate_missing_token_id(self):
        result = self.m.handle_tool("delegation_validate", {})
        assert "error" in result


class TestDelegationCheckOp:
    def setup_method(self):
        self.m = fresh_module()
        result = self.m.handle_tool("delegation_create", {
            "issuer": "orch",
            "subject": "worker",
            "ops_allowed": ["read", "query"],
            "task_id": "t1",
            "contract_id": "c1",
        })
        self.token_id = result["token_id"]

    def test_allowed_op(self):
        result = self.m.handle_tool("delegation_check_op", {
            "token_id": self.token_id,
            "requested_op": "read",
        })
        assert result["allowed"] is True

    def test_disallowed_op(self):
        result = self.m.handle_tool("delegation_check_op", {
            "token_id": self.token_id,
            "requested_op": "delete",
        })
        assert result["allowed"] is False

    def test_missing_token_id(self):
        result = self.m.handle_tool("delegation_check_op", {"requested_op": "read"})
        assert "error" in result


# ---------------------------------------------------------------------------
# Lamport Clock tools
# ---------------------------------------------------------------------------

class TestLamportClock:
    def setup_method(self):
        self.m = fresh_module()

    def test_tick(self):
        before = self.m._lamport.value
        result = self.m.handle_tool("lamport_tick", {})
        assert result["time"] > before
        assert "agent_id" in result

    def test_receive(self):
        result = self.m.handle_tool("lamport_receive", {"remote_timestamp": 100})
        assert result["time"] >= 100
        assert result["remote_timestamp"] == 100

    def test_receive_missing_timestamp(self):
        result = self.m.handle_tool("lamport_receive", {})
        assert "error" in result

    def test_compare_ts1_before_ts2(self):
        result = self.m.handle_tool("lamport_compare", {
            "ts1_time": 1,
            "ts1_agent": "a",
            "ts2_time": 5,
            "ts2_agent": "b",
        })
        assert result["ordering"] == "ts1_before_ts2"
        assert result["happened_before"] is True

    def test_compare_ts2_before_ts1(self):
        result = self.m.handle_tool("lamport_compare", {
            "ts1_time": 10,
            "ts1_agent": "a",
            "ts2_time": 3,
            "ts2_agent": "b",
        })
        assert result["ordering"] == "ts2_before_ts1"

    def test_compare_concurrent(self):
        result = self.m.handle_tool("lamport_compare", {
            "ts1_time": 5,
            "ts1_agent": "x",
            "ts2_time": 5,
            "ts2_agent": "x",
        })
        assert result["ordering"] == "concurrent"

    def test_compare_missing_times(self):
        result = self.m.handle_tool("lamport_compare", {"ts1_agent": "a"})
        assert "error" in result


# ---------------------------------------------------------------------------
# Protocol-level tests (subprocess)
# ---------------------------------------------------------------------------

class TestProtocol:
    def _call(self, req_obj):
        proc = subprocess.run(
            [sys.executable, str(MCP_PATH / "mcp_identity.py")],
            input=json.dumps(req_obj) + "\n",
            capture_output=True,
            text=True,
            timeout=10,
        )
        return json.loads(proc.stdout.strip().split("\n")[0])

    def test_initialize(self):
        resp = self._call({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}})
        assert resp["result"]["serverInfo"]["name"] == "hummbl-identity"
        assert resp["result"]["protocolVersion"] == "2024-11-05"

    def test_tools_list(self):
        resp = self._call({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})
        tools = {t["name"] for t in resp["result"]["tools"]}
        assert "identity_register" in tools
        assert "delegation_create" in tools
        assert "lamport_tick" in tools
        assert len(tools) == 10

    def test_unknown_method(self):
        resp = self._call({"jsonrpc": "2.0", "id": 3, "method": "no_such_method", "params": {}})
        assert "error" in resp

    def test_tools_call_identity_list(self):
        resp = self._call({
            "jsonrpc": "2.0",
            "id": 4,
            "method": "tools/call",
            "params": {"name": "identity_list", "arguments": {}},
        })
        content = json.loads(resp["result"]["content"][0]["text"])
        assert "agents" in content
