# NISTIR 8605 COSAiS Watch Matrix — HUMMBL

**Series**: NIST Interagency Reports — Control Overlays for Securing AI Systems (COSAiS)
**Project**: https://csrc.nist.gov/projects/cosais
**Status on this review (2026-08-31)**: **watch only**. The series is targeted to **finalize in 2027** (Jan 2026 annotated outline, “Proposed Deliverables and Timeline”). **No overlay control IDs yet.**
**Last reviewed**: 2026-08-31
**Reviewer**: documentation pass per [ADR-001](../adr/ADR-001-coverage-matrix-not-self-grade.md) and LANDING-013
**HUMMBL version mapped against**: hummbl-governance v1.4.2 (`pyproject.toml` on this tree)

## Boundary disclaimer (watch, not a mapping)

This file exists so the COSAiS / NISTIR 8605 series is **not silent**. It is **not** an SP 800-53 overlay, **not** a FedRAMP baseline, and **not** a DoD AI overlay.

The Jan 2026 annotated outline (discussion draft for Cyber AI Profile Workshop #2, 14 January 2026) is explicit: the summary table is “populated with only a subset of **example** controls for the annotated outline” and “the list of controls identified for potential inclusion in this overlay is **not complete**.”

**Do not promote AC-2 examples — or any other 800-53 IDs from that outline — to Fulfilled overlay IDs.** Those strings (the structure example is **AC-06 Least Privilege**; additional illustrations include AC-03, AC-22, AU-02, CM-02, RA-05, …) are discussion-draft examples. They are not selected overlay controls. This matrix does not copy them into a control table.

**No separate FedRAMP or DoD AI overlay exists outside this series** as a public NISTIR 8605-family deliverable on this review. Do not invent one.

**No public “fulfills NISTIR 8605 / COSAiS.”** No row in this file is ✅.

## Completeness

Completeness for this watch matrix = **document-level rows** for the five volumes named in the Jan 2026 outline, plus programme rows that record: watch-only status, 2027 finalization target, “no overlay IDs yet,” the AC-2 / outline-example ban, and the FedRAMP/DoD non-existence statement.

Sources opened this session:

- https://csrc.nist.gov/projects/cosais (project page; last NIST update shown 8 January 2026)
- https://csrc.nist.gov/csrc/media/Projects/cosais/documents/COSAiS-Predictive-AI-annotated-outline-Jan2026.pdf (annotated outline for NISTIR 8605 + 8605A)

Volume titles below are copied from that outline’s “Proposed Deliverables and Timeline.” Later slide decks shorten 8605D to “Controls for Securing Agentic AI Systems”; this file keeps the outline title.

## Coverage state legend

| Glyph | State | Meaning |
|---|---|---|
| ✅ | Fulfilled | Named HUMMBL primitive implements the control; evidence artifact must be validated before public use |
| 🟡 | Partial | HUMMBL primitive provides part; a published overlay ID would complete it. Both parts named. |
| ⚪ | Boundary | Watch / unpublished / organizational. No overlay ID to map. |
| ⛔ | Out of scope | Control does not apply to the AI governance platform context (retained for completeness). |

## Programme-boundary rows

| ID | Public statement | HUMMBL coverage | Evidence |
|---|---|---|---|
| COSAiS watch | SP 800-53 Control Overlays for Securing AI Systems — project will develop a series of overlays using SP 800-53 (also leveraging SP 800-218A, Draft NIST AI 800-1, NIST AI 100-2e2025) | ⚪ Boundary: watch only. HUMMBL is not a COSAiS overlay author. | n/a — boundary; https://csrc.nist.gov/projects/cosais |
| Finalize 2027 | Outline: issue 8605 + 8605A drafts by Q3 FY2026; further volume drafts through 2026–2027; **series (all volumes) finalized in 2027**, pending resources | ⚪ Boundary: publication schedule. Not a HUMMBL milestone. | n/a — boundary |
| No overlay control IDs yet | Overlays (Volumes A–D) will be in the publications and in CPRT **when finalized**. No initial public draft of 8605/8605A was on the project page as of this review | ⚪ Boundary: nothing to map at control grain. | n/a — boundary |
| Jan 2026 outline examples (not Fulfilled) | Outline examples include AC-06 (structure), plus AC-03, AC-22, AU-02, and others. **Do not promote AC-2 or any outline example to a Fulfilled overlay ID** | ⚪ Boundary: examples only. This row exists so those IDs cannot be silently treated as selected COSAiS controls. | n/a — boundary; outline PDF |
| No FedRAMP / DoD AI overlay outside this series | No separate public FedRAMP AI overlay or DoD AI 800-53 overlay was found as a COSAiS sibling on this review | ⚪ Boundary: do not invent FedRAMP-AI or DoD-AI overlay IDs here. CMMC stays in [`cmmc-2.md`](./cmmc-2.md) (domain grain only). | n/a — boundary |

## Document-level volume rows

| ID | Title (Jan 2026 outline) | HUMMBL coverage | Evidence |
|---|---|---|---|
| NISTIR 8605 | Control Overlays for Securing AI Systems: Overview and Methodology | ⚪ Boundary: methodology volume not published as IPD on this review. No methodology clauses mapped. | n/a — boundary |
| NISTIR 8605A | Control Overlays for Securing AI Systems: Using and Fine-Tuning Predictive AI | ⚪ Boundary: predictive-AI overlay. Annotated outline only. Example 800-53 IDs in that outline are not rows. | n/a — boundary |
| NISTIR 8605B | Control Overlays for Securing AI Systems: Adapting and Using Generative AI | ⚪ Boundary: generative-AI overlay not issued as IPD. COSAiS concept-paper use case “Adapting and Using Generative AI – Assistant/LLM” is not an ID list. | n/a — boundary |
| NISTIR 8605C | Control Overlays for Securing AI Systems: Security Controls for AI Developers | ⚪ Boundary: developer-control overlay not issued as IPD. | n/a — boundary |
| NISTIR 8605D | Control Overlays for Securing AI Systems: Using Agentic AI: Single Agent and Multi-Agent | ⚪ Boundary: **watch**. HUMMBL ships agentic governors (`kill_switch`, `circuit_breaker`, `delegation`, `identity`). That does not map to 8605D overlay IDs because **none are published**. Do not treat agentic primitives as COSAiS Fulfilled. | `hummbl_governance/kill_switch.py`, `hummbl_governance/circuit_breaker.py`, `hummbl_governance/delegation.py`, `hummbl_governance/identity.py` (existence only; not overlay evidence) |

## Surfaces named so they are not silent (not extra completeness rows)

- **ISO/IEC 42003 (AWI)**: AIMS guidance work item reported in public ISO catalogues; **no public text confirmed this session**. Not a file in this PR. **Do not invent ISO 42004** (no public 42004 found; see [`iso-42006.md`](./iso-42006.md)).
- **Google SAIF, Microsoft RAI v2, AWS service cards**: vendor programme / service documentation. **Not** added as control matrices (operator instruction).
- Concept-paper use cases (single-agent, multi-agent, developer controls) are absorbed into the volume rows above; they are not a second ID set.

## Summary

| Section | Rows | ✅ | 🟡 | ⚪ | ⛔ |
|---|---:|---:|---:|---:|---:|
| Programme-boundary | 5 | 0 | 0 | 5 | 0 |
| Document-level volumes | 5 | 0 | 0 | 5 | 0 |
| **Totals** | **10** | **0** | **0** | **10** | **0** |

## Draft coverage summary (not public claim)

This matrix is internal starter material. It must not be used as public evidence that HUMMBL fulfills COSAiS, NISTIR 8605A–D, FedRAMP AI, or a DoD AI overlay. Existing coverage matrices last reviewed 2026-05-14 / v0.8.0 are not upgraded by this file.

## Cross-references

- ADR: [`docs/adr/ADR-001-coverage-matrix-not-self-grade.md`](../adr/ADR-001-coverage-matrix-not-self-grade.md)
- NIST CSF 2.0 (different instrument; last reviewed 2026-05-14 / v0.8.0): [`nist-csf.md`](./nist-csf.md)
- NIST AI RMF 1.0 (different instrument; last reviewed 2026-05-14 / v0.8.0): [`nist-ai-rmf.md`](./nist-ai-rmf.md)
- CMMC 2.0 domain watch (not a COSAiS overlay): [`cmmc-2.md`](./cmmc-2.md)
- Project: https://csrc.nist.gov/projects/cosais
