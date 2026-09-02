# API Reference

Complete reference for every public class and function in `hummbl_cognition`,
grounded in the source. Modules are documented in dependency order. Each entry
lists the source file and line numbers, signature, parameters, return type, and
an example.

> **Note on imports:** the in-repo source imports models from
> `hummbl_governance.cognition.models` (the parent package). When using the
> installed `hummbl-cognition` package, import models from
> `hummbl_cognition.models`. The functions below are otherwise identical.

---

## `ledger_writer.py` — Append-only JSONL writer

The canonical write path and integrity layer. 976 lines.

### `post_entry(entry, *, ledger_path=None, secret=None) -> LedgerEntry`

`ledger_writer.py:528-628`

Append a `LedgerEntry` to the ledger under an exclusive advisory lock. This is
the **only** sanctioned write path.

**Parameters**

| Name | Type | Default | Description |
|---|---|---|---|
| `entry` | `LedgerEntry` | required | The entry to write. Must have a valid `content_hash`. |
| `ledger_path` | `str \| Path \| None` | `None` | Override ledger path. Falls back to `COGNITION_LEDGER` env, then git-root default. |
| `secret` | `bytes \| None` | `None` | HMAC-SHA256 key. Falls back to `BUS_SIGNING_SECRET` env (must be ≥ 32 bytes). |

**Returns:** `LedgerEntry` — the entry as written (includes `signature` if
signing was enabled).

**Raises:** `ValueError` (schema/hash/validation failure),
`ContentScanError` (prompt injection / credential / exfiltration / invisible
Unicode), `PIIDetectedError` (when `PII_SCAN_STRICT=true`), `OSError` (I/O).

**Pipeline:** content scan → PII scan → schema validation → hash verification →
HMAC signing → locked append → permission hardening.

```python
from hummbl_cognition.ledger_writer import post_entry
from hummbl_cognition.models import LedgerEntry

entry = LedgerEntry.create(
    content="Pin SDK versions in requirements.txt.",
    agent="claude-code",
    vendor="anthropic",
    model="claude-opus-4",
    entry_type="lesson",
    scope="project",
    tags=["python"],
    confidence=0.9,
)
written = post_entry(entry, ledger_path="ledger.jsonl")
```

### `read_entries(*, ledger_path=None, since=None, entry_type=None, scope=None, agent=None, tags=None, limit=100, verify_signatures=False, signing_key=None, delegation_token=None) -> list[LedgerEntry]`

`ledger_writer.py:661-795`

Read and filter ledger entries, most recent first.

**Parameters**

| Name | Type | Default | Description |
|---|---|---|---|
| `ledger_path` | `str \| Path \| None` | `None` | Override ledger path. |
| `since` | `str \| None` | `None` | ISO 8601 timestamp; only entries after this are returned. |
| `entry_type` | `str \| LedgerEntryType \| None` | `None` | Filter by entry type. |
| `scope` | `str \| LedgerScope \| None` | `None` | Filter by scope. |
| `agent` | `str \| None` | `None` | Substring match on agent identifier. |
| `tags` | `list[str] \| None` | `None` | Entries must contain **all** listed tags. |
| `limit` | `int` | `100` | Max entries to return (most recent first). |
| `verify_signatures` | `bool` | `False` | Drop entries whose HMAC signature fails. Unsigned entries pass through. |
| `signing_key` | `bytes \| None` | `None` | HMAC key; falls back to `BUS_SIGNING_SECRET`. |
| `delegation_token` | `object \| None` | `None` | IDP token; when `ENABLE_IDP` is true it must include `"read:ledger"` in `ops_allowed`. |

**Returns:** `list[LedgerEntry]`, most recent first. Returns `[]` if the file
does not exist.

**Raises:** `PermissionError` — when `ENABLE_IDP` is true, a token is supplied,
and it lacks `"read:ledger"` (`ledger_writer.py:718-728`).

```python
from hummbl_cognition.ledger_writer import read_entries

recent = read_entries(ledger_path="ledger.jsonl", entry_type="lesson", limit=5)
signed_only = read_entries(verify_signatures=True, limit=100)
```

