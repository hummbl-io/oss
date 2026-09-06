# Charter: HUMMBL, LLC

**Status:** live v1.0 (public)
**Author:** Operator, HUMMBL, LLC
**Date:** 2026-06-23
**Tracking:** docs/artifacts/ARTIFACT_MANIFEST.md (item 12)
**Reader:** steward, operators, Board, external partners
**Decision:** what HRI may decide, what it must escalate, how it operates

**TL;DR:** HUMMBL, LLC (HRI) is the steward of HUMMBL's governance doctrine, constitutions, and normative files. HRI is not a legal entity; it is a functional role held by Operator as Principal Agent, with delegation to trusted agents and human collaborators. This charter defines HRI's purpose, scope, authority, decision rights, and escalation rules. HRI may decide doctrine, standards, and coverage matrices; HRI must escalate funding, legal commitments, and strategic pivots to the Principal Agent.

---

## 1. Purpose

HUMMBL, LLC exists to:

1. **Steward HUMMBL's governance doctrine** — the 10 AI governance principles (`DOCTRINE_ai_governance.md`) and their amendments
2. **Steward HUMMBL's constitutions** — the repo-level constitutions (`CONSTITUTION.md` in each HUMMBL repo) and the machine-global AGENTS.md
3. **Steward HUMMBL's normative files** — claims manifest, public namespace, public boundaries, ADRs, CODEOWNERS
4. **Author and maintain coverage matrices** — EU AI Act, NIST AI RMF, and future frameworks
5. **Author and maintain public artifacts** — white papers, position papers, case studies, market analyses, business cases, evidence packs, playbooks
6. **Convene the Board** — the AI Board of Directors that reviews high-stakes decisions
7. **Publish research** — the HUMMBL research corpus (docs/research/, cognitive ledger, evidence docs)

