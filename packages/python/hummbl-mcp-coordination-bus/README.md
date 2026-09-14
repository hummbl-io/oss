# hummbl-mcp-coordination-bus

Thin shim MCP server for the HUMMBL coordination bus. Delegates to the
`hummbl-bus` package (pip-installed), which provides the actual server
implementation.

## Tools

- `bus_read` — read recent bus messages (optionally filtered)
- `bus_post` — post a message to the coordination bus
- `bus_search` — search messages by content, agent, or type
- `bus_stats` — message count, agent activity, type breakdown
- `bus_agents` — list all agents with message counts and last activity

## Install

```bash
pip install hummbl-mcp-coordination-bus
```

This pulls in `hummbl-bus` as a dependency.

## Run

```bash
hummbl-mcp-coordination-bus
```

Or via stdio JSON-RPC:

```bash
python coordination_bus_mcp_server.py
```

## Environment

- `BUS_FILE` — path to the bus TSV file (default: package default)
- `BUS_CANONICAL_BRIDGE_URL` — remote bridge URL for canonical writes
- `BUS_BRIDGE_TOKEN` — auth token for the remote bridge

## Source of truth

The actual implementation lives in the
[hummbl-bus](https://github.com/hummbl-io/hummbl-bus) repo. This package is a
thin entry point for the monorepo's MCP server catalog.

## License

Apache-2.0
