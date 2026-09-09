# hummbl-mcp-omnichannel

The Omni-Meta Systems-of-Systems (OMSOS) Governance Gate.
This server acts as the central router for all outbound fleet communications (Discord, Signal, Social, Voice).

Crucially, it enforces the **"Draft, don't Send"** state machine. Agents do not dispatch directly; they enqueue drafts. Operators must cryptographically or explicitly approve drafts before the router dispatches them to downstream providers.

## Architecture (Zero Dependencies)
- `state.py`: SQLite-backed state machine for message drafts.
- `mcp_server.py`: Standard `stdio` MCP JSON-RPC interface.
- `dispatcher.py`: Routing logic to downstream platform MCPs based on urgency and target.
