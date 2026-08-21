# UNESCO Recommendation on the Ethics of AI Coverage Matrix — HUMMBL

**Standard**: UNESCO Recommendation on the Ethics of Artificial Intelligence (adopted 23 November 2021, 41st session of the General Conference)
**Effective**: 23 November 2021 (non-binding recommendation to 193 Member States)
**Source**: https://unesdoc.unesco.org/48231/pf0000381137
**Last reviewed**: 2026-06-25
**Reviewer**: claude-code (huxley) per [ADR-001](../adr/ADR-001-coverage-matrix-not-self-grade.md)
**HUMMBL version**: hummbl-governance v0.8.0

## Boundary disclaimer

HUMMBL is not an intergovernmental policy advisory and does not provide guidance on UNESCO Member State implementation of the Recommendation. The Recommendation is a non-binding soft-law instrument addressed to Member States, not to AI systems directly. It articulates 4 values, 10 core principles, and 11 policy action areas spanning the entire AI system life cycle — from research and design through deployment, maintenance, and termination. Many obligations are directed at governments (legislation, national strategies, international cooperation, funding) and are not software-addressable. HUMMBL maps technical primitives to the Recommendation's principles and policy areas where AI-system-level controls are relevant: safety, oversight, transparency, accountability, data protection, and impact assessment.

## Scope summary

The Recommendation applies to all AI actors — including researchers, developers, business enterprises, universities, and public/private entities — involved in any stage of the AI system life cycle (research, design, development, deployment, use, maintenance, operation, trade, financing, monitoring, validation, end-of-use, disassembly, termination). It covers AI systems with varying degrees of autonomy that process data and information in ways resembling intelligent behaviour, including machine learning, machine reasoning, and cyber-physical systems. The Recommendation is grounded in international human rights law and emphasises four values (human rights and dignity, environment and ecosystem flourishing, diversity and inclusiveness, peaceful/just/interconnected societies), ten core principles, and eleven policy action areas. It explicitly prohibits AI for social scoring or mass surveillance and requires that life-and-death decisions never be ceded to AI systems.

## Obligations + coverage

### Values (§III.1, paras 13–24)

| Obligation | Coverage | Evidence |
|---|---|---|
| Respect, protect, and promote human rights, fundamental freedoms, and human dignity throughout the AI life cycle (para 13–16) | ✅ Identity registry + delegation tokens enforce agent identity and accountability; authority engine validates actions against doctrine (cross-ref EU AI Act Art. 1–2, OECD AI Principles) | `hummbl_governance/identity.py`, `hummbl_governance/delegation.py`, `hummbl_governance/kernel/authority_engine.py` |
| Recognise, protect, and promote environment and ecosystem flourishing; reduce carbon footprint and environmental impact of AI systems (para 17–18) | ✅ Cost-governor budget enforcement + physical-governor kinematic limits constrain resource consumption (cross-ref NIST AI RMF GOVERN) | `hummbl_governance/cost_governor.py`, `hummbl_governance/physical_governor.py` |
| Ensure diversity and inclusiveness throughout the AI life cycle; promote participation of all individuals and groups regardless of race, gender, disability, or other grounds (para 19–21) | 🟡 Partial: output-validator bias-detection gate + compliance-mapper fairness assessment address algorithmic discrimination; broader participation and access are org/societal tasks | `hummbl_governance/output_validator.py`, `hummbl_governance/compliance_mapper.py` |
| Promote peaceful, just, and interconnected societies; AI must not segregate, objectify, or undermine human autonomy (para 22–24) | ⚪ Boundary: societal-level peace and justice outcomes are not software-addressable | |

### Core principles (§III.2, paras 25–47)

