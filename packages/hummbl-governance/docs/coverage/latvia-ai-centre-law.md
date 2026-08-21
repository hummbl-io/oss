# Latvia AI Centre Law Coverage Matrix — HUMMBL

**Standard**: Artificial Intelligence Centre Law (Mākslīgā intelekta centra likums), adopted by Saeima 6 March 2025, proclaimed 19 March 2025
**Effective**: 20 March 2025
**Source**: https://likumi.lv/ta/id/359339-maksliga-intelekta-centra-likums
**Last reviewed**: 2026-06-25
**Reviewer**: claude-code (huxley) per [ADR-001](../adr/ADR-001-coverage-matrix-not-self-grade.md)
**HUMMBL version**: hummbl-governance v0.8.0

## Boundary disclaimer

HUMMBL is not Latvian legal counsel and does not provide legal advice on the Artificial Intelligence Centre Law. The Law primarily establishes the AI Centre as a state-supported foundation under the Ministry of Smart Administration and Regional Development, with cross-sectoral governance including the Ministry of Defence. It creates a special regulatory environment (sandbox) for AI testing, defines data processing rules, and tasks the Centre with risk identification, guidance, and ecosystem coordination. Statutory compliance is the customer-organization responsibility. HUMMBL maps technical primitives to the Law's risk-mitigation, data-governance, safety, oversight, and transparency obligations that arise from the Centre's mandate.

## Scope summary

The Law establishes the Artificial Intelligence Centre as a foundation registered in the Associations and Foundations Register, with a nine-member Supervisory Board comprising representatives from the Ministry of Smart Administration and Regional Development, the Ministry of Economics, the Ministry of Defence, plus private-sector and higher-education representatives. The Centre's remit covers AI ecosystem building, risk identification, ethical deployment, skills development, dataset curation, Latvian language and cultural data inclusion, and administration of a special regulatory environment for AI system testing with time-bound regulatory derogations. Data processing within the sandbox is subject to minimisation, anonymisation/pseudonymisation, access restrictions, and mandatory deletion after development. The EU AI Act applies directly in Latvia and governs prohibited AI, high-risk AI, transparency, and GPAI models; this Law complements but does not duplicate that framework.

## Obligations + coverage

### Centre objectives — ethical and safe AI use (Art. 2)

| Obligation | Coverage | Evidence |
|---|---|---|
| Ensure AI systems are used ethically, responsibly, and safely, respecting fundamental human rights (Art. 2(5)) | ✅ Output-validation gate + reasoning-engine ethical-constraint checking (cross-ref EU AI Act Art. 14, Council of Europe AI Convention) | `hummbl_governance/output_validator.py`, `hummbl_governance/reasoning.py` |
| Implement measures to mitigate risks associated with AI use (Art. 2(6)) | ✅ Risk-mitigation substrate: adverse-event tuples + risk-treatment tuples + circuit-breaker fast-fail (cross-ref NIST AI RMF, EU AI Act Art. 9) | `hummbl_governance/audit_log.py`, `hummbl_governance/compliance_mapper.py`, `hummbl_governance/circuit_breaker.py` |
| Unite public, private, and academic intellectual and financial resources for AI ecosystem partnership (Art. 2(1)) | 🟡 Partial: coordination-bus supports multi-agent coordination and messaging; financial-resource pooling is organizational, not software-addressable | `hummbl_governance/coordination_bus.py` |
| Promote society's skills and equality in the field of AI (Art. 2(4)) | ⚪ Boundary: skills development and public education are organizational/policy tasks, not software-addressable | |

### Centre tasks — risk identification and guidance (Art. 4)

