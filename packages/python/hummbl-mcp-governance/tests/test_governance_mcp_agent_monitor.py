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

"""Fail-closed lifecycle_authorize on the hummbl-mcp-governance monitor."""

import importlib
import sys
from pathlib import Path

MCP_PATH = Path(__file__).resolve().parent.parent
if str(MCP_PATH) not in sys.path:
    sys.path.insert(0, str(MCP_PATH))

import governance_mcp_agent_monitor as mcp


def fresh_module():
    import governance_mcp_agent_monitor

    return importlib.reload(governance_mcp_agent_monitor)


def test_unknown_agent_denied():
    m = fresh_module()
    result = m.handle_tool("lifecycle_authorize", {"agent": "worker-1", "action": "read"})
    assert result["allowed"] is False
    assert result["reason"] == "agent:unknown"
    assert m._lifecycle._allow_unregistered_agents is False


def test_registered_active_agent_allowed():
    m = fresh_module()
    registered = m.handle_tool(
        "lifecycle_register_agent",
        {"agent": "worker-1", "trust": "medium", "status": "active"},
    )
    assert registered["registered"] is True
    result = m.handle_tool("lifecycle_authorize", {"agent": "worker-1", "action": "read"})
    assert result["allowed"] is True
    assert result["checks"]["agent_registered"] is True


def test_import_has_handle_tool():
    assert callable(mcp.handle_tool)
