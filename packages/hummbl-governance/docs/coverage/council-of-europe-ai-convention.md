# Council of Europe Framework Convention on AI Coverage Matrix — HUMMBL

**Standard**: Council of Europe Framework Convention on Artificial Intelligence and Human Rights, Democracy and the Rule of Law (CETS 225)
**Effective**: Opened for signature September 5, 2024; entry into force pending (requires 5 ratifications incl. at least 3 CoE member states)
**Source**: https://www.coe.int/en/web/artificial-intelligence/framework-convention
**Last reviewed**: 2026-06-25
**Reviewer**: claude-code (huxley) per [ADR-001](../adr/ADR-001-coverage-matrix-not-self-grade.md)
**HUMMBL version**: hummbl-governance v0.8.0

## Boundary disclaimer

HUMMBL is not international legal counsel and does not provide legal advice on the Framework Convention. The Convention is a treaty binding on state Parties, not on private AI systems directly; it obliges each Party to adopt or maintain legislative, administrative, or other measures giving effect to its principles. Measures must be graduated and differentiated by severity and probability of adverse impacts on human rights, democracy, and the rule of law. Statutory compliance is the customer-organization responsibility. HUMMBL maps technical primitives to the Convention's transparency, accountability, risk-management, remedy, and oversight principles to support organizations building AI systems consistent with those principles.

## Scope summary

The Convention covers activities within the lifecycle of AI systems that have the potential to interfere with human rights, democracy, and the rule of law. It applies mandatorily to activities by public authorities or private actors acting on their behalf (Art. 3(1)(a)); each Party must also address risks from private-actor activities not covered by (a) in a manner conforming with the Convention's object and purpose (Art. 3(1)(b)). National security activities are excluded (Art. 3(2)); national defence matters are excluded (Art. 3(4)); R&D on systems not yet made available is excluded unless testing has potential to interfere with human rights, democracy, or the rule of law (Art. 3(3)). The Convention is technology-neutral and does not regulate technology types or create new human rights; it reinforces existing applicable obligations.

## Obligations + coverage

### General obligations (Chapter II, Arts. 4–5)

