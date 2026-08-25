# Singapore IMDA Model AI Governance Framework + Agentic AI Coverage Matrix — HUMMBL

**Standard**: Singapore Model AI Governance Framework (2nd ed., 2020) + Model AI Governance Framework for Generative AI (May 2024) + IMDA / AI Verify guidance
**Source**: https://www.imda.gov.sg/-/media/imda/files/sgs/-/media/imda/files/programmes/ai-verify/model-ai-governance-framework-for-generative-ai
**Last reviewed**: 2026-05-14
**Reviewer**: claude-code (huxley) per [ADR-001](../adr/ADR-001-coverage-matrix-not-self-grade.md)
**HUMMBL version**: hummbl-governance v0.8.0

## Boundary disclaimer

The Singapore Model AI Governance Framework is **voluntary** guidance. No certification body. AI Verify is an open-source testing framework. This matrix maps HUMMBL primitives to the 9 dimensions of the Generative AI framework and the broader Model AI Governance Framework's 4 key areas.

## Structure — Model AI Governance Framework (4 key areas)

| Area | Key questions | Coverage | Evidence |
|---|---|---|---|
| Internal governance structures + measures | Who is accountable? Roles + responsibilities? Risk management? Monitoring? | 🟡 Partial: DCT/DCTX captures roles; org structure is task | |
| Determining the level of human involvement | Risk-based human oversight, from human-in-the-loop to human-out-of-the-loop | ✅ INTENT + DCT + kill_switch primitives (cross-ref EU AI Act Art. 14) | `hummbl_governance/delegation.py`, `hummbl_governance/kill_switch.py` |
| Operations management | Data preparation, model selection, training, validation, deployment, monitoring | ✅ Lifecycle tuple chain (cross-ref ISO 42001 A.6) | `hummbl_governance/lifecycle.py`, `hummbl_governance/audit_log.py` |
| Stakeholder interaction + communication | Transparency, explainability, communication | 🟡 Partial: transparency + explainability primitives; org communication is task | |

## Structure — Generative AI Framework (9 dimensions)

| Dimension | Coverage | Evidence |
|---|---|---|
| 1. Accountability | 🟡 Partial: DCTX delegation chain = accountability allocation; org policy completes | |
| 2. Data | ✅ Dataset tuples + provenance chain + quality primitives (cross-ref ISO 42001 A.7) | `hummbl_governance/audit_log.py`, `hummbl_governance/schema_validator.py` |
| 3. Trusted Development + Deployment | ✅ Lifecycle tuple + V&V + deployment tuples + signed audit trail | `hummbl_governance/lifecycle.py`, `hummbl_governance/audit_log.py` |
| 4. Incident Reporting | ✅ Incident tuple + notification SLA + escalation (cross-ref EU AI Act Art. 73) | `hummbl_governance/audit_log.py`, `hummbl_governance/coordination_bus.py` |
| 5. Testing + Assurance | ✅ 927 governance tests + redteam tuples + safety-eval primitives | `.github/workflows/ci.yml`, `hummbl_governance/audit_log.py` |
| 6. Security | ✅ HMAC-SHA256 delegation tokens + Bandit/Semgrep + pip-audit blocking | `hummbl_governance/delegation.py`, `.github/workflows/ci.yml` |
| 7. Content Provenance | 🟡 Content-provenance tuples shipped. C2PA integration admitted as Tier-2 dependency (`[c2pa-mcp]` pyproject extra); implementation per ADR-GOV-001 spec is planned, not yet shipped. Customer integrates via the extra today. | |
| 8. Safety + Alignment | 🟡 Partial: Alignment-eval tuples + RLHF-evidence primitives; alignment-evaluation methodology is research | |
| 9. AI for Public Good | ⚪ Boundary: Civic-impact framing is org strategy | |

## Summary

| Component | Items | ✅ | 🟡 | ⚪ |
|---|---|---|---|---|
| Model AI Governance Framework (4 areas) | 4 | 2 | 2 | 0 |
| Generative AI Framework (9 dimensions) | 9 | 5 | 3 | 1 |
| **Totals** | **13** | **7** | **5** | **1** |

---

## Draft coverage summary (not public claim)

This matrix is internal starter material. It must not be used as public evidence that HUMMBL fulfills this framework until row counts, evidence commands, artifact paths, and boundary classifications are validated.

Counts above (7 ✅ / 5 🟡 / 1 ⚪) reflect the draft row classification after the c2pa Tier-2 admitted-dependency correction; do not headline these numbers externally until validation per ADR-001 evidence invariant.

## Cross-references

- ADR: [`docs/adr/ADR-001-coverage-matrix-not-self-grade.md`](../adr/ADR-001-coverage-matrix-not-self-grade.md)
- Content-provenance overlap with C2PA — admitted Tier-2 dependency, implementation per `hummbl_governance/docs/research/2026-05-01_c2pa-receipt-mcp-spec.md` spec, not yet shipped
- Significant overlap with EU AI Act + NIST AI RMF + ISO 42001 — see those matrices
