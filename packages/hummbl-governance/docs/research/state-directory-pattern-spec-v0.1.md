# Specification: The `_state/` Directory Pattern for Agent Memory

**Version:** 0.1 (draft)
**Date:** 2026-08-10
**Status:** PROPOSED — derived from HUMMBL fleet production implementation
**Evidence base:** HUMMBL fleet `_state/` convention (S1 primary source, sub-agent GLM-E analysis)

---

## 1. Purpose

The `_state/` directory provides file-based, human-readable, git-diffable runtime state for single-machine, multi-agent coordination. It is **not** a database replacement — it is a minimal-viable persistence layer that survives process restarts, supports cross-machine sync, and provides audit trails without binary dependencies.

**Design principle:** Files over databases. Text over binary. Append-only for events, last-writer-wins for current state.

---

## 2. Minimum Viable Implementation

Two files:

```
_state/
├── ledger.jsonl    # Append-only event log (never mutated)
└── state.json      # Current state (last-writer-wins, overwritten on save)
```

- `ledger.jsonl` — one JSON object per line, never edited, never deleted. Provides audit trail and event sourcing.
- `state.json` — the current agent state, overwritten on each save. Provides fast recovery without replaying the ledger.

**This is sufficient for single-agent persistence.** Everything else in this spec is augmentation.

---

## 3. Full Implementation

```
_state/
├── coordination/
│   └── messages.tsv              # Append-only TSV bus (timestamp, from, to, type, message)
├── cognition/
│   ├── ledger.jsonl              # Append-only cognitive ledger (lessons, decisions, discoveries)
│   ├── state.json                # Current cognitive state (last-writer-wins)
│   ├── intent.md                 # Current intent (last-writer-wins)
│   └── index.json                # BM25 inverted index over ledger
├── memory/
│   └── <agent>.design.md         # Per-agent memory architecture design docs
├── snapshots/
│   └── <timestamp>-<tag>.tar.gz  # Tarball backups of entire _state/
└── governance/
    └── reports/                  # AAR files
```

---

## 4. File Classification: Append-Only vs. Last-Writer-Wins

This is the core design decision. Files are explicitly classified:

| File | Classification | Rationale |
|------|---------------|-----------|
| `ledger.jsonl` | **Append-only** | Events are immutable history; never edit or delete |
| `messages.tsv` | **Append-only** | Bus messages are immutable; merge via sort-union |
| `state.json` | **Last-writer-wins** | Current state is overwritten on each save |
| `intent.md` | **Last-writer-wins** | Current intent is overwritten on each save |
| `index.json` | **Derived** | Regenerated from ledger; can be rebuilt |
| `snapshots/*.tar.gz` | **Immutable** | Once written, never modified |

**Why this matters:** Cross-machine sync uses different strategies for each class:
- Append-only files: sort-union merge (`sort -u` of both copies, deduplicate)
- Last-writer-wins files: rsync (most recent timestamp wins)
- Derived files: regenerate after sync
- Immutable files: rsync (add new files only)

---

## 5. Ledger Entry Format

Each line in `ledger.jsonl` is a JSON object:

```json
{
  "id": "<uuid>",
  "type": "lesson|decision|discovery|correction|convention|inference|milestone",
  "content": "<the actual content>",
  "agent": "<agent identity>",
  "timestamp": "<ISO 8601>",
  "confidence": 0.0-1.0,
  "provenance": {
    "source": "<where this came from>",
    "evidence": ["<evidence references>"]
  },
  "prev_hash": "<SHA-256 of previous line, or null for genesis>",
  "hash": "<SHA-256 of this line's canonical JSON>"
}
```

**Hash chaining:** Each entry's `prev_hash` links to the previous entry's `hash`, forming a tamper-evident chain. The genesis entry has `prev_hash: null`.

**Content scanning:** Before persistence, all entries are scanned for:
- Prompt injection vectors
- Credential leakage (API keys, tokens, passwords)
- Exfiltration patterns (unusual outbound data shapes)
- Invisible Unicode (zero-width characters, RTL overrides)

---

## 6. State File Format

`state.json` is a single JSON object representing the current agent state:

```json
{
  "agent": "<agent identity>",
  "session": "<session id>",
  "updated_at": "<ISO 8601>",
  "current_task": "<task description>",
  "context": {
    "working_directory": "<path>",
    "active_repo": "<repo name>",
    "branch": "<git branch>"
  },
  "history": [
    {"action": "<action>", "timestamp": "<ISO 8601>", "result": "<result>"}
  ]
}
```

**No file locking at the format level.** Implementations may use `flock` or file-based locks (`state.json.lock`) for concurrent access, but the format itself is lock-free.

---

## 7. Snapshot and Rollback

Snapshots are tarball archives of the entire `_state/` directory:

