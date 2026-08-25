# Vermont Act 101 Coverage Matrix — HUMMBL

**Standard**: Act 101 (H.814) — An act relating to neurological rights and the use of artificial intelligence technology in health and human services
**Effective**: May 18, 2026 (on passage)
**Source**: https://legislature.vermont.gov/Documents/2026/Docs/ACTS/ACT101/ACT101%20As%20Enacted.pdf
**Last reviewed**: 2026-06-25
**Reviewer**: claude-code (huxley) per [ADR-001](../adr/ADR-001-coverage-matrix-not-self-grade.md)
**HUMMBL version**: hummbl-governance v0.8.0

## Boundary disclaimer

HUMMBL is not Vermont legal counsel and does not provide legal advice on Act 101. The Act declares individual neurological rights (18 V.S.A. ch. 42C § 1891), extends the Artificial Intelligence Advisory Council (3 V.S.A. § 5023) through June 30, 2030, and directs the Council to study and report on responsible AI use in health care, human services, and education by January 15, 2027. The enacted version deferred detailed healthcare-AI regulations (generative-AI patient-communication notice, mental-health chatbot disclosure, utilization-review restrictions) to the Council's recommendation process rather than codifying them directly. Statutory compliance is the customer-organization responsibility. HUMMBL maps technical primitives to the Act's neurological-rights, AI-review, and study-report obligations.

## Scope summary

Act 101 applies to the State of Vermont's recognition of individual neurological rights and the operations of the AI Advisory Council within the Division of Artificial Intelligence. The Act addresses AI systems developed, employed, or procured in State government, with a sectoral focus on health care, human services, and education. It does not impose direct operational obligations on private AI developers or deployers; instead it establishes a rights framework and a study/report mandate whose recommendations may inform future legislation. The Council's January 15, 2027 report is to cover generative-AI guidance for regulated professions and AI regulation in health-insurance utilization review.

## Obligations + coverage

### Intent and legislative goals (Sec. 1)

| Obligation | Coverage | Evidence |
|---|---|---|
| Protect human rights, promote equity, increase efficiency, enhance accessibility, create transparency, and guarantee accountability in health care and human services AI | 🟡 Partial: compliance-mapper + audit-log support transparency and accountability; equity and accessibility promotion is org task | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/audit_log.py` |
| Maximize the benefits and minimize the risks of AI in health care and human services | 🟡 Partial: health-probe + reward-monitor track behavioral health and reward signals; risk-minimization strategy is org task | `hummbl_governance/health_probe.py`, `hummbl_governance/reward_monitor.py` |
| Promote the ethical and responsible use of augmented intelligence in service delivery, coverage determinations, and access to health care and human services | 🟡 Partial: compliance-mapper + reasoning engine provide ethical-use substrate; deployment governance is org task | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/reasoning.py` |
| Prevent harm from the use of augmented and other AI in health care and human services | ✅ Kill-switch 4-mode halt + circuit-breaker fast-fail + capability-fence enforce harm-prevention boundaries | `hummbl_governance/kill_switch.py`, `hummbl_governance/circuit_breaker.py`, `hummbl_governance/capability_fence.py` |
| Improve the experience of patients, providers, and payers through AI | ⚪ Boundary: user-experience outcome is organizational, not software-addressable | |
| Improve quality of care, drive positive health outcomes, and cultivate population health through AI | ⚪ Boundary: health-outcome metrics are organizational/clinical, not software-addressable | |

### Neurological rights (Sec. 2, 18 V.S.A. ch. 42C § 1891)

| Obligation | Coverage | Evidence |
|---|---|---|
| Right to mental and neural data privacy | ✅ Capability-fence enforces data-access boundaries + identity registry binds data subjects + output-validator prevents neural-data leakage in outputs | `hummbl_governance/capability_fence.py`, `hummbl_governance/identity.py`, `hummbl_governance/output_validator.py` |
| Right to freedom of thought | 🟡 Partial: reasoning engine preserves agent reasoning autonomy; no direct neural-interface primitive (cross-ref physical-governor for BCI boundary) | `hummbl_governance/reasoning.py`, `hummbl_governance/physical_governor.py` |
| Right to nondiscrimination in the development and application of neurotechnologies | 🟡 Partial: stride-mapper + compliance-mapper support bias/discrimination assessment; fairness auditing is org task | `hummbl_governance/stride_mapper.py`, `hummbl_governance/compliance_mapper.py` |
| Right to change an individual's decision regarding neurotechnology and to determine by what means to change that decision | ✅ Delegation token revocation + lifecycle state transitions support consent withdrawal and decision-change | `hummbl_governance/delegation.py`, `hummbl_governance/lifecycle.py` |
| Right to protection from neurotechnological interventions of the mind and from unauthorized access to or manipulation of an individual's brain activity | ✅ Kill-switch halt + circuit-breaker fast-fail + capability-fence access boundary prevent unauthorized intervention | `hummbl_governance/kill_switch.py`, `hummbl_governance/circuit_breaker.py`, `hummbl_governance/capability_fence.py` |
| Right to protection from unauthorized neurotechnological alterations in mental functions critical to personality | ✅ Capability-fence + output-validator + kill-switch prevent unauthorized alteration of agent state and outputs | `hummbl_governance/capability_fence.py`, `hummbl_governance/output_validator.py`, `hummbl_governance/kill_switch.py` |

