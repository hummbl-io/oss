# OECD AI Principles Coverage Matrix — HUMMBL

**Standard**: OECD Recommendation of the Council on Artificial Intelligence (OECD/LEGAL/0449), as amended May 2024
**Effective**: May 3, 2024 (2024 update; originally adopted May 22, 2019)
**Source**: https://oecd.ai/en/ai-principles
**Last reviewed**: 2026-06-25
**Reviewer**: claude-code (huxley) per [ADR-001](../adr/ADR-001-coverage-matrix-not-self-grade.md)
**HUMMBL version**: hummbl-governance v0.8.0

## Boundary disclaimer

The OECD AI Principles are a **non-binding** intergovernmental recommendation — the first IGO standard on AI. There is no certification body; adherence is self-declared by 47 jurisdictions. HUMMBL is not OECD-affiliated and does not provide conformance attestation. The Principles address both "AI actors" (organizations/individuals in the AI lifecycle) and governments (Section 2 recommendations). HUMMBL maps technical primitives to the Section 1 values-based principles directed at AI actors; Section 2 government recommendations are largely boundary (organizational/policy strategy).

## Scope summary

The Recommendation applies to all AI actors across the AI system lifecycle: "design, data and models," "verification and validation," "deployment," and "operation and monitoring." The 2024 update added explicit focus on generative AI, information integrity (misinformation/disinformation), uses outside intended purpose (intentional and unintentional misuse), safe override/repair/decommission by human interaction, responsible business conduct throughout the lifecycle, interoperable governance, and environmental sustainability. The OECD definition of an AI system and its lifecycle are adopted by the EU, Council of Europe, United States, and UN in their legislative/regulatory frameworks.

## Obligations + coverage

### Inclusive growth, sustainable development and well-being (Principle 1.1)

| Obligation | Coverage | Evidence |
|---|---|---|
| Proactively engage in responsible stewardship of trustworthy AI for beneficial outcomes — augmenting human capabilities, enhancing creativity | 🟡 Partial: governance substrate supports responsible stewardship; "beneficial outcomes" determination is org judgment | `hummbl_governance/audit_log.py`, `hummbl_governance/compliance_mapper.py` |
| Advance inclusion of underrepresented populations; reduce economic, social, gender and other inequalities | ⚪ Boundary: inclusion/inequality outcomes are org policy and societal, not software-addressable | |
| Protect natural environments; invigorate sustainable development (2024: explicit environmental sustainability reference) | 🟡 Partial: compute-cost tracking supports environmental-impact awareness; full sustainability program is org task | `hummbl_governance/cost_governor.py`, `hummbl_governance/audit_log.py` |

### Human rights and democratic values, including fairness and privacy (Principle 1.2)

| Obligation | Coverage | Evidence |
|---|---|---|
| Respect the rule of law, human rights and democratic values throughout the AI system lifecycle — freedom, dignity, autonomy | 🟡 Partial: lifecycle governance + authority engine enforce rule-based constraints; human-rights compliance determination is org legal task | `hummbl_governance/lifecycle.py`, `hummbl_governance/kernel/authority_engine.py`, `hummbl_governance/kernel/law_engine.py` |
| Privacy and data protection throughout the AI lifecycle | ✅ Privacy-risk tuple + data-protection controls (cross-ref GDPR matrix, NIST AI RMF MS-2.10) | `hummbl_governance/audit_log.py`, `hummbl_governance/schema_validator.py` |
| Non-discrimination and equality, diversity, fairness, social justice | 🟡 Partial: fairness-eval tuple type shipped; bias-mitigation methodology and diversity outcomes are org judgment (cross-ref NIST AI RMF MS-2.11) | `hummbl_governance/audit_log.py`, `hummbl_governance/compliance_mapper.py` |
| Implement mechanisms and safeguards, such as capacity for human determination, appropriate to context | ✅ Human-oversight delegation token + human-in-loop DCT + kill-switch override (cross-ref EU AI Act Art. 14, South Korea Art. 34) | `hummbl_governance/delegation.py`, `hummbl_governance/kill_switch.py`, `hummbl_governance/kernel/authority_engine.py` |
| Safeguard information integrity; address misinformation and disinformation in context of generative AI (2024 addition) | ✅ Output-validation gate + provenance-labeling tuple + content-authenticity controls (cross-ref EU AI Act Art. 50, South Korea Art. 31) | `hummbl_governance/output_validator.py`, `hummbl_governance/audit_log.py` |

