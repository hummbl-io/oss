# Troubleshooting

Common issues encountered when running the Cognitive Ledger Protocol, each with
a root cause grounded in the source and a concrete fix.

## Concurrency errors

### Symptom: Torn or interleaved JSONL lines when multiple agents write

**Cause:** A writer bypassed `post_entry()` and appended to `ledger.jsonl`
directly with a raw `open(..., "a")`. The advisory lock in `_lock_file()`
(`ledger_writer.py:49-59`) is **cooperative** — it only excludes writers that
also call it. `fcntl.flock` does not prevent a process that ignores it from
writing.

**Fix:**

- Route every write through `post_entry()` (`ledger_writer.py:528-628`), which
  acquires `LOCK_EX`, writes one line, `flush()`es, and releases `LOCK_UN`
  (`ledger_writer.py:606-614`).
- If you must write manually, replicate the lock: `fcntl.flock(f, fcntl.LOCK_EX)`
  before writing and `fcntl.flock(f, fcntl.LOCK_UN)` after, with a `flush()`
  in between.
- Readers tolerate malformed lines (`ledger_writer.py:751-756` skips them with a
  warning), so torn lines won't crash readers — but they will be reported by
  `validate_integrity` as `parse_error`.

### Symptom: "No advisory file locking backend available; proceeding unlocked"

**Cause:** Neither `fcntl` (POSIX) nor `msvcrt` (Windows) could be imported
(`ledger_writer.py:21-29, 59`). This happens on unsupported platforms.

**Fix:** This is safe for single-agent use. For multi-agent writes, run on a
platform with `fcntl` (Linux/macOS) or `msvcrt` (Windows), or federate writes
through a single `OpenBrainClient` (`client.py`) to a primary server that does
the locked appends.

### Symptom: `PermissionError: Delegation token does not permit 'read:ledger'`

**Cause:** `ENABLE_IDP` is set to a truthy value and a `delegation_token` was
supplied to `read_entries()` whose `ops_allowed` lacks `"read:ledger"`
(`ledger_writer.py:718-728`).

**Fix:** Issue a delegation token that includes `"read:ledger"` in
`ops_allowed`, or unset `ENABLE_IDP` if IDP gating is not required (fail-open
for backward compatibility, `ledger_writer.py:720-721`).

## File locking conflicts

### Symptom: Writer hangs indefinitely

**Cause:** A previous process crashed while holding the advisory lock, or a
long-running reader is mistakenly holding a lock. Note that `read_entries` and
`validate_integrity` do **not** take a lock (`ledger_writer.py:746`,
`ledger_writer.py:820`), so they cannot cause this.

**Fix:** `fcntl.flock` locks are automatically released when the process exits
or the file descriptor closes — a crashed process releases its lock on death.
A genuine hang almost always means a process is alive but stuck in user code
before reaching `_unlock_file`. Kill the stuck process. If using `msvcrt` on
Windows, `msvcrt.locking` with `LK_LOCK` retries until it succeeds
(`ledger_writer.py:57`), so a true deadlock requires manual intervention
(kill one writer).

### Symptom: Ledger file has overly permissive permissions

**Cause:** The file was created outside `post_entry` (which hardens new files
to `0o660` via `_harden_file_permissions`, `ledger_writer.py:451-460, 617-618`),
or the chmod failed (logged as a warning, `ledger_writer.py:459-460`).

**Fix:** Manually `chmod 0o660 ledger.jsonl`, and ensure future writes go
through `post_entry` so the hardening runs on first creation.

## Corruption recovery

### Symptom: `validate_integrity` reports `parse_error` on specific lines

