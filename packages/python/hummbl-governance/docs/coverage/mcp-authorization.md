# MCP Authorization (2026-07-28) Coverage Matrix — HUMMBL

**Standard**: Model Context Protocol — Authorization (transport-level OAuth profile)
**Revision**: **2026-07-28** (final)
**Official**: https://modelcontextprotocol.io/specification/2026-07-28/basic/authorization
**Last reviewed**: 2026-08-31
**Reviewer**: documentation pass per [ADR-001](../adr/ADR-001-coverage-matrix-not-self-grade.md) and LANDING-013
**HUMMBL version mapped against**: hummbl-governance v1.4.2 (`pyproject.toml` on this tree)

## Boundary disclaimer (product-interop, not a legal mapping)

This is a **protocol interoperability** workpaper. It is **not** a regulation, **not** a certification scheme, and **not** a claim that HUMMBL conforms to MCP Authorization 2026-07-28.

Authorization is **OPTIONAL** in the specification. When supported:

- HTTP-based transports **SHOULD** conform to this specification.
- STDIO transports **SHOULD NOT** follow this specification; they retrieve credentials from the environment.
- Alternative transports MUST follow established security best practices for their protocol.

**No public “fulfills MCP Authorization.”** No row in this file is ✅.

## What this profile builds on (not extra completeness rows)

The 2026-07-28 page names these as the selected subset: OAuth 2.1 (draft-ietf-oauth-v2-1-13); RFC 6750 (Bearer); RFC 8414 (AS metadata); RFC 8707 (resource indicators); RFC 9728 (Protected Resource Metadata); RFC 9207 (`iss`); RFC 7591 (DCR — **deprecated** here in favor of CIMD); OAuth Client ID Metadata Documents (draft-ietf-oauth-client-id-metadata-document-00); OpenID Connect Discovery 1.0 and Dynamic Client Registration 1.0.

**RFC 8693** (OAuth 2.0 Token Exchange, `act` / `may_act`) is **not** in this specification and is **not** a row here. See the coverage README related-artifacts sentence. Do not fight PR 92 `ietf.md`.

## Investigation — HUMMBL MCP entry points (this tree)

Shipped MCP servers in this monorepo are **STDIO JSON-RPC**, not HTTP resource servers:

- `packages/python/hummbl-governance/mcp_server.py` — STDIO (`sys.stdin` JSON-RPC). `PROTOCOL_VERSION = "2024-11-05"`. Env paths (`GOVERNANCE_STATE_DIR`, `GOVERNANCE_DB_PATH`, `GOVERNANCE_AUDIT_DIR`). No Bearer / PRM / CIMD.
- `packages/python/hummbl-bif/mcp_server.py` — STDIO JSON-RPC; env / local state; no HTTP OAuth profile.
- `packages/python/hummbl-cognition/src/hummbl_cognition/mcp_server.py` — STDIO JSON-RPC; env / local ledger; no HTTP OAuth profile.
- `packages/python/hummbl-bus/src/hummbl_bus/mcp_server.py` — STDIO JSON-RPC; env `BUS_FILE`; no HTTP OAuth profile.
- `base120-mcp` (base120 package README) — STDIO command for Claude Code / Cursor; process spawn, not an HTTP RS.

No HTTP MCP server, no `/.well-known/oauth-protected-resource`, and no authorization-server implementation were found in these packages. HUMMBL `delegation` HMAC tokens are an in-process capability primitive, **not** MCP access tokens.

## Coverage state legend

| Glyph | State | Meaning |
|---|---|---|
| ✅ | Fulfilled | Named HUMMBL primitive implements the control; evidence artifact must be validated before public use |
| 🟡 | Partial | HUMMBL primitive or shipped STDIO server provides part; HTTP OAuth / AS / customer host completes it. Both parts named. |
| ⚪ | Boundary | Control is HTTP RS/AS/client, or otherwise outside shipped HUMMBL. |
| ⛔ | Out of scope | Control does not apply to the AI governance platform context (retained for completeness). |

## Completeness

Completeness for this first matrix = the grain requested for 2026-07-28: **RS / client / AS roles**; **PRM discovery**; **CIMD / DCR / pre-registration**; **`resource` parameter**; **audience validation**; **401 / 403 `insufficient_scope`**; **step-up**; **STDIO vs HTTP**. Optional MCP Authorization Extensions are named in prose only (the spec says they are optional, additive, and versioned independently).

## Role rows

| ID | Requirement (2026-07-28) | HUMMBL coverage | Evidence |
|---|---|---|---|
| RS (resource server) | A protected MCP server acts as an OAuth 2.1 resource server and accepts access tokens on protected resource requests | ⚪ Boundary: no HTTP MCP resource server on this tree. In-process primitives are not an MCP RS. | n/a — boundary |
| Client | An MCP client acts as an OAuth 2.1 client, making protected resource requests on behalf of a resource owner | ⚪ Boundary: HUMMBL does not ship an MCP OAuth client. Host agents (Claude Code, Cursor) are the client. | n/a — boundary |
| AS (authorization server) | The AS interacts with the user if needed and issues access tokens for the MCP server. AS implementation is out of spec scope; it may be co-hosted or separate | ⚪ Boundary: HUMMBL is not an authorization server. | n/a — boundary |

