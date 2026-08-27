# Position Paper: HUMMBL EU AI Act Readiness

**Status:** live v1.0 (public)
**Author:** Operator, HUMMBL, LLC
**Date:** 2026-06-23
**Tracking:** docs/artifacts/ARTIFACT_MANIFEST.md (item 9)
**Reader:** compliance buyer at an EU-operating AI-native team evaluating governance vendors for EU AI Act readiness
**Decision:** whether to engage HUMMBL for EU AI Act readiness work

**TL;DR:** The EU AI Act's high-risk obligations (Annex III) were originally enforceable from August 2, 2026. The 2026 Digital Omnibus agreement (May 2026, Parliament-endorsed June 16, 2026) extends this to **December 2, 2027**, subject to formal Council adoption and Official Journal publication. Until then, August 2, 2026 remains the legally binding date. HUMMBL provides deterministic, in-process evidence for 10 of the core operational articles (Art. 9–17, 19) that a high-risk AI system provider must satisfy. This paper maps HUMMBL's primitives to those articles, shows what HUMMBL covers and what it does not, and explains why a compliance buyer should choose HUMMBL for the technical-evidence layer of their EU AI Act readiness program.

---

## 1. The deadline

The EU AI Act (Regulation (EU) 2024/1689) was published 12 July 2024, entered into force 1 August 2024, and phases in over 36 months. The most consequential deadline for most AI-native teams is the enforcement of obligations for high-risk AI systems (Annex III use cases).

**Original date:** August 2, 2026 (Article 113(a)).

**Current expected date:** December 2, 2027 — extended by the 2026 Digital Omnibus (political agreement May 2026, Parliament endorsement June 16, 2026). The Council must formally adopt and publish in the Official Journal before the extension takes effect. Until then, August 2, 2026 remains the legally binding date.

After the applicable deadline, a provider placing a high-risk AI system on the EU market without complying with Articles 8–17 (the operational requirements) is exposed to penalties under Article 99: up to €35 million or 7% of worldwide annual turnover, whichever is higher.

**HUMMBL's public stance:** The site (hummbl.io) uses December 2, 2027 as the target date, hedged with "subject to formal adoption." Internal materials should match this framing or explicitly note the divergence.

### What counts as "high-risk"

Annex III lists 8 areas of high-risk use:

1. Biometrics (remote identification, biometric categorization)
2. Critical infrastructure (safety components of road, rail, water, energy)
3. Education and vocational training (admissions, scoring, proctoring)
4. Employment and worker management (recruitment, promotion, performance)
5. Essential services (credit scoring, insurance pricing, public benefits)
6. Law enforcement (polygraphs, risk assessments, evidence reliability)
7. Migration, asylum, and border control (eligibility, security risk)
8. Administration of justice and democratic processes

If your AI system is in any of these 8 areas and is placed on the EU market, you are a high-risk provider. The obligations apply to you on August 2, 2026.

### What "compliance" means

A high-risk provider must:

1. **Establish a risk management system** (Art. 9) — continuous, iterative, across the lifecycle
2. **Ensure data governance** (Art. 10) — training, validation, test sets; bias examination
3. **Maintain technical documentation** (Art. 11) — per Annex IV, comprehensive
4. **Keep automatic records** (Art. 12) — logs over the lifetime of the system
5. **Ensure transparency** (Art. 13) — instructions for use, interpretability
6. **Provide human oversight** (Art. 14) — design for effective human supervision
7. **Ensure accuracy, robustness, cybersecurity** (Art. 15) — throughout lifecycle
8. **Meet provider obligations** (Art. 16) — quality management, cooperation
9. **Maintain a quality management system** (Art. 17) — documented, auditable
10. **Automatically generate logs** (Art. 19) — in a format usable by the deployer

A provider must also undergo a conformity assessment (Art. 43): either internal control (Annex VI) or, for biometric identification systems, Notified Body assessment (Annex VII). The provider then issues an EU declaration of conformity (Art. 47) and affixes the CE mark.

This is a lot. And most of it is not a software problem — it is a documentation, process, and evidence problem. That is where HUMMBL fits.

---

