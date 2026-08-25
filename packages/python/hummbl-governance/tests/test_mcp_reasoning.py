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

"""Tests for mcp_reasoning.py — ReasoningEngine, SchemaValidator, ContractNetManager."""

import importlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

MCP_PATH = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(MCP_PATH))

import mcp_reasoning as mcp  # noqa: E402


def fresh_module():
    import mcp_reasoning
    importlib.reload(mcp_reasoning)
    return mcp_reasoning


# ---------------------------------------------------------------------------
# ReasoningEngine tools
# ---------------------------------------------------------------------------

class TestReasoningListModels:
    def test_list_models(self):
        result = mcp.handle_tool("reasoning_list_models", {})
        assert "count" in result
        assert "models" in result
        assert isinstance(result["models"], list)

    def test_models_have_required_fields(self):
        result = mcp.handle_tool("reasoning_list_models", {})
        for model in result["models"]:
            assert "code" in model
            assert "name" in model
            assert "transformation" in model


class TestReasoningGetModel:
    def test_get_model_found(self):
        # First get list to find a real code
        list_result = mcp.handle_tool("reasoning_list_models", {})
        if list_result["count"] == 0:
            pytest.skip("No Base120 models loaded")
        first_code = list_result["models"][0]["code"]
        result = mcp.handle_tool("reasoning_get_model", {"code": first_code})
        assert result["found"] is True
        assert "definition" in result
        assert "transformation" in result

    def test_get_model_not_found(self):
        result = mcp.handle_tool("reasoning_get_model", {"code": "XXXX"})
        assert result["found"] is False

    def test_get_model_missing_code(self):
        result = mcp.handle_tool("reasoning_get_model", {})
        assert "error" in result


class TestReasoningSystemPrompt:
    def test_system_prompt_known_code(self):
        list_result = mcp.handle_tool("reasoning_list_models", {})
        if list_result["count"] == 0:
            pytest.skip("No Base120 models loaded")
        first_code = list_result["models"][0]["code"]
        result = mcp.handle_tool("reasoning_system_prompt", {"code": first_code, "depth": 1})
        assert "system_prompt" in result
        assert len(result["system_prompt"]) > 0
        assert result["length"] > 0

    def test_system_prompt_unknown_code(self):
        result = mcp.handle_tool("reasoning_system_prompt", {"code": "ZZNOTREAL"})
        assert "error" in result

    def test_system_prompt_missing_code(self):
        result = mcp.handle_tool("reasoning_system_prompt", {})
        assert "error" in result


# ---------------------------------------------------------------------------
# SchemaValidator tools
# ---------------------------------------------------------------------------

class TestSchemaValidate:
    def test_valid_object(self):
        result = mcp.handle_tool("schema_validate", {
            "instance": {"name": "Alice", "age": 30},
            "schema": {
                "type": "object",
                "required": ["name"],
                "properties": {
                    "name": {"type": "string"},
                    "age": {"type": "integer"},
                },
            },
        })
        assert result["valid"] is True
        assert result["error_count"] == 0

    def test_invalid_missing_required(self):
        result = mcp.handle_tool("schema_validate", {
            "instance": {"age": 30},
            "schema": {
                "type": "object",
                "required": ["name"],
                "properties": {"name": {"type": "string"}},
            },
        })
        assert result["valid"] is False
        assert result["error_count"] > 0

    def test_invalid_type(self):
        result = mcp.handle_tool("schema_validate", {
            "instance": "hello",
            "schema": {"type": "integer"},
        })
        assert result["valid"] is False

    def test_validate_array(self):
        result = mcp.handle_tool("schema_validate", {
            "instance": [1, 2, 3],
            "schema": {"type": "array", "items": {"type": "integer"}, "minItems": 1},
        })
        assert result["valid"] is True

    def test_missing_schema(self):
        result = mcp.handle_tool("schema_validate", {"instance": {}})
        assert "error" in result

    def test_missing_instance(self):
        result = mcp.handle_tool("schema_validate", {"schema": {"type": "object"}})
        assert "error" in result


class TestSchemaValidateDict:
    def test_valid_dict(self):
        result = mcp.handle_tool("schema_validate_dict", {
            "entry": {"event": "auth", "agent": "worker"},
            "schema": {
                "type": "object",
                "required": ["event"],
                "properties": {"event": {"type": "string"}},
            },
        })
        assert result["valid"] is True

    def test_invalid_dict(self):
        result = mcp.handle_tool("schema_validate_dict", {
            "entry": {"agent": "worker"},
            "schema": {
                "type": "object",
                "required": ["event"],
            },
        })
        assert result["valid"] is False

    def test_missing_entry(self):
        result = mcp.handle_tool("schema_validate_dict", {"schema": {"type": "object"}})
        assert "error" in result


# ---------------------------------------------------------------------------
# ContractNetManager tools
# ---------------------------------------------------------------------------

class TestContractAnnounce:
    def test_announce_basic(self):
        m = fresh_module()
        result = m.handle_tool("contract_announce", {
            "announcer": "orch",
            "task_id": "task-1",
            "requirements": {"skill": "ocr"},
            "deadline_seconds": 60,
        })
        assert "announcement_id" in result
        assert result["phase"] == "bidding"

    def test_announce_missing_fields(self):
        result = mcp.handle_tool("contract_announce", {"announcer": "orch"})
        assert "error" in result


