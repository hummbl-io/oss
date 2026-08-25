# ISO/IEC 42005:2025 Coverage Matrix — HUMMBL

**Standard**: ISO/IEC 42005:2025 — Information technology — Artificial intelligence — AI system impact assessment
**Effective**: May 2025
**Source**: https://www.iso.org/standard/42005
**Last reviewed**: 2026-06-25
**Reviewer**: claude-code (huxley) per [ADR-001](../adr/ADR-001-coverage-matrix-not-self-grade.md)
**HUMMBL version**: hummbl-governance v0.8.0

## Boundary disclaimer

HUMMBL is not an ISO 42005 conformity assessor and does not conduct AI system impact assessments (AIIAs) on behalf of customer organizations. ISO/IEC 42005 is a **guidance standard** (Type 2 guidance, not certifiable) that helps organizations perform structured impact assessments of AI systems on individuals, groups, and society. The assessment process, stakeholder consultation, severity/likelihood judgments, and management approval decisions are the customer-organization responsibility. HUMMBL maps technical primitives to the standard's process-design, documentation, impact-identification, mitigation, and monitoring obligations.

## Scope summary

ISO/IEC 42005:2025 applies to any organization developing, providing, or using AI systems — regardless of sector or size — that wants to assess and manage the potential impacts of their AI systems on people and society. The standard covers the full AI system lifecycle (design, development, deployment, post-market monitoring) and addresses both intended and unintended (reasonably foreseeable) consequences. It complements ISO/IEC 42001 (AI management systems), ISO/IEC 23894 (AI risk management), and ISO/IEC 38507 (AI governance) by focusing specifically on societal and human impacts. Key structure: Clause 5 (assessment process), Clause 6 (assessment documentation), Annex A (42001 integration), Annex B (23894 integration), Annex C (harms and benefits taxonomy), Annex D (alignment with other assessments), Annex E (example template).

## Obligations + coverage

### Assessment process design (Clause 5.1–5.7)

| Obligation | Coverage | Evidence |
|---|---|---|
| 5.1 Establish a structured, consistent AIIA process tailored to organizational context (internal and external factors) | ✅ Impact-assessment process template + context-factor tuples (cross-ref ISO 42001 Cl. 4 context, NIST AI RMF GOVERN) | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/audit_log.py` |
| 5.2 Document the AIIA process including methodology, roles, inputs, outputs, and decision-making workflow | ✅ Process-documentation tuple types + immutable audit-log retention | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/audit_log.py` |
| 5.3 Integrate AIIA with existing organizational governance, risk management, and compliance processes | ✅ Cross-framework compliance mapping (cross-ref ISO 42001 Cl. 6 planning, ISO 23894 risk treatment) | `hummbl_governance/compliance_mapper.py` |
| 5.4 Define timing of assessments — at design, pre-deployment, and after major system changes | ✅ Lifecycle-stage gating + post-change re-assessment triggers | `hummbl_governance/lifecycle.py`, `hummbl_governance/health_probe.py` |
| 5.5 Define scope of each AIIA — which AI systems, components, uses, and stakeholders are covered | ✅ Scope-definition tuple + stakeholder-registration tuples | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/identity.py` |
| 5.6 Allocate responsibilities for performing, reviewing, and approving assessments across multidisciplinary teams | ✅ Delegation-token assignment + role-based accountability registry (cross-ref ISO 42001 Cl. 5.3 roles) | `hummbl_governance/delegation.py`, `hummbl_governance/identity.py` |
| 5.7 Establish thresholds for sensitive uses, restricted uses, and impact scales that trigger in-depth assessment | 🟡 Partial: capability-fence + compliance-mapper define technical thresholds and classification tuples; organizational sensitivity classification and risk-appetite decisions are org task | `hummbl_governance/capability_fence.py`, `hummbl_governance/compliance_mapper.py` |

### Performing and analysing the assessment (Clause 5.8–5.9)

| Obligation | Coverage | Evidence |
|---|---|---|
| 5.8 Perform assessment systematically — identify impacts, potential harms, and benefits across dimensions (human rights, safety, security, fairness, autonomy, socioeconomic well-being) | ✅ Impact-identification tuples + STRIDE-based threat/impact mapping (cross-ref Annex C harms and benefits taxonomy, NIST AI RMF MEASURE) | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/stride_mapper.py` |
| 5.9 Analyse results — evaluate severity and likelihood of identified impacts, considering vulnerability of affected parties and reversibility of harm | ✅ Severity/likelihood scoring tuples + STRIDE risk-rating engine | `hummbl_governance/stride_mapper.py`, `hummbl_governance/compliance_mapper.py` |

