# hummbl-mcp-onepassword

MCP server exposing the 1Password CLI (`op`) as tools for autonomous agent
secret access. Wraps the 1Password service account token (from Windows
Credential Manager via PowerShell profile) so agents can retrieve secrets
without human intervention.

## Tools

- `onepassword_get` — retrieve a secret value by item title + vault + field
- `onepassword_list` — list items in a vault (title, category, id; no values)
- `onepassword_vaults` — list vaults accessible to the service account
- `onepassword_fields` — discover field names for an item (no values revealed)
- `onepassword_resolve` — look up a secret by common name (e.g. "github pat", "anthropic key")

## Install

```bash
pip install hummbl-mcp-onepassword
```

## Run

```bash
hummbl-mcp-onepassword
```

Or via stdio JSON-RPC:

```bash
python onepassword_mcp_server.py
```

## Prerequisites

- `op` CLI v2.30+ installed and on PATH
- `OP_SERVICE_ACCOUNT_TOKEN` env var set (auto-loaded from Windows Credential
  Manager by `~/.bin/load-1p-token.ps1` via the PowerShell profile)
- Service account must have access to the target vaults

## Security

Secret values are returned in MCP content but agents MUST redact them in
user-facing output. The `onepassword_fields` tool returns field names only
(no values) for safe discovery.

## Dependencies

None (Python stdlib only). Requires the `op` CLI as an external binary.

## License

Apache-2.0
