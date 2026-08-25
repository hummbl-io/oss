# Examples

Concrete, copy-pasteable examples grounded in the `hummbl_cognition` source.
Each example references the exact functions and line numbers it exercises.

## Sample `ledger.jsonl` entries

Each line is one `LedgerEntry` serialized via `to_jsonl()`
(`ledger_writer.py:603`). Fields are enforced by `_validate_entry_schema()`
(`ledger_writer.py:463-525`).

```jsonl
{"id":"clp-a1b2c3d4e5f6","timestamp":"2026-06-20T09:14:00Z","agent":"claude-code","vendor":"anthropic","model":"claude-opus-4","type":"lesson","scope":"project","content":"Pin SDK versions in requirements.txt to avoid silent breakage.","content_hash":"9f2c3a1b7e8d4f6a2c5b8e1d3f7a9c2b4e6f8a1d3c5b7e9f2a4d6c8b0e2f4a6","tags":["python","dependencies"],"confidence":0.9,"assurance_level":"SELF","links":[]}
{"id":"clp-b2c3d4e5f6a7b8","timestamp":"2026-06-21T11:02:00Z","agent":"cursor","vendor":"openai","model":"gpt-4o","type":"decision","scope":"project","content":"Adopt the Cognitive Ledger Protocol for all agent memory writes.","content_hash":"1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b","tags":["architecture","clp"],"confidence":0.95,"assurance_level":"PEER","links":[]}
{"id":"clp-c3d4e5f6a7b8c9","timestamp":"2026-06-22T16:45:00Z","agent":"claude-code","vendor":"anthropic","model":"claude-opus-4","type":"correction","scope":"project","content":"Earlier lesson was too broad: only pin major.minor, allow patch to float for security fixes.","content_hash":"3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4","tags":["python","dependencies"],"confidence":0.85,"assurance_level":"SELF","supersedes":"clp-a1b2c3d4e5f6","links":["clp-a1b2c3d4e5f6"]}
{"id":"clp-d4e5f6a7b8c9d0","timestamp":"2026-06-23T08:30:00Z","agent":"consolidator","vendor":"local","model":"qwen3.5:9b","type":"convention","scope":"project","content":"Dependency management: pin major.minor versions; allow patch floats for security. Decided 2026-06-21.","content_hash":"5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6","tags":["consolidated","group-size-3"],"assurance_level":"SELF","links":["clp-a1b2c3d4e5f6","clp-b2c3d4e5f6a7b8","clp-c3d4e5f6a7b8c9"]}
```

Note the relationships:

- `clp-c3d4...` is a `correction` whose `supersedes` points at `clp-a1b2...`.
  `active_entries()` (`query.py:41-61`) will exclude `clp-a1b2...` from the
  active set.
- `clp-d4e5...` is a consolidated `convention` whose `links` point at the three
  source entries (`consolidator.py:346-355`). Its `tags` include `consolidated`.

## Sample `state.json`

Consumed by `build_boot_context()` (`boot_context.py:176-213`) and parsed via
`SharedState.from_dict()` (`boot_context.py:181`).

```json
{
  "sprint": {"name": "cognition-hardening"},
  "active_agents": {
    "claude-code": {"status": "writing docs"},
    "cursor": {"status": "reviewing PR"},
    "gemini-cli": {"status": "idle"}
  },
  "claimed_files": {
    "docs/architecture/index.md": {"agent": "claude-code", "purpose": "diagrams"},
    "hummbl_cognition/indexer.py": {"agent": "cursor", "purpose": "BM25 tuning"}
  },
  "flags": {"kill_switch": false, "consolidation_enabled": true}
}
```

Rendered by `build_boot_context()` as:

```
## Shared State
- Sprint: cognition-hardening
- Agents: claude-code (writing docs), cursor (reviewing PR), gemini-cli (idle)
- Claimed: docs/architecture/index.md (claude-code) -- diagrams
- Claimed: hummbl_cognition/indexer.py (cursor) -- BM25 tuning
- Flags: consolidation_enabled=true, kill_switch=false
```

## Sample `intent.md`

Read verbatim under `## Current Intent` (`boot_context.py:164-174`).

```markdown
# Sprint Goal: Cognition Hardening

Harden the Cognitive Ledger Protocol against multi-agent concurrency and
prompt-injection attacks. Ship BM25 stigmergic ranking. Zero third-party
runtime dependencies.

## Priorities
1. File-lock correctness across POSIX and Windows.
2. Content scanning before every write.
3. Crash-safe index persistence.
```

## Query examples with output

### Filtered query

```python
from hummbl_cognition.query import query_entries

for e in query_entries(entry_type="lesson", tags=["python"], limit=5):
    print(f"[{e.timestamp[:10]}] {e.agent}: {e.content}")
```

Output:

```
[2026-06-20] claude-code: Pin SDK versions in requirements.txt to avoid silent breakage.
```

### Active entries (supersedes resolved)

```python
from hummbl_cognition.query import active_entries

for e in active_entries(limit=10):
    print(f"{e.type:12} {e.id}  {e.content[:60]}")
```

Output (note `clp-a1b2...` is excluded because it was superseded):

```
convention   clp-d4e5f6a7b8c9d0  Dependency management: pin major.minor versions; allow
correction   clp-c3d4e5f6a7b8c9  Earlier lesson was too broad: only pin major.minor, allow
decision     clp-b2c3d4e5f6a7b8  Adopt the Cognitive Ledger Protocol for all agent memory
```

### BM25 search

