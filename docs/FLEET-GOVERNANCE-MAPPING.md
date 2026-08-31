# HUMMBL Fleet Governance — Framework Mapping

**Status:** Positioning document
**Date:** 2026-08-21
**Authors:** HUMMBL fleet
**Research basis:** deep-research-mode session, 2026-08-21 (3 lanes, 30 sources)

## Purpose

HUMMBL governs an agent fleet with runtime primitives (kill switch,
circuit breaker, cost governor, delegation tokens). This document maps
those primitives to existing AI governance frameworks, identifies where
the frameworks provide coverage and where they are silent, and positions
HUMMBL's fleet governance relative to the current regulatory and
standards landscape.

This is both a due-diligence artifact (evidence that HUMMBL has mapped
its governance to external frameworks) and a differentiator (HUMMBL
operates where no framework currently provides requirements).

---

## 1. The governance vacuum

**Finding (HIGH confidence):** No major AI governance framework governs
a fleet-of-agents as a unit. All three major frameworks use "an AI system"
(singular) as their governance subject.

| Framework | Governance unit | Fleet-of-agents coverage |
|-----------|----------------|--------------------------|
| NIST AI RMF 1.0 | An AI system (lifecycle) | None — no subcategory addresses fleet orchestration, cascade failure, or runtime cost governors |
| ISO/IEC 42001:2023 | Organization-level (AIMS) | None — certifiable management system, but no runtime primitives for fleet coordination |
| EU AI Act (Regulation 2024/1689) | AI system / GPAI model | None — agents are "covered in principle" but the Commission's own FAQ calls considerations "preliminary" |

The EU Commission AI Office FAQ states: *"while AI agents are not a
separate category of AI under the AI Act, the definitions of an AI system
in Article 3(1) AI Act and of a GPAI model in Article 3(63) AI Act are
sufficient to cover AI agents."* Independent legal analysis (Jones,
"The Hidden Layer," EU Law Live 2026) identifies a structural gap: the
Act's binary provider/deployer distinction cannot accommodate fleet
orchestration layers.

An arXiv unified taxonomy paper (2026) confirms *"the widening gap
between all three instruments and general-purpose and agentic AI."*

**Implication:** HUMMBL's fleet governance primitives are not just best
practice — they occupy territory where no external framework provides
mandatory or even advisory requirements. This is simultaneously a
competitive moat (HUMMBL has governance primitives others lack) and a
regulatory risk (no external validation signal; regulators may fill the
void ex-post with unfavorable interpretations).

---

## 2. Primitive-to-framework mapping

| HUMMBL Primitive | NIST AI RMF | ISO/IEC 42001 | EU AI Act | Academic backing | Emerging standards |
|------------------|-------------|---------------|-----------|------------------|-------------------|
| **Kill switch** | Govern 1.7 (decommissioning) | Annex A (lifecycle controls) | Art. 14 (human oversight) | FAccT 2024 — real-time monitoring | Not standardized |
| **Circuit breaker** | Manage 1.1 (proceed/stop decision) | Clause 8 (operational controls) | Art. 9 (risk mgmt), Art. 15 (robustness) | Swiss Cheese Model (arXiv 2408.02205) | Microsoft ACS `deny`/`escalate` verdicts |
| **Cost governor** | Govern 1.3 (risk tolerance) | Clause 6 (planning) | Art. 9 (risk mgmt) | GOVSIM commons failure (arXiv 2404.16698) | Not standardized |
| **Delegation tokens** | Govern 2.1 (roles/responsibilities) | Annex A (accountability) | Art. 25 (value chain responsibilities) | FAccT 2024 — agent identifiers | HDP (IETF provenance); DeepMind DCT (paper, not IETF); AAT (`draft-niyikiza-oauth-attenuating-agent-tokens-01`); `delegation_chain` JWT (`draft-liu-oauth-chain-delegation-00`) |
| **Agent fleet as unit** | **No coverage** | **No coverage** | **No coverage** | Federated governance (emerging) | ADCS spec |

### Sources

