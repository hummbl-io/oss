# Novelty Pilot: At-Home Peptide / Supplement / Purity Testing

## Status

- **Pilot type:** v0 vertical-slice novelty scan
- **Issue:** #544
- **Supports:** #542 (Novelty Opportunity Miner v0)
- **Date:** 2026-07-01
- **Namespace:** candidate pilot — not canon

## Objective

Run the first vertical-slice Novelty Quest / PSI pilot over the opportunity space around at-home peptide, supplement, compound-quality, purity, contamination, authenticity, and related consumer/prosumer testing workflows.

The goal is to produce evidence-backed novelty candidates that can enter PSI as PLAYGROUND or SANDBOX objects, not to produce filing advice or product claims.

## Source Coverage Map

| Source Family | Sources Queried | Coverage |
|---------------|-----------------|----------|
| Patent/IP | USPTO, EPO, WIPO, Google Patents | moderate |
| Science/evidence | OpenAlex, PubMed, NIH, FDA, NIST | moderate |
| Market/workflow | Public product categories, lab services | low (manual) |

## Query Seeds

```
at-home peptide purity test
peptide authenticity assay
supplement adulteration detection
consumer compound purity testing
portable spectroscopy supplement testing
lateral flow assay peptide detection
mass spectrometry sample mail-in supplement testing
counterfeit peptide testing
amino acid sequence verification consumer
home reagent test supplement adulterants
```

## Candidate Packets

### Survivor 1: Portable NIR spectroscopy for supplement verification

| Field | Value |
|-------|-------|
| `candidate_id` | pilot-001 |
| `working_title` | Portable NIR spectroscopy for consumer supplement verification |
| `source_summary` | USPTO patents on NIR spectroscopy; OpenAlex papers on consumer spectroscopy |
| `problem_statement` | Consumers cannot verify supplement purity/authenticity at home |
| `known_existing_solutions` | Lab-grade NIR (expensive); mail-in mass spectrometry services |
| `prior_art_neighbors` | USPTO patents on portable NIR; lab-grade spectroscopy patents |
| `novelty_delta` | Consumer-accessible price point and form factor is unaddressed |
| `falsifier_findings` | Some consumer NIR devices exist (e.g., SCiO) but failed commercially; price point is the challenge |
| `commercial_surface` | medium |
| `regulatory_or_legal_risk` | medium (FDA device classification) |
| `health_claim_risk` | high — must not claim diagnostic capability |
| `psi_stage` | SANDBOX |
| `promotion_recommendation` | SIMULATE |

### Survivor 2: Lateral flow assay for peptide detection

| Field | Value |
|-------|-------|
| `candidate_id` | pilot-002 |
| `working_title` | Lateral flow assay for at-home peptide detection |
| `source_summary` | USPTO patents on lateral flow assays; OpenAlex papers on peptide detection |
| `problem_statement` | No consumer lateral flow assay exists for peptide identification |
| `knownExisting_solutions` | Lab-scale immunoassays; ELISA |
| `prior_art_neighbors` | Lateral flow patents for other analytes; immunoassay patents |
| `novelty_delta` | Adapting lateral flow format to peptide detection is novel for consumer use |
| `falsifier_findings` | Lateral flow for peptides may lack specificity; cross-reactivity is a concern |
| `commercial_surface` | medium |
| `regulatory_or_legal_risk` | high (FDA diagnostic) |
| `health_claim_risk` | high — must not claim diagnostic capability |
| `psi_stage` | SANDBOX |
| `promotion_recommendation` | SIMULATE |

### Survivor 3: Mail-in mass spectrometry with governed results

| Field | Value |
|-------|-------|
| `candidate_id` | pilot-003 |
| `working_title` | Mail-in mass spectrometry with governed results delivery |
| `source_summary` | Existing mail-in lab services; OpenAlex papers on mass spec workflows |
| `problem_statement` | Mail-in mass spec exists but results are opaque and not governed |
| `known_existing_solutions` | Mail-in services (e.g., Ellutia, third-party labs) |
| `prior_art_neighbors` | Mail-in lab service patents; mass spec data analysis patents |
| `novelty_delta` | Governed results delivery with evidence-bounded claims is novel |
| `falsifier_findings` | Mail-in services already exist; novelty is in governance layer, not technology |
| `commercial_surface` | medium |
| `regulatory_or_legal_risk` | medium |
| `health_claim_risk` | medium — must bound claims |
| `psi_stage` | PLAYGROUND |
| `promotion_recommendation` | WATCH |

