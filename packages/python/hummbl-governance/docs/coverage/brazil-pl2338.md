# Brazil PL 2338/2023 Coverage Matrix — HUMMBL

**Standard**: Projeto de Lei nº 2338/2023 — Marco Legal da Inteligência Artificial (Senate-approved text, Substitutivo CTIA)
**Effective**: Pending — Senate approved 10 December 2024; entry into force 1 year after publication per Art. 45 (Chamber of Deputies may amend)
**Source**: https://regulations.ai/regulations/brazil-2023-05-pl2338
**Last reviewed**: 2026-06-25
**Reviewer**: claude-code (huxley) per [ADR-001](../adr/ADR-001-coverage-matrix-not-self-grade.md)
**HUMMBL version**: hummbl-governance v0.8.0

## Boundary disclaimer

HUMMBL is not Brazilian legal counsel and does not provide legal advice on PL 2338/2023 (Marco Legal da IA). The bill is not yet law — it passed the Senate on 10 December 2024 and awaits a rapporteur's report in the Chamber of Deputies Special Commission. The Senate-approved text establishes a risk-based framework (excessive / high / non-high risk) with rights of affected persons, high-risk AI accountability, and ANPD-led governance via the Sistema Nacional de Regulação e Governança de IA (SIA). Statutory compliance is the customer-organization responsibility. HUMMBL maps technical primitives to the bill's transparency, human-oversight, risk-management, documentation, and rights-of-affected-persons obligations. The LGPD (Lei 13.709/2018) already applies to AI systems processing personal data regardless of the Marco Legal's enactment.

## Scope summary

PL 2338/2023 applies to AI agents (suppliers, operators, and deployers) who develop, place on the market, or use AI systems in Brazil, including extraterritorial conduct with domestic impact. It excludes private non-economic use, R&D before market placement, and national-security/defense activities. The bill establishes three risk tiers: **excessive risk** (prohibited — social scoring, indiscriminate biometric surveillance, vulnerability exploitation), **high risk** (employment, credit/insurance, education, healthcare, criminal justice, essential public services, autonomous vehicles), and **non-high risk** (general transparency obligations). High-risk systems trigger impact assessments, human oversight, documentation, bias mitigation, and incident reporting. Penalties reach R$50,000,000 or 2% of annual revenue per infringement. The ANPD coordinates the SIA and may update the high-risk list.

## Obligations + coverage

### Rights of affected persons — general (Art. 5, Art. 9)

| Obligation | Coverage | Evidence |
|---|---|---|
| Right to prior information about interactions with AI systems | ✅ Transparency-notification primitive + interaction-log tuple (cross-ref EU AI Act Art. 50, LGPD Art. 20) | `hummbl_governance/audit_log.py`, `hummbl_governance/compliance_mapper.py` |
| Right to explanation of decisions, recommendations, or predictions | ✅ Explanation-disclosure generator + reasoning-trace capture (cross-ref EU AI Act Art. 13, Korea Art. 34) | `hummbl_governance/reasoning.py`, `hummbl_governance/compliance_mapper.py` |
| Right to contest decisions producing legal effects or significantly affecting interests | ✅ Contestation-request tuple + decision-review workflow substrate | `hummbl_governance/audit_log.py`, `hummbl_governance/compliance_mapper.py` |
| Right to human participation in AI decisions, considering context and state of the art | ✅ Human-oversight delegation token + intervention-record tuple (cross-ref EU AI Act Art. 14) | `hummbl_governance/delegation.py`, `hummbl_governance/identity.py` |
| Right to non-discrimination and correction of discriminatory biases (direct, indirect, illegal, or abusive) | ✅ Bias-detection hook + correction-request tuple + output-validation gate | `hummbl_governance/output_validator.py`, `hummbl_governance/audit_log.py` |
| Right to privacy and personal data protection per LGPD | ✅ Data-handling provenance tuple + audit-log retention (cross-ref LGPD, GDPR) | `hummbl_governance/audit_log.py`, `hummbl_governance/identity.py` |
| AI agents must clearly and accessibly inform procedures for exercising affected-person rights | 🟡 Partial: disclosure generator produces the notice; delivery channel and accessibility formatting are org tasks | `hummbl_governance/compliance_mapper.py` |

### Rights of affected persons — high-risk AI (Art. 6, Arts. 9–13)