| Obligation | Coverage | Evidence |
|---|---|---|
| Identify security risks related to AI solutions in public and private sectors (Art. 4(1)(2)) | ✅ STRIDE threat-modeling mapper + risk-identification tuples + audit-log evidence capture (cross-ref NIST AI RMF MAP) | `hummbl_governance/stride_mapper.py`, `hummbl_governance/audit_log.py`, `hummbl_governance/compliance_mapper.py` |
| Provide opinions on AI or deepfake technology use during election campaigns, election day, or state official appointment processes (Art. 4(1)(3)) | ✅ Content-authenticity tuple + deepfake-labeling output-validation gate + audit-log opinion record (cross-ref EU AI Act Art. 50(2), South Korea AI Basic Act Art. 31) | `hummbl_governance/output_validator.py`, `hummbl_governance/audit_log.py` |
| Develop guidelines for public and private sectors on AI use and risk management (Art. 4(1)(5)) | ✅ Compliance-mapper guideline-generation + risk-treatment template production (cross-ref NIST AI RMF GOVERN) | `hummbl_governance/compliance_mapper.py` |
| Prepare proposals on risks that significantly limit human rights, democratic governance, and public security (Art. 4(1)(6)) | ✅ Risk-assessment template + human-rights impact component + STRIDE threat model (cross-ref EU AI Act Art. 27 FRIA, Council of Europe AI Convention) | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/stride_mapper.py` |
| Promote Latvian language sustainability and cultural data inclusion in AI solutions (Art. 4(1)(7)) | ⚪ Boundary: linguistic and cultural policy is organizational/national, not software-addressable | |

### Data governance (Art. 4, Art. 9)

| Obligation | Coverage | Evidence |
|---|---|---|
| Identify, create, and organize datasets for AI training (Art. 4(1)(8)) | 🟡 Partial: schema-validator validates dataset structure and integrity; dataset curation and sourcing are organizational tasks | `hummbl_governance/schema_validator.py` |
| Process personal data only for AI development, testing, and validation; comply with purpose-limitation (Art. 9(2)) | ✅ Audit-log purpose-binding tuples + identity-based access control + law-engine rule enforcement (cross-ref GDPR Art. 5) | `hummbl_governance/audit_log.py`, `hummbl_governance/identity.py`, `hummbl_governance/kernel/law_engine.py` |
| Apply data minimisation — process only personal data necessary for the specific AI system (Art. 9(4)) | ✅ Schema-validator field-level validation + audit-log data-scope tuples (cross-ref GDPR Art. 5(1)(c)) | `hummbl_governance/schema_validator.py`, `hummbl_governance/audit_log.py` |
| Anonymize or pseudonymize personal data where possible without defeating AI system purpose (Art. 9(4)) | ✅ Identity-registry pseudonymization + audit-log transformation record (cross-ref GDPR Art. 25) | `hummbl_governance/identity.py`, `hummbl_governance/audit_log.py` |
| Restrict data access to directly involved subjects with written agreements; prohibit transfer to third parties (Art. 9(5)–(6)) | ✅ Identity-based access control + delegation-token authorization + capability-fence data-boundary enforcement | `hummbl_governance/identity.py`, `hummbl_governance/delegation.py`, `hummbl_governance/capability_fence.py` |
| Irreversibly delete all personal data after AI system development, except where law provides otherwise (Art. 9(7)) | ✅ Lifecycle end-of-life deletion + audit-log deletion-record tuple + receipt-engine deletion confirmation | `hummbl_governance/lifecycle.py`, `hummbl_governance/audit_log.py`, `hummbl_governance/kernel/receipt_engine.py` |

### Special regulatory environment — sandbox (Art. 8)

| Obligation | Coverage | Evidence |
|---|---|---|
| Organize special regulatory environment for AI system development, testing, and advancement (Art. 8(1)) | ✅ Capability-fence sandboxed execution + health-probe monitoring + admission-control for sandbox entry (cross-ref EU AI Act Art. 57 regulatory sandbox) | `hummbl_governance/capability_fence.py`, `hummbl_governance/health_probe.py`, `hummbl_governance/kernel/admission_control.py` |
| Ensure AI development and testing does not endanger state, society, environment, economic security, or human health and life (Art. 8(2)) | ✅ Kill-switch 4-mode halt + circuit-breaker fast-fail + physical-governor safety boundary (cross-ref EU AI Act Art. 15, NIST AI RMF MEASURE) | `hummbl_governance/kill_switch.py`, `hummbl_governance/circuit_breaker.py`, `hummbl_governance/physical_governor.py` |
| Issue administrative acts with sandbox conditions, time periods, and regulatory derogations (Art. 8(2)) | 🟡 Partial: law-engine encodes rules and schedule-engine enforces time bounds; administrative-act issuance is an organizational function | `hummbl_governance/kernel/law_engine.py`, `hummbl_governance/kernel/schedule_engine.py` |
| Exclude sanctioned entities, Russian/Belarusian-influenced entities, and entities with criminal sanctions from sandbox (Art. 8(3)) | 🟡 Partial: identity-registry supports entity screening and exclusion lists; sanctions-screening data sourcing is organizational | `hummbl_governance/identity.py`, `hummbl_governance/kernel/identity_engine.py` |

### Governance, oversight, and transparency (Arts. 6, 7)

| Obligation | Coverage | Evidence |
|---|---|---|
| Supervisory Board with 9 members from ministries, private sector, and higher education (Art. 7(3)) | ⚪ Boundary: board composition and appointment are organizational/legal-entity governance, not software-addressable | |
| Centre under Ministry of Smart Administration supervision for delegated state administration tasks (Art. 4(2)) | ⚪ Boundary: ministerial oversight hierarchy is governmental, not software-addressable | |
| Ensure transparency in acquisition and use of financial resources and property (Art. 6(4)) | ✅ Audit-log immutable transaction record + receipt-engine evidence tuples + cost-governor budget tracking | `hummbl_governance/audit_log.py`, `hummbl_governance/kernel/receipt_engine.py`, `hummbl_governance/cost_governor.py` |
| State budget funds used only for defined tasks; contractual safeguards with termination conditions for free-use transfers (Art. 6(2)–(3)) | 🟡 Partial: cost-governor enforces budget-to-task allocation; contract-net manages contractual terms; termination enforcement is organizational | `hummbl_governance/cost_governor.py`, `hummbl_governance/contract_net.py` |

## Summary

| Section | Obligations | ✅ | 🟡 | ⚪ |
|---|---:|---:|---:|---:|
| Centre objectives — ethical and safe AI (Art. 2) | 4 | 2 | 1 | 1 |
| Centre tasks — risk and guidance (Art. 4) | 5 | 4 | 0 | 1 |
| Data governance (Arts. 4, 9) | 6 | 5 | 1 | 0 |
| Special regulatory environment — sandbox (Art. 8) | 4 | 2 | 2 | 0 |
| Governance, oversight, and transparency (Arts. 6, 7) | 4 | 1 | 1 | 2 |
| **Totals** | **23** | **14** | **5** | **4** |

---

## Draft coverage summary (not public claim)

This matrix is internal starter material. It must not be used as public evidence that HUMMBL fulfills this framework until row counts, evidence commands, artifact paths, and boundary classifications are validated.

## Cross-references

- ADR: [`docs/adr/ADR-001-coverage-matrix-not-self-grade.md`](../adr/ADR-001-coverage-matrix-not-self-grade.md)
- Risk management overlaps EU AI Act Art. 9 — see [`eu-ai-act.md`](./eu-ai-act.md)
- Deepfake labeling overlaps EU AI Act Art. 50(2) and South Korea AI Basic Act Art. 31 — see [`eu-ai-act.md`](./eu-ai-act.md), [`south-korea-ai-basic-act.md`](./south-korea-ai-basic-act.md)
- Data minimisation and deletion overlap GDPR Art. 5, Art. 25 — see [`gdpr.md`](./gdpr.md)
- Human-rights risk assessment overlaps EU AI Act Art. 27 (FRIA) and Council of Europe AI Convention — see [`eu-ai-act.md`](./eu-ai-act.md), [`council-of-europe-ai-convention.md`](./council-of-europe-ai-convention.md)
- STRIDE threat modeling overlaps NIST AI RMF MAP — see [`nist-ai-rmf.md`](./nist-ai-rmf.md), [`stride.md`](./stride.md)
- Regulatory sandbox overlaps EU AI Act Art. 57 — see [`eu-ai-act.md`](./eu-ai-act.md)
