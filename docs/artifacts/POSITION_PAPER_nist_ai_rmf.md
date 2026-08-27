# Position Paper: HUMMBL NIST AI RMF Alignment

**Status:** live v1.0 (public)
**Author:** Operator, HUMMBL, LLC
**Date:** 2026-06-23
**Tracking:** docs/artifacts/ARTIFACT_MANIFEST.md (item 10)
**Reader:** compliance buyer at a US-operating AI-native team evaluating governance vendors for NIST AI RMF alignment
**Decision:** whether to engage HUMMBL for NIST AI RMF alignment work

**TL;DR:** NIST AI RMF 1.0 (NIST AI 100-1, January 2023) is the de facto US framework for AI risk management. It is voluntary — no certification body, no mandatory assessment — but it is the framework US federal agencies require of AI vendors (per OMB Circular M-24-10) and the framework most enterprise buyers ask about. HUMMBL maps to all 4 core functions (GOVERN, MAP, MEASURE, MANAGE) across ~70 subcategories, with deterministic, in-process evidence for 20 subcategories and partial coverage for 31. This paper maps HUMMBL's primitives to the framework, shows what HUMMBL covers and what it does not, and explains why a compliance buyer should choose HUMMBL for the technical-evidence layer of their NIST AI RMF alignment program.

---

## 1. The framework

NIST AI RMF 1.0 was published January 2023 as NIST AI 100-1. It is a **voluntary** framework — no certification body, no mandatory assessment, no statutory penalties. Conformance is self-attested or third-party-assessed via consulting engagements.

The framework organizes AI risk management around 4 core functions:

| Function    | Purpose                                                               | Subcategories |
| ----------- | --------------------------------------------------------------------- | ------------- |
| **GOVERN**  | Policies, processes, procedures, and practices for AI risk management | ~19           |
| **MAP**     | Context recognition: identify AI system's use, context, risks         | ~18           |
| **MEASURE** | Analyze, assess, benchmark, monitor AI risks and trustworthiness      | ~20           |
| **MANAGE**  | Prioritize and act on risks: allocate resources, control, respond     | ~13           |
| **Total**   |                                                                       | **~70**       |

### Why it matters

NIST AI RMF is voluntary, but it is not optional in practice for three reasons:

1. **Federal procurement** — OMB Circular M-24-10 (effective December 2023) requires US federal agencies to require AI RMF alignment from AI vendors. If you sell to the US federal government, your buyer asks about AI RMF.
2. **Enterprise procurement** — most Fortune 500 AI governance RFPs ask for AI RMF alignment. It is the lingua franca of US AI governance.
3. **EU AI Act crosswalk** — NIST AI RMF and EU AI Act share the same risk-management vocabulary. AI RMF alignment is a down payment on EU AI Act readiness.

### What "alignment" means

NIST AI RMF alignment is not a pass/fail test. It is a maturity assessment: for each of the ~70 subcategories, the organization demonstrates that it has a practice, process, or tool that addresses the subcategory. The maturity is typically scored on a 1-5 scale (Initial → Repeatable → Defined → Managed → Optimized).

A compliance buyer's NIST AI RMF alignment program typically produces:

1. **A coverage matrix** — for each subcategory, what the organization does to address it
2. **Evidence artifacts** — documents, logs, dashboards that demonstrate the practice
3. **A maturity assessment** — scored 1-5 per subcategory, with improvement plan
4. **A third-party assessment** — optional but common for enterprise buyers

This is a documentation and evidence problem, not a software problem. That is where HUMMBL fits.

---

## 2. What HUMMBL provides

HUMMBL is a Python library that emits deterministic, in-process evidence for the technical-evidence subcategories of NIST AI RMF. It is not a NIST-recognized assessor. It does not issue conformance certifications. It provides the **technical evidence layer** that supports a self-attestation or third-party assessment.

### The mapping

HUMMBL maintains a coverage matrix in `hummbl-io/hummbl-governance/docs/coverage/nist-ai-rmf.md` that maps every subcategory (~70) across all 4 functions to either a HUMMBL primitive that addresses it, a partial-coverage description, or an explicit boundary statement. No subcategory is silently excluded.

The summary:

| Function   | Subcategories | ✅ Fulfilled | 🟡 Partial | ⚪ Boundary |
| ---------- | ------------- | ------------ | ---------- | ----------- |
| GOVERN     | ~19           | 4            | 8          | 7           |
| MAP        | ~18           | 3            | 9          | 6           |
| MEASURE    | ~20           | 8            | 8          | 4           |
| MANAGE     | ~13           | 5            | 6          | 2           |
| **Totals** | **~70**       | **20**       | **31**     | **19**      |

The 20 ✅ are subcategories where a HUMMBL primitive implements the control and a runnable evidence artifact exists. The 31 🟡 are subcategories where HUMMBL provides part of the control and the customer organization provides the rest. The 19 ⚪ are subcategories that are organizational, regulatory, or institutional — not addressable by a software library.

