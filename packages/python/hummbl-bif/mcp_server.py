#!/usr/bin/env python3
"""MCP Server for the Batch Ingestion Framework (BIF).

Exposes BIF methodology tools (session management, templates, validation,
status tracking) as MCP tools via stdio JSON-RPC.

Zero third-party dependencies. Uses only Python stdlib.

Usage:
    python3 mcp_server.py

Configure in Claude Code settings.json:
    {
      "mcpServers": {
        "bif": {
          "command": "python3",
          "args": ["<local-path>"]
        }
      }
    }
"""
