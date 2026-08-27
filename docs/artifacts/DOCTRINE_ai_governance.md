# Doctrine: AI Governance Principles

**Status:** live v1.0 (public)
**Author:** Operator, HUMMBL, LLC
**Date:** 2026-06-23
**Tracking:** docs/artifacts/ARTIFACT_MANIFEST.md (item 11)
**Reader:** team, agents (Codex, Claude Code, Gemini, OpenCode, Kai, Apex, Nexus, Auditor, Hermes, Devin)
**Decision:** use these principles as the decision-consistency baseline for all HUMMBL governance work

**TL;DR:** HUMMBL operates on 10 AI governance principles. They are not aspirations; they are decision rules. When a principle conflicts with a business outcome, the principle wins. When an agent's output conflicts with a principle, the output is rejected. When a customer asks HUMMBL to violate a principle, HUMMBL declines the work. These principles are the doctrine that makes HUMMBL's governance claims credible — HUMMBL governs itself by the same principles it sells.

---

## 1. Why a doctrine

HUMMBL sells AI governance infrastructure. A vendor that sells governance without governing itself is a hypocrisy risk. The doctrine closes that gap: these are the principles HUMMBL applies to its own AI systems (agents, briefings, dashboards, automated decisions), and they are the same principles HUMMBL recommends to its customers.

The doctrine is also a decision-consistency baseline. When an agent faces a choice — should I publish this claim? should I emit this receipt? should I promote this artifact? should I delegate this capability? — the doctrine gives the answer. This reduces decision fatigue and makes agent behavior predictable across sessions and across agents.

### What a doctrine is (and is not)

A **doctrine** is a set of principles that govern decisions. It is not:

- A **policy** — policies are specific rules for specific situations; doctrines are general principles that generate policies
- A **standard** — standards are auditable conformance criteria; doctrines are the values that standards implement
- A **regulation** — regulations are externally imposed; doctrines are self-adopted
- A **process** — processes are step-by-step; doctrines are decision rules

The doctrine sits above policies, standards, and processes. It is the source from which they derive.

---

## 2. The 10 principles

### Principle 1: Honesty over optics

Every public claim is either validated with cited evidence or marked unproven. No claim is presented as verified without evidence. No claim is silently omitted to avoid embarrassment. When HUMMBL is wrong, HUMMBL says so publicly and corrects the claim.

**Decision rule:** If you cannot cite a source for a claim, do not make the claim. If you have a source, cite it. If the source is weak (tier C), mark it unproven. If the source is wrong, retract.

**Source:** CONSTITUTION §3.1 (public claim honesty invariant).

### Principle 2: Determinism over judgment

HUMMBL's governance evidence is deterministic: the same input produces the same output, every time. HUMMBL does not use LLM-judged compliance evidence. An LLM can assist a human in interpreting evidence, but the evidence itself is a fact, not a judgment.

**Decision rule:** When choosing between a deterministic mechanism and an LLM-judged mechanism for governance evidence, choose deterministic. Use LLMs for interpretation, not for evidence generation.

**Source:** White paper §4 (deterministic evidence vs LLM-judged).

### Principle 3: In-process over platform

HUMMBL's primitives run in the customer's process. Agent activity does not leave the customer's runtime to be judged on someone else's cloud. This is a structural choice: it eliminates data residency questions, vendor lock-in, and assessor-access friction.

**Decision rule:** When designing a governance mechanism, prefer in-process over SaaS. A SaaS platform is acceptable for non-evidence surfaces (dashboards, reporting), but the evidence itself is in-process.

**Source:** White paper §3 (in-process governance).

### Principle 4: Open-source over closed

HUMMBL's governance library is Apache 2.0 open-source. A third-party assessor can inspect the source code that generates the evidence. A customer can fork the library if HUMMBL stops maintaining it. A competitor can verify that the evidence generation logic is correct.

**Decision rule:** When choosing between open-source and closed-source for a governance mechanism, choose open-source. Closed-source is acceptable for non-evidence surfaces (the dashboard UI, the SaaS platform), but the evidence-generation logic is open.

