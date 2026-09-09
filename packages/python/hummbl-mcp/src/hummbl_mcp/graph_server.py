"""HUMMBL Graph MCP server — stdio JSON-RPC dispatcher for graphify artifacts.

Exposes tools:
  - graph_corpora
  - graph_status
  - graph_query
  - graph_neighbors
  - graph_path

Usage:
    python -m hummbl_mcp.graph_server

Or via uv:
    uv run python -m hummbl_mcp.graph_server
"""

from __future__ import annotations

import sys
from typing import Any

from hummbl_mcp.graph_tools import get_handlers, get_tool_definitions
from hummbl_mcp.protocol import (
    INTERNAL_ERROR,
    METHOD_NOT_FOUND,
    JsonRpcError,
    JsonRpcRequest,
    error_response,
    parse_request_line,
    success_response,
)
from hummbl_mcp.server import HummblMCPServer


MCP_PROTOCOL_VERSION = "2024-11-05"
SERVER_NAME = "hummbl-graph-mcp"
SERVER_VERSION = "0.1.0"


class GraphMCPServer(HummblMCPServer):
    """Graph-specific MCP server with its own initialize identity."""

    def _handle_initialize(self, params: dict[str, Any]) -> dict[str, Any]:
        return {
            "protocolVersion": MCP_PROTOCOL_VERSION,
            "capabilities": {
                "tools": {"listChanged": False},
            },
            "serverInfo": {
                "name": SERVER_NAME,
                "version": SERVER_VERSION,
            },
        }


def make_graph_server() -> HummblMCPServer:
    """Factory returning a graph-only MCP server."""
    return GraphMCPServer(
        tool_definitions=get_tool_definitions(),
        handlers=get_handlers(),
        receipt_identity=SERVER_NAME,
    )


if __name__ == "__main__":  # pragma: no cover
    from hummbl_mcp.server import serve_stdio

    serve_stdio(make_graph_server())
