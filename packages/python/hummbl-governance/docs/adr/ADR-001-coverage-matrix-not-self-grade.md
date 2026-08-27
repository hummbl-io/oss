# ADR-001 — Coverage matrix, not self-grade, for compliance claims

- **Status:** accepted
- **Date:** 2026-05-14
- **Decision owner:** Reuben Bowlby (operator)
- **Steward:** HUMMBL, LLC
- **Authors:** claude-code (host-C)
- **Supersedes:** implicit pre-2026-05-14 framing of "governance score / A+ rubric"
- **Superseded by:** none
- **Related:** `hummbl-governance#26` (methodology issue), `feedback_no_self_grades_on_public_surface.md` (operator memory rule), `hummbl-production#241` (claim_status: hold), `hummbl-production#242` (claim_status: retired)

---

## Context

On 2026-05-14, opencode shipped an A+ Governance Rubric v2 producing a composite score of 90.3% (158/175) across 7 compliance frameworks. A methodology peer review (`hummbl-governance#26`) identified four P1 findings, the central one being that the score measured "completeness within a chosen mapping surface" rather than coverage of each standard's actual surface (e.g., ISO 27001 score = 92% within 6 of 93 controls = ~6.5% surface coverage). A regulation-weighted re-aggregation was proposed (B+ headline) that would survive scrutiny better than A+, but the operator then rejected the entire shape of the question.

> *"we don't need to publish our own self grades."* — operator, 2026-05-14 ~09:00Z

The operator subsequently clarified that a different artifact IS wanted:

> *"we can however create a chart / matrix that scores us against all compliance standards. i want to be able to say my system fulfills ALL compliance standards"* — operator, 2026-05-14 ~09:25Z

This ADR codifies the structural distinction between the two.

---

## Decision

HUMMBL **does not** publish self-issued numeric or letter grades against external compliance frameworks on the public claim surface.

HUMMBL **does** maintain coverage matrices as internal evidence workpapers. A matrix can become public claim support only after its row counts, evidence paths, command examples, and boundary classifications are validated.

> *"HUMMBL maps applicable controls in [enumerated standards] to technical primitives, partial customer-policy splits, or explicit boundary statements. Public use requires validated evidence cells and operator/legal review."*

Validated matrices may replace aggregate score claims as the public-facing artifact of compliance work. Draft matrices are internal starter material only.

---

## Definitions

### Self-grade (REJECTED)

Any of the following on the public claim surface (hummbl.io, pitch deck, one-pager, capability brief, outreach copy, blog, social, press):

- Letter grades on external frameworks: *"A+ governance"*, *"B+ Law-Bound"*, *"Production tier"*
- Percentages on external frameworks: *"92% NIST CSF coverage"*, *"90.3% governance maturity"*, *"88% law-bound composite"*
- "X of N controls mapped" framed as a coverage claim **when the remaining N–X controls are not enumerated as rows** (mapping subset hidden behind a fraction = self-grade)
- Composite scores across frameworks of any shape
- Tier labels (*"Substantial"*, *"Partial"*, *"Claimed"*) used as marketing copy without methodology footnote

### Coverage matrix (ACCEPTED)

A complete, validated enumeration of every control across every named framework, with the following invariants:

1. **Completeness invariant**: every article/control/subcategory in every named framework has a row. No silent exclusions. Frameworks dropped from the matrix are dropped from the claim, not hidden.
2. **Row invariant**: every row is either (a) fulfilled by a named HUMMBL primitive, (b) partially fulfilled with explicit description of what HUMMBL covers and what customer policy covers, or (c) a boundary row stating that the control is the customer organization's responsibility and HUMMBL provides the evidence interface.
3. **Evidence invariant**: every "fulfilled" row must point to a validated evidence command or resolvable artifact before public use. Draft rows may contain planned or external evidence targets only when explicitly labeled as such.
4. **Attestation honesty**: where a framework requires third-party attestation (SOC 2 Type II, ISO 27001 certification, EU AI Act Notified Body conformity assessment), boundary disclaimers explicitly state this and do not claim the attestation. The matrix supports a claim of *"every applicable control mapped"*, not of *"holds the certification."*