## 2. What HUMMBL provides

HUMMBL is a Python library that emits deterministic, in-process evidence for the technical-evidence obligations of Articles 9, 10, 11, 12, 13, 14, 15, 16, 17, and 19. It is not a Notified Body. It does not issue conformity declarations. It does not affix CE marks. It provides the **technical evidence interface** that supports either conformity assessment path.

### The mapping

HUMMBL maintains a coverage matrix in `hummbl-io/hummbl-governance/docs/coverage/eu-ai-act.md` that maps every article in the EU AI Act (all 113 articles, all 13 annexes) to either a HUMMBL primitive that addresses it, a partial-coverage description, or an explicit boundary statement. No article is silently excluded.

The summary:

| Chapter                     | Articles | ✅ Fulfilled | 🟡 Partial | ⚪ Boundary | ⛔ Out of scope |
| --------------------------- | -------- | ------------ | ---------- | ----------- | --------------- |
| I — General provisions      | 1–4      | 0            | 0          | 4           | 0               |
| II — Prohibited practices   | 5        | 0            | 1          | 0           | 0               |
| III — High-risk systems     | 6–49     | 18           | 7          | 19          | 0               |
| IV — Transparency           | 50       | 1            | 1          | 0           | 0               |
| V — GPAI models             | 51–56    | 0            | 2          | 4           | 0               |
| VI — Innovation measures    | 57–63    | 0            | 1          | 5           | 0               |
| VII — Governance            | 64–70    | 0            | 0          | 7           | 0               |
| VIII — EU database          | 71       | 0            | 1          | 0           | 0               |
| IX — Post-market monitoring | 72–94    | 4            | 5          | 14          | 0               |
| X — Codes of conduct        | 95       | 0            | 1          | 0           | 0               |
| XI–XIII                     | 96–113   | 0            | 0          | 15          | 0               |
| **Totals**                  | **113**  | **23**       | **19**     | **71**      | **0**           |

The 23 ✅ are articles where a HUMMBL primitive implements the control and a runnable evidence artifact exists. The 19 🟡 are articles where HUMMBL provides part of the control and the customer organization provides the rest. The 71 ⚪ are articles that are organizational, regulatory, or institutional — not addressable by a software library. The 0 ⛔ means no article is silently excluded.

### The load-bearing articles (Art. 9–17, 19)

These are the articles a high-risk provider must satisfy operationally. Here is how HUMMBL maps to each:

| Article | Requirement                                            | HUMMBL primitive                                                                                                                                                                                     | Evidence                                                                                                      |
| ------- | ------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------- |
| Art. 9  | Risk management system (continuous, iterative)         | Governance bus (every agent action emits a tuple); circuit breaker + kill switch for residual risk control                                                                                           | `governance_bus` tuples with `INTENT`, `DCT`, adverse-event types; `circuit_breaker` and `kill_switch` events |
| Art. 10 | Data and data governance                               | `ATTEST` and `EVIDENCE` tuple types for dataset provenance, transformation chain, bias examination                                                                                                   | Dataset-card schema; governance bus `DATASET` tuple type                                                      |
| Art. 11 | Technical documentation (Annex IV)                     | `compliance_mapper --framework eu-ai-act --export annex-iv` generates Annex IV documentation from compliance-mapper output                                                                           | Live-regenerated on every release                                                                             |
| Art. 12 | Record-keeping (automatic logs over lifetime)          | Append-only governance bus (JSONL) + cognition ledger (JSONL); every agent action, every delegation, every kill-switch event recorded; retention configurable, default 5+ years aligned with Art. 19 | `_state/coordination/messages.tsv`, `_state/cognition/ledger.jsonl`                                           |
| Art. 13 | Transparency (instructions for use, interpretability)  | `INTENT` tuples capture purpose and objectives; delegation chain (`DCT`) makes the decision path legible                                                                                             | `INTENT` tuple type; `DCT` chain                                                                              |
| Art. 14 | Human oversight                                        | Kill switch (4 modes: DISENGAGED → HALT_NONCRITICAL → HALT_ALL → EMERGENCY); delegation token expiry; circuit breaker automatic halt                                                                 | `kill_switch_core.py`, `delegation_token.py`, `circuit_breaker.py`                                            |
| Art. 15 | Accuracy, robustness, cybersecurity                    | 1,234 governance tests (per-primitive coverage); circuit breaker for robustness; HMAC-SHA256 signed delegation tokens for integrity                                                                  | `pytest` corpus; `circuit_breaker.py`; `delegation_token.py`                                                  |
| Art. 16 | Provider obligations (quality management, cooperation) | Governance bus provides the evidence trail for QMS audits; compliance mapper generates the report on demand                                                                                          | `compliance_mapper.py --framework eu-ai-act`                                                                  |
| Art. 17 | Quality management system                              | Same as Art. 16 — the governance bus is the QMS evidence backbone                                                                                                                                    | `governance_bus.py`                                                                                           |
| Art. 19 | Automatically generated logs                           | Governance bus is automatically generated (every agent action); format is structured JSONL, usable by deployer                                                                                       | `governance_bus.py`                                                                                           |