### Recording, approval, and monitoring (Clause 5.10–5.12)

| Obligation | Coverage | Evidence |
|---|---|---|
| 5.10 Record and report findings, mitigation measures, and approvals for transparency and audit readiness | ✅ Immutable audit-log records + compliance-report generator (cross-ref ISO 42001 Cl. 7.5 documented information) | `hummbl_governance/audit_log.py`, `hummbl_governance/compliance_mapper.py` |
| 5.11 Define approval workflows and authority levels for impact assessment outcomes | ✅ Authority-engine approval gates + doctrine-engine policy enforcement (cross-ref ISO 42001 Cl. 5.1 leadership commitment) | `hummbl_governance/kernel/authority_engine.py`, `hummbl_governance/kernel/doctrine_engine.py` |
| 5.12 Implement ongoing monitoring and periodic review to keep assessments current as AI systems or context evolve | ✅ Health-probe continuous monitoring + lifecycle re-assessment triggers + audit-log change tracking (cross-ref ISO 42001 Cl. 9 performance evaluation) | `hummbl_governance/health_probe.py`, `hummbl_governance/lifecycle.py`, `hummbl_governance/audit_log.py` |

### Assessment documentation content (Clause 6.2–6.6)

| Obligation | Coverage | Evidence |
|---|---|---|
| 6.2 Document the scope of the AI system impact assessment | ✅ Scope-documentation tuple + audit-log record | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/audit_log.py` |
| 6.3 Document AI system information — description, functionalities, capabilities, purpose, intended uses, and unintended (reasonably foreseeable) uses | ✅ System-description tuple types + intended/unintended-use classification (cross-ref ISO 23894 Cl. 6 risk sources) | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/audit_log.py` |
| 6.4 Document data information and quality — sources, quality characteristics, and data documentation | ✅ Schema-validation records + data-quality documentation tuples | `hummbl_governance/schema_validator.py`, `hummbl_governance/audit_log.py` |
| 6.5 Document algorithm and model information — algorithms used, development history, model versioning | ✅ Reasoning-trace records + audit-log model/version lineage | `hummbl_governance/reasoning.py`, `hummbl_governance/audit_log.py` |
| 6.6 Document deployment environment — geographical area, languages, complexity, and operational constraints | 🟡 Partial: capability-fence + physical-governor capture technical deployment constraints; geographic/language scoping and operational-context documentation is org task | `hummbl_governance/capability_fence.py`, `hummbl_governance/physical_governor.py` |

### Impacts, stakeholders, and mitigation (Clause 6.7–6.9)

| Obligation | Coverage | Evidence |
|---|---|---|
| 6.7 Identify relevant interested parties — directly and indirectly affected stakeholders | ✅ Stakeholder-registration tuples + identity-registry records (cross-ref ISO 42001 Cl. 4.2 interested parties) | `hummbl_governance/identity.py`, `hummbl_governance/delegation.py` |
| Consult representatives of affected groups during the assessment process to ground impact identification in real-world experience | ⚪ Boundary: multi-stakeholder consultation with affected communities is organizational, not software-addressable | |
| 6.8 Document actual and reasonably foreseeable impacts — harms, benefits, and potential misuse scenarios | ✅ Impact-documentation tuples + STRIDE threat modeling + foreseeable-misuse classification (cross-ref Annex C taxonomy) | `hummbl_governance/stride_mapper.py`, `hummbl_governance/compliance_mapper.py` |
| 6.9 Record measures to address harms and maximize benefits — mitigation actions, design changes, and enhancement plans | ✅ Mitigation-measure tuples + safety-control enforcement (kill-switch, circuit-breaker, output-validator, capability-fence) (cross-ref ISO 23894 Cl. 8 risk treatment) | `hummbl_governance/kill_switch.py`, `hummbl_governance/circuit_breaker.py`, `hummbl_governance/output_validator.py`, `hummbl_governance/capability_fence.py` |