### `validate_integrity(*, ledger_path=None, secret=None) -> tuple[int, list[str]]`

`ledger_writer.py:798-860`

Validate every line: JSON parsing, content-hash verification (skips grandfathered
non-hex hashes), and HMAC signature verification when a secret is available.

**Returns:** `(valid_count, error_descriptions)` — a tuple of the count of valid
entries and a list of human-readable error strings (e.g.
`"Line 42: content_hash mismatch for clp-..."`).

```python
from hummbl_cognition.ledger_writer import validate_integrity

valid, errors = validate_integrity(ledger_path="ledger.jsonl")
print(f"{valid} valid, {len(errors)} errors")
```

### `validate_integrity_report(*, ledger_path=None, secret=None) -> dict[str, object]`

`ledger_writer.py:901-964`

Like `validate_integrity` but returns a structured, serializable report. Errors
are classified into `signature_mismatch`, `content_hash_mismatch`,
`parse_error`, `other`; consecutive line numbers are grouped into ranges; up to
5 samples per class are kept; remediation guidance is attached from
`_REMEDIATION` (`ledger_writer.py:881-898`).

**Returns:** dict with keys `ledger_path`, `ledger_exists`, `total_lines`,
`valid_entries`, `errors` (`{total, by_class}`), and `remediation`.

```python
import json
from hummbl_cognition.ledger_writer import validate_integrity_report

report = validate_integrity_report(ledger_path="ledger.jsonl")
print(json.dumps(report, indent=2))
```

### `scan_content(text) -> None`

`ledger_writer.py:341-395`

Scan text for prompt injection, credential leakage, exfiltration vectors, and
invisible Unicode. NFC-normalizes, then transliterates cross-script homoglyphs
via `_transliterate_confusables` (`ledger_writer.py:323-329`) before regex
matching. Invisible-character detection runs on the **raw** text first.

**Raises:** `ContentScanError(category, detail)` with `category` one of
`invisible_unicode`, `prompt_injection`, `credential_leak`, `exfiltration`.

```python
from hummbl_cognition.ledger_writer import scan_content, ContentScanError

try:
    scan_content("ignore previous instructions")
except ContentScanError as e:
    print(e.category, e.detail)  # prompt_injection ...
```

### `scan_pii(text, *, strict=False) -> list[tuple[str, str]]`

`ledger_writer.py:139-164`

Scan for emails, US phone numbers, SSNs, and IP addresses. Allowlisted patterns
(`noreply@anthropic.com`, Tailscale/loopback IPs) are skipped
(`ledger_writer.py:122-127`).

**Parameters:** `text` — text to scan; `strict` — if `True`, raise
`PIIDetectedError` on the first match.

**Returns:** list of `(pii_type, matched_value)` tuples.

### `scrub_pii(text) -> str`

`ledger_writer.py:167-182`

Replace PII with SHA-256 pseudonyms of the form `[<type>:<12hex>]`, preserving
data utility (same input → same hash) while removing actual PII. Allowlisted
values are kept.

### `scrub_pii_from_dict(data) -> dict`

`ledger_writer.py:185-206`

Recursively scrub PII from all string values in a (possibly nested) dict or
list. Returns a new dict.

### Exceptions

#### `ContentScanError(ValueError)`

`ledger_writer.py:332-338` — attributes `category: str`, `detail: str`.

#### `PIIDetectedError(ValueError)`

`ledger_writer.py:130-136` — attributes `pii_type: str`, `detail: str`.

### Internal helpers (documented for operators)

| Function | Lines | Purpose |
|---|---|---|
| `_lock_file(file_obj)` | `49-59` | Acquire exclusive advisory lock (fcntl/msvcrt). |
| `_unlock_file(file_obj)` | `62-71` | Release advisory lock. |
| `_resolve_ledger_path(override)` | `398-425` | Resolve ledger path (override → env → git root). |
| `_resolve_signing_secret()` | `428-441` | Resolve HMAC secret from `BUS_SIGNING_SECRET` (warns if < 32 bytes). |
| `_sign_entry(entry_jsonl, secret)` | `444-448` | Compute HMAC-SHA256 hex digest of a JSONL line. |
| `_verify_entry_signature(entry, raw_line, signing_key)` | `631-658` | Verify a signature with `hmac.compare_digest`. |
| `_harden_file_permissions(path)` | `451-460` | chmod ledger to `0o660`. |
| `_validate_entry_schema(entry)` | `463-525` | Stdlib schema validation (required fields, enums, limits). |
| `_classify_error(error)` | `967-976` | Classify an error string into a category name. |