### Artificial Intelligence Advisory Council (Sec. 3, 3 V.S.A. § 5023)

| Obligation | Coverage | Evidence |
|---|---|---|
| Council established to advise the Director of the Division of Artificial Intelligence on reviewing AI systems in State government | ⚪ Boundary: government-body establishment is organizational, not software-addressable | |
| Review all aspects of AI systems developed, employed, or procured in State government | 🟡 Partial: compliance-mapper + audit-log + stride-mapper provide review/assessment substrate; government review process is org task | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/audit_log.py`, `hummbl_governance/stride_mapper.py` |
| Engage in public outreach and education on AI | ⚪ Boundary: public education is organizational, not software-addressable | |
| Council membership with ethics and human-rights expertise and diverse stakeholder representation | ⚪ Boundary: appointive membership is organizational | |
| Council duration extended to June 30, 2030 | ⚪ Boundary: legislative scheduling is organizational | |

### Responsible and ethical AI use — study and report (Sec. 4)

| Obligation | Coverage | Evidence |
|---|---|---|
| Review guidelines and recommendations from AMA, NASW, NEA, and other professional organizations on AI use in health care, human services, and education | 🟡 Partial: compliance-mapper cross-framework mapping + audit-log evidence retention support guideline review; substantive review is org task | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/audit_log.py` |
| Research existing and potential uses of AI in public participation processes and in public finance | ⚪ Boundary: policy research is organizational, not software-addressable | |
| Create opportunities for public education and engagement in the development of AI policy | ⚪ Boundary: public engagement is organizational | |
| Submit written report to the General Assembly on or before January 15, 2027 | 🟡 Partial: compliance-mapper report generator produces report content; legislative submission is org task | `hummbl_governance/compliance_mapper.py` |
| Report to recommend guidance on the use of generative AI by regulated professions | 🟡 Partial: output-validator + compliance-mapper provide labeling/guidance substrate; profession-specific guidance is org task | `hummbl_governance/output_validator.py`, `hummbl_governance/compliance_mapper.py` |
| Report to recommend regulating the use of AI and augmented intelligence in health-insurance utilization review processes | 🟡 Partial: audit-log + compliance-mapper provide review/audit substrate for utilization-review AI; regulatory recommendation is org task | `hummbl_governance/audit_log.py`, `hummbl_governance/compliance_mapper.py` |

## Summary

| Section | Obligations | ✅ | 🟡 | ⚪ |
|---|---:|---:|---:|---:|
| Intent and legislative goals (Sec. 1) | 6 | 1 | 3 | 2 |
| Neurological rights (Sec. 2, § 1891) | 6 | 4 | 2 | 0 |
| AI Advisory Council (Sec. 3, § 5023) | 5 | 0 | 1 | 4 |
| Study and report (Sec. 4) | 6 | 0 | 4 | 2 |
| **Totals** | **23** | **5** | **10** | **8** |

---

## Draft coverage summary (not public claim)

This matrix is internal starter material. It must not be used as public evidence that HUMMBL fulfills this framework until row counts, evidence commands, artifact paths, and boundary classifications are validated.

## Cross-references

- ADR: [`docs/adr/ADR-001-coverage-matrix-not-self-grade.md`](../adr/ADR-001-coverage-matrix-not-self-grade.md)
- Neurological rights overlap Chile neuro-rights framework — see [`chile-ai-bill.md`](./chile-ai-bill.md)
- AI system review overlaps NIST AI RMF GOVERN — see [`nist-ai-rmf.md`](./nist-ai-rmf.md)
- Generative-AI guidance for regulated professions overlaps EU AI Act Art. 50, Colorado § 6-1-1704, South Korea AI Basic Act Art. 31 — see [`eu-ai-act.md`](./eu-ai-act.md), [`colorado-ai-act.md`](./colorado-ai-act.md), [`south-korea-ai-basic-act.md`](./south-korea-ai-basic-act.md)
- Utilization-review AI regulation overlaps EU AI Act Art. 27 (FRIA) for high-risk healthcare AI — see [`eu-ai-act.md`](./eu-ai-act.md)
