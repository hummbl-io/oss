# Copyright 2024-2026 HUMMBL
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

"""Protocol guard tests: non-dict JSON-RPC payloads must not kill the loop."""

import importlib
import io
import json
import sys
from pathlib import Path

import pytest

MCP_PATH = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(MCP_PATH))

LOOP_MODULES = [
    "governance_mcp_server",
    "governance_mcp_compliance",
    "governance_mcp_sandbox",
]

HANDLER_MODULES = [
    "governance_mcp_agent_monitor",
    "governance_mcp_identity",
    "governance_mcp_physical",
    "governance_mcp_reasoning",
]


@pytest.mark.parametrize("name", LOOP_MODULES)
def test_non_dict_payloads_get_invalid_request(name, monkeypatch, capsys):
    srv = importlib.import_module(name)
    monkeypatch.setattr(
        "sys.stdin",
        io.StringIO('123\n[1, 2]\n{"jsonrpc": "2.0", "id": 7, "method": "initialize"}\n'),
    )
    srv.main()
    out = [json.loads(line) for line in capsys.readouterr().out.splitlines() if line.strip()]
    errors = [m for m in out if "error" in m]
    assert len(errors) == 2
    assert all(e["error"]["code"] == -32600 for e in errors)
    assert any(m.get("id") == 7 and "result" in m for m in out)


@pytest.mark.parametrize("name", HANDLER_MODULES)
def test_handle_request_non_dict_returns_invalid_request(name):
    srv = importlib.import_module(name)
    res = srv.handle_request([1, 2, 3])
    assert res["error"]["code"] == -32600
    assert res["error"]["message"] == "Invalid Request"


@pytest.mark.parametrize("name", HANDLER_MODULES)
def test_handle_request_non_dict_params_normalized(name):
    srv = importlib.import_module(name)
    res = srv.handle_request(
        {"jsonrpc": "2.0", "id": 9, "method": "tools/list", "params": [1, 2]}
    )
    assert "error" not in res or res["error"]["code"] != -32603