```bash
tar czf _state/snapshots/$(date -u +%Y%m%dT%H%M%SZ)-<tag>.tar.gz \
  --exclude='_state/snapshots' \
  -C _state .
```

**Restore:**
```bash
tar xzf _state/snapshots/<timestamp>-<tag>.tar.gz -C _state
```

**Verification:** After restore, verify ledger hash chain integrity by recomputing all hashes from genesis.

---

## 8. Cross-Machine Sync

```bash
# Sync last-writer-wins files
rsync -av --include='state.json' --include='intent.md' \
  source:_state/ dest:_state/

# Merge append-only files (sort-union)
for f in ledger.jsonl messages.tsv; do
  sort -u source:_state/$f dest:_state/$f > _state/$f
done

# Regenerate derived files
python rebuild_index.py _state/ledger.jsonl > _state/index.json

# Verify line counts post-sync
wc -l source:_state/ledger.jsonl dest:_state/ledger.jsonl _state/ledger.jsonl
```

---

## 9. Memory Hierarchy (4-Tier)

| Tier | Storage | Purpose | Examples |
|------|---------|---------|----------|
| Short-term | Context window | Current conversation | In-process buffer |
| Episodic | `ledger.jsonl` | Append-only event log | Lessons, decisions, discoveries |
| Semantic | `index.json` (BM25) | Retrieval over ledger | Inverted index for search |
| Long-term | `snapshots/*.tar.gz` | Compressed archives | Tarball backups |

**This is the minimum viable 4-tier hierarchy.** Production systems may add:
- Vector DB (pgvector, Qdrant) for semantic retrieval at scale
- Graph store (Neo4j) for relationship queries
- Redis with TTL for short-term cache

---

## 10. Comparison to Framework Approaches

| Dimension | `_state/` (this spec) | Framework DBs (MemGPT, CrewAI) |
|-----------|----------------------|-------------------------------|
| Survives restart | Yes (files on disk) | Yes (all frameworks) |
| Audit trail | Yes (append-only JSONL) | Partial (LangGraph checkpoints, not append-only) |
| Cross-machine sync | Yes (rsync + sort-union merge) | Requires DB replication or shared Postgres |
| Human-readable | Yes (plain text) | No (SQLite binary, vector DB binary) |
| Git-diffable | Yes (text files) | No (binary DBs) |
| Snapshot/rollback | Yes (tarball) | Partial (LangGraph checkpoint restore) |
| Semantic search | Partial (BM25 index) | Yes (vector DB built-in) |
| Scale (10k+ entries) | Linear scan (BM25 helps) | Indexed DB (better) |
| Concurrency | flock / file locks | DB transactions |
| Dependencies | Zero (stdlib only) | Framework + DB driver |

**Verdict:** `_state/` is superior for single-machine, multi-agent coordination (auditability, sync, human-readiness, git-diffability). Framework DBs are superior for semantic retrieval at scale. The BM25 index bridges the gap for moderate-scale semantic search without a vector DB.

---

## 11. Gitignore Policy

`_state/` is **always gitignored**. Runtime state must not be committed to version control.

```gitignore
# .gitignore
_state/
```

**Exception:** Empty `.gitkeep` files may be committed to preserve directory structure in a fresh clone. The actual state files are runtime-generated.

---

## 12. Adoption Checklist

- [ ] Create `_state/` directory (gitignored)
- [ ] Create `_state/cognition/ledger.jsonl` (empty)
- [ ] Create `_state/cognition/state.json` (initial state)
- [ ] Implement append-only write for ledger (never edit, never delete)
- [ ] Implement last-writer-wins write for state.json
- [ ] Add content scanning before persistence (prompt injection, credentials)
- [ ] Add snapshot capability (tarball of `_state/`)
- [ ] Add hash chaining to ledger entries (SHA-256, prev_hash)
- [ ] Add BM25 index generation (optional, for semantic search)
- [ ] Add cross-machine sync (rsync + sort-union merge)
- [ ] Document file classification (append-only vs. last-writer-wins) in AGENTS.md

---

## 13. Open Questions

1. **Should this be proposed as an industry standard?** It's more architecturally complete than any framework's default, but it's a single implementation. Needs multi-operator validation before standardization.

2. **Vector DB integration point?** The spec is silent on where a vector DB fits. Proposed: `_state/vector/` for vector indexes, with `index.json` (BM25) as a fallback when no vector DB is present.

3. **Concurrency at scale?** `flock` works for single-machine. For distributed agents, a coordination service (etcd, Consul) or a shared filesystem (NFS) is needed. This spec does not address distributed concurrency.

4. **Retention policy?** The ledger grows forever. When and how to compact? Proposed: snapshot + archive entries older than N days, keep only the hash chain headers.

5. **Encryption?** The spec is plaintext. For sensitive state, file-level encryption (age, gpg) should be applied to `state.json` and `snapshots/`. The ledger may remain plaintext for auditability.
