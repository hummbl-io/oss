# hummbl-mcp

HUMMBL MCP server modules -- gateway, tools, and protocol adapters.

## Overview

Python MCP framework providing server infrastructure, protocol handling,
governance integration, and tool adapters for Model Context Protocol
deployments. 23 modules covering:

- **MCP core**: server, protocol, receipts
- **MCP tools**: bridge_tools, gcp_tools, graph_tools, graph_server, billing_tools, billing_middleware, basen_server, kb_tools
- **MCP services**: mcp_gateway, mcp_call_tracer, mcp_doctor, mcp_git_vault, mcp_governance, mcp_kill_switch, mcp_ollama_router, mcp_research, mcp_skills, mcp_spark_gateway, mcp_trust, idp_mcp_gateway

### Kill-switch state and recovery

The dedicated `hummbl_mcp.mcp_kill_switch` server exposes only status, task-check,
and history tools. Configure `GOVERNANCE_STATE_DIR` and the same
`HUMMBL_SIGNING_SECRET` (or `DCT_SECRET`) used by the governance writer before
starting the process. The default directory is `<tempdir>/governance`; production
operators should select durable, access-controlled storage shared by both processes.

The shared core re-reads and verifies the state file before every decision,
including reads through retained references. An absent key, missing file, invalid
signature, or malformed state returns an MCP tool error; callers must treat errors
as denial. Reads never create state, disable verification, or clear an emergency.
The critical-task exemptions remain unchanged: EMERGENCY blocks every task.

For first-time provisioning, an authorized operator configures the signing key
and explicitly engages EMERGENCY using `KillSwitch(state_dir=...)`. Release is a
separate authorized governance operation after successful verification. Restoring
the original credential preserves the signed mode; it does not disengage the switch.
For damaged or legacy unsigned state, preserve the evidence and have the operator
establish a trusted signed EMERGENCY snapshot before considering release. Deleting
the file is not recovery: both running and newly started readers reject its absence.

Writers require a key when HMAC is mandatory and atomically replace the state file.
Failed writes raise an error, preserve the previous file, and prevent the affected
instance from making decisions until an explicit EMERGENCY write succeeds. Do not
restart as a substitute for resolving a failed write: other processes can observe
only transitions successfully committed to storage.

These checks cover the snapshot read at the decision boundary, not cancellation
of work already running. They do not add writer authorization, distributed writer
ordering, or replay protection; the existing governance authorization boundary and
storage/key access controls remain required. History includes local and observed
transitions, not an exhaustive cross-process audit log.

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
