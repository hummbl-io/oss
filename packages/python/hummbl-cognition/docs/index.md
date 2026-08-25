# HUMMBL Cognitive Ledger Protocol (CLP) — Documentation

The **HUMMBL Cognitive Ledger Protocol (CLP)** is an append-only JSONL memory
system designed for multi-agent AI coordination. It gives independent agents a
durable, shared, queryable record of what they have learned, decided, and
corrected — without requiring a central server or a mutable database.

This package (`hummbl-cognition`, v0.1.0, Python ≥ 3.11, Apache-2.0) implements
the protocol with a stdlib-only core: no third-party runtime dependencies are
required for reading, writing, indexing, or validating the ledger.

## What the protocol provides

- **Append-only shared memory** — a `ledger.jsonl` file where every learning,
  decision, correction, convention, and discovery is recorded as an immutable
  JSON line. Entries are never edited or deleted; corrections are new entries
  that *supersede* earlier ones (`ledger_writer.py`, `query.py`).
- **Three-layer architecture** — *Shared State* (`state.json`), *Shared Memory*
  (`ledger.jsonl`), and *Shared Intent* (`intent.md`), unified into a single
  boot context for agent injection (`__init__.py`, `boot_context.py`).
- **BM25 full-text search** — a derived, always-rebuildable inverted term index
  over the ledger with stigmergic (retrieval-frequency) ranking boosts
  (`indexer.py`).
- **Concurrency-safe writes** — platform-adaptive advisory file locking
  (`fcntl` on POSIX, `msvcrt` on Windows) so multiple agents can append safely
  (`ledger_writer.py`, `feedback_tracker.py`).
- **Content hardening** — every entry is scanned for prompt-injection patterns,
  leaked credentials, exfiltration vectors, invisible Unicode, and cross-script
  homoglyphs before it is allowed to reach the ledger (`ledger_writer.py`).
- **Integrity validation** — content-hash verification and optional HMAC-SHA256
  signatures detect tampering; a structured report classifies errors and groups
  them by line range (`ledger_writer.py`).
- **Nightly consolidation** — semantically related entries are grouped (by
  Zettelkasten links and BM25/Jaccard similarity) and synthesized into
  `convention` summaries via a local Ollama model (`consolidator.py`).
- **Remote federation** — an HTTP client lets secondary machines search, ingest
  into, and reindex a primary "Open Brain" server (`client.py`).

## Code surface

The package is eight Python modules (2,668 lines total):

| Module | Lines | Role |
|---|---|---|
| `ledger_writer.py` | 976 | Append-only JSONL writer, file locking, content scanning, PII scrubbing, schema validation, signature signing/verification, integrity reports |
| `consolidator.py` | 428 | Nightly grouping + LLM synthesis of related entries |
| `indexer.py` | 324 | BM25 inverted index with stigmergic ranking |
| `client.py` | 246 | HTTP client for the remote Open Brain server |
| `boot_context.py` | 235 | Frozen-snapshot boot context from all three layers |
| `feedback_tracker.py` | 172 | Append-only retrieval log feeding stigmergic ranking |
| `__init__.py` | 158 | Package facade re-exporting the public API |
| `query.py` | 129 | Filtered queries, supersedes resolution, boot summarization |

## Where to start

- **New to the protocol?** Read [Getting Started](getting-started/index.md) for
  a first ledger write, first query, and the file-locking basics.
- **Want the big picture?** Read [Architecture](architecture/index.md) for the
  three-layer model, the append-only design, the locking mechanism, and the BM25
  indexing pipeline (with diagrams).
- **Building against the library?** Read the [API Reference](reference/api-reference.md)
  for every public class and function, with signatures and examples.
- **Modeling entries?** Read [Data Models](reference/data-models.md) for the
  `LedgerEntry`, `LedgerEntryType`, `LedgerScope`, and `SharedState` schemas.
- **Using the command line?** Read the [CLI Reference](cli/index.md) for the
  `post`, `query`, `validate`, `state`, `boot`, `search`, and `reindex`
  commands, plus the `consolidator` and `client` sub-CLIs.
- **Looking for concrete examples?** Read [Examples](examples/index.md) for
  sample ledger lines, a sample `state.json`, query outputs, and a multi-agent
  coordination walkthrough.
- **Something broke?** Read [Troubleshooting](troubleshooting/index.md) for
  concurrency errors, lock conflicts, corruption recovery, and performance.
- **Migrating existing knowledge?** Read [Migrations](migrations/index.md) for
  importing from bus history, git logs, and `memory.md` files.

## Installation

```bash
pip install hummbl-cognition
```

The package declares a console-script entry point
`hummbl-cognition = "hummbl_cognition.__main__:main"` (see `pyproject.toml`).
The library API is importable directly from the submodules documented here.