---

## `query.py` — Query interface

Filtered queries, supersedes-chain resolution, and boot summarization. 129 lines.

### `query_entries(*, ledger_path=None, entry_type=None, scope=None, agent=None, since=None, tags=None, limit=50) -> list[LedgerEntry]`

`query.py:16-38`

Thin wrapper around `read_entries` with query-friendly defaults (`limit=50`).

```python
from hummbl_cognition.query import query_entries

decisions = query_entries(entry_type="decision", scope="project", limit=10)
```

### `active_entries(*, ledger_path=None, limit=200) -> list[LedgerEntry]`

`query.py:41-61`

Return entries that have **not** been superseded. Collects every `supersedes`
target across all entries and filters out those IDs.

```python
from hummbl_cognition.query import active_entries

current = active_entries(ledger_path="ledger.jsonl")
```

### `latest_by_scope(*, ledger_path=None, limit=500) -> dict[str, LedgerEntry]`

`query.py:64-79`

Return the most recent active entry per scope. Because `active_entries` already
returns most-recent-first, the first entry seen for each scope wins.

```python
from hummbl_cognition.query import latest_by_scope

by_scope = latest_by_scope()  # {"project": LedgerEntry, "global": LedgerEntry, ...}
```

### `summarize_for_boot(*, ledger_path=None, max_entries=50, max_age_days=30) -> str`

`query.py:82-129`

Produce a compact markdown summary of recent active entries, prioritized
`decision > correction > lesson > convention > discovery` (`query.py:105-111`),
filtered to the last `max_age_days`. Returns `"No recent learnings."` when
empty. Each line: `- [YYYY-MM-DD] (agent) TYPE: content [tags]`.

```python
from hummbl_cognition.query import summarize_for_boot

print(summarize_for_boot(max_entries=20, max_age_days=7))
```

---

## `indexer.py` — BM25 index

`indexer.py:324` lines. Storage default: `hummbl_governance/_state/cognition/index.json`.

### `tokenize(text) -> list[str]`

`indexer.py:46-49`

Lowercase, match `[a-z0-9_]+(?:\.[a-z0-9_]+)*`, drop stopwords (`_STOPWORDS`,
`indexer.py:34-41`) and single-character tokens.

### `BM25Index(index_path=None)`

`indexer.py:72-324`

BM25 inverted term index over ledger entries. Tuning constants: `BM25_K1 = 1.5`,
`BM25_B = 0.75` (`indexer.py:30-31`).

**Attributes:** `inverted_index` (`term → [(doc_id, tf)]`),
`doc_lengths` (`doc_id → token count`), `doc_meta` (`doc_id → metadata dict`),
`retrieval_counts` (`doc_id → count`), `total_docs`, `avg_doc_length`,
`built_at`, `entry_count`.

#### `build(ledger_path=None) -> int`

`indexer.py:94-155` — Build the index from all ledger entries. Returns the
count indexed. Searchable text per entry = `content + type + scope + agent +
tags`. Stores a 200-char `content_preview` plus `tags` and `links` in
`doc_meta`.

#### `search(query, *, limit=20, scope=None, entry_type=None, since=None, boost_retrievals=True) -> list[dict[str, Any]]`

`indexer.py:157-224` — BM25 search. Returns `[{"id", "score", "meta"}, ...]`
sorted by score descending. Stigmergic boost up to +20% for frequently
retrieved entries when `boost_retrievals=True`.

```python
from hummbl_cognition.indexer import BM25Index

idx = BM25Index()
idx.build(ledger_path="ledger.jsonl")
for r in idx.search("OAuth token refresh", scope="project", limit=5):
    print(r["score"], r["meta"]["content_preview"])
```

#### `record_retrieval(entry_id) -> None`

`indexer.py:226-230` — Increment the retrieval counter for an entry (feeds
stigmergic ranking).