### The load-bearing subcategories

HUMMBL's primitives concentrate in MEASURE (measurement infrastructure is what HUMMBL is) and MANAGE (kill-switch + incident-response primitives). Here is how HUMMBL maps to the load-bearing subcategories:

| Subcategory     | Requirement                                                       | HUMMBL primitive                                           | Evidence                                   |
| --------------- | ----------------------------------------------------------------- | ---------------------------------------------------------- | ------------------------------------------ |
| **GOVERN-1.1**  | Legal and regulatory requirements understood, managed, documented | Coverage matrix index (this matrix is the documentation)   | `docs/coverage/nist-ai-rmf.md`             |
| **GOVERN-1.6**  | Mechanisms to inventory AI systems + categorize by risk           | AI-system inventory tuple + risk-classification field      | `governance_bus` `AI_SYSTEM` tuple type    |
| **GOVERN-1.7**  | Processes for decommissioning/phasing out AI systems              | Decommission tuple + retention/erasure primitives          | `governance_bus` `DECOMMISSION` tuple type |
| **MAP-1.1**     | Organizational context documented                                 | `DCTX` (delegation context) tuples document the context    | `delegation_context.py`                    |
| **MAP-2.2**     | Risk assessment basis                                             | `ATTEST` and `EVIDENCE` tuples                             | `attest.py`                                |
| **MEASURE-2.5** | Trustworthiness evaluations                                       | Signed entries (HMAC-SHA256) prove the evaluation happened | `delegation_token.py`                      |
| **MEASURE-2.8** | Impact metrics                                                    | `COST_GOVERNOR` events track cost impact                   | `cost_tracker.py`                          |
| **MANAGE-1.3**  | Response plans executed                                           | `KILLSWITCH` events prove the response was executed        | `kill_switch_core.py`                      |
| **MANAGE-2.4**  | Risk treatment applied                                            | `CIRCUIT_BREAKER` state transitions prove the treatment    | `circuit_breaker.py`                       |

### How to use it

A compliance buyer integrates HUMMBL into their AI system's runtime. Every agent action emits a governance bus tuple. The compliance mapper reads the bus and generates a NIST AI RMF report on demand:

```python
from hummbl_governance import ComplianceMapper

mapper = ComplianceMapper(governance_dir="the coordination bus")
report = mapper.generate_nist_rmf_report(days=30)
print(report.to_json())
```

The report contains, for each of GOVERN-1.1, GOVERN-1.7, MAP-1.1, MAP-2.2, MEASURE-2.5, MEASURE-2.8, MANAGE-1.3, MANAGE-2.4, the evidence tuples from the last 30 days that satisfy that subcategory. This is the technical evidence you bring to your self-attestation or third-party assessment.

---

## 3. What HUMMBL does not provide

HUMMBL is honest about its boundary. This is not a "HUMMBL makes you NIST AI RMF aligned" claim. HUMMBL provides the **technical evidence layer**. The compliance buyer still needs:

1. **A NIST-recognized third-party assessor** (optional) — HUMMBL is not an assessor. The organization chooses whether to self-attest or engage a third party; HUMMBL provides the evidence either path requires.
2. **Organizational policies** (GOVERN-1.2, 1.3, 1.4) — HUMMBL provides the evidence backbone; the policies are the organization's authorship.
3. **Workforce training** (GOVERN-2.2, 3.1, 3.2) — HUMMBL provides documentation; the training program is the organization's HR responsibility.
4. **Executive accountability** (GOVERN-2.3) — HUMMBL provides the delegation chain that documents who approved what; the accountability structure is the organization's.
5. **Risk tolerance definition** (MAP-1.2, 1.3) — HUMMBL provides the inventory; the risk tolerance is the organization's.
6. **Impact assessment methodology** (MEASURE-2.1, 2.2) — HUMMBL records the evidence that the assessment happened; the methodology is the organization's.
7. **Incident response plan** (MANAGE-1.1, 1.2) — HUMMBL provides the kill switch and circuit breaker; the IR plan is the organization's.

The 19 ⚪ boundary subcategories are mostly these: organizational, regulatory, or institutional obligations that no software library can satisfy. HUMMBL's honesty about this boundary is itself a governance feature. A vendor that claims to "make you aligned" is overclaiming. A vendor that says "here is the technical evidence layer, and here is where your organizational work begins" is telling the truth.

---

## 4. Why HUMMBL for NIST AI RMF alignment

### 1. Deterministic evidence, not LLM-judged

Most AI governance vendors (Credo AI, Holistic AI, Arthur AI, Fiddler AI, IBM watsonx.governance) use LM-assisted compliance: an LLM judges whether a subcategory is satisfied. This produces "audit-ready evidence" — a document that looks like alignment but is not deterministic. If the LLM changes its judgment, the evidence changes.

