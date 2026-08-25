# African Union Continental AI Strategy Coverage Matrix — HUMMBL

**Standard**: Continental Artificial Intelligence Strategy (AU), endorsed by AU Executive Council at 45th Ordinary Session, Accra, Ghana
**Effective**: July 18–19, 2024 (endorsement); implementation period 2025–2030
**Source**: https://au.int/en/documents/20240809/continental-artificial-intelligence-strategy
**Last reviewed**: 2026-06-25
**Reviewer**: claude-code (huxley) per [ADR-001](../adr/ADR-001-coverage-matrix-not-self-grade.md)
**HUMMBL version**: hummbl-governance v0.8.0

## Boundary disclaimer

HUMMBL is not African Union legal counsel and does not provide legal advice on the Continental AI Strategy. The Strategy is a non-binding continental policy framework (not a regulation) that guides AU Member States in developing national AI policies and governance systems. It articulates five focus areas, fifteen action areas, and high-level principles (people-centred, human rights and dignity, peace and prosperity, inclusion and diversity, ethics and transparency, local-first). Statutory implementation is the responsibility of AU Member States and customer organizations. HUMMBL maps technical primitives to the Strategy's governance, ethics, safety, data, capacity-building, transparency, and cooperation objectives.

## Scope summary

The Strategy applies continent-wide to AU Member States, the African Union Commission, regional economic communities, private sector actors, academia, and international partners. It is aligned with Agenda 2063, the AU Digital Transformation Strategy (2020–2030), the AU Data Policy Framework (2022), and the Malabo Convention on Cyber Security and Personal Data Protection. The Strategy's five focus areas are: (1) harnessing AI's benefits for African people and institutions; (2) minimising risks through governance, human rights, and ethics; (3) building capabilities in infrastructure, talent, datasets, and innovation; (4) fostering regional and international cooperation; (5) stimulating public and private investment. Implementation is phased 2025–2030 with a midterm review in 2027 and an African AI readiness index for monitoring.

## Obligations + coverage

### AI governance and regulatory frameworks (Action area 1)

| Obligation | Coverage | Evidence |
|---|---|---|
| Establish appropriate AI governance systems and regulations at regional and national levels | ✅ Governance-kernel substrate: authority + law + doctrine engines provide policy-as-code governance scaffold | `hummbl_governance/kernel/authority_engine.py`, `hummbl_governance/kernel/law_engine.py`, `hummbl_governance/kernel/doctrine_engine.py` |
| Adopt multi-tiered governance framework grounded in human rights, inclusion, and transparency | ✅ Layered governance: identity-engine + authority-engine + evidence-engine enforce tiered accountability | `hummbl_governance/kernel/identity_engine.py`, `hummbl_governance/kernel/authority_engine.py`, `hummbl_governance/kernel/evidence_engine.py` |
| Develop national AI strategies aligned with continental priorities | 🟡 Partial: compliance-mapper provides strategy-template + gap-analysis; national strategy authoring is org task | `hummbl_governance/compliance_mapper.py` |
| Create institutional mechanisms for responsible, safe, and accountable AI development | ✅ Institutional-governance substrate: admission-control + schedule-engine + receipt-engine for accountable execution | `hummbl_governance/kernel/admission_control.py`, `hummbl_governance/kernel/schedule_engine.py`, `hummbl_governance/kernel/receipt_engine.py` |

### Ethical principles and human rights (Action area 10 + guiding principles)