**Source:** CONSTITUTION §3.5 (Apache-2.0 license invariant).

### Principle 5: Boundary honesty

HUMMBL states what it does not do. HUMMBL is not a Notified Body under EU AI Act Article 31. HUMMBL is not a NIST-recognized assessor. HUMMBL does not issue conformity certifications. HUMMBL provides the technical evidence layer; the conformity assessment is the provider's and their assessor's.

**Decision rule:** When describing what HUMMBL does, also describe what HUMMBL does not do. A vendor that claims to "make you aligned" is overclaiming. A vendor that says "here is the technical evidence layer, and here is where your organizational work begins" is telling the truth.

**Source:** EU AI Act position paper §3; NIST AI RMF position paper §3.

### Principle 6: Receipts for every governance action

Every governance action — claim promotion, artifact publication, delegation, kill-switch event, circuit-breaker transition — emits a receipt. The receipt is hash-chained to the prior receipt. Tampering with any receipt breaks the chain.

**Decision rule:** If a governance action does not emit a receipt, it did not happen. If a receipt cannot be verified against the chain, it is suspect. Every governance action gets a receipt; every receipt is in the chain.

**Source:** CONSTITUTION §3.6 (receipt integrity invariant); KRINEIA receipt chain.

### Principle 7: Human authority over agent action

Operator is the Principal Agent. Software agents (Devin, Codex, Claude Code, Gemini, OpenCode, Kai, Apex, Nexus, Auditor, Hermes) are delegated drafting, research, and execution systems. Agents can draft, collect, compare, format, inspect, and surface. Agents cannot confer strategic authority on themselves, promote drafts to live, publish external claims, or redefine strategic goals.

**Decision rule:** When an agent produces an output that requires strategic authority (publish, promote, fund, commit, decline), the output is a recommendation to the Principal Agent, not a decision. The Principal Agent decides; the agent implements.

**Source:** Authority boundary section in every HUMMBL artifact; MULTI_AGENT.md governance model.

### Principle 8: Framework-agnostic primitives

HUMMBL's primitives (KillSwitch, CircuitBreaker, DelegationToken, GovernanceBus, Receipt, AgentRegistry, CostGovernor, CapabilityFence) are framework-agnostic. The same primitive produces evidence for EU AI Act, NIST AI RMF, SOC 2, GDPR, OWASP. The compliance mapper does the framework-specific mapping.

**Decision rule:** When designing a new primitive, make it framework-agnostic. Framework-specific logic belongs in the compliance mapper, not in the primitive. A customer who integrates a primitive once should get evidence for multiple frameworks.

**Source:** NIST AI RMF position paper §4 (crosswalk to EU AI Act); compliance_mapper.py.

### Principle 9: Public coverage matrices

HUMMBL publishes per-article / per-subcategory coverage matrices for every framework it supports. The EU AI Act coverage matrix maps all 113 articles. The NIST AI RMF coverage matrix maps all ~70 subcategories. No subcategory is silently excluded.

**Decision rule:** When HUMMBL supports a framework, publish the coverage matrix. The matrix shows what HUMMBL covers, what is partial, and what is boundary. No coverage matrix is silent about gaps.

**Source:** EU AI Act coverage matrix; NIST AI RMF coverage matrix; competitive analysis (no other vendor publishes per-article matrices).

### Principle 10: Recursive self-improvement

HUMMBL uses its own governance primitives to govern its own operations. The claims manifest governs HUMMBL's claims. The KRINEIA receipt chain governs HUMMBL's artifact promotions. The kill switch governs HUMMBL's agents. The governance bus records HUMMBL's agent actions. HUMMBL is its own first customer.

**Decision rule:** When HUMMBL builds a governance primitive, HUMMBL uses it on itself first. If the primitive is not good enough for HUMMBL's own operations, it is not good enough for customers. The case study (claims remediation 2026-06-23) is the proof: HUMMBL used its own claims manifest to catch its own claim errors.

**Source:** Case study `CASE_STUDY_claims_remediation.md`; RETROSPECTIVE_wave_1.md (RSI loop).

