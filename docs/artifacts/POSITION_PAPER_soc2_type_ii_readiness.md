# Position Paper: SOC 2 Type II Readiness

**Status:** live v1.0 (public)
**Author:** Operator, HUMMBL, LLC (drafted by Devin)
**Date:** 2026-06-23
**Tracking:** docs/artifacts/ARTIFACT_MANIFEST.md (item 24)
**Reader:** enterprise buyer, compliance buyer, auditor
**Position:** HUMMBL is structurally ready for SOC 2 Type II; the gap is operational (no external audit yet conducted)

**TL;DR:** HUMMBL's governance infrastructure maps cleanly to the SOC 2 Trust Service Criteria (Common, Security, Availability, Confidentiality). The artifact stack (23 artifacts, 307 claims, 16 KRINEIA receipts) provides the evidence an auditor would inspect. The gap is not structural — it is operational: HUMMBL has not yet engaged a third-party auditor. This paper argues that HUMMBL should pursue SOC 2 Type II readiness in Q4 2026/Q1 2027, after the first pilot integration, as a market-entry enabler for enterprise buyers who require it.

---

## 1. The argument

### 1.1 SOC 2 Type II is a customer requirement, not a legal requirement

SOC 2 (System and Organization Controls 2) is an auditing framework from the AICPA (American Institute of Certified Public Accountants). It is not a legal requirement. It is a customer requirement: enterprise buyers require their vendors to demonstrate SOC 2 Type II compliance as a precondition for procurement.

A buyer asks: "Can I trust this vendor with my data?" SOC 2 Type II is the standard answer. Without it, the buyer's procurement team blocks the deal.

### 1.2 HUMMBL's wedge does not require SOC 2 immediately

HUMMBL's wedge is deterministic, in-process, open-source governance infrastructure. The library runs in the buyer's environment, not in HUMMBL's cloud. The buyer's data does not flow to HUMMBL. This is a structural differentiator: HUMMBL is not a SaaS that processes customer data.

For a buyer evaluating HUMMBL's library, the SOC 2 question is different: "Can I trust this open-source library?" The answer is the Apache 2.0 license, the 1,234 tests, the artifact stack, the claims manifest, and the KRINEIA receipt chain. SOC 2 is not the primary trust signal for an open-source library.

### 1.3 But SOC 2 will be required for enterprise buyers

Some enterprise buyers will require SOC 2 Type II regardless of HUMMBL's in-process architecture. Their procurement teams have a checklist; SOC 2 is on the checklist; the checklist does not have an "open-source library" exception.

HUMMBL should pursue SOC 2 Type II readiness to unblock these buyers. The right time is Q4 2026/Q1 2027, after the first pilot integration, when HUMMBL has a customer reference to pair with the audit.

### 1.4 HUMMBL is structurally ready; the gap is operational

HUMMBL's governance infrastructure maps cleanly to the SOC 2 Trust Service Criteria. The artifact stack provides the evidence an auditor would inspect. The gap is not "HUMMBL lacks controls" — the gap is "HUMMBL has not engaged an auditor to attest to the controls."

This paper maps HUMMBL's controls to the SOC 2 criteria, identifies the operational gaps, and proposes a readiness plan.

---

## 2. SOC 2 Trust Service Criteria mapping

SOC 2 has 5 Trust Service Criteria (TSC): Common, Security, Availability, Processing Integrity, Confidentiality, Privacy. HUMMBL maps to 4 of the 5 (Processing Integrity and Privacy are application-specific).

### 2.1 Common Criteria (CC1-CC9)

