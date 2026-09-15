# PSI / Crucible Integration Options

Status: **exploration** — options for review before any build. No option is
selected here. Every claim is grounded in a file path on disk as of
2026-09-09.

This doc maps how arcana's content/artifact pipeline could join PSI's
intent/signal pipeline and the `crucible-telemetry` skill surface, then lists
the concrete build slices with honest tradeoffs.

---

## 1. What each surface actually is (grounded)

### PSI — Signal Pipeline (`~/projects/psi`)

PSI refines **noisy intent → fleet-ready signal** through staged trust
boundaries with operator-approved gates.

- Pipeline: `PLAYGROUND (zero trust) → SANDBOX (medium) → INNOVATIONS (high) → FLEET`
  (`PSI/docs/signal-pipeline.md`)
- Gates (operator-approved; no stage self-promotes):
  - **Seed**: `playground/ → sandbox/` — "This has a testable core."
  - **Propose**: `sandbox/ → innovations/` — "This survived experimentation."
  - **Ship**: `innovations/ → Fleet` — "This is worth fleet resources."
- Sanitization receipts: `Cherry-pick / Adopt / Adapt / Avoid` decisions with
  provenance (`PSI/docs/sanitization-receipt-template.md`)
- Claims ledger: append-only, stage-aware JSONL at `PSI/docs/claims-ledger.md`
  (tool: `PSI/tools/claims_ledger.py`; 17 unit tests)
- Tool suite (all stdlib, `--json` modes):
  - `tools/psi_stage.py` — current stage from CWD, allowed/prohibited, exit gate
  - `tools/psi_session.py` — session lifecycle (new/check/list/find/close)
  - `tools/psi_seed.py` — seed tracking + gate status
  - `tools/psi_gate.py` — unified gate management (queue/check/criteria/record) across all 3 gates
  - `tools/psi_status.py` — repo overview snapshot
  - `tools/psi_tui.py` — operator dashboard (ANSI, no deps)
  - `tools/psi_graveyard.py` — graveyard management (list/check/resurface)
- Tests: 45 unittest + 68 smoke = **113 total** (`PSI/tests/`)
- Bus policy per stage (playground: none; sandbox: no fleet writes;
  innovations: STATUS/PROPOSAL/SITREP allowed, adoption still needs operator)

### crucible-telemetry — skill (`~/.agents/skills/crucible-telemetry/SKILL.md`)

Agent lifecycle metrics, guardrail violations, fleet health.

- Event TSV: `~/.claude/telemetry/crucible-events.tsv`
- Columns: `timestamp_utc, event_type, agent, detail, machine, session_id`
- Event types: `GUARD_BLOCK`, `SCOPE_VIOLATION`, `HOOK_FAILURE`
- Secondary source: bus messages (`_state/coordination/messages.tsv`)
- Output: Fleet Status table, Violation Summary, Demotion Signals, Promotion
  Candidates, Recommendations
- Base120 mapping: SY5 (feedback loops), SY11 (governance patterns), DE12
  (constraint isolation), IN2 (inversion)
- Skill chains: `agent-audit`, `rsi-dashboard`
- **Domain: agent guardrail metrics** (not content)

### arcana — content/artifact pipeline (`~/projects/arcana`)

arcana refines **topic → article family → scored → released**.

- `POIESIS_STAGES` (`scripts/ecosystem_contracts.py:59-65`):
  `seed, demiurge, crucible, loom, threshold` — **contract only, no runtimes**
  (`POIESIS/` contains only `README.md`)
- `PRAXIS` archetypes — **contract only** (`PRAXIS/` contains only `README.md`)
- `EVIDENCE/`, `LINGUA/`, `NOMOS/` — **contract only** (each has
  `__init__.py`, `contracts.py`, `README.md`; no functions)
- `RELEASE/gate.py` — **executable** (article → PAIDEIA → LINGUA → NOMOS →
  EVIDENCE → RELEASE → JSON+MD receipt; `pass/hold/blocked`; 5 tests)
- `SYNTHESIS/runtime.py` — **executable** (`paideia-review` workflow:
  article+plan → PAIDEIA score → per-axis gap → root-cause attribution →
  prompt-refiner edit proposal → JSON+MD receipt; 7 tests)
- `scripts/debate_protocol.py` — **executable** (8 phases, 17-field verdict
  ledger, 6 verdict statuses `ACCEPTED/REFUTED/CONDITIONAL/DOMAIN_LIMITED/
  UNRESOLVED/NEEDS_FORMALIZATION`; Ollama-backed, CPU-testable via
  `ollama_fn` injection; 16 tests)
