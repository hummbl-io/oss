# PAIDEIA-9 v0.2 — draft proposals

Status: **ADOPTED (Wave 2)** as of 2026-09-09. Proposal A (EMOTION, Em) and
Proposal C (intent polarity) are now canonical: `ecosystem_contracts.PAIDEIA_AXES`
is the 10-tuple `M-D-E-V-C-L-S-P-A-Em`, `PAIDEIA_VERSION = "v0.2-draft"`, and
per-axis `intent` in `{required, deliberate_absent, n_a}` is the additive
polarity field (defaults to `required` for v0.1 plans). Proposal B (AUTHENTICITY
split) remains deferred. v0.1 plans/scores are kept as-is and consumed
version-aware (see `paideia_signature_v0_1`, `gap_analysis.parse_signature`,
`overnight_v0.load_paideia_plan`). This file is retained as the proposal
record; the live contract is in `scripts/ecosystem_contracts.py`.

v0.1 spec: [paideia-9.md](paideia-9.md)

---

## Proposal A: Add EMOTION (10th axis)

### Problem
Affect modulates encoding and retrieval independently of motivation
(Tyng et al. 2017 review in *Frontiers in Psychology*). A horror game and
a comfort tutorial can both score V=4 (motivation) with opposite valence.
No existing PAIDEIA axis distinguishes them.

### Proposal
Add a 10th axis **EMOTION (Em)** scored 0-4:

| Score | Anchor |
|-------|--------|
| 0 | Affect-flat / deliberately dispassionate (e.g. technical reference) |
| 1 | Minor affect signals (word choice, cadence) but content is neutral |
| 2 | Moderate emotional tone; some hooks (curiosity, resolve) but not load-bearing |
| 3 | Emotional arc is a real vehicle for the content |
| 4 | Affect is the content (elegy, rage, awe); ideas ride on emotion |

Valence (positive/negative) is separate from intensity. Consider whether to
track valence as a sub-field (`{intensity: 0-4, valence: pos|neg|mixed}`)
or keep it simple.

### Evidence anchor
Tyng, Amin, Saad & Malik (2017). "The Influences of Emotion on Learning
and Memory." *Frontiers in Psychology* 8:1454.

### Signature change
From `M-D-E-V-C-L-S-P-A` (9 axes) to `M-D-E-V-C-L-S-P-A-Em` (10 axes).

### Open questions
- Is affect genuinely orthogonal to V (motivation), or a facet of it? SDT's
  relatedness component overlaps mild positive affect. Keep them separate if
  the use case surfaces content that scores V-low / Em-high (horror fiction
  with no relatedness-support) or V-high / Em-low (a dry mastery-oriented
  practice set).
- Is valence a required sub-field? Likely yes; many content decisions turn
  on whether the emotional pull is positive (aspirational) or negative (fear).

### Verdict
**Recommend adopt.** The horror-vs-comfort distinction is real and
systematically missing from v0.1.

---

## Proposal B: Split A (AUTHENTICITY) into A_internal and A_external