## Discovery and registration

| ID | Requirement (2026-07-28) | HUMMBL coverage | Evidence |
|---|---|---|---|
| PRM discovery (RFC 9728) | MCP servers MUST implement Protected Resource Metadata. Clients MUST use PRM for AS discovery. AS MUST offer RFC 8414 and/or OpenID Connect Discovery; clients MUST support both | ⚪ Boundary: no PRM document, no `WWW-Authenticate` `resource_metadata`, no AS metadata endpoints. | n/a — boundary |
| CIMD | Authorization servers and MCP clients SHOULD support OAuth Client ID Metadata Documents. Clients MUST obtain a client ID via CIMD, pre-registration, or DCR (priority in Client Registration) | ⚪ Boundary: no CIMD client_id URL, no metadata fetch. | n/a — boundary |
| DCR (RFC 7591) | AS and clients MAY support Dynamic Client Registration. **Deprecated** in this revision; retained for AS that do not support CIMD | ⚪ Boundary: no `/register`. DCR is not implemented and is not treated as the preferred path. | n/a — boundary |
| Pre-registration | Third registration mechanism: use an existing `client_id` | ⚪ Boundary: no MCP OAuth client registration of any kind. | n/a — boundary |

## Token binding and errors

| ID | Requirement (2026-07-28) | HUMMBL coverage | Evidence |
|---|---|---|---|
| `resource` parameter (RFC 8707) | Clients MUST include `resource` on authorization and token requests; it MUST identify the MCP server via its canonical URI | ⚪ Boundary: no authorization-code or token request path. | n/a — boundary |
| Audience validation | MCP servers MUST validate that access tokens were issued for them as audience (RFC 8707 §2). Invalid/expired tokens MUST get HTTP 401. Servers MUST NOT accept or transit other tokens | ⚪ Boundary: no access-token audience check. `delegation.py` HMAC verify is not RFC 8707 audience binding. | `hummbl_governance/delegation.py` (in-process DCT only; not MCP tokens) |
| 401 Unauthorized | Authorization required or token invalid. Example challenge carries `WWW-Authenticate: Bearer` plus `resource_metadata` and optional `scope` | ⚪ Boundary: STDIO servers do not emit HTTP 401 / `WWW-Authenticate`. | n/a — boundary |
| 403 `insufficient_scope` | Insufficient permissions SHOULD be HTTP 403 with `error="insufficient_scope"`, `scope=`, and `resource_metadata` (RFC 6750 §3.1) | ⚪ Boundary: no HTTP 403 scope challenge. `capability_fence` / `ops_allowed` deny is not this error object. | `hummbl_governance/capability_fence.py`, `hummbl_governance/delegation.py` (local deny only) |
| Step-up | Clients SHOULD (user-delegated) or MAY (`client_credentials`) run a step-up authorization flow on `insufficient_scope`, unioning previous and challenged scopes, with retry limits | ⚪ Boundary: no step-up authorization flow. | n/a — boundary |

## Transport split

| ID | Requirement (2026-07-28) | HUMMBL coverage | Evidence |
|---|---|---|---|
| STDIO vs HTTP | HTTP implementations SHOULD conform. STDIO implementations SHOULD NOT follow this specification and instead retrieve credentials from the environment | 🟡 Partial: shipped entry points are STDIO and take state/credentials from the environment (the STDIO half of the split). They do **not** implement the HTTP SHOULD. Protocol string on the governance server is still `2024-11-05`, not a 2026-07-28 HTTP RS. | `packages/python/hummbl-governance/mcp_server.py` (stdio loop + env vars); sibling STDIO servers in bif / cognition / bus |

## Surfaces named so they are not silent (not extra completeness rows)

- **MCP Authorization Extensions** (optional, additive, independently versioned): not adopted. ⚪ Boundary.
- **Refresh tokens / `offline_access`**: resource servers SHOULD NOT advertise `offline_access` in PRM / `WWW-Authenticate`. No token issuance here. ⚪ Boundary.
- **RFC 9207 `iss` on the authorization response**: client/AS concern. ⚪ Boundary.

## Summary

| Section | Rows | ✅ | 🟡 | ⚪ | ⛔ |
|---|---:|---:|---:|---:|---:|
| Roles | 3 | 0 | 0 | 3 | 0 |
| Discovery and registration | 4 | 0 | 0 | 4 | 0 |
| Token binding and errors | 5 | 0 | 0 | 5 | 0 |
| Transport split | 1 | 0 | 1 | 0 | 0 |
| **Totals** | **13** | **0** | **1** | **12** | **0** |

## Draft coverage summary (not public claim)

This matrix is internal starter material. It must not be used as public evidence that HUMMBL conforms to MCP Authorization 2026-07-28, is an MCP resource server, or implements CIMD/DCR/PRM. Existing coverage matrices last reviewed 2026-05-14 / v0.8.0 are not upgraded by this file.

## Cross-references

- ADR: [`docs/adr/ADR-001-coverage-matrix-not-self-grade.md`](../adr/ADR-001-coverage-matrix-not-self-grade.md)
- Microsoft ACS (vendor policy verdicts; different surface): [`microsoft-acs.md`](./microsoft-acs.md)
- Official spec: https://modelcontextprotocol.io/specification/2026-07-28/basic/authorization