| Obligation | Coverage | Evidence |
|---|---|---|
| Proportionality and do no harm — AI use must not exceed what is necessary for a legitimate aim; risk assessment procedures must be implemented (para 25–26) | ✅ Kill-switch 4-mode halt + circuit-breaker fast-fail enforce proportionality; compliance-mapper risk-assessment template (cross-ref NIST AI RMF MAP) | `hummbl_governance/kill_switch.py`, `hummbl_governance/circuit_breaker.py`, `hummbl_governance/compliance_mapper.py` |
| Safety and security — unwanted harms and vulnerabilities to attack must be avoided, prevented, and eliminated throughout the AI life cycle (para 27) | ✅ Kill-switch + circuit-breaker + capability-fence sandbox + output-validator safety gate (cross-ref EU AI Act Art. 15) | `hummbl_governance/kill_switch.py`, `hummbl_governance/circuit_breaker.py`, `hummbl_governance/capability_fence.py`, `hummbl_governance/output_validator.py` |
| Fairness and non-discrimination — minimise and avoid reinforcing biased applications and outcomes; effective remedy against discrimination must be available (para 28–30) | ✅ Output-validator bias-detection gate + compliance-mapper fairness assessment + stride-mapper threat modelling (cross-ref EU AI Act Art. 10) | `hummbl_governance/output_validator.py`, `hummbl_governance/compliance_mapper.py`, `hummbl_governance/stride_mapper.py` |
| Sustainability — continuous assessment of human, social, cultural, economic, and environmental impact of AI technologies (para 31) | ✅ Cost-governor resource-budget enforcement + compliance-mapper impact-assessment template (cross-ref NIST AI RMF MEASURE) | `hummbl_governance/cost_governor.py`, `hummbl_governance/compliance_mapper.py` |
| Right to privacy and data protection — privacy must be respected throughout the AI life cycle; adequate data protection frameworks and privacy impact assessments (para 32–34) | ✅ Identity registry access-control + audit-log data-processing records + compliance-mapper privacy-impact-assessment template (cross-ref GDPR Art. 5, EU AI Act Art. 10) | `hummbl_governance/identity.py`, `hummbl_governance/audit_log.py`, `hummbl_governance/compliance_mapper.py` |
| Human oversight and determination — ethical and legal responsibility must always be attributable to physical persons or legal entities; life-and-death decisions must not be ceded to AI (para 35–36) | ✅ Delegation-token human-oversight authority + identity registry + kernel authority-engine enforcement (cross-ref EU AI Act Art. 14) | `hummbl_governance/delegation.py`, `hummbl_governance/identity.py`, `hummbl_governance/kernel/authority_engine.py` |
| Transparency and explainability — people must be informed when decisions are AI-informed; individuals should access reasons for decisions and request review (para 37–41) | ✅ Audit-log immutable decision records + compliance-mapper explanation-disclosure generator + reasoning-engine trace logging (cross-ref EU AI Act Art. 13) | `hummbl_governance/audit_log.py`, `hummbl_governance/compliance_mapper.py`, `hummbl_governance/reasoning.py` |
| Responsibility and accountability — ethical and legal responsibility must always be attributable to AI actors; oversight, audit, and due-diligence mechanisms must be developed (para 42–43) | ✅ Audit-log immutable accountability trail + kernel receipt-engine + kernel authority-engine role-based attribution (cross-ref NIST AI RMF GOVERN) | `hummbl_governance/audit_log.py`, `hummbl_governance/kernel/receipt_engine.py`, `hummbl_governance/kernel/authority_engine.py` |
| Awareness and literacy — public awareness and understanding of AI technologies and data should be promoted through education and training (para 44–45) | 🟡 Partial: compliance-mapper documentation + health-probe system-status reporting support awareness; public education programmes are org/societal tasks | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/health_probe.py` |
| Multi-stakeholder and adaptive governance and collaboration — participation of different stakeholders throughout the AI life cycle; open standards and interoperability (para 46–47) | 🟡 Partial: coordination-bus multi-agent coordination + contract-net multi-stakeholder task allocation address system-level collaboration; broader governance participation is org/societal | `hummbl_governance/coordination_bus.py`, `hummbl_governance/contract_net.py` |

### Policy Area 1: Ethical impact assessment (§IV, paras 50–53)

| Obligation | Coverage | Evidence |
|---|---|---|
| Introduce frameworks for ethical impact assessments to identify benefits, concerns, risks, and mitigation measures for AI systems (para 50) | ✅ Compliance-mapper impact-assessment template with human-rights, environmental, and social-impact components (cross-ref EU AI Act Art. 27 FRIA, NIST AI RMF MAP) | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/audit_log.py` |
| Develop due diligence and oversight mechanisms to identify, prevent, mitigate, and account for AI system impacts on human rights and rule of law (para 51) | ✅ Audit-log due-diligence records + stride-mapper threat modelling + compliance-mapper risk-treatment tuples (cross-ref NIST AI RMF MANAGE) | `hummbl_governance/audit_log.py`, `hummbl_governance/stride_mapper.py`, `hummbl_governance/compliance_mapper.py` |
| Monitor all phases of the AI life cycle, including algorithm functioning, data, and AI actors involved (para 52) | ✅ Audit-log lifecycle event capture + health-probe continuous monitoring + kernel sequence-engine ordered-event tracking | `hummbl_governance/audit_log.py`, `hummbl_governance/health_probe.py`, `hummbl_governance/kernel/sequence_engine.py` |
| Establish regulatory framework for ethical impact assessments with auditability, traceability, explainability, and external review (para 53) | 🟡 Partial: audit-log + compliance-mapper provide auditability and traceability substrate; regulatory framework adoption and external review are org/government tasks | `hummbl_governance/audit_log.py`, `hummbl_governance/compliance_mapper.py` |