- **NIST AI RMF 1.0** — [airc.nist.gov/airmf-resources/airmf/5-sec-core/](https://airc.nist.gov/airmf-resources/airmf/5-sec-core/) (Tier 2, primary)
- **NIST AI 600-1 (GenAI Profile)** — [nvlpubs.nist.gov/nistpubs/ai/NIST.AI.600-1.pdf](https://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.600-1.pdf) (Tier 2, primary)
- **EU AI Act FAQ on agents** — [ai-act-service-desk.ec.europa.eu](https://ai-act-service-desk.ec.europa.eu/en/ai-act/faq/how-are-ai-agents-addressed-within-ai-act-0) (Tier 2, primary)
- **ISO/IEC 42001:2023** — [iso.org/standard/42001](https://www.iso.org/standard/42001) (Tier 2, primary)
- **FAccT 2024 — Visibility into AI Agents** — [facctconference.org/static/papers24/facct24-63.pdf](https://facctconference.org/static/papers24/facct24-63.pdf) (Tier 1, peer-reviewed)
- **Swiss Cheese Model for AI Safety** — [arxiv.org/abs/2408.02205](https://arxiv.org/abs/2408.02205) (Tier 1 preprint, CSIRO)
- **"The Hidden Layer" (EU Law Live)** — [doi.org/10.5281/zenodo.19954774](https://doi.org/10.5281/zenodo.19954774) (Tier 3, legal practitioner)
- **IETF HDP Draft** — [ietf.org/archive/id/draft-helixar-hdp-agentic-delegation-01.html](https://www.ietf.org/archive/id/draft-helixar-hdp-agentic-delegation-01.html) (Tier 4, standards-track)

---

## 3. What HUMMBL has that frameworks do not require

### 3.1 Runtime cost governance

The GOVSIM simulation (arXiv 2404.16698) applied Ostrom's commons
governance logic to LLM multi-agent environments and found that **all
but the most powerful LLMs fail to achieve sustainable equilibrium** —
survival rate below 54%. The failure mode is inability to reason about
long-term group effects; individually rational agents collectively
over-consume resources.

HUMMBL's cost governor is therefore not just a financial control — it is
a **commons-protection mechanism** with academic backing showing it is
necessary for sustainable fleet operation. No major framework requires
or even addresses runtime cost governance for agent fleets.

### 3.2 Cryptographic delegation chains

HUMMBL's delegation tokens implement:
- HMAC-SHA256 signed tokens (symmetric)
- Time-bounded expiry (default 120 minutes)
- Task/contract binding (TokenBinding)
- Least-privilege enforcement (ops_allowed, resource_selectors, caveats)
- Fail-closed authentication (rejects on any anomaly)

Related work is three layers, not one IETF token:
- **HDP (Human Delegation Provenance)** — IETF provenance draft
- **DCT (Delegation Capability Tokens)** — DeepMind paper (not IETF)
- **AAT** — `draft-niyikiza-oauth-attenuating-agent-tokens-01`
- **`delegation_chain` JWT** — `draft-liu-oauth-chain-delegation-00`

HUMMBL's design principles match (time-bounding, least-privilege, signed)
but the wire format diverges (HMAC-SHA256 symmetric vs. Ed25519
asymmetric; no chain structure vs. append-only chain). See
`docs/DELEGATION-IETF-GAP-ANALYSIS.md` for the detailed audit.

### 3.3 Circuit-breaker layered guardrails

The Swiss Cheese Model (arXiv 2408.02205) proposes multi-layered
guardrails across pipeline stages (input -> plan -> tool -> output) where
each layer has holes but stacking prevents hole alignment. HUMMBL's
circuit breaker implements this architecture. Microsoft's Agent Control
Specification (ACS) defines five normalized governance verdicts
(`allow`, `warn`, `deny`, `escalate`, `transform`) — HUMMBL's circuit
breaker should be compared against ACS's model for interoperability.

---

## 4. Compliance posture

### 4.1 ISO 42001 + NIST AI RMF (dual adoption, recommended)

NIST publishes an official crosswalk
(`airc.nist.gov/docs/NIST_AI_RMF_to_ISO_IEC_42001_Crosswalk.pdf`) enabling
dual compliance without duplicative effort. NIST provides the operating
model (Govern/Map/Measure/Manage); ISO 42001 provides the certifiable
wrapper (PDCA management system, Annex A controls, third-party audit).

**Recommendation:** HUMMBL should pursue ISO 42001 certification with
NIST AI RMF as the operating model. The AIMS structure provides the audit
wrapper; HUMMBL's runtime primitives satisfy the operational controls.

### 4.2 EU AI Act (custom mapping required)

The EU AI Act's accountability structure is binary: "providers" vs
"deployers." An agent fleet with hierarchical delegation and peer-mesh
communication creates a multi-dimensional accountability graph that
Article 25 (value chain responsibilities) cannot absorb.

**Recommendation:** HUMMBL should preemptively document each agent's
provider/deployer classification and map its meta-governor layer to
Article 25 as a value-chain intermediary. This is lower risk than waiting
for regulatory interpretation. Note: the May 2026 "Digital Omnibus"
amendments may alter this structure — re-audit when the amendment text
is reflected in EU AI Act Service Desk resources.

### 4.3 Liability and insurance

Oxford Martin AIGI (Nov 2024) found no insurer has a mature AI agent
fleet product. HUMMBL's cost governor is the closest analogue to what
insurers would want as an underwriting signal, but no carrier currently
prices this. The report recommends strict liability regimes for a subset
of AI agent harms and mandated insurance for certain applications.

**Recommendation:** Document HUMMBL's governance primitives as
underwriting-relevant signals (kill switch = harm-termination capability,
cost governor = financial exposure cap, audit log = incident
reconstructability). This positions HUMMBL favorably when the insurance
market matures.

---

## 5. Competitive positioning

HUMMBL's fleet governance is novel in three dimensions:

1. **Fleet-as-unit governance** — no framework or competitor governs an
   agent fleet as a unit. HUMMBL's primitives (kill switch, circuit
   breaker, cost governor, delegation tokens) are fleet-scoped, not
   model-scoped.

2. **Runtime enforcement, not just policy** — frameworks define what
   should be governed; HUMMBL implements how it is enforced at runtime.
   The Swiss Cheese Model validates layered runtime guardrails; HUMMBL
   ships them.

3. **Cryptographic delegation** — HUMMBL's delegation tokens predate the
   IETF standardization effort but align with its design principles.
   This is a head start that becomes a compliance asset when the IETF
   drafts ratify.

**Risk to monitor:** Operating in a governance vacuum means HUMMBL's
governance choices have no external validation signal. If a regulator
later defines fleet governance requirements that diverge from HUMMBL's
design, HUMMBL may face costly refactoring. Mitigation: engage with
IETF delegation chain drafts (R3), monitor NIST AI RMF 1.0 revision
(announced April 2026), and re-audit EU AI Act after Digital Omnibus
amendments.

---

## 6. Decision log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-08-21 | Document fleet governance mapping (this file) | Due diligence + differentiator; HUMMBL operates in a validated governance vacuum |
| 2026-08-21 | Pursue ISO 42001 + NIST AI RMF dual adoption | Official crosswalk enables dual compliance; AIMS provides audit wrapper, NIST provides operating model |
| 2026-08-21 | Preemptive EU AI Act provider/deployer self-classification | Article 25 cannot absorb fleet orchestration; self-classification is lower risk than waiting for regulatory interpretation |
| 2026-08-21 | Audit delegation tokens against IETF HDP/DCT drafts | Align wire format before drafts ratify; avoid costly refactoring (see DELEGATION-IETF-GAP-ANALYSIS.md) |
| 2026-08-31 | IETF delegation gap analysis landed; DCT is not IETF | Analysis at `docs/DELEGATION-IETF-GAP-ANALYSIS.md` (not a claim of alignment). HDP = IETF provenance; DCT = DeepMind paper; AAT = `draft-niyikiza-oauth-attenuating-agent-tokens-01` |
| 2026-08-21 | Document cost governor as commons-protection mechanism | GOVSIM (arXiv 2404.16698) validates runtime cost governance as necessary for sustainable fleet operation |

---

## 7. Open questions

1. **NIST AI RMF 1.0 revision** (announced April 2026) — may incorporate
   agentic AI more deeply. Re-audit all NIST citations when published.
2. **EU AI Act Digital Omnibus amendments** (May 2026) — may alter
   provider/deployer accountability structure. Re-audit when reflected
   in EU AI Act Service Desk resources.
3. **IETF delegation drafts ratification** — HDP is an IETF provenance
   draft; DCT is a DeepMind paper (not IETF); AAT is
   `draft-niyikiza-oauth-attenuating-agent-tokens-01`. Check quarterly;
   engage if HUMMBL's design diverges from the draft trajectory.
4. **Microsoft ACS alignment** — should HUMMBL's circuit breaker adopt
   the ACS verdict model (`allow`/`warn`/`deny`/`escalate`/`transform`)
   for interoperability with ACS-adapter frameworks (LangChain, CrewAI,
   OpenAI Agents, LangGraph, AutoGen)?
5. **Insurance market maturity** — when will carriers price fleet
   governance primitives as underwriting signals? Monitor Oxford Martin
   AIGI publications.

---

*Research basis: deep-research-mode session 2026-08-21, Lane 3 (AI
governance frameworks for agent fleets), 10 sources, all verified live.
See session receipt for full source tiering and claim-honesty labels.*
