# MCP Access Patterns: Comprehensive Research for HUMMBL

> **Date**: 2026-06-23
> **Author**: Devin (T2-COGNITION)
> **Purpose**: Strategic research deliverable driving implementation decisions for HUMMBL's MCP server fleet
> **Status**: COMPLETE
> **Sources**: MCP specification (2024-11-05, 2025-03-26, 2025-06-18, 2025-11-25, draft), Cloudflare Agents docs, client documentation (Claude Desktop, Claude Code, Cursor, VS Code, Windsurf), IETF security draft, SDK documentation

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [MCP Protocol Overview](#2-mcp-protocol-overview)
3. [Transport Mechanisms](#3-transport-mechanisms)
4. [Client Configuration Patterns](#4-client-configuration-patterns)
5. [Authentication & Authorization](#5-authentication--authorization)
6. [Session Management](#6-session-management)
7. [Deployment Patterns](#7-deployment-patterns)
8. [Bridging & Adapter Patterns](#8-bridging--adapter-patterns)
9. [Security Considerations](#9-security-considerations)
10. [Gap Analysis: HUMMBL Current State](#10-gap-analysis-hummbl-current-state)
11. [Recommendations](#11-recommendations)
12. [Appendix: Quick Reference Tables](#12-appendix-quick-reference-tables)

---

## 1. Executive Summary

HUMMBL operates 11 MCP servers (1 TypeScript, 10 Python) that need to be "fit for any set and setting" — accessible from every major AI client, deployment topology, and authentication model. This research identifies **14 distinct access patterns** across transports, client configs, auth models, deployment topologies, and bridging strategies.

**Current state**: All 11 servers support only stdio transport. The TypeScript server (`@hummbl/mcp-server`) has an additional Cloudflare Workers HTTP deployment, but it is a direct REST-like API, not a compliant MCP Streamable HTTP transport. No server implements OAuth 2.1, session management, or the MCP Streamable HTTP transport.

**Critical gap**: The MCP specification has evolved significantly. The 2025-03-26 revision replaced HTTP+SSE with Streamable HTTP. The 2025-11-25 revision added Tasks, simplified OAuth (Client ID Metadata Documents), and strengthened security requirements. HUMMBL's servers are behind on all of these.

**Top 3 recommendations** (detailed in Section 11):

1. Implement Streamable HTTP transport on the TypeScript server using Cloudflare Agents SDK (`McpAgent.serve()`)
2. Add `mcp-remote` compatibility so stdio-only clients can reach remote HUMMBL servers
3. Port Python servers to support Streamable HTTP via a shared transport layer

---

## 2. MCP Protocol Overview

### 2.1 Protocol Versions

| Version        | Date     | Key Changes                                                                                                                                                                                                                                                                                                                                                    |
| -------------- | -------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **2024-11-05** | Nov 2024 | Initial public spec. stdio + HTTP+SSE transports. OAuth 2.1 with Dynamic Client Registration.                                                                                                                                                                                                                                                                  |
| **2025-03-26** | Mar 2025 | **Streamable HTTP replaces HTTP+SSE**. Stateless servers possible. Single `/mcp` endpoint. Session IDs optional via `Mcp-Session-Id` header.                                                                                                                                                                                                                   |
| **2025-06-18** | Jun 2025 | Lifecycle refinements. Capability negotiation improvements. `Mcp-Protocol-Version` header.                                                                                                                                                                                                                                                                     |
| **2025-11-25** | Nov 2025 | **Tasks primitive** (async/long-running). OAuth simplified: Client ID Metadata Documents (CIMD) replace DCR as recommended. OIDC Discovery 1.0 support. Tool icons. Enum elicitation. M2M OAuth (client_credentials). Enterprise IdP controls (Cross App Access). Extensions formalized. SEP-1024: client security requirements for local server installation. |
| **Draft**      | Ongoing  | SEP-2575 (stateless MCP — remove `initialize` handshake). SEP-2567 (sessionless MCP — remove `Mcp-Session-Id`, use explicit state handles). Per-request metadata headers. MRTR (Multi-Request Transport Response).                                                                                                                                             |

### 2.2 Architecture

MCP follows a **client-host-server** architecture:

- **Host**: The LLM application (Claude Desktop, Cursor, VS Code, etc.) that initiates connections
- **Client**: A connector within the host, one per server connection
- **Server**: A service that provides context and capabilities

Communication uses **JSON-RPC 2.0** messages over a transport layer.

### 2.3 Server Features (Capabilities)

Servers offer three primary feature types, negotiated during initialization:

| Feature       | Description                                                                       | Discovery Method                    | Control                                                                    |
| ------------- | --------------------------------------------------------------------------------- | ----------------------------------- | -------------------------------------------------------------------------- |
| **Tools**     | Functions the AI model can execute (e.g., `select_model`, `apply_transformation`) | `tools/list` → `tools/call`         | Model-controlled (agent decides when to call)                              |
| **Resources** | Context/data for the model or user (e.g., `models://all`)                         | `resources/list` → `resources/read` | Application-controlled (user selects) or model-controlled with auto-attach |
| **Prompts**   | Templated messages/workflows (e.g., `problem_decomposition`)                      | `prompts/list` → `prompts/get`      | User-controlled (user selects from menu)                                   |

### 2.4 Client Features (Capabilities)

Clients may offer:

| Feature         | Description                                                       |
| --------------- | ----------------------------------------------------------------- |
| **Sampling**    | Server can request LLM completions from the client's model        |
| **Roots**       | Server can query filesystem/URI boundaries the client operates in |
| **Elicitation** | Server can request structured input from the user (2025-06-18+)   |

### 2.5 Capability Negotiation

During initialization (`initialize` request/response):

1. Client sends its supported protocol version, capabilities, and implementation info
2. Server responds with its protocol version, capabilities, and server info
3. Both parties must respect declared capabilities throughout the session
4. The `tools.listChanged`, `resources.subscribe`, `resources.listChanged`, `prompts.listChanged` flags indicate whether the server will notify on changes

**Draft spec change**: SEP-2575 proposes removing the `initialize` handshake entirely, replacing it with per-request capability declarations via `_meta.io.modelcontextprotocol/clientCapabilities` headers. A `server/discover` method would replace upfront negotiation.

---

## 3. Transport Mechanisms

### 3.1 stdio (Local Subprocess)

| Attribute          | Detail                                            |
| ------------------ | ------------------------------------------------- |
| **Spec status**    | Standard (all versions)                           |
| **Protocol**       | JSON-RPC 2.0 over stdin/stdout, newline-delimited |
| **Process model**  | Client spawns server as child process             |
| **Direction**      | Bidirectional (stdin → server, stdout → client)   |
| **Sessions**       | Implicit (one per process)                        |
| **Multi-client**   | No (1:1 client-server)                            |
| **Network access** | No (local only)                                   |

**How users connect**:

```json
{
  "mcpServers": {
    "hummbl": {
      "command": "npx",
      "args": ["@hummbl/mcp-server"]
    }
  }
}
```

**Server requirements**:

- Read JSON-RPC from stdin, write to stdout
- Messages delimited by newlines, MUST NOT contain embedded newlines
- MAY write UTF-8 logs to stderr
- MUST NOT write anything to stdout that isn't a valid MCP message
- Implement `initialize` handshake, capability negotiation, and all registered tools/resources/prompts

**Authentication**: None at transport level. Credentials passed via environment variables (`env` field in config). Server inherits client process's OS permissions.

**Client support**: ALL clients (Claude Desktop, Claude Code, Cursor, VS Code, Windsurf, Gemini CLI, Cline, Continue, etc.)

**Pros**:

- Simplest implementation — no HTTP stack needed
- Zero network exposure — no attack surface
- Implicit trust between client and server (user launched both)
- Secrets stay local via env vars
- Low latency (no network overhead)
- Works with `npx`/`uvx` — no explicit install step

**Cons**:

- Local only — cannot serve remote clients
- 1:1 client-server — no sharing across multiple clients
- Client must be able to spawn processes (not possible in browser-based clients)
- Server lifecycle tied to client process
- No streaming or server-initiated notifications (though the pipe is technically bidirectional, most stdio implementations are request-response)

**Best use cases**: Local development tools, personal AI assistants, single-user scenarios, tools that access local filesystem, servers distributed via npm/PyPI

---

### 3.2 HTTP+SSE (Legacy Remote Transport)

| Attribute            | Detail                                                                                     |
| -------------------- | ------------------------------------------------------------------------------------------ |
| **Spec status**      | **DEPRECATED** since 2025-03-26. Eligible for removal in future revision.                  |
| **Protocol version** | 2024-11-05                                                                                 |
| **Endpoints**        | Two separate endpoints: `/sse` (GET, persistent stream) + `/messages` or `/message` (POST) |
| **Process model**    | Server is independent process, handles multiple clients                                    |
| **Direction**        | Half-duplex: server→client via SSE stream, client→server via POST                          |
| **Sessions**         | Session ID via query string parameter, tracked in memory                                   |
| **Multi-client**     | Yes                                                                                        |
| **Network access**   | Yes (HTTP/HTTPS)                                                                           |

**How users connect**:

```json
{
  "mcpServers": {
    "hummbl-remote": {
      "type": "sse",
      "url": "https://mcp.hummbl.io/sse",
      "headers": {
        "Authorization": "Bearer ${API_TOKEN}"
      }
    }
  }
}
```

**Server requirements**:

- `/sse` endpoint: GET establishes persistent SSE stream, sends initial `endpoint` event with POST URL
- `/messages` endpoint: POST receives JSON-RPC messages from client
- Session management via query string `sessionId` parameter
- SSE stream carries all server→client messages (responses, notifications, requests)
- Must maintain in-memory session state for each connected client

**Authentication**: OAuth 2.1 (per spec) or API key via headers. Server must validate tokens on every request.

**Client support**: Claude Desktop (via custom connectors), Claude Code (`type: "sse"`), Cursor (URL-based), VS Code (`type: "sse"`), Windsurf (`serverUrl`), Gemini CLI. Some clients only support this via `mcp-remote` adapter.

**Pros**:

- Works with older clients that haven't upgraded to Streamable HTTP
- Server-Sent Events are firewall-friendly (standard HTTP)
- Supports multiple clients

**Cons**:

- **DEPRECATED** — should not be used for new implementations
- Requires two endpoints — more complex routing
- Stateful by design — cannot be truly stateless
- Long-lived connections — problematic for load balancers and serverless platforms
- Session state in memory — difficult to scale horizontally
- Half-duplex — less flexible than full bidirectional

**Best use cases**: Backwards compatibility with older clients only. Migrate to Streamable HTTP ASAP.

---

### 3.3 Streamable HTTP (Current Standard Remote Transport)

| Attribute            | Detail                                                                           |
| -------------------- | -------------------------------------------------------------------------------- |
| **Spec status**      | **STANDARD** since 2025-03-26                                                    |
| **Protocol version** | 2025-03-26+                                                                      |
| **Endpoint**         | Single endpoint: `/mcp` (supports POST and GET)                                  |
| **Process model**    | Server is independent process, can be stateless or stateful                      |
| **Direction**        | Request-response (POST) + optional SSE streaming (GET or upgraded POST response) |
| **Sessions**         | Optional via `Mcp-Session-Id` header (stateful mode) or none (stateless mode)    |
| **Multi-client**     | Yes                                                                              |
| **Network access**   | Yes (HTTP/HTTPS)                                                                 |

**How users connect**:

```json
{
  "mcpServers": {
    "hummbl-remote": {
      "type": "http",
      "url": "https://mcp.hummbl.io/mcp",
      "headers": {
        "Authorization": "Bearer ${API_TOKEN}"
      }
    }
  }
}
```

Note: `"type": "streamable-http"` is accepted as an alias for `"http"` in Claude Code and other clients.

**Server requirements**:

- Single `/mcp` endpoint supporting POST and GET methods
- **POST**: Client sends JSON-RPC messages. Server responds with either:
  - `Content-Type: application/json` (single JSON response), OR
  - `Content-Type: text/event-stream` (SSE stream for multiple messages/streaming)
- Client MUST include `Accept: application/json, text/event-stream` header
- **GET**: Client MAY open an SSE stream for server-to-client messages (notifications, requests)
- **DELETE** (2025-11-25+): Client can terminate a session
- `Mcp-Protocol-Version` header on requests (2025-06-18+)
- Session management: Server MAY return `Mcp-Session-Id` header in `initialize` response. Client MUST include it on subsequent requests if present.
- Stateless mode: No session tracking, each request independent (simplest, most scalable)
- Stateful mode: Track sessions in memory or distributed store, enables server-to-client requests and notifications
- `X-Accel-Buffering: no` header recommended on SSE responses (prevents proxy buffering)
- MUST validate `Origin` header to prevent DNS rebinding attacks
- SHOULD bind to localhost only when running locally

**Authentication**: OAuth 2.1 (per spec) for remote servers. API keys also common. See Section 5.

**Client support**: Claude Desktop (via custom connectors), Claude Code (`type: "http"` or `"streamable-http"`), Cursor (URL-based, auto-detects), VS Code (`type: "http"`), Windsurf (`serverUrl`), Gemini CLI, Cloudflare AI Playground, MCP Inspector.

**Pros**:

- **Current standard** — future-proof
- Stateless mode possible — trivially scalable, works behind load balancers, compatible with serverless
- Single endpoint — simpler routing and infrastructure
- "Just HTTP" — compatible with existing middleware, CDNs, proxies, WAFs
- Supports both simple request-response and rich streaming
- Backwards compatible with HTTP+SSE (can serve both `/mcp` and `/sse`+`/messages`)
- Flexible upgrade path — start stateless, add sessions when needed

**Cons**:

- More complex to implement than stdio (HTTP server, content negotiation, SSE streaming)
- Stateful mode has same scaling challenges as legacy SSE
- Requires authentication for remote exposure
- Must handle CORS, Origin validation, DNS rebinding protection

**Best use cases**: Remote/hosted MCP servers, multi-client scenarios, enterprise deployments, servers behind API gateways, Cloudflare Workers deployments, any scenario requiring network access.

---

### 3.4 WebSocket Transport

| Attribute          | Detail                                                              |
| ------------------ | ------------------------------------------------------------------- |
| **Spec status**    | **Not in the official MCP specification** (community/SDK extension) |
| **Protocol**       | JSON-RPC 2.0 over WebSocket frames                                  |
| **Process model**  | Server is independent process, handles multiple clients             |
| **Direction**      | Full-duplex bidirectional                                           |
| **Sessions**       | Implicit (one per WebSocket connection)                             |
| **Multi-client**   | Yes                                                                 |
| **Network access** | Yes (ws:// or wss://)                                               |

**How users connect**:

```json
{
  "mcpServers": {
    "hummbl-ws": {
      "type": "websocket",
      "url": "wss://mcp.hummbl.io/ws"
    }
  }
}
```

Note: WebSocket support is SDK-dependent. Claude Code supports `"type": "websocket"` in `.mcp.json`. The Kotlin SDK uses a `mcp` WebSocket subprotocol. Other clients vary.

**Server requirements**:

- WebSocket server endpoint (e.g., `wss://host/ws`)
- Implement MCP subprotocol (some SDKs use `mcp` as subprotocol identifier)
- Handle connection lifecycle (open, message, close, ping/pong)
- Full-duplex JSON-RPC message handling
- Keep-alive ping/pong for connection health
- Optional: auto-reconnection with exponential backoff

**Authentication**: Token via headers or query parameter during WebSocket upgrade handshake. OAuth 2.1 not standardized for WebSocket in MCP spec.

**Client support**: Claude Code (explicit `"type": "websocket"`), Kotlin SDK (native), Rust SDKs (turbomcp, mcpkit), PHP SDK. **Not supported** by Claude Desktop, Cursor, VS Code, or Windsurf directly.

**Pros**:

- True full-duplex — ideal for real-time, interactive scenarios
- Lower latency than HTTP polling for high-frequency communication
- Persistent connection — no reconnection overhead per message
- Auto-reconnection support in some SDKs

**Cons**:

- **Not in the official MCP specification** — implementation varies across SDKs
- Limited client support — most major AI clients don't support it
- More complex infrastructure (WebSocket-aware load balancers, proxies)
- Harder to secure than standard HTTPS (WAF rules, inspection)
- Connection state management at scale
- No standardized auth model in MCP context

**Best use cases**: Real-time interactive tools, streaming data feeds, scenarios requiring server-initiated messages at high frequency. Generally **not recommended** for HUMMBL — Streamable HTTP covers these needs with broader client support.

---

### 3.5 Direct HTTP API (REST-like, No MCP Protocol Wrapper)

| Attribute       | Detail                                              |
| --------------- | --------------------------------------------------- |
| **Spec status** | Not MCP — this is a non-MCP access pattern          |
| **Protocol**    | HTTP REST (JSON request/response)                   |
| **Endpoint**    | Any REST path (e.g., `/v1/recommend`, `/v1/models`) |

**How users connect**: Direct HTTP calls, no MCP client needed:

```bash
curl https://api.hummbl.io/v1/recommend \
  -H 'Content-Type: application/json' \
  -d '{"problem": "How do I prioritize features?"}'
```

**Server requirements**: Standard REST API. No MCP protocol implementation needed. HUMMBL already has this via `api.hummbl.io`.

**Authentication**: API key, bearer token, or no auth (HUMMBL API is currently free/no-auth).

**Client support**: Any HTTP client (curl, Postman, application code, LangChain, CrewAI, etc.). Not accessible from MCP-native clients (Claude Desktop, etc.) without an MCP wrapper.

**Pros**:

- Simplest to implement and consume
- Universal compatibility — any HTTP client
- No MCP protocol overhead
- Easy to document and test
- Already deployed for HUMMBL

**Cons**:

- Not MCP-compatible — invisible to Claude Desktop, Cursor, VS Code MCP panels
- No capability negotiation, tool discovery, or standardized protocol
- Each consumer must hardcode API paths and schemas
- No streaming or server-initiated communication

**Best use cases**: Non-AI integrations, programmatic access from application code, simple API consumers, backward compatibility. Should be maintained alongside MCP transport, not instead of it.

---

## 4. Client Configuration Patterns

### 4.1 Claude Desktop (`claude_desktop_config.json`)

| Attribute                | Detail                                                                      |
| ------------------------ | --------------------------------------------------------------------------- |
| **Config file**          | `claude_desktop_config.json`                                                |
| **macOS path**           | `~/Library/Application Support/Claude/claude_desktop_config.json`           |
| **Windows path**         | `%APPDATA%\Claude\claude_desktop_config.json`                               |
| **Linux path**           | `~/.config/Claude/claude_desktop_config.json`                               |
| **Top-level key**        | `mcpServers`                                                                |
| **Transports supported** | stdio (via config file), Streamable HTTP + SSE (via UI "custom connectors") |
| **Reload**               | Full quit and relaunch of Claude Desktop                                    |

**stdio config**:

```json
{
  "mcpServers": {
    "hummbl": {
      "command": "npx",
      "args": ["@hummbl/mcp-server"],
      "env": {
        "API_KEY": "your-key"
      }
    }
  }
}
```

**Remote servers**: Added via Settings → Connectors → Add custom connector (UI), NOT in the JSON file. Supports OAuth 2.1 flows.

**Key notes**:

- GUI apps don't inherit shell PATH — use full paths for `command` if needed
- All file paths in `args` must be absolute
- `env` field for secrets — never hardcode in committed config
- Tools appear as hammer icon in chat input
- `.mcpb` files support one-click install (MCP bundle format)

**HUMMBL current support**: Yes — the website shows this exact config pattern for `@hummbl/mcp-server`.

---

### 4.2 Claude Code (`.mcp.json` / `~/.claude.json`)

| Attribute                | Detail                                                                          |
| ------------------------ | ------------------------------------------------------------------------------- |
| **Config files**         | `.mcp.json` (project scope), `~/.claude.json` (local + user scope)              |
| **Project scope**        | `.mcp.json` in project root — checked into version control for team sharing     |
| **Local scope**          | `~/.claude.json` under project entry — private, current project only (default)  |
| **User scope**           | `~/.claude.json` under top-level `mcpServers` — all projects                    |
| **Windows path**         | `%USERPROFILE%\.claude.json`                                                    |
| **Transports supported** | stdio, HTTP (Streamable HTTP), SSE, WebSocket                                   |
| **CLI commands**         | `claude mcp add`, `claude mcp add-json`, `claude mcp list`, `claude mcp remove` |
| **Reload**               | Automatic on new session                                                        |

**stdio config** (`.mcp.json`):

```json
{
  "mcpServers": {
    "hummbl": {
      "command": "npx",
      "args": ["@hummbl/mcp-server"],
      "env": {
        "API_KEY": "${HUMMBL_API_KEY}"
      }
    }
  }
}
```

**Streamable HTTP config**:

```json
{
  "mcpServers": {
    "hummbl-remote": {
      "type": "http",
      "url": "https://mcp.hummbl.io/mcp",
      "headers": {
        "Authorization": "Bearer ${HUMMBL_TOKEN}"
      }
    }
  }
}
```

**SSE config**:

```json
{
  "mcpServers": {
    "hummbl-sse": {
      "type": "sse",
      "url": "https://mcp.hummbl.io/sse",
      "headers": {
        "Authorization": "Bearer ${HUMMBL_TOKEN}"
      }
    }
  }
}
```

**WebSocket config**:

```json
{
  "mcpServers": {
    "hummbl-ws": {
      "type": "websocket",
      "url": "wss://mcp.hummbl.io/ws"
    }
  }
}
```

**Key notes**:

- `"type": "streamable-http"` accepted as alias for `"http"`
- Environment variable expansion: `${VAR}` and `${VAR:-default}`
- Project scope takes precedence over user scope
- `claude mcp add --scope project --transport stdio hummbl npx @hummbl/mcp-server`
- `claude mcp add --scope user --transport http hummbl-remote https://mcp.hummbl.io/mcp`
- Agent SDK: `mcpServers` option in `query()` calls, or load from `.mcp.json` via `settingSources`

**HUMMBL current support**: Yes for stdio. Website shows `npx @hummbl/mcp-server` config. No remote HTTP config documented yet.

---

### 4.3 Cursor (`.cursor/mcp.json`)

| Attribute                | Detail                                                                         |
| ------------------------ | ------------------------------------------------------------------------------ |
| **Config files**         | `.cursor/mcp.json` (project scope), `~/.cursor/mcp.json` (global)              |
| **Project scope**        | `.cursor/mcp.json` in project root — commit to git for team sharing            |
| **Global scope**         | `~/.cursor/mcp.json` (macOS/Linux), `%USERPROFILE%\.cursor\mcp.json` (Windows) |
| **Top-level key**        | `mcpServers`                                                                   |
| **Transports supported** | stdio (`command`), Streamable HTTP (`url`), SSE (`url`)                        |
| **Reload**               | Restart Cursor after saving config                                             |
| **UI**                   | Settings → Tools & MCP → Add new MCP server                                    |

**stdio config**:

```json
{
  "mcpServers": {
    "hummbl": {
      "command": "npx",
      "args": ["-y", "@hummbl/mcp-server"],
      "env": {
        "API_KEY": "${env:HUMMBL_API_KEY}"
      }
    }
  }
}
```

**Remote HTTP config**:

```json
{
  "mcpServers": {
    "hummbl-remote": {
      "url": "https://mcp.hummbl.io/mcp",
      "headers": {
        "Authorization": "Bearer ${env:HUMMBL_TOKEN}"
      }
    }
  }
}
```

**OAuth config** (static credentials):

```json
{
  "mcpServers": {
    "hummbl-oauth": {
      "url": "https://mcp.hummbl.io/mcp",
      "auth": {
        "CLIENT_ID": "your-client-id",
        "CLIENT_SECRET": "your-client-secret",
        "scopes": ["read", "write"]
      }
    }
  }
}
```

**Key notes**:

- `type` field: `"stdio"` or `"streamableHttp"` (or omit for auto-detect)
- `envFile` field: path to `.env` file for loading variables
- Variable interpolation: `${env:VAR_NAME}`
- Project-level config takes priority over global
- Also supports UI-based configuration (Settings → Tools & MCP)

**HUMMBL current support**: Yes for stdio. Config format is nearly identical to Claude Desktop.

---

### 4.4 VS Code (`.vscode/mcp.json`)

| Attribute                | Detail                                                              |
| ------------------------ | ------------------------------------------------------------------- |
| **Config files**         | `.vscode/mcp.json` (workspace), user profile `mcp.json`             |
| **Workspace**            | `.vscode/mcp.json` — commit to source control for team sharing      |
| **User profile**         | Via "MCP: Open User Configuration" command                          |
| **Top-level key**        | `servers` (NOT `mcpServers` — VS Code uses `servers`)               |
| **Transports supported** | stdio (`type: "stdio"`), HTTP (`type: "http"`), SSE (`type: "sse"`) |
| **Reload**               | Automatic detection or command palette                              |
| **IntelliSense**         | Yes — VS Code provides autocomplete for mcp.json                    |
| **Dev Containers**       | Supported via `customizations.vscode.mcp` in `devcontainer.json`    |

**stdio config** (`.vscode/mcp.json`):

```json
{
  "servers": {
    "hummbl": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "@hummbl/mcp-server"],
      "env": {
        "API_KEY": "${input:hummbl-api-key}"
      }
    }
  },
  "inputs": [
    {
      "type": "promptString",
      "id": "hummbl-api-key",
      "description": "HUMMBL API Key",
      "password": true
    }
  ]
}
```

**Remote HTTP config**:

```json
{
  "servers": {
    "hummbl-remote": {
      "type": "http",
      "url": "https://mcp.hummbl.io/mcp",
      "headers": {
        "Authorization": "Bearer ${input:hummbl-token}"
      }
    }
  }
}
```

**Key notes**:

- Uses `servers` key, not `mcpServers` (important difference from other clients)
- `inputs` array for secure credential prompts (VS Code prompts user, doesn't store in file)
- `sandbox` configuration for filesystem/network access rules (macOS/Linux only)
- `sandboxEnabled: true` for sandboxed execution
- `dev` mode with `watch` for development (auto-restart on file changes)
- `cwd` field for working directory
- Remote development: define in workspace settings or remote user settings for remote machines

**HUMMBL current support**: Yes for stdio. The `servers` key difference means HUMMBL docs need a VS Code-specific config example.

---

### 4.5 Windsurf (`mcp_config.json`)

| Attribute                | Detail                                               |
| ------------------------ | ---------------------------------------------------- |
| **Config file**          | `mcp_config.json`                                    |
| **Path (macOS/Linux)**   | `~/.codeium/windsurf/mcp_config.json`                |
| **Path (Windows)**       | `%USERPROFILE%\.codeium\windsurf\mcp_config.json`    |
| **Scope**                | Global only — NO project-level config                |
| **Top-level key**        | `mcpServers`                                         |
| **Transports supported** | stdio (`command`), Streamable HTTP/SSE (`serverUrl`) |
| **Reload**               | Windsurf watches the file and auto-reloads on change |
| **Tool limit**           | 100 tools across ALL connected servers (hard limit)  |

**stdio config**:

```json
{
  "mcpServers": {
    "hummbl": {
      "command": "npx",
      "args": ["-y", "@hummbl/mcp-server"],
      "env": {
        "API_KEY": "${env:HUMMBL_API_KEY}"
      }
    }
  }
}
```

**Remote HTTP config** (note: `serverUrl`, NOT `url`):

```json
{
  "mcpServers": {
    "hummbl-remote": {
      "serverUrl": "https://mcp.hummbl.io/mcp",
      "headers": {
        "Authorization": "Bearer ${env:HUMMBL_TOKEN}"
      }
    }
  }
}
```

**Key notes**:

- Uses `serverUrl` instead of `url` for remote servers (common gotcha — `url` is silently ignored)
- Variable interpolation: `${env:VAR_NAME}` and `${file:/path/to/file}`
- No project-level config — global only
- 100-tool hard limit across all servers
- Also has UI: MCPs icon in Cascade panel, or Settings → Cascade → MCP Servers
- Teams/admins may need to enable remote transports

**HUMMBL current support**: Yes for stdio. The `serverUrl` vs `url` difference must be documented.

---

### 4.6 CLI Direct Invocation

| Attribute     | Detail                                         |
| ------------- | ---------------------------------------------- |
| **Pattern**   | Run MCP server directly from command line      |
| **Transport** | stdio (implicit)                               |
| **Use case**  | Testing, debugging, manual interaction, piping |

**Examples**:

```bash
# Direct invocation (stdio mode)
npx @hummbl/mcp-server

# Python server
python -m hummbl_governance.mcp_server

# With environment variables
HUMMBL_API_KEY=your-key npx @hummbl/mcp-server

# Pipe a JSON-RPC request
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{...}}' | npx @hummbl/mcp-server

# Using MCP Inspector for testing
npx @modelcontextprotocol/inspector npx @hummbl/mcp-server
```

**Client support**: Any terminal. MCP Inspector for visual testing. Not a "client" per se, but a direct access pattern.

**Pros**: Quick testing, debugging, no client setup needed, scriptable
**Cons**: Not interactive for AI use, manual JSON-RPC construction, no tool discovery UI

---

### 4.7 Client Configuration Comparison Matrix

| Feature               | Claude Desktop               | Claude Code                    | Cursor                     | VS Code                  | Windsurf                     |
| --------------------- | ---------------------------- | ------------------------------ | -------------------------- | ------------------------ | ---------------------------- |
| **Config file**       | `claude_desktop_config.json` | `.mcp.json` / `~/.claude.json` | `.cursor/mcp.json`         | `.vscode/mcp.json`       | `mcp_config.json`            |
| **Config key**        | `mcpServers`                 | `mcpServers`                   | `mcpServers`               | `servers`                | `mcpServers`                 |
| **stdio**             | Yes                          | Yes                            | Yes                        | Yes                      | Yes                          |
| **Streamable HTTP**   | Via UI connectors            | `type: "http"`                 | `url` field                | `type: "http"`           | `serverUrl` field            |
| **SSE (legacy)**      | Via UI connectors            | `type: "sse"`                  | `url` field                | `type: "sse"`            | `serverUrl` field            |
| **WebSocket**         | No                           | `type: "websocket"`            | No                         | No                       | No                           |
| **Project scope**     | No                           | Yes (`.mcp.json`)              | Yes (`.cursor/mcp.json`)   | Yes (`.vscode/mcp.json`) | No                           |
| **User/global scope** | Yes                          | Yes (`~/.claude.json`)         | Yes (`~/.cursor/mcp.json`) | Yes (user profile)       | Yes (global only)            |
| **Env var expansion** | No                           | `${VAR}`, `${VAR:-default}`    | `${env:VAR}`               | `${input:id}`            | `${env:VAR}`, `${file:path}` |
| **OAuth support**     | Yes (UI connectors)          | Yes                            | Yes (static creds)         | Yes                      | Yes                          |
| **Tool limit**        | None known                   | None known                     | None known                 | None known               | 100 tools (all servers)      |
| **Auto-reload**       | No (restart app)             | Yes (new session)              | No (restart)               | Yes                      | Yes (file watch)             |
| **Dev mode**          | No                           | No                             | No                         | Yes (`dev.watch`)        | No                           |

---

## 5. Authentication & Authorization

### 5.1 OAuth 2.1 (MCP Standard for Remote Servers)

| Attribute        | Detail                                                                        |
| ---------------- | ----------------------------------------------------------------------------- |
| **Spec**         | OAuth 2.1 (IETF draft) + RFC 8414, RFC 7591, RFC 8707, RFC 6750, RFC 9728     |
| **Required for** | HTTP-based transports (Streamable HTTP, SSE)                                  |
| **NOT for**      | stdio (uses env vars for credentials)                                         |
| **Spec version** | 2025-03-26: RFC 8414 + RFC 7591. 2025-11-25: RFC 9728 + OIDC Discovery + CIMD |

**How it works**:

1. **Client attempts connection** to MCP server (`POST /mcp`)
2. **Server returns `401 Unauthorized`** with `WWW-Authenticate` header containing `resource_metadata` URL (RFC 9728)
3. **Client fetches Protected Resource Metadata (PRM)** document from the URL
4. **PRM contains** `authorization_servers` field pointing to authorization server(s)
5. **Client discovers authorization server metadata** via:
   - OAuth 2.0 Authorization Server Metadata (RFC 8414), OR
   - OpenID Connect Discovery 1.0 (2025-11-25+)
6. **Client registers** with authorization server:
   - **2025-11-25**: OAuth Client ID Metadata Documents (CIMD) — client publishes a URL with its metadata (recommended)
   - **Legacy**: Dynamic Client Registration (RFC 7591) — still MAY be supported
7. **User authenticates** via browser redirect to `/authorize` endpoint
8. **Authorization code** exchanged for access token at `/token` endpoint
9. **Client includes `resource` parameter** (RFC 8707) in auth and token requests to bind token to specific MCP server
10. **Access token** sent as Bearer token in `Authorization` header on all subsequent MCP requests

**Default endpoint paths** (when no metadata discovery):
| Endpoint | Path |
|----------|------|
| Authorization | `/authorize` |
| Token | `/token` |
| Registration | `/register` |

**Server requirements**:

- Act as OAuth 2.1 **resource server** — validate access tokens
- Serve Protected Resource Metadata document (RFC 9728)
- Include `authorization_servers` field in PRM
- Return `401` with `WWW-Authenticate: resource_metadata="..."` on unauthenticated requests
- Validate token `aud` (audience) claim matches server's URI
- **Never accept token passthrough** — tokens must be issued specifically for this server
- Include `scope` parameter in `WWW-Authenticate` for incremental consent (2025-11-25)

**2025-11-25 additions**:

- **Client ID Metadata Documents (CIMD)**: Clients publish a URL pointing to JSON describing their properties. Replaces DCR as recommended mechanism.
- **M2M OAuth**: `client_credentials` grant for machine-to-machine (headless agents, automations)
- **Enterprise IdP controls**: Cross App Access (XAA) — IdP (Okta/Entra) sees and controls which AI apps access which MCP servers
- **Default scopes**: Standardized baseline scope names
- **OIDC Discovery 1.0**: Alternative to RFC 8414 for auth server metadata

**Client support**: Claude Desktop (UI connectors), Claude Code, Cursor (static creds), VS Code, Windsurf. All major clients support OAuth for remote servers.

### 5.2 API Key / Bearer Token

| Attribute       | Detail                                           |
| --------------- | ------------------------------------------------ |
| **Spec status** | Not standardized in MCP (but widely used)        |
| **Mechanism**   | `Authorization: Bearer <token>` or custom header |

**How it works**: Client includes API key in `headers` field of config. Server validates against known keys.

**Server requirements**: Validate token, map to user/tenant, enforce rate limits.

**Pros**: Simple, no browser redirect needed, works with all clients
**Cons**: No standardized discovery, no scope-based permissions, manual key distribution

**HUMMBL context**: The HUMMBL REST API (`api.hummbl.io`) is currently free/no-auth. If MCP servers need auth, API keys are the simplest starting point before full OAuth.

### 5.3 Environment Variables (stdio only)

| Attribute       | Detail                       |
| --------------- | ---------------------------- |
| **Spec status** | Standard for stdio transport |
| **Mechanism**   | `env` field in client config |

**How it works**: Client passes environment variables to server process at spawn time.

```json
{
  "mcpServers": {
    "hummbl": {
      "command": "npx",
      "args": ["@hummbl/mcp-server"],
      "env": {
        "HUMMBL_API_KEY": "your-key",
        "HUMMBL_API_URL": "https://api.hummbl.io"
      }
    }
  }
}
```

**Security**: Credentials never leave the machine. Server inherits client's process environment. As secure as the client process itself.

**Best practice**: Use variable expansion (`${HUMMBL_API_KEY}`) in shared configs so secrets aren't committed to version control.

### 5.4 Cloudflare Access (for Cloudflare Workers deployments)

| Attribute       | Detail                                                     |
| --------------- | ---------------------------------------------------------- |
| **Mechanism**   | Cloudflare Access as OAuth provider in front of MCP server |
| **Integration** | `workers-oauth-provider` library wraps Worker code         |

**How it works**: Cloudflare Access handles the OAuth flow. The `OAuthProvider` class wraps the MCP server handler:

```typescript
export default new OAuthProvider({
  apiHandlers: { "/mcp": MyMCP.serve("/mcp") },
  authorizeEndpoint: "/authorize",
  tokenEndpoint: "/token",
  clientRegistrationEndpoint: "/register",
  defaultHandler: AuthHandler,
});
```

**Pros**: Turnkey OAuth for Cloudflare-hosted MCP servers, integrates with Cloudflare Access identity providers (Google, GitHub, SAML, etc.)
**Cons**: Cloudflare-specific — only works for Workers deployments

---

## 6. Session Management

### 6.1 Stateful Sessions (Current Spec)

| Attribute     | Detail                                                                                |
| ------------- | ------------------------------------------------------------------------------------- |
| **Header**    | `Mcp-Session-Id`                                                                      |
| **Lifecycle** | Created at `initialize`, included on all subsequent requests, terminated at shutdown  |
| **ID format** | Globally unique, cryptographically secure (UUID, JWT, or hash). ASCII 0x21-0x7E only. |

**How it works**:

1. Client sends `initialize` request
2. Server responds with `Mcp-Session-Id` header (if it wants sessions)
3. Client MUST include this header on all subsequent requests
4. Server tracks session state in memory or distributed store
5. Client sends `DELETE` to `/mcp` to terminate session (2025-11-25+)

**When sessions are needed**:

- Server needs to send requests TO the client (sampling, elicitation, roots)
- Server pushes unsolicited notifications
- Per-client state must be maintained across requests
- Tool execution depends on prior call state

**When sessions are NOT needed (stateless mode)**:

- Tools are pure functions (no cross-call state)
- No server-to-client requests
- No unsolicited notifications
- Each request is independent

**Recommendation from C# SDK docs**: "We recommend most servers disable sessions entirely by setting `Stateless` to `true`. Stateless mode avoids the complexity, memory overhead, and deployment constraints that come with sessions."

### 6.2 Stateless Mode (Recommended Default)

| Attribute          | Detail                                                               |
| ------------------ | -------------------------------------------------------------------- |
| **Session header** | None — no `Mcp-Session-Id`                                           |
| **Each request**   | Independent, self-contained                                          |
| **Scaling**        | Trivial — works behind any load balancer, no session affinity needed |
| **Serverless**     | Compatible — no in-memory state to lose                              |

**How to implement**: Simply do NOT include `Mcp-Session-Id` in the `initialize` response. Each POST to `/mcp` is handled independently.

### 6.3 Future: Sessionless MCP (Draft SEPs)

**SEP-2575** (Make MCP Stateless): Proposes removing the `initialize` handshake entirely. Each request carries its own protocol version, client identity, and capabilities via headers. No connection lifecycle.

**SEP-2567** (Sessionless MCP via Explicit State Handles): Proposes removing `Mcp-Session-Id` from the protocol. Servers that need cross-call state use explicit handles (e.g., `create_basket()` returns `basket_id`, passed to `add_item(basket_id, ...)`). The model threads state, not the protocol.

**Impact on HUMMBL**: These SEPs are draft/proposal stage. Design HUMMBL's MCP servers to be stateless now (no session dependency), and use explicit state handles in tool design (e.g., `analysis_id` returned from `analyze_problem`, passed to `apply_transformation`). This makes future migration trivial.

### 6.4 Session Management Comparison

| Mode                   | Session Header   | State                 | Scaling           | Serverless | Server→Client | Notifications |
| ---------------------- | ---------------- | --------------------- | ----------------- | ---------- | ------------- | ------------- |
| **Stateless**          | None             | None                  | Trivial           | Yes        | No            | No            |
| **Stateful**           | `Mcp-Session-Id` | In-memory/distributed | Requires affinity | No         | Yes           | Yes           |
| **Draft: Sessionless** | Removed          | Explicit handles      | Trivial           | Yes        | Via MRTR      | Via MRTR      |

---

## 7. Deployment Patterns

### 7.1 Local (stdio Subprocess)

| Attribute            | Detail                                                       |
| -------------------- | ------------------------------------------------------------ |
| **Transport**        | stdio                                                        |
| **Server lifecycle** | Managed by client (spawned on connect, killed on disconnect) |
| **Scaling**          | 1:1 (one server per client)                                  |
| **Auth**             | Environment variables                                        |
| **Infrastructure**   | None — runs on user's machine                                |

**HUMMBL current**: All 11 servers support this. TypeScript via `npx @hummbl/mcp-server`, Python via `python -m <module>` or `hummbl-governance-mcp`.

**Best for**: Individual developers, personal AI assistants, tools accessing local resources, development/testing

### 7.2 Remote (Cloudflare Workers)

| Attribute            | Detail                                                        |
| -------------------- | ------------------------------------------------------------- |
| **Transport**        | Streamable HTTP                                               |
| **Server lifecycle** | Always-on (edge deployment)                                   |
| **Scaling**          | Automatic (Cloudflare edge network)                           |
| **Auth**             | OAuth 2.1 (via `workers-oauth-provider`) or Cloudflare Access |
| **Infrastructure**   | Cloudflare Workers + optional Durable Objects                 |

**Implementation options** (Cloudflare Agents SDK):

| Approach                            | Stateful? | Durable Objects? | Best for                                       |
| ----------------------------------- | --------- | ---------------- | ---------------------------------------------- |
| `createMcpHandler()`                | No        | No               | Stateless tools, simplest setup                |
| `McpAgent` class                    | Yes       | Yes              | Stateful tools, per-session state, elicitation |
| Raw `StreamableHTTPServerTransport` | No        | No               | Full control, no SDK dependency                |

**Stateless example**:

```typescript
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { createMcpHandler } from "agents/mcp";

const server = new McpServer({ name: "hummbl-base120", version: "1.0.0" });
// Register tools...
export default createMcpHandler(server);
```

**Stateful example** (with OAuth):

```typescript
import { McpAgent } from "agents/mcp";
import { OAuthProvider } from "@cloudflare/workers-oauth-provider";

class MyMCP extends McpAgent {
  server = new McpServer({ name: "hummbl-base120", version: "1.0.0" });
  async init() {
    /* register tools */
  }
}

export default new OAuthProvider({
  apiHandlers: { "/mcp": MyMCP.serve("/mcp") },
  authorizeEndpoint: "/authorize",
  tokenEndpoint: "/token",
  clientRegistrationEndpoint: "/register",
  defaultHandler: AuthHandler,
});
```

**Key Cloudflare features**:

- WebSocket Hibernation: stateful MCP servers sleep during inactive periods, preserving state
- Stream resumability: `EventStore` + `Last-Event-ID` header for SSE replay
- `X-Accel-Buffering: no` header for immediate SSE delivery
- Edge idle-stream watchdog (~5 min): Durable Objects keep streams alive

**HUMMBL current**: The TypeScript server has a Cloudflare Workers deployment (`api.hummbl.io`), but it's a direct REST API, not a compliant MCP Streamable HTTP transport. The `wrangler.toml` in `hummbl-production/api/` deploys the HUMMBL REST API, not an MCP server.

### 7.3 Remote (Containerized — Docker/Kubernetes)

| Attribute            | Detail                                                   |
| -------------------- | -------------------------------------------------------- |
| **Transport**        | Streamable HTTP                                          |
| **Server lifecycle** | Container orchestration (K8s Deployment, Docker Compose) |
| **Scaling**          | Horizontal (2-3 replicas for HA)                         |
| **Auth**             | OAuth 2.1, API key, mTLS                                 |
| **Infrastructure**   | Docker/K8s cluster, ingress controller, TLS termination  |

**Docker stdio**:

```bash
docker run --rm -i -v $(pwd)/data:/data hummbl/mcp-server:latest
```

**Docker Streamable HTTP**:

```bash
docker run -d -p 8080:8080 -e MCP_TRANSPORT=http hummbl/mcp-server:latest
```

**Docker Compose**:

```yaml
services:
  mcp-server:
    build: .
    ports:
      - "8000:8000"
    environment:
      - MCP_TRANSPORT=http
      - DATABASE_URL=postgresql://app:pass@db:5432/app
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/mcp"]
    restart: unless-stopped
```

**Best for**: Enterprise deployments, on-premises, multi-tenant, when Cloudflare isn't suitable

### 7.4 Hybrid (Local stdio + Remote HTTP)

| Attribute               | Detail                                         |
| ----------------------- | ---------------------------------------------- |
| **Pattern**             | Server supports both stdio and Streamable HTTP |
| **Transport selection** | Determined by how server is invoked            |
| **Auth**                | env vars for stdio, OAuth/API key for HTTP     |

**Implementation**: Server checks at startup whether it's running as a subprocess (stdin is a pipe) or standalone process:

- If stdin is a pipe → run stdio transport
- If standalone → start HTTP server on configured port

**Example pattern**:

```typescript
if (process.stdin.isTTY) {
  // Standalone mode — start HTTP server
  startHttpServer();
} else {
  // Subprocess mode — use stdio transport
  startStdioServer();
}
```

**Best for**: Servers that need to work both locally (for individual developers) and remotely (for teams/production). This is the ideal target for HUMMBL servers.

### 7.5 Serverless (with SSE Proxy)

| Attribute     | Detail                                                                        |
| ------------- | ----------------------------------------------------------------------------- |
| **Challenge** | SSE requires long-lived connections; serverless functions have timeout limits |
| **Solution**  | Thin SSE proxy on persistent compute + tool execution on serverless           |

**Architecture**:

```
Client ← SSE → [Persistent Proxy/VM] → [Serverless Function] → [Database/API]
```

**Best for**: Cost-optimized deployments where idle compute is expensive. Generally not needed for HUMMBL if using Cloudflare Workers (which handle SSE natively via Durable Objects).

---

## 8. Bridging & Adapter Patterns

### 8.1 `mcp-remote` (stdio-to-Remote Bridge)

| Attribute     | Detail                                                           |
| ------------- | ---------------------------------------------------------------- |
| **Package**   | `mcp-remote` (npm) or `@automattic/mcp-remote`                   |
| **Purpose**   | Lets stdio-only clients connect to remote MCP servers with OAuth |
| **Mechanism** | Runs as local stdio server, proxies to remote HTTP/SSE server    |

**How it works**: The client thinks it's connecting to a local stdio server. `mcp-remote` translates stdio JSON-RPC to HTTP requests to the remote server, handling OAuth flows in a browser popup.

**Config** (for stdio-only clients like Claude Desktop):

```json
{
  "mcpServers": {
    "hummbl-remote": {
      "command": "npx",
      "args": ["mcp-remote", "https://mcp.hummbl.io/mcp"]
    }
  }
}
```

**Transport strategies**:

```bash
npx mcp-remote https://example.com/mcp --transport http-only
npx mcp-remote https://example.com/sse --transport sse-only
npx mcp-remote https://example.com/mcp --transport http-first  # default
npx mcp-remote https://example.com/sse --transport sse-first
```

**Features**:

- OAuth 2.1 support (browser popup for auth)
- `--enable-proxy` for outbound HTTP(S) proxy
- Auto-detects Streamable HTTP vs SSE
- Works with Claude Desktop, Cursor, and any stdio-only client

**HUMMBL relevance**: **Critical**. This is the bridge that lets stdio-only clients reach HUMMBL's remote MCP servers without the client needing native HTTP support. Every HUMMBL remote server should be testable via `mcp-remote`.

### 8.2 `mcp-stdio` (Bidirectional Gateway)

| Attribute   | Detail                                                          |
| ----------- | --------------------------------------------------------------- |
| **Package** | `mcp-stdio` (GitHub: shigechika/mcp-stdio)                      |
| **Purpose** | stdio-to-HTTP gateway AND HTTP-to-stdio gateway (bidirectional) |

**Client mode** (stdio → HTTP): Same as `mcp-remote` — bridges local clients to remote servers.

**Serve mode** (HTTP → stdio): Exposes a local stdio MCP server as a Streamable HTTP endpoint:

```bash
mcp-stdio serve --listen 127.0.0.1:9000 -- my-mcp-server --stdio
```

This serves:

- Streamable HTTP on `/mcp`
- Legacy SSE on `/sse` + `/messages`
- Health on `/health`

**HUMMBL relevance**: The `serve` mode can instantly expose any of HUMMBL's 10 Python stdio servers as HTTP endpoints without modifying the Python code. Useful for testing and gradual migration.

### 8.3 `ferry` (Transparent MCP Proxy)

| Attribute   | Detail                                                     |
| ----------- | ---------------------------------------------------------- |
| **Package** | `ferry` (GitHub: jpetrucciani/ferry)                       |
| **Purpose** | stdio/sse/streamable HTTP transport proxy and tunnel       |
| **Modes**   | Client mode (stdio→HTTP), Serve mode (stdio→HTTP or relay) |

**Features**:

- `auto` transport mode: probes Streamable HTTP first, falls back to SSE
- `MCP-Session-Id` and `MCP-Protocol-Version` handling
- Best-effort SSE resume via `Last-Event-ID`
- SOCKS5 proxy support
- TOML configuration

**Serve mode**:

```bash
ferry serve --listen 127.0.0.1:9000 stdio -- my-mcp-server --stdio
```

### 8.4 Docker MCP Gateway

| Attribute     | Detail                                                                        |
| ------------- | ----------------------------------------------------------------------------- |
| **Provider**  | Docker Desktop                                                                |
| **Purpose**   | Single MCP server that dynamically serves containerized tools                 |
| **Mechanism** | Gateway MCP server routes to Docker containers running individual MCP servers |

**How it works**: Instead of configuring multiple MCP servers in client config, connect one "Docker" MCP server. Docker Desktop UI manages which tools are available. Tools run in isolated containers.

**HUMMBL relevance**: HUMMBL could publish Docker images for each MCP server, making them available through Docker's MCP Catalog. This provides sandboxed isolation and easy discovery.

---

## 9. Security Considerations

### 9.1 Transport Security by Type

| Transport           | Attack Surface                                               | Mitigation                                                                                                               |
| ------------------- | ------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------ |
| **stdio**           | Process boundary — compromised pipe leaks all tool calls     | Run in isolated process sessions, restricted filesystem access. Only connect to trusted servers.                         |
| **Streamable HTTP** | Network endpoint — any network-adjacent attacker can connect | TLS everywhere. Validate `Origin` header (DNS rebinding). Bind to localhost when local. Authentication on all endpoints. |
| **SSE (legacy)**    | Persistent HTTP connection                                   | TLS, strict CORS, origin validation. Same as Streamable HTTP.                                                            |
| **WebSocket**       | Persistent WS connection                                     | WSS (TLS), authentication during upgrade handshake, validate Origin.                                                     |

### 9.2 Critical Security Requirements (from MCP Spec)

1. **Origin header validation** (Streamable HTTP): Servers MUST validate `Origin` header on all incoming connections to prevent DNS rebinding attacks.

2. **Localhost binding**: When running locally, servers SHOULD bind to `127.0.0.1` only, not `0.0.0.0`.

3. **Authentication for remote**: All remote (HTTP-based) servers MUST implement authentication. OAuth 2.1 is the standard.

4. **No token passthrough**: Servers MUST NOT accept tokens issued for other services. The MCP spec explicitly forbids this. If a client passes a GitHub token to your MCP server to use with the GitHub API, that's a security violation. The server must issue its own tokens.

5. **Token audience validation**: Validate that the `aud` (audience) claim in access tokens matches your server's URI. Reject with `403` if not.

6. **SSRF prevention**: Servers that accept URL parameters MUST validate the resolved IP address at connection time (not parse time) to resist DNS rebinding. Block RFC 1918 ranges, loopback, link-local.

7. **Network egress restrictions**: Server processes SHOULD run with egress restrictions enforced at the OS level.

8. **SEP-1024 (2025-11-25)**: Client security requirements for local server installation — clients must apply safer install behavior for stdio servers.

### 9.3 Security Best Practices for HUMMBL

| Concern                 | Recommendation                                                                                                                                                                         |
| ----------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **stdio servers**       | Audit all server startup commands. Review for suspicious patterns (`sudo`, `rm`, network ops to unknown hosts, access to `~/.ssh/`). HUMMBL servers are open-source — users can audit. |
| **Remote servers**      | Implement OAuth 2.1 with Cloudflare Access or `workers-oauth-provider`. Never expose without auth.                                                                                     |
| **API keys**            | If using API keys instead of full OAuth, use `Authorization: Bearer` header, validate on every request, rotate regularly.                                                              |
| **CORS**                | Set strict CORS policies on remote MCP endpoints. Only allow known client origins.                                                                                                     |
| **Rate limiting**       | Implement rate limiting on remote endpoints to prevent abuse.                                                                                                                          |
| **Input validation**    | All tool inputs must be validated against their JSON schema. HUMMBL's governance module has input validation infrastructure.                                                           |
| **Output sanitization** | Validate outputs before returning to client. HUMMBL has `validateOutput` in `security.ts`.                                                                                             |
| **Audit logging**       | Log all tool calls with timestamps, provenance, and signatures. HUMMBL's governance bus and audit log support this.                                                                    |

---

## 10. Gap Analysis: HUMMBL Current State

### 10.1 Current Inventory

| Server                         | Language   | Transport | Remote?                                          | Auth     | Session | OAuth |
| ------------------------------ | ---------- | --------- | ------------------------------------------------ | -------- | ------- | ----- |
| `@hummbl/mcp-server` (Base120) | TypeScript | stdio     | Cloudflare Workers (REST API, NOT MCP transport) | None     | No      | No    |
| `hummbl-governance-mcp`        | Python     | stdio     | No                                               | env vars | No      | No    |
| `hummbl-compliance-mcp`        | Python     | stdio     | No                                               | env vars | No      | No    |
| `hummbl-sandbox-mcp`           | Python     | stdio     | No                                               | env vars | No      | No    |
| `hummbl-identity-mcp`          | Python     | stdio     | No                                               | env vars | No      | No    |
| `hummbl-agent-monitor-mcp`     | Python     | stdio     | No                                               | env vars | No      | No    |
| `hummbl-reasoning-mcp`         | Python     | stdio     | No                                               | env vars | No      | No    |
| `hummbl-physical-mcp`          | Python     | stdio     | No                                               | env vars | No      | No    |
| `hummbl-base120-mcp`           | Python     | stdio     | No                                               | env vars | No      | No    |
| `hummbl-bif-mcp`               | Python     | stdio     | No                                               | env vars | No      | No    |
| `hummbl-utf-mcp`               | Python     | stdio     | No                                               | env vars | No      | No    |

### 10.2 Gap Matrix

| Capability                             | Spec Standard          | HUMMBL TS                  | HUMMBL Python | Gap Severity        |
| -------------------------------------- | ---------------------- | -------------------------- | ------------- | ------------------- |
| stdio transport                        | Required               | Yes                        | Yes           | None                |
| Streamable HTTP transport              | Standard (2025-03-26)  | No (has REST API, not MCP) | No            | **CRITICAL**        |
| HTTP+SSE (legacy)                      | Deprecated             | No                         | No            | Low (skip)          |
| WebSocket                              | Non-standard           | No                         | No            | Low (skip)          |
| OAuth 2.1                              | Required for remote    | No                         | No            | **HIGH**            |
| Session management                     | Optional               | No                         | No            | Medium              |
| Stateless mode                         | Recommended            | N/A                        | N/A           | Low (design for it) |
| `Mcp-Protocol-Version` header          | Required (2025-06-18+) | No                         | No            | Medium              |
| `Mcp-Session-Id` header                | Optional               | No                         | No            | Low                 |
| Protected Resource Metadata (RFC 9728) | Required (2025-11-25)  | No                         | No            | **HIGH**            |
| Origin header validation               | Required               | No                         | No            | **HIGH** (security) |
| Tool icons (2025-11-25)                | Optional               | No                         | No            | Low                 |
| Tasks primitive (2025-11-25)           | Experimental           | No                         | No            | Low                 |
| Elicitation support                    | Optional               | No                         | No            | Medium              |
| `mcp-remote` compatibility             | Bridge pattern         | Untested                   | Untested      | **HIGH**            |
| Cloudflare Agents SDK integration      | Deployment             | No (uses raw Hono)         | N/A           | **HIGH**            |
| Docker containerization                | Deployment             | No                         | No            | Medium              |
| Client-specific config docs            | Documentation          | Claude Desktop only        | None          | **HIGH**            |

### 10.3 Key Findings

1. **The TypeScript server's Cloudflare Workers deployment is NOT an MCP server.** It's a REST API (`api.hummbl.io`) built with Hono. It does not implement the MCP Streamable HTTP transport, JSON-RPC, or capability negotiation. Users cannot connect Claude Desktop, Cursor, or any MCP client to it as a remote MCP server.

2. **No server implements the MCP Streamable HTTP transport.** This is the current standard for remote MCP access (since March 2025). Without it, HUMMBL servers are invisible to remote clients, cloud deployments, and multi-user scenarios.

3. **No server implements OAuth 2.1.** The MCP spec requires OAuth for remote servers. Without it, any remote deployment would be unauthenticated (acceptable for HUMMBL's free API, but not for governance/compliance servers that may handle sensitive data).

4. **Documentation only covers Claude Desktop stdio config.** No docs for Claude Code, Cursor, VS Code, Windsurf, or remote access patterns. The website shows one config snippet for `claude_desktop_config.json`.

5. **Python servers have no path to remote deployment.** They are stdio-only with no HTTP transport layer. The `mcp-stdio serve` bridge or `ferry serve` could expose them without code changes, but this is undocumented.

6. **No `mcp-remote` testing.** Even if remote servers existed, the bridge for stdio-only clients hasn't been validated.

7. **The wargame finding [R1-F3]** identified that the Python MCP server entry point (`hummbl-governance-mcp = "mcp_server:main"`) has path ambiguity that may cause launch failures in some installation scenarios.

---

## 11. Recommendations

### 11.1 Implementation Priority Order

#### Phase 1: Foundation (Immediate — 1-2 weeks)

**R1. Implement Streamable HTTP on TypeScript server via Cloudflare Agents SDK**

The `@hummbl/mcp-server` should use `McpAgent.serve("/mcp")` or `createMcpHandler()` to expose a compliant MCP Streamable HTTP endpoint at `mcp.hummbl.io/mcp` (or `api.hummbl.io/mcp`).

```typescript
// Target implementation
import { McpAgent } from "agents/mcp";
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";

class HummblMCP extends McpAgent {
  server = new McpServer({
    name: "hummbl-base120",
    version: "1.0.0",
  });

  async init() {
    // Register existing tools: select_model, apply_transformation, analyze_problem
    // Register existing resources: models://all, models://by-transformation, etc.
    // Register existing prompts: problem_decomposition
  }
}

export default HummblMCP.serve("/mcp");
```

This gives:

- Compliant MCP Streamable HTTP transport
- Works with Claude Desktop (custom connectors), Claude Code (`type: "http"`), Cursor, VS Code, Windsurf
- Cloudflare edge deployment with automatic scaling
- SSE streaming support built-in
- Optional Durable Objects for stateful sessions

**Effort**: Medium. The tools/resources/prompts already exist in the stdio implementation — they need to be registered on the McpServer instance instead of (or in addition to) the stdio transport.

**R2. Maintain stdio support (hybrid mode)**

The server should support both stdio and HTTP. At startup, detect whether running as subprocess or standalone:

```typescript
if (process.stdin.isTTY) {
  // Standalone — serve HTTP
  export default HummblMCP.serve("/mcp");
} else {
  // Subprocess — serve stdio
  const transport = new StdioServerTransport();
  await server.connect(transport);
}
```

**R3. Document client-specific configurations**

Create config snippets for ALL major clients:

| Client         | Config file                  | Key difference                                         |
| -------------- | ---------------------------- | ------------------------------------------------------ |
| Claude Desktop | `claude_desktop_config.json` | `mcpServers` key, remote via UI                        |
| Claude Code    | `.mcp.json`                  | `type: "http"` for remote                              |
| Cursor         | `.cursor/mcp.json`           | `url` field for remote                                 |
| VS Code        | `.vscode/mcp.json`           | `servers` key (not `mcpServers`), `inputs` for secrets |
| Windsurf       | `mcp_config.json`            | `serverUrl` (not `url`), global only                   |

Add these to the HUMMBL website setup section and README.

**R4. Test `mcp-remote` compatibility**

Verify that `npx mcp-remote https://mcp.hummbl.io/mcp` works from Claude Desktop. This bridges stdio-only clients to the new remote endpoint.

```json
{
  "mcpServers": {
    "hummbl-remote": {
      "command": "npx",
      "args": ["mcp-remote", "https://mcp.hummbl.io/mcp"]
    }
  }
}
```

#### Phase 2: Authentication & Python Bridge (2-4 weeks)

**R5. Add OAuth 2.1 to the TypeScript remote server**

Use Cloudflare's `workers-oauth-provider` library:

```typescript
export default new OAuthProvider({
  apiHandlers: { "/mcp": HummblMCP.serve("/mcp") },
  authorizeEndpoint: "/authorize",
  tokenEndpoint: "/token",
  clientRegistrationEndpoint: "/register",
  defaultHandler: AuthHandler,
});
```

This provides:

- Full OAuth 2.1 flow with browser-based auth
- Protected Resource Metadata (RFC 9728)
- Token validation with audience checking
- Integration with Cloudflare Access identity providers

**Decision needed**: Should the Base120 server require auth? Currently the REST API is free/no-auth. Options:

- Keep Base120 remote server authless (free public service), add auth only to governance/compliance servers
- Add optional auth with anonymous tier for Base120

**R6. Expose Python servers via `mcp-stdio serve` or `ferry serve`**

Without modifying Python code, expose each Python stdio server as an HTTP endpoint:

```bash
# Using mcp-stdio
mcp-stdio serve --listen 127.0.0.1:9001 -- hummbl-governance-mcp

# Using ferry
ferry serve --listen 127.0.0.1:9001 stdio -- hummbl-governance-mcp
```

For production, deploy these bridge processes alongside the Python servers in Docker containers or as Cloudflare Workers proxying to a Python backend.

**R7. Implement Origin header validation and security headers**

Add to all remote MCP endpoints:

- `Origin` header validation (DNS rebinding prevention)
- Strict CORS policies
- Rate limiting
- `X-Accel-Buffering: no` on SSE responses
- TLS everywhere (Cloudflare handles this)

#### Phase 3: Python Native HTTP (1-2 months)

**R8. Add Streamable HTTP transport to Python MCP servers**

Use the `mcp` Python SDK's `FastMCP` or direct `StreamableHTTPServerTransport`:

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("hummbl-governance")

@mcp.tool()
def kill_switch_status() -> dict:
    """Get current kill switch status."""
    return get_kill_switch_status()

# Run as stdio (default)
mcp.run()

# Or run as HTTP
# mcp.run(transport="streamable-http", host="0.0.0.0", port=8000)
```

Priority order for Python servers:

1. `hummbl-governance-mcp` — most likely to need remote access (multi-agent governance)
2. `hummbl-compliance-mcp` — enterprise compliance needs remote access
3. `hummbl-identity-mcp` — identity management needs remote access
4. `hummbl-reasoning-mcp` — reasoning tools useful remotely
5. Remaining servers as needed

**R9. Containerize all servers**

Create Dockerfiles for each server:

- Multi-stage builds for minimal image size
- Support both stdio (`docker run -i`) and HTTP (`docker run -p 8080:8080`) modes
- Health checks for HTTP mode
- Publish to Docker Hub / GitHub Container Registry

**R10. Publish to Docker MCP Catalog**

Package servers as Docker MCP tools for discovery through Docker Desktop's MCP gateway. This provides sandboxed isolation and easy installation for Docker users.

#### Phase 4: Advanced Features (Future)

**R11. Add elicitation support** — For governance/compliance servers that need to ask users for input during tool execution. Requires stateful sessions (McpAgent with Durable Objects).

**R12. Implement Tasks primitive (experimental)** — For long-running compliance audits, governance checks, or multi-step reasoning workflows. The 2025-11-25 spec introduced Tasks as an experimental feature for async/long-running operations.

**R13. Add tool icons** — The 2025-11-25 spec allows servers to expose icons for tools, resources, and prompts. Improves UX in client UIs.

**R14. Design for stateless MCP (future-proofing)** — Follow SEP-2567 patterns: use explicit state handles in tool design (e.g., `analysis_id` returned from one tool, passed to another) rather than relying on session state. This makes migration to the future stateless protocol trivial.

**R15. Consider WebSocket transport** — Only if a specific use case requires high-frequency, full-duplex communication. Low priority — Streamable HTTP covers most needs.

### 11.2 Decision Matrix: Which Patterns to Implement

| Pattern                  | Implement?           | Priority        | Rationale                                                      |
| ------------------------ | -------------------- | --------------- | -------------------------------------------------------------- |
| stdio                    | Already have         | Maintain        | Universal baseline. All servers must keep this.                |
| Streamable HTTP (TS)     | **Yes**              | P1 (immediate)  | Current MCP standard. Unlocks remote access for all clients.   |
| Streamable HTTP (Python) | **Yes**              | P3 (1-2 months) | Needed for governance/compliance/identity remote access.       |
| HTTP+SSE (legacy)        | **No**               | Skip            | Deprecated. Not worth implementing.                            |
| WebSocket                | **No**               | Skip            | Not in spec, limited client support. Streamable HTTP suffices. |
| Direct HTTP API          | Already have         | Maintain        | `api.hummbl.io` REST API stays as-is for non-MCP consumers.    |
| OAuth 2.1                | **Yes**              | P2              | Required for remote servers per spec. Use Cloudflare Access.   |
| `mcp-remote` bridge      | **Yes**              | P1              | Critical for stdio-only client compatibility.                  |
| `mcp-stdio serve` bridge | **Yes**              | P2              | Quick path to expose Python servers without code changes.      |
| Docker containerization  | **Yes**              | P3              | Enterprise deployment, isolation, Docker MCP Catalog.          |
| Session management       | **Optional**         | P4              | Only if elicitation or server-to-client requests needed.       |
| Stateless mode           | **Yes** (by default) | P1              | Design all servers stateless. Use explicit state handles.      |
| Tasks primitive          | **Maybe**            | P4              | Experimental. Monitor spec stability before implementing.      |
| Elicitation              | **Maybe**            | P4              | Only if governance/compliance servers need user input.         |

### 11.3 Target Architecture

```
                    ┌─────────────────────────────────────────────────┐
                    │              HUMMBL MCP Server Fleet             │
                    │                                                 │
  Claude Desktop    │  ┌─────────────┐     ┌─────────────────────┐   │
  (stdio)  ────────►│  │ @hummbl/     │     │  hummbl-governance   │   │
                    │  │ mcp-server   │     │  -mcp (Python)       │   │
  Claude Code       │  │ (TypeScript) │     │  + 9 other Python    │   │
  (stdio)  ────────►│  │              │     │  servers              │   │
                    │  │ stdio + HTTP │     │  stdio (+ HTTP P3)   │   │
  Cursor            │  └──────┬───────┘     └──────────┬───────────┘   │
  (stdio)  ────────►│         │                        │               │
                    │         │                        │               │
  VS Code           │  ┌──────▼────────────────────────▼───────────┐  │
  (stdio)  ────────►│  │         Cloudflare Workers Edge            │  │
                    │  │  mcp.hummbl.io/mcp (Streamable HTTP)       │  │
  Windsurf          │  │  OAuth 2.1 via workers-oauth-provider      │  │
  (stdio)  ────────►│  │  Stateless (default) / Stateful (Durable)  │  │
                    │  └───────────────────┬───────────────────────┘  │
  Any client        │                      │                          │
  (remote)  ───────►│                      │                          │
                    │                      │                          │
  stdio-only        │  ┌───────────────────▼───────────────────────┐  │
  clients    ──────►│  │  mcp-remote bridge (npx mcp-remote URL)    │  │
  (via bridge)      │  └───────────────────────────────────────────┘  │
                    │                                                 │
  REST consumers    │  ┌───────────────────────────────────────────┐  │
  (non-MCP) ───────►│  │  api.hummbl.io (existing REST API)         │  │
                    │  └───────────────────────────────────────────┘  │
                    └─────────────────────────────────────────────────┘
```

---

## 12. Appendix: Quick Reference Tables

### 12.1 Transport Quick Reference

| Transport       | Spec Status             | Endpoint(s)          | Direction                       | Stateless? | Multi-client | Auth                 |
| --------------- | ----------------------- | -------------------- | ------------------------------- | ---------- | ------------ | -------------------- |
| stdio           | Standard                | stdin/stdout         | Bidirectional                   | N/A (1:1)  | No           | env vars             |
| Streamable HTTP | Standard (2025-03-26)   | `/mcp` (POST+GET)    | Request-response + optional SSE | Yes        | Yes          | OAuth 2.1            |
| HTTP+SSE        | Deprecated (2025-03-26) | `/sse` + `/messages` | Half-duplex                     | No         | Yes          | OAuth 2.1            |
| WebSocket       | Non-standard            | `ws://` or `wss://`  | Full-duplex                     | No         | Yes          | Token (non-standard) |

### 12.2 Client Config File Locations

| Client                | File                         | macOS/Linux                             | Windows                                           |
| --------------------- | ---------------------------- | --------------------------------------- | ------------------------------------------------- |
| Claude Desktop        | `claude_desktop_config.json` | `~/Library/Application Support/Claude/` | `%APPDATA%\Claude\`                               |
| Claude Code (project) | `.mcp.json`                  | Project root                            | Project root                                      |
| Claude Code (user)    | `~/.claude.json`             | `~/.claude.json`                        | `%USERPROFILE%\.claude.json`                      |
| Cursor (project)      | `mcp.json`                   | `.cursor/mcp.json`                      | `.cursor\mcp.json`                                |
| Cursor (global)       | `mcp.json`                   | `~/.cursor/mcp.json`                    | `%USERPROFILE%\.cursor\mcp.json`                  |
| VS Code (workspace)   | `mcp.json`                   | `.vscode/mcp.json`                      | `.vscode\mcp.json`                                |
| VS Code (user)        | `mcp.json`                   | User profile dir                        | User profile dir                                  |
| Windsurf              | `mcp_config.json`            | `~/.codeium/windsurf/mcp_config.json`   | `%USERPROFILE%\.codeium\windsurf\mcp_config.json` |

### 12.3 Remote Server Config by Client

| Client         | Key          | Field for URL       | Type field                              | Notes                                    |
| -------------- | ------------ | ------------------- | --------------------------------------- | ---------------------------------------- |
| Claude Desktop | `mcpServers` | N/A (UI connectors) | N/A                                     | Remote servers via Settings → Connectors |
| Claude Code    | `mcpServers` | `url`               | `"type": "http"` or `"streamable-http"` | Also supports `"sse"` and `"websocket"`  |
| Cursor         | `mcpServers` | `url`               | Omit or `"streamableHttp"`              | OAuth via `auth` object                  |
| VS Code        | `servers`    | `url`               | `"type": "http"`                        | Uses `servers` not `mcpServers`          |
| Windsurf       | `mcpServers` | `serverUrl`         | Omit                                    | Uses `serverUrl` not `url`               |

### 12.4 OAuth 2.1 Spec References

| RFC/Spec             | Purpose                                | Required?                      |
| -------------------- | -------------------------------------- | ------------------------------ |
| OAuth 2.1 (draft-13) | Core authorization protocol            | YES                            |
| RFC 8414             | Authorization Server Metadata          | YES (or OIDC Discovery)        |
| RFC 9728             | Protected Resource Metadata            | YES (2025-11-25+)              |
| RFC 7591             | Dynamic Client Registration            | MAY (legacy, CIMD preferred)   |
| RFC 8707             | Resource Indicators (audience binding) | YES                            |
| RFC 6750             | Bearer Token Usage                     | YES                            |
| RFC 7662             | Token Introspection                    | Optional                       |
| OIDC Discovery 1.0   | Alternative to RFC 8414                | YES (alternative, 2025-11-25+) |
| CIMD (SEP-991)       | Client ID Metadata Documents           | Recommended (2025-11-25+)      |

### 12.5 MCP Protocol Version Timeline

```
2024-11-05 ──── Initial public spec (stdio + HTTP+SSE)
     │
2025-03-26 ──── Streamable HTTP replaces HTTP+SSE
     │           Stateless servers possible
     │           Mcp-Session-Id header
     │
2025-06-18 ──── Lifecycle refinements
     │           Mcp-Protocol-Version header
     │           Capability negotiation improvements
     │
2025-11-25 ──── Tasks primitive (experimental)
     │           OAuth: CIMD replaces DCR
     │           OIDC Discovery 1.0
     │           Tool icons
     │           M2M OAuth (client_credentials)
     │           Enterprise IdP controls (XAA)
     │           SEP-1024: local server install security
     │           Extensions formalized
     │
Draft ──────── SEP-2575: Remove initialize handshake
     │           SEP-2567: Remove sessions, use explicit state handles
     │           Per-request metadata headers
     │           MRTR (Multi-Request Transport Response)
```

### 12.6 HUMMBL Server Status Summary

| Server                          | stdio | Streamable HTTP | OAuth | Docker | Docs                |
| ------------------------------- | ----- | --------------- | ----- | ------ | ------------------- |
| `@hummbl/mcp-server` (TS)       | ✅    | ❌ (REST only)  | ❌    | ❌     | Claude Desktop only |
| `hummbl-governance-mcp` (Py)    | ✅    | ❌              | ❌    | ❌     | ❌                  |
| `hummbl-compliance-mcp` (Py)    | ✅    | ❌              | ❌    | ❌     | ❌                  |
| `hummbl-sandbox-mcp` (Py)       | ✅    | ❌              | ❌    | ❌     | ❌                  |
| `hummbl-identity-mcp` (Py)      | ✅    | ❌              | ❌    | ❌     | ❌                  |
| `hummbl-agent-monitor-mcp` (Py) | ✅    | ❌              | ❌    | ❌     | ❌                  |
| `hummbl-reasoning-mcp` (Py)     | ✅    | ❌              | ❌    | ❌     | ❌                  |
| `hummbl-physical-mcp` (Py)      | ✅    | ❌              | ❌    | ❌     | ❌                  |
| `hummbl-base120-mcp` (Py)       | ✅    | ❌              | ❌    | ❌     | ❌                  |
| `hummbl-bif-mcp` (Py)           | ✅    | ❌              | ❌    | ❌     | ❌                  |
| `hummbl-utf-mcp` (Py)           | ✅    | ❌              | ❌    | ❌     | ❌                  |

---

## References

- [MCP Specification 2025-03-26](https://modelcontextprotocol.io/specification/2025-03-26)
- [MCP Specification 2025-06-18](https://modelcontextprotocol.io/specification/2025-06-18)
- [MCP Specification 2025-11-25](https://modelcontextprotocol.io/specification/2025-11-25)
- [MCP Draft Specification](https://modelcontextprotocol.io/specification/draft)
- [MCP Transports](https://modelcontextprotocol.io/specification/2025-03-26/basic/transports)
- [MCP Streamable HTTP](https://modelcontextprotocol.io/specification/draft/basic/transports/streamable-http)
- [MCP Authorization](https://modelcontextprotocol.io/specification/2025-03-26/basic/authorization)
- [MCP Authorization (2025-11-25)](https://modelcontextprotocol.io/specification/2025-11-25/basic/authorization)
- [MCP Lifecycle](https://modelcontextprotocol.io/specification/2025-06-18/basic/lifecycle)
- [MCP Tools](https://modelcontextprotocol.io/specification/draft/server/tools)
- [MCP Architecture (Draft)](https://mcp.mintlify.app/specification/draft/architecture)
- [SEP-2575: Make MCP Stateless](https://modelcontextprotocol.io/seps/2575-stateless-mcp)
- [SEP-2567: Sessionless MCP via Explicit State Handles](https://modelcontextprotocol.io/seps/2567-sessionless-mcp)
- [Cloudflare Agents: Build a Remote MCP Server](https://developers.cloudflare.com/agents/guides/remote-mcp-server/)
- [Cloudflare Agents: Transport](https://developers.cloudflare.com/agents/model-context-protocol/protocol/transport/)
- [Cloudflare Agents: McpAgent API](https://developers.cloudflare.com/agents/api-reference/mcp-agent-api/)
- [Cloudflare Agents: createMcpHandler](https://developers.cloudflare.com/agents/api-reference/mcp-handler-api/)
- [Cloudflare Blog: Remote MCP Servers](https://blog.cloudflare.com/remote-model-context-protocol-servers-mcp/)
- [Claude Desktop MCP Setup](https://support.claude.com/en/articles/10949351-getting-started-with-local-mcp-servers-on-claude-desktop)
- [Claude Code MCP Docs](https://code.claude.com/docs/en/mcp)
- [Claude Code MCP Quickstart](https://code.claude.com/docs/en/mcp-quickstart)
- [Cursor MCP Docs](https://cursor.com/docs/mcp)
- [VS Code MCP Configuration Reference](https://code.visualstudio.com/docs/copilot/reference/mcp-configuration)
- [VS Code MCP Servers](https://code.visualstudio.com/docs/copilot/customization/mcp-servers)
- [Windsurf Cascade MCP](https://docs.windsurf.com/windsurf/cascade/mcp)
- [mcp-remote (geelen)](https://github.com/geelen/mcp-remote)
- [mcp-remote (automattic)](https://github.com/automattic/mcp-remote)
- [mcp-stdio](https://github.com/shigechika/mcp-stdio)
- [ferry](https://github.com/jpetrucciani/ferry)
- [MCP TypeScript SDK: SSE+Streamable HTTP Compatible Server](https://github.com/modelcontextprotocol/typescript-sdk/blob/v1.x/src/examples/server/sseAndStreamableHttpCompatibleServer.ts)
- [IETF: MCP Security Considerations Draft](https://www.ietf.org/archive/id/draft-mohiuddin-mcp-security-considerations-00.html)
- [MCP Transport Security](https://www.systemshardening.com/articles/ai-landscape/mcp-transport-security/)
- [MCP Security Best Practices (Nevo)](https://nevo.systems/blogs/nevo-journal/mcp-security-best-practices)
- [WorkOS: MCP 2025-11-25 Spec Update](https://workos.com/blog/mcp-2025-11-25-spec-update)
- [MCP 2025-11-25 Changelog](https://github.com/modelcontextprotocol/modelcontextprotocol/blob/main/docs/specification/2025-11-25/changelog.mdx)
- [Docker: Build MCP Servers for Production](https://www.docker.com/blog/build-to-prod-mcp-servers-with-docker/)
- [MCP C# SDK: Stateless and Stateful Mode](https://csharp.sdk.modelcontextprotocol.io/concepts/stateless/stateless.html)
- [MCP C# SDK: Transports](https://csharp.sdk.modelcontextprotocol.io/concepts/transports/transports.html)
- [MCP RFC PR #206: Streamable HTTP](https://github.com/modelcontextprotocol/modelcontextprotocol/pull/206)
- [Microsoft MCP for Beginners: MCP Hosts](https://github.com/microsoft/mcp-for-beginners/blob/HEAD/03-GettingStarted/12-mcp-hosts/README.md)

---

**End of document.**
