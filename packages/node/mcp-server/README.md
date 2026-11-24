# @hummbl/mcp-server

Model Context Protocol (MCP) server for the **HUMMBL Base120** mental models
framework — 120 structured reasoning operators for analysis, planning, and
decision work. Runs locally over stdio; no account, daemon, or hosted service
required.

## What it provides

- **Model tools** — `get_model`, `list_all_models`, `search_models`,
  `get_transformation`, `search_problem_patterns`, `get_related_models`
- **Methodology tools** — `get_methodology`, `audit_model_references`
- **Workflow tools** — `list_workflows`, `find_workflow_for_problem`,
  `start_workflow`, `continue_workflow`, `recommend_models`,
  `get_recommendation_history`
- **Export** — `export_models` (JSON/Markdown/PDF catalog export)
- **Resources & prompts** — browsable model catalog and workflow prompt
  templates

All 120 models are bundled and served locally. An optional
`HUMMBL_API_KEY` enables enhanced recommendations via the hosted HUMMBL API;
without it the server runs fully local-only.

## Install

Requires Node.js 22+.

```bash
npm install -g @hummbl/mcp-server
# or run without installing:
npx -y @hummbl/mcp-server
```

## Client setup

### Claude Desktop

Add to `claude_desktop_config.json`
(`%APPDATA%\Claude\claude_desktop_config.json` on Windows,
`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "hummbl": {
      "command": "npx",
      "args": ["-y", "@hummbl/mcp-server"]
    }
  }
}
```

### Cursor

Add to `~/.cursor/mcp.json` (or `.cursor/mcp.json` in a project):

```json
{
  "mcpServers": {
    "hummbl": {
      "command": "npx",
      "args": ["-y", "@hummbl/mcp-server"]
    }
  }
}
```

### VS Code

Add to `.vscode/mcp.json` in your workspace (or user profile):

```json
{
  "servers": {
    "hummbl": {
      "command": "npx",
      "args": ["-y", "@hummbl/mcp-server"]
    }
  }
}
```

### Codex CLI

Add to `~/.codex/config.toml`:

```toml
[mcp_servers.hummbl]
command = "npx"
args = ["-y", "@hummbl/mcp-server"]
```

## Optional: enhanced recommendations

Set `HUMMBL_API_KEY` in the client's environment to enable API-backed
recommendations and relationship lookups. Without it, every tool works in
local-only mode against the bundled catalog.

## Development

```bash
npm install
npm run build      # tsc -> dist/
npm test           # vitest
npm run typecheck
```

## License

Apache-2.0. See [LICENSE](../../LICENSE) at the repository root.
