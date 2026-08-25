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

## State Files

- `_state/cognition/ledger.jsonl` — the canonical append-only ledger
- `_state/cognition/state.json` — current cognitive state
- `_state/cognition/intent.md` — current sprint intent

## Dependencies

- **Required**: `hummbl-bus` (bus writer for coordination messages)
- **Optional**: `hummbl-governance` (kill switch, security arbiter — install with `[governance]` extra)
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