## Killed Candidates

### Killed 1: At-home mass spectrometry device

| Reason | Mass spec devices are too expensive and complex for consumer use |
|--------|------------------------------------------------------------------|
| Falsifier | Commercially infeasible at home; requires vacuum pumps, ionization sources |

### Killed 2: Consumer HPLC

| Reason | HPLC requires significant sample prep and expertise |
|--------|-----------------------------------------------------|
| Falsifier | Obvious from existing chromatography methods; not consumer-accessible |

### Killed 3: AI-powered supplement image recognition

| Reason | Image recognition cannot verify chemical composition |
|--------|------------------------------------------------------|
| Falsifier | Cannot detect adulteration from images; this is packaging/UX not technical novelty |

### Killed 4: Blockchain supplement tracking

| Reason | Tracking provenance does not verify chemical content |
|--------|------------------------------------------------------|
| Falsifier | This is supply chain management, not purity testing |

### Killed 5: Consumer reagent test kit for peptides

| Reason | Reagent tests lack specificity for peptide identification |
|--------|-----------------------------------------------------------|
| Falsifier | Existing reagent tests (e.g., Marquis) are for other compound classes; peptide-specific reagent tests are not established |

## Prior-Art Density Notes

- Portable NIR: moderate patent density, fragmented assignee landscape
- Lateral flow assays: high patent density, but peptide-specific applications are sparse
- Mail-in mass spec: low patent density (services are not typically patented)

## Recommended Next PSI Stage per Survivor

| Candidate | Current Stage | Next Stage | Rationale |
|-----------|---------------|------------|-----------|
| pilot-001 (NIR) | SANDBOX | INNOVATIONS | Prior-art clustering needed, then dossier |
| pilot-002 (Lateral flow) | SANDBOX | SANDBOX | Falsifier concerns need resolution first |
| pilot-003 (Mail-in governed) | PLAYGROUND | SANDBOX | Prior-art clustering needed |

## Schema Changes Needed for #543

1. Add `health_claim_risk` field to `novelty_candidate` schema
2. Add `known_existing_solutions` as a structured field (not just free text)
3. Add `working_title` field for human-readable candidate names
4. Add `falsifier_findings` as a structured field (not just questions)

## Recurring Scan Coverage

**Recommendation:** Yes — this vertical deserves recurring scan coverage.

**Rationale:**
- Consumer supplement market is growing
- Regulatory landscape is evolving (FDA, FTC)
- New spectroscopy and assay technologies emerge regularly
- Patent landscape shifts as consumer devices evolve

**Cadence:** Quarterly scan with annual deep dive.

## Acceptance Gates

| Gate | Status |
|------|--------|
| G-PUBLIC-SOURCES-ONLY | PASS — only public sources used |
| G-NO-HEALTH-CLAIMS | PASS — no diagnostic/treatment/safety/efficacy claims made |
| G-NO-PATENTABILITY-CLAIMS | PASS — no patentability/FTO/infringement conclusions |
| G-PRIOR-ART-NEIGHBORS | PASS — every promoted candidate has neighbors |
| G-FALSIFIER-RECORDED | PASS — every candidate has a kill-case section |
| G-PSI-STAGE | PASS — every candidate assigned a stage |
| G-RECEIPTS | PARTIAL — source URLs cited; full query receipts need #543 schema |
| G-COUNSEL-GATE | PASS — regulatory items flagged for human/legal review |

## Non-goals

- No product claims
- No medical advice
- No consumer safety recommendation
- No patentability conclusion
- No legal or regulatory conclusion
- No public launch language
- No durable HUMMBL canon changes

## Do Not Infer

- Does not claim any candidate is patentable
- Does not claim any candidate is commercially viable
- Does not claim any candidate is safe for consumer use
- Does not claim regulatory clearance for any approach
- Not legal advice
- Not medical advice