#### `add_document(doc_id, text, metadata=None) -> None`

`indexer.py:232-251` — Incrementally add one document without a full rebuild;
updates `avg_doc_length` incrementally.

#### `save(path=None) -> Path`

`indexer.py:253-289` — Crash-safe save (temp + fsync + atomic rename). Returns
the saved path.

#### `load(path=None) -> bool`

`indexer.py:291-324` — Load from disk. Returns `True` on success, `False` if
the file is missing or corrupt.

---

## `boot_context.py` — Boot context builder

`boot_context.py:235` lines.

### `build_boot_context(cognition_dir=None, *, max_entries=50, max_age_days=30) -> str`

`boot_context.py:138-235`

Build a complete, frozen-snapshot boot context from all three layers and return
it as markdown. Reads `intent.md`, `state.json` (parsed into `SharedState`), and
`ledger.jsonl` (summarized via the index when available, else sequential scan).

**Parameters**

| Name | Type | Default | Description |
|---|---|---|---|
| `cognition_dir` | `str \| Path \| None` | `None` | Cognition directory (override → `COGNITION_DIR` env → git root + default). |
| `max_entries` | `int` | `50` | Max ledger entries in the summary. |
| `max_age_days` | `int` | `30` | Only include entries from the last N days. |

**Returns:** `str` — markdown starting with `# Cognitive Ledger Boot Context`.
If nothing is found, appends `No cognitive data available yet.`

```python
from hummbl_cognition.boot_context import build_boot_context

ctx = build_boot_context("/path/to/cognition", max_age_days=14)
# Inject once into the agent system prompt.
```

---

## `consolidator.py` — Nightly consolidation

`consolidator.py:428` lines. Append-only and idempotent.

### `run_consolidation(*, ledger_path=None, dry_run=False, model=DEFAULT_MODEL, base_url=DEFAULT_OLLAMA_URL) -> dict[str, Any]`

`consolidator.py:263-366`

Run one consolidation pass. Groups unconsolidated entries by Zettelkasten links
(episodic) then by Jaccard similarity (semantic), synthesizes each group via
Ollama, and posts a `convention` entry tagged `consolidated` with `links` to the
sources.

**Parameters**

| Name | Type | Default | Description |
|---|---|---|---|
| `ledger_path` | `str \| Path \| None` | `None` | Override ledger path. |
| `dry_run` | `bool` | `False` | Show groups without writing. |
| `model` | `str` | `"qwen3.5:9b"` | Ollama model for synthesis. |
| `base_url` | `str` | `"http://127.0.0.1:11434"` | Ollama base URL. |

**Returns:** `{"groups_found", "consolidated", "skipped", "errors"}`.

**Safety:** checks the kill switch before the run and before each LLM call
(`consolidator.py:274-277, 319-321`); caps at 20 groups per run
(`MAX_CONSOLIDATIONS_PER_RUN`); falls back to concatenation if Ollama is down.

```python
from hummbl_cognition.consolidator import run_consolidation

result = run_consolidation(dry_run=True)
print(result)  # {"groups_found": 3, "consolidated": 3, "skipped": 0, "errors": []}
```

### `status(*, ledger_path=None) -> dict[str, Any]`

`consolidator.py:369-380`

Report consolidation status.

**Returns:** `{"total_entries", "consolidated_entries", "source_entries_covered",
"unconsolidated"}`.

### `main(argv=None) -> int`

`consolidator.py:383-424` — CLI entry point with `run` and `status`
subcommands (see [CLI Reference](../cli/index.md)).

### Constants

| Constant | Value | Location |
|---|---|---|
| `DEFAULT_OLLAMA_URL` | `http://127.0.0.1:11434` | `consolidator.py:43` |
| `DEFAULT_MODEL` | `qwen3.5:9b` | `consolidator.py:44` |
| `MIN_GROUP_SIZE` | `2` | `consolidator.py:45` |
| `MAX_GROUP_SIZE` | `10` | `consolidator.py:46` |
| `SIMILARITY_THRESHOLD` | `0.13` | `consolidator.py:47` |
| `MAX_CONSOLIDATIONS_PER_RUN` | `20` | `consolidator.py:48` |