### Policy Area 2: Ethical governance and stewardship (§IV, paras 54–70)

| Obligation | Coverage | Evidence |
|---|---|---|
| Ensure AI governance mechanisms are inclusive, transparent, multidisciplinary, and multi-stakeholder with anticipation, protection, monitoring, enforcement, and redress (para 54) | 🟡 Partial: coordination-bus + kernel authority-engine + audit-log provide transparent governance substrate; inclusiveness and redress mechanisms are org/societal | `hummbl_governance/coordination_bus.py`, `hummbl_governance/kernel/authority_engine.py`, `hummbl_governance/audit_log.py` |
| Investigate and redress harms caused through AI systems; promote auditability and traceability (para 55) | ✅ Audit-log immutable traceability + kernel receipt-engine evidence records + compliance-mapper harm-reporting tuples (cross-ref NIST AI RMF MANAGE) | `hummbl_governance/audit_log.py`, `hummbl_governance/kernel/receipt_engine.py`, `hummbl_governance/compliance_mapper.py` |
| Develop certification mechanisms for AI systems with regular monitoring and re-certification (para 56) | ⚪ Boundary: certification-body accreditation and mutual recognition are governmental, not software-addressable | |
| Appoint independent AI Ethics Officer to oversee ethical impact assessment, auditing, and continuous monitoring (para 58) | 🟡 Partial: delegation-token role assignment + identity registry support role designation; appointment of an independent officer is org task | `hummbl_governance/delegation.py`, `hummbl_governance/identity.py` |
| Develop accountability and liability frameworks ensuring ultimate responsibility lies with natural or legal persons; AI systems must not be given legal personality (para 68) | ✅ Kernel authority-engine + identity registry enforce that all actions are attributable to registered agents; no AI legal personality is modelled (cross-ref EU AI Act Art. 14) | `hummbl_governance/kernel/authority_engine.py`, `hummbl_governance/identity.py`, `hummbl_governance/kernel/identity_engine.py` |

### Policy Area 3: Data policy (§IV, paras 71–77)

| Obligation | Coverage | Evidence |
|---|---|---|
| Develop data governance strategies ensuring continual evaluation of training data quality, data security, and protection measures (para 71) | ✅ Schema-validator data-quality enforcement + audit-log data-processing records + compliance-mapper data-governance assessment (cross-ref GDPR Art. 5) | `hummbl_governance/schema_validator.py`, `hummbl_governance/audit_log.py`, `hummbl_governance/compliance_mapper.py` |
| Put in place safeguards to protect the right to privacy; carry out privacy impact assessments and apply privacy by design (para 72) | ✅ Identity registry access-control + compliance-mapper privacy-impact-assessment template + output-validator data-minimisation gate (cross-ref GDPR Art. 25) | `hummbl_governance/identity.py`, `hummbl_governance/compliance_mapper.py`, `hummbl_governance/output_validator.py` |
| Ensure individuals retain rights over personal data including access, erasure, and effective independent oversight (para 73–74) | 🟡 Partial: audit-log supports data-subject access and erasure records; legal rights enforcement and independent oversight authority are org/legal tasks | `hummbl_governance/audit_log.py`, `hummbl_governance/identity.py` |

### Policy Area 5: Environment and ecosystems (§IV, paras 84–86)

| Obligation | Coverage | Evidence |
|---|---|---|
| Assess direct and indirect environmental impact throughout the AI life cycle including carbon footprint, energy consumption, and raw material extraction (para 84) | ✅ Cost-governor resource-budget enforcement + compliance-mapper environmental-impact-assessment template (cross-ref NIST AI RMF GOVERN) | `hummbl_governance/cost_governor.py`, `hummbl_governance/compliance_mapper.py` |
| Favour data-, energy-, and resource-efficient AI methods; apply precautionary principle where disproportionate negative impacts exist (para 86) | ✅ Cost-governor budget caps + circuit-breaker fast-fail on resource-threshold breach + kill-switch halt on precautionary trigger | `hummbl_governance/cost_governor.py`, `hummbl_governance/circuit_breaker.py`, `hummbl_governance/kill_switch.py` |

### Policy Area 11: Health and social well-being (§IV, paras 121–130)