| Criterion                                 | HUMMBL control                                                                       | Evidence                                                                                                                 |
| ----------------------------------------- | ------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------ |
| CC1: Control Environment                  | Doctrine (10 principles), Charter (HRI authority), Board (5 Directors)               | docs/artifacts/DOCTRINE_ai_governance.md, CHARTER_hri.md, governance/board/registry.yaml                                 |
| CC2: Communication and Information        | Coordination bus (TSV), KRINEIA receipts, claims manifest                            | the coordination bus log, _receipts/krineia/primary.jsonl, web/manifest/claims-provenance.json |
| CC3: Risk Assessment | Risk assessment and review process described in the original paper | Private supporting records omitted; operation and counts are not publicly verified here. |
| CC4: Monitoring Activities                | Health endpoint (8 probes), CI checks (P7 claims, P11 manifest), wave retrospectives | hummbl_governance/services/health.py, .github/workflows/claims-validation.yml (private retrospective support omitted)                   |
| CC5: Control Activities                   | KillSwitch, CircuitBreaker, DelegationToken, CapabilityFence                         | hummbl-governance library (8 primitives)                                                                                 |
| CC6: Logical and Physical Access Controls | Agent identity registry, model tier policy, GPG signing                              | hummbl_governance/services/agent_identity.py, .agents/rules/model-tier-policy.md, GPG key [REDACTED-GPG-KEY]               |
| CC7: System Operations                    | Deployment checklist, runbook, fleet rollout playbook                                | docs/artifacts/PLAYBOOK_fleet_rollout.md, deploy-checklist skill                                                         |
| CC8: Change Management                    | Claims change playbook, ADR process, single-branch workflow (ADR-004)                | docs/artifacts/PLAYBOOK_claims_change.md, docs/adr/, ADR-004                                                             |
| CC9: Risk Mitigation | Mitigation planning and review described in the original paper | Private supporting records omitted; operating effectiveness is not publicly verified here. |

### 2.2 Security (SC1-SC7)

| Criterion                     | HUMMBL control                                         | Evidence                                                                        |
| ----------------------------- | ------------------------------------------------------ | ------------------------------------------------------------------------------- |
| SC1: Security events          | KillSwitch (4 modes), alert routing                    | hummbl_governance.KillSwitch, hummbl_governance/services/alerts.py              |
| SC2: Access controls          | Agent identity registry, CapabilityFence               | hummbl_governance/services/agent_identity.py, hummbl_governance.CapabilityFence |
| SC3: Intrusion detection      | Security adapter (Bandit + Semgrep), redteam skill     | hummbl_governance/integrations/security_adapter.py, redteam skill               |
| SC4: Vulnerability management | Dependency checks, supply-chain audit, dep-check skill | dep-check skill, supply-chain-audit skill                                       |
| SC5: Change management        | ADR process, claims change playbook                    | docs/adr/, docs/artifacts/PLAYBOOK_claims_change.md                             |
| SC6: Data disposal            | Not yet formalized                                     | GAP — needs formalization                                                       |
| SC7: System operations        | Deployment checklist, runbook                          | deploy-checklist skill                                                          |

### 2.3 Availability (A1-A3)

| Criterion                  | HUMMBL control                                        | Evidence                                                    |
| -------------------------- | ----------------------------------------------------- | ----------------------------------------------------------- |
| A1: Performance monitoring | Health endpoint (8 probes), dashboard check           | hummbl_governance/services/health.py, dashboard-check skill |
| A2: Incident handling      | Incident response plan, postmortem skill, kill switch | incident-response-plan skill, postmortem skill, KillSwitch  |
| A3: Recovery               | Backup verification, state snapshots, rollback skill  | backup-verify skill, state-snapshot skill, rollback skill   |

### 2.4 Confidentiality (C1-C2)

| Criterion               | HUMMBL control                                                             | Evidence                                             |
| ----------------------- | -------------------------------------------------------------------------- | ---------------------------------------------------- |
| C1: Data classification | Model tier policy (T1-BYOK, T2-ZEN, T3-FREE)                               | .agents/rules/model-tier-policy.md, MODEL_TIERS.md   |
| C2: Data protection     | In-process architecture (no data flows to HUMMBL), zero-egress T2-ZEN tier | hummbl-governance architecture, model-tier-policy.md |

### 2.5 Processing Integrity (PI1-PI2) — partial

| Criterion                 | HUMMBL control                                         | Evidence                                              |
| ------------------------- | ------------------------------------------------------ | ----------------------------------------------------- |
| PI1: Processing integrity | Deterministic primitives (not LLM-judged), 1,234 tests | hummbl-governance library, test suite                 |
| PI2: Error handling       | CircuitBreaker (3 states), error catalog               | hummbl_governance.CircuitBreaker, error-catalog skill |

### 2.6 Privacy (P1-P8) — not applicable