---

## 3. How the principles interact

The 10 principles are not independent. They form a coherent system:

```
Principle 1 (honesty) requires Principle 6 (receipts) — honesty needs proof
Principle 2 (determinism) requires Principle 4 (open-source) — determinism needs inspectability
Principle 3 (in-process) requires Principle 8 (framework-agnostic) — in-process needs reusability
Principle 5 (boundary honesty) requires Principle 9 (public matrices) — boundary needs visibility
Principle 7 (human authority) requires Principle 6 (receipts) — authority needs audit trail
Principle 10 (RSI) requires all 9 — HUMMBL governs itself by all principles
```

A violation of any principle weakens the others. A vendor that claims honesty (P1) but does not emit receipts (P6) cannot prove the honesty claim. A vendor that claims determinism (P2) but is closed-source (P4) cannot prove the determinism claim. The principles are only credible together.

---

## 4. How to apply the doctrine

### For agents

When an agent faces a decision, apply the principles in order:

1. **Is this a public claim?** (P1) — If yes, cite a source or mark unproven.
2. **Is this governance evidence?** (P2) — If yes, use a deterministic mechanism, not LLM-judged.
3. **Does this leave the customer's process?** (P3) — If yes, justify why in-process is not possible.
4. **Is the evidence-generation logic open?** (P4) — If no, justify why closed is acceptable.
5. **Am I claiming something HUMMBL does not do?** (P5) — If yes, state the boundary.
6. **Does this action emit a receipt?** (P6) — If no, emit one before completing.
7. **Am I exercising strategic authority?** (P7) — If yes, route to the Principal Agent.
8. **Am I building framework-specific logic into a primitive?** (P8) — If yes, move it to the mapper.
9. **Am I supporting a framework without a coverage matrix?** (P9) — If yes, publish the matrix.
10. **Am I using HUMMBL's primitives on HUMMBL's operations?** (P10) — If no, ask why.

### For the team

When the team faces a decision, apply the principles as a tiebreaker:

- If a business outcome conflicts with a principle, the principle wins.
- If a customer asks HUMMBL to violate a principle, HUMMBL declines the work.
- If a competitor's behavior suggests violating a principle would be profitable, HUMMBL does not violate the principle.
- If a principle seems wrong, propose an amendment (see §5).

### For customers

When a customer evaluates HUMMBL, apply the principles as a checklist:

- Does HUMMBL cite sources for its claims? (P1)
- Is HUMMBL's evidence deterministic? (P2)
- Does HUMMBL run in-process? (P3)
- Is HUMMBL open-source? (P4)
- Does HUMMBL state its boundaries? (P5)
- Does HUMMBL emit receipts? (P6)
- Does HUMMBL keep human authority over agents? (P7)
- Are HUMMBL's primitives framework-agnostic? (P8)
- Does HUMMBL publish coverage matrices? (P9)
- Does HUMMBL use its own primitives? (P10)

If any answer is "no," the customer should ask why. HUMMBL's answer should be either "yes" or a justified exception.

---

## 5. Amendment process

The doctrine is not immutable. Principles can be added, revised, or retired. The amendment process is:

1. **Propose** — any agent or human can propose an amendment via a bus PROPOSAL message.
2. **Review** — the Principal Agent and Board review the proposal.
3. **Decide** — the Principal Agent decides (accept, reject, defer).
4. **Receipt** — if accepted, emit a KRINEIA receipt for the amendment.
5. **Publish** — update this document and the manifest.

Amendments are versioned. The current version is v1.0. The version history is in the review log of `ARTIFACT_MANIFEST.md`.

### What cannot be amended

Principles 1 (honesty), 6 (receipts), and 7 (human authority) are constitutional invariants per CONSTITUTION §3. They cannot be amended without a constitutional amendment (CONSTITUTION §7), which requires a KRINEIA receipt and human approval. The other principles (2, 3, 4, 5, 8, 9, 10) can be amended via the doctrine amendment process.

---

## 6. Boundary disclaimer