HUMMBL produces deterministic evidence: the same input produces the same output, every time. A governance bus tuple is a fact, not a judgment. When you bring HUMMBL evidence to a third-party assessor, the evidence is reproducible. When the LLM-judged vendor's evidence is questioned, the vendor has to re-run the LLM and hope it judges the same way.

For NIST AI RMF assessment, deterministic evidence is stronger than LLM-judged evidence. The assessor can verify it. The LLM-judged evidence requires the assessor to trust the vendor's LLM.

### 2. In-process, not platform

HUMMBL runs in your process. Your agent activity does not leave your runtime to be judged on someone else's cloud. For NIST AI RMF alignment, this matters for three reasons:

- **Data residency**: if your agent activity is processed on a SaaS platform, you have a data transfer question. HUMMBL in-process avoids this.
- **Vendor lock-in**: if your compliance evidence is locked in a SaaS platform, switching vendors means losing your evidence history. HUMMBL's evidence is in your filesystem, in open formats (JSONL, TSV).
- **Assessor access**: a third-party assessor can inspect your HUMMBL evidence directly. A SaaS platform requires the assessor to go through the vendor's audit interface.

### 3. Open-source, inspectable

HUMMBL is Apache 2.0 open-source. A third-party assessor can inspect the source code that generates the evidence. A SaaS platform's evidence generation is a black box. For NIST AI RMF assessment, inspectability is a feature: the assessor can verify that the evidence generation logic is correct, not just that the evidence exists.

### 4. The coverage matrix is public

HUMMBL publishes the full NIST AI RMF coverage matrix — all ~70 subcategories across all 4 functions — in `hummbl-io/hummbl-governance/docs/coverage/nist-ai-rmf.md`. No other vendor publishes this. Credo AI, Holistic AI, Arthur AI, Fiddler AI, IBM watsonx.governance, Collibra, OneTrust, Modulos, Airia, ServiceNow — none of them publish a per-subcategory coverage matrix. They publish marketing summaries; HUMMBL publishes the matrix.

A compliance buyer can read the matrix before engaging HUMMBL and know exactly which subcategories HUMMBL covers, which are partial, and which are boundary. There is no surprise in the sales process.

### 5. Crosswalk to EU AI Act

NIST AI RMF and EU AI Act share the same risk-management vocabulary. A HUMMBL integration that produces evidence for NIST AI RMF also produces evidence for EU AI Act Articles 9, 10, 12, 13, 14, 15. The same governance bus tuples, the same delegation tokens, the same kill-switch events satisfy both frameworks. This is a feature of HUMMBL's primitive design: the primitives are framework-agnostic; the compliance mapper does the framework-specific mapping.

For a compliance buyer facing both US federal procurement (AI RMF) and EU market access (AI Act), HUMMBL is a single integration that serves both.

### 6. The receipt chain is verifiable

HUMMBL's KRINEIA receipt chain (`_receipts/krineia/primary.jsonl`) is hash-linked: each receipt's hash is computed from the previous receipt's hash plus the current receipt's content. Tampering with any receipt breaks the chain. A third-party assessor can verify the chain in seconds. This is the same cryptographic primitive that underpins blockchain evidence — but without the blockchain overhead.

---

## 5. The 30-day plan

If you are a compliance buyer starting a NIST AI RMF alignment program, here is what HUMMBL recommends:

### Days 1–7: Gap assessment

1. Read the HUMMBL NIST AI RMF coverage matrix. Identify which subcategories your current system satisfies and which it does not.
2. Run `compliance_mapper --framework nist-ai-rmf --days 30` on your existing governance traces (if any). Identify which subcategories have evidence and which do not.
3. Score your current maturity 1-5 per subcategory. Identify the lowest-scoring subcategories.

### Days 8–14: Integration

1. `pip install hummbl-governance` in your AI system's runtime.
2. Instrument your agents to emit governance bus tuples for every action, every delegation, every kill-switch event.
3. Configure the compliance mapper to generate the NIST AI RMF report on a schedule (weekly is reasonable).

### Days 15–21: Evidence collection

1. Run the system in production for 7 days. The governance bus accumulates evidence tuples.
2. Generate the NIST AI RMF report. Review the evidence for each subcategory.
3. Identify gaps. Address them (either by instrumenting more agent actions, or by documenting organizational controls for the boundary subcategories).

### Days 22–30: Assessment

1. Bring the NIST AI RMF report, the coverage matrix, and the KRINEIA receipt chain to your self-attestation or third-party assessment.
2. The assessor inspects the evidence. The deterministic, in-process, open-source nature of the evidence makes inspection straightforward.
3. Score your post-integration maturity 1-5 per subcategory. Document the improvement.

