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

"""Thin shim MCP server for the HUMMBL coordination bus.

This is a monorepo catalog entry point for the coordination-bus MCP server.
The actual server implementation lives in the `hummbl-bus` package
(https://github.com/hummbl-io/hummbl-bus), which is pip-installed and provides
the `hummbl_bus.mcp_server` module.

This shim delegates entirely to the installed package, so the monorepo has a
consistent `packages/python/<name>/<name>_mcp_server.py` entry point for
every MCP server in the fleet without duplicating the `hummbl_bus` source.
Each shim's module name is namespaced per-package (rather than a bare
`mcp_server`) so multiple HUMMBL MCP servers can be pip-installed into the
same Python environment without colliding on the same top-level module name.

Tools exposed (via delegation):
  bus_read    — read recent bus messages (optionally filtered)
  bus_post    — post a message to the coordination bus
  bus_search  — search messages by content, agent, or type
  bus_stats   — message count, agent activity, type breakdown
  bus_agents  — list all agents with message counts and last activity

Environment:
  BUS_FILE              - path to the bus TSV file (default: package default)
  BUS_CANONICAL_BRIDGE_URL - remote bridge URL for canonical writes
  BUS_BRIDGE_TOKEN      - auth token for the remote bridge

Wire into MCP config::

    {
      "mcpServers": {
        "coordination-bus": {
          "command": "hummbl-mcp-coordination-bus",
          "env": {
            "BUS_CANONICAL_BRIDGE_URL": "${BUS_CANONICAL_BRIDGE_URL}",
            "BUS_BRIDGE_TOKEN": "${BUS_BRIDGE_TOKEN}"
          }
        }
      }
    }

Zero third-party dependencies (delegates to installed hummbl_bus).
"""

from __future__ import annotations

# Delegate entirely to the installed package's MCP server module.
from hummbl_bus.mcp_server import main


if __name__ == "__main__":
    main()