### Transparency and explainability (Principle 1.3)

| Obligation | Coverage | Evidence |
|---|---|---|
| Provide meaningful information to foster general understanding of AI systems | ✅ Capability-disclosure generator + AI-system inventory tuple (cross-ref EU AI Act Art. 13, G7 Code principle 3) | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/audit_log.py` |
| Make stakeholders aware of their interactions with AI systems, including in the workplace | ✅ Transparency-notification primitive + interaction-logging (cross-ref EU AI Act Art. 50, South Korea Art. 31) | `hummbl_governance/audit_log.py`, `hummbl_governance/compliance_mapper.py` |
| Enable those affected by an AI system to understand the outcome | ✅ Explanation-disclosure generator + outcome-traceability tuple (cross-ref EU AI Act Art. 13, South Korea Art. 34) | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/audit_log.py` |
| Enable those adversely affected to challenge outcome based on plain, easy-to-understand information on factors and logic | ✅ Challenge-procedure tuple + explanation-disclosure with factor/logic fields (cross-ref EU AI Act Art. 86 right to explanation) | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/kernel/evidence_engine.py` |

### Robustness, security and safety (Principle 1.4)

| Obligation | Coverage | Evidence |
|---|---|---|
| AI systems robust, secure, safe throughout entire lifecycle — normal use, foreseeable use or misuse, adverse conditions | ✅ Kill-switch 4-mode halt + circuit-breaker fast-fail + capability-fence boundary enforcement (cross-ref NIST AI RMF MS-2.6/2.7, G7 Code principle 1) | `hummbl_governance/kill_switch.py`, `hummbl_governance/circuit_breaker.py`, `hummbl_governance/capability_fence.py` |
| Ensure traceability of datasets, processes, and decisions throughout AI lifecycle to enable analysis and inquiry | ✅ Immutable audit-log with full lifecycle traceability + receipt-engine provenance (cross-ref NIST AI RMF MS-2.8, G7 Code principle 2) | `hummbl_governance/audit_log.py`, `hummbl_governance/kernel/receipt_engine.py`, `hummbl_governance/kernel/sequence_engine.py` |
| Apply systematic risk management approach to each phase of lifecycle on continuous basis — privacy, digital security, safety, bias | ✅ Risk-mgmt program substrate: risk-identification + assessment + treatment tuples + continuous monitoring (cross-ref NIST AI RMF GOVERN/MAP/MEASURE/MANAGE, EU AI Act Art. 9) | `hummbl_governance/audit_log.py`, `hummbl_governance/coordination_bus.py`, `hummbl_governance/compliance_mapper.py` |
| Ensure AI systems can be overridden, repaired, and/or decommissioned safely by human interaction (2024 addition) | ✅ Kill-switch human-override modes + lifecycle decommission primitives + circuit-breaker safe-shutdown (cross-ref South Korea Art. 32) | `hummbl_governance/kill_switch.py`, `hummbl_governance/lifecycle.py`, `hummbl_governance/circuit_breaker.py` |
| Address uses outside intended purpose, intentional misuse, or unintentional misuse (2024 addition) | ✅ Capability-fence scope enforcement + output-validator misuse-detection + adverse-event monitoring (cross-ref G7 Code principle 2) | `hummbl_governance/capability_fence.py`, `hummbl_governance/output_validator.py`, `hummbl_governance/coordination_bus.py` |
| Responsible business conduct throughout lifecycle — cooperation with suppliers of AI knowledge and resources, users, stakeholders (2024 addition) | 🟡 Partial: supplier-DCT tuples + third-party-risk tracking; supplier-cooperation program is org task (cross-ref NIST AI RMF GV-6.1) | `hummbl_governance/delegation.py`, `hummbl_governance/audit_log.py` |

### Accountability (Principle 1.5)

| Obligation | Coverage | Evidence |
|---|---|---|
| AI actors accountable for proper functioning of AI systems based on roles, context, and state of art | ✅ Accountability-chain audit + delegation-token role binding + identity registry (cross-ref NIST AI RMF GV-2.1, EU AI Act Art. 14) | `hummbl_governance/audit_log.py`, `hummbl_governance/delegation.py`, `hummbl_governance/identity.py` |
| Accountability for respect of all principles (1.1–1.4) based on roles and context | ✅ Compliance-mapper crosswalk + authority-engine rule enforcement + receipt-engine attestation | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/kernel/authority_engine.py`, `hummbl_governance/kernel/receipt_engine.py` |
| Evidence-based accountability — auditable records of decisions, actions, and oversight throughout lifecycle | ✅ Immutable audit-log + Lamport-clock ordering + receipt-engine signed attestations | `hummbl_governance/audit_log.py`, `hummbl_governance/lamport_clock.py`, `hummbl_governance/kernel/receipt_engine.py` |