```python
from hummbl_cognition.indexer import BM25Index

idx = BM25Index()
idx.build(ledger_path="ledger.jsonl")
idx.save()
for r in idx.search("dependency pinning", limit=3):
    print(f"{r['score']:.3f}  {r['id']}  {r['meta']['content_preview'][:50]}")
```

Output:

```
2.814  clp-d4e5f6a7b8c9d0  Dependency management: pin major.minor versions; allow
1.927  clp-c3d4e5f6a7b8c9  Earlier lesson was too broad: only pin major.minor, allow
1.203  clp-a1b2c3d4e5f6  Pin SDK versions in requirements.txt to avoid silent
```

### Boot context

```python
from hummbl_cognition.boot_context import build_boot_context

print(build_boot_context("/path/to/cognition", max_entries=5, max_age_days=30))
```

Output:

```
# Cognitive Ledger Boot Context

## Current Intent
# Sprint Goal: Cognition Hardening
...

## Shared State
- Sprint: cognition-hardening
- Agents: claude-code (writing docs), cursor (reviewing PR), gemini-cli (idle)
- Flags: consolidation_enabled=true, kill_switch=false

## Recent Learnings
- [2026-06-21] (cursor) DECISION: Adopt the Cognitive Ledger Protocol for all agent memory writes. [architecture, clp]
- [2026-06-22] (claude-code) CORRECTION: Earlier lesson was too broad: only pin major.minor, allow patch to float for security fixes. [python, dependencies]
- [2026-06-23] (consolidator) CONVENTION: Dependency management: pin major.minor versions; allow patch floats for security. [consolidated, group-size-3]
```

Entries are prioritized `decision > correction > lesson > convention > discovery`
(`query.py:105-111`, `boot_context.py:38-44`).

## Multi-agent coordination example

Two agents, `claude-code` and `cursor`, share a single ledger on a common
filesystem. They coordinate through three mechanisms: the append-only ledger,
the mutable shared state, and the frozen boot context.

```python
# --- Agent 1: claude-code learns something and posts it ---
from hummbl_cognition.ledger_writer import post_entry
from hummbl_cognition.models import LedgerEntry

lesson = LedgerEntry.create(
    content="Never commit .env files; use a vault for secrets.",
    agent="claude-code",
    vendor="anthropic",
    model="claude-opus-4",
    entry_type="lesson",
    scope="global",
    tags=["security", "secrets"],
    confidence=0.95,
    assurance_level="VERIFIED",
)
post_entry(lesson)  # safe under fcntl.flock(LOCK_EX)
```

```python
# --- Agent 2: cursor boots, sees the lesson, and later corrects it ---
from hummbl_cognition.boot_context import build_boot_context
from hummbl_cognition.query import active_entries

# Frozen snapshot at session start (includes claude-code's lesson)
ctx = build_boot_context()
# ... agent works, discovers the lesson needs refinement ...

# Post a correction that supersedes the original
from hummbl_cognition.ledger_writer import post_entry
from hummbl_cognition.models import LedgerEntry

original = active_entries(entry_type="lesson", tags=["security"])[0]
correction = LedgerEntry.create(
    content="Refinement: .env is fine for local dev if gitignored; production must use a vault.",
    agent="cursor",
    vendor="openai",
    model="gpt-4o",
    entry_type="correction",
    scope="global",
    tags=["security", "secrets"],
    confidence=0.9,
    supersedes=original.id,
    links=[original.id],
)
post_entry(correction)
```

```python
# --- Agent 3: consolidator runs nightly and synthesizes the pair ---
from hummbl_cognition.consolidator import run_consolidation

result = run_consolidation()
# Posts a "convention" entry linking both, with tags=["consolidated", "group-size-2"]
print(result)  # {"groups_found": 1, "consolidated": 1, "skipped": 0, "errors": []}
```

```python
# --- Any agent: search the consolidated knowledge ---
from hummbl_cognition.indexer import BM25Index

idx = BM25Index()
idx.load()
for r in idx.search("secrets env vault", limit=3):
    print(r["score"], r["meta"]["type"], r["meta"]["content_preview"][:60])
```

### Why this is safe concurrently

- `post_entry` serializes appends via `fcntl.flock(LOCK_EX)` on POSIX
  (`ledger_writer.py:49-59`), so `claude-code` and `cursor` cannot interleave a
  torn line.
- Each line is ≤ 4096 chars (`MAX_CONTENT_BYTES`, `ledger_writer.py:45`), within
  the atomic-append budget.
- Readers (`read_entries`, `active_entries`) take no lock and skip malformed
  lines (`ledger_writer.py:751-756`), so they never block writers.
- The boot context is a frozen snapshot (`boot_context.py:7-17`), so
  `cursor`'s session is not invalidated when `claude-code` writes mid-session.

## Retrieval feedback loop

Feeding retrieval events back into stigmergic ranking (`feedback_tracker.py`,
`indexer.py:198-206`):

```python
from hummbl_cognition.indexer import BM25Index
from hummbl_cognition.feedback_tracker import log_retrieval, get_retrieval_counts

idx = BM25Index()
idx.load()
results = idx.search("secrets vault", limit=5)

# Log which entries were retrieved (append-only, lock-protected)
log_retrieval(
    query="secrets vault",
    entry_ids=[r["id"] for r in results],
    agent="claude-code",
    session_id="s-99",
)

# Later: fold counts into the index for a stigmergic boost
counts = get_retrieval_counts()
idx.retrieval_counts = counts
idx.save()
# Next search gives frequently-retrieved entries up to +20% score
```