| Obligation | Coverage | Evidence |
|---|---|---|
| Ensure AI systems in health care are safe, effective, scientifically proven, and that final diagnosis and treatment decisions are taken by humans (para 121–123) | ✅ Kill-switch + circuit-breaker + output-validator safety gate + delegation-token human-determination authority for life-critical decisions (cross-ref EU AI Act Art. 14) | `hummbl_governance/kill_switch.py`, `hummbl_governance/circuit_breaker.py`, `hummbl_governance/output_validator.py`, `hummbl_governance/delegation.py` |
| Ensure users can easily identify whether they are interacting with a living being or an AI system and can request human intervention (para 127) | ✅ Output-validator AI-identification labeling + identity registry agent-type disclosure (cross-ref EU AI Act Art. 50, Colorado § 6-1-1704) | `hummbl_governance/output_validator.py`, `hummbl_governance/identity.py` |
| Regulate human-robot interactions; ensure AI-powered neurotechnologies and brain-computer interfaces preserve human dignity and autonomy (para 125–126) | ✅ Physical-governor kinematic limits + capability-fence action restriction + output-validator safety gate for physical-AI interactions | `hummbl_governance/physical_governor.py`, `hummbl_governance/capability_fence.py`, `hummbl_governance/output_validator.py` |

### Monitoring and evaluation (§V, paras 131–134)

| Obligation | Coverage | Evidence |
|---|---|---|
| Credibly and transparently monitor and evaluate policies, programmes, and mechanisms related to ethics of AI using quantitative and qualitative approaches (para 131) | ✅ Audit-log immutable monitoring records + compliance-mapper evaluation template + health-probe continuous system-status reporting (cross-ref NIST AI RMF MEASURE) | `hummbl_governance/audit_log.py`, `hummbl_governance/compliance_mapper.py`, `hummbl_governance/health_probe.py` |
| Develop tools and indicators for assessing effectiveness and efficiency against agreed standards; monitoring should be continuous and proportionate to risk (para 133) | ✅ Compliance-mapper indicator framework + audit-log continuous event capture + stride-mapper risk-proportionate monitoring (cross-ref NIST AI RMF MEASURE) | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/audit_log.py`, `hummbl_governance/stride_mapper.py` |
| Consider mechanisms such as ethics commissions, AI ethics observatories, regulatory sandboxes, and assessment guides for AI actors (para 134) | ⚪ Boundary: institutional mechanisms (commissions, observatories, sandboxes) are governmental/organisational, not software-addressable | |

## Summary

| Section | Obligations | ✅ | 🟡 | ⚪ |
|---|---:|---:|---:|---:|
| Values (§III.1, paras 13–24) | 4 | 2 | 1 | 1 |
| Core principles (§III.2, paras 25–47) | 10 | 8 | 2 | 0 |
| Policy Area 1: Ethical impact assessment (paras 50–53) | 4 | 3 | 1 | 0 |
| Policy Area 2: Ethical governance and stewardship (paras 54–70) | 5 | 2 | 2 | 1 |
| Policy Area 3: Data policy (paras 71–77) | 3 | 2 | 1 | 0 |
| Policy Area 5: Environment and ecosystems (paras 84–86) | 2 | 2 | 0 | 0 |
| Policy Area 11: Health and social well-being (paras 121–130) | 3 | 3 | 0 | 0 |
| Monitoring and evaluation (§V, paras 131–134) | 3 | 2 | 0 | 1 |
| **Totals** | **34** | **24** | **7** | **3** |

---

## Draft coverage summary (not public claim)

This matrix is internal starter material. It must not be used as public evidence that HUMMBL fulfills this framework until row counts, evidence commands, artifact paths, and boundary classifications are validated.

## Cross-references

- ADR: [`docs/adr/ADR-001-coverage-matrix-not-self-grade.md`](../adr/ADR-001-coverage-matrix-not-self-grade.md)
- Human oversight overlaps EU AI Act Art. 14 — see [`eu-ai-act.md`](./eu-ai-act.md)
- Transparency overlaps EU AI Act Art. 13 — see [`eu-ai-act.md`](./eu-ai-act.md)
- Impact assessment overlaps EU AI Act Art. 27 (FRIA) — see [`eu-ai-act.md`](./eu-ai-act.md)
- Risk management overlaps NIST AI RMF MAP/MEASURE/MANAGE — see [`nist-ai-rmf.md`](./nist-ai-rmf.md)
- Privacy and data protection overlaps GDPR Art. 5, Art. 25 — see [`gdpr.md`](./gdpr.md)
- Transparency notification overlaps South Korea AI Basic Act Art. 31 — see [`south-korea-ai-basic-act.md`](./south-korea-ai-basic-act.md)
- Values and principles overlap OECD AI Principles — see [`oecd-ai-principles.md`](./oecd-ai-principles.md)
- AI identification labeling overlaps Colorado AI Act § 6-1-1704 — see [`colorado-ai-act.md`](./colorado-ai-act.md)