class TestContractBid:
    def setup_method(self):
        self.m = fresh_module()
        result = self.m.handle_tool("contract_announce", {
            "announcer": "orch",
            "task_id": "task-bid",
            "deadline_seconds": 300,
        })
        self.ann_id = result["announcement_id"]

    def test_bid_accepted(self):
        result = self.m.handle_tool("contract_bid", {
            "announcement_id": self.ann_id,
            "bidder": "worker-1",
            "cost": 0.5,
            "capability": 0.9,
        })
        assert result["accepted"] is True

    def test_bid_multiple_workers(self):
        self.m.handle_tool("contract_bid", {
            "announcement_id": self.ann_id,
            "bidder": "worker-1",
            "cost": 0.5,
            "capability": 0.9,
        })
        result = self.m.handle_tool("contract_bid", {
            "announcement_id": self.ann_id,
            "bidder": "worker-2",
            "cost": 0.3,
            "capability": 0.7,
        })
        assert result["accepted"] is True

    def test_bid_missing_fields(self):
        result = self.m.handle_tool("contract_bid", {"announcement_id": self.ann_id})
        assert "error" in result

    def test_bid_nonexistent_announcement(self):
        result = self.m.handle_tool("contract_bid", {
            "announcement_id": "nonexistent-id",
            "bidder": "w1",
        })
        assert result["accepted"] is False


class TestContractEvaluate:
    def setup_method(self):
        self.m = fresh_module()
        result = self.m.handle_tool("contract_announce", {
            "announcer": "orch",
            "task_id": "task-eval",
            "deadline_seconds": 300,
        })
        self.ann_id = result["announcement_id"]

    def test_evaluate_lowest_cost(self):
        self.m.handle_tool("contract_bid", {
            "announcement_id": self.ann_id,
            "bidder": "w1",
            "cost": 0.8,
        })
        self.m.handle_tool("contract_bid", {
            "announcement_id": self.ann_id,
            "bidder": "w2",
            "cost": 0.3,
        })
        result = self.m.handle_tool("contract_evaluate", {
            "announcement_id": self.ann_id,
            "strategy": "lowest_cost",
        })
        assert result["winner"]["bidder"] == "w2"
        assert result["phase"] == "awarded"

    def test_evaluate_highest_capability(self):
        self.m.handle_tool("contract_bid", {
            "announcement_id": self.ann_id,
            "bidder": "w1",
            "capability": 0.5,
        })
        self.m.handle_tool("contract_bid", {
            "announcement_id": self.ann_id,
            "bidder": "w2",
            "capability": 0.9,
        })
        result = self.m.handle_tool("contract_evaluate", {
            "announcement_id": self.ann_id,
            "strategy": "highest_capability",
        })
        assert result["winner"]["bidder"] == "w2"

    def test_evaluate_no_bids(self):
        result = self.m.handle_tool("contract_evaluate", {"announcement_id": self.ann_id})
        assert result["winner"] is None
        assert result["phase"] == "failed"

    def test_evaluate_nonexistent(self):
        result = self.m.handle_tool("contract_evaluate", {"announcement_id": "bad-id"})
        assert "error" in result

    def test_evaluate_missing_id(self):
        result = self.m.handle_tool("contract_evaluate", {})
        assert "error" in result


class TestContractStatus:
    def setup_method(self):
        self.m = fresh_module()
        result = self.m.handle_tool("contract_announce", {
            "announcer": "orch",
            "task_id": "task-status",
            "deadline_seconds": 300,
        })
        self.ann_id = result["announcement_id"]

    def test_status_bidding(self):
        result = self.m.handle_tool("contract_status", {"announcement_id": self.ann_id})
        assert result["found"] is True
        assert result["phase"] == "bidding"
        assert result["bid_count"] == 0

    def test_status_with_bid(self):
        self.m.handle_tool("contract_bid", {
            "announcement_id": self.ann_id,
            "bidder": "w1",
            "cost": 0.5,
        })
        result = self.m.handle_tool("contract_status", {"announcement_id": self.ann_id})
        assert result["bid_count"] == 1

    def test_status_not_found(self):
        result = self.m.handle_tool("contract_status", {"announcement_id": "nope"})
        assert result["found"] is False

    def test_status_missing_id(self):
        result = self.m.handle_tool("contract_status", {})
        assert "error" in result


class TestContractSummary:
    def test_summary_structure(self):
        result = mcp.handle_tool("contract_summary", {})
        assert "by_phase" in result
        assert "total" in result
        assert "active_bidding" in result


# ---------------------------------------------------------------------------
# Protocol-level tests
# ---------------------------------------------------------------------------

class TestProtocol:
    def _call(self, req_obj):
        proc = subprocess.run(
            [sys.executable, str(MCP_PATH / "mcp_reasoning.py")],
            input=json.dumps(req_obj) + "\n",
            capture_output=True,
            text=True,
            timeout=10,
        )
        return json.loads(proc.stdout.strip().split("\n")[0])

    def test_initialize(self):
        resp = self._call({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}})
        assert resp["result"]["serverInfo"]["name"] == "hummbl-reasoning"

    def test_tools_list(self):
        resp = self._call({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})
        tools = {t["name"] for t in resp["result"]["tools"]}
        assert "reasoning_list_models" in tools
        assert "schema_validate" in tools
        assert "contract_announce" in tools
        assert len(tools) == 10

    def test_tools_call_contract_summary(self):
        resp = self._call({
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {"name": "contract_summary", "arguments": {}},
        })
        content = json.loads(resp["result"]["content"][0]["text"])
        assert "by_phase" in content