### Recommendations for policymakers (Section 2 — Principles 2.1–2.5)

| Obligation | Coverage | Evidence |
|---|---|---|
| Invest in R&D for trustworthy AI; encourage open, representative, privacy-respecting datasets (2.1) | ⚪ Boundary: government R&D investment and open-data policy are organizational/national strategy | |
| Foster an inclusive AI-enabling ecosystem — digital technologies, infrastructure, AI-knowledge sharing (2.2) | ⚪ Boundary: ecosystem-building is government policy | |
| Shape an enabling, interoperable governance and policy environment for AI (2.3, 2024: interoperability emphasis) | 🟡 Partial: compliance-mapper crosswalks support interoperability across frameworks (NIST, ISO, EU AI Act, SOC 2); policy environment is government task | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/stride_mapper.py` |
| Build human capacity and prepare for labour market transformation — skills, training, fair transition (2.4) | ⚪ Boundary: workforce development and labour-market policy are organizational/government | |
| International co-operation for trustworthy AI — share AI knowledge, develop global technical standards, comparable metrics (2.5) | 🟡 Partial: this coverage-matrix index + crosswalks contribute to interoperable governance; standards participation and metrics development are org/government | `hummbl_governance/compliance_mapper.py` |

## Summary

| Section | Obligations | ✅ | 🟡 | ⚪ |
|---|---:|---:|---:|---:|
| Inclusive growth, sustainable development and well-being (1.1) | 3 | 0 | 2 | 1 |
| Human rights and democratic values, including fairness and privacy (1.2) | 5 | 3 | 2 | 0 |
| Transparency and explainability (1.3) | 4 | 4 | 0 | 0 |
| Robustness, security and safety (1.4) | 6 | 5 | 1 | 0 |
| Accountability (1.5) | 3 | 3 | 0 | 0 |
| Recommendations for policymakers (2.1–2.5) | 5 | 0 | 2 | 3 |
| **Totals** | **26** | **15** | **7** | **4** |

---

## Draft coverage summary (not public claim)

This matrix is internal starter material. It must not be used as public evidence that HUMMBL fulfills this framework until row counts, evidence commands, artifact paths, and boundary classifications are validated.

The OECD AI Principles are non-binding; coverage here indicates primitive-level support for AI-actor obligations, not conformance attestation. Section 2 (government recommendations) is largely boundary — HUMMBL's compliance-mapper crosswalks contribute to interoperability (Principle 2.3, 2.5) but do not constitute national policy implementation.

## Cross-references

- ADR: [`docs/adr/ADR-001-coverage-matrix-not-self-grade.md`](../adr/ADR-001-coverage-matrix-not-self-grade.md)
- Transparency/explainability overlaps EU AI Act Art. 13/50 — see [`eu-ai-act.md`](./eu-ai-act.md)
- Risk management overlaps NIST AI RMF (all functions) — see [`nist-ai-rmf.md`](./nist-ai-rmf.md)
- Human oversight overlaps EU AI Act Art. 14, South Korea AI Basic Act Art. 34 — see [`eu-ai-act.md`](./eu-ai-act.md), [`south-korea-ai-basic-act.md`](./south-korea-ai-basic-act.md)
- Information integrity / provenance overlaps G7 Code principle 7 — see [`g7-ai-code.md`](./g7-ai-code.md)
- Robustness/safety overlaps G7 Code principles 1–2, NIST AI RMF MS-2.6/2.7 — see [`g7-ai-code.md`](./g7-ai-code.md), [`nist-ai-rmf.md`](./nist-ai-rmf.md)
- Privacy overlaps GDPR — see [`gdpr.md`](./gdpr.md)
- Accountability overlaps NIST AI RMF GOVERN 2, ISO 42001 — see [`nist-ai-rmf.md`](./nist-ai-rmf.md), [`iso-42001.md`](./iso-42001.md)
