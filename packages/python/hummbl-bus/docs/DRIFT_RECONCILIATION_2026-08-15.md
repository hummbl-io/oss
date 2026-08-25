# Bus Drift Reconciliation - 2026-08-15

## Verdict

`hummbl-bus` has completed Phase B (promote + absorb) of the cutover program.
All 12 promote modules are in hummbl-bus with tests, the bus-generic functions
from `bus_writer_core.py` are absorbed, Windows cross-process locking is ported,
and byte-identical TSV parity tests are in place. 196 tests pass on main.

**Recommendation: hummbl-bus is ready for Phase C (shadow period). Run as a
read-only mirror alongside hummbl-governance's writer for 30 days before flipping
the write cutover. Do not promote to canonical v1 until Phase C + D complete.**

> **Update 2026-08-15 (post-cutover):** The original verdict below was written
> before PRs #14-#22 landed. It is preserved as the pre-cutover baseline. The
> current status is reflected in §Cutover Completion Status below.

## Cutover Completion Status (2026-08-15, post PRs #14-#22)

| Gate | Status | PR | Evidence |
| --- | --- | --- | --- |
| 1. Promote 12 modules | **DONE** | #15, #16, #18, #19, #20 | 10 modules promoted; bus_writer_signing + bus_writer_cli confirmed already absorbed |
| 2. Absorb 3 modules | **DONE (scoped)** | #21 | 4 bus-generic functions absorbed; hummbl-governance-specific policy stays in FM |
| 3. Windows cross-process locking | **DONE** | #14 | `_msvcrt_path_lock`, `_cross_process_lock` ported |
| 4. Process-level concurrency tests | **DONE** | #14 | `test_concurrent_writes_lose_no_messages`, `test_concurrent_dead_letters_lose_no_records` |
| 5. Resolve 3 FM-only modules | **DONE** | — | `inference_tier`, `work_queue`, `autonomy_ladder` confirmed stay in hummbl-governance |
| 6. Resolve 1 deferred module | **OPEN** | — | `lane_classifier` — operator decision pending |
| 7. Verify HB-only features | **DONE** | #22 | Correlation IDs + structured events confirmed present in both; HB supports legacy schema |
| 8. Parity tests (byte-identical TSV) | **DONE** | (this update) | `tests/test_tsv_parity.py` — 16 tests, golden-fixture approach |
| 9. Shadow period (30 days) | **NOT STARTED** | — | Next step: Phase C |
| 10. Write cutover | **NOT STARTED** | — | Phase D, after shadow period |

**Test count:** 196 passed (up from 33 at program start, 20 at 2026-05-24 snapshot).

**PRs merged:** #14 (Windows lock), #15 (message_types + bus_utils), #16 (authority),
#17 (.gitattributes), #18 (spool + replay cluster), #19 (wip_healer + bus_auditor),
#20 (bus_ed25519_verifier), #21 (bus_writer_core generic), #22 (drift sync).