### Problem
v0.1's A axis (Brown, Collins & Duguid 1989, "Situated cognition") targets
*external* authenticity — does the content prepare the learner for real
contexts? But a video game (Portal) has perfect *internal* authenticity
(diegetic coherence of its own physics) and zero *external* authenticity
(it doesn't transfer to work).

In v0.1, Portal scored A=3, which conflates these.

### Proposal
Split A into two axes:

- **A_internal** — diegetic / internal coherence. Does the content cohere
  within its own rules? Anchors: narrative theory (Ryan, *Narrative as
  Virtual Reality*), game design (Juul, *Half-Real*).
- **A_external** — transfer / real-world authenticity. Does the content
  situate in actual work tasks? Anchor: Brown, Collins & Duguid (1989);
  transfer literature (Barnett & Ceci 2002).

Both scored 0-4.

### Alternative (lighter)
Keep A as one axis but require the `referent` field (§5 of v0.1) to
distinguish — artifact-internal vs external-transfer. Less structural
change but places more burden on the scorer.

### Signature change
If adopted: `M-D-E-V-C-L-S-P-Ai-Ae-Em` = 11 axes. Heavy.

### Verdict
**Lean no.** Single A with a clearer rubric is probably enough:
- A should score **external transfer only**.
- Internal coherence is a content-quality question, not a pedagogy axis.
- Portal-type artifacts should be out-of-scope for instructional PAIDEIA
  per `instructional_intent: false` (v0.1 §6), so the conflation doesn't
  arise if we're strict about scope.

Alternative: keep A as single axis, adopt the stricter rubric. No split.

---

## Proposal D: LLM ensemble detectors for HARD axes (D, V, L)

### Problem
v0.1's `score_paideia.py` returns stub values (`2, "STUB: defaults to ..."`)
for the three HARD axes — DEPTH, MOTIVATION, LOAD. Per spec §9, these
require LLM judgment with a rubric, and they are drift-prone under
single-run scoring (the spec recommends ensemble + variance flagging).

The rec #2 E2E chain test on 2026-04-25 made this concrete: target
3-3-3-3-3-2-3-3-4 / actual 1-2-3-2-1-2-1-1-2 with E and L the only met
axes. The score gap is dominated by HARD-axis stubs returning a flat 2
regardless of content.

### Proposal
Implement LLM-backed detectors for D, V, L using:

- One versioned rubric prompt per axis at
  `prompts/paideia_detect_{depth,motivation,load}_v1.txt`
- N independent runs per axis (default `n_runs=3`) with bumped seeds
- Score = `round(mean(samples))`; standard deviation reported in the note
- `low_confidence` flag when std exceeds 0.75 (per spec §9 reliability floor)
- Invalid runs (parse failure, out-of-range score) are skipped, not retried;
  if all runs invalid, score=0 with `all_runs_invalid: <reasons>` note

### Module
`scripts/paideia_detectors_llm.py` exposes:

```python
detect_axis_llm(axis: str, text: str, *, endpoint, ollama_fn=None,
                n_runs=3, seed=None, timeout=600) -> (score, note)

detect_hard_axes(text: str, *, endpoint, ollama_fn=None,
                 n_runs=3, seed=None, timeout=600) -> {axis: (score, note)}
```

`ollama_fn` is the dependency-injection point so the module is fully
testable without touching the network. Tests use a fake that returns
canned `OllamaResult`s.

### Wiring into score_paideia
`score_paideia.score_content` gains keyword args:
`use_llm=False`, `endpoint=None`, `ollama_fn=None`, `n_runs=3`, `seed=None`.

When `use_llm=True`, the function still runs all 9 heuristic detectors,
then overrides D / V / L with `detect_hard_axes` outputs and bumps
`prompt_version` to `paideia-score-v0.2-llm`. M/C/P heuristics and E/S/A
regex detectors are unchanged.

CLI: `python score_paideia.py --content X.md --use-llm --n-runs 3`.

### Cost / latency
With qwen3.5:9b on a local machine, ~1-2s per detector run, so 3 axes × 3 runs ≈
9-18s per article. For score_all over the existing 12 articles, ~2-4 min
total. Defaults are conservative; n_runs=5 is well-supported by the same
plumbing.

### Status
- [x] Three v1 rubric prompts landed
- [x] `paideia_detectors_llm.py` module (CPU-testable)
- [x] `score_paideia.score_content` `use_llm` flag wired
- [x] CLI `--use-llm`, `--endpoint`, `--n-runs`, `--seed` flags added
- [x] 26 tests in `test_paideia_detectors.py` (parser, aggregator,
      ensemble logic, seeding, integration with score_content)
- [ ] Calibrate prompts against hand-scored corpus (target κ > 0.6 with
      human, per spec §12)
- [ ] Score the existing 12 articles with `--use-llm` and compare
      v0.1 vs v0.2 signatures (real-data validation; needs GPU window)
- [ ] Wire `score_all.py` to optionally pass through `--use-llm`

### Verdict
**Recommend adopt as v0.2 baseline.** Closes the spec gap from §9
("HARD axis detectors land in v0.2") and the rec #2 score-vs-target gap.
EMOTION axis (Proposal A) and intent polarity (Proposal C) are independent
and can land in v0.3 or alongside D when the prompts and scorer changes
land together.

---

## Proposal C: Intent polarity per axis

### Problem
A score of 0 conflates two cases:
- "Absent by oversight" — the content SHOULD have this but doesn't (design debt)
- "Absent by design" — the content type doesn't need this (e.g. a reference
  page deliberately omits scaffolding)