### How to use it

A compliance buyer integrates HUMMBL into their AI system's runtime. Every agent action emits a governance bus tuple. Every delegation emits a signed delegation token. Every kill-switch event and circuit-breaker transition is recorded. The compliance mapper reads the bus and generates an EU AI Act report on demand:

```python
from hummbl_governance import ComplianceMapper

mapper = ComplianceMapper(governance_dir="_state/coordination")
report = mapper.generate_eu_ai_act_report(days=30)
print(report.to_json())
```

The report contains, for each of Art. 9, 10, 11, 12, 13, 14, 15, 16, 17, 19, the evidence tuples from the last 30 days that satisfy that article's requirement. This is the technical evidence you bring to your conformity assessment.

---

## 3. What HUMMBL does not provide

HUMMBL is honest about its boundary. This is not a "HUMMBL makes you EU AI Act compliant" claim. HUMMBL provides the **technical evidence layer**. The compliance buyer still needs:

1. **A Notified Body or internal control assessment** (Art. 43) — HUMMBL is not a Notified Body. The provider chooses the assessment path; HUMMBL provides the evidence either path requires.
2. **An EU declaration of conformity** (Art. 47) — the provider issues this, not HUMMBL.
3. **CE marking** — the provider affixes this, not HUMMBL.
4. **Registration in the EU database** (Art. 71) — the provider registers, not HUMMBL.
5. **A quality management system** (Art. 17) — HUMMBL provides the evidence backbone; the QMS itself is the provider's organizational process.
6. **Human oversight organizational measures** (Art. 14) — HUMMBL provides the technical kill switch; the organizational oversight process is the provider's.
7. **Bias examination methodology** (Art. 10) — HUMMBL records the evidence that bias examination happened; the methodology is the provider's.
8. **Post-market monitoring plan** (Art. 72) — HUMMBL provides the monitoring primitives; the plan is the provider's.

The 71 ⚪ boundary articles in the coverage matrix are mostly these: organizational, regulatory, or institutional obligations that no software library can satisfy. HUMMBL's honesty about this boundary is itself a governance feature. A vendor that claims to "make you compliant" is lying. A vendor that says "here is the technical evidence layer, and here is where your organizational work begins" is telling the truth.

---

## 4. Why HUMMBL for EU AI Act readiness

### 1. Deterministic evidence, not LLM-judged

Most AI governance vendors (Credo AI, Holistic AI, Arthur AI, Fiddler AI, IBM watsonx.governance) use LM-assisted compliance: an LLM judges whether a control is satisfied. This produces "audit-ready evidence" — a document that looks like compliance but is not deterministic. If the LLM changes its judgment, the evidence changes.

HUMMBL produces deterministic evidence: the same input produces the same output, every time. A governance bus tuple is a fact, not a judgment. When you bring HUMMBL evidence to a Notified Body, the evidence is reproducible. When the LLM-judged vendor's evidence is questioned, the vendor has to re-run the LLM and hope it judges the same way.

For EU AI Act conformity assessment, deterministic evidence is stronger than LLM-judged evidence. The Notified Body can verify it. The LLM-judged evidence requires the Notified Body to trust the vendor's LLM.