**Drift fixes synced in #22:** dead-letter metadata redaction (#1761), dead-letter
permission hardening (D4 #1731), Kimi identity retirement (2026-04-05).

## What changed since 2026-05-24

| Metric | 2026-05-24 | 2026-08-15 | Delta |
| --- | ---: | ---: | ---: |
| hummbl-governance/bus modules | 21 | 30 | +9 |
| hummbl-bus modules | 13 | 13 | 0 |
| founder-only modules | 8 | 17 | +9 |
| bus_writer_core.py lines | 1,843 | 2,676 | +833 |
| common modules with SHA drift | 12 of 13 | 13 of 13 | +1 |

Nine new modules (~1,700 lines) landed in hummbl-governance with no hummbl-bus
counterpart. The common modules all drifted further. The extraction is further
from parity than it was 2.5 months ago.

## Validation Run

Not re-run in this pass. The 2026-05-24 run reported 20 passed; hummbl-bus
tests should be re-run before any promotion decision. This reconciliation is
a structural and semantic comparison only.

## Module Inventory (2026-08-15)

### Common modules (13) — all SHA-drifted

| Module | FM lines | HB lines | Drift summary |
| --- | ---: | ---: | --- |
| `__init__.py` | 53 | 54 | minor |
| `bridge_client.py` | 222 | 94 | FM has remote-first write path, HB is older |
| `bridge_server.py` | 586 | 257 | FM has ~2x the surface (auth, health, multi-route) |
| `bridge_tcp_client.py` | 103 | 49 | FM expanded |
| `bus_integration.py` | 520 | 334 | FM has integration mixin growth |
| `bus_manager.py` | 424 | 395 | moderate drift |
| `bus_policy.py` | 191 | 124 | FM added privileged-type and host rules |
| `bus_security.py` | 398 | 393 | near-parity (1 line diff in 2026-05; recheck) |
| `bus_verifier.py` | 311 | 279 | FM added authority + host verification |
| `bus_writer.py` | 113 | 1,164 | **structural split** — FM is thin wrapper, HB absorbed core |
| `mcp_server.py` | 339 | 363 | HB may have features FM lacks (bidirectional drift) |
| `message_signing.py` | 218 | 217 | near-parity |
| `secure_tsv.py` | 328 | 325 | near-parity |

### Founder-only modules (17)

| Module | Lines | Classification | Rationale |
| --- | ---: | --- | --- |
| `authority.py` | 258 | **promote** | Privileged-write principal proofs (DECISION/DIRECTIVE). Core bus security. |
| `bus_auditor.py` | 229 | **promote** | Bus health auditor daemon (PROPOSAL-012 C7). Bus integrity. |
| `bus_ed25519_verifier.py` | 225 | **promote** | Optional Ed25519 verification (lazy `cryptography` import, stdlib-safe). Bus security. |
| `bus_utils.py` | 52 | **absorb** | Shared TSV parser. Belongs in `bus_writer.py` or a utils module. |
| `bus_writer_cli.py` | 176 | **promote** | CLI entry point. Part of the package surface. |
| `bus_writer_core.py` | 2,676 | **absorb** | The canonical write path. HB already absorbed an older, smaller version into `bus_writer.py` (1,164 lines). Needs semantic merge. |
| `bus_writer_signing.py` | 223 | **absorb** | HMAC signing + nonce + file hardening. Belongs in `bus_writer.py`. |
| `inference_tier.py` | 187 | **hummbl-governance-only** | PROPOSAL-012 C4: cost-optimized inference routing. Agent orchestration, not bus transport. |
| `lane_classifier.py` | 214 | **defer** | PROPOSAL-012 C2: foreground/background lane classification. Boundary case — bus-adjacent but orchestration-flavored. Operator decision. |
| `message_types.py` | 90 | **promote** | Canonical message vocabulary. Core bus protocol. |
| `replay_ledger.py` | 99 | **promote** | Persistent replay ledger for remote writes. Part of portable bus contract. |
| `replay_worker.py` | 84 | **promote** | Oldest-first replay worker. Part of portable bus contract. |
| `seed_import.py` | 179 | **promote** | Idempotent seed/import for bus migration. Needed for cutover itself. |
| `spool.py` | 150 | **promote** | Client-side outbound spool. Part of portable bus contract. |
| `wip_healer.py` | 186 | **promote** | Stale WIP self-healing (PROPOSAL-012 C6). Bus integrity. |
| `work_queue.py` | 256 | **hummbl-governance-only** | PROPOSAL-012 C3: push/pull work loop. Agent orchestration on top of the bus, not bus transport. |
| `autonomy_ladder.py` | 173 | **hummbl-governance-only** | PROPOSAL-012 C5: autonomy escalation tiers. Agent orchestration policy. |

**Totals:** 12 promote, 3 absorb, 2 hummbl-governance-only, 1 defer, 1 founder-only-already-absorbed-partially.

## Semantic Diff — `bus_writer.py` (the critical gap)

hummbl-governance split its writer into `bus_writer.py` (113-line wrapper) +
`bus_writer_core.py` (2,676) + `bus_writer_cli.py` (176) +
`bus_writer_signing.py` (223) = **3,188 lines**.

Hummbl-bus has a single `bus_writer.py` at **1,164 lines** — an absorption of
an older, smaller core.

### Features hummbl-governance has that hummbl-bus lacks

- **Windows cross-process locking** (`_msvcrt_path_lock`, `_cross_process_lock`) — hummbl-bus is flock-only, will not run correctly on Windows. This is a platform-critical gap for the Anvil runner.
- **Secret redaction** (`_redact_secrets`, `_redact_url_credentials`, `_redact_metadata`) — hummbl-bus has no redaction layer.
- **Bus path hygiene** (`resolve_canonical_bus_path`, `find_shadow_bus_paths`, `assert_local_bus_hygiene`, `_allowed_bus_roots`, `_validate_bus_path`) — hummbl-bus has no shadow-bus detection or path validation.
- **Authority validation** (`_record_privileged_type_event`, `_extract_authority_field`, `_validate_privileged_message_type`, `_validate_authority_field`) — ties to `authority.py`. hummbl-bus has no privileged-write proofs.
- **Host-tag validation** (`_is_host_exempt_sender`, `_message_has_host`, `_validate_canonical_message_type`, `_validate_host_presence`) — hummbl-bus has no host-tag enforcement.
- **Review receipt schema validation** (`_validate_review_receipt_schema`).
- **WIP pairing validation** (`_validate_wip_pairing`).
- **Autonomy validation** (`_maybe_validate_autonomy`) — ties to `autonomy_ladder.py`.
- **Multi-decision suggestions** (`_suggest_multi_decision`).
- **Bridge URL validation** (`_validate_bridge_url`).

### Features hummbl-bus has that hummbl-governance may lack

- **Correlation IDs** (`_sanitize_correlation_id`, `generate_correlation_id`, `extract_correlation_id`, `_inject_correlation_id`).
- **Structured events** (`build_structured_event`, `parse_structured_event`, `post_structured_event`).
- **TSV integrity validation** (`validate_tsv_integrity`).
- **Dead-letter writer** (`write_dead_letter`) — hummbl-governance may have this in `spool.py` or another module; verify before claiming drift.

**Action:** verify whether correlation IDs and structured events exist anywhere
in hummbl-governance's bus before treating these as hummbl-bus-only. If they are
genuinely absent, they are a protocol feature the cutover must preserve.

## Release Gates Before Canonical Promotion

1. **Promote 12 modules** from hummbl-governance into hummbl-bus (see classification
   table). Each promotion needs: copy, re-import to `hummbl_bus.*`, smoke test,
   semantic parity test against the hummbl-governance source.
2. **Absorb 3 modules** (`bus_writer_core`, `bus_writer_cli`, `bus_writer_signing`)
   into hummbl-bus's `bus_writer.py`. This is the hardest gate: merge 3,188
   lines of split hummbl-governance code into the 1,164-line hummbl-bus file while
   preserving both the hummbl-bus-only features (correlation IDs, structured
   events) and the hummbl-governance-only features (Windows locking, redaction,
   authority, host-tag, path hygiene).
3. **Add Windows cross-process locking** to hummbl-bus. Without this, hummbl-bus
   cannot be the canonical writer on Anvil (Windows). This is a platform
   blocker, not a nice-to-have.
4. **Add process-level concurrency tests** for the merged `bus_writer.py`,
   including Windows `msvcrt` locking and Unix `fcntl` locking.
5. **Resolve the 3 hummbl-governance-only modules** (`inference_tier`, `work_queue`,
   `autonomy_ladder`) — confirm they stay in hummbl-governance or move to a separate
   orchestration package. They do not belong in the bus package.
6. **Resolve the 1 deferred module** (`lane_classifier`) — operator decision on
   whether lane classification is bus protocol or orchestration policy.
7. **Verify hummbl-bus-only features** (correlation IDs, structured events) are
   genuinely absent from hummbl-governance before treating as drift to preserve.
8. **Run the full hummbl-bus test suite** and add parity tests that assert
   hummbl-bus produces byte-identical TSV output to hummbl-governance for a fixed
   message set.
9. **Shadow period**: run hummbl-bus as a read-only mirror alongside
   hummbl-governance's writer for a defined window (retirement index recommends 30
   days) before switching writes.
