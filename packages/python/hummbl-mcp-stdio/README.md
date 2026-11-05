# hummbl-mcp-stdio

Shared JSON-RPC stdio dispatcher for HUMMBL MCP shim servers.

The `hummbl-mcp-*` packages each hand-rolled the same ~100-line MCP
protocol loop (newline-delimited JSON-RPC on stdin/stdout,
`initialize` / `tools/list` / `tools/call` handling, error shaping).
This package owns that plumbing once so shims only declare their tool
surface and handlers.

## Usage

```python
from hummbl_mcp_stdio import serve_stdio

serve_stdio(
    server_name="my-mcp-server",
    server_version="0.1.0",
    tools=[{"name": "my_tool", "description": "...", "inputSchema": {...}}],
    handlers={"my_tool": lambda args: {"content": [{"type": "text", "text": "ok"}]}},
)
```

`handle_request(request, *, server_name, server_version, tools, handlers)`
is also exported for tests and non-stdio transports.

## Protocol notes

- Protocol version: `2024-11-05` (matches existing shims).
- `tools/call` handler exceptions are returned as MCP error content with
  traceback, matching prior shim behavior — the server stays alive.
- Malformed stdin lines are skipped silently, matching prior shim behavior.
