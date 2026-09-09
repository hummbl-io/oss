# LLM-optimized content templates

Following the prior research on content ingestibility for AI agents. These
templates are the minimum viable shape for every arcana output to be
RAG-friendly and agent-parseable.

## Per-article frontmatter

Every `article.md` produced by the arcana pipeline should carry:

```yaml
---
title: "..."                            # required — canonical human title
slug: "..."                             # required — URL-safe identifier
date: 2026-04-24                        # required — first generation
updated: 2026-04-24                     # optional — if the doc has been edited
authors: [arcana-overnight]             # required
perspectives: [yarvin, gramsci, ...]    # required — lens IDs used
synthesist: default                     # which synthesist style produced this
summary: "..."                          # required — 3-sentence TL;DR
word_count: 2100                        # optional but useful
reading_time_min: 9                     # optional but useful
evidence_tier: synthesized              # synthesized | primary | speculative
license: CC-BY-4.0
canonical_url: "..."
related: []                             # other article slugs referenced
paideia_vector: 3-2-1-2-0-3-2-0-2       # PAIDEIA-9 signature if scored
paideia_version: paideia-score-v0.1     # which scorer produced it
llm_optimized_variant: article.llm.md   # path to the stripped companion
outputs:
  hero: hero.png
  diagram: diagram.svg
  audio: null
  notebook: null
  schema: schema.jsonld
  meta: meta.json
---
```

## `article.llm.md` — the agent-optimized variant

Key differences from `article.md`:

1. **Dense tables over prose where possible** — token-dense
2. **Consistent entity naming** — one canonical name per entity
3. **No decorative adjectives** — "powerful," "robust," "cutting-edge" stripped
4. **ATX headings only** — `#`, `##`, `###` (tokenizes clean)
5. **Breadcrumb-prefixed sections** — each H2 starts with "Article > Section:"
6. **Inline citations** — `[^n]` markdown footnotes with stable URLs; no
   endnote-only styles (break under chunking)
7. **ASCII punctuation** — `"`, `--`, `...` not smart quotes or `…`
8. **No emojis** — cost multiple tokens each

## `meta.json` — flat metadata object

```json
{
  "title": "...",
  "slug": "...",
  "date": "2026-04-24",
  "authors": ["arcana-overnight"],
  "perspectives": ["yarvin", "gramsci", "..."],
  "synthesist": "default",
  "summary": "...",
  "word_count": 2100,
  "paideia_vector": "3-2-1-2-0-3-2-0-2",
  "license": "CC-BY-4.0",
  "canonical_url": "..."
}
```

## `schema.jsonld` — schema.org JSON-LD

```json
{
  "@context": "https://schema.org",
  "@type": "TechArticle",
  "headline": "...",
  "description": "...",
  "author": {"@type": "Organization", "name": "HUMMBL / arcana"},
  "datePublished": "2026-04-24",
  "license": "https://creativecommons.org/licenses/by/4.0/",
  "keywords": ["...", "..."],
  "url": "..."
}
```

## Site-level `/llms.txt`

Per Jeremy Howard / Answer.AI proposal (Sept 2024). A plain-text index for AI crawlers listing canonical URLs and 1-line summaries.

```
# arcana

> Multi-lens governance and political-philosophy analysis. Each article is a synthesized read of a topic through 9-12 theoretical lenses, with PAIDEIA-9 content-quality scores.

## Articles

- [Google's New Enterprise Agent Platform](/2026-04-24/google-s-new-enterprise-agent-platform/): Nine lenses converge on algorithmic sovereignty; diverge on locus of power.
- [Liability Frameworks for Autonomous Agents](/2026-04-24/what-liability-frameworks.../): ...
- ...

## PAIDEIA-9

- [PAIDEIA-9 spec](/docs/paideia-9.md): 9-axis evidence-grounded framework for content design.
- [Generator family pattern](/docs/generator-family.md): shared pattern across the brainstorm-and-merge generators.
```

## Site-level `/llms-full.txt`

Inlines the full `article.llm.md` of every article. Intended for agents that want a single flat corpus rather than crawling links. ~10-50MB for a moderate site.

## Chunking for embeddings

- **Default chunk size**: 512 tokens with ~50-token overlap
- **Chunk on semantic boundaries**: headings first, then paragraphs — never mid-sentence
- **Prepend breadcrumb to each chunk**: "Article Title > § Section > Subsection\n\n<chunk content>" — boosts retrieval precision
- **Long-context models** (≥ 32k): 1024-2048 token chunks preserve more paragraph semantics

## Anti-patterns (token-wasters)

- Decorative Unicode borders / box-drawing characters
- Emoji in technical prose (each = 2-5 tokens for ZWJ sequences)
- Smart quotes `"` `"` → prefer ASCII `"`
- Em-dashes `—` → prefer `--` (though single em-dash tokenizes to 1 token in Claude tokenizer, mixed punctuation confuses retrieval)
- Repeated boilerplate (cookie notices, footers) — move to exclusion list
- Decorative adjectives that carry no propositional content

## Implementation checklist (per-article outputs)

```
outputs/<date>/<slug>/
├── article.md                  # canonical human
├── article.llm.md              # agent-optimized (NEW)
├── meta.json                   # flat metadata (NEW)
├── schema.jsonld               # JSON-LD (NEW)
├── summary.txt                 # 3-sentence TL;DR (NEW)
├── synthesis.json              # existing
├── perspective_*.json          # existing
├── reflection.md               # intrapersonal prompts (NEW, per PAIDEIA axis C)
├── hero.png                    # ComfyUI default, when image gen wired
├── diagram.mmd + diagram.svg   # Mermaid source + rendered
├── paideia_score.json          # PAIDEIA-9 vector + per-axis
└── run.log                     # existing
```

## Integration

- `overnight_v0.py` generates `article.md`, `synthesis.json`, `perspective_*.json`, `run.log`
- Pending: post-processor that reads `article.md` + `synthesis.json` and emits
  `article.llm.md`, `meta.json`, `schema.jsonld`, `summary.txt`
- Pending: `score_paideia.py` runs on `article.md` → `paideia_score.json`
- Pending: `generate_paideia_plan.py` can run BEFORE generation and the plan
  becomes the contract for downstream generators