**Cause:** Those JSONL lines are malformed — typically from a torn write (see
[Concurrency errors](#symptom-torn-or-interleaved-jsonl-lines-when-multiple-agents-write))
or manual editing of the ledger.

**Fix:** Per the remediation guidance (`_REMEDIATION["parse_error"]`,
`ledger_writer.py:893-897`): preserve the raw bytes, identify the writer/source,
and only quarantine or repair with explicit operator approval and a backup. Use
`validate_integrity_report()` (`ledger_writer.py:901-964`) to get line ranges:

```python
from hummbl_cognition.ledger_writer import validate_integrity_report
import json

print(json.dumps(validate_integrity_report(), indent=2))
```

To repair, back up the file, remove or fix the malformed lines, and re-run
`validate_integrity` until clean. Never edit lines in place casually — the
ledger is append-only by design.

### Symptom: `content_hash_mismatch` on some entries

**Cause:** The stored `content_hash` no longer matches a hash of the content
fields. This indicates either content mutation (someone edited the file) or
schema/canonicalization drift between the writer version and the validator
(`_REMEDIATION["content_hash_mismatch"]`, `ledger_writer.py:888-892`).

**Fix:** Inspect each flagged entry with `LedgerEntry.verify_hash()` and
classify it as schema-era drift vs. true corruption before any repair. For
schema drift, append a superseding `correction` entry rather than editing the
original. For true corruption, restore from backup.

### Symptom: `signature_mismatch` on some entries

**Cause:** The HMAC signature no longer verifies. This usually means the
`BUS_SIGNING_SECRET` changed (signing-secret drift) or historical signature
coverage changed (`_REMEDIATION["signature_mismatch"]`,
`ledger_writer.py:882-887`).

**Fix:** Do **not** re-sign in place. First confirm the expected historical
signing secret, then either document a waiver range or append a superseding
attestation ledger entry. Note that `validate_integrity` skips hash verification
for grandfathered non-hex `content_hash` values (`ledger_writer.py:835-842`),
but signature mismatches are always reported when a secret is available.

### Symptom: `read_entries(verify_signatures=True)` silently drops entries

**Cause:** Entries whose signature fails verification are dropped and logged as
warnings (`ledger_writer.py:758-777`). This is by design — it prevents tampered
entries from influencing the agent.

**Fix:** Check the logs for `"Dropping ledger entry ... signature mismatch"`.
Run `validate_integrity_report()` to get the full list, then follow the
signature-mismatch remediation above.

## Content scanning rejections

### Symptom: `ContentScanError: prompt_injection`

**Cause:** The content matched one of the injection patterns (e.g.
"ignore previous instructions") after NFC normalization and confusable
transliteration (`ledger_writer.py:78-87, 368-375`).

**Fix:** Remove the injection-like phrasing. If the match is a false positive
on legitimate content, rephrase it. The scan runs on `content`, `evidence`,
`tags`, and `agent` (`ledger_writer.py:562-568`).

### Symptom: `ContentScanError: credential_leak`

**Cause:** The content matched a credential pattern (OpenAI/Anthropic/GitHub/
GitLab/Slack/Google/AWS keys, PEM private keys) after confusable transliteration
(`ledger_writer.py:90-101, 377-386`). Cross-script homoglyphs like Cyrillic
`к` are mapped to Latin `k` before matching (`ledger_writer.py:296`), so
obfuscation does not bypass the scan.

**Fix:** Remove the secret from the content. Never store credentials in the
append-only ledger — it is designed for long-term retention.

### Symptom: `ContentScanError: invisible_unicode`

**Cause:** The raw text contains an invisible Unicode codepoint (zero-width
chars, bidi controls, Ogham space, etc.) from `_INVISIBLE_CODEPOINTS`
(`ledger_writer.py:222-273`). Detection runs on raw text **before** NFC
normalization (`ledger_writer.py:353-360`).

**Fix:** Strip the invisible characters. The error message lists the exact
codepoints (e.g. `U+200B, U+202E`).

### Symptom: `PIIDetectedError` at write time

**Cause:** `PII_SCAN_STRICT=true` and the content contained an email, US phone,
SSN, or IP address not on the allowlist (`ledger_writer.py:139-164`).

**Fix:** Either remove the PII, or use `scrub_pii()` / `scrub_pii_from_dict()`
(`ledger_writer.py:167-206`) to replace it with SHA-256 pseudonyms before
posting. Allowlisted values (e.g. `noreply@anthropic.com`, loopback IPs) are
kept automatically (`ledger_writer.py:122-127`).

## Large ledger performance

### Symptom: `read_entries` is slow on a 100K+ entry ledger

**Cause:** `read_entries` scans the entire file line by line, parsing every
line and applying filters in Python (`ledger_writer.py:746-795`). It is O(n)
in the number of lines.

**Fix:**

- **Build and use the BM25 index.** `build_boot_context()` already tries the
  index first (`_summarize_indexed`, `boot_context.py:47-108`) and falls back
  to a scan only when the index is missing or empty. Run `reindex` after bulk
  writes.
- **Use `BM25Index.search()` for text queries** instead of `read_entries` with
  substring filters. The index does filtered, scored lookup without scanning
  every line (`indexer.py:157-224`).
- **Use the `since` filter** to avoid processing old entries when you only need
  recent ones.
- **Run the consolidator nightly** (`consolidator.py`) so that related entries
  are compressed into `convention` summaries, reducing the active set that
  `active_entries()` must process.

### Symptom: Index build is slow

**Cause:** `BM25Index.build()` reads all entries (`limit=999_999`,
`indexer.py:96`) and tokenizes every one. It is O(n) and runs in Python.

**Fix:** Build incrementally with `add_document()` (`indexer.py:232-251`) for
new entries between full rebuilds. Schedule full `build()` runs off-peak. The
index save is crash-safe (temp + fsync + rename, `indexer.py:253-289`), so a
crash mid-build leaves the previous index intact.

### Symptom: Boot context generation is slow

**Cause:** The index is missing or empty, forcing the sequential-scan fallback
`summarize_for_boot()` (`query.py:82-129`), which reads and sorts all entries.

**Fix:** Ensure `index.json` exists and is current (`reindex`). Once present,
`_summarize_indexed()` (`boot_context.py:47-108`) uses only index metadata — no
ledger scan — and is fast at any scale.

## Index rebuild

### Symptom: Search returns stale results after bulk imports

**Cause:** The index is a derived artifact (`indexer.py:1-7`); it is not
updated automatically when entries are appended outside `add_document`.

**Fix:** Rebuild the index:

```python
from hummbl_cognition.indexer import BM25Index

idx = BM25Index()
idx.build(ledger_path="ledger.jsonl")
idx.save()
```

Or via the CLI: `hummbl-cognition reindex`. The build replaces all in-memory
structures (`indexer.py:98-100`) and the save is atomic.

### Symptom: `BM25Index.load()` returns `False`

**Cause:** The index file is missing, or it failed to parse
(`indexer.py:291-301` returns `False` on `json.JSONDecodeError` or `OSError`).

**Fix:** Rebuild the index with `build()` + `save()`. If the file exists but is
corrupt, delete it first so `load()` cleanly returns `False` and triggers a
rebuild.

### Symptom: Stigmergic boost not applied

**Cause:** `retrieval_counts` is empty. Either no retrieval events have been
logged, or the counts were not folded into the index.

**Fix:**

1. Log retrievals with `log_retrieval()` (`feedback_tracker.py:79-109`).
2. Aggregate with `get_retrieval_counts()` (`feedback_tracker.py:112-143`).
3. Assign to `idx.retrieval_counts` and `idx.save()`. Search with
   `boost_retrievals=True` (the default, `indexer.py:165, 198-206`).