### "Fulfills ALL" (PERMITTED)

Any public headline claim that HUMMBL maps or fulfills applicable controls is permitted **only when**:

- The matrix is complete (Completeness invariant)
- "Applicable" is defined explicitly in each row (Row invariant)
- Boundary rows are visible alongside fulfilled rows (Attestation honesty)

The claim does NOT assert:
- That HUMMBL holds statutory certifications (those require accredited third parties)
- That every named framework is technically achievable by software alone (some controls are organizational/physical by design)
- That coverage is universal across all standards in existence (only enumerated standards are in scope)

---

## Canonical row syntax

```
| Article / Control | Requirement (≤1 line) | HUMMBL coverage | Evidence artifact |
|---|---|---|---|
| EU AI Act Art. 9 | Continuous iterative risk mgmt across lifecycle | ✅ governance bus + risk register tuples + signed audit log | `compliance_mapper --framework eu-ai-act --control art-9` |
| EU AI Act Art. 5 | Prohibited AI practices (8 categories) | 🟡 Customer policy (not platform-enforceable). HUMMBL provides use-case classification + red-flag detection + kill-switch. | `services/kill_switch_core.py` + use-case taxonomy |
| EU AI Act Art. 71 | EU institutional structure (AI Office) | ⚪ Boundary: organizational/regulatory. HUMMBL provides notification interface. | n/a — boundary row |
| EU AI Act Art. 99 | Penalties (Tier 2: €15M / 3% turnover) | ⚪ Boundary: regulatory penalty structure (not a software control). | n/a — informational row |
```

### Coverage state legend (canonical)

| State | Glyph | Meaning |
|---|---|---|
| Fulfilled | ✅ | Named HUMMBL primitive implements the control; evidence artifact must be validated before public use |
| Partial | 🟡 | HUMMBL primitive provides part of the control; customer policy completes it. Both parts named explicitly. |
| Boundary | ⚪ | Control is organizational, physical, regulatory, or otherwise outside what software can implement. HUMMBL provides evidence interface or notification mechanism where applicable. |
| Out of scope | ⛔ | Control does not apply to the AI governance platform context (e.g., physical badge access for unmanned services). Row exists to explicitly disclaim, not to silently exclude. |

### Per-framework boilerplate (required at top of each matrix file)

- Source citation (e.g., "Regulation (EU) 2024/1689 (AI Act)")
- Effective date / enforcement timeline reference
- Boundary disclaimer ("HUMMBL is not a [Notified Body / accredited registrar / CPA firm / etc.]; statutory certification requires accredited third parties.")
- Last-reviewed date and reviewer identity

---

## Frameworks in scope

Each framework gets its own matrix file under `docs/coverage/<framework-slug>.md`. Initial scope:

| Framework | Slug | Article/control count | Pilot priority |
|---|---|---|---|
| EU AI Act | `eu-ai-act` | ~113 articles + 13 annexes | **Pilot 1** |
| GDPR | `gdpr` | 99 articles | 2 |
| ISO 27001:2022 | `iso-27001` | 93 controls + 4 themes | 3 |
| NIST AI RMF | `nist-ai-rmf` | 4 Functions × ~70 Subcategories | 4 |
| NIST CSF 2.0 | `nist-csf` | 6 Functions × 106 Subcategories | 5 |
| SOC 2 | `soc2` | 5 TSCs × ~60-100 criteria | 6 |
| ISO 42001 | `iso-42001` | ~30 controls | 7 |
| OWASP LLM Top 10 | `owasp-llm` | ~10 risk categories | 8 |
| Colorado AI Act (SB 24-205) | `colorado-ai-act` | varies | 9 |
| NYC LL144 | `nyc-ll144` | varies | 10 |
| Singapore IMDA Agentic AI | `imda-agentic` | varies | 11 |
| G7 AI Code of Conduct | `g7-ai-code` | 11 principles | 12 |

