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

"""Thin shim MCP server for the Cognitive Ledger Protocol (CLP).

This is a monorepo catalog entry point for the cognitive-ledger MCP server.
The actual server implementation lives in the `hummbl-cognition` package
(https://github.com/hummbl-io/hummbl-cognition), which is pip-installed and
provides the `hummbl_cognition.mcp_server` module.

This shim delegates entirely to the installed package, so the monorepo has a
consistent `packages/python/<name>/<name>_mcp_server.py` entry point for every
MCP server in the fleet without duplicating the 63-file `hummbl_cognition`
source. Each shim's module name is namespaced per-package (rather than a bare
`mcp_server`) so multiple HUMMBL MCP servers can be pip-installed into the
same Python environment without colliding on the same top-level module name.

Tools exposed (via delegation):
  ledger_search   — BM25 search over the cognitive ledger
  ledger_query    — structured query of ledger entries
  ledger_post     — append a new entry to the cognitive ledger
  ledger_stats    — ledger statistics (entry count, date range, types)
  boot_context    — build session startup context from the ledger
  reindex         — rebuild the BM25 search index

Environment:
  CLP_STATE_DIR     - ledger state directory (default: hummbl_cognition default)
  COGNITION_VENDOR  - default vendor for ledger_post (anthropic|openai|google|...)
  COGNITION_MODEL   - default model for ledger_post

Wire into MCP config::

    {
      "mcpServers": {
        "cognitive-ledger": {
          "command": "hummbl-mcp-cognitive-ledger",
          "env": {
            "CLP_STATE_DIR": "C:\\path\\to\\hummbl-cognition\\_state\\cognition"
          }
        }
      }
    }

Zero third-party dependencies (delegates to installed hummbl_cognition).
"""

from __future__ import annotations


# Delegate entirely to the installed package's MCP server module.
# This imports the module's run() function and calls it with the real stdio.
from hummbl_cognition.mcp_server import main


if __name__ == "__main__":
    main()
