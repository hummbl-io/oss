# HAW-2026-001 — Retinal Neurodevelopmental Screening AI

**Case study ID**: HAW-2026-001
**Category**: Ophthalmic AI — neurodevelopmental screening
**Status**: Filed 2026-07-03
**Priority**: P2 — coverage scaffold due 2026-07-17
**Coverage matrix**: [`docs/coverage/ophthalmic-ai.md`](../../coverage/ophthalmic-ai.md)

---

## Summary

RetinaMind (developed by Edward Kang, 2026 Regeneron Science Talent Search finalist) is a retinal fundus imaging AI system that screens for autism spectrum disorder (ASD) and attention-deficit/hyperactivity disorder (ADHD) from the vascular and structural patterns in retinal photographs. The tool represents an emerging class of ophthalmic AI that generates neurodevelopmental inferences from ophthalmological images — a domain that does not fit cleanly into existing general-purpose medical AI governance frameworks.

This case study documents the regulatory trigger set, evidence chain, and governance gaps surfaced by this tool's regulatory trajectory.

---

## Technology

| Field | Detail |
|---|---|
| Tool | RetinaMind |
| Developer | Edward Kang (2026 Regeneron STS finalist) |
| Modality | Retinal fundus imaging (color fundus photography) |
| Claimed output | ASD / ADHD screening score from retinal morphology |
| Inference domain | Neurodevelopmental — ophthalmological proxy biomarker |
| Target population | Pediatric and adolescent patients |

---

## Evidence chain

| Citation | Year | Journal | Key finding | Governance relevance |
|---|---|---|---|---|
| Lai et al. | 2020 | eClinicalMedicine | Retinal microvascular changes associated with ASD | Foundational biomarker hypothesis |
| Kim et al. | 2023 | JAMA Network Open | Retinal structural differences in ADHD cohort | Extends hypothesis to ADHD domain |
| Choi et al. | 2025 | npj Digital Medicine | AI model trained on retinal images predicts ASD/ADHD | Direct precedent for AI-based screening |

### Critical limitation: single-dataset validation

All three studies use the Korean AIHub dataset (`dataSetSn=71516`). No external validation on non-Korean cohorts has been published. This creates:

- **Ethnic generalizability gap** — retinal vascular morphology has known population-stratified variation; a model trained and validated on a single Korean dataset may not generalize.
- **Geographic/environmental confounders** — Korean pediatric cohort may have correlated lifestyle, dietary, and environmental exposures not present in other populations.
- **No independent replication** — all evidence is from the same data source; independent replication from a different dataset is absent.

This is a P1 governance gap for any deployment outside the Korean pediatric population demographic.

---

## Regulatory trigger set

### EU AI Act (effective Aug 2, 2026)

| Provision | Trigger |
|---|---|
| Annex III §1(b) | AI system as safety component in medical device OR AI system that is itself a medical device — retinal screening AI classifies as medical device AI |
| Art. 9 | Risk management system required for all Annex III high-risk systems |
| Art. 10 | Data governance — training data must be representative, free from errors, complete |
| Art. 13 | Transparency — deployers must be informed of intended purpose, accuracy, limitations |
| Art. 14 | Human oversight — measures to enable human override |
| Art. 15 | Accuracy, robustness, cybersecurity requirements |

The Aug 2, 2026 effective date for Annex III high-risk AI provisions means any deployment on EU patients after that date triggers full conformity assessment obligations.

**Single-dataset gap vs. Art. 10**: EU AI Act Art. 10(3) requires training data to be "relevant, sufficiently representative" and "free of errors." A model with no external validation dataset falls short of Art. 10(3) representativeness requirement for EU deployment.

### FDA SaMD (Software as a Medical Device)

| Pathway | Applicability |
|---|---|
| De Novo (21 CFR Part 515B) | Novel device type — retinal AI for neurodevelopmental screening has no predicate; De Novo classification required |
| Predetermined Change Control Plan (PCCP) | Required for AI/ML-based SaMD that undergoes planned model updates |
| 21 CFR Part 820 (QSR) | Quality system requirements |
| Clinical validation | FDA guidance requires clinical validation data from target population |

The FDA 2021 AI/ML-based SaMD Action Plan and 2023 Marketing Submission Recommendations require multi-site clinical validation — the single Korean dataset does not satisfy these requirements.

### HIPAA

| Provision | Trigger |
|---|---|
| Privacy Rule | Retinal images are PHI when linked to patient identity; de-identification per Safe Harbor or Expert Determination required for training |
| Security Rule | Electronic PHI safeguards for stored/transmitted retinal images |
| Minimum Necessary | Access to retinal images limited to minimum necessary for stated purpose |

### ONC HTI-1 (45 CFR Part 170)

| Provision | Trigger |
|---|---|
| Certification criterion § 170.315(b)(11) | Predictive decision support interventions must provide source attributes, development methods, and performance metrics |
| Transparency requirements | ONC HTI-1 requires clinical decision support software to disclose training data populations |

---

## Governance gaps surfaced

1. **No ophthalmic-AI-specific coverage category** — the retinal → neurodevelopmental inference domain does not fit existing framework coverage rows (general medical AI, diagnostic imaging AI, or mental health AI). See coverage matrix: [`docs/coverage/ophthalmic-ai.md`](../../coverage/ophthalmic-ai.md).

2. **Single-dataset validation against EU AI Act Art. 10** — no multi-dataset or external validation published; Art. 10(3) representativeness requirement unsatisfied for EU deployment.

3. **Cross-population generalizability** — all evidence from Korean pediatric cohort; no validation on South Asian, African, Hispanic, or European pediatric populations.

4. **Pediatric vulnerability classification** — target population includes children; EU AI Act Art. 9(2)(b) and FDA pediatric device provisions impose heightened obligations for pediatric-targeted AI.

5. **Ophthalmologist-in-the-loop gap** — retinal imaging for neurodevelopmental screening ordinarily requires ophthalmologist and developmental pediatrician collaboration; AI screening that bypasses this pathway raises Art. 14 human oversight concerns.

---

## Related artifacts

- Coverage matrix: [`docs/coverage/ophthalmic-ai.md`](../../coverage/ophthalmic-ai.md)
- EU AI Act coverage: [`docs/coverage/eu-ai-act.md`](../../coverage/eu-ai-act.md)
- NIST AI RMF coverage: [`docs/coverage/nist-ai-rmf.md`](../../coverage/nist-ai-rmf.md)
- ISO 42001 coverage: [`docs/coverage/iso-42001.md`](../../coverage/iso-42001.md)

---

*Filed under hummbl-governance issue #185. Coverage skeleton due 2026-07-17.*