The existing 5 mapping docs (`gdpr-mapping.md`, `iso27001-mapping.md`, `nist-csf-mapping.md`, `nist-rmf-mapping.md`, `soc2-mapping.md`) shipped on 2026-05-14 are **starter material** but do NOT satisfy this ADR: they map only a subset of each framework and need expansion to every control + explicit boundary rows for unmapped controls. The pilot matrix establishes the syntax that the existing docs then conform to.

---

## What this ADR does NOT change

- The internal rubric work (per-framework scoring, weighted aggregations, methodology reviews) continues as an internal tool for due-diligence packets, operator decisions, and quarterly improvement targeting. It does not appear on the public surface.
- The 5 mapping docs already shipped remain valid as starter material; they are not retracted, they are expanded.
- Third-party attestation engagements (CPA firm for SOC 2 Type II, accredited registrar for ISO 27001, etc.) remain separate from this work and are governed by their own decision processes.

---

## Consequences

**Positive:**
- Defensible to a knowledgeable buyer reading the matrix row-by-row alongside the source standard
- "Fulfills ALL applicable" survives scrutiny because applicability is enumerated, not hidden
- Boundary rows preempt the "but you don't implement X" objection by stating it first
- Internal rubric is preserved for DD packets where prospects ask for it specifically

**Negative / costs:**
- ~500-700 rows of authoring work across 12 frameworks
- Matrix must be kept current as standards evolve (annual recurring maintenance)
- Some boundary rows will require legal review (especially statutory penalty rows, EU institutional structure rows)
- Single contradicting row breaks any public coverage headline; rigor in row authoring is load-bearing

**Migration path:**
1. **Pilot**: build EU AI Act matrix as the template (this PR's companion artifact). Establishes row syntax, boundary-row patterns, evidence-artifact pointers.
2. **Expand**: backfill the 5 existing mapping docs to the full surface of each framework, conforming to ADR row syntax. (~6 weeks at 1-2 frameworks per week.)
3. **Public-surface integration**: replace residual "governance maturity" / "tier" language on hummbl.io with link to the matrix index. The compliance.json `public_claim_status` already moved `hold→retired` in hummbl-production#242.
4. **Marketing copy**: new headline claim is *"Every applicable control in [framework list] mapped to a HUMMBL primitive or explicit boundary statement. Read the matrix."* with a link.

---

## Open questions

- **Q1**: Authority for boundary-row classification (especially regulatory penalty rows). Default: operator review for first matrix; pattern-replicate after.
- **Q2**: Versioning policy for matrix updates as standards evolve. Default: matrix file versioned per HUMMBL release; standards-update sweep on every named-framework revision.
- **Q3**: Whether boundary rows for non-applicable controls (Out of scope ⛔) should be retained as evidence-of-completeness or removed for compactness. Default: retain so exclusions remain deliberate and reviewable.
- **Q4**: Translation of the matrix into hummbl.io UI (table, accordion, downloadable PDF, all three?). Defer to marketing surface work.

---

## References

- Methodology issue: [hummbl-governance#26](https://github.com/hummbl-io/hummbl-governance/issues/26)
- Memory rule: `feedback_no_self_grades_on_public_surface.md` (host-C)
- Compliance status retirement: [hummbl-production#242](https://github.com/hummbl-io/hummbl-production/pull/242)
- Original A+ rubric shipment: [hummbl-governance@6a47ca2](https://github.com/hummbl-io/hummbl-governance/commit/6a47ca2) + [hummbl-production@9d297b2](https://github.com/hummbl-io/hummbl-production/commit/9d297b2)
- Bus DECISION: 2026-05-14T~09:05Z `[lane=marketing/claude/no-self-grades]`
- Existing mapping docs: `docs/{gdpr,iso27001,nist-csf,nist-rmf,soc2}-mapping.md`
- Pilot artifact (companion to this ADR): `docs/coverage/eu-ai-act.md` (to be added in same PR)