| Obligation | Coverage | Evidence |
|---|---|---|
| Right to contest and request review of high-risk AI decisions, recommendations, or predictions | ✅ Contestation + review-request tuple with audit trail | `hummbl_governance/audit_log.py`, `hummbl_governance/compliance_mapper.py` |
| Right to request human intervention or review when decisions produce relevant legal effects or significantly affect interests | ✅ Human-intervention delegation token + oversight-record tuple | `hummbl_governance/delegation.py`, `hummbl_governance/identity.py` |
| Right to correction of incomplete, inaccurate, or outdated data used by AI systems (per LGPD Art. 18) | ✅ Data-correction-request tuple + provenance-update primitive | `hummbl_governance/audit_log.py`, `hummbl_governance/identity.py` |
| Right to anonymization, blocking, or elimination of unnecessary or non-compliant data | 🟡 Partial: deletion/anonymization-request tuple is generated; execution on underlying data store is org task | `hummbl_governance/audit_log.py` |
| Right to fair and isonomic treatment — prohibition of direct, indirect, illegal, or abusive discrimination | ✅ Non-discrimination gate + output-validation policy enforcement | `hummbl_governance/output_validator.py`, `hummbl_governance/capability_fence.py` |
| High-risk AI agents must inform procedures for exercising rights sufficiently, objectively, clearly, and accessibly | 🟡 Partial: disclosure generator produces content; accessibility and delivery are org tasks | `hummbl_governance/compliance_mapper.py` |

### Excessive risk — prohibited AI practices (Art. 5 substitutivo, Art. 18 list)

| Obligation | Coverage | Evidence |
|---|---|---|
| Prohibition on government social scoring systems | ✅ Capability-fence policy block + kill-switch enforcement on prohibited use patterns (cross-ref EU AI Act Art. 5) | `hummbl_governance/capability_fence.py`, `hummbl_governance/kill_switch.py` |
| Prohibition on indiscriminate biometric surveillance in public spaces (with law-enforcement exceptions) | ✅ Capability-fence biometric-scope restriction + circuit-breaker fast-fail | `hummbl_governance/capability_fence.py`, `hummbl_governance/circuit_breaker.py` |
| Prohibition on AI exploiting vulnerabilities of specific groups (children, elderly, persons with disabilities) causing harm | ✅ Vulnerability-exploitation detection gate + output-validator policy enforcement | `hummbl_governance/output_validator.py`, `hummbl_governance/capability_fence.py` |

### High-risk AI — agent obligations (Arts. 7–8, substitutivo CTIA)

