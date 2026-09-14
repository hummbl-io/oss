"""hummbl_mcp — MCP server modules, gateway, tools, and protocol adapters.

Extracted from the original monorepo's mcp/ directory + MCP-related services/ modules.
Part of the HUMMBL scavenger-mode extraction.
"""
from __future__ import annotations

__version__ = "0.1.0"

_LAZY = {
    # MCP core
    "server": "server",
    "protocol": "protocol",
    "receipts": "receipts",
    # MCP tools
    "bridge_tools": "bridge_tools",
    "gcp_tools": "gcp_tools",
    "graph_tools": "graph_tools",
    "graph_server": "graph_server",
    "billing_tools": "billing_tools",
    "billing_middleware": "billing_middleware",
    "basen_server": "basen_server",
    # MCP services
    "mcp_gateway": "mcp_gateway",
    "mcp_call_tracer": "mcp_call_tracer",
    "mcp_doctor": "mcp_doctor",
    "mcp_git_vault": "mcp_git_vault",
    "mcp_governance": "mcp_governance",
    "mcp_kill_switch": "mcp_kill_switch",
    "mcp_ollama_router": "mcp_ollama_router",
    "mcp_research": "mcp_research",
    "mcp_skills": "mcp_skills",
    "mcp_spark_gateway": "mcp_spark_gateway",
    "mcp_trust": "mcp_trust",
    "idp_mcp_gateway": "idp_mcp_gateway",
}


def __getattr__(name: str):
    if name in _LAZY:
        import importlib
        mod = importlib.import_module(f"hummbl_mcp.{_LAZY[name]}")
        globals()[name] = mod
        return mod
    raise AttributeError(f"module 'hummbl_mcp' has no attribute '{name}'")


def __dir__():
    return sorted(list(_LAZY.keys()) + ["__version__"])
