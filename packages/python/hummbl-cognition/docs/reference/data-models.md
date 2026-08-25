# Data Models

This document covers every data model in the Cognitive Ledger Protocol. The
model classes (`LedgerEntry`, `LedgerEntryType`, `LedgerScope`, `SharedState`)
are defined in the `models` module of the parent `hummbl_governance.cognition`
package and re-exported by `hummbl_cognition/__init__.py:30-35`. Their exact
shape is enforced throughout this package by `_validate_entry_schema()`
(`ledger_writer.py:463-525`) and by how each field is read across
`query.py`, `indexer.py`, `boot_context.py`, and `consolidator.py`.

> **Import path:** in the installed `hummbl-cognition` package, import from
> `hummbl_cognition.models`. In the in-repo source the imports read
> `hummbl_governance.cognition.models`; the classes are identical.

---

## `LedgerEntry`

The atomic unit of the append-only ledger. One `LedgerEntry` serializes to
exactly one JSONL line in `ledger.jsonl`.

### Fields

| Field | Type | Required | Valid values / constraints | Source evidence |
|---|---|---|---|---|
| `id` | `str` | yes | Format `clp-<12 hex chars>` (`^clp-[a-f0-9]{12}$`) | `ledger_writer.py:481-482` |
| `timestamp` | `str` | yes | ISO 8601, e.g. `2026-06-25T14:30:00Z` | `ledger_writer.py:475`; written by `feedback_tracker.py:92` style |
| `agent` | `str` | yes | Agent identifier (e.g. `claude-code`, `consolidator`); substring-filtered in queries | `ledger_writer.py:567-568`, `query.py` `agent` filter |
| `vendor` | `str` | yes | One of `anthropic`, `google`, `human`, `local`, `moonshot`, `openai` | `ledger_writer.py:485-487` |
| `model` | `str` | yes | Model name (e.g. `claude-opus-4`, `qwen3.5:9b`) | `ledger_writer.py:475`; consolidator sets it to the Ollama model (`consolidator.py:350`) |
| `type` | `str` | yes | A canonical `LedgerEntryType` value (see below) | `ledger_writer.py:491-495` |
| `scope` | `str` | yes | A canonical `LedgerScope` value (see below) | `ledger_writer.py:498-502` |
| `content` | `str` | yes | Max 4096 characters (`MAX_CONTENT_BYTES`) | `ledger_writer.py:45, 505-506` |
| `content_hash` | `str` | yes | 64-char lowercase SHA-256 hex (`^[a-f0-9]{64}$`) | `ledger_writer.py:509-510`; verified by `verify_hash()` |
| `tags` | `list[str]` | no | Max 10 tags | `ledger_writer.py:513-515`; indexed in `indexer.py:120` |
| `confidence` | `float \| None` | no | `0.0 ≤ confidence ≤ 1.0` | `ledger_writer.py:518-520`; stored in `doc_meta` (`indexer.py:135`) |
| `assurance_level` | `str \| None` | no | One of `SELF`, `PEER`, `VERIFIED` | `ledger_writer.py:523-525` |
| `evidence` | `str \| None` | no | Supporting text; scanned for injection/credentials like `content` | `ledger_writer.py:563-564` |
| `signature` | `str \| None` | no | HMAC-SHA256 hex; set by `post_entry` when a signing secret is available | `ledger_writer.py:595-601, 631-658` |
| `supersedes` | `str \| None` | no | ID of an earlier entry this one replaces | `query.py:57-61` (`active_entries`) |
| `links` | `list[str]` | no | IDs of related entries (Zettelkasten-style); used for consolidation grouping and stored in `doc_meta` | `consolidator.py:145-191`, `indexer.py:138` |

### Methods (used across the package)

| Method | Description | Source evidence |
|---|---|---|
| `LedgerEntry.create(content, agent, vendor, model, entry_type, scope, tags=..., confidence=..., ...)` | Construct an entry, generating `id`, `timestamp`, and `content_hash`. | Called in `consolidator.py:346-355` |
| `to_dict() -> dict` | Serialize to a plain dict. | `ledger_writer.py:472, 599, 653-654` |
| `from_dict(d) -> LedgerEntry` | Deserialize from a dict. | `ledger_writer.py:601, 654-655, 829` |
| `to_jsonl() -> str` | Serialize to a single JSONL line (no trailing newline). | `ledger_writer.py:596, 603, 656` |
| `verify_hash() -> bool` | Recompute the content hash and compare to `content_hash`. | `ledger_writer.py:584, 837` |

### Example serialized line

```json
{"id":"clp-a1b2c3d4e5f6","timestamp":"2026-06-25T14:30:00Z","agent":"claude-code","vendor":"anthropic","model":"claude-opus-4","type":"lesson","scope":"project","content":"Pin SDK versions in requirements.txt to avoid silent breakage.","content_hash":"9f2c...","tags":["python","dependencies"],"confidence":0.9,"assurance_level":"SELF","links":[]}
```