| Obligation | Coverage | Evidence |
|---|---|---|
| Ensure safety of AI systems and rights of affected persons per regulatory requirements | ✅ Kill-switch 4-mode halt + circuit-breaker fast-fail + output-validation gate (cross-ref EU AI Act Art. 15, Korea Art. 32) | `hummbl_governance/kill_switch.py`, `hummbl_governance/circuit_breaker.py`, `hummbl_governance/output_validator.py` |
| Conduct preliminary risk assessment to determine risk level before market placement or use | ✅ Impact-assessment template + risk-classification tuple (cross-ref EU AI Act Art. 9, Korea Art. 34) | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/audit_log.py` |
| Implement risk management system to identify, assess, and mitigate risks throughout lifecycle | ✅ Risk-mgmt program substrate: identify + assess + treat tuple cycle (cross-ref NIST AI RMF, EU AI Act Art. 9) | `hummbl_governance/audit_log.py`, `hummbl_governance/coordination_bus.py` |
| Document tests assessing appropriate levels of reliability and safety | ✅ Test-evidence tuple + immutable audit-log retention | `hummbl_governance/audit_log.py`, `hummbl_governance/health_probe.py` |
| Document degree of human oversight contributing to results | ✅ Oversight-record tuple + delegation-token audit trail (cross-ref EU AI Act Art. 14) | `hummbl_governance/delegation.py`, `hummbl_governance/audit_log.py` |
| Implement measures to mitigate and prevent discriminatory biases | ✅ Bias-mitigation gate + output-validation policy + capability-fence enforcement | `hummbl_governance/output_validator.py`, `hummbl_governance/capability_fence.py` |
| Provide adequate information for interpretation of results and operation of AI systems (respecting trade secrecy) | ✅ Explanation-disclosure generator + reasoning-trace capture with secrecy-scoped redaction | `hummbl_governance/reasoning.py`, `hummbl_governance/compliance_mapper.py` |
| Human oversight of high-risk AI to prevent or minimize risks to rights and freedoms (Art. 8) | ✅ Human-oversight delegation token + intervention capability + halt authority (cross-ref EU AI Act Art. 14) | `hummbl_governance/delegation.py`, `hummbl_governance/kill_switch.py` |
| Implement alternative effective measures when human oversight is demonstrably impossible or disproportionate (Art. 8 §1) | 🟡 Partial: fallback-control tuple + automated-safeguard enforcement; demonstration of impossibility is org legal task | `hummbl_governance/circuit_breaker.py`, `hummbl_governance/audit_log.py` |
| Communicate serious incidents to respective sectoral authorities | 🟡 Partial: incident-detection + adverse-event tuple + report generator; regulatory submission is org task | `hummbl_governance/audit_log.py`, `hummbl_governance/compliance_mapper.py` |
| Transparency on management and governance policies for social and sustainable responsibility | 🟡 Partial: governance-policy documentation tuple generated; policy content and publication are org tasks | `hummbl_governance/compliance_mapper.py` |

### Risk classification and governance (Art. 15, Art. 18, Art. 45 SIA)

| Obligation | Coverage | Evidence |
|---|---|---|
| SIA regulates and updates the list of high-risk AI systems based on impact criteria (Art. 15) | ⚪ Boundary: regulatory-list maintenance by ANPD/SIA is institutional, not software-addressable | |
| Authority identifies new high-risk or excessive-risk hypotheses per criteria (Art. 18) | ⚪ Boundary: regulatory classification authority is institutional | |
| AI agents may conduct self-assessment to demonstrate compliance with safety, transparency, and ethical requirements | ✅ Self-assessment template + compliance-evidence export (cross-ref NIST AI RMF GOVERN) | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/audit_log.py` |
| ANPD coordinates the SIA with sectoral authorities and permanent cooperation council (Cria) | ⚪ Boundary: inter-agency institutional coordination is organizational | |
| Algorithmic impact assessment for high-risk systems | ✅ Impact-assessment template with human-rights + bias component (cross-ref EU AI Act Art. 27 FRIA, Korea Art. 35) | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/audit_log.py` |

### Liability, penalties, and enforcement (Arts. 40–44, substitutivo CTIA)

| Obligation | Coverage | Evidence |
|---|---|---|
| Supplier or operator liable for full reparation of patrimonial, moral, individual, or collective damage regardless of AI autonomy degree | ⚪ Boundary: civil liability determination is legal, not software-addressable | |
| Administrative fines up to R$50,000,000 or 2% of annual revenue per infringement, whichever is higher | ⚪ Boundary: administrative-penalty exposure is legal | |
| Cooperate with ANPD and sectoral authority inspections and investigations | 🟡 Partial: audit-log export + compliance-report generator supports inspection; cooperation act is org task | `hummbl_governance/audit_log.py`, `hummbl_governance/compliance_mapper.py` |
| Comply with corrective orders for safety, transparency, or rights violations | ⚪ Boundary: regulatory-order compliance is organizational | |

## Summary

| Section | Obligations | ✅ | 🟡 | ⚪ |
|---|---:|---:|---:|---:|
| Rights of affected persons — general (Art. 5, 9) | 7 | 6 | 1 | 0 |
| Rights of affected persons — high-risk (Art. 6, 9–13) | 6 | 4 | 2 | 0 |
| Excessive risk — prohibited (Art. 5 sub., 18) | 3 | 3 | 0 | 0 |
| High-risk AI — agent obligations (Arts. 7–8) | 11 | 7 | 4 | 0 |
| Risk classification + governance (Art. 15, 18, 45) | 5 | 2 | 0 | 3 |
| Liability, penalties, enforcement (Arts. 40–44) | 4 | 0 | 1 | 3 |
| **Totals** | **36** | **22** | **8** | **6** |

---

## Draft coverage summary (not public claim)

This matrix is internal starter material. It must not be used as public evidence that HUMMBL fulfills this framework until row counts, evidence commands, artifact paths, and boundary classifications are validated. PL 2338/2023 is not yet law; obligations reflect the Senate-approved text (Substitutivo CTIA, 10 December 2024) and may be modified by the Chamber of Deputies.

## Cross-references

- ADR: [`docs/adr/ADR-001-coverage-matrix-not-self-grade.md`](../adr/ADR-001-coverage-matrix-not-self-grade.md)
- Rights of affected persons overlap EU AI Act Arts. 13–14, 50 — see [`eu-ai-act.md`](./eu-ai-act.md)
- High-risk obligations overlap EU AI Act Art. 9 (risk management), Art. 14 (human oversight) — see [`eu-ai-act.md`](./eu-ai-act.md)
- Risk classification overlaps EU AI Act Arts. 5–6 — see [`eu-ai-act.md`](./eu-ai-act.md)
- Impact assessment overlaps EU AI Act Art. 27 (FRIA), Korea Art. 35 — see [`eu-ai-act.md`](./eu-ai-act.md), [`south-korea-ai-basic-act.md`](./south-korea-ai-basic-act.md)
- Human oversight overlaps Korea Art. 34, EU AI Act Art. 14 — see [`south-korea-ai-basic-act.md`](./south-korea-ai-basic-act.md)
- Personal data rights overlap LGPD (Lei 13.709/2018), GDPR — see [`gdpr.md`](./gdpr.md)
- Risk management overlaps NIST AI RMF — see [`nist-ai-rmf.md`](./nist-ai-rmf.md)
