# Chile AI Bill Coverage Matrix — HUMMBL

**Standard**: Proyecto de Ley que regula los Sistemas de Inteligencia Artificial (Boletín N° 16821-19, refundido con Boletín N° 15869-19)
**Effective**: Enacted September 15, 2025 (pending implementation — staggered entry into force per transitory provisions)
**Source**: https://www.camara.cl/
**Last reviewed**: 2026-06-25
**Reviewer**: claude-code (huxley) per [ADR-001](../adr/ADR-001-coverage-matrix-not-self-grade.md)
**HUMMBL version**: hummbl-governance v0.8.0

## Boundary disclaimer

HUMMBL is not Chilean legal counsel and does not provide legal advice on the AI Bill. The Bill distinguishes "operators" (providers, implementers, importers, distributors, authorized representatives) and classifies AI uses into unacceptable (prohibited), high-risk, limited-risk, and no-evident-risk tiers. Statutory compliance is the customer-organization responsibility. HUMMBL maps technical primitives to the Bill's risk-management, transparency, human-oversight, incident-reporting, and cybersecurity obligations.

## Scope summary

The Bill applies to providers introducing AI systems into the Chilean market, implementers domiciled in Chile, and foreign providers/implementers whose system outputs are used in Chile. Exceptions cover national defense, internal security, public-order systems, pre-commercialization R&D, and personal non-professional use. High-risk AI covers sectors including biometric identification, critical infrastructure, education and vocational training, employment and worker management, and access to essential public or private services. The Bill adopts a four-tier risk classification mirroring the EU AI Act, with Chile-specific institutional governance under the Ministry of Science, Technology, Knowledge and Innovation, the Data Protection Agency (APDP), and a Technical Advisory Council. Staggered entry into force: 6 months (unacceptable-risk prohibitions), 12 months (institutional provisions), 18 months (general articulado), 24 months (high-risk technical requirements).

## Obligations + coverage

### Prohibited practices — unacceptable risk (Art. 6)

| Obligation | Coverage | Evidence |
|---|---|---|
| Prohibit subliminal manipulation techniques that distort human behavior causing harm | ✅ Capability-fence blocks manipulative output patterns + output-validator gate (cross-ref EU AI Act Art. 5) | `hummbl_governance/capability_fence.py`, `hummbl_governance/output_validator.py` |
| Prohibit generic social scoring systems evaluating persons based on social behavior | ✅ Capability-fence blocks scoring-on-social-traits patterns + output-validator discrimination gate | `hummbl_governance/capability_fence.py`, `hummbl_governance/output_validator.py` |
| Prohibit biometric categorization based on sensitive personal data | ✅ Capability-fence blocks sensitive-attribute inference + output-validator bias gate | `hummbl_governance/capability_fence.py`, `hummbl_governance/output_validator.py` |
| Prohibit real-time remote biometric identification in public spaces (with judicial-authorization exceptions) | ✅ Capability-fence blocks real-time biometric-ID mode + kill-switch halt on policy violation | `hummbl_governance/capability_fence.py`, `hummbl_governance/kill_switch.py` |
| Prohibit non-selective facial-image extraction from the internet or CCTV | ✅ Capability-fence blocks bulk facial-extraction capability + output-validator gate | `hummbl_governance/capability_fence.py`, `hummbl_governance/output_validator.py` |
| Prohibit emotion recognition in workplaces and educational institutions | ✅ Capability-fence blocks emotion-recognition-in-context patterns | `hummbl_governance/capability_fence.py` |

### High-risk AI obligations (Art. 8)

