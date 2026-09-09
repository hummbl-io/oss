# hummbl-mcp-cognitive-ledger

Thin shim MCP server for the Cognitive Ledger Protocol (CLP). Delegates to
the `hummbl-cognition` package (pip-installed), which provides the actual
server implementation.

## Tools

- `ledger_search` — BM25 search over the cognitive ledger
- `ledger_query` — structured query of ledger entries
- `ledger_post` — append a new entry to the cognitive ledger
- `ledger_stats` — ledger statistics (entry count, date range, types)
- `boot_context` — build session startup context from the ledger
- `reindex` — rebuild the BM25 search index

## Install

```bash
pip install hummbl-mcp-cognitive-ledger
```

This pulls in `hummbl-cognition` as a dependency.

## Run

```bash
hummbl-mcp-cognitive-ledger
```

Or via stdio JSON-RPC:

```bash
python mcp_server.py
```

## Environment

- `CLP_STATE_DIR` — ledger state directory (default: hummbl_cognition default)
- `COGNITION_VENDOR` — default vendor for `ledger_post` (anthropic|openai|google|moonshot|local|human)
- `COGNITION_MODEL` — default model for `ledger_post`

## Source of truth

The actual implementation lives in the
[hummbl-cognition](https://github.com/hummbl-io/hummbl-cognition) repo. This
package is a thin entry point for the monorepo's MCP server catalog.

## License

Apache-2.0
