# Migrations

The Cognitive Ledger Protocol can ingest knowledge from existing sources so
that a team can adopt the append-only ledger without losing prior learnings.
Three migration paths are exposed by the package facade:

```python
from hummbl_cognition import (
    import_from_bus_history,
    import_from_git_log,
    import_from_memory_md,
)
```

These are re-exported by `__init__.py:25-29` and listed in `__all__`
(`__init__.py:118-120`). Their implementation lives in the
`hummbl_governance.cognition.migration` module of the parent package; the standalone
`hummbl-cognition` distribution re-exports them so that the same import works
in both contexts.

> **Source pools:** the Open Brain client recognizes five memory pools —
> `ledger`, `bus`, `briefings`, `findings`, `memory_md` (`client.py:170-174`).
> The three migration functions cover the three most common on-disk sources:
> bus history, git log, and `memory.md` files.

Every migration produces `LedgerEntry` objects and writes them through
`post_entry()` (`ledger_writer.py:528-628`), so each imported entry receives the
full content scan, schema validation, hash verification, optional HMAC signing,
and locked append — exactly like a live agent write. This means migrations are
**idempotent-safe at the schema level**: any entry that fails
`_validate_entry_schema()` (`ledger_writer.py:463-525`) is rejected before it
reaches the ledger.

## Common transformation rules

All three migrations map source records onto the `LedgerEntry` schema. The
required fields and their constraints (from `_validate_entry_schema`,
`ledger_writer.py:475-525`) are:

| Target field | Rule | Source |
|---|---|---|
| `id` | Auto-generated as `clp-<12 hex>` by `LedgerEntry.create()` | `ledger_writer.py:481-482` |
| `timestamp` | ISO 8601; from the source record's time, or the import time if unavailable | `ledger_writer.py:475` |
| `agent` | The source's author/actor (e.g. a bus participant, a git author, or `human`) | `ledger_writer.py:567` |
| `vendor` | One of `anthropic`, `google`, `human`, `local`, `moonshot`, `openai` | `ledger_writer.py:485-487` |
| `model` | The source's model, or `"unknown"` / `"n/a"` for non-AI sources | `ledger_writer.py:475` |
| `type` | A canonical `LedgerEntryType` (`decision`, `correction`, `lesson`, `convention`, `discovery`) | `ledger_writer.py:491-495` |
| `scope` | A canonical `LedgerScope` (`project`, `global`, `session`) | `ledger_writer.py:498-502` |
| `content` | The source's text, truncated to 4096 chars | `ledger_writer.py:505-506` |
| `content_hash` | Auto-computed SHA-256 by `LedgerEntry.create()` | `ledger_writer.py:509-510` |
| `tags` | ≤ 10 tags; typically include a migration-source tag (e.g. `imported`, `from-bus`) | `ledger_writer.py:513-515` |
| `confidence` | `0.0`–`1.0`; often lower for imported entries (e.g. `0.5`) | `ledger_writer.py:518-520` |

Because `post_entry` enforces canonical `type` and `scope` at write time
(`ledger_writer.py:489-502`), any historical aliases in the source must be
mapped to canonical values during transformation. Readers tolerate aliases, but
new writes do not — this prevents schema drift from accumulating in the ledger.

---

## `import_from_bus_history`

Migrate records from the coordination bus history (the `bus` memory pool,
`client.py:172`) into the ledger.

### Source format

