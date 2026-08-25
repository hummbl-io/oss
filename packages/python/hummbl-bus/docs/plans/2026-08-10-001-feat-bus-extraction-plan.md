---
title: hummbl-bus Extraction - Plan
type: feat
date: 2026-08-10
topic: bus-extraction
artifact_contract: ce-unified-plan/v1
artifact_readiness: requirements-only
product_contract_source: ce-brainstorm
execution: code
---

# hummbl-bus Extraction - Plan

## Goal Capsule

- **Objective:** Extract hummbl-bus from hummbl-governance to canonical v1, with split-channel flooding fix baked in and forensic preservation of all drift, code, and message history.
- **Product authority:** This plan owns the bus extraction + flooding fix. Surrounding L2 extractions (hummbl-tuples, krineia), Gitea token revocation, hummbl-io migration, and fleet-health tool are not active scope.
- **Open blockers:** Fleet agents must adopt split-channel posting behavior simultaneously. Migration order must avoid actively-touched files. Operator confirms hummbl-governance archive curation timeline (PROPOSAL v2, req_id=1bad06f123c7466faccf1dfa2919a7e5).

---

## Product Contract

### Summary

Full extraction of hummbl-bus from hummbl-governance to canonical v1, with split-channel flooding fix baked in. Drift between the two bus surfaces is documented as forensic evidence, not erased. hummbl-governance's bus/ directory is frozen as readable reference. The 114 files importing from `hummbl_governance.bus` migrate to `hummbl_bus`. The 7,735-message archive is preserved as-is.

### Problem Frame

The coordination bus has two problems braided together.

**Drift.** hummbl-bus was extracted from hummbl-governance at 0.1.0 but never reconciled. Of 13 common modules, only 2 (`bus_policy.py`, `bus_security.py`) share identical SHA. 17 founder-only modules (replay, spool, work_queue, authority, lane_classifier, etc) were never classified. hummbl-bus's `bus_writer.py` (1,372 lines) absorbed three hummbl-governance modules (`bus_writer_core`, `bus_writer_signing`, `bus_writer_cli`). The extraction is stalled at "IN PROGRESS" with 5 release gates unmet. hummbl-governance remains the canonical bus source, which blocks hummbl-governance's transition to curated archive.

**Flooding.** The bus is a heartbeat channel pretending to be a coordination channel. Of 7,735 messages, 1,317 are STATUS (17%) and 117 are PROPOSAL (1.5%). Scheduled tasks (codex watch loops, dead-mans-switch, bus-watcher) post heartbeats into the same channel as decisions. Finding signal requires grep every time. The bus works, but it doesn't work for coordination — it works for observation.

Extraction alone won't fix flooding — flooding is message-policy, not code-organization. But extraction is the moment to fix it: new package, new policy, clean break.

### Key Decisions

- **KD1. Split channels (writer-side) over rate-limiting or reader-filter.** Status/heartbeat messages go to a separate sink (log file or separate TSV). Coordination bus keeps only PROPOSAL, DECISION, REVIEW, ACK, BLOCKED, MILESTONE. Governs R3.
  *(session-settled: user-directed — chosen over rate-limit + dedup, reader-side filter, split + rate-limit: clean separation, no policy enforcement needed)*

- **KD2. Full 121-file migration over shim or let-die.** All importing files migrate to `hummbl_bus`. Explicit imports, clean break, no shim debt. Governs R5.
  *(session-settled: user-directed — chosen over reverse-shim, let-die-with-archive: explicit imports preferred)*

- **KD3. Forensic freeze-dry over reverse-shim.** hummbl-governance/bus/ is frozen as-is, never shimmed, never deleted, never modified. Stays as readable reference. Drift is documented, not erased. Governs R2, R6.
  *(session-settled: user-approved — chosen over reverse-shim: preserves maximum forensic evidence; operator stated "I love forensics")*

- **KD4. Approach D (extract + freeze-dry) over big-bang, phased-with-shim, or extract+shim.** mtsmu score 0.82. Documents drift, classifies modules, extracts v1, migrates incrementally, freezes hummbl-governance bus/ as reference, preserves message archive. Governs R1-R7.

### Requirements

#### Extraction