HRI is the **stewardship layer** of HUMMBL. It is not the engineering layer (that is the engineering agents), not the operations layer (that is hummbl-governance), and not the commercial layer (that is the Principal Agent's business development). HRI stewards the doctrine, the constitutions, and the public artifacts.

---

## 2. Scope

### In scope

HRI has authority over:

| Domain                | Examples                                                              | Authority                                |
| --------------------- | --------------------------------------------------------------------- | ---------------------------------------- |
| **Doctrine**          | AI governance principles, amendment process                           | Author + amend (per doctrine §5)         |
| **Constitutions**     | Repo-level CONSTITUTION.md files                                      | Propose amendments (per constitution §7) |
| **Normative files**   | claims-provenance.json, public-namespace.json, public-boundaries.json | Author + maintain                        |
| **Coverage matrices** | EU AI Act, NIST AI RMF, future frameworks                             | Author + maintain                        |
| **Public artifacts**  | White papers, position papers, case studies, market analyses          | Author + promote (per manifest)          |
| **ADRs**              | Architecture Decision Records                                         | Author + maintain                        |
| **Research corpus**   | docs/research/, cognitive ledger, evidence docs                       | Author + maintain                        |
| **Board convening**   | AI Board of Directors meetings                                        | Convene + facilitate                     |

### Out of scope

HRI does NOT have authority over:

| Domain                         | Owner                                          | Why                                                                    |
| ------------------------------ | ---------------------------------------------- | ---------------------------------------------------------------------- |
| **Engineering implementation** | Engineering agents (Devin, Codex, Claude Code) | HRI defines what; engineering builds how                               |
| **Operations**                 | hummbl-governance platform                     | HRI defines governance; operations runs the platform                   |
| **Commercial**                 | Principal Agent (Operator)                       | HRI does not sign contracts, set prices, or close deals                |
| **Legal**                      | Principal Agent + counsel                      | HRI does not provide legal advice; legal commitments need PA + counsel |
| **Funding**                    | Principal Agent + Board                        | HRI recommends; PA and Board decide                                    |
| **Strategic pivots**           | Principal Agent + Board                        | HRI assesses; PA and Board decide                                      |
| **Personnel**                  | Principal Agent                                | HRI does not hire, fire, or assign personnel                           |

---

## 3. Authority and decision rights

### Decision matrix

| Decision type                            | HRI may decide             | HRI must escalate              | Escalation path                     |
| ---------------------------------------- | -------------------------- | ------------------------------ | ----------------------------------- |
| **Doctrine amendment (P2,3,4,5,8,9,10)** | Yes — per doctrine §5      | No                             | —                                   |
| **Doctrine amendment (P1,6,7)**          | Propose only               | Yes — constitutional amendment | PA + KRINEIA receipt                |
| **Constitution amendment**               | Propose only               | Yes — per constitution §7      | PA + ADR + KRINEIA receipt          |
| **New coverage matrix**                  | Yes                        | No                             | —                                   |
| **Coverage matrix update**               | Yes                        | No                             | —                                   |
| **New public artifact**                  | Draft + recommend          | Yes — promote to live          | PA approval + KRINEIA receipt       |
| **Artifact status change**               | Propose                    | Yes — promote/demote           | PA approval + KRINEIA receipt       |
| **ADR**                                  | Yes — author + maintain    | No (unless constitutional)     | —                                   |
| **Research publication**                 | Yes                        | No                             | —                                   |
| **Board convening**                      | Yes — convene + facilitate | No                             | —                                   |
| **Funding allocation**                   | Recommend only             | Yes                            | PA + Board                          |
| **Legal commitment**                     | No                         | Yes                            | PA + counsel                        |
| **Strategic pivot**                      | Assess only                | Yes                            | PA + Board                          |
| **Personnel**                            | No                         | Yes                            | PA                                  |
| **Public claim on hummbl.io**            | Draft + recommend          | Yes                            | PA approval + claims manifest entry |

### The escalation principle

HRI's default is to **draft, recommend, and escalate**. HRI does not make decisions that require strategic authority, legal commitment, or funding allocation. Those decisions go to the Principal Agent (and, for funding and strategic pivots, to the Board).

This is consistent with Doctrine Principle 7 (human authority over agent action): HRI is a functional role held by the Principal Agent with delegation to agents. When HRI acts through an agent, the agent is drafting and recommending; the Principal Agent is deciding.

---

## 4. Structure

### Roles

| Role             | Held by                                                          | Authority                                                          |
| ---------------- | ---------------------------------------------------------------- | ------------------------------------------------------------------ |
| **Director**     | Operator (Principal Agent)                                  | Final authority on all HRI decisions                               |
| **Steward**      | Operator (delegated to trusted agents)                      | Day-to-day stewardship of doctrine, constitutions, normative files |
| **Researcher**   | Agents (Devin, Codex, Claude Code, Gemini) + human collaborators | Author research, draft artifacts, maintain coverage matrices       |
| **Board member** | AI Director personas (per Board Constitution Registry)           | Review high-stakes decisions, ask questions, give verdicts         |
| **Operator**     | Agents (Kai, Apex, Nexus, Auditor, Hermes)                       | Execute HRI decisions, maintain receipts, audit compliance         |

### The Director

The Director is the Principal Agent (Operator). The Director:

- Holds final authority on all HRI decisions
- Approves all promotions to live (public or private)
- Approves all funding allocations
- Approves all strategic pivots
- Approves all legal commitments
- Convenes the Board when needed
- Is the single point of accountability for HRI's outputs

### The Steward

The Steward role is held by the Director and delegated to trusted agents. The Steward:

- Maintains the doctrine, constitutions, and normative files
- Authors and updates coverage matrices
- Drafts public artifacts
- Emits KRINEIA receipts for governance actions
- Convenes the Board on the Director's behalf
- Is the single point of responsibility for HRI's stewardship

### The Board

The Board is the AI Board of Directors (per the Board Constitution Registry). The Board:

- Reviews high-stakes decisions (funding, strategic pivots, constitutional amendments)
- Asks questions of the Director
- Gives a verdict (UNANIMOUS_ACCEPT, ACCEPT_WITH_CONDITIONS, DEFER, REJECT)
- Is advisory — the Director retains final authority
- Is convened by the Steward on the Director's behalf

### Researchers and Operators

Researchers and Operators are agents and human collaborators who execute HRI's work. They:

- Author research and draft artifacts
- Maintain coverage matrices
- Execute HRI decisions
- Maintain receipts and audit compliance
- Cannot promote artifacts to live (that is the Director's)
- Cannot make strategic decisions (that is the Director's + Board's)

---

## 5. Operating model

### How HRI makes decisions

1. **Draft** — a researcher or steward drafts the decision (doctrine amendment, artifact, coverage matrix update)
2. **Review** — the steward reviews the draft for doctrine consistency
3. **Recommend** — the steward recommends the draft to the Director
4. **Decide** — the Director decides (accept, reject, defer)
5. **Receipt** — if accepted, the steward emits a KRINEIA receipt
6. **Publish** — the steward publishes the decision (update the manifest, the doctrine, the constitution, the coverage matrix)

### How HRI convenes the Board

1. **Trigger** — a high-stakes decision is pending (funding, strategic pivot, constitutional amendment)
2. **Convene** — the steward convenes the Board via the board-meeting-orchestrator skill
3. **Brief** — the steward briefs the Board on the decision
4. **Questions** — each Board member asks questions of the Director
5. **Answers** — the Director answers in writing
6. **Verdict** — the Board gives a verdict (UNANIMOUS_ACCEPT, ACCEPT_WITH_CONDITIONS, DEFER, REJECT)
7. **Decide** — the Director decides (the Board is advisory)
8. **Receipt** — the steward emits a KRINEIA receipt for the Board review

### How HRI amends the doctrine

Per Doctrine §5:

1. **Propose** — any agent or human proposes via a bus PROPOSAL
2. **Review** — the Director and Board review
3. **Decide** — the Director decides
4. **Receipt** — KRINEIA receipt emitted
5. **Publish** — doctrine updated, manifest updated

For constitutional invariants (Principles 1, 6, 7), the process requires a constitutional amendment (CONSTITUTION §7): a PR, an ADR, a KRINEIA receipt, and human approval.

---

## 6. Boundary disclaimer

HRI is a **functional role**, not a legal entity. HRI is not incorporated, has no bank account, cannot sign contracts, and has no legal standing. HRI is the name for the stewardship function that Operator performs as Principal Agent, with delegation to trusted agents and human collaborators.

HRI's outputs (doctrine, constitutions, coverage matrices, public artifacts) are HUMMBL's outputs. HUMMBL is the brand; HRI is the stewardship function. The legal entity behind HUMMBL is Operator's sole proprietorship (or future entity, if incorporated). HRI does not change this.

HRI's authority is **internal to HUMMBL**. HRI does not claim authority over other organizations' governance. HRI's doctrine is HUMMBL's self-adopted doctrine; other organizations may adopt different doctrines.

---

## 7. How to verify this charter

A reader can re-verify every claim in this charter independently:

1. **HRI is the steward** — inspect `CONSTITUTION.md` §5 ("Steward: HUMMBL, LLC").
2. **HRI stewards the doctrine** — inspect `docs/artifacts/DOCTRINE_ai_governance.md` (authored by HRI).
3. **HRI stewards coverage matrices** — inspect `hummbl-io/hummbl-governance/docs/coverage/` (maintained by HRI).
4. **HRI convenes the Board** — inspect the Board review log in `docs/artifacts/ARTIFACT_MANIFEST.md` (Board meeting 2026-06-23).
5. **HRI is not a legal entity** — this is a self-declaration; verify by checking that no incorporation documents exist for "HUMMBL, LLC" (it is a functional role, not a legal entity).
6. **The Director is the Principal Agent** — inspect the authority boundary section in any HUMMBL artifact.
7. **The Board is advisory** — inspect the Board Constitution Registry and the board-meeting-orchestrator skill.

If any claim in this charter cannot be re-verified, open an issue at `hummbl-io/hummbl-production/issues` and the claim will be corrected or removed per CONSTITUTION §3.1.

---

## References

- CONSTITUTION: `CONSTITUTION.md` (§5 authority, §7 amendment)
- Doctrine: `docs/artifacts/DOCTRINE_ai_governance.md`
- White paper: `docs/artifacts/WHITE_PAPER_governance_infrastructure.md`
- Supporting private records are omitted from this public tree; claims depending on them cannot be independently re-verified here.
- Board Constitution Registry: `hummbl-io/hummbl-governance/.agents/board/BOARD_CONSTITUTION_REGISTRY.md`
- Board meeting orchestrator: `board-meeting-orchestrator` skill
- Claims manifest: `web/manifest/claims-provenance.json`
- KRINEIA receipt chain: `_receipts/krineia/primary.jsonl`
- MULTI_AGENT.md governance model: `hummbl-io/hummbl-governance/MULTI_AGENT.md`

---

## Authority boundary

**Operator** is the human **Principal Agent** for HUMMBL — the goal-owning, value-bearing, accountable agent. **Devin** (and other software agents: Codex, Claude Code, Gemini, OpenCode, Kai, Apex, Nexus, Auditor, Hermes) are **delegated drafting, research, and execution systems**. They can draft, collect, compare, format, inspect, and surface — they cannot confer strategic authority on themselves, promote drafts to live, publish external claims, or redefine strategic goals. This charter was drafted by Devin at the direction of the Principal Agent, based on the CONSTITUTION, doctrine, and existing HUMMBL governance artifacts, and was promoted to live (public) by Principal Agent decision on 2026-06-23. HRI is a functional role held by the Principal Agent; this charter documents that role. This document is **public** — it is intended for external readers (steward, operators, Board, partners) and may be published on hummbl.io.