The bus is an append-only coordination system (the ledger writer "mirrors the
design of bus/bus_writer.py", `ledger_writer.py:7-8`). Bus history records
typically contain: a timestamp, a participant/agent, an event type, a payload,
and optional tags.

### Transformation rules

| Source field | Target field | Notes |
|---|---|---|
| bus timestamp | `timestamp` | Normalized to ISO 8601. |
| participant / agent | `agent` | Falls back to `"unknown"` if absent. |
| event type | `type` | Map bus event kinds to `LedgerEntryType`: decisions → `decision`, corrections → `correction`, learnings → `lesson`, conventions → `convention`, discoveries → `discovery`. Unknown kinds default to `discovery`. |
| bus scope / channel | `scope` | Map to canonical `LedgerScope`. Channel-specific → `session`; project-wide → `project`; cross-project → `global`. |
| payload text | `content` | Truncated to 4096 chars (`ledger_writer.py:505`). |
| bus tags | `tags` | Prepended with `imported`, `from-bus`; capped at 10. |
| — | `vendor` | Set to `"human"` or the participant's vendor if known. |
| — | `confidence` | Default `0.5` for imported bus records (lower than live entries). |

### Usage

```python
from hummbl_cognition import import_from_bus_history

result = import_from_bus_history(
    bus_path="hummbl_governance/_state/bus/history.jsonl",
    ledger_path="hummbl_governance/_state/cognition/ledger.jsonl",
)
print(result)  # e.g. {"imported": 342, "skipped": 3, "errors": [...]}
```

### Validation steps

1. Run `validate_integrity(ledger_path=...)` (`ledger_writer.py:798-860`) to
   confirm all imported entries parse and have valid content hashes.
2. Run `validate_integrity_report()` (`ledger_writer.py:901-964`) for a
   structured view; resolve any `parse_error` or `content_hash_mismatch`.
3. Spot-check a few entries with `read_entries(tags=["from-bus"])` to confirm
   field mapping.
4. Rebuild the index: `BM25Index().build(); .save()` so imported entries are
   searchable.

---

## `import_from_git_log`

Migrate knowledge embedded in commit messages into the ledger. This captures
decisions and conventions that were recorded only in version-control history.

### Source format

Git log entries: commit hash, author, date, and commit message (subject + body).
The migration typically scans `git log` output for conventional-commit prefixes
or decision markers.

### Transformation rules

| Source field | Target field | Notes |
|---|---|---|
| commit date | `timestamp` | Author date in ISO 8601. |
| author name/email | `agent` | Use the author's identifier; `vendor="human"`. |
| commit subject + body | `content` | Combined, truncated to 4096 chars. |
| conventional-commit prefix | `type` | `feat:`/`fix:` → `discovery` or `lesson`; `docs:` with a decision → `decision`; `refactor:` establishing a pattern → `convention`. Commits that revert → `correction` with `supersedes` left unset (no target ID available). |
| affected scope | `scope` | Repo-wide → `project`; config/global → `global`. |
| commit hash | `links` | Stored as a tag like `git:<short-hash>` or in `links` for traceability. |
| — | `tags` | `imported`, `from-git`, plus extracted keywords; capped at 10. |
| — | `model` | `"git"` or `"n/a"` (non-AI source). |
| — | `confidence` | Default `0.5`; raised for commits explicitly marked as decisions. |

### Usage

```python
from hummbl_cognition import import_from_git_log

result = import_from_git_log(
    repo_path=".",
    ledger_path="hummbl_governance/_state/cognition/ledger.jsonl",
    since="2025-01-01",  # optional: only commits after this date
)
print(result)
```

### Validation steps

1. Run `validate_integrity()` on the ledger.
2. Verify no commit message exceeded the 4096-char content cap (check the
   `errors` list in the result for truncation warnings).
3. Confirm `vendor` is `"human"` and `type` values are canonical by querying:
   `read_entries(tags=["from-git"])`.
4. Rebuild the BM25 index so commit-derived entries are searchable alongside
   live entries.

---

## `import_from_memory_md`

Migrate knowledge from free-form `memory.md` (or `MEMORY.md`) markdown files —
the `memory_md` memory pool (`client.py:174`). This is the most common starting
point for teams that have been keeping notes in a single markdown file.

### Source format

A markdown file with headings, bullet points, and prose. The migration parses
the file into discrete knowledge items, typically splitting on headings or
bullet boundaries.

### Transformation rules

| Source element | Target field | Notes |
|---|---|---|
| heading level / section | `type` | Top-level "Decisions" → `decision`; "Lessons" / "Learnings" → `lesson`; "Conventions" / "Patterns" → `convention`; "Discoveries" → `discovery`. Unsectioned bullets default to `discovery`. |
| bullet / paragraph text | `content` | Truncated to 4096 chars. |
| file's last-modified time | `timestamp` | Falls back to import time if unavailable. |
| author (from frontmatter or filename) | `agent` | Defaults to `"human"`. |
| — | `vendor` | `"human"` (markdown is human-authored). |
| — | `model` | `"n/a"`. |
| — | `scope` | `"project"` by default; override per-section if the file mixes scopes. |
| markdown emphasis / inline code | `tags` | Extracted keywords; prepend `imported`, `from-memory-md`; cap at 10. |
| — | `confidence` | `0.6` (human-authored, but unverified). |

### Usage

```python
from hummbl_cognition import import_from_memory_md

result = import_from_memory_md(
    memory_path="MEMORY.md",
    ledger_path="hummbl_governance/_state/cognition/ledger.jsonl",
)
print(result)
```

### Validation steps

1. Run `validate_integrity()` and `validate_integrity_report()`.
2. Query the imported set: `read_entries(tags=["from-memory-md"])` and verify
   that section-to-type mapping is correct.
3. If the markdown contained any prompt-injection phrasing or credentials,
   `post_entry` will have raised `ContentScanError` (`ledger_writer.py:341-395`)
   — review the `errors` list and clean the source file before re-importing.
4. Rebuild the index: `BM25Index().build(); .save()`.

---

## Post-migration checklist

After any migration, run this sequence to ensure the ledger is consistent and
searchable:

```python
from hummbl_cognition.ledger_writer import validate_integrity, validate_integrity_report
from hummbl_cognition.indexer import BM25Index
from hummbl_cognition.query import active_entries
import json

# 1. Integrity check
valid, errors = validate_integrity()
assert not errors, f"{len(errors)} integrity errors: {errors[:3]}"

# 2. Structured report (for the record)
report = validate_integrity_report()
print(json.dumps(report["errors"], indent=2))

# 3. Rebuild the search index
idx = BM25Index()
count = idx.build()
idx.save()
print(f"Indexed {count} entries")

# 4. Confirm active set is sane
active = active_entries(limit=500)
print(f"{len(active)} active entries after migration")
```

### Avoiding duplicate imports

Because the ledger is append-only, re-running a migration will create duplicate
entries. To prevent this:

- Tag every imported entry with a source-specific tag (`from-bus`, `from-git`,
  `from-memory-md`) plus a batch identifier (e.g. `import-2026-06-25`).
- Before re-importing, check for existing entries with that batch tag:
  `read_entries(tags=["import-2026-06-25"])`. If any exist, the batch was
  already imported.
- The migration functions themselves are designed to skip records that have
  already been consolidated (mirroring the consolidator's
  `_get_consolidated_ids` pattern, `consolidator.py:104-112`), but a batch tag
  is the simplest manual guard.

### Running the consolidator after migration

Once imported entries are in the ledger, run the consolidator to group and
synthesize related entries from different sources:

```bash
python -m hummbl_cognition.consolidator run
```

This will produce `convention` entries (tagged `consolidated`) that link the
imported source entries together (`consolidator.py:346-355`), giving agents a
unified view of pre-protocol and post-protocol knowledge.
