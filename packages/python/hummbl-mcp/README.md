# hummbl-mcp

HUMMBL MCP server modules -- gateway, tools, and protocol adapters.

## Overview

Python MCP framework providing server infrastructure, protocol handling,
governance integration, and tool adapters for Model Context Protocol
deployments. 23 modules covering:

- **MCP core**: server, protocol, receipts
- **MCP tools**: bridge_tools, gcp_tools, graph_tools, graph_server, billing_tools, billing_middleware, basen_server, kb_tools
- **MCP services**: mcp_gateway, mcp_call_tracer, mcp_doctor, mcp_git_vault, mcp_governance, mcp_kill_switch, mcp_ollama_router, mcp_research, mcp_skills, mcp_spark_gateway, mcp_trust, idp_mcp_gateway

## Installation

```bash
pip install -e .
```

## Conventions

- Python 3.11+ required
- Zero third-party runtime dependencies (stdlib only)
- Optional integrations: `hummbl-bus`, `hummbl-cognition`, `hummbl-governance`
- All credentials via environment variables -- no secrets in code

## License

MIT OR Apache-2.0