- `PAIDEIA v0.2` — 10 axes `M-D-E-V-C-L-S-P-A-Em` (`scripts/score_paideia.py`)
- `scripts/kstar_diagnostic.py` — semantic diversity (K*=31.08 at 115 lenses)
- **Zero references to PSI today** (grep confirmed across the repo)

---

## 2. The structural mapping

arcana is the **content/artifact** mirror of PSI's **intent/signal** pipeline.
Both are staged refinement with operator-approved gates and append-only
receipts. The pieces exist separately; the join is what's missing.

| PSI (intent) | arcana (content) | Status |
|---|---|---|
| Seed gate — "testable core" | topic-spec → runnable debate/paideia plan | exists (`debate_protocol.load_topic_spec`, `generate_paideia_plan`) |
| Propose gate — "survived experimentation" | **crucible** stage: debate + paideia-review survive → candidate article | **contract only, no runtime** |
| Ship gate — "worth fleet resources" | `RELEASE/gate.py` `pass/hold/blocked` | **executable** |
| claims-ledger (JSONL, stage-aware) | EVIDENCE receipts + debate verdict ledger (17 fields) | partial — arcana has per-run receipts, no append-only stage-aware ledger |
| sanitization receipt (Cherry-pick/Adopt/Adapt/Avoid) | `prompt_refiner` propose/apply edits with provenance | analogous — both are provenance-preserving refinement |
| `crucible-events.tsv` (agent GUARD_BLOCK/SCOPE_VIOLATION/HOOK_FAILURE) | content stress-test events (debate REFUTED, paideia insufficient_data, gate hold) | **missing** |

The two crucible surfaces are the same event-schema pattern on different
domains: `crucible-telemetry` measures **agent** guardrail violations; an
arcana crucible would measure **content** stress-test survival.

---

## 3. Build options

Each option lists: what it is, what exists vs what's missing, cost, what it
unblocks, and the honest tradeoff. No option is recommended over another
here — that's the operator's call.

### Option A — Executable crucible workflow in SYNTHESIS

**What**: A second SYNTHESIS workflow (`crucible`) that chains
`debate_protocol` + `paideia-review` + `release-gate` into one stress-test
receipt, making `POIESIS_STAGES["crucible"]` executable.

**Exists**: all three pieces (`debate_protocol.py`, `SYNTHESIS/runtime.py`
paideia-review, `RELEASE/gate.py`) are executable and tested independently.

**Missing**: the orchestrator that chains them and emits one "what survived"
receipt with a crucible verdict (e.g. `SURVIVED / WEAKENED / REFUTED /
HOLD`).

**Input shape (sub-fork)**:
- A1 — topic-spec in → full chain incl. debate → receipt out
- A2 — article+plan in → paideia-review + release-gate (skip debate) → receipt out
- A3 — both inputs supported (topic-spec OR article+plan)

**Cost**: ~1 new module (`SYNTHESIS/crucible.py` or extend `runtime.py`) +
tests. No new deps. Reuses all existing pieces.

**Unblocks**: the Propose-gate equivalent becomes real; one receipt records
what survived debate, where paideia gaps are, and whether the release gate
holds. Establishes SYNTHESIS as genuinely multi-workflow (paideia-review +
crucible).

**Tradeoff**: largest single slice; the crucible verdict vocabulary needs
defining (do debate verdicts + paideia gaps + gate decision roll up into one
crucible status? how?).

### Option B — arcana↔PSI mapping doc

**What**: `docs/psi-mapping.md` mapping arcana's POIESIS stages + RELEASE
gate to PSI's Seed/Propose/Ship with trust-boundary tags, and arcana's
crucible to `crucible-telemetry`'s event schema.

**Exists**: both pipelines are documented enough to map (this doc §2 is the
draft).

**Missing**: the canonical mapping doc in arcana.

**Cost**: 1 doc, no code.

**Unblocks**: shared vocabulary, reviewable correspondence, and a reference
for any future cross-repo work. Prerequisite-ish for Option D.

**Tradeoff**: docs-only doesn't make anything executable; value is
coordination/clarity, not capability.

### Option C — Content crucible-telemetry bridge

**What**: A writer in arcana emitting content stress-test events into a TSV
mirroring `crucible-telemetry`'s schema
(`timestamp_utc, event_type, artifact, detail, module, run_id`) with event
types like `DEBATE_REFUTED`, `PAIDEIA_INSUFFICIENT_DATA`, `GATE_HOLD`,
`PROMPT_EDIT_PROPOSED`.

**Exists**: `crucible-telemetry` skill + its TSV schema; arcana's
debate/paideia/gate outputs that would source the events.

**Missing**: the arcana-side writer + a decision on TSV location
(arcana-local `scripts/paideia/crucible-events.tsv` vs a shared path the
skill already reads).