### Integration and alignment (Annexes A–D)

| Obligation | Coverage | Evidence |
|---|---|---|
| Annex A: Integrate AIIA process with ISO/IEC 42001 AI management system to avoid duplication | ✅ ISO crosswalk mapping + shared evidence substrate (cross-ref [`docs/coverage/iso-42001.md`](./iso-42001.md)) | `hummbl_governance/compliance_mapper.py` |
| Annex B: Align AIIA with ISO/IEC 23894 AI risk management lifecycle | ✅ Cross-framework risk mapping + STRIDE-to-risk-treatment bridge (cross-ref [`docs/coverage/iso-iec-23894.md`](./iso-iec-23894.md)) | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/stride_mapper.py` |
| Annex C: Apply Harms and Benefits Taxonomy to systematically categorize identified impacts | ✅ STRIDE threat categories + impact-classification tuples covering bias, privacy, safety, security, economic, and benefit dimensions | `hummbl_governance/stride_mapper.py`, `hummbl_governance/compliance_mapper.py` |
| Annex D: Align AIIA with other organizational assessments (privacy/DPIA, ethics, environmental) | 🟡 Partial: compliance-mapper supports cross-framework mapping and shared evidence; scheduling combined assessments and inter-team coordination is org task | `hummbl_governance/compliance_mapper.py` |

## Summary

| Section | Obligations | ✅ | 🟡 | ⚪ |
|---|---:|---:|---:|---:|
| Assessment process design (Cl. 5.1–5.7) | 7 | 6 | 1 | 0 |
| Performing and analysing (Cl. 5.8–5.9) | 2 | 2 | 0 | 0 |
| Recording, approval, monitoring (Cl. 5.10–5.12) | 3 | 3 | 0 | 0 |
| Assessment documentation content (Cl. 6.2–6.6) | 5 | 4 | 1 | 0 |
| Impacts, stakeholders, mitigation (Cl. 6.7–6.9) | 4 | 3 | 0 | 1 |
| Integration and alignment (Annexes A–D) | 4 | 3 | 1 | 0 |
| **Totals** | **25** | **21** | **3** | **1** |

---

## Draft coverage summary (not public claim)

This matrix is internal starter material. It must not be used as public evidence that HUMMBL fulfills this framework until row counts, evidence commands, artifact paths, and boundary classifications are validated.

## Cross-references

- ADR: [`docs/adr/ADR-001-coverage-matrix-not-self-grade.md`](../adr/ADR-001-coverage-matrix-not-self-grade.md)
- AIIA process integration overlaps ISO/IEC 42001 AIMS — see [`iso-42001.md`](./iso-42001.md)
- Risk management alignment overlaps ISO/IEC 23894 — see [`iso-iec-23894.md`](./iso-iec-23894.md)
- Impact assessment overlaps EU AI Act Art. 27 (FRIA) — see [`eu-ai-act.md`](./eu-ai-act.md)
- Impact assessment overlaps South Korea AI Basic Act Art. 35 — see [`south-korea-ai-basic-act.md`](./south-korea-ai-basic-act.md)
- Harms and benefits taxonomy overlaps NIST AI RMF MEASURE — see [`nist-ai-rmf.md`](./nist-ai-rmf.md)
- Threat/impact modeling overlaps STRIDE — see [`stride.md`](./stride.md)