### Proposal
Add an `intent` field per axis:

```json
"per_axis": {
  "S": {
    "target": 0,
    "referent": "artifact",
    "intent": "deliberate_absent",  // or "required" | "n_a"
    "rationale": "Reference pages are random-access; scaffolding is an anti-feature",
    "citation": "Mayer 2021 §14 on expertise reversal"
  }
}
```

Values:
- `required` — axis is expected to score >0; a 0 is design debt
- `deliberate_absent` — axis is intentionally 0 for this content type
- `n_a` — axis doesn't apply (use with `instructional_intent: false`)

### Scorer behavior
When computing a signature or diffing plan vs actual:
- `required` axes contribute to gaps if missed
- `deliberate_absent` axes are skipped
- `n_a` axes are skipped

### Verdict
**Recommend adopt.** This cleanly fixes the API-reference-page false-
penalization problem from the stress-test without inventing new axes.

---

## Proposed v0.2 state

If we accept **A** (EMOTION) + **C** (intent polarity) and reject B (A split):

- 10 axes: M-D-E-V-C-L-S-P-A-Em
- Each axis has `{target, referent, intent, rationale, citation}`
- Non-instructional content uses `instructional_intent: false` AND can mark
  individual axes as `intent: n_a`

### Migration path
- v0.1 plans/scores become v0.2 with `intent: required` everywhere by default
- v0.2 scorer adds a 10th axis; v0.1 signatures become shorter strings for
  compatibility comparisons
- `generate_paideia_plan.py` bumps to `paideia-plan-v2`, file at
  `prompts/paideia_plan_v2.txt`
- Existing 11 scored articles (v0.1 signatures) are kept as-is; re-scoring
  to v0.2 is opt-in

### What this implies for code
- `overnight_v0.py` constants: add "Em" to PAIDEIA_AXES (backward break —
  existing v0.1 plan files would fail validation). Handle via version key
  in plan JSON.
- `score_paideia.py`: add detector for EMOTION (candidate: sentiment +
  affect-word density heuristic; anchor to a small lexicon).
- `generate_paideia_plan.py`: update prompt + validator for 10 axes +
  intent field.

---

## Remaining open questions (neither adopt nor reject yet)

1. **Is PAIDEIA still a single framework after v0.2?** With `instructional_intent`
   false + `intent: n_a` per axis, the framework already flexes across
   content types. Adding more axes increases flex but also increases the
   chance that *no* axis cleanly applies to some artifact. There's a point
   at which "one framework with exceptions everywhere" = "not really one
   framework."

2. **Automated intent detection?** Can the scorer guess `intent` per axis
   for existing content? Probably requires the content metadata
   (content_type, audience) not the raw text. Defer; score by hand for the
   first ~100 articles to build a labeled set.

3. **Ensembling the scorer.** The agent research flagged D/V/L as drift-prone
   for single-LLM scoring. An ensemble (3 runs, variance threshold) would
   address this. Separate from v0.2 — a scorer-quality question, not a
   spec question.

---

## Recommendation

**v0.2 in two waves.**

Wave 1 (LANDED 2026-04-25, scaffold only): Proposal D — LLM ensemble
detectors for HARD axes D/V/L. Prompts + module + tests landed; awaits
calibration run + score_all wiring.

Wave 2 (DRAFT): Proposals A + C — EMOTION axis + intent polarity.
Defer B (Authenticity split). Final signature `M-D-E-V-C-L-S-P-A-Em`
with `intent` field per axis.

Implementation effort for Wave 2:
- Spec doc rewrite: ~1 hour
- `overnight_v0.py` PAIDEIA_AXES update + v0.2 plan schema: ~1 hour
- `score_paideia.py` EMOTION detector + intent handling: ~2 hours
- `generate_paideia_plan.py` v2 prompt + validator: ~1 hour
- Tests: ~1 hour
- Re-score 12 existing articles under v0.2: 1 minute (CPU-only)

Total Wave 2: ~6 hours; doesn't need Ollama except for the EMOTION detector
calibration if we add an LLM-based EMOTION detector (stretch — likely yes
to stay consistent with the D/V/L pattern from Wave 1).
