# SYNTHESIS - Runtime Orchestration Surface

**Module**: SYNTHESIS
**Type**: ARCANA sibling module
**Status**: RUNTIME-DEBUT (paideia-review workflow landed in `SYNTHESIS/runtime.py`; broader orchestration still ROADMAP)
**Created**: 2026-09-09

## What is SYNTHESIS?

SYNTHESIS is the runtime orchestration surface for ARCANA run pipelines. It
selects lenses, sequences stages, routes work across sibling modules, and
assembles receipt bundles. It is the layer that turns the contract surfaces
(ARCANA, PRAXIS, POIESIS, PAIDEIA, PRAWN, NOMOS, EVIDENCE, RELEASE, LINGUA)
into a coordinated run.

## Responsibilities

- Select which lenses/stages run for a given topic and in what order.
- Dispatch sub-tasks to the right lens or stage, managing parallelism and
  dependencies while preserving the reason-act separation (PRAWN).
- Track run state and surface drift between the plan and execution.
- Assemble per-step receipts into a bundle for EVIDENCE and RELEASE.

## Compatibility and boundaries

- SYNTHESIS orchestrates and routes; it does not generate content (ARCANA /
  POIESIS), score artifacts (PAIDEIA), set normative policy (NOMOS), or
  publish (RELEASE).
- SYNTHESIS must remain side-effect-free with respect to the external world;
  all write authority stays in PRAWN Work / RELEASE.
- Status is ROADMAP: contracts and personas are scaffolded, runtime behavior
  is intentionally out of scope this phase (docs/platform-set.md §8).

## Runtime debut: `paideia-review` workflow

`SYNTHESIS/runtime.py` is the first executable SYNTHESIS surface. It debuts
with the **paideia-review** workflow, a *different* cross-module chain from
the release gate in `RELEASE/gate.py`:

    article.md + plan.json
      -> PAIDEIA score (score_paideia.score_content, use_llm=False)
      -> target vs actual per-axis gap (overnight_v0.load_paideia_plan, version-aware)
      -> root-cause attribution (gap_analysis.attribute_root_cause)
      -> prompt edit proposal (prompt_refiner.propose_edits / render_proposal)
      -> SYNTHESIS receipt bundle (JSON) + Markdown summary

This composes existing runnable sibling functions and does **not** duplicate
the release-gate chain (article -> PAIDEIA -> LINGUA -> NOMOS -> EVIDENCE ->
RELEASE). It establishes SYNTHESIS as the cross-module workflow entry point,
with the release gate being one workflow and paideia-review another.

Single-article in v0.1 of this runtime. Root-cause attribution
(`gap_analysis.attribute_root_cause`) with `sample_size=1` still proposes
prompt edits for axes where `target>=3` and `actual<=1.5` (the
`prompt_weakness` branch fires before the sample-size guard, confidence
0.55); axes with other gap patterns return `insufficient_data` and no edit.
Batch mode (multiple articles sharing one plan, raising confidence and
sample size) is a later PR in this arc.

### Usage

```bash
python SYNTHESIS/runtime.py --article path/to/article.md \
    --plan scripts/paideia/plans/plan.json --output-dir out/
```

### Tests

`tests/test_synthesis_runtime.py` (7 tests): bundle shape, v0.1-plan
compatibility (Em filled), missing-input errors, summary rendering,
output writing, CLI.

## Canonical contract

- Version: `v0.1-draft`
- Surface: `SYNTHESIS/contracts.py`
- Runtime: `SYNTHESIS/runtime.py` (paideia-review workflow, schema
  `synthesis-paideia-review-v0.1`)

## Personas (initial scaffold)

SYNTHESIS has 3 orchestration-role personas inlined in `scripts/lenses.json`
under the `lenses` key (school `SYNTHESIS / ...`), backed by the
`SYNTHESIS_ROLES` roster in `SYNTHESIS/contracts.py`:

- `conductor` - run orchestration
- `dispatcher` - stage dispatch
- `monitor` - run-state monitoring
