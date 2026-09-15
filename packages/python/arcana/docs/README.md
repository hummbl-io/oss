# arcana/docs/

Design documents, frameworks, and research digests.

| Doc | What it is |
|-----|-----------|
| [platform-set.md](platform-set.md) | Exhaustive platform surface map (implemented modules + sibling contracts) |
| [ecosystem-roadmap.md](ecosystem-roadmap.md) | Sequenced expansion plan for sibling contracts, receipts, validation, and release gates |
| [review-packet-ecosystem-contracts.md](review-packet-ecosystem-contracts.md) | Review packet for ecosystem-contract expansion scope, validation, and risks |
| [paideia-9.md](paideia-9.md) | PAIDEIA-9 content-design framework — 9 evidence-anchored axes, 0-4 rubric, referent specification, instructional_intent flag, integration with ARCANA pipeline |
| [generator-family.md](generator-family.md) | Shared pattern across the 6 brainstorm-and-merge generators; checklist for adding a new generator; conventions; hardening roadmap |
| [llm-content-templates.md](llm-content-templates.md) | Per-article output contract (article.md + article.llm.md + meta.json + schema.jsonld + reflection.md); llms.txt / llms-full.txt conventions; token-economy anti-patterns |
| [research-2026-04-24.md](research-2026-04-24.md) | Compressed picks from parallel agent research: Phoenix for observability, Astro+Cloudflare for publishing, Promptfoo for evals |
| [pressure-test-prawn-account.md](pressure-test-prawn-account.md) | Pressure-test of the PRAWN `account` stage against 5 ARCANA lenses (Foucault, Yarvin, Schmitt, Ostrom, Ashby); 5 amendments absorbed into the contract |
| [pressure-test-prawn-work.md](pressure-test-prawn-work.md) | Pressure-test of the PRAWN `work` stage against 3 ARCANA lenses (Schneier, Ashby, Illich); 3 amendments absorbed into the contract |
| [paideia-9-v0.2-draft.md](paideia-9-v0.2-draft.md) | PAIDEIA-9 v0.2 proposal record -- EMOTION (Em) axis + intent polarity ADOPTED (Wave 2); AUTHENTICITY split deferred |
| [kstar-semantic-115.md](kstar-semantic-115.md) | Live semantic K* diagnostic on the 115-lens registry (K*=31.08, 86/115 distinct clusters, 1.17% near-dup pairs) |
| [psi-crucible-integration-options.md](psi-crucible-integration-options.md) | Exploration: how arcana's content pipeline could join PSI's intent pipeline + the crucible-telemetry skill; six build options for review |
| [crucible-verdict-vocabulary.md](crucible-verdict-vocabulary.md) | Draft contract: how debate verdicts + PAIDEIA gaps + release-gate decision roll up into one crucible status (SURVIVED/WEAKENED/REFUTED/HOLD) |
| [psi-ship-to-arcana-topic-spec-mapping.md](psi-ship-to-arcana-topic-spec-mapping.md) | Draft contract: how a PSI Ship-gated innovation becomes an arcana topic-spec input (field mapping + seed schema + push direction) |
| [quickstart.md](quickstart.md) | From zero to one generated article in ~20 minutes (Ollama + one topic) |
| [AUDIT-2026-08-23.md](AUDIT-2026-08-23.md) | Repository audit snapshot, 2026-08-23 |

## Conceptual map

```
PRAWN (governed operational cycle)
  perceive → reason → account → work → notate → (feeds perceive)
    ↓ orders the taxonomies below
ARCANA (lenses) × PRAXIS (archetypes) × POIESIS (production stages)
    ↓
PAIDEIA-9 (content design)
    ↓
generate_paideia_plan.py  → target 9-vector
    ↓
generate_* family         → lenses, presets, synthesists, scenarios, topics
    ↓
overnight_v0.py           → run multi-lens synthesis
    ↓
generate_article_variants → post-process (article.llm.md + meta + schema + reflection)
    ↓
score_paideia.py          → retroactive tagging
    ↓
generate_llms_txt.py      → site-level AI discoverability
```

### Framework roles

| Framework | Type | Question it answers |
|-----------|------|---------------------|
| **PRAWN** | Operational cycle | *In what order does a governed agent move through time?* |
| **ARCANA** | Taxonomy (lenses) | *Through what theoretical frames do we see?* |
| **PRAXIS** | Taxonomy (archetypes) | *Who are we when we act?* |
| **POIESIS** | Taxonomy (production stages) | *What phase of making are we in?* |
| **PAIDEIA** | Scoring rubric (9 axes) | *How good is the artifact?* |

PRAWN is the temporal spine the taxonomies hang on. The taxonomies tell you
*what to use* at each stage; PRAWN tells you *when* and *in what order*.

## Start-here reading order

- **Building your first thing**: generator-family.md → pick a generator → run it
- **Designing a new content type**: paideia-9.md → score a sample → fill gaps
- **Publishing**: llm-content-templates.md → research-2026-04-24.md (Astro section)
- **Debugging a bad run**: generator-family.md (conventions) → look for PROMPT_VERSION in TSV log

## What's NOT in docs/ yet

Deferred drafts (not yet written):
- `publishing-launch.md` — concrete weekend Astro+Cloudflare checklist
- `observability-spike.md` — Arize Phoenix install + 1-generator instrumentation
- `promptfoo-eval-config.md` — arcana-specific rubric + 15 seed cases

Note: `paideia-9-v0.2-draft.md` was previously listed here as a deferred
draft; it now exists and is ADOPTED (Wave 2) — see the nav table above.