**Cost**: 1 small module + tests. Needs the location decision and
confirmation that the existing skill can be pointed at a second TSV (or
whether arcana events should be a separate stream the skill learns to merge).

**Unblocks**: unified fleet+content crucible view through the existing skill;
arcana content stress-test becomes visible in the same dashboard as agent
guardrail violations.

**Tradeoff**: the skill currently keys on `agent` (gemini/kimi/codex/claude);
content events key on `artifact`/`module`, so the schema is parallel but not
identical — the skill may need a small change to read both, or arcana events
stay a separate stream.

### Option D — PSI Ship → arcana topic-spec join

**What**: When PSI Ship-gates an innovation, that ship-packet becomes an
arcana topic-spec input (fleet-ready signal → arcana analysis topic for
multi-lens analysis).

**Exists**: PSI's `ship-packet-template.md` and arcana's
`scripts/topics/arcana-metaethics-good-evil-001.json` topic-spec shape.

**Missing**: a shared contract mapping ship-packet fields → topic-spec
fields, and an import path (does arcana read from `PSI/innovations/`? does
PSI write a topic-spec into `arcana/scripts/topics/`?).

**Cost**: a shared schema + an import/conversion path. Cross-repo (PSI +
arcana). Bigger than A-C.

**Unblocks**: the actual pipeline join — PSI innovations automatically
become arcana topics. This is the "fleet-ready signal gets multi-lens
analysis" loop.

**Tradeoff**: cross-repo coupling; needs a decision on direction (PSI pushes
to arcana vs arcana pulls from PSI) and on whether the ship-packet →
topic-spec mapping is 1:1 or lossy. Should probably land after B (the
mapping doc) so the contract is reviewable first.

### Option E — arcana claims-ledger adoption (PSI-pattern)

**What**: Adopt PSI's append-only, stage-aware JSONL claims-ledger pattern
in arcana for debate verdicts + paideia scores + gate decisions. Every
arcana artifact's provenance and gate history becomes an append-only ledger
entry.

**Exists**: PSI's `tools/claims_ledger.py` (write/query/validate/stats,
`--json` modes, 17 tests) + `docs/claims-ledger.md` schema.

**Missing**: an arcana-side ledger module + a decision on whether to port
PSI's tool verbatim, adapt it, or share it as a dependency.

**Cost**: 1 module + tests (mirror `claims_ledger.py`); possibly a shared
package if both repos should use one implementation.

**Unblocks**: full audit trail of every arcana artifact's lifecycle —
topic-spec → debate verdict → paideia score → gate decision — queryable and
validation-tested. Matches PSI's audit posture.

**Tradeoff**: arcana currently has per-run receipts (JSON bundles) but no
cross-run append-only ledger; this adds a new persistence layer. Is the
audit-trail need real now, or is this premature infrastructure?

### Option F — arcana stage-aware tooling (PSI-pattern)

**What**: `psi_stage`/`psi_gate` analogues for arcana:
`arcana_stage.py` (print current POIESIS stage from CWD, allowed/prohibited,
exit gate) and `arcana_gate.py` (record gate decisions with timestamped
receipts across Seed/Propose/Ship-equivalent gates).

**Exists**: PSI's `tools/psi_stage.py` + `tools/psi_gate.py` as reference
implementations.

**Missing**: arcana equivalents + a decision on whether arcana's gates are
literally Seed/Propose/Ship (mirroring PSI) or the POIESIS-named stages
(seed/demiurge/crucible/loom/threshold).

**Cost**: 2-3 small tools + tests.

**Unblocks**: operator can manage arcana gates the same way they manage PSI
gates; consistent operator-facing surface across both repos.

**Tradeoff**: arcana's POIESIS stages are 5, PSI's are 3 — the mapping isn't
1:1 (Option B would resolve this). Building the tooling before the mapping
is settled risks encoding the wrong gate vocabulary.

---

## 4. Honest notes

- **No option is picked here.** The operator decides which slice(s) to build.
- Options are not mutually exclusive; natural orderings exist:
  - B before D (mapping doc before the cross-repo join)
  - B before F (mapping before stage-tooling that encodes the mapping)
  - A is independent and the highest-leverage *executable* slice
  - C is independent and the cheapest *bridge to an existing skill*
  - E is independent and the largest *audit-infrastructure* slice
- The crucible verdict vocabulary (Option A) and the ship-packet → topic-spec
  mapping (Option D) are the two places where real design work is needed
  before code — both are contracts, not just plumbing.
- Everything in §1 was verified by reading the actual files on
  2026-09-09; nothing is from memory or inference.