| Obligation | Coverage | Evidence |
|---|---|---|
| Adopt and implement ethical principles for AI that respect human dignity, gender equality, and human rights | ✅ Doctrine-engine encodes ethical principles as enforceable doctrine rules (cross-ref UNESCO AI Ethics, OECD AI Principles) | `hummbl_governance/kernel/doctrine_engine.py`, `hummbl_governance/compliance_mapper.py` |
| Ensure AI systems uphold inclusion, non-discrimination, and diversity (sex, gender, race, ethnicity, disability, age) | ✅ Output-validator bias-detection gate + doctrine-engine non-discrimination rules | `hummbl_governance/output_validator.py`, `hummbl_governance/kernel/doctrine_engine.py` |
| Protect vulnerable populations and ensure equitable distribution of AI benefits | 🟡 Partial: capability-fence restricts harmful capabilities; equity-distribution assessment is org policy task | `hummbl_governance/capability_fence.py` |
| Ensure AI systems are culturally relevant and contextually appropriate to African contexts | ⚪ Boundary: cultural-relevance assessment requires human judgment and local-context data, not software-addressable | |
| Conduct impact assessments to identify and mitigate potential harms (bias, discrimination, marginalisation) | ✅ Impact-assessment template with human-rights + bias component (cross-ref EU AI Act Art. 27 FRIA, NIST AI RMF) | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/audit_log.py` |

### Safety, security and technical standards (Action area 11)

| Obligation | Coverage | Evidence |
|---|---|---|
| Adopt and implement technical standards to ensure safety and security of AI systems across the continent | ✅ Safety-substrate: kill-switch + circuit-breaker + capability-fence enforce safety controls (cross-ref NIST AI RMF, ISO/IEC 23894) | `hummbl_governance/kill_switch.py`, `hummbl_governance/circuit_breaker.py`, `hummbl_governance/capability_fence.py` |
| Implement safeguards and protection from AI-related threats and misuse | ✅ Threat-mitigation: capability-fence + output-validator + kill-switch 4-mode halt | `hummbl_governance/capability_fence.py`, `hummbl_governance/output_validator.py`, `hummbl_governance/kill_switch.py` |
| Ensure AI systems advance peaceful and prosperous societies (peace and security principle) | 🟡 Partial: physical-governor + capability-fence prevent physical harm; peace-and-security assurance is broader org policy | `hummbl_governance/physical_governor.py`, `hummbl_governance/capability_fence.py` |

### Data governance, infrastructure and sovereignty (Action area 6)

| Obligation | Coverage | Evidence |
|---|---|---|
| Ensure availability of high-quality and diverse datasets for AI development | 🟡 Partial: schema-validator enforces data-quality + format standards; dataset curation is org task | `hummbl_governance/schema_validator.py` |
| Build underlying AI infrastructure (HPC, data centres, cloud, IoT) | ⚪ Boundary: physical-infrastructure provisioning is organizational, not software-addressable | |
| Promote data in open format or through regulatory sandboxes | 🟡 Partial: capability-fence sandbox mode + schema-validator open-format validation; sandbox deployment is org task | `hummbl_governance/capability_fence.py`, `hummbl_governance/schema_validator.py` |
| Ensure data sovereignty and facilitate cross-border data flows per AU Data Policy Framework | 🟡 Partial: identity-engine + audit-log track data lineage and jurisdiction; cross-border flow compliance is org legal task | `hummbl_governance/kernel/identity_engine.py`, `hummbl_governance/audit_log.py` |
| Protect personal data per Malabo Convention on Cyber Security and Personal Data Protection | ✅ Audit-log immutable record + identity-engine data-subject tracking + capability-fence data-access controls | `hummbl_governance/audit_log.py`, `hummbl_governance/kernel/identity_engine.py`, `hummbl_governance/capability_fence.py` |

### Capacity building, skills and innovation (Action areas 8–9)

| Obligation | Coverage | Evidence |
|---|---|---|
| Promote diversity in AI skills and AI talent, with particular attention to women and girls | ⚪ Boundary: workforce-development and education programs are organizational, not software-addressable | |
| Encourage research and innovation in AI through partnerships between academia, private and public sectors | ⚪ Boundary: research-partnership formation is organizational, not software-addressable | |
| Support AI readiness through skills development and knowledge transfer | 🟡 Partial: compliance-mapper readiness-assessment + health-probe capability diagnostic; training delivery is org task | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/health_probe.py` |

### Information integrity and transparency (Action area 7)

| Obligation | Coverage | Evidence |
|---|---|---|
| Promote information integrity and media and information literacy | 🟡 Partial: output-validator content-authenticity labeling + provenance tuples; literacy education is org task | `hummbl_governance/output_validator.py`, `hummbl_governance/audit_log.py` |
| Ensure transparency and accountability in AI development and deployment | ✅ Audit-log immutable trail + receipt-engine execution receipts + compliance-mapper transparency reporting | `hummbl_governance/audit_log.py`, `hummbl_governance/kernel/receipt_engine.py`, `hummbl_governance/compliance_mapper.py` |
| Provide explainability and disclosure for AI-generated outputs | ✅ Output-validator provenance-labeling + reasoning-engine explanation trace (cross-ref EU AI Act Art. 13, South Korea AI Basic Act Art. 31) | `hummbl_governance/output_validator.py`, `hummbl_governance/reasoning.py` |
| Detect and label AI-generated content to combat misinformation | ✅ Content-authenticity tuple + deepfake-labeling primitive (cross-ref EU AI Act Art. 50(2)) | `hummbl_governance/output_validator.py` |

