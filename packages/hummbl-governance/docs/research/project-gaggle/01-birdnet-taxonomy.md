# Project GAGGLE — Case Study #1: BirdNET+ Taxonomy

**Project:** GAGGLE — *Aggregator-of-Aggregators Taxonomy & Pattern Library*
**Case Study:** 01 — BirdNET+ Taxonomy (Cornell Lab of Ornithology + Chemnitz UT)
**Status:** discovery / observed (production reference implementation)
**Date:** 2026-08-20
**Origin:** Goose timeout → V-formation analogy (clp-1015ab17600f) → bird API research → BirdNET architecture study
**Cognitive Ledger:** pending (will be posted with taxonomy-v0.2 expansion)

---

## Why this case study exists

The HUMMBL Omni-Meta Sovereign Mesh (HUAOMP ⊗ MTSMU) is an Aggregator-of-Aggregators
currently in Phase -1 Discovery. Its classification taxonomy is a 5-tuple:

> `⟨Domain, Mechanism, TrustTier, LatencyClass, InterfaceMode⟩`

BirdNET+ Taxonomy is a **working production implementation of the same pattern** —
an aggregator that pulls from 8+ canonical sources, normalizes them, cross-references
IDs, resolves multilingual conflicts, and serves a unified queryable surface via REST
API + bulk download. It has 16,193 species, 434 languages, and a live public API.

This case study extracts the architectural patterns BirdNET uses that the current
HUAOMP 5-tuple does not capture, and proposes taxonomy expansions for Phase -1.

**The honest scope caveat (falsification condition):** Bird taxonomy is a bounded,
cooperative, finite-domain (~16k species, stable authority list, non-adversarial
sources). HUAOMP's 20 domains include adversarial, jurisdictional, and shifting
sources (prediction markets, legal dockets, cyber threat intel). BirdNET proves the
aggregator-of-aggregators pattern works for bounded-cooperative domains. It does
**not** prove it works for adversarial ones. The ingestion architecture, source-
precedence rules, cross-reference-ID normalization, and build pipeline are
domain-agnostic and transfer directly; the trust/conflict-resolution layer is not.

---

## BirdNET+ Taxonomy architecture (observed)

### Identity layer

