# hummbl-mcp-basen

MCP server exposing the Base120 + BaseN governance surface: operator lookup,
family browse, embedding-backed recommendations, and tiered apply modes.

## What it provides

- **4 parameterized tools:**
  - `basen_operator_lookup(operator_id, variant)` — lookup by ID, such as `P1` or `SY20`
  - `basen_family_browse(family, variant)` — list operators in a family, such as `P`, `IN`, `CO`, `DE`, `RE`, or `SY`
  - `basen_recommend(problem_description, variant, top_k)` — embedding-backed recommendations with keyword fallback
  - `basen_apply(operator_id, input, mode)` — apply an operator with `advisory`, `analytic`, or `empirical` mode
- **127 URI-addressable resources:**
  - `basen://base120/operator/{P1..SY20}` — 120 operators
  - `basen://base120/family/{P|IN|CO|DE|RE|SY}` — 6 families
  - `basen://base120/manifest` — full catalog manifest
- **3 starter prompts:**
  - `basen-recon` — apply BaseN to recon a problem
  - `basen-spec` — convert intent into a spec
  - `basen-audit` — audit an artifact with BaseN

Tier 1 calls emit and persist a governance record shaped like a `BaseNTuple`
unless disabled with `BASEN_PERSIST_TUPLES=0`. `basen_apply` is mode-sensitive:
`advisory` is a Tier 0 descriptive read, while `analytic` and `empirical` are
Tier 1 calls.

## Install

```bash
pip install hummbl-mcp-basen
```

Or from the monorepo:

```bash
cd packages/python/basen
pip install -e .
```

## Run

```bash
hummbl-mcp-basen
```

Or via Python module:

```bash
python -m basen.mcp_server
```

Then write newline-delimited JSON-RPC requests to stdin:

```json
{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}
{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}
{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"basen_operator_lookup","arguments":{"operator_id":"IN2"}}}
{"jsonrpc":"2.0","id":4,"method":"resources/read","params":{"uri":"basen://base120/family/IN"}}
{"jsonrpc":"2.0","id":5,"method":"prompts/get","params":{"name":"basen-recon","arguments":{"input":"Plan a migration."}}}
```

## Wiring into Claude Code / Devin

```json
{
  "mcpServers": {
    "basen": {
      "command": "hummbl-mcp-basen",
      "env": {
        "BASEN_MCP_AGENT": "basen-mcp"
      }
    }
  }
}
```

## Environment variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `BASEN_REGISTRY_PATH` | bundled `data/base120_registry.json` | Override registry path |
| `BASEN_MCP_AGENT` | `basen-mcp` | Emitted agent identity in tuples |
| `BASEN_TUPLE_LOG` | `_state/governance/tuples.jsonl` | JSONL tuple log path |
| `BASEN_PERSIST_TUPLES` | `1` | Set to `0` to disable tuple persistence |
| `BASEN_EMBED_URL` | `http://127.0.0.1:11434/api/embeddings` | Ollama embeddings endpoint |
| `BASEN_EMBED_MODEL` | `nomic-embed-text` | Embedding model name |
| `BASEN_EMBED_TIMEOUT` | `5.0` | Embedding request timeout (seconds) |
| `BASEN_EMBED_CACHE_DIR` | `_state/basen` | Embedding cache directory |
| `BASEN_CHAT_URL` | `http://127.0.0.1:11434/api/chat` | Ollama chat endpoint |
| `BASEN_CHAT_MODEL` | `qwen3.5:9b` | Chat model for empirical apply mode |
| `BASEN_CHAT_TIMEOUT` | `30.0` | Chat request timeout (seconds) |

## Recommendation honesty

The `basen_recommend` tool can use `nomic-embed-text` embeddings when the
configured Ollama endpoint is reachable. This is semantic nearest-neighbor
matching over operator text, not genuine analogy or expert reasoning.

In practice:

- Returns: operators semantically near the query text.
- Does not return: an authoritative "right operator" for the task.
- Fallback behavior: if embeddings are unavailable, the server uses
  `keyword-overlap-v0.1-fallback`.

Use recommendations as a first-pass narrowing step, then validate candidate
operators against the actual problem and operator definitions.

## Architecture

- **Stdlib-only** — no third-party runtime dependencies
- **MCP protocol 2024-11-05** over JSON-RPC 2.0 on stdio
- **Cross-platform** — fcntl on POSIX, msvcrt on Windows for file locking
- **Tier model** — Tier 0 reads (no tuple), Tier 1 writes (EVIDENCE tuple), Tier 2 governed (full tuple), Tier 3 chain-linked

## File layout

```text
packages/python/basen/
├── basen/
│   ├── __init__.py
│   ├── mcp_server.py          # MCP server (4 tools, 127 resources, 3 prompts)
│   ├── basen_tuple.py          # BaseNTuple governance record
│   ├── basen_tier.py           # Tier classifier (0=read, 1=write, 2=governed, 3=chain)
│   └── data/
│       └── base120_registry.json  # 120 operators with id, name, domain, definition, difficulty
├── pyproject.toml
└── README.md
```

## Relationship to hummbl-mcp-base120

The `hummbl-mcp-base120` package (in `packages/python/base120/`) is a simpler
public SDK server with 5 tools (get, list, families, prompt, record) that wraps
the `base120` PyPI package's `Engine` API.

This package (`hummbl-mcp-basen`) is the advanced governance server with:
- Embedding-backed recommendations (Ollama nomic-embed-text)
- Tiered apply modes (advisory, analytic, empirical with LLM dispatch)
- 127 URI-addressable resources
- 3 starter prompts
- BaseNTuple governance record emission and persistence
- Richer registry fields (domain_name, difficulty)

Both servers can coexist — they serve different audiences.

## License

Apache-2.0
