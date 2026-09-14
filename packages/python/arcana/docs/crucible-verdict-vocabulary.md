# Crucible Verdict Vocabulary

Status: **draft** — contract proposal for the crucible workflow's rollup
verdict (Option A from `psi-crucible-integration-options.md`). Defines how
debate verdicts + PAIDEIA gaps + the release-gate decision combine into one
crucible status. No code yet; this is the contract before the runtime.

## Context

The crucible is `POIESIS_STAGES["crucible"]` — *"Stress-Testing — evaluation
under pressure; what survives becomes canon"* (`scripts/ecosystem_contracts.py:62`).
Today it is contract-only. A SYNTHESIS `crucible` workflow would chain three
existing executable pieces and emit one "what survived" receipt:

```
topic-spec ─→ debate_protocol  ─→ per-claim verdicts
                                ↓
              paideia-review    ─→ per-axis gaps + root causes
                                ↓
              release-gate      ─→ pass / hold / blocked
                                ↓
              crucible verdict  ─→ SURVIVED / WEAKENED / REFUTED / HOLD
```

The open question is the rollup: how do the three outputs combine into one
crucible status? This doc defines that.

## Inputs (grounded in existing code)

### 1. Debate verdicts (`scripts/debate_protocol.py`)
A list of per-claim verdicts, each from `VERDICT_STATUSES`:
`ACCEPTED`, `REFUTED`, `CONDITIONAL`, `DOMAIN_LIMITED`, `UNRESOLVED`, `NEEDS_FORMALIZATION`.

### 2. PAIDEIA gaps (`SYNTHESIS/runtime.py` paideia-review)
Per-axis: `gap` (target - actual), `root_cause`, `proposed_fix`, `confidence`.
Plus `axes_underperforming` (gap > 0) and `axes_exceeding` (gap < 0).
Hard axes (D, V, L per PAIDEIA v0.2 §9) are critical; gaps on them weigh more.

### 3. Release-gate decision (`RELEASE/gate.py`)
`pass` / `hold` / `blocked`. Criteria (grounded in `release_decision`):
- `blocked` — empty artifact
- `hold` — lingua warnings OR nomos external-target-requires-standards-mapping
- `pass` — otherwise

## Crucible verdict vocabulary

| Status | Meaning | Becomes canon? |
|---|---|---|
| `SURVIVED` | Passed all three stress tests; no refutations, no critical gaps, gate `pass` | Yes — canon candidate |
| `WEAKENED` | Survived with caveats; conditional/domain-limited verdicts or addressable gaps, gate `pass` or `hold` with addressable reasons | Not yet — revise and re-crucible |
| `REFUTED` | A load-bearing claim was refuted, OR gate `blocked` | No — rejected |
| `HOLD` | Insufficient data; too many unresolved verdicts or paideia attribution returned `insufficient_data` on critical axes | No — needs another pass (batch mode or re-debate) |

## Rollup rules (precedence, highest first)

1. **Release gate == `blocked`** → `REFUTED` (the artifact is empty/invalid;
   no point evaluating further).
2. **Any debate verdict == `REFUTED` on a load-bearing claim** → `REFUTED`.
3. **Insufficient data** → `HOLD`: debate has more than `N` unresolved
   verdicts (`UNRESOLVED` + `NEEDS_FORMALIZATION`), OR paideia attribution
   returned `insufficient_data` on all critical (hard) axes. `N` default 2
   (tunable; batch mode raises sample size and reduces this branch).
4. **Caveats present but no refutation** → `WEAKENED`: debate has
   `CONDITIONAL` or `DOMAIN_LIMITED` verdicts (no `REFUTED`), OR paideia has
   underperforming axes with addressable gaps (`root_cause == "prompt_weakness"`
   and `confidence >= 0.5`), OR release gate == `hold`.
5. **Otherwise** → `SURVIVED`: no refutations, no unresolved load-bearing
   claims, no critical paideia gaps, gate `pass`.

## Open definitions this contract depends on

### "Load-bearing claim"
A claim is **load-bearing** if its removal would collapse the resolution.
The debate protocol does not currently tag claims as load-bearing — the
`constructive_claims` / `adversarial_claims` ledger fields carry `id`,
`claim`, `claim_type`, `assumptions`, `scope`, `uncertainty` but no
`load_bearing` flag.

**Gap to close before the runtime lands**: add an optional
`load_bearing: bool` field to claim objects (default `false`), set by the
constructive/adversarial agents in their phase output. The crucible rollup
only counts `REFUTED` verdicts against claims where `load_bearing == true`.
Without this flag, the rollup falls back to treating *all* `REFUTED` verdicts
as load-bearing (conservative — biases toward `REFUTED`).

### "Critical paideia axes"
The hard axes **D** (Depth), **V** (Motivation), **L** (Load) per PAIDEIA
v0.2 §9. These require LLM judgment and are drift-prone; gaps on them weigh
more than gaps on heuristic-detected axes (M, C, P, E, S, A, Em).

### "Addressable gap"
A paideia gap is **addressable** when `root_cause == "prompt_weakness"` and
`confidence >= 0.5` (i.e., `prompt_refiner` can propose an edit). Gaps with
`root_cause == "insufficient_data"` are not addressable in single-article
mode and push toward `HOLD`.

## Receipt shape (proposed)

The crucible receipt extends the existing SYNTHESIS bundle shape:

```json
{
  "schema_version": "synthesis-crucible-v0.1",
  "workflow": "crucible",
  "generated_at": "<UTC ISO>",
  "inputs": { "topic_spec": {...}, "article": {...}, "plan": {...} },
  "debate": { "verdicts": [...], "verdict_counts": {...} },
  "paideia_review": { "axis_gaps": [...], "axes_underperforming": [...] },
  "release_gate": { "decision": "pass|hold|blocked", "reasons": [...] },
  "crucible_verdict": "SURVIVED|WEAKENED|REFUTED|HOLD",
  "crucible_reasoning": "<why this verdict, citing the rule that fired>",
  "load_bearing_refutations": [...],
  "addressable_gaps": [...]
}
```

`crucible_reasoning` must cite which rollup rule fired and the evidence that
satisfied it (e.g., "rule 2: claim con-3 REFUTED, load_bearing=true").

## Input-shape sub-fork (from options doc)

- **A1** — topic-spec in → full chain incl. debate → receipt
- **A2** — article+plan in → paideia-review + release-gate (skip debate) → receipt
- **A3** — both inputs supported

A1 is the full crucible. A2 is a partial crucible (no debate stress-test);
its verdict vocabulary collapses to `SURVIVED` / `WEAKENED` / `HOLD` (no
`REFUTED` possible without debate — the release gate's `blocked` maps to
`REFUTED` but that's the empty-artifact edge case). This doc recommends A3
with the verdict computed over whichever inputs are present.

## What this contract does NOT decide

- Whether the crucible verdict is operator-gated (PSI-style) or automatic.
  PSI's gates are operator-approved; the crucible verdict here is a
  *recommendation* from the workflow, not a gate decision. The operator
  decides whether a `WEAKENED` artifact is revised or shipped.
- Whether `crucible-events.tsv` (Option C) records the verdict or only the
  sub-events. That's Option C's scope, not this contract's.