- **Authority anchor:** [AviList](https://avilist.org) — a global bird species
  checklist that reconciles and unifies major world bird lists. A bird must appear
  on the current AviList edition to be included. AviList is the **invariant layer**;
  everything else is layered on top.
- **Stable internal ID:** Every species receives a BirdNET ID (BN-prefix + 5-digit
  number, e.g. `BN00042`). These are **stable across releases** so downstream
  systems can reference a species without worrying about taxonomic name changes.
  The mapping is stored persistently; new species get the next available number.
- **Cross-reference ID graph:** Every species carries external identifiers from
  GBIF, NCBI, Avibase, BirdLife, Macaulay Library, Xeno-Canto, iNaturalist, eBird.
  The aggregator is a **node in a larger ID graph**, not a closed system.

### Source layer (8 collectors)

| # | Source | Role | What it provides |
|---|--------|------|------------------|
| 1 | AviList | Taxonomic authority | Canonical species list (the universe) |
| 2 | iNaturalist | Backbone | Taxon IDs, observation counts, common names (dozens of languages), default taxon photos |
| 3 | eBird | Species pages + regional names | Species pages, Macaulay images, common names in 60+ regional language variants |
| 4 | Wikidata | External IDs + licenses | GBIF/NCBI/Avibase/BirdLife IDs, Wikimedia Commons images + licensing |
| 5 | Wikipedia | Descriptions | Species descriptions in ~20 languages |
| 6 | Macaulay Library | Media cross-reference | Sound recordings, images (copyrighted, licensed under Cornell terms) |
| 7 | Xeno-Canto | Audio cross-reference | Sound recordings |
| 8 | observation.org | Observation cross-reference | Observation records |

### Source-precedence lattice (per-field, not per-source)

This is the critical pattern the HUAOMP 5-tuple misses. **Trust is not per-source;
it is per-source-per-field.** Different fields pull from different sources with
different precedence orders:

**Common names (per-locale):**
1. AviList (English — the authority)
2. eBird (regional language variants — e.g. different Spanish names in Argentina vs Chile vs Mexico)
3. iNaturalist (community-contributed names in languages eBird doesn't cover)
4. Wikidata labels (fill remaining gaps)

**Images (license-aware):**
1. iNaturalist default taxon photo (if Creative Commons licensed)
2. eBird + Macaulay Library species image
3. Wikimedia Commons via Wikidata
4. iNaturalist observation photo (CC-licensed, last resort)
5. Manual override (for misleading/poor auto-selected images)

**Descriptions (per-locale):**
1. Wikipedia extracts
2. Claude-translated/shortened overlays for core languages
3. eBird species description in English (fallback)

### Coverage asymmetry doctrine

> "Species found on iNaturalist but absent from AviList are excluded, and species
> listed on AviList but not yet on iNaturalist are still included so that coverage
> stays as complete as possible."

This is a **bidirectional coverage rule**:
- Authority-over-source: if a source has entities the authority doesn't recognize → **exclude** (source is over-covering)
- Source-under-authority: if the authority has entities the source doesn't → **include with gaps** (source is under-covering)

The authority defines the universe. Sources can over-cover (trimmed) or under-cover
(filled from other sources / left sparse).

### Cross-cutting exclusion filters

> "Species flagged as extinct on iNaturalist are excluded from all groups."

A single flag in one source triggers exclusion across **all groups**. This is a
cross-cutting filter that applies regardless of the per-field source-precedence
lattice.

### Domain-adaptive evidence threshold

> "Some groups, like insects and amphibians, require a slightly higher minimum
> to filter out very sparse or questionable entries."

Different domains (bird vs insect vs amphibian) have **different minimum-evidence
thresholds**. The threshold is domain-adaptive, not global.

### Build pipeline phasing

```
collectors/  →  raw_data/  →  build/metadata  →  dist/species_metadata.{json,csv,zip}
   (ingest)     (park)         (normalize)        (distribute)
```

Separation of concerns:
- **Collectors** — one per source, each writes raw_data JSON
- **Build** — reads all raw_data, applies precedence lattice, produces normalized output
- **Dist** — packaged for REST API + bulk download

### License heterogeneity

> "The metadata itself (names, descriptions, identifiers) is available under the
> project's open-source license. Images, however, carry their own individual
> licenses: most are Creative Commons in various flavors, and Macaulay Library
> images are copyrighted by their photographers and used under Cornell's terms."

**License is tracked per-asset, not per-dataset.** The aggregator must filter and
attribute per-image based on its individual license. This is a field-level provenance
concern, not a dataset-level one.

### Interface layer

- **REST API** — programmatic query access
- **Bulk download** — CSV, JSON, ZIP (full dataset)
- **Browsable website** — human-facing
- All three served from the same `dist/` build output

---

## Taxonomy expansion proposed (v0.1 → v0.2)

The current HUAOMP 5-tuple is:
> `⟨Domain, Mechanism, TrustTier, LatencyClass, InterfaceMode⟩`

BirdNET reveals 7 dimensions this tuple does not capture. Proposed expansion to a
12-tuple (detailed in `taxonomy-v0.2.md`, pending):

| # | New dimension | BirdNET evidence | HUAOMP gap |
|---|---------------|------------------|------------|
| 1 | **AuthorityAnchor** | AviList defines the canonical entity universe | HUAOMP has MTSMU invariant extraction but no named authority-anchor pattern per pillar |
| 2 | **StableIDNamespace** | BN-IDs stable across releases, decoupled from upstream name changes | HUAOMP uses UUIDv7 + SHA-256 fingerprint but doesn't address stable-external-ID-vs-changing-upstream-IDs |
| 3 | **CrossRefIDGraph** | GBIF/NCBI/Avibase/BirdLife/Macaulay/Xeno-Canto IDs per entity | HUAOMP's CER has entity fingerprint but doesn't model the cross-reference ID graph |
| 4 | **PerFieldPrecedenceLattice** | Names vs images vs descriptions each have different source-precedence orders | HUAOMP's TrustTier is per-source; BirdNET shows it must be per-source-per-field |
| 5 | **CoverageAsymmetryDoctrine** | Authority-over-source (exclude) vs source-under-authority (include with gaps) | HUAOMP has no coverage-asymmetry doctrine |
| 6 | **LicenseHeterogeneity** | Per-asset license tracking (CC variants, copyrighted, Cornell terms) | HUAOMP doesn't address license heterogeneity |
| 7 | **DomainAdaptiveThreshold** | Insects/amphibians require higher minimum evidence than birds | HUAOMP has κ_floor but doesn't make it domain-adaptive |

**Plus 3 architectural patterns** (not classification dimensions, but required
patterns for any aggregator-of-aggregators):

| Pattern | BirdNET evidence | HUAOMP gap |
|---------|------------------|------------|
| **BuildPipelinePhasing** | collectors → raw_data → build → dist (4 phases) | HUAOMP's MTSMU pipeline is logical (5 steps) but doesn't separate ingestion from normalization from distribution |
| **ManualOverrideLayer** | "manual overrides when auto-selected image is misleading" | HUAOMP has no escape hatch for when automated precedence produces wrong results |
| **CrossCuttingExclusionFilter** | Extinct flag in iNat → excluded across all groups | HUAOMP has no cross-cutting exclusion doctrine |

---

## What HUAOMP should learn from BirdNET (concrete)

1. **Name the AuthorityAnchor per pillar.** Every one of HUAOMP's 20 domain pillars
   needs ONE source that defines the canonical entity universe (the "AviList" for
   that domain). For Capital Markets: is it SEC EDGAR's CIK? For Legal: is it
   CourtListener's case ID? For Prediction Markets: is it the contract address?
   Without a named authority anchor, the aggregator has no universe to normalize
   against.

2. **Issue stable internal IDs.** HUAOMP should issue its own stable IDs (HUAOMP-IDs)
   decoupled from upstream source IDs, so that when SEC changes a CIK or CourtListener
   renumbers a docket, downstream HUAOMP consumers don't break. BirdNET's BN-ID
   pattern is the reference.

3. **Model the cross-reference ID graph explicitly.** Every entity should carry
   external IDs from every source that references it. The CER's SHA-256 fingerprint
   is for dedup; the cross-ref ID graph is for interoperability. Different concern.

4. **Make TrustTier per-field, not per-source.** A source can be authoritative for
   one field (e.g. eBird for regional bird names) and non-authoritative for another
   (e.g. eBird for species descriptions — Wikipedia/Claude wins there). The
   precedence lattice is per-field.

5. **Define a coverage-asymmetry doctrine.** What happens when a source has entities
   the authority doesn't recognize? What happens when the authority has entities the
   source doesn't? BirdNET's rule (exclude over-coverage, include under-coverage with
   gaps) is a starting point — but HUAOMP's adversarial domains may need a different
   rule (e.g. flag over-coverage for review rather than auto-exclude).

6. **Track license per-asset.** HUAOMP's evidence-grade system should track license
   per-evidence-asset, not per-source. A source can serve some assets under CC and
   others under proprietary terms.

7. **Make κ_floor domain-adaptive.** Different HUAOMP domains need different minimum-
   evidence thresholds. Cyber threat intel (high adversarial) needs a higher floor
   than, say, OpenAlex scholarly graph (low adversarial).

---

## What HUAOMP should NOT copy from BirdNET (the honest limits)

1. **Conflict resolution is trivial in BirdNET.** When AviList and eBird disagree
   on a name, AviList wins because it's the authority. HUAOMP's domains have
   adversarial sources where the "authority" itself may be contested (e.g. which
   regulatory body is authoritative for a given jurisdiction?). BirdNET's
   authority-anchor pattern assumes the authority is uncontested. HUAOMP needs a
   **contested-authority doctrine** that BirdNET doesn't model.

2. **No adversarial source detection.** BirdNET's sources are all cooperative
   scientific/community platforms. HUAOMP needs to detect sources that are
   actively trying to deceive (disinformation, manipulated markets, fabricated
   legal filings). BirdNET has no equivalent.

3. **No temporal conflict.** BirdNET species are stable; a species doesn't
   "change its mind" about what it is. HUAOMP's domains have entities that
   change over time (a company's status, a legal precedent, a market price).
   BirdNET's stable-ID pattern handles taxonomic name changes but not semantic
   changes in the entity itself.

4. **No jurisdictional layer.** BirdNET's locale problem is linguistic (same
   species, different names in different Spanish variants). HUAOMP's jurisdiction
   problem is legal/epistemic (same concept, different legal status in different
   jurisdictions). Linguistic locale resolution is a subset; jurisdictional
   authority resolution is harder.

---

## Provenance

- **Primary source:** https://birdnet.cornell.edu/taxonomy/about (fetched 2026-08-20)
- **Source code:** https://github.com/birdnet-team/birdnet-taxonomy (119 commits, open source)
- **API docs:** https://birdnet.cornell.edu/taxonomy/docs
- **Dataset version:** v0.3-Jul2026 (16,193 species, 434 languages)
- **Related ledger entry:** clp-1015ab17600f (V-formation → rotating-leadership far analogy, same session origin)
- **Related HUAOMP skill:** `omni-meta-aggregator-discovery` (`~/.agents/skills/omni-meta-aggregator-discovery/SKILL.md`)
- **Related HUAOMP spec:** `hummbl_governance/docs/research/2026-08-16_omni_meta_aggregator_huaomp_mtsmu_discovery.md`

## Next steps

1. **Write `taxonomy-v0.2.md`** — the expanded 12-tuple classification spec with
   the 7 new dimensions formally defined, plus the 3 architectural patterns.
   (Pending operator ACK per doc-creation checkpoint protocol.)
2. **Identify Case Study #2** — a production aggregator-of-aggregators from an
   **adversarial** domain (not bounded-cooperative like BirdNET), to test whether
   the patterns transfer or break. Candidates: Google Scholar (academic, semi-
   cooperative), Recorded Future (threat intel, adversarial), Bloomberg Terminal
   (financial, proprietary), Polymarket + Kalshi together (prediction markets,
   semi-adversarial).
3. **Log to Cognitive Ledger** — post the taxonomy expansion as a discovery once
   v0.2 is written and operator-acked.
4. **Post PROPOSAL to bus** — the taxonomy expansion is proposal-worthy (it
   changes the HUAOMP Phase -1 classification scheme).
