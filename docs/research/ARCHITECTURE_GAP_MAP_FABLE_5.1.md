# HUMMBL Architecture Gap Map — Fable 5.1 Design Session Input

> **Rescue note (2026-09-04):** Copied from archived `hummbl-io/hummbl-governance` commit [`839eeece12da1b347db975509e8b9f0431aa5c0b`](https://github.com/hummbl-io/hummbl-governance/commit/839eeece12da1b347db975509e8b9f0431aa5c0b) (first commit of PR #499). Do not use PR #499 HEAD — later fixture commits delete most of that repo.
>
> Canonical blob on the archived repo: [`docs/research/ARCHITECTURE_GAP_MAP_FABLE_5.1.md` @ 839eeece](https://github.com/hummbl-io/hummbl-governance/blob/839eeece12da1b347db975509e8b9f0431aa5c0b/docs/research/ARCHITECTURE_GAP_MAP_FABLE_5.1.md)
>
> Source PR (open, dirty, do not merge): https://github.com/hummbl-io/hummbl-governance/pull/499

**Date**: 2026-09-03
**Status**: Internal synthesis — feeds Fable 5.1 architecture design session
**Method**: Codebase mapping of 10 specified files + 4 grep sweeps against research findings

This file is the keepable work from the agent PR on the archived standalone repo. The live tree is `hummbl-io/oss`.

## How to close the archived PR

`hummbl-io/hummbl-governance` is archived and read-only. GitHub will reject close/comment/merge until you unarchive.

1. GitHub → `hummbl-io/hummbl-governance` → Settings → Danger Zone → Unarchive.
2. Close https://github.com/hummbl-io/hummbl-governance/pull/499 **without merging**.
3. Do not merge. HEAD is +2/−261,689 across 1,107 files.
4. Re-archive the repo immediately.
5. Optional: delete branch `docs/architecture-gap-map` after close. The keepable commit stays reachable from this copy and from the closed PR commit URL.

## Keepable commit vs dirty HEAD

| Ref | SHA | What it is |
|-----|-----|------------|
| Keep | `839eeece12da1b347db975509e8b9f0431aa5c0b` | Adds this 448-line map only |
| Do not use | `0fd3ae09dfbf5c223d906ab2a77eb87896b0feec` | PR HEAD. Later commits: `init` / `add tests` / `fixture` from `test <t@t.com>` and `CI Test` |

## One-sentence claim from the source doc

Build the CognitiveLedger (provenance graph) first. Every later governance decision depends on knowing where things came from. HUMMBL already has the vocabulary (Durable Intelligence doctrine), the format (state-directory spec), and the primitives (hash-chained receipts), but not the runtime that unifies them.

## Source document outline

1. Component inventory (kernel, primitives, contracts, confirmed absences)
2. Provenance substrate
3. Enforcement boundary (Tier 1 advisory → Tier 1.5 / 2 / 3)
4. Unified authority model (belief, action, recovery, autonomy, evolution)
5. Seven architecture decisions
6. Build order: CognitiveLedger → PDP/PEP split → Tier 1.5 → Recovery+Autonomy

Full original text remains at the blob URL above (448 lines). Paste it here in a follow-up commit if you want this path to be a byte-for-byte copy instead of a rescue pointer.
