# ASEAN Guide on AI Governance and Ethics Coverage Matrix — HUMMBL

**Standard**: ASEAN Guide on AI Governance and Ethics (ASEAN Secretariat, endorsed by the 4th ASEAN Digital Ministers' Meeting, 2 February 2024)
**Effective**: February 2024 (voluntary regional guidance)
**Source**: https://asean.org/wp-content/uploads/2024/02/ASEAN-Guide-on-AI-Governance-and-Ethics_beautified_201223_v2.pdf
**Last reviewed**: 2026-06-25
**Reviewer**: claude-code (huxley) per [ADR-001](../adr/ADR-001-coverage-matrix-not-self-grade.md)
**HUMMBL version**: hummbl-governance v0.8.0

## Boundary disclaimer

HUMMBL is not ASEAN legal counsel and does not provide legal advice on the ASEAN Guide on AI Governance and Ethics. The Guide is voluntary, non-binding regional guidance endorsed by the ASEAN Digital Ministers — it is not statute. It provides practical best-practice recommendations for organisations designing, developing, and deploying traditional (non-generative) AI in commercial, non-military, non-dual-use applications across the 10 ASEAN Member States. Statutory compliance with each member state's domestic law remains a customer-organisation responsibility. HUMMBL maps technical primitives to the Guide's seven guiding principles, four-area governance framework, and national/regional recommendations.

## Scope summary

The Guide applies to organisations operating in ASEAN that design, develop, or deploy traditional AI technologies for commercial and non-military/non-dual-use applications. It is structured across four areas: (A) seven guiding principles for trustworthy AI, (B) four key implementation areas for organisations — internal governance structures, human involvement in AI-augmented decision-making, operations management, and stakeholder interaction and communication, (C) national-level recommendations for policymakers, and (D) regional-level recommendations for policymakers. The Guide is principle-driven, risk-based, and light-touch, reflecting the diversity of digital-development stages across ASEAN Member States. It builds directly on Singapore's Model AI Governance Framework and aims to foster interoperability of AI frameworks across jurisdictions. An expanded Generative AI edition (January 2025) extends the Guide to Gen AI but is out of scope for this matrix.

## Obligations + coverage

### Guiding principles (§B)

| Obligation | Coverage | Evidence |
|---|---|---|
| Transparency and Explainability — disclose AI usage to stakeholders and provide understandable explanations of how AI reaches outcomes | ✅ Transparency-notification primitive + explanation-disclosure generator (cross-ref Singapore Model Framework §D, EU AI Act Art. 50) | `hummbl_governance/output_validator.py`, `hummbl_governance/compliance_mapper.py` |
| Fairness and Equity — ensure algorithmic decisions do not create discriminatory or unjust impacts; rectify imbalances to ensure equity | ✅ Output-validator bias-detection gate + reasoning-engine fairness checks (cross-ref NIST AI RMF MEASURE) | `hummbl_governance/output_validator.py`, `hummbl_governance/reasoning.py` |
| Security and Safety — adopt risk-prevention approach; precautions so humans can intervene to prevent harm from unsafe AI decisions | ✅ Kill-switch 4-mode halt + circuit-breaker fast-fail + capability-fence isolation | `hummbl_governance/kill_switch.py`, `hummbl_governance/circuit_breaker.py`, `hummbl_governance/capability_fence.py` |
| Human-centricity — respect human-centered values throughout AI lifecycle; protect human rights, freedom, and well-being | ✅ Human-oversight delegation token + lifecycle human-in-the-loop checkpoints (cross-ref Singapore Model Framework §B, EU AI Act Art. 14) | `hummbl_governance/delegation.py`, `hummbl_governance/lifecycle.py` |
| Privacy and Data Governance — mechanisms for data privacy/protection and data quality/integrity across lifecycle; data-access protocols | ✅ Identity-registry access control + audit-log data-lineage tuples + schema-validator integrity checks (cross-ref GDPR, India DPDP) | `hummbl_governance/identity.py`, `hummbl_governance/audit_log.py`, `hummbl_governance/schema_validator.py` |
| Accountability and Integrity — AI actors accountable for AI-system decisions and compliance with laws and ethics; act with integrity | ✅ Receipt-engine accountability tuples + authority-engine role binding + immutable audit trail | `hummbl_governance/kernel/receipt_engine.py`, `hummbl_governance/kernel/authority_engine.py`, `hummbl_governance/audit_log.py` |
| Robustness and Reliability — consistent performance as designed; reproducible results; resist tampering and compromise | ✅ Health-probe monitoring + convergence-guard stability checks + output-validator reproducibility gate | `hummbl_governance/health_probe.py`, `hummbl_governance/convergence_guard.py`, `hummbl_governance/output_validator.py` |

### Internal governance structures and measures (§C.1)

| Obligation | Coverage | Evidence |
|---|---|---|
| Establish multi-disciplinary central governing body (e.g. AI Ethics Advisory Board) to oversee AI governance efforts, representative of diverse stakeholders, disciplines, and geographies | ✅ Coordination-bus topic registration + multi-agent message routing (cross-ref Singapore Model Framework §A) | `hummbl_governance/coordination_bus.py` |
| Define clear roles and responsibilities for personnel responsible for AI design, development, and deployment | ✅ Delegation-token issuance + identity-registry role assignment | `hummbl_governance/delegation.py`, `hummbl_governance/identity.py` |
| Align AI governance with business strategy, risk appetite, and corporate values | 🟡 Partial: doctrine-engine captures governance doctrine; strategic alignment is org task | `hummbl_governance/kernel/doctrine_engine.py` |
| Ensure staff are trained and aware of AI ethics responsibilities and applicable laws | 🟡 Partial: lifecycle onboarding tracks training state; curriculum delivery is org task | `hummbl_governance/lifecycle.py` |

### Human involvement in AI-augmented decision-making (§C.2)

| Obligation | Coverage | Evidence |
|---|---|---|
| Conduct risk impact assessments to determine the level of risk and appropriate human involvement | ✅ Risk-assessment template + risk-tiering tuples (cross-ref Singapore Model Framework §B, NIST AI RMF ASSESS) | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/audit_log.py` |
| Human-in-the-loop oversight for high-risk and human-over-the-loop monitoring for medium-risk AI-augmented decisions | ✅ Human-oversight delegation token + approval-gate enforcement + health-probe review trigger | `hummbl_governance/delegation.py`, `hummbl_governance/kernel/authority_engine.py`, `hummbl_governance/health_probe.py` |
| Human-out-of-loop permitted only for low-risk decisions with safeguards and periodic review | ✅ Capability-fence scope restriction + lifecycle periodic-review checkpoints | `hummbl_governance/capability_fence.py`, `hummbl_governance/lifecycle.py` |

### Operations management (§C.3)

| Obligation | Coverage | Evidence |
|---|---|---|
| Integrate AI governance into every stage of the AI lifecycle — data collection, model development, deployment, monitoring | ✅ Lifecycle stage-gate enforcement + audit-log per-stage evidence tuples | `hummbl_governance/lifecycle.py`, `hummbl_governance/audit_log.py` |
| Maintain data quality, lineage, and provenance throughout the AI lifecycle | ✅ Audit-log data-lineage tuples + schema-validator integrity checks + receipt-engine provenance | `hummbl_governance/audit_log.py`, `hummbl_governance/schema_validator.py`, `hummbl_governance/kernel/receipt_engine.py` |
| Implement monitoring and incident-response mechanisms for deployed AI systems | ✅ Health-probe monitoring + circuit-breaker fast-fail + adverse-event tuples | `hummbl_governance/health_probe.py`, `hummbl_governance/circuit_breaker.py`, `hummbl_governance/audit_log.py` |
| Validate AI outputs against safety, correctness, and policy constraints; enforce cost/resource budgets | ✅ Output-validator gate + schema-validator conformance + cost-governor budget enforcement | `hummbl_governance/output_validator.py`, `hummbl_governance/schema_validator.py`, `hummbl_governance/cost_governor.py` |

### Stakeholder interaction and communication (§C.4)

| Obligation | Coverage | Evidence |
|---|---|---|
| Provide general disclosures of when AI is used in product or service offerings, including intended purpose and how AI affects the decision-making process | ✅ Transparency-notification primitive + explanation-disclosure generator (cross-ref EU AI Act Art. 50, Singapore Model Framework §D) | `hummbl_governance/output_validator.py`, `hummbl_governance/compliance_mapper.py` |
| Develop trust with stakeholders throughout design, development, and deployment | 🟡 Partial: audit-log transparency + receipt-engine accountability support trust; relationship-building is org task | `hummbl_governance/audit_log.py`, `hummbl_governance/kernel/receipt_engine.py` |
| Provide channels for stakeholder feedback and grievance redress | 🟡 Partial: coordination-bus message routing supports feedback ingest; grievance process is org task | `hummbl_governance/coordination_bus.py` |

### National-level recommendations for policymakers (§D)

| Obligation | Coverage | Evidence |
|---|---|---|
| Invest strategically in AI R&D; support workforce upskilling and AI talent nurturing | ⚪ Boundary: government R&D and workforce-development policy is organizational, not software-addressable | |
| Promote accessible data and infrastructure; encourage AI governance tools adoption by organisations | 🟡 Partial: HUMMBL primitives are governance tools organisations can adopt; promotion is policy task | `hummbl_governance/compliance_mapper.py` |
| Enhance public awareness of AI impacts and implications | ⚪ Boundary: public-awareness campaigns are organizational, not software-addressable | |

### Regional-level recommendations for policymakers (§E)

| Obligation | Coverage | Evidence |
|---|---|---|
| Set up an ASEAN Working Group on AI Governance; foster regional coordination and knowledge-sharing on AI governance best practices | ⚪ Boundary: intergovernmental body formation and coordination is organizational | |
| Develop common approach to personal data protection and data governance; align regional AI governance with international developments | 🟡 Partial: compliance-mapper crosswalks to international frameworks (NIST, ISO, EU); alignment act is policy task | `hummbl_governance/compliance_mapper.py` |

## Summary

| Section | Obligations | ✅ | 🟡 | ⚪ |
|---|---:|---:|---:|---:|
| Guiding principles (§B) | 7 | 7 | 0 | 0 |
| Internal governance structures (§C.1) | 4 | 2 | 2 | 0 |
| Human involvement in decision-making (§C.2) | 3 | 3 | 0 | 0 |
| Operations management (§C.3) | 4 | 4 | 0 | 0 |
| Stakeholder interaction and communication (§C.4) | 3 | 1 | 2 | 0 |
| National-level recommendations (§D) | 3 | 0 | 1 | 2 |
| Regional-level recommendations (§E) | 2 | 0 | 1 | 1 |
| **Totals** | **26** | **17** | **6** | **3** |

---

## Draft coverage summary (not public claim)

This matrix is internal starter material. It must not be used as public evidence that HUMMBL fulfills this framework until row counts, evidence commands, artifact paths, and boundary classifications are validated.

## Cross-references

- ADR: [`docs/adr/ADR-001-coverage-matrix-not-self-grade.md`](../adr/ADR-001-coverage-matrix-not-self-grade.md)
- Built on Singapore Model AI Governance Framework — see [`singapore-model-ai-governance.md`](./singapore-model-ai-governance.md)
- Transparency overlaps EU AI Act Art. 50 — see [`eu-ai-act.md`](./eu-ai-act.md)
- Risk management overlaps NIST AI RMF ASSESS/MEASURE — see [`nist-ai-rmf.md`](./nist-ai-rmf.md)
- Human oversight overlaps EU AI Act Art. 14 — see [`eu-ai-act.md`](./eu-ai-act.md)
- Privacy and data governance overlaps GDPR — see [`gdpr.md`](./gdpr.md) and India DPDP — see [`india-dpdp.md`](./india-dpdp.md)
- Companion Generative AI edition (Jan 2025) extends the Guide — out of scope for this matrix
