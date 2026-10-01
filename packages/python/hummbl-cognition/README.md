# hummbl-cognition

[![CI](https://github.com/hummbl-io/hummbl-cognition/actions/workflows/ci.yml/badge.svg)](https://github.com/hummbl-io/hummbl-cognition/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/license-MIT-blue)](LICENSE)

*Cognitive Ledger Protocol (CLP) and Open Brain server for HUMMBL agent reasoning.*

## What this is

The cognition layer for the HUMMBL multi-agent platform. Provides:

- **CLP v1.1** (Cognitive Ledger Protocol) — append-only JSONL ledger with SHA-256 hash-chaining for tamper-evident shared memory
- **Open Brain** — HTTP server with BM25 search and lineage graph API
- **Sigil Forge** — DSL compiler and execution engine for governed agent rituals
- **Belonging/HRSI** — belonging baseline checks and HRSI check-in tooling
- **Receipt modules** — 17 receipt types for audit trails (issueops, dispatcher, compliance, HIBP, etc.)
- **Migration tooling** — import from bus history, git log, and memory markdown

## Architecture

```
ledger_writer.py     → append-only JSONL with O(1) hash-chaining & HMAC verification
query.py             → search and retrieve from the ledger
boot_context.py      → session startup context loading
server.py            → Open Brain HTTP server (:11435) with /lineage graph API
consolidator.py      → nightly ledger aggregation
sigil_forge/         → DSL compiler, execution engine, policy, rituals, evals
```

## Installation

```bash
pip install hummbl-cognition

# With governance integration (kill switch, security arbiter):
pip install "hummbl-cognition[governance]"

# With Ed25519 entry signing (asymmetric receipts):
pip install "hummbl-cognition[primitives]"
```

## CLI

```bash
python -m hummbl_cognition post "insight text here"
python -m hummbl_cognition query "search term"
python -m hummbl_cognition validate
python -m hummbl_cognition state
python -m hummbl_cognition boot
python -m hummbl_cognition search "pattern"
python -m hummbl_cognition reindex
python -m hummbl_cognition keygen --agent <name>        # generate Ed25519 signing keypair
python -m hummbl_cognition scitt-export --id <clp-id>   # SCITT-shaped statement for one entry
                                                        # (shaped after draft-ietf-scitt-architecture-13;
                                                        #  export shape, not a conformance claim)
```

## Key Modules

| Module | Role |
|--------|------|
| `ledger_writer.py` | Append-only JSONL with hash-chaining — KRINEIA audit trail |
| `query.py` | Ledger search with scoring |
| `boot_context.py` | Loads session context at startup |
| `server.py` | Open Brain HTTP server — GET /status, POST /search, GET /lineage/{id} |
| `consolidator.py` | Nightly ledger consolidation |
| `lattice_advisor.py` | Base120 / Domain120 / BaseN operator recommendations |
| `belonging_check.py` | BKI belonging baseline checks |
| `feedback_tracker.py` | Tracks user feedback for learning |
| `sigil_forge/` | DSL compiler, execution engine, policy enforcement, rituals |

## CLP v1.1 Metadata Extensions

- `previous_hash`: SHA-256 hex digest of the preceding raw ledger JSONL line (cryptographic tamper-evidence)
- `valid_time`: ISO 8601 UTC timestamp tracking when a fact occurred in reality (bi-temporal support)
- `contests`: Target entry ID being disputed/refuted (explicit belief-DAG support)
- `ed25519_sig` / `signer_key_id`: optional per-agent Ed25519 signature over the canonical entry (sorted-keys JSON minus signature fields). Opt-in by key presence under `<ledger_dir>/keys/` — keep that directory out of version control; verification needs only the public key, no shared secret

## State Files

- `_state/cognition/ledger.jsonl` — the canonical append-only ledger
- `_state/cognition/state.json` — current cognitive state
- `_state/cognition/intent.md` — current sprint intent

## Local bus cache retrieval

The `bus` pool in `OpenBrainRetriever` and the MCP `memory_search` tool reads
`~/.cache/bus/messages.tsv`. This is cached evidence, not live bus authority.
Retrieval does not contact or refresh the bus. There is no automatic search
or fallback to retired `_state/coordination/*.tsv` mirrors. An explicit cache
override can select any permitted local file, including an older mirror;
diagnostics identify the selected path.

Set `HUMMBL_BUS_CACHE_PATH` to an absolute local file path to select another
cache, or pass `bus_cache_path=` when constructing the retriever. The explicit
argument takes precedence. Relative paths, URLs, UNC/device paths, empty
overrides, and non-regular files are rejected without fallback. Local filesystem
mounts and concurrent path changes are not an OS-enforced network boundary.

Each search reads at most the final 1 MiB plus one leading boundary byte of
the captured file length and considers the last 200 complete TSV rows. A
complete row must end with a newline within that captured length. A trailing
row without a newline is intentionally discarded even if its columns look
valid; retrieval does not read beyond the captured EOF or invent a newline.
Incomplete boundary rows, malformed UTF-8, and rows without a valid
timezone-aware timestamp are excluded. For the bus pool, `since` is an
inclusive time bound: compact and extended ISO timestamps are compared as
datetimes in UTC, including explicit offsets. Date-only and naive datetime
lower bounds mean UTC; an invalid or empty bound produces `invalid_since`
diagnostics and no bus results. Result context uses the same filtered read;
bus results are never expanded by rereading their source paths.

Bus results include provenance and freshness metadata: selected path, selection
method, observation time, file modification time and age, latest valid timestamp
and age in the scanned rows, and `live_verified: false`. Ages are observations,
not a freshness SLA; negative ages indicate timestamps ahead of the local clock.
The latest timestamp describes the scanned cache rows, not necessarily the
matched message. Result text retains message timestamps.

`retriever.source_diagnostics["bus"]` records the most recent search even when
there are no results; MCP returns it under `source_diagnostics.bus`. Its status
distinguishes unavailable or invalid caches, empty/invalid rows, `since` filtering,
and no query match. Byte/row truncation, discarded partial rows, malformed-row
counts, and detected changes during the read are explicit. A complete cache
scan does not establish complete bus history or verify the cache's provenance.

## Dependencies

- **Required**: `hummbl-bus` (bus writer for coordination messages)
- **Optional**: `hummbl-governance` (kill switch, security arbiter — install with `[governance]` extra)
- **Optional**: `cryptography` (Ed25519 ledger signing — install with `[primitives]` extra)
- **Stdlib-only core** — no other third-party runtime dependencies

## Rules

- Ledger is APPEND-ONLY — never delete, never mutate entries
- Open Brain server binds `127.0.0.1` only
- Consolidator runs periodically via scheduler

## Related

- [hummbl-bus](https://github.com/hummbl-io/hummbl-bus) — coordination bus
- [hummbl-governance](https://github.com/hummbl-io/hummbl-governance) — governance primitives
- [hummbl-skills](https://github.com/hummbl-io/hummbl-skills) — agent skills registry
- [hummbl-agent](https://github.com/hummbl-io/hummbl-agent) — governed control plane

Learn more at [hummbl.io](https://hummbl.io).

## License

MIT.