| Obligation | Coverage | Evidence |
|---|---|---|
| Establish continuous, iterative risk-management system across the AI lifecycle | ✅ Risk-mgmt program substrate: INTENT + adverse-event tuples + risk-treatment tuples (cross-ref NIST AI RMF, EU AI Act Art. 9) | `hummbl_governance/audit_log.py`, `hummbl_governance/compliance_mapper.py` |
| Implement data governance with bias detection and representativeness assessment | ✅ Bias-detection evidence tuple + data-governance assessment template | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/audit_log.py` |
| Maintain technical documentation demonstrating compliance | ✅ Documentation-retention tuple + immutable audit-log evidence store | `hummbl_governance/audit_log.py`, `hummbl_governance/compliance_mapper.py` |
| Implement automatic event-logging (registros) for traceability across lifecycle | ✅ Immutable audit-log with automatic event recording + Lamport-clock ordering | `hummbl_governance/audit_log.py`, `hummbl_governance/lamport_clock.py` |
| Ensure transparency and explainability sufficient for operators and affected persons to understand system operation | ✅ Explanation-disclosure generator + transparency-notification primitive (cross-ref EU AI Act Art. 13) | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/output_validator.py` |
| Design for effective human oversight — system must be controllable and monitorable by natural persons | ✅ Human-oversight delegation token + kill-switch 4-mode halt + circuit-breaker fast-fail (cross-ref EU AI Act Art. 14) | `hummbl_governance/delegation.py`, `hummbl_governance/kill_switch.py`, `hummbl_governance/circuit_breaker.py` |
| Guarantee adequate levels of accuracy, robustness, and cybersecurity per Ley N° 21.663 | ✅ Circuit-breaker fast-fail + output-validator robustness gate + health-probe monitoring | `hummbl_governance/circuit_breaker.py`, `hummbl_governance/output_validator.py`, `hummbl_governance/health_probe.py` |
| Ensure system respects fundamental rights and prevents stereotyping or degradation of persons or groups | ✅ Output-validator discrimination gate + bias-evidence tuples + capability-fence | `hummbl_governance/output_validator.py`, `hummbl_governance/capability_fence.py` |

### Post-market monitoring and incidents (Arts. 9, 12)

| Obligation | Coverage | Evidence |
|---|---|---|
| Establish and document post-implementation monitoring system proportional to identified risks | ✅ Post-market surveillance substrate: health-probe continuous monitoring + adverse-event tuples | `hummbl_governance/health_probe.py`, `hummbl_governance/audit_log.py` |
| Report incidents to APDP within 72 hours of establishing causal link between AI use and incident | 🟡 Partial: incident-detection + audit-log capture produces the report; 72-hour submission to APDP is org task | `hummbl_governance/audit_log.py`, `hummbl_governance/compliance_mapper.py` |
| Notify affected persons when an incident is confirmed | 🟡 Partial: notification-content generator produces the notice; delivery to affected persons is org task | `hummbl_governance/compliance_mapper.py` |
| Adopt immediate corrective measures — deactivate, withdraw from market, or suspend the system | ✅ Kill-switch 4-mode halt + circuit-breaker fast-fail + capability-fence block | `hummbl_governance/kill_switch.py`, `hummbl_governance/circuit_breaker.py`, `hummbl_governance/capability_fence.py` |
| Coordinate cybersecurity-related incidents with Agencia Nacional de Ciberseguridad (ANCI) per Ley N° 21.663 | 🟡 Partial: incident evidence export supports coordination; inter-agency communication is org task | `hummbl_governance/audit_log.py`, `hummbl_governance/compliance_mapper.py` |

### Transparency obligations (Arts. 5, 10, 11)