### 2. In-process, not platform

HUMMBL runs in your process. Your agent activity does not leave your runtime to be judged on someone else's cloud. For EU AI Act compliance, this matters for three reasons:

- **Data residency** (Art. 10, 12): if your agent activity is processed on a US-based SaaS platform, you have a data transfer question under GDPR. HUMMBL in-process avoids this.
- **Vendor lock-in**: if your compliance evidence is locked in a SaaS platform, switching vendors means losing your evidence history. HUMMBL's evidence is in your filesystem, in open formats (JSONL, TSV).
- **Audit access**: a Notified Body can inspect your HUMMBL evidence directly. A SaaS platform requires the Notified Body to go through the vendor's audit interface.

### 3. Open-source, inspectable

HUMMBL is Apache 2.0 open-source. A Notified Body can inspect the source code that generates the evidence. A SaaS platform's evidence generation is a black box. For EU AI Act conformity assessment, inspectability is a feature: the Notified Body can verify that the evidence generation logic is correct, not just that the evidence exists.

### 4. The coverage matrix is public

HUMMBL publishes the full EU AI Act coverage matrix — all 113 articles, all 13 annexes — in `hummbl-io/hummbl-governance/docs/coverage/eu-ai-act.md`. No other vendor publishes this. Credo AI, Holistic AI, Arthur AI, Fiddler AI, IBM watsonx.governance, Collibra, OneTrust, Modulos, Airia, ServiceNow — none of them publish a per-article coverage matrix. They publish marketing summaries; HUMMBL publishes the matrix.

A compliance buyer can read the matrix before engaging HUMMBL and know exactly which articles HUMMBL covers, which are partial, and which are boundary. There is no surprise in the sales process.

### 5. The receipt chain is verifiable

HUMMBL's KRINEIA receipt chain (`_receipts/krineia/primary.jsonl`) is hash-linked: each receipt's hash is computed from the previous receipt's hash plus the current receipt's content. Tampering with any receipt breaks the chain. A Notified Body can verify the chain in seconds. This is the same cryptographic primitive that underpins blockchain evidence — but without the blockchain overhead.

---

## 5. The 60-day plan

If you are a compliance buyer with a high-risk AI system facing the August 2, 2026 deadline, here is what HUMMBL recommends:

### Days 1–14: Gap assessment

1. Read the HUMMBL EU AI Act coverage matrix. Identify which of Art. 9–17, 19 your current system satisfies and which it does not.
2. Run `compliance_mapper --framework eu-ai-act --days 30` on your existing governance traces (if any). Identify which articles have evidence and which do not.
3. Identify your conformity assessment path (Annex VI internal control, or Annex VII Notified Body for biometric systems).
4. Engage a Notified Body (if Annex VII) or an internal auditor (if Annex VI) for the assessment scope.

### Days 15–35: Integration

1. `pip install hummbl-governance` in your AI system's runtime.
2. Instrument your agents to emit governance bus tuples for every action, every delegation, every kill-switch event.
3. Configure retention (default 5+ years, aligned with Art. 19).
4. Configure the compliance mapper to generate the EU AI Act report on a schedule (weekly is reasonable).

### Days 36–50: Evidence collection

1. Run the system in production for 14 days. The governance bus accumulates evidence tuples.
2. Generate the EU AI Act report. Review the evidence for each article.
3. Identify gaps. Address them (either by instrumenting more agent actions, or by documenting organizational controls for the boundary articles).

### Days 51–60: Assessment

1. Bring the EU AI Act report, the coverage matrix, and the KRINEIA receipt chain to your Notified Body or internal auditor.
2. The Notified Body inspects the evidence. The deterministic, in-process, open-source nature of the evidence makes inspection straightforward.
3. Issue the EU declaration of conformity (Art. 47). Affix the CE mark.

This is a 60-day plan for a system that is already in production. If your system is not yet in production, the integration phase is shorter (no existing traces to migrate).

---

## 6. The boundary disclaimer (statutory)