- R1. hummbl-bus reaches v1.0.0 with all 5 release gates from `docs/DRIFT_RECONCILIATION_2026-05-24.md` satisfied: founder-only modules classified, common modules semantically diffed, concurrency tests added, replay/spool decision made, README updated to canonical posture.

- R2. All 11 drifted common modules are semantically diffed and reconciled. Each reconciliation decision is recorded in an updated drift document with: what diverged, why, when, and which version won. The drift itself is forensic evidence, not noise to discard.

- R3. hummbl-bus v1 ships with split-channel policy: a coordination channel (PROPOSAL, DECISION, REVIEW, ACK, BLOCKED, MILESTONE) and a separate heartbeat/status sink. The policy is documented in the README and enforced by the writer API.

- R4. All 17 founder-only modules are classified as one of: `promote` (move to hummbl-bus), `absorbed` (already merged into a hummbl-bus module, document where), `defer` (not in v1, tracked for later), or `founder-only` (stays in hummbl-governance archive, not portable). Classification rationale is recorded per-module.

#### Migration

- R5. All 114 files in hummbl-governance that import from `hummbl_governance.bus` migrate to import from `hummbl_bus`. Migration is incremental (batches) and verifiable per-batch. Migration order avoids files actively being touched by other agents.

- R6. hummbl-governance's `hummbl_governance/bus/` directory is frozen as-is after migration completes. No shimming, no deletion, no modification. It remains as readable reference for forensic analysis. The 7,735-message `messages.tsv` archive is preserved as-is, unfiltered.

#### Forensic preservation

- R7. The drift reconciliation document becomes a living forensic record. Every reconciliation decision (which version won, what was discarded, why) is recorded with date and rationale. The document is preserved in hummbl-bus `docs/` as the canonical account of how the bus evolved.

### Actors

- **Operator** — owns archive curation timeline decision, Gitea token revocation coupling, hummbl-governance freeze declaration.
- **Migration agent (likely codex)** — owns drift reconciliation, semantic diffs, module classification, incremental file migration. codex has deepest bus-global.py knowledge per bus-backup-hardening-v3 review.
- **Fleet agents (all)** — must adopt split-channel posting behavior when hummbl-bus v1 lands. STATUS/heartbeat goes to the new sink, not the coordination channel.

### Key Flows

- F1. Drift reconciliation
  - **Trigger:** Extraction kickoff.
  - **Actors:** Migration agent.
  - **Steps:** For each of 11 drifted common modules, produce a semantic diff. Record what diverged, why, and which version wins. Update `DRIFT_RECONCILIATION` doc per decision.
  - **Outcome:** All common modules reconciled. Drift documented as forensic evidence.
  - **Covered by:** R1, R2, R7.

- F2. Founder-only module classification
  - **Trigger:** Drift reconciliation complete.
  - **Actors:** Migration agent.
  - **Steps:** For each of 17 founder-only modules, classify as promote/absorbed/defer/founder-only. Record rationale. Promote modules move to hummbl-bus. Absorbed modules get documentation pointing to where functionality now lives. Defer modules are tracked. Founder-only modules stay in archive.
  - **Outcome:** All modules classified. hummbl-bus module inventory complete.
  - **Covered by:** R1, R4.

- F3. Split-channel policy landing
  - **Trigger:** hummbl-bus v1 writer API implementation.
  - **Actors:** Migration agent, fleet agents.
  - **Steps:** hummbl-bus v1 writer enforces split channels (coordination types only in main channel, STATUS/heartbeat routed to separate sink). Fleet agents update posting behavior to use the new writer API. Watch loops, dead-mans-switch, bus-watcher post to heartbeat sink.
  - **Outcome:** Coordination channel contains only signal. Flooding fixed.
  - **Covered by:** R3.

- F4. Incremental file migration
  - **Trigger:** hummbl-bus v1 + split channels live.
  - **Actors:** Migration agent.
  - **Steps:** Migrate 114 importing files in batches of 10-20. Per-batch: update imports, run tests, verify no breakage. Avoid files actively touched by other agents (coordinate via bus).
  - **Outcome:** All files import from `hummbl_bus`. hummbl-governance bus/ frozen as reference.
  - **Covered by:** R5, R6.

### Acceptance Examples

- AE1. **Covers R3.** Given a fleet agent posting a watch-cycle STATUS message, when the writer API receives it, then the message is routed to the heartbeat sink, not the coordination channel. The coordination channel contains zero STATUS messages after v1 cutover.