| Obligation | Coverage | Evidence |
|---|---|---|
| Mark synthetic content (audio, image, video, text) in machine-readable format detectable as AI-generated or manipulated | ✅ Content-authenticity tuple + provenance-labeling primitive (cross-ref EU AI Act Art. 50(2)) | `hummbl_governance/output_validator.py`, `hummbl_governance/audit_log.py` |
| Ensure technical marking solutions are effective, interoperable, and proportionate to content type and state of the art | ✅ Output-validator labeling gate with interoperable provenance tuple format | `hummbl_governance/output_validator.py` |
| Provide transparency on training data — biennial report on categories of data used for training general-purpose AI | 🟡 Partial: compliance-report generator produces the report content; biennial publication is org task | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/audit_log.py` |
| Disclose training data to copyright holders or parties with legitimate interests | ⚪ Boundary: legal-rights disclosure to third parties is organizational, not software-addressable | |
| Inform persons clearly and timely when interacting with limited-risk AI systems (except when evident from context) | ✅ Transparency-notification primitive + interaction-labeling tuple (cross-ref EU AI Act Art. 50(1)) | `hummbl_governance/output_validator.py`, `hummbl_governance/audit_log.py` |
| Ensure limited-risk systems provide transparency, explainability, and security proportional to risk level | ✅ Proportionate-transparency tuple + output-validator gate + capability-fence | `hummbl_governance/output_validator.py`, `hummbl_governance/capability_fence.py` |

### Governance and institutional framework (Arts. 4, 16, 24)

| Obligation | Coverage | Evidence |
|---|---|---|
| Observe general principles: human oversight, safety, transparency, accountability, fairness, environmental well-being | ✅ Doctrine-engine encodes governance principles + authority-engine enforces policy | `hummbl_governance/kernel/doctrine_engine.py`, `hummbl_governance/kernel/authority_engine.py` |
| Cooperate with APDP inspections and fact-finding investigations | 🟡 Partial: audit-log export + compliance-report generator supports inspection; cooperation act is org task | `hummbl_governance/audit_log.py`, `hummbl_governance/compliance_mapper.py` |
| Comply with APDP corrective orders for transparency, safety, or reliability violations | ⚪ Boundary: regulatory-order compliance is organizational | |
| Maintain risk registers and documentation for audit and conformity assessment | ✅ Immutable audit-log retention + documentation-retention tuple + evidence-engine | `hummbl_governance/audit_log.py`, `hummbl_governance/kernel/evidence_engine.py` |
| Technical Advisory Council evaluates implementation and recommends changes every three years | ⚪ Boundary: government-council deliberation is organizational, not software-addressable | |

### Sandbox and innovation safeguards

| Obligation | Coverage | Evidence |
|---|---|---|
| Regulated sandboxes for supervised experimentation of innovative AI systems | 🟡 Partial: capability-fence + output-validator sandbox mode provides controlled testing environment; formal sandbox approval is org task | `hummbl_governance/capability_fence.py`, `hummbl_governance/output_validator.py` |
| Limited exemptions for pre-commercialization R&D respecting fundamental rights | 🟡 Partial: capability-fence scoped-mode supports research exemptions; legal exemption determination is org task | `hummbl_governance/capability_fence.py` |
| Proportionality and scaled obligations for SMEs | ⚪ Boundary: SME-proportionality determination is organizational, not software-addressable | |

### Sanctions and enforcement (Arts. 24–27)

| Obligation | Coverage | Evidence |
|---|---|---|
| Infracciones gravísimas — up to 20,000 UTM for violating unacceptable-risk prohibitions | ⚪ Boundary: administrative-fine exposure is legal, not software-addressable | |
| Infracciones graves — up to 10,000 UTM for violating high-risk obligations (Art. 8) | ⚪ Boundary: administrative-fine exposure is legal | |
| Infracciones leves — up to 5,000 UTM for providing inaccurate or incomplete information to authority | ⚪ Boundary: administrative-fine exposure is legal | |
| Mitigating factors — prompt cooperation and active remediation reduce sanctions | ⚪ Boundary: sanction-mitigation determination is legal/administrative | |

## Summary

| Section | Obligations | ✅ | 🟡 | ⚪ |
|---|---:|---:|---:|---:|
| Prohibited practices — unacceptable risk (Art. 6) | 6 | 6 | 0 | 0 |
| High-risk AI obligations (Art. 8) | 8 | 8 | 0 | 0 |
| Post-market monitoring and incidents (Arts. 9, 12) | 5 | 2 | 3 | 0 |
| Transparency obligations (Arts. 5, 10, 11) | 6 | 4 | 1 | 1 |
| Governance and institutional framework (Arts. 4, 16, 24) | 5 | 2 | 1 | 2 |
| Sandbox and innovation safeguards | 3 | 0 | 2 | 1 |
| Sanctions and enforcement (Arts. 24–27) | 4 | 0 | 0 | 4 |
| **Totals** | **37** | **22** | **7** | **8** |

---

## Draft coverage summary (not public claim)

This matrix is internal starter material. It must not be used as public evidence that HUMMBL fulfills this framework until row counts, evidence commands, artifact paths, and boundary classifications are validated.

## Cross-references

- ADR: [`docs/adr/ADR-001-coverage-matrix-not-self-grade.md`](../adr/ADR-001-coverage-matrix-not-self-grade.md)
- Prohibited practices overlap EU AI Act Art. 5 — see [`eu-ai-act.md`](./eu-ai-act.md)
- Risk management overlaps EU AI Act Art. 9 and NIST AI RMF — see [`eu-ai-act.md`](./eu-ai-act.md), [`nist-ai-rmf.md`](./nist-ai-rmf.md)
- Human oversight overlaps EU AI Act Art. 14 — see [`eu-ai-act.md`](./eu-ai-act.md)
- Transparency and synthetic-content labeling overlap EU AI Act Art. 50 — see [`eu-ai-act.md`](./eu-ai-act.md)
- Incident reporting overlaps South Korea AI Basic Act Art. 32 — see [`south-korea-ai-basic-act.md`](./south-korea-ai-basic-act.md)
- Cybersecurity obligations reference Ley N° 21.663 (Chile cybersecurity framework)
- Data protection coordination references Ley N° 21.719 (Chile personal-data protection law)
