# Getting Started

This guide takes you from a fresh checkout to writing ledger entries, querying
them, building a search index, and generating a boot context — all using the
real `hummbl_cognition` API. Every snippet below maps to a concrete function or
class in the source.

## Prerequisites

- Python ≥ 3.11 (declared in `pyproject.toml`, `requires-python = ">=3.11"`).
- The `hummbl_cognition` package installed (`pip install hummbl-cognition`) or
  the repo on your path.
- No third-party runtime dependencies are required for the core. The
  consolidator's LLM synthesis optionally calls a local
  [Ollama](https://ollama.ai) server (`consolidator.py:43`, default
  `http://127.0.0.1:11434`); if Ollama is unavailable it degrades gracefully to
  a concatenation fallback (`consolidator.py:338-343`).

## How paths are resolved

Every module that touches disk follows the same three-tier resolution pattern.
For the ledger (`ledger_writer.py:398-425`):

1. An explicit `ledger_path` argument passed to the function.
2. The `COGNITION_LEDGER` environment variable.
3. The git repository root joined with the default
   `hummbl_governance/_state/cognition/ledger.jsonl`.

The same pattern is used for the index (`COGNITION_INDEX`, `indexer.py:52-69`),
the retrieval log (`COGNITION_RETRIEVAL_LOG`, `feedback_tracker.py:59-76`), and
the cognition directory (`COGNITION_DIR`, `boot_context.py:115-135`). For quick
experiments, set `COGNITION_LEDGER` once:

```bash
export COGNITION_LEDGER=/tmp/my-ledger.jsonl
```

## Your first ledger entry

A ledger entry is built with `LedgerEntry.create(...)` and persisted with
`post_entry(...)` from `ledger_writer.py`. `post_entry` is the **only** canonical
write path: it scans content, validates the schema, verifies the content hash,
optionally signs the entry, and appends under an exclusive advisory lock
(`ledger_writer.py:528-628`).

```python
from hummbl_cognition.ledger_writer import post_entry
from hummbl_cognition.models import LedgerEntry

entry = LedgerEntry.create(
    content="Always pin the SDK version in requirements.txt to avoid silent breakage.",
    agent="claude-code",
    vendor="anthropic",
    model="claude-opus-4",
    entry_type="lesson",
    scope="project",
    tags=["python", "dependencies"],
    confidence=0.9,
)
written = post_entry(entry, ledger_path="/tmp/my-ledger.jsonl")
print(written.id)  # e.g. clp-a1b2c3d4e5f6
print(written.content_hash)  # 64-char SHA-256 hex
```

What happened under the hood (`ledger_writer.py:557-628`):

1. The parent directory is created (`path.parent.mkdir(parents=True, exist_ok=True)`).
2. `scan_content()` runs on `content`, `evidence`, `tags`, and `agent` —
   rejecting prompt injection, credentials, exfiltration vectors, and invisible
   Unicode (`ledger_writer.py:341-395`).
3. `scan_pii()` checks for emails, phone numbers, SSNs, and IP addresses. By
   default it only warns; set `PII_SCAN_STRICT=true` to block
   (`ledger_writer.py:572-578`).
4. `_validate_entry_schema()` enforces required fields, the `clp-<12hex>` ID
   format, vendor/type/scope enums, the 4096-char content cap, the 10-tag cap,
   confidence range, and assurance level (`ledger_writer.py:463-525`).
5. `entry.verify_hash()` confirms the stored `content_hash` matches a hash of
   the content fields.
6. If a signing secret is available (the `secret` argument or the
   `BUS_SIGNING_SECRET` env var, which must be ≥ 32 bytes), the entry is
   HMAC-SHA256 signed (`ledger_writer.py:428-448, 594-601`).
7. The JSONL line is appended under `fcntl.flock(LOCK_EX)` (POSIX) or
   `msvcrt.locking(LK_LOCK)` (Windows), then flushed and unlocked
   (`ledger_writer.py:606-614`).
8. New files are hardened to mode `0o660` (`ledger_writer.py:451-460, 617-618`).

## Your first query

Reading is done with `read_entries(...)` (`ledger_writer.py:661-795`) or the
thin wrapper `query_entries(...)` (`query.py:16-38`). Results are returned
**most recent first**.

