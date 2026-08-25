# CLI Reference

The `hummbl-cognition` package exposes command-line interfaces for posting,
querying, validating, searching, and maintaining the cognitive ledger. This
document covers the top-level command surface and the two runnable module CLIs
that ship in the package.

## Entry points

`pyproject.toml` (line 21) declares the console script:

```
hummbl-cognition = "hummbl_cognition.__main__:main"
```

This dispatches the top-level commands (`post`, `query`, `validate`, `state`,
`boot`, `search`, `reindex`). Each maps to a library function documented in the
[API Reference](../reference/api-reference.md). Two additional module CLIs are
directly runnable via `python -m`:

- `python -m hummbl_cognition.consolidator` — nightly consolidation
  (`consolidator.py:383-424`).
- `python -m hummbl_cognition.client` — remote Open Brain client
  (`client.py:150-242`).

## Path resolution

All commands honor the environment-variable path overrides (see
[Getting Started](../getting-started/index.md#how-paths-are-resolved)):

| Variable | Controls | Module |
|---|---|---|
| `COGNITION_LEDGER` | Ledger file path | `ledger_writer.py:406` |
| `COGNITION_INDEX` | Index file path | `indexer.py:56` |
| `COGNITION_DIR` | Cognition directory | `boot_context.py:119` |
| `COGNITION_RETRIEVAL_LOG` | Retrieval log path | `feedback_tracker.py:63` |
| `BUS_SIGNING_SECRET` | HMAC signing secret (≥ 32 bytes) | `ledger_writer.py:430` |
| `PII_SCAN_STRICT` | `true` to block PII at write time | `ledger_writer.py:572` |
| `OPEN_BRAIN_URL` | Remote brain server URL | `client.py:47` |
| `OPEN_BRAIN_TOKEN` | Remote brain bearer token | `client.py:52` |

---

## Top-level commands

### `hummbl-cognition post`

Append a ledger entry. Wraps `LedgerEntry.create()` + `post_entry()`
(`ledger_writer.py:528-628`).

```
hummbl-cognition post --agent <id> --vendor <v> --model <m> \
  --type <t> --scope <s> --content "<text>" [--tags a,b] [--confidence 0.9] \
  [--evidence "<text>"] [--ledger <path>]
```

| Flag | Required | Description |
|---|---|---|
| `--agent` | yes | Agent identifier (e.g. `claude-code`). |
| `--vendor` | yes | One of `anthropic`, `google`, `human`, `local`, `moonshot`, `openai` (`ledger_writer.py:485`). |
| `--model` | yes | Model name. |
| `--type` | yes | A canonical `LedgerEntryType` (`decision`, `correction`, `lesson`, `convention`, `discovery`). |
| `--scope` | yes | A canonical `LedgerScope` (`project`, `global`, `session`). |
| `--content` | yes | Entry content (max 4096 chars). |
| `--tags` | no | Comma-separated tags (max 10). |
| `--confidence` | no | Float in `[0.0, 1.0]`. |
| `--evidence` | no | Supporting evidence text. |
| `--ledger` | no | Override ledger path. |

**Example:**

```bash
hummbl-cognition post --agent claude-code --vendor anthropic --model claude-opus-4 \
  --type lesson --scope project \
  --content "Pin SDK versions in requirements.txt to avoid silent breakage." \
  --tags python,dependencies --confidence 0.9
```

The entry is content-scanned, schema-validated, hash-verified, optionally
signed, and appended under an exclusive lock. On success the entry ID
(`clp-<12hex>`) is printed.

### `hummbl-cognition query`

Read and filter entries. Wraps `query_entries()` (`query.py:16-38`) and
`active_entries()` (`query.py:41-61`).

```
hummbl-cognition query [--type <t>] [--scope <s>] [--agent <a>] [--since <iso>] \
  [--tags a,b] [--limit N] [--active-only] [--ledger <path>] [--json]
```

| Flag | Required | Description |
|---|---|---|
| `--type` | no | Filter by entry type. |
| `--scope` | no | Filter by scope. |
| `--agent` | no | Substring match on agent. |
| `--since` | no | ISO 8601 timestamp; only entries after this. |
| `--tags` | no | Comma-separated; entries must contain all. |
| `--limit` | no | Max results (default 50). Most recent first. |
| `--active-only` | no | Exclude superseded entries. |
| `--ledger` | no | Override ledger path. |
| `--json` | no | Emit JSON lines. |

**Example:**

```bash
hummbl-cognition query --type lesson --tags python --limit 5 --active-only
```

### `hummbl-cognition validate`

Validate ledger integrity. Wraps `validate_integrity()` /
`validate_integrity_report()` (`ledger_writer.py:798-964`).

```
hummbl-cognition validate [--ledger <path>] [--report] [--secret <bytes>]
```

| Flag | Required | Description |
|---|---|---|
| `--ledger` | no | Override ledger path. |
| `--report` | no | Emit the structured report (classified errors, line ranges, remediation). |
| `--secret` | no | HMAC key (falls back to `BUS_SIGNING_SECRET`). |

**Example:**

```bash
hummbl-cognition validate --report
```

Output (report mode) includes `total_lines`, `valid_entries`, and per-class
error counts (`signature_mismatch`, `content_hash_mismatch`, `parse_error`,
`other`) with line ranges and remediation guidance.

### `hummbl-cognition state`

Read and render the shared state (`state.json`). Wraps `SharedState.from_dict()`
as used in `build_boot_context()` (`boot_context.py:176-213`).

```
hummbl-cognition state [--cognition-dir <path>] [--json]
```

| Flag | Required | Description |
|---|---|---|
| `--cognition-dir` | no | Override cognition directory. |
| `--json` | no | Emit raw `state.json` JSON. |

**Example:**

```bash
hummbl-cognition state
# Sprint: cognition-hardening
# Agents: claude-code (writing docs), cursor (idle)
# Claimed: docs/architecture/index.md (claude-code) -- diagrams
# Flags: consolidation_enabled=true, kill_switch=false
```

### `hummbl-cognition boot`

Generate the frozen-snapshot boot context. Wraps `build_boot_context()`
(`boot_context.py:138-235`).

```
hummbl-cognition boot [--cognition-dir <path>] [--max-entries N] [--max-age-days N]
```

| Flag | Required | Description |
|---|---|---|
| `--cognition-dir` | no | Override cognition directory. |
| `--max-entries` | no | Max ledger entries in summary (default 50). |
| `--max-age-days` | no | Only entries from the last N days (default 30). |

**Example:**

```bash
hummbl-cognition boot --max-age-days 14
```

Prints markdown starting with `# Cognitive Ledger Boot Context`, suitable for
injecting into an agent system prompt once at session start.

### `hummbl-cognition search`

Full-text BM25 search over the ledger. Wraps `BM25Index.search()`
(`indexer.py:157-224`). Builds/loads the index as needed.

```
hummbl-cognition search "<query>" [--limit N] [--scope <s>] [--type <t>] \
  [--since <iso>] [--no-boost] [--index <path>] [--ledger <path>] [--json]
```

| Flag | Required | Description |
|---|---|---|
| `<query>` | yes | Search query. |
| `--limit` | no | Max results (default 20). |
| `--scope` | no | Filter by scope. |
| `--type` | no | Filter by entry type. |
| `--since` | no | ISO timestamp filter. |
| `--no-boost` | no | Disable stigmergic retrieval boost. |
| `--index` | no | Override index path. |
| `--ledger` | no | Override ledger path (used if index must be built). |
| `--json` | no | Emit JSON lines. |

**Example:**

```bash
hummbl-cognition search "OAuth token refresh" --scope project --limit 5
```

### `hummbl-cognition reindex`

Rebuild the BM25 index from the ledger. Wraps `BM25Index.build()` + `save()`
(`indexer.py:94-155, 253-289`).

```
hummbl-cognition reindex [--ledger <path>] [--index <path>]
```

| Flag | Required | Description |
|---|---|---|
| `--ledger` | no | Override ledger path. |
| `--index` | no | Override index output path. |

**Example:**

```bash
hummbl-cognition reindex
# Built index: 1284 entries, 9421 terms, avg_doc_len=18.3
# Saved index to hummbl_governance/_state/cognition/index.json
```

---

## `python -m hummbl_cognition.consolidator`

Nightly consolidation CLI (`consolidator.py:383-424`).

### `consolidator run`

```
python -m hummbl_cognition.consolidator run [--dry-run] [--model <m>] \
  [--ollama-url <url>] [--ledger <path>]
```

| Flag | Required | Description |
|---|---|---|
| `--dry-run` | no | Show groups without writing. |
| `--model` | no | Ollama model (default `qwen3.5:9b`). |
| `--ollama-url` | no | Ollama base URL (default `http://127.0.0.1:11434`). |
| `--ledger` | no | Override ledger path. |

**Example:**

```bash
python -m hummbl_cognition.consolidator run --dry-run
# {"groups_found": 3, "consolidated": 3, "skipped": 0, "errors": []}
```

### `consolidator status`

```
python -m hummbl_cognition.consolidator status [--ledger <path>]
```

Prints JSON: `total_entries`, `consolidated_entries`, `source_entries_covered`,
`unconsolidated`.

---

## `python -m hummbl_cognition.client`

Remote Open Brain client CLI (`client.py:150-242`).

### Global flag

```
--url <url>   Server URL (default: OPEN_BRAIN_URL env or http://100.109.69.16:11435)
```

### `client search`

```
python -m hummbl_cognition.client search "<query>" [--budget N] [--scope <s>] \
  [--type <t>] [--since <iso>] [--sources ...] [--limit N] [--json]
```

| Flag | Required | Description |
|---|---|---|
| `<query>` | yes | Search query. |
| `--budget` | no | Token budget (default 2000). |
| `--scope` | no | Filter by scope. |
| `--type` | no | Filter by type. |
| `--since` | no | ISO timestamp filter. |
| `--sources` | no | Memory pools: `ledger`, `bus`, `briefings`, `findings`, `memory_md` (`client.py:170-174`). |
| `--limit` | no | Max results (default 20). |
| `--json` | no | JSON output. |

**Example:**

```bash
python -m hummbl_cognition.client search "OAuth refresh" --limit 5
```

### `client status`

```bash
python -m hummbl_cognition.client status
```

### `client reindex`

```bash
python -m hummbl_cognition.client reindex
```

### `client health`

```bash
python -m hummbl_cognition.client health
# OK  (or UNREACHABLE)
```

---

## Exit codes

- `0` — success.
- `1` — run completed with errors (consolidator) or server unreachable (client
  health).
- `2` — no subcommand given / usage error (both `main()` functions return 2 in
  this case: `consolidator.py:407, 424`, `client.py:190, 242`).