- AE2. **Covers R2, R7.** Given a future reader examining the drift reconciliation doc, when they look up `bridge_client.py`, then they find: the hummbl-governance version (240 lines) vs hummbl-bus version (108 lines), what diverged, why the hummbl-bus rewrite won, and the date the decision was made.

- AE3. **Covers R4.** Given a future reader examining the module classification, when they look up `replay_ledger.py`, then they find: classification (promote/absorbed/defer/founder-only), rationale, and if absorbed, where the functionality now lives in hummbl-bus.

- AE4. **Covers R6.** Given hummbl-governance after migration completes, when a reader opens `hummbl_governance/bus/`, then they find the original modules unchanged — no shim, no deletion, no forwarding pointer. The directory is frozen reference.

### Scope Boundaries

**Deferred for later:**
- hummbl-tuples extraction (same L2 pattern, separate effort)
- krineia extraction (same L2 pattern, separate effort)
- bus-backup-hardening (opencode proposal v3 — should target hummbl-bus after extraction, not hummbl-governance)
- Searchable index over the 7,735-message archive (forensic tooling, not extraction scope)

**Outside this product's identity:**
- Gitea token revocation (coupled decision, operator-owned, separate PROPOSAL)
- hummbl-io org migration (coupled decision, operator-owned, separate PROPOSAL)
- Fleet-health tool (where dead-remote scan moves after hummbl-governance freezes)
- ADR-GOV-008 ratification (consensus framework, independent of extraction)

### Dependencies / Assumptions

- **Depends on:** Operator confirming hummbl-governance archive curation timeline (PROPOSAL v2, req_id=1bad06f123c7466faccf1dfa2919a7e5). Extraction cannot complete while hummbl-governance's bus status is ambiguous.
- **Assumption:** codex is available as migration agent (deepest bus-global.py knowledge). If not, operator assigns alternative.
- **Assumption:** Fleet agents adopt split-channel posting behavior within the migration window. If some agents keep posting STATUS to the coordination channel, flooding persists partially.
- **Assumption:** The 114-file count (verified 2026-08-10) is stable. Files actively added during migration are tracked and migrated too.

### Outstanding Questions

**Resolve Before Planning:**
- OQ1. What is the heartbeat sink? Separate TSV file, log file, or discarded entirely? Affects writer API design.
- OQ2. Does the coordination channel retain BLOCKED and MILESTONE, or do those also move to heartbeat? They're signal-adjacent but lower-priority than PROPOSAL/DECISION/REVIEW/ACK.
- OQ3. Migration batch size — 10-20 files assumed. Operator or migration agent confirms based on collision risk with active work.

**Deferred to Planning:**
- OQ4. Semantic diff tooling — manual diff, automated semantic diff, or AST comparison? Planning decides.
- OQ5. Test strategy for reconciled modules — port hummbl-governance tests, write new parity tests, or both? Planning decides.
- OQ6. Concurrency test scope for `bus_writer.py` (release gate 3) — process-level, thread-level, or both? Planning decides.

### Sources / Research

- `docs/DRIFT_RECONCILIATION_2026-05-24.md` — drift table, release gates, module classification framework
- `docs/BUS_REPO_PROMOTION_REPORT_2026-05-08.md` — promotion report and known gaps
- `docs/ADR-001-extraction-and-bridge-protocol.md` — bridge and MCP server decisions
- `docs/PRD-v0.2.0.md` — v0.2.0 purpose, background, target users, requirements
- hummbl-governance bus modules: `hummbl-governance/hummbl_governance/hummbl_governance/bus/` (28 .py files, 17 founder-only)
- bus-global.py: `hummbl-governance/hummbl_governance/hummbl_governance/scripts/bus-global.py`
- Bus message archive: `hummbl-governance/_state/coordination/messages.tsv` (7,735 messages, 1,317 STATUS, 117 PROPOSAL — verified 2026-08-10)
- Coupled proposals: req_id=1bad06f123c7466faccf1dfa2919a7e5 (archive curation v2), req_id=3528515b13c14434adccbe9a8f178a6f (v1 SUPERSEDED), req_id=69684d859d044a429834087ccbeccac0 (3-proposal review)