HUMMBL is **not** a Notified Body under EU AI Act Article 31. This position paper maps technical primitives to control requirements; it does **not** constitute a Notified Body conformity assessment per Article 43. Statutory conformity assessment for Annex III high-risk systems requires either (a) internal control assessment per Annex VI, or (b) Notified Body assessment per Annex VII (mandatory for biometric identification systems). HUMMBL provides the **technical evidence interface** that supports either assessment path; the legal conformity declaration is the provider's responsibility.

This position paper is not legal advice. A compliance buyer should engage qualified EU regulatory counsel for the legal conformity assessment. HUMMBL provides the technical evidence layer; the legal layer is the provider's and their counsel's.

---

## 7. How to verify this position paper

A reader can re-verify every claim in this paper independently:

1. **The EU AI Act exists and the deadline is August 2, 2026** — check the official text at https://eur-lex.europa.eu/eli/reg/2024/1689/oj. Article 113 sets the application dates.
2. **HUMMBL's coverage matrix exists** — inspect `hummbl-io/hummbl-governance/docs/coverage/eu-ai-act.md`. 306 lines, 113 articles, all 13 annexes.
3. **The compliance mapper exists and generates EU AI Act reports** — `pip install hummbl-governance` and run `compliance_mapper --framework eu-ai-act --days 30`.
4. **The governance bus exists** — inspect `_state/coordination/messages.tsv` in any HUMMBL-instrumented repo.
5. **The KRINEIA receipt chain exists** — inspect `_receipts/krineia/primary.jsonl` in `hummbl-io/hummbl-production`.
6. **HUMMBL is open-source** — check https://github.com/hummbl-io/hummbl-governance for Apache 2.0 license.
7. **The 1,234 tests exist** — clone `hummbl-io/hummbl-governance` and run `pytest --collect-only`.

If any claim in this paper cannot be re-verified, open an issue at `hummbl-io/hummbl-production/issues` and the claim will be corrected or removed per CONSTITUTION §3.1.

---

## References

- EU AI Act: Regulation (EU) 2024/1689 — https://eur-lex.europa.eu/eli/reg/2024/1689/oj
- HUMMBL EU AI Act coverage matrix: `hummbl-io/hummbl-governance/docs/coverage/eu-ai-act.md`
- HUMMBL compliance mapper: `hummbl-io/hummbl-governance/hummbl_governance/compliance_mapper.py`
- HUMMBL governance bus: `hummbl-io/hummbl-governance/hummbl_governance/governance_bus.py`
- HUMMBL kill switch: `hummbl-io/hummbl-governance/hummbl_governance/kill_switch_core.py`
- HUMMBL delegation token: `hummbl-io/hummbl-governance/hummbl_governance/delegation_token.py`
- HUMMBL circuit breaker: `hummbl-io/hummbl-governance/hummbl_governance/circuit_breaker.py`
- White paper: `docs/artifacts/WHITE_PAPER_governance_infrastructure.md`
- Competitive analysis: `docs/artifacts/COMPETITIVE_ANALYSIS_ai_governance.md`
- Case study: `docs/artifacts/CASE_STUDY_claims_remediation.md`
- Claims manifest: `web/manifest/claims-provenance.json`
- CONSTITUTION: `CONSTITUTION.md` (§3.1 public claim honesty invariant)

---

## Authority boundary

**Operator** is the human **Principal Agent** for HUMMBL — the goal-owning, value-bearing, accountable agent. **Devin** (and other software agents: Codex, Claude Code, Gemini, OpenCode, Kai, Apex, Nexus, Auditor, Hermes) are **delegated drafting, research, and execution systems**. They can draft, collect, compare, format, inspect, and surface — they cannot confer strategic authority on themselves, promote drafts to live, publish external claims, or redefine strategic goals. This position paper was drafted by Devin at the direction of the Principal Agent, based on the HUMMBL EU AI Act coverage matrix and compliance mapper source code, and was promoted to live (public) by Principal Agent decision on 2026-06-23. The underlying coverage matrix was authored by claude-code (self-hosted-runner-3) per ADR-001 and reviewed 2026-05-14. This document is **public** — it is intended for external readers (compliance buyers at EU-operating AI-native teams) and may be published on hummbl.io.
