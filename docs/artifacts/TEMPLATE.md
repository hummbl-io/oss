# Template: HUMMBL Artifact

> **Usage:** Copy this file to `docs/artifacts/<TYPE>_<subject>.md` and fill in the placeholders. Delete this header block before promoting to live.

**Status:** draft v0.1 (public|private)
**Author:** Operator, HUMMBL Research Institute
**Date:** YYYY-MM-DD
**Tracking:** docs/artifacts/ARTIFACT_MANIFEST.md (item N)
**Reader:** <target reader — who is this for?>
**Decision:** <what decision should the reader make after reading this?>

**TL;DR:** <3-5 sentence summary. The reader should understand the thesis and the ask in one paragraph.>

---

## 1. <Section: problem or context>

<What problem does this artifact address? What is the context the reader needs to understand? For position papers, this is the framework or regulation. For business cases, this is the opportunity. For case studies, this is the customer situation. For market analysis, this is the market landscape.>

---

## 2. <Section: what HUMMBL provides>

<What does HUMMBL do to address the problem? Be specific. Cite source code paths, coverage matrices, primitive names. For position papers, this is the mapping. For business cases, this is the scope. For case studies, this is the response. For market analysis, this is the wedge.>

---

## 3. <Section: what HUMMBL does not provide (boundary)>

<Be honest about the boundary. What does HUMMBL NOT do? What is the customer's responsibility? What is a regulatory or institutional obligation that no software can satisfy? This section is a governance feature — a vendor that claims to "make you aligned" is overclaiming. A vendor that says "here is the technical evidence layer, and here is where your organizational work begins" is telling the truth.>

---

## 4. <Section: why HUMMBL / differentiation>

<Why should the reader choose HUMMBL over alternatives? Cite the competitive analysis. Highlight: deterministic evidence (not LLM-judged), in-process (not SaaS platform), open-source (inspectable), public coverage matrix (no other vendor publishes this), framework-agnostic primitives (one integration serves multiple frameworks), hash-linked receipt chain (verifiable).>

---

## 5. <Section: plan or recommendations>

<What should the reader do next? For position papers, this is the 30-60 day plan. For business cases, this is the funding ask and timeline. For case studies, this is the engagement model. For market analysis, this is the segment prioritization.>

---

## 6. <Section: boundary disclaimer (statutory or framework-specific)>

<For compliance-oriented artifacts, include the statutory boundary. Example for NIST AI RMF: "NIST AI RMF is a voluntary framework, not a regulation. There is no certification body for AI RMF; conformance is self-attested or third-party-assessed via consulting engagements. HUMMBL maps technical primitives to AI RMF subcategories; framework adoption is the customer organization's responsibility.">

<Example for EU AI Act: "HUMMBL is not a Notified Body under EU AI Act Article 31. Conformity assessment for high-risk AI systems requires either internal control (Annex VI) or Notified Body assessment (Annex VII, mandatory for biometric identification). HUMMBL provides the technical evidence layer; the conformity assessment is the provider's and their Notified Body's.">

---

## 7. How to verify this artifact

A reader can re-verify every claim in this artifact independently:

1. **<Claim 1>** — <how to verify (URL, file path, command)>
2. **<Claim 2>** — <how to verify>
3. **<Claim 3>** — <how to verify>

If any claim in this artifact cannot be re-verified, open an issue at `hummbl-io/hummbl-production/issues` and the claim will be corrected or removed per CONSTITUTION §3.1.

---

## References

- <list of source artifacts, URLs, repos, regulations>
- White paper: `docs/artifacts/WHITE_PAPER_governance_infrastructure.md`
- Competitive analysis: `docs/artifacts/COMPETITIVE_ANALYSIS_ai_governance.md`
- Claims manifest: `web/manifest/claims-provenance.json`
- CONSTITUTION: `CONSTITUTION.md` (§3.1 public claim honesty invariant)

---

## Authority boundary

**Operator** is the human **Principal Agent** for HUMMBL — the goal-owning, value-bearing, accountable agent. **Devin** (and other software agents: Codex, Claude Code, Gemini, OpenCode, Kai, Apex, Nexus, Auditor, Hermes) are **delegated drafting, research, and execution systems**. They can draft, collect, compare, format, inspect, and surface — they cannot confer strategic authority on themselves, promote drafts to live, publish external claims, or redefine strategic goals. This <artifact type> was drafted by Devin at the direction of the Principal Agent, based on <source materials>, and was promoted to live (public|private) by Principal Agent decision on YYYY-MM-DD. This document is **public|private** — <intended audience and publication status>.

---

## Per-artifact-type section guide

| Artifact type        | Extra sections                              | Tone                | Typical length |
| -------------------- | ------------------------------------------- | ------------------- | -------------- |
| White paper          | Thesis, architecture, evidence              | Authoritative       | 800-1200 lines |
| Strategic plan       | Phases, milestones, budget                  | Decision-oriented   | 400-600 lines  |
| Risk register        | Risk table, mitigations                     | Operational         | 200-400 lines  |
| Competitive analysis | Vendor table, 2x2 matrix, buyer questions   | Analytical          | 500-800 lines  |
| Business case        | Cost, ROI, alternatives, recommendation     | Decision-oriented   | 400-600 lines  |
| Case study           | Problem, response, outcome, proof           | Narrative           | 300-500 lines  |
| Position paper       | Framework, mapping, boundary, plan          | Compliance-oriented | 400-600 lines  |
| Market analysis      | Size, segmentation, wedge, prioritization   | Strategic           | 400-600 lines  |
| Doctrine             | Principles, invariants, decision rules      | Authoritative       | 200-400 lines  |
| Charter              | Purpose, scope, authority, decision rights  | Authoritative       | 200-400 lines  |
| Evidence pack        | Evidence inventory, verification, packaging | Operational         | 300-500 lines  |
| Playbook             | Steps, roles, decision trees                | Operational         | 200-400 lines  |

---

## Claims checklist

Before promoting to live, verify:

- [ ] Every factual claim in this artifact has a corresponding entry in `web/manifest/claims-provenance.json`
- [ ] Each claim has: id, page, claim, source, source_quote, verified_date, tier (A/B/C), status (validated/unproven/etc.)
- [ ] Tier A claims (primary sources, code, regulations) are validated
- [ ] Tier B claims (secondary sources, analyst reports) are validated and marked with refresh cadence
- [ ] Tier C claims (internal estimates, inferences) are marked "unproven" with notes explaining the inference
- [ ] No claim silently lacks provenance (CONSTITUTION §3.1)

Use `python scripts/add_claims.py <claims.json>` to add claims to the manifest.

## Promotion checklist

Before promoting to live:

- [ ] Artifact follows this template structure
- [ ] Authority boundary section is present and correct
- [ ] Claims are added to the manifest
- [ ] Manifest item status is updated (use `python scripts/update_manifest.py`)
- [ ] KRINEIA receipt is emitted (use `python scripts/emit_receipt.py`)
- [ ] Commit on working branch
- [ ] Cherry-pick to wave branch (use `bash scripts/promote_to_wave_branch.sh`)
- [ ] Bus STATUS posted to hummbl-governance coordination bus

Origin: P4 from RETROSPECTIVE_wave_1.md. Extracted from wave 1 artifact patterns (Days 6-10).