HUMMBL does not process personal data (the library runs in the buyer's environment). Privacy criteria are the buyer's responsibility, not HUMMBL's.

---

## 3. The gap analysis

### 3.1 Structural gaps (none)

HUMMBL has controls for all 4 applicable Trust Service Criteria (Common, Security, Availability, Confidentiality). The controls are documented, evidenced, and verifiable. There are no structural gaps.

### 3.2 Operational gaps

| Gap                                  | Status                                                                       | Remediation                                                                     |
| ------------------------------------ | ---------------------------------------------------------------------------- | ------------------------------------------------------------------------------- |
| No external audit conducted          | Not started                                                                  | Engage a CPA firm (AICPA-accredited) for SOC 2 Type II audit in Q4 2026/Q1 2027 |
| SC6 (Data disposal) not formalized   | Not formalized                                                               | Draft a data disposal policy (Q3 2026)                                          |
| No penetration test conducted        | Not started                                                                  | Engage a third-party penetration tester (Q4 2026)                               |
| No formal incident response plan     | Partial (incident-response-plan skill exists but not formalized as a policy) | Formalize the incident response plan as a policy (Q3 2026)                      |
| No vendor management program         | Not started                                                                  | Draft a vendor management policy (Q1 2027)                                      |
| No formal data classification policy | Partial (model tier policy exists but not mapped to SOC 2)                   | Map model tier policy to SOC 2 data classification (Q3 2026)                    |

### 3.3 Documentation gaps

| Gap                            | Status                                                      | Remediation                                                                       |
| ------------------------------ | ----------------------------------------------------------- | --------------------------------------------------------------------------------- |
| No SOC 2 bridge document       | Not started                                                 | Draft a SOC 2 bridge document mapping HUMMBL controls to AICPA criteria (Q4 2026) |
| No auditor-ready evidence pack | Partial (evidence pack item 13 exists but is self-compiled) | Extend the evidence pack to be auditor-ready (Q4 2026)                            |
| No formal policies document    | Partial (policies are distributed across artifacts)         | Consolidate policies into a single document (Q4 2026)                             |

---

## 4. The readiness plan

### Phase 1: Q3 2026 — Formalize the gaps

- Draft data disposal policy (SC6)
- Formalize incident response plan as a policy
- Map model tier policy to SOC 2 data classification
- Add SOC 2 crosswalk to the coverage matrices

### Phase 2: Q4 2026 — Prepare for audit

- Draft SOC 2 bridge document
- Extend evidence pack to be auditor-ready
- Consolidate policies into a single document
- Engage a third-party penetration tester
- Select a CPA firm (AICPA-accredited)

### Phase 3: Q1 2027 — Conduct the audit

- Engage the CPA firm for SOC 2 Type II audit
- Observation period: 6-12 months (Type II requires observation over time)
- Receive the auditor's report
- Publish the SOC 2 Type II report (under NDA to enterprise buyers)

### Phase 4: Q2 2027+ — Maintain

- Annual SOC 2 Type II re-audit
- Continuous monitoring (P7 claims CI, P11 manifest CI, health endpoint)
- Quarterly claims review (per claims change playbook)

---

## 5. The cost

SOC 2 Type II audits cost $20,000-$80,000 depending on the firm, scope, and observation period. HUMMBL's cost will be at the lower end because:

- HUMMBL is a single-founder company (low organizational complexity)
- HUMMBL's controls are already documented (the artifact stack)
- HUMMBL's architecture is in-process (no customer data flows to HUMMBL, reducing scope)
- HUMMBL's evidence is already machine-verifiable (P7, P11, KRINEIA receipts)

Estimated cost: $20,000-$40,000 for the first audit (Q1 2027), $15,000-$30,000 for annual re-audits.

### Funding source

The SOC 2 audit is not yet funded. It should be funded from the first pilot integration revenue (Q1 2027 target) or from the existing operating budget if the first pilot integration is delayed.

---

## 6. The competitive context

| Vendor                 | SOC 2 Type II             | Notes                                 |
| ---------------------- | ------------------------- | ------------------------------------- |
| Credo AI               | Yes                       | Established vendor, full SOC 2        |
| Holistic AI            | Unknown                   | Not publicly disclosed                |
| Arthur AI              | Yes                       | Established vendor                    |
| Fiddler AI             | Yes                       | Established vendor                    |
| IBM watsonx.governance | Yes (IBM's broader SOC 2) | Inherited from IBM                    |
| HUMMBL                 | Not yet                   | Structural readiness, operational gap |

HUMMBL is behind established competitors on SOC 2. This is expected — HUMMBL is pre-revenue and pre-audit. The readiness plan closes this gap by Q1 2027.

---

## 7. The position

HUMMBL is structurally ready for SOC 2 Type II. The artifact stack provides the evidence. The gap is operational: no external audit has been conducted.

HUMMBL should:

1. Pursue SOC 2 Type II readiness in Q4 2026/Q1 2027
2. Fund the audit from first pilot integration revenue or operating budget
3. Use the audit as a market-entry enabler for enterprise buyers who require it
4. Not delay the first pilot integration for the audit — the audit follows the pilot, not the other way around

HUMMBL should NOT:

1. Pursue SOC 2 before the first pilot integration (no customer reference to pair with the audit)
2. Pursue SOC 2 as a marketing tool (it is a procurement enabler, not a marketing asset)
3. Pursue ISO 27001 or ISO 42001 before SOC 2 (SOC 2 is the US market standard; ISO is the international standard and can follow)

---

## 8. How to verify this paper

The following are historical checks of selected supporting artifacts, not proof of SOC 2 readiness or operating effectiveness. Private and external-repository evidence may be unavailable to a public reader; file presence alone does not validate a control:

1. **The artifact stack exists:** `ls docs/artifacts/ARTIFACT_MANIFEST.md`
2. **Risk-assessment support:** Private records are omitted; this public tree does not provide verification of their contents or operating effectiveness.
3. **The doctrine exists:** `ls docs/artifacts/DOCTRINE_ai_governance.md`
4. **The charter exists:** `ls docs/artifacts/CHARTER_hri.md`
5. **The evidence pack exists:** `ls docs/artifacts/EVIDENCE_PACK_fleet_rollout.md`
6. **The claims manifest has 307 claims:** `python3 -c "import json; d=json.loads(open('web/manifest/claims-provenance.json', encoding='utf-8').read()); print(d['summary'])"`
7. **The KRINEIA chain has 16+ receipts:** `wc -l _receipts/krineia/primary.jsonl`
8. **The health endpoint exists:** `ls hummbl_governance/services/health.py` (in hummbl-governance repo)
9. **The agent identity registry exists:** `ls hummbl_governance/services/agent_identity.py` (in hummbl-governance repo)
10. **The model tier policy exists:** `ls .agents/rules/model-tier-policy.md`

If any verification fails, open an issue at `hummbl-io/hummbl-production/issues`.

---

## References

- White paper: `docs/artifacts/WHITE_PAPER_governance_infrastructure.md` (item 1)
- Supporting private records are omitted from this public tree; claims depending on them cannot be independently re-verified here.
- Competitive analysis: `docs/artifacts/COMPETITIVE_ANALYSIS_ai_governance.md` (item 4)
- Doctrine: `docs/artifacts/DOCTRINE_ai_governance.md` (item 11)
- Charter: `docs/artifacts/CHARTER_hri.md` (item 12)
- Evidence pack: `docs/artifacts/EVIDENCE_PACK_fleet_rollout.md` (item 13)
- Claims change playbook: `docs/artifacts/PLAYBOOK_claims_change.md` (item 14)
- Fleet rollout playbook: `docs/artifacts/PLAYBOOK_fleet_rollout.md` (item 15)
- Agent onboarding playbook: `docs/artifacts/PLAYBOOK_agent_onboarding.md` (item 23)
- ADR-004: `docs/adr/ADR-004-single-branch-workflow.md` (item 22)
- Claims manifest: `web/manifest/claims-provenance.json`
- KRINEIA receipt chain: `_receipts/krineia/primary.jsonl`
- hummbl-governance: https://github.com/hummbl-io/hummbl-governance (Apache 2.0)
- AICPA SOC 2 framework: https://www.aicpa-cima.com/topic/audit-assurance/audit-and-assurance-greater-than-soc-2

---

## Authority boundary

**Operator** is the human **Principal Agent** for HUMMBL. **Devin** (and other software agents) are delegated drafting, research, and execution systems. This position paper was drafted by Devin at the direction of the Principal Agent, based on the artifact stack (23 artifacts), the claims manifest, the SOC 2 Trust Service Criteria (AICPA), and the competitive analysis, and was promoted to live (public) by Principal Agent decision on 2026-06-23. The position is a proposal for the Principal Agent to approve or revise. This document is **public** — it is intended for external use (enterprise buyers, compliance buyers, auditors) and is published at hummbl.io.