This is a 30-day plan for a system that is already in production. If your system is not yet in production, the integration phase is shorter (no existing traces to migrate).

---

## 6. The boundary disclaimer

NIST AI RMF is a **voluntary** framework, not a regulation. There is no certification body for AI RMF; conformance is self-attested or third-party-assessed via consulting engagements. HUMMBL maps technical primitives to AI RMF subcategories; framework adoption (governance structure, organizational priorities, AI risk tolerance) is the customer organization's responsibility.

This position paper is not legal advice. A compliance buyer should engage qualified counsel for the legal interpretation of AI RMF alignment obligations. HUMMBL provides the technical evidence layer; the legal layer is the provider's and their counsel's.

---

## 7. How to verify this position paper

A reader can re-verify every claim in this paper independently:

1. **NIST AI RMF 1.0 exists** — check the official document at https://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.100-1.pdf (NIST AI 100-1, January 2023).
2. **HUMMBL's coverage matrix exists** — inspect `hummbl-io/hummbl-governance/docs/coverage/nist-ai-rmf.md`. 217 lines, ~70 subcategories, all 4 functions.
3. **The compliance mapper exists and generates NIST AI RMF reports** — `pip install hummbl-governance` and run `compliance_mapper --framework nist-ai-rmf --days 30`.
4. **The governance bus exists** — inspect `the coordination bus log` in any HUMMBL-instrumented repo.
5. **The KRINEIA receipt chain exists** — inspect `_receipts/krineia/primary.jsonl` in `hummbl-io/hummbl-production`.
6. **HUMMBL is open-source** — check https://github.com/hummbl-io/hummbl-governance for Apache 2.0 license.
7. **OMB Circular M-24-10 requires AI RMF alignment for federal AI vendors** — check the OMB circular at https://www.whitehouse.gov/wp-content/uploads/2024/03/M-24-10-Advancing-Governance-Innovation-and-Risk-Management-for-Agency-Use-of-Artificial-Intelligence.pdf.

If any claim in this paper cannot be re-verified, open an issue at `hummbl-io/hummbl-production/issues` and the claim will be corrected or removed per CONSTITUTION §3.1.

---

## References

- NIST AI RMF 1.0: NIST AI 100-1 (January 2023) — https://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.100-1.pdf
- NIST AI RMF Playbook: https://www.nist.gov/itl/ai-risk-management-framework/playbook
- OMB Circular M-24-10: https://www.whitehouse.gov/wp-content/uploads/2024/03/M-24-10-Advancing-Governance-Innovation-and-Risk-Management-for-Agency-Use-of-Artificial-Intelligence.pdf
- HUMMBL NIST AI RMF coverage matrix: `hummbl-io/hummbl-governance/docs/coverage/nist-ai-rmf.md`
- HUMMBL compliance mapper: `hummbl-io/hummbl-governance/hummbl_governance/compliance_mapper.py`
- HUMMBL governance bus: `hummbl-io/hummbl-governance/hummbl_governance/governance_bus.py`
- HUMMBL kill switch: `hummbl-io/hummbl-governance/hummbl_governance/kill_switch_core.py`
- HUMMBL delegation token: `hummbl-io/hummbl-governance/hummbl_governance/delegation_token.py`
- HUMMBL circuit breaker: `hummbl-io/hummbl-governance/hummbl_governance/circuit_breaker.py`
- White paper: `docs/artifacts/WHITE_PAPER_governance_infrastructure.md`
- Competitive analysis: `docs/artifacts/COMPETITIVE_ANALYSIS_ai_governance.md`
- EU AI Act position paper: `docs/artifacts/POSITION_PAPER_eu_ai_act.md`
- Case study: `docs/artifacts/CASE_STUDY_claims_remediation.md`
- Claims manifest: `web/manifest/claims-provenance.json`
- CONSTITUTION: `CONSTITUTION.md` (§3.1 public claim honesty invariant)

---

## Authority boundary

**Operator** is the human **Principal Agent** for HUMMBL — the goal-owning, value-bearing, accountable agent. **Devin** (and other software agents: Codex, Claude Code, Gemini, OpenCode, Kai, Apex, Nexus, Auditor, Hermes) are **delegated drafting, research, and execution systems**. They can draft, collect, compare, format, inspect, and surface — they cannot confer strategic authority on themselves, promote drafts to live, publish external claims, or redefine strategic goals. This position paper was drafted by Devin at the direction of the Principal Agent, based on the HUMMBL NIST AI RMF coverage matrix and compliance mapper source code, and was promoted to live (public) by Principal Agent decision on 2026-06-23. The underlying coverage matrix was authored by claude-code (self-hosted-runner-3) per ADR-001 and reviewed 2026-05-14. This document is **public** — it is intended for external readers (compliance buyers at US-operating AI-native teams) and may be published on hummbl.io.