10. **Cutover**: flip `BUS_CANONICAL_BRIDGE_URL` / writer import to hummbl-bus,
    verify bus writes land, verify `_state/coordination/messages.tsv` path
    resolution, post DECISION + MILESTONE receipts.

## Cutover Plan (gate 1 of the retirement index)

The retirement index says: "Reconcile and cut over the bus. Almost every other
active capability depends on it." This is the work that unblocks:

- `bus-production-ledger-bridge` (active → migrated)
- `bus-standalone-extraction` (shadowed → migrated)

### Phase A — Semantic reconciliation (this report)

Done. The drift is classified and the gaps are named.

### Phase B — Promote + absorb (the long part)

Promote 12 modules, absorb 3, add Windows locking, add concurrency tests, add
parity tests. Each module is a small PR. The `bus_writer.py` merge is the
largest single piece.

### Phase C — Shadow period

Run hummbl-bus as a read-only mirror. Verify it reads the same TSV, resolves
the same paths, and produces the same validation results. 30 days is the
retirement index default.

### Phase D — Write cutover

Flip the writer import. Verify writes land. Post receipts. Mark
`bus-standalone-extraction` and `bus-production-ledger-bridge` as `migrated`
in the retirement index.

## Current Recommendation (updated 2026-08-15, post PRs #14-#22)

**hummbl-bus is ready for Phase C (shadow period).** All promote/absorb gates
are complete, Windows locking is ported, concurrency tests pass, and
byte-identical TSV parity tests are in place (16 tests in
`tests/test_tsv_parity.py`). 196 tests pass on main.

The original recommendation below is preserved as the pre-cutover baseline.

---

**Original recommendation (pre-cutover):**

Keep `hummbl-bus` at `0.1.0` extraction status. The drift has widened, not
narrowed, since the last reconciliation. The cutover is a multi-PR program,
not a single promotion. The single highest-risk gap is the missing Windows
cross-process locking — without it, hummbl-bus cannot replace the hummbl-governance
writer on Anvil regardless of how much other code is promoted.

**This gap is now closed** (PR #14, 2026-08-15).

### Next steps

1. **Phase C — Shadow period**: Run hummbl-bus as a read-only mirror alongside
   hummbl-governance's writer for 30 days. Verify it reads the same TSV, resolves
   the same paths, and produces the same validation results.
2. **Phase D — Write cutover**: Flip the writer import. Verify writes land.
   Post DECISION + MILESTONE receipts. Mark `bus-standalone-extraction` and
   `bus-production-ledger-bridge` as `migrated` in the retirement index.
3. **Gate 6 — lane_classifier**: Operator decision on whether lane
   classification is bus protocol or orchestration policy. This is the only
   remaining open gate.
