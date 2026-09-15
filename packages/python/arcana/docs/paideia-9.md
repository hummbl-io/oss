# PAIDEIA-9

**Principled Axes for Instruction, Design, Engagement, Integration & Assessment — 9 axes.**

*Pronunciation: pie-DAY-uh. Greek παιδεία — the holistic formation of a person through learning.*

Short-form identifier: `PDA9`
Version: `v0.1-draft`
Status: DRAFT, post-stress-test. Amendments tracked in `§10`.
Owner: HUMMBL
Generators: `generate_paideia_plan.py`, `score_paideia.py` (skeleton)

---

## 1. Purpose

PAIDEIA-9 is an evidence-anchored framework for designing and evaluating instructional content across modalities. It exists to:

1. **Replace ad-hoc content design choices with a measurable 9-vector target**, so content generators and human authors converge on the same quality bar.
2. **Surface what content is missing** rather than just what it contains — explicit 0-scores on PRACTICE or METACOGNITION are design signals.
3. **Remain compatible** with the downstream generator family (`generate_outline.py`, `generate_examples.py`, etc.) and with any LLM-driven authoring pipeline.

PAIDEIA-9 is NOT:
- A theory of individual differences (it deliberately rejects the debunked *learning styles* frame).
- A universal content framework (it's a **pedagogy** framework — §10 note on scope ambiguity).
- A rebadge of Bloom's Taxonomy or Gardner's MI.

## 2. Evidence grounding

Every axis anchors to replicated cognitive-science or instructional-design research. Frameworks explicitly **excluded on evidence grounds**: VAK/VARK (Pashler et al. 2008), Felder-Silverman, Honey & Mumford, Dunn & Dunn, MBTI-as-learning-lens, Connectivism as empirical claim.

Frameworks directly **load-bearing**: Mayer 2009, Paivio 1986, Biggs & Collis 1982, Chi & Wylie 2014, Ryan & Deci 2000, Flavell 1979, Zimmerman 2000, Sweller 2011, Kalyuga 2007, Dreyfus 1980, Vygotsky 1978, Roediger & Karpicke 2006, Dunlosky et al. 2013, Brown et al. 1989, van Merriënboer 2018.

## 3. The nine axes

| # | ID | Name | One-line def | Evidence anchor |
|---|----|------|--------------|----------------|
| 1 | **M** | MODALITY | Representational channels used — verbal, visual-spatial, symbolic, embodied, auditory | Mayer 2009; Paivio 1986 |
| 2 | **D** | DEPTH | Intellectual operation demanded, scored via SOLO structure of expected response | Biggs & Collis 1982 |
| 3 | **E** | ENGAGEMENT | Overt learner activity mode: Passive / Active / Constructive / Interactive | Chi & Wylie 2014 (ICAP) |
| 4 | **V** | MOTIVATION | Degree to which autonomy, competence, and relatedness needs are afforded | Ryan & Deci 2000 (SDT) |
| 5 | **C** | METACOGNITION | Explicit prompts for planning, monitoring, reflection on one's own understanding | Flavell 1979; Zimmerman 2000 |
| 6 | **L** | LOAD | Estimated extraneous and germane cognitive load vs. learner's expertise | Sweller 2011; Kalyuga 2007 |
| 7 | **S** | SCAFFOLD | Position on novice→expert arc the content targets, and fade schedule | Dreyfus 1980; Vygotsky 1978 |
| 8 | **P** | PRACTICE | Presence and quality of retrieval, spacing, interleaving, feedback | Roediger & Karpicke 2006; Dunlosky et al. 2013 |
| 9 | **A** | AUTHENTICITY | Degree of situated, context-embedded, whole-task realism | Brown et al. 1989; van Merriënboer 2018 |

Compact content signature: **`M-D-E-V-C-L-S-P-A`** — a 9-vector of integer scores 0-4.

## 4. 0-4 rubric (per axis)

All axes are scored on the same scale with consistent semantics:

- **0** — absent or explicitly removed
- **1** — present but minimal, token-level
- **2** — present and functional, baseline
- **3** — well-developed, better than baseline
- **4** — maximally developed for this content type

## 5. Referent specification

**Stress-test finding:** every axis silently scored *the artifact*, *the inferred reader's state*, or *the actual reader's demand*. These diverge. Example: DEPTH=4 on a Euclidean proof means *a learner who understands it operates at extended-abstract* — a claim about the inferred reader, not the text.

**v0.1 requirement:** each axis score **must specify a referent**:

- **`artifact`** — the content object itself (e.g., "the text contains 3 visual channels")
- **`reader_state`** — inferred state of the assumed reader (e.g., "an expert reader is at Dreyfus stage 4")
- **`reader_demand`** — what the content demands of the actual reader (e.g., "this proof demands extended-abstract SOLO")

The `per_axis` field in a PAIDEIA plan must include `{"target": int, "referent": str, "rationale": str, "citation": str}`.

## 6. Instructional intent

**Stress-test finding:** the framework assumes *instructional* content. Haiku, TikTok, and pure art score 0 on LOAD/SCAFFOLD/PRACTICE not because they fail instructionally but because they aren't trying to instruct.

**v0.1 requirement:** every plan carries `instructional_intent: bool`. When `false`:

- L, S, P may score 0 without triggering "deficiency" flags
- `content_type_warning` explains which axes are partial/advisory
- The scorer outputs a partial PAIDEIA vector rather than a full one

PAIDEIA-9 is a **pedagogy** framework. Non-instructional artifacts can be scored advisorily; their partial vectors should not be compared directly to instructional vectors.

## 7. Worked example

Content: a short technical explainer video on rate limiters.

```
{
  "instructional_intent": true,
  "target_vector": {"M":3, "D":2, "E":1, "V":2, "C":0, "L":3, "S":2, "P":0, "A":2},
  "per_axis": {
    "M": {"target":3, "referent":"artifact",       "rationale":"Narration + diagrams + animated token bucket; no embodied.", "citation":"Mayer 2009"},
    "D": {"target":2, "referent":"reader_demand",  "rationale":"Multistructural — lists strategies without relational synthesis.", "citation":"Biggs & Collis 1982"},
    "E": {"target":1, "referent":"artifact",       "rationale":"Active (pause-and-think) but no constructive prompts.", "citation":"Chi & Wylie 2014"},
    "V": {"target":2, "referent":"artifact",       "rationale":"Competence supported; autonomy linear; relatedness low.", "citation":"Ryan & Deci 2000"},
    "C": {"target":0, "referent":"artifact",       "rationale":"No metacognitive prompts.", "citation":"Flavell 1979"},
    "L": {"target":3, "referent":"reader_state",   "rationale":"Load managed: segmented, signaled, no split-attention.", "citation":"Sweller 2011"},
    "S": {"target":2, "referent":"reader_state",   "rationale":"Targets advanced-beginner; one fade to competent.", "citation":"Dreyfus 1980"},
    "P": {"target":0, "referent":"artifact",       "rationale":"No retrieval, spacing, or feedback.", "citation":"Roediger & Karpicke 2006"},
    "A": {"target":2, "referent":"artifact",       "rationale":"Pseudocode real; not real system.", "citation":"Brown et al. 1989"}
  }
}
```

Signature: `3-2-1-2-0-3-2-0-2`. Zeroes on C and P are explicit design debt; fix with a 3-question retrieval card + one "what would you try first?" prompt.

## 8. Integration with ARCANA generator pipeline

```
┌─────────────────────┐
│ generate_paideia_plan.py │  → PaideiaPlan (target 9-vector + per_axis + hints)
└─────────────────────┘
            │
            ▼
┌─────────────────────┐
│ downstream generators │  consume hints:
│ - generate_outline    │  depth & scaffold scaling
│ - generate_examples   │  authenticity & modality mix
│ - generate_assessment │  practice & metacognition items
│ - generate_delivery   │  engagement + motivation framing
└─────────────────────┘
            │
            ▼
┌─────────────────────┐
│ score_paideia.py    │  → scored vector + delta from plan
└─────────────────────┘
```

The plan becomes a *contract* that downstream generators must satisfy; the scorer validates output against the plan.

`score_paideia.py` currently returns `comparable_vector: false`. M/C/P are heuristic; D/V/L are stubs (or uncalibrated LLM scores if `--use-llm --allow-uncalibrated`). Do not treat the signature as a PAIDEIA-9 grade, and do not compare vectors across artifacts until HARD axes have a locked rubric, extractive evidence, and a human calibration set.

## 9. Scoring existing content (retroactive tagging)

Per-axis auto-scorer difficulty (see §10 stress-test findings):

| Axis | Difficulty | Detection strategy |
|------|-----------|--------------------|
| M | EASY | Count present channels (text/image/audio/code/video) via content-type + presence detection |
| D | HARD | Map content claims to SOLO levels via rubric prompt; use exemplars per level |
| E | MEDIUM | Detect ICAP affordances (read-only / select / generate / turn-taking) |
| V | HARD | SDT is latent; detect autonomy-support language, mastery feedback, social cues |
| C | EASY | Regex-plus-semantic for prompt verbs: "predict," "reflect," "why," "what if" |
| L | HARD | Requires expertise model of reader; detect extraneous markers (split-attention, redundancy) |
| S | MEDIUM | Detect fade schedule (worked-examples → partial → independent); single artifacts default low |
| P | EASY | Detect retrieval prompts, spacing intervals, interleaved sets, feedback loops |
| A | MEDIUM | Compare task surface to real-world task inventory; LLM has priors but hallucinates |

**Reliability floor:** D, V, L are drift-prone for single-LLM scoring. Ensemble (3+ runs) with variance threshold; flag any axis with inter-run std > 0.75 for human review.

## 10. Stress-test findings + pending amendments

Stress-test applied 5 content types: haiku, API reference, video game (Portal), TikTok, scientific proof.

**Passing**: video game (cleanly scored 4-3-4-4-2-3-3-4-3).

**Structural weaknesses surfaced:**

1. **Scope ambiguity** — framework is pedagogy-specific. **Fixed in v0.1** via `instructional_intent` flag (§6).
2. **Referent ambiguity** — axes silently score artifact vs inferred-reader vs demand. **Fixed in v0.1** via required `referent` field (§5).
3. **Missing affect axis** — emotional valence (Tyng et al. 2017) is orthogonal to V and has evidence for memory/transfer. **Pending v0.2**: add 10th axis EMOTION.
4. **Authenticity split** — A conflates internal coherence (diegetic, e.g. video game world) with external transfer (real-world). **Pending v0.2**: split into A_internal and A_external OR clarify rubric that A targets external transfer only.
5. **Intent polarity** — zero scores don't distinguish "absent by oversight" from "absent by design." **Pending v0.2**: add `intent` flag per axis (required|deliberate_absent|n/a).

## 11. Content types outside v0.1 scope

- Pure aesthetic artifacts (poetry, visual art without didactic intent)
- Entertainment (games treated as artifacts; instructional framing optional)
- News reporting (information transfer, not skill building)
- Persuasive content (marketing, political) — different framework needed

For these, score PAIDEIA-9 advisorily; do not compare vectors to instructional content.

## 12. Next steps

- [ ] Implement `score_paideia.py` with per-axis detectors (skeleton landed, detectors incremental)
- [ ] Calibrate detectors against hand-scored seed corpus (target κ > 0.6 with human)
- [x] v0.2 amendments: EMOTION axis (Em) + intent polarity adopted (Proposal A + C; Proposal B deferred). See [paideia-9-v0.2-draft.md](paideia-9-v0.2-draft.md).
- [x] `generate_content_plan_bundle.py` — chains paideia_plan + downstream generators end-to-end (scaffolded: the four downstream generators are recorded with `implemented=False` until they land; introduces the v0.2 `intent` polarity field as an additive per-axis layer)
- [ ] Cross-reference each axis to Base120 via MCP server (currently UNVERIFIED)

## 12a. PAIDEIA scorers in lenses.json

All 9 PAIDEIA scorer personas are now inlined in `scripts/lenses.json` under the
`paideia_scorers` key. Each scorer has a dedicated system prompt that encodes
the axis definition, the 0-4 rubric, the evidence anchor, and the required JSON
output schema (`{axis, score, referent, rationale, citation}`). The scorers are
designed to be invoked individually or as an ensemble for per-axis scoring.

| Scorer key | Axis | Axis name | Evidence anchor |
|------------|------|-----------|-----------------|
| `modality_scorer` | M | MODALITY | Mayer 2009; Paivio 1986 |
| `depth_scorer` | D | DEPTH | Biggs & Collis 1982 |
| `engagement_scorer` | E | ENGAGEMENT | Chi & Wylie 2014 (ICAP) |
| `motivation_scorer` | V | MOTIVATION | Ryan & Deci 2000 (SDT) |
| `metacognition_scorer` | C | METACOGNITION | Flavell 1979; Zimmerman 2000 |
| `load_scorer` | L | LOAD | Sweller 2011; Kalyuga 2007 |
| `scaffold_scorer` | S | SCAFFOLD | Dreyfus 1980; Vygotsky 1978 |
| `practice_scorer` | P | PRACTICE | Roediger & Karpicke 2006; Dunlosky et al. 2013 |
| `authenticity_scorer` | A | AUTHENTICITY | Brown et al. 1989; van Merriënboer 2018 |

**Drift-prone axes** (D, V, L) carry explicit flags in their system prompts
instructing the scorer to flag uncertain scores for human review, consistent
with the reliability floor in §9.

## 13. References

- Mayer, R. E. (2021). *Multimedia Learning* (3rd ed.). Cambridge.
- Paivio, A. (1986). *Mental Representations*. Oxford.
- Biggs, J., & Collis, K. (1982). *Evaluating the Quality of Learning*. Academic Press.
- Chi, M. T. H., & Wylie, R. (2014). The ICAP framework. *Educational Psychologist* 49(4).
- Ryan, R. M., & Deci, E. L. (2000). Intrinsic and extrinsic motivations. *Contemporary Educational Psychology* 25.
- Flavell, J. H. (1979). Metacognition and cognitive monitoring. *American Psychologist* 34(10).
- Zimmerman, B. J. (2000). Attaining self-regulation. *Handbook of Self-Regulation*.
- Sweller, J., Ayres, P., & Kalyuga, S. (2011). *Cognitive Load Theory*. Springer.
- Kalyuga, S. (2007). Expertise reversal effect. *Educational Psychology Review* 19(4).
- Dreyfus, S. E., & Dreyfus, H. L. (1980). *A Five-Stage Model*. UC Berkeley.
- Vygotsky, L. S. (1978). *Mind in Society*. Harvard.
- Roediger, H. L., & Karpicke, J. D. (2006). Test-enhanced learning. *Psychological Science* 17(3).
- Dunlosky, J., et al. (2013). Improving students' learning. *Psychological Science in the Public Interest* 14(1).
- Brown, J. S., Collins, A., & Duguid, P. (1989). Situated cognition. *Educational Researcher* 18(1).
- van Merriënboer, J. J. G., & Kirschner, P. A. (2018). *Ten Steps to Complex Learning* (3rd ed.). Routledge.
- Waterhouse, L. (2006). Multiple intelligences. *Educational Psychologist* 41(4).
- Pashler, H., et al. (2008). Learning styles. *Psychological Science in the Public Interest* 9(3).