| Obligation | Coverage | Evidence |
|---|---|---|
| Ensure AI lifecycle activities are consistent with obligations to protect human rights as enshrined in applicable international and domestic law (Art. 4) | 🟡 Partial: compliance-mapper maps AI activities to human-rights frameworks; law-engine encodes legal obligations; but ensuring consistency with all applicable human rights law is broader than software | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/kernel/law_engine.py`, `hummbl_governance/audit_log.py` |
| Adopt measures to ensure AI systems are not used to undermine integrity, independence, and effectiveness of democratic institutions and processes, including separation of powers, judicial independence, and access to justice (Art. 5(1)) | ⚪ Boundary: protecting democratic institutions and processes is a state-level governance matter, not directly software-addressable | |
| Adopt measures to protect democratic processes, including individuals' fair access to and participation in public debate and ability to freely form opinions (Art. 5(2)) | ⚪ Boundary: protection of democratic participation is a state-level policy matter | |

### Principles for AI lifecycle activities (Chapter III, Arts. 7–13)

| Obligation | Coverage | Evidence |
|---|---|---|
| Respect human dignity and individual autonomy in relation to AI lifecycle activities (Art. 7) | 🟡 Partial: doctrine-engine encodes dignity-respecting governance doctrines; capability-fence constrains AI actions that could violate dignity; but "respect for human dignity" is a broad ethical principle beyond software enforcement | `hummbl_governance/kernel/doctrine_engine.py`, `hummbl_governance/capability_fence.py`, `hummbl_governance/output_validator.py` |
| Ensure adequate transparency and oversight requirements tailored to specific contexts and risks, including identification of AI-generated content (Art. 8) | ✅ Transparency + oversight substrate: output-validation gate labels AI-generated content; audit-log provides transparency trail; compliance-mapper maps context-specific transparency requirements (cross-ref EU AI Act Art. 50, South Korea AI Basic Act Art. 31) | `hummbl_governance/output_validator.py`, `hummbl_governance/audit_log.py`, `hummbl_governance/compliance_mapper.py` |
| Ensure accountability and responsibility for adverse impacts on human rights, democracy, and the rule of law resulting from AI lifecycle activities (Art. 9) | ✅ Accountability substrate: immutable audit-log + receipt-engine accountability receipts + identity attribution + delegation-chain tracing (cross-ref EU AI Act Art. 14, NIST AI RMF GOVERN) | `hummbl_governance/audit_log.py`, `hummbl_governance/kernel/receipt_engine.py`, `hummbl_governance/identity.py`, `hummbl_governance/delegation.py` |
| Ensure AI lifecycle activities respect equality, including gender equality, and prohibition of discrimination (Art. 10(1)) | 🟡 Partial: output-validator can check for discriminatory outputs; compliance-mapper maps to equality frameworks; but ensuring non-discrimination requires bias testing and dataset auditing beyond HUMMBL's current primitives | `hummbl_governance/output_validator.py`, `hummbl_governance/compliance_mapper.py` |
| Adopt measures aimed at overcoming inequalities to achieve fair, just, and equitable outcomes (Art. 10(2)) | ⚪ Boundary: systemic inequality remediation is a societal and policy matter, not software-addressable | |
| Protect privacy rights and personal data through applicable domestic and international laws, standards, and frameworks (Art. 11(a)) | 🟡 Partial: audit-log records data-access events; identity-engine manages agent identity and data-access attribution; but comprehensive personal-data protection requires dedicated privacy mechanisms (cross-ref GDPR) | `hummbl_governance/audit_log.py`, `hummbl_governance/kernel/identity_engine.py`, `hummbl_governance/identity.py` |
| Put in place effective guarantees and safeguards for individuals regarding privacy (Art. 11(b)) | 🟡 Partial: capability-fence restricts unauthorized data access; audit-log records access with tamper-evidence; but comprehensive privacy safeguards are broader than access controls | `hummbl_governance/capability_fence.py`, `hummbl_governance/audit_log.py` |
| Promote reliability of AI systems and trust in their outputs, including quality and security throughout the lifecycle (Art. 12) | ✅ Reliability substrate: health-probe monitors system health; circuit-breaker prevents unreliable operation; schema-validator ensures output quality and conformance (cross-ref NIST AI RMF MEASURE, ISO/IEC 42001) | `hummbl_governance/health_probe.py`, `hummbl_governance/circuit_breaker.py`, `hummbl_governance/schema_validator.py` |
| Enable establishment of controlled environments (sandboxes) for developing, experimenting, and testing AI systems under supervision of competent authorities (Art. 13) | ✅ Sandbox substrate: capability-fence provides sandboxed execution with restricted capabilities; output-validator validates sandbox outputs; cost-governor bounds sandbox resource consumption | `hummbl_governance/capability_fence.py`, `hummbl_governance/output_validator.py`, `hummbl_governance/cost_governor.py` |

### Remedies and procedural safeguards (Chapter IV, Arts. 14–15)

| Obligation | Coverage | Evidence |
|---|---|---|
| Ensure availability of accessible and effective remedies for violations of human rights resulting from AI lifecycle activities (Art. 14(1)) | ⚪ Boundary: legal remedy availability is a state-level judicial and administrative matter | |
| Document relevant information regarding AI systems and usage, provide to authorized bodies and, where appropriate, to affected persons (Art. 14(2)(a)) | ✅ Documentation substrate: audit-log documents AI system activities with immutable trail; compliance-mapper generates documentation for authorities; receipt-engine produces verifiable records | `hummbl_governance/audit_log.py`, `hummbl_governance/compliance_mapper.py`, `hummbl_governance/kernel/receipt_engine.py` |
| Ensure information is sufficient for affected persons to contest decisions made by or substantially informed by AI systems, and the use of the system itself (Art. 14(2)(b)) | ✅ Explainability substrate: reasoning-engine provides explainable reasoning traces; audit-log records decision context and inputs; compliance-mapper generates contestability reports (cross-ref EU AI Act Art. 13, South Korea AI Basic Act Art. 34) | `hummbl_governance/reasoning.py`, `hummbl_governance/audit_log.py`, `hummbl_governance/compliance_mapper.py` |
| Provide effective possibility for persons concerned to lodge a complaint to competent authorities (Art. 14(2)(c)) | ⚪ Boundary: complaint mechanisms are institutional and legal processes, not software-addressable | |
| Ensure effective procedural guarantees, safeguards, and rights where AI significantly impacts human rights enjoyment (Art. 15(1)) | 🟡 Partial: audit-log + compliance-mapper provide documentation substrate for procedural guarantees; but procedural rights and safeguards are legal and institutional | `hummbl_governance/audit_log.py`, `hummbl_governance/compliance_mapper.py` |
| Notify persons interacting with AI systems that they are interacting with such systems rather than a human (Art. 15(2)) | ✅ Notification substrate: output-validator enforces AI-interaction notification labels; audit-log records notification events (cross-ref EU AI Act Art. 50(1), South Korea AI Basic Act Art. 31) | `hummbl_governance/output_validator.py`, `hummbl_governance/audit_log.py` |

### Risk and impact management framework (Chapter V, Art. 16)

| Obligation | Coverage | Evidence |
|---|---|---|
| Adopt measures for identification, assessment, prevention, and mitigation of risks posed by AI systems, considering actual and potential impacts on human rights, democracy, and the rule of law (Art. 16(1)) | ✅ Risk-management substrate: compliance-mapper provides risk-assessment framework; stride-mapper maps threats to human rights and democracy; evidence-engine collects risk evidence; audit-log records risk events (cross-ref NIST AI RMF MAP, EU AI Act Art. 9) | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/stride_mapper.py`, `hummbl_governance/kernel/evidence_engine.py`, `hummbl_governance/audit_log.py` |
| Implement graduated and differentiated measures: context and intended use (a), severity and probability (b), stakeholder perspectives (c), iterative application (d), monitoring (e), documentation (f), testing before first use and significant modification (g) (Art. 16(2)) | ✅ Graduated-measures substrate: compliance-mapper for risk graduation by context/severity; health-probe for continuous monitoring; lifecycle for iterative lifecycle management; audit-log for documentation; schema-validator for pre-deployment testing; schedule-engine for assessment scheduling | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/health_probe.py`, `hummbl_governance/lifecycle.py`, `hummbl_governance/audit_log.py`, `hummbl_governance/schema_validator.py`, `hummbl_governance/kernel/schedule_engine.py` |
| Ensure adverse impacts are adequately addressed; document impacts and measures, and inform risk management (Art. 16(3)) | ✅ Impact-addressing substrate: audit-log records adverse impacts and mitigation actions; compliance-mapper links impacts to risk-treatment tuples; evidence-engine captures impact evidence | `hummbl_governance/audit_log.py`, `hummbl_governance/compliance_mapper.py`, `hummbl_governance/kernel/evidence_engine.py` |
| Assess need for moratorium, ban, or other measures on certain AI uses incompatible with human rights, democracy, or rule of law (Art. 16(4)) | ✅ Halt/ban substrate: kill-switch provides 4-mode halt capability; capability-fence blocks specific use-cases; circuit-breaker enforces moratoria via fast-fail; authority-engine encodes ban authority | `hummbl_governance/kill_switch.py`, `hummbl_governance/capability_fence.py`, `hummbl_governance/circuit_breaker.py`, `hummbl_governance/kernel/authority_engine.py` |

### Implementation measures (Chapter VI, Arts. 17–20)

| Obligation | Coverage | Evidence |
|---|---|---|
| Secure implementation of the Convention without discrimination on any ground (Art. 17) | ⚪ Boundary: non-discriminatory implementation of the Convention by state Parties is a legal and policy matter | |
| Take due account of specific needs and vulnerabilities of persons with disabilities and of children (Art. 18) | ⚪ Boundary: accommodating vulnerable-group needs is a policy and design matter beyond HUMMBL's technical scope | |
| Ensure important AI questions are considered through public discussion and multistakeholder consultation (Art. 19) | ⚪ Boundary: multistakeholder public consultation is an institutional and political process | |
| Encourage and promote adequate digital literacy and digital skills for all population segments (Art. 20) | ⚪ Boundary: population-wide digital literacy promotion is an educational and policy matter | |

### Follow-up, reporting, and oversight (Chapter VII, Arts. 24–26)

| Obligation | Coverage | Evidence |
|---|---|---|
| Provide report to Conference of the Parties within first two years and periodically thereafter on activities to give effect to Art. 3(1)(a) and (b) (Art. 24) | 🟡 Partial: compliance-mapper generates compliance reports from audit-log evidence; but report submission to the Conference of the Parties is a state diplomatic task | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/audit_log.py` |
| Cooperate internationally and exchange relevant information on AI aspects with significant effects on human rights, democracy, and rule of law (Art. 25) | ⚪ Boundary: inter-state cooperation and information exchange is diplomatic, not software-addressable | |
| Establish or designate one or more effective, independent, and impartial oversight mechanisms with necessary powers, expertise, and resources (Art. 26(1)–(2)) | ⚪ Boundary: establishing state oversight bodies is institutional and legal | |
| Facilitate cooperation among multiple oversight mechanisms and with existing domestic human rights structures (Art. 26(3)–(4)) | ⚪ Boundary: inter-agency coordination is institutional | |