This doctrine is HUMMBL's self-adopted set of principles. It is not a regulation, a standard, or a certification. HUMMBL does not claim that adopting this doctrine makes an organization "governance-aligned." The doctrine is HUMMBL's decision-consistency baseline; other organizations may adopt different doctrines.

HUMMBL's compliance with its own doctrine is self-attested. The evidence of compliance is in the claims manifest, the KRINEIA receipt chain, the coverage matrices, and the open-source code. A third party can inspect this evidence and assess HUMMBL's compliance. HUMMBL does not claim perfect compliance; HUMMBL claims to try, to emit receipts when it tries, and to correct when it fails.

---

## 7. How to verify this doctrine

A reader can re-verify every principle's source independently:

1. **P1 (honesty)** — inspect `web/manifest/claims-provenance.json`; every claim has a status and source.
2. **P2 (determinism)** — inspect `hummbl-io/hummbl-governance/hummbl_governance/`; the primitives are deterministic Python.
3. **P3 (in-process)** — `pip install hummbl-governance`; the library runs in your process.
4. **P4 (open-source)** — check https://github.com/hummbl-io/hummbl-governance for Apache 2.0 license.
5. **P5 (boundary honesty)** — inspect the EU AI Act and NIST AI RMF position papers; both state boundaries.
6. **P6 (receipts)** — inspect `_receipts/krineia/primary.jsonl`; the chain is hash-linked and verifiable.
7. **P7 (human authority)** — inspect the authority boundary section in any HUMMBL artifact.
8. **P8 (framework-agnostic)** — inspect `compliance_mapper.py`; the primitives are shared across frameworks.
9. **P9 (public matrices)** — inspect `hummbl-io/hummbl-governance/docs/coverage/`; the matrices are public.
10. **P10 (RSI)** — inspect the case study and this retrospective; HUMMBL uses its own primitives on itself.

If any principle's source cannot be re-verified, open an issue at `hummbl-io/hummbl-production/issues` and the principle will be corrected or removed per CONSTITUTION §3.1.

---

## References

- CONSTITUTION: `CONSTITUTION.md` (§3 protected invariants)
- White paper: `docs/artifacts/WHITE_PAPER_governance_infrastructure.md`
- Competitive analysis: `docs/artifacts/COMPETITIVE_ANALYSIS_ai_governance.md`
- EU AI Act position paper: `docs/artifacts/POSITION_PAPER_eu_ai_act.md`
- NIST AI RMF position paper: `docs/artifacts/POSITION_PAPER_nist_ai_rmf.md`
- Case study: `docs/artifacts/CASE_STUDY_claims_remediation.md`
- Wave 1 retrospective: `docs/artifacts/RETROSPECTIVE_wave_1.md`
- KRINEIA receipt chain: `_receipts/krineia/primary.jsonl`
- Claims manifest: `web/manifest/claims-provenance.json`
- EU AI Act coverage matrix: `hummbl-io/hummbl-governance/docs/coverage/eu-ai-act.md`
- NIST AI RMF coverage matrix: `hummbl-io/hummbl-governance/docs/coverage/nist-ai-rmf.md`
- MULTI_AGENT.md governance model: `hummbl-io/hummbl-governance/MULTI_AGENT.md`

---

## Authority boundary

**Operator** is the human **Principal Agent** for HUMMBL — the goal-owning, value-bearing, accountable agent. **Devin** (and other software agents: Codex, Claude Code, Gemini, OpenCode, Kai, Apex, Nexus, Auditor, Hermes) are **delegated drafting, research, and execution systems**. They can draft, collect, compare, format, inspect, and surface — they cannot confer strategic authority on themselves, promote drafts to live, publish external claims, or redefine strategic goals. This doctrine was drafted by Devin at the direction of the Principal Agent, based on the CONSTITUTION, white paper, position papers, case study, and wave 1 retrospective, and was promoted to live (public) by Principal Agent decision on 2026-06-23. The doctrine is the decision-consistency baseline for all HUMMBL governance work; amendments require the process in §5. This document is **public** — it is intended for external readers (team, agents, customers, assessors) and may be published on hummbl.io.
