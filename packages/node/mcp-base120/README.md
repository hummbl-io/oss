# HUMMBL Base120 MCP

Read-only, deterministic access to the frozen Base120 catalog through the
Model Context Protocol (MCP).

> **Technical canary:** this package is private and unpublished. Its source,
> corpus licensing, release provenance, hosted parity, and privacy gates must
> be resolved before any public release.

## Contract

The server exposes exactly four tools:

| Tool | Purpose |
| --- | --- |
| `base120_get` | Return one model by code. |
| `base120_list` | List all models or one transformation family. |
| `base120_search` | Search model codes, names, and definitions. |
| `base120_prompt` | Format a deterministic prompt locally. |

The local server has no network egress, telemetry, durable writes, external
model calls, mutation tools, billing, customer data, or fleet configuration.

## Run the technical canary

Node.js 22 or newer is required.

```bash
cd packages/node/mcp-base120
npm ci
npm test
node bin/mcp-base120.mjs
```

The stdio transport accepts one newline-delimited JSON-RPC message per line.
The canary supports the current stateless MCP revision (`2026-07-28`) and the
`2025-11-25` and `2025-06-18` initialization-based revisions. A current client
starts with discovery:

```json
{"jsonrpc":"2.0","id":1,"method":"server/discover","params":{"_meta":{"io.modelcontextprotocol/protocolVersion":"2026-07-28","io.modelcontextprotocol/clientCapabilities":{},"io.modelcontextprotocol/clientInfo":{"name":"example","version":"1.0.0"}}}}
```

Every subsequent current-revision request carries the same `_meta` fields.
Legacy clients must complete `initialize` before calling `tools/list` or a
tool.

## JavaScript API

```js
import { getModel, listModels, searchModels, formatPrompt } from "@hummbl/mcp-base120";

const model = getModel("P1");
const systemsModels = listModels({ transformation: "SY" });
const matches = searchModels("feedback");
const prompt = formatPrompt("P1", "What is the smallest useful canary?");
```

## Corpus provenance

`data/catalog.json` is generated from:

```text
packages/python/base120/Base120_Canonical_Model_Registry.yaml
```

Run `npm run generate` after an intentional registry change. CI runs
`npm run check:generated` and rejects stale catalog or provenance artifacts.
The committed provenance file records normalized source and generated-catalog
SHA-256 hashes.

## Product boundary

The machine-readable boundary is [`product.json`](product.json). This canary
must not be published or deployed until every blocking admission item is
cleared. In particular, the existing Base120 software/corpus license language
requires reconciliation before redistribution from npm.

See [`SECURITY.md`](SECURITY.md) for reporting and current limitations.