## Summary

| Section | Obligations | ✅ | 🟡 | ⚪ |
|---|---:|---:|---:|---:|
| General obligations (Arts. 4–5) | 3 | 0 | 1 | 2 |
| Principles for AI lifecycle (Arts. 7–13) | 9 | 4 | 4 | 1 |
| Remedies and procedural safeguards (Arts. 14–15) | 6 | 3 | 1 | 2 |
| Risk and impact management (Art. 16) | 4 | 4 | 0 | 0 |
| Implementation measures (Arts. 17–20) | 4 | 0 | 0 | 4 |
| Follow-up, reporting, and oversight (Arts. 24–26) | 4 | 0 | 1 | 3 |
| **Totals** | **30** | **11** | **7** | **12** |

---

## Draft coverage summary (not public claim)

This matrix is internal starter material. It must not be used as public evidence that HUMMBL fulfills this framework until row counts, evidence commands, artifact paths, and boundary classifications are validated.

## Cross-references

- ADR: [`docs/adr/ADR-001-coverage-matrix-not-self-grade.md`](../adr/ADR-001-coverage-matrix-not-self-grade.md)
- Transparency and AI-generated content identification overlaps EU AI Act Art. 50 — see [`eu-ai-act.md`](./eu-ai-act.md)
- Transparency and notification overlap South Korea AI Basic Act Art. 31 — see [`south-korea-ai-basic-act.md`](./south-korea-ai-basic-act.md)
- Risk management framework overlaps NIST AI RMF MAP/MEASURE — see [`nist-ai-rmf.md`](./nist-ai-rmf.md)
- Accountability and oversight overlap EU AI Act Art. 14 — see [`eu-ai-act.md`](./eu-ai-act.md)
- Contestability and explanation overlap EU AI Act Art. 13 — see [`eu-ai-act.md`](./eu-ai-act.md)
- Reliability and quality overlap ISO/IEC 42001 — see [`iso-42001.md`](./iso-42001.md)
- Privacy and data protection overlap GDPR — see [`gdpr.md`](./gdpr.md)
- Safe innovation / sandboxes overlap EU AI Act Art. 57 (regulatory sandboxes) — see [`eu-ai-act.md`](./eu-ai-act.md)
