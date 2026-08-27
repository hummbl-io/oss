# G7 Hiroshima AI Process — International Code of Conduct Coverage Matrix — HUMMBL

**Standard**: G7 Hiroshima AI Process International Code of Conduct for Organizations Developing Advanced AI Systems (October 30, 2023)
**Source**: https://www.mofa.go.jp/files/100573472.pdf
**Last reviewed**: 2026-05-14
**Reviewer**: claude-code (host-C) per [ADR-001](../adr/ADR-001-coverage-matrix-not-self-grade.md)
**HUMMBL version**: hummbl-governance v1.2.2

## Boundary disclaimer

The G7 Hiroshima Code of Conduct is **voluntary** guidance for organizations developing advanced AI systems (including GPAI/foundation models). No certification body. Adherence is self-declared or third-party-assessed via consulting engagements.

## Structure

11 principles directed at organizations developing the most advanced AI systems. Each principle = a "should" obligation.

## Coverage matrix

| # | Principle | Coverage | Evidence |
|---|---|---|---|
| 1 | Take appropriate measures throughout AI lifecycle to identify, evaluate, mitigate risks (including pre-deployment, throughout deployment) | ✅ Lifecycle tuple + `INTENT` + adverse-event + risk-treatment + monitoring; risk-register integration per Krineia connector spec (cross-ref NIST AI RMF MAP/MEASURE/MANAGE, EU AI Act Art. 9) | `hummbl_governance/lifecycle.py`, `hummbl_governance/audit_log.py`, `hummbl_governance/coordination_bus.py` |
| 2 | Identify + mitigate vulnerabilities, incidents, patterns of misuse after deployment (including market) | ✅ Vulnerability tuple + incident-detection + post-market monitoring (cross-ref EU AI Act Art. 72-73) | `hummbl_governance/audit_log.py`, `hummbl_governance/coordination_bus.py` |
| 3 | Publicly report advanced AI systems' capabilities, limitations, domains of appropriate + inappropriate use | ✅ Capability-disclosure generator (cross-ref EU AI Act Art. 13, Singapore Generative AI Framework Dimension 3) | `hummbl_governance/compliance_mapper.py` |
| 4 | Work towards responsible information sharing + incident reporting among orgs developing advanced AI systems | 🟡 Partial: information-sharing tuples + incident-disclosure; participation in industry forums is org task | |
| 5 | Develop, implement, disclose AI governance + risk management policies based on risk-based approach | ✅ Risk-based governance substrate: risk-tier classification + treatment-tier mapping (cross-ref NIST AI RMF) | `hummbl_governance/audit_log.py`, `hummbl_governance/schema_validator.py` |
| 6 | Invest in + implement robust security controls — physical security, cybersecurity, insider threats | 🟡 Partial: cybersecurity covered (cross-ref OWASP LLM Top 10, NIST CSF, ISO 27001 A.8); physical + insider-threat are org programs | |
| 7 | Develop + deploy reliable content authentication + provenance mechanisms — watermarking, identification | 🟡 Partial: content-provenance tuples shipped. C2PA integration admitted as Tier-2 dependency (`[c2pa-mcp]` pyproject extra) per `hummbl_governance/docs/research/2026-05-01_adr-001-admission-c2pa-stack.md`; implementation per ADR-GOV-001 spec is planned, not yet shipped. Customer integrates via the extra today (cross-ref Singapore Dimension 7). | |
| 8 | Prioritize research to mitigate societal, safety, security risks; prioritize investment in effective mitigation measures | ⚪ Boundary: research-program is org strategy | |
| 9 | Prioritize development of advanced AI systems to address world's greatest challenges (climate, health, education) | ⚪ Boundary: strategic direction | |
| 10 | Advance development + adoption of international technical standards | 🟡 Partial: standards-adoption is org strategy; this matrix index = HUMMBL adoption | |
| 11 | Implement appropriate data input measures + protections for personal data + intellectual property | ✅ Data-input controls (cross-ref GDPR matrix); IP-respect tuple type for training-data provenance | `hummbl_governance/audit_log.py`, `hummbl_governance/schema_validator.py` |

## Summary

| Status | Count |
|---|---|
| ✅ Fulfilled | 5 |
| 🟡 Partial | 4 |
| ⚪ Boundary | 2 |
| **Total** | **11** |

---

## Draft coverage summary (not public claim)

This matrix is internal starter material. It must not be used as public evidence that HUMMBL fulfills this framework until row counts, evidence commands, artifact paths, and boundary classifications are validated.

Counts above (5 ✅ / 4 🟡 / 2 ⚪) reflect the draft row classification after the c2pa Tier-2 admitted-dependency correction; do not headline these numbers externally until validation per ADR-001 evidence invariant.

## Cross-references

- ADR: [`docs/adr/ADR-001-coverage-matrix-not-self-grade.md`](../adr/ADR-001-coverage-matrix-not-self-grade.md)
- Significant overlaps with EU AI Act (lifecycle, post-market), NIST AI RMF (risk-based approach), OWASP LLM Top 10 (security), Singapore IMDA (content provenance, governance) — see respective matrices
