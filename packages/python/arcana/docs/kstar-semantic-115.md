# K* Semantic Diagnostic — 115-lens registry (2026-09-09)

Live semantic K* measurement of the prompt-space diversity of
`scripts/lenses.json` after the v0.2 maturation (ARCANA waves, PRAWN,
synthesists, SYNTHESIS/CANON). Run via `kstar_diagnostic.py --embed ollama
--lenses-json`, Ollama `nomic-embed-text` (768-dim). Raw JSON:
`scripts/paideia/kstar_semantic_115.json`.

## Headline numbers

| metric | 88-lens (prior) | 115-lens (now) |
|---|---|---|
| n | 88 | 115 |
| **kstar_semantic** | 16.16 | **31.08** |
| mean pairwise cosine | — | 0.647 |
| median pairwise cosine | — | 0.6444 |
| frac pairs cos >= 0.80 | — | 0.0117 |
| clusters @ 0.80 | — | 86 / 115 |
| empty prompts | 0 | 0 |

K* nearly doubled (16.16 -> 31.08): completing the rosters materially
increased prompt-space diversity, not just prompt count. 86 of 115 lenses
form distinct clusters at the 0.80 threshold; only 1.17% of pairs (77/6555)
are near-duplicates.

## Near-duplicate pairs (cos >= 0.80) — all intellectual adjacency, not dupes

The 77 near-dup pairs are genuine school-adjacency clusters, not duplicate
prompts. The highest is freud/jung at 0.906 — well below 1.0, so no pair is
a copy. Representative clusters:

- **Psychoanalytic / developmental**: freud/jung 0.906, erikson/jung 0.882, freud/erikson 0.857
- **Linguistic philosophy**: humboldt/wittgenstein 0.898, sapir/whorf 0.892, humboldt/herder 0.890, humboldt/whorf 0.874, wittgenstein/whorf 0.856
- **Capabilities**: nussbaum/sen 0.871 (Nussbaum built on Sen — expected)
- **Autopoiesis / cybernetics**: maturana/varela 0.865 (co-authors), luhmann/latour 0.864, bateson/maturana 0.844
- **Postcolonial**: fanon/bhabha 0.862
- **Continental hermeneutics**: heidegger/gadamer 0.846, nietzsche/gadamer 0.845

## One signal worth noting

`humboldt` appears in 7 of the top 30 near-dup pairs (with wittgenstein,
herder, nietzsche, whorf, sapir, heidegger, gadamer). Its prompt reads as
the most "generic philosophical" of the linguistic-philosophy lenses. Not a
defect — the pair scores stay below 0.91 — but if a future pass wants to
sharpen differentiation, humboldt is the highest-leverage prompt to tighten
(toward its specific relativist-universalist contribution rather than
general language-philosophy framing).

## Interpretation

The coverage tests prove *presence* of prompts; K* semantic proves
*diversity* of prompts. With K* = 31.08, 86/115 distinct clusters, and zero
exact duplicates, the maturation work delivered a genuinely diverse
prompt space. The near-dup pairs that do exist are the ones a political-
philosophy registry *should* have clustering (paired theorists, co-authors,
teacher-student lines) — they reflect intellectual structure, not
prompt-writing laziness.

Method: L2-normalize -> Gram -> trace-normalize -> Jacobi eigenvalues ->
exp(Shannon entropy), per Yang et al. Eq. 16-18. K* is embedding-model-
dependent (Yang et al. App. B.2); `embed_model` is recorded in the JSON for
reproducibility.