```python
from hummbl_cognition.query import query_entries, active_entries

# Filter by type and tags (entries must contain ALL tags)
lessons = query_entries(
    ledger_path="/tmp/my-ledger.jsonl",
    entry_type="lesson",
    tags=["python"],
    limit=10,
)
for e in lessons:
    print(f"[{e.timestamp[:10]}] {e.agent}: {e.content}")
```

`active_entries()` (`query.py:41-61`) filters out entries that have been
superseded by a correction — it collects every `supersedes` target and removes
those IDs from the result set, leaving only current knowledge.

## File locking basics

Two modules implement the same locking helper pair: `_lock_file` /
`_unlock_file` (`ledger_writer.py:49-71` and `feedback_tracker.py:34-56`). The
behavior is platform-adaptive:

- **POSIX** (`fcntl` available): `fcntl.flock(file_obj, fcntl.LOCK_EX)` to
  acquire, `fcntl.LOCK_UN` to release. This is a cooperative advisory lock —
  only writers that also call `_lock_file` are mutually excluded.
- **Windows** (`msvcrt` available): `msvcrt.locking(fileno, msvcrt.LK_LOCK, 1)`
  to acquire, `msvcrt.LK_UNLCK` to release, after flushing and seeking to 0.
- **Neither** (unsupported platform): a warning is logged and the write
  proceeds unlocked. This is safe for single-agent use but **not** for
  concurrent multi-agent writes.

Because the lock is advisory, all agents writing to the same ledger **must** go
through `post_entry()` (or otherwise honor the same lock) to get mutual
exclusion. Bypassing it with a raw `open(..., "a")` will interleave lines
unsafely.

## Building a search index

The BM25 index is a derived artifact — rebuild it any time from the ledger
(`indexer.py:72-324`). Storage defaults to
`hummbl_governance/_state/cognition/index.json` (`indexer.py:27`).

```python
from hummbl_cognition.indexer import BM25Index

index = BM25Index(index_path="/tmp/my-index.json")
count = index.build(ledger_path="/tmp/my-ledger.jsonl")
index.save()
print(f"Indexed {count} entries")

results = index.search("dependencies breakage", limit=5)
for r in results:
    print(f"{r['score']:.3f}  {r['id']}  {r['meta']['content_preview'][:60]}")
```

`search()` scores documents with BM25 (k1=1.5, b=0.75, `indexer.py:30-31`) and
optionally applies a stigmergic boost of up to +20% for frequently retrieved
entries (`indexer.py:198-206`). The save path is crash-safe: it writes a temp
file, `fsync`s, then atomically `os.replace`s it (`indexer.py:253-289`).

## Generating a boot context

`build_boot_context()` (`boot_context.py:138-235`) reads all three layers and
returns a single markdown string for injecting into an agent's system prompt at
session start. It is a **frozen snapshot** — computed once and immutable for the
session, so mid-session ledger writes do not invalidate the LLM's prefix cache
(`boot_context.py:7-17`).

```python
from hummbl_cognition.boot_context import build_boot_context

context = build_boot_context("/tmp/cognition")
print(context)
```

It tries the BM25 index first for fast summarization at scale
(`boot_context.py:47-108`) and falls back to a sequential scan via
`summarize_for_boot()` (`query.py:82-129`) when the index is missing or empty.

## CLI quick start

The package ships two runnable module CLIs in this version. The consolidator
(`consolidator.py:383-424`):

```bash
python -m hummbl_cognition.consolidator run --dry-run
python -m hummbl_cognition.consolidator status
```

The Open Brain client (`client.py:150-242`):

```bash
python -m hummbl_cognition.client search "OAuth token refresh" --limit 5
python -m hummbl_cognition.client health
python -m hummbl_cognition.client reindex
```

The top-level `hummbl-cognition` console script (declared in `pyproject.toml`)
dispatches the `post`, `query`, `validate`, `state`, `boot`, `search`, and
`reindex` commands. See the [CLI Reference](../cli/index.md) for the full
command surface, flags, and examples, and the [API Reference](../reference/api-reference.md)
for the library functions each command wraps.

## Next steps

- [Architecture](../architecture/index.md) — the three-layer model and data flow.
- [API Reference](../reference/api-reference.md) — every public function and class.
- [Examples](../examples/index.md) — sample entries, queries, and multi-agent flows.