### Cooperation, investment and monitoring (Action areas 12–15)

| Obligation | Coverage | Evidence |
|---|---|---|
| Foster regional and international cooperation on AI governance and capability building | 🟡 Partial: coordination-bus + lamport-clock support multi-agent coordination; inter-governmental cooperation is org task | `hummbl_governance/coordination_bus.py`, `hummbl_governance/lamport_clock.py` |
| Accelerate public and private investment in AI at national and regional levels | ⚪ Boundary: investment mobilization is organizational, not software-addressable | |
| Establish monitoring and evaluation framework with African AI readiness index | 🟡 Partial: health-probe + compliance-mapper readiness-assessment provide diagnostic substrate; index publication is org task | `hummbl_governance/health_probe.py`, `hummbl_governance/compliance_mapper.py` |
| Conduct midterm review of Strategy implementation progress (2027) | 🟡 Partial: audit-log + compliance-mapper produce review-evidence export; review execution is org task | `hummbl_governance/audit_log.py`, `hummbl_governance/compliance_mapper.py` |

## Summary

| Section | Obligations | ✅ | 🟡 | ⚪ |
|---|---:|---:|---:|---:|
| AI governance and regulatory frameworks (Action area 1) | 4 | 3 | 1 | 0 |
| Ethical principles and human rights (Action area 10 + principles) | 5 | 3 | 1 | 1 |
| Safety, security and technical standards (Action area 11) | 3 | 2 | 1 | 0 |
| Data governance, infrastructure and sovereignty (Action area 6) | 5 | 1 | 3 | 1 |
| Capacity building, skills and innovation (Action areas 8–9) | 3 | 0 | 1 | 2 |
| Information integrity and transparency (Action area 7) | 4 | 3 | 1 | 0 |
| Cooperation, investment and monitoring (Action areas 12–15) | 4 | 0 | 3 | 1 |
| **Totals** | **28** | **12** | **10** | **6** |

---

## Draft coverage summary (not public claim)

This matrix is internal starter material. It must not be used as public evidence that HUMMBL fulfills this framework until row counts, evidence commands, artifact paths, and boundary classifications are validated. The AU Continental AI Strategy is a non-binding policy framework; HUMMBL primitives map to the technical-governance and safety substrates that support Member State implementation, not to the political, investment, or capacity-building objectives that require organizational action.

## Cross-references

- ADR: [`docs/adr/ADR-001-coverage-matrix-not-self-grade.md`](../adr/ADR-001-coverage-matrix-not-self-grade.md)
- Ethical principles overlap UNESCO AI Ethics — see [`unesco-ai-ethics.md`](./unesco-ai-ethics.md)
- Ethical principles overlap OECD AI Principles — see [`oecd-ai-principles.md`](./oecd-ai-principles.md)
- Impact assessment overlaps EU AI Act Art. 27 (FRIA) — see [`eu-ai-act.md`](./eu-ai-act.md)
- Risk management overlaps NIST AI RMF — see [`nist-ai-rmf.md`](./nist-ai-rmf.md)
- Safety standards overlap ISO/IEC 23894 — see [`iso-iec-23894.md`](./iso-iec-23894.md)
- Transparency overlaps EU AI Act Art. 50, South Korea AI Basic Act Art. 31 — see [`eu-ai-act.md`](./eu-ai-act.md), [`south-korea-ai-basic-act.md`](./south-korea-ai-basic-act.md)
- Data protection overlaps Malabo Convention, GDPR — see [`gdpr.md`](./gdpr.md)
- National AI strategy overlap: Rwanda AI Policy — see [`rwanda-ai-policy.md`](./rwanda-ai-policy.md), Egypt AI Strategy — see [`egypt-ai-strategy.md`](./egypt-ai-strategy.md)