---

## `LedgerEntryType`

The canonical entry types. The set of valid values is enforced at write time
against `CANONICAL_LEDGER_TYPES` (`ledger_writer.py:491-495`); historical
aliases are accepted on **read** but rejected on **write** to prevent schema
drift. The priority ordering used for boot-context summarization is defined in
`query.py:105-111` and `boot_context.py:38-44`:

| Type | Priority | Meaning |
|---|---|---|
| `decision` | 0 (highest) | A committed decision; surfaces first in boot context. |
| `correction` | 1 | A correction that supersedes an earlier entry. |
| `lesson` | 2 | A learned insight or takeaway. |
| `convention` | 3 | An established convention (also the type used for consolidated entries, `consolidator.py:351`). |
| `discovery` | 4 | A newly discovered fact. |

> The consolidator posts entries of type `convention` with
> `tags: ["consolidated", ...]` and `links` to their source entries
> (`consolidator.py:346-355`).

---

## `LedgerScope`

The canonical scopes. Enforced at write time against `CANONICAL_LEDGER_SCOPES`
(`ledger_writer.py:498-502`); historical aliases are read-only. Scopes partition
the ledger by applicability breadth. Observed values in the codebase:

| Scope | Usage |
|---|---|
| `project` | Project-wide knowledge. Used by the consolidator for synthesized entries (`consolidator.py:352`). |
| `global` | Cross-project knowledge. |
| `session` | Ephemeral, session-scoped knowledge. |

`latest_by_scope()` (`query.py:64-79`) returns the most recent active entry per
scope, and `BM25Index.search(scope=...)` (`indexer.py:214`) filters results by
scope.

---

## `SharedState`

The mutable snapshot stored in `state.json` (Layer 1). Parsed via
`SharedState.from_dict(data)` in `build_boot_context()` (`boot_context.py:181`).
Its fields are rendered into the boot context (`boot_context.py:183-209`):

| Field | Type | Required | Description | Source evidence |
|---|---|---|---|---|
| `sprint` | `dict \| None` | no | Current sprint info; must contain a `name` key (rendered as `Sprint: <name>`). | `boot_context.py:184-186` |
| `active_agents` | `dict[str, dict] \| None` | no | Map of agent ID → info dict containing a `status` key. Rendered as `Agents: id (status), ...`. | `boot_context.py:188-193` |
| `claimed_files` | `dict[str, dict] \| None` | no | Map of file path → `{agent, purpose}`. Rendered as `Claimed: <path> (<agent>) -- <purpose>`. | `boot_context.py:195-200` |
| `flags` | `dict[str, Any] \| None` | no | Arbitrary key-value flags. Rendered as `Flags: k=v, ...` (sorted). | `boot_context.py:202-206` |

### Example `state.json`

```json
{
  "sprint": {"name": "cognition-hardening"},
  "active_agents": {
    "claude-code": {"status": "writing docs"},
    "cursor": {"status": "idle"}
  },
  "claimed_files": {
    "docs/architecture/index.md": {"agent": "claude-code", "purpose": "diagrams"}
  },
  "flags": {"kill_switch": false, "consolidation_enabled": true}
}
```

---

## Relationships between models

```
SharedState (state.json)          LedgerEntry (ledger.jsonl)
        │                                │
        │  rendered into                 │  filtered / searched
        │  boot context                  │  via query.py / indexer.py
        ▼                                ▼
   build_boot_context() ────────── summarize_for_boot()
        │                                │
        │  also reads intent.md          │  active_entries() resolves
        │  (Layer 3)                     │  supersedes chains
        ▼                                ▼
   markdown boot context           BM25Index (index.json)
   (frozen per session)            (derived, rebuildable)
```

- A **`LedgerEntry`** of type `correction` points its `supersedes` field at an
  earlier entry's `id`; `active_entries()` removes the superseded entry from
  the active set (`query.py:54-61`).
- A **consolidated `LedgerEntry`** (type `convention`, tag `consolidated`) uses
  its `links` field to point at the source entry IDs it synthesizes
  (`consolidator.py:346-355`); `_get_consolidated_ids()` collects those links to
  skip already-consolidated entries (`consolidator.py:104-112`).
- **`SharedState`** is independent of the ledger but co-rendered with it in the
  boot context. It is the only mutable layer; the ledger is append-only.
- **`LedgerEntryType`** and **`LedgerScope`** are the controlled vocabularies
  that keep the ledger queryable and the index coherent. New writes must use
  canonical values; readers tolerate historical aliases
  (`ledger_writer.py:489-502`).