---

## `feedback_tracker.py` — Retrieval log

`feedback_tracker.py:172` lines. Append-only JSONL at
`hummbl_governance/_state/cognition/retrieval_log.jsonl`.

### `log_retrieval(*, query, entry_ids, agent="unknown", session_id="", log_path=None) -> None`

`feedback_tracker.py:79-109`

Append a retrieval event under an exclusive advisory lock. The query is
truncated to 500 chars and `entry_ids` capped at 50 (`feedback_tracker.py:94-95`).

```python
from hummbl_cognition.feedback_tracker import log_retrieval

log_retrieval(
    query="oauth refresh",
    entry_ids=["clp-abc123def456"],
    agent="claude-code",
    session_id="s-42",
)
```

### `get_retrieval_counts(*, log_path=None, since=None) -> dict[str, int]`

`feedback_tracker.py:112-143`

Aggregate retrieval counts per entry ID. Returns `{entry_id: count}`.

### `read_retrieval_log(*, log_path=None, limit=100) -> list[dict[str, Any]]`

`feedback_tracker.py:146-172`

Read recent retrieval events, most recent first.

---

## `client.py` — Open Brain HTTP client

`client.py:246` lines. Stdlib-only HTTP. Default server
`http://localhost:11435` (`client.py:31`).

### `OpenBrainClient(url=None, *, timeout=30, token=None)`

`client.py:37-147`

HTTP client for a remote Open Brain server.

**Parameters**

| Name | Type | Default | Description |
|---|---|---|---|
| `url` | `str \| None` | `None` | Server URL; falls back to `OPEN_BRAIN_URL` env, then `DEFAULT_URL`. |
| `timeout` | `int` | `30` | Request timeout in seconds. |
| `token` | `str \| None` | `None` | Bearer token; falls back to `OPEN_BRAIN_TOKEN` env. |

**Response safety:** reads at most `MAX_RESPONSE_SIZE = 10 MB` per response
(`client.py:34, 74`).

#### `search(query, *, token_budget=2000, scope=None, entry_type=None, since=None, sources=None, agent="remote-client", limit=20) -> list[dict[str, Any]]`

`client.py:91-123` — `POST /search`. Returns result dicts with `source`,
`entry_id`, `score`, `content`, `metadata`, `tokens`. `sources` filters memory
pools: `ledger`, `bus`, `briefings`, `findings`, `memory_md`
(`client.py:170-174`).

#### `status() -> dict[str, Any]`

`client.py:125-127` — `GET /status`.

#### `health() -> bool`

`client.py:129-135` — `GET /health`; returns `True` only if `status == "ok"`.

#### `reindex() -> dict[str, Any]`

`client.py:137-139` — `POST /reindex`.

#### `ingest(entries) -> dict[str, Any]`

`client.py:141-147` — `POST /ingest` with `{"entries": entries}`. Used by
secondary brains to federate findings to the primary brain.

```python
from hummbl_cognition.client import OpenBrainClient

brain = OpenBrainClient("http://100.64.0.1:11435")
for r in brain.search("OAuth refresh", limit=5):
    print(r["score"], r["content"][:80])
```

### `main(argv=None) -> int`

`client.py:150-242` — CLI entry point with `search`, `status`, `reindex`, and
`health` subcommands (see [CLI Reference](../cli/index.md)).

---

## `__init__.py` — Package facade

`__init__.py:158` lines. Re-exports the public API into `__all__`
(`__init__.py:96-158`). Notable re-exports:

- From `ledger_writer`: `post_entry`, `read_entries`, `validate_integrity`.
- From `models`: `LedgerEntry`, `LedgerEntryType`, `LedgerScope`, `SharedState`.
- From `indexer`: `BM25Index`.
- From `boot_context`: `build_boot_context`.

> The facade also references sibling modules (`migration`, `schema_validator`,
> `state_manager`, `verified_writer`, `sigil_forge`, `startup_context`,
> `retriever`) that live in the parent `hummbl_governance` package and are not
> shipped in the standalone `hummbl-cognition` distribution. The eight modules
> documented above constitute the complete in-repo code surface.
