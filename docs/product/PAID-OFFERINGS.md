# HUMMBL Paid Offerings Definition

> **Status:** Draft / Active Proposal  
> **Issue:** [oss#216](https://github.com/hummbl-io/oss/issues/216)  
> **Rule:** Reduce scope, not price. Deliver high-value, bounded diagnostic bridges from existing production capabilities. Zero new platform infrastructure without validated customer demand.

---

## Executive Summary

HUMMBL maintains 47 in-tree packages, mature governance primitives, schema validation harnesses, and automated security boundaries. Rather than constructing speculative SaaS platforms, this document packages mature, existing capabilities into 5 concrete, maintainable paid offerings.

Each offering defines:
- The exact initial customer profile (ICP) and urgent problem
- A bounded, tangible deliverable
- Fixed-scope pricing with clear support boundaries
- Direct linkage to maintained in-tree packages and tools
- A low-friction customer demand validation step

```
                     ┌────────────────────────────────────────┐
                     │          Free Open Source              │
                     │  (PyPI packages, schemas, public docs) │
                     └───────────────────┬────────────────────┘
                                         │
                                         ▼
                     ┌────────────────────────────────────────┐
                     │   Paid Diagnostic Bridges ($233–$500)  │
                     │  • Agentic Workflow Intake ($233)      │
                     │  • AI Governance Micro-Audit ($500)    │
                     └───────────────────┬────────────────────┘
                                         │
                                         ▼
                     ┌────────────────────────────────────────┐
                     │    Scoped Technical Sprints ($3K–$15K) │
                     │  • Eval Harness & Red-Team ($3,500)    │
                     │  • Supply Chain & CI Integrity ($4,500)│
                     │  • ARCANA Architecture Review ($6,000) │
                     └────────────────────────────────────────┘
```

---

## Candidate Offerings Matrix

| Offering | Target Customer | Maintained Source Surface | Deliverable | Pricing Model | Delivery Time |
|---|---|---|---|---|---|
| **1. AI Governance & Compliance Gap Audit** | AI/ML Engineering Leads, Compliance Officers | `packages/python/hummbl-governance` (51 primitives, compliance mapper) | Governance Scorecard + Remediation Matrix | $500 (Diagnostic) / $5,000 (Full Audit) | 48 hours / 5 days |
| **2. Agentic Contract & State Integrity Review** | Multi-Agent Systems Architects, CTOs | `packages/python/hummbl-contracts`, CLP protocol | Validated Contract Schemas + State Transition Test Suite | $233 (Intake) / $3,500 (Sprint) | 24 hours / 3 days |
| **3. Agent Fleet Eval & Safety Benchmark** | AI Product Teams, Head of AI | `agent-eval-harness`, golden-fixture suite | Multi-turn Benchmark Report + Adversarial Failure Analysis | $3,500 fixed sprint | 4 days |
| **4. Release Integrity & Supply Chain Guard** | SecOps, Platform Leads, DevSecOps | `tools/scripts/`, `hummbl_governance` release receipts | Hash-Locked Build Lockfile + Gitleaks & Boundary CI Gate | $4,500 fixed sprint | 3 days |
| **5. ARCANA Strategic Architecture Review** | Enterprise Architects, Venture Technical Partners | `packages/python/arcana` | Dialectical Debate Brief + Technical Debt Ledger | $6,000 fixed sprint | 5 days |

---

## Offering 1: AI Governance & Compliance Gap Audit

### 1. Initial Customer
- **Target Persona:** Head of AI, VP Engineering, or Chief Compliance Officer at growth-stage AI startups (Series A–C) deploying customer-facing LLM agents.
- **Trigger Event:** Customer security questionnaire, SOC 2 / ISO 42001 audit requirement, EU AI Act compliance preparation, or enterprise procurement block.

### 2. Core Problem
Companies deploying LLMs lack enforceable runtime guardrails and audit trails. Standard checklists are descriptive and non-executable; existing compliance tools do not integrate directly into continuous integration or runtime agent loops.

### 3. Concrete Deliverable
- **Executable Scorecard:** A machine-readable JSON/Markdown governance assessment evaluated against EU AI Act, NIST AI RMF, and ISO 42001.
- **Enforcement Code Pack:** Production-ready Python snippets integrating `hummbl_governance` primitives (`capability_fence`, `admission_control`, `audit_log`, `schema_validator`) directly into the customer's codebase.
- **Remediation Priority Matrix:** Traffic-light risk matrix categorizing high-risk agent autonomous actions with mitigation paths.

### 4. Pricing Model & Payment
- **Micro-Audit:** $500 one-time flat fee. Pre-paid via Stripe Payment Link (`prod_UpAPID4unEzKtQ`).
- **Full Governance Sprint:** $5,000 flat fee (scope: up to 3 core agent workflows).
- **No discounts:** Scope is reduced to maintain margins, never price.

### 5. Support Boundary
- **Included:** 1 asynchronous code review, 1 written deliverable report, and a 30-minute debrief call.
- **Out of Scope:** Ongoing legal representation, direct real-time on-call support, or continuous custom software maintenance beyond the 14-day delivery window.

### 6. Maintained Source Surface
- `packages/python/hummbl-governance` (51 active primitives, stdlib-only).
- `hummbl_governance/compliance_mapper.py` and `hummbl_governance/capability_fence.py`.

### 7. Demand Validation Step
- **Smoke Test:** Direct outreach to 10 founders/CTOs with recent SOC 2 / compliance announcements offering the $500 Micro-Audit with a guaranteed 48-hour turnaround.
- **Success Gate:** 2 prepaid diagnostic orders before developing automated reporting portals.

---

## Offering 2: Agentic Contract & State Integrity Review

### 1. Initial Customer
- **Target Persona:** Lead Architect or Staff Engineer building multi-agent systems, autonomous coding assistants, or complex tool-calling pipelines.
- **Trigger Event:** Unpredictable multi-agent failures, corrupt shared state, JSON hallucination breaking tool calls, or runaway API billing loops.

### 2. Core Problem
Multi-agent systems suffer from informal schemas: prompt-based state transitions drift, unstructured tool arguments fail silently, and unvalidated agent message buses corrupt operational context.

### 3. Concrete Deliverable
- **Formal Contract Schemas:** Standard JSON Schema Draft 2020-12 schemas for all inter-agent messages, tool payloads, and shared ledger states.
- **Offline Conformance Test Suite:** A zero-dependency test harness built on `hummbl-contracts` validating all state mutations offline in CI.
- **Intake Review Receipt:** Cryptographically verified findings receipt documenting schema edge cases (e.g. enum/const mismatches, nested property leaks).

### 4. Pricing Model & Payment
- **Workflow Intake Review:** $233 flat fee. Pre-paid via Stripe Payment Link (`prod_UpAOk0nopLsoij`).
- **Contract Hardening Sprint:** $3,500 fixed scope (up to 5 inter-agent message interfaces).

### 5. Support Boundary
- **Included:** Contract schema files, integration test suite patch, and written architectural findings.
- **Out of Scope:** Rewriting customer model prompts, hosting customer coordination buses, or vendor API cost reimbursement.

### 6. Maintained Source Surface
- `packages/python/hummbl-contracts` (CLP ledger schemas, stdlib-only schema validator).
- `schemas/public/` contract validation specifications.

### 7. Demand Validation Step
- **Smoke Test:** Publish a technical case study demonstrating how `hummbl-contracts` eliminated runtime agent state drift, linked to the $233 intake review link.
- **Success Gate:** 3 paid reviews from inbound developers.

---

## Offering 3: Agent Fleet Evaluation & Safety Benchmark

### 1. Initial Customer
- **Target Persona:** Product Managers and AI Tech Leads deploying LLM applications where model upgrades or prompt changes frequently cause silent regression.
- **Trigger Event:** Model provider deprecation (e.g., migrating from GPT-4o to Claude 3.5 Sonnet or Gemini 1.5 Pro), customer-reported hallucination incidents, or pre-launch safety reviews.

### 2. Core Problem
Teams rely on subjective eyeballing or expensive manual testing to evaluate agents. They lack deterministic golden test fixtures, multi-turn regression suites, and automated adversarial probes.

### 3. Concrete Deliverable
- **Custom Golden-Fixture Suite:** 25–50 domain-specific evaluation test cases with deterministic scoring rubrics.
- **Automated Regression Runner:** Offline CI-compatible eval runner producing machine-readable pass/fail and latency/cost metrics.
- **Red-Team Vulnerability Audit:** Adversarial test report probing jailbreak susceptibility, prompt injection, and unauthorized capability escalation.

### 4. Pricing Model & Payment
- **Evaluation Sprint:** $3,500 flat fee per agent workflow.
- Invoiced 50% upfront, 50% upon delivery of the golden test suite and scorecard.

### 5. Support Boundary
- **Included:** Golden test suite code, evaluation report, and 1 benchmark run comparison across up to 3 model providers.
- **Out of Scope:** LLM inference API costs (customer provides API keys or executes locally).

### 6. Maintained Source Surface
- `hummbl-io/agent-eval-harness` and `packages/python/hummbl-governance/tests/fixtures/`.
- Local evaluation runners and rubric validators.

### 7. Demand Validation Step
- **Smoke Test:** Offer a free 5-sample regression probe to 5 prospect companies; convert prospects with identified regressions to the $3,500 full evaluation sprint.
- **Success Gate:** 1 converted sprint agreement.

---

## Offering 4: Software Supply Chain & Release Integrity Guard

### 1. Initial Customer
- **Target Persona:** Head of Platform, DevSecOps Lead, or VP Infrastructure distributing open-source or commercial Python/Node packages.
- **Trigger Event:** Dependency security alerts, PyPI package account compromise concerns, customer demands for reproducible builds / SBOMs, or CI runner security audits.

### 2. Core Problem
Modern Python and Node monorepos face supply-chain attacks, mutable build environments, unpinned CI actions, and accidental secret leakage to public repos.

### 3. Concrete Deliverable
- **Deterministic Build Lockfiles:** Hash-locked pip/uv build environment configurations (`requirements-build.lock`) preventing dependency tampering.
- **Fail-Closed Boundary CI Pipeline:** Pre-configured GitHub Actions workflows enforcing:
  - Immutable SHA-pinned GitHub Actions.
  - Fail-closed secret and credential denylist scanning.
  - Self-hosted runner boundary isolation (preventing untrusted PR code execution).
- **Public Provenance & SBOM Record:** Machine-readable `PROVENANCE.md` and external import manifests.

### 4. Pricing Model & Payment
- **Security & Integrity Sprint:** $4,500 fixed scope.

### 5. Support Boundary
- **Included:** CI workflow configuration, build lockfile generation scripts, and verification test suite.
- **Out of Scope:** Remediation of third-party upstream CVEs within customer libraries.

### 6. Maintained Source Surface
- `tools/scripts/check_boundary_patterns.py`, `tools/scripts/validate_workflows.py`, `tools/scripts/check_rights_distribution.py`.
- `.github/workflows/boundary-check.yml` and `.github/scripts/lock_build_env.py`.

### 7. Demand Validation Step
- **Smoke Test:** Publish an open-source security audit highlighting common GitHub Actions runner vulnerabilities and offering the 3-day hardening sprint.
- **Success Gate:** 1 signed engagement before extending scripts to additional package ecosystems.

---

## Offering 5: ARCANA Strategic Architecture Review

### 1. Initial Customer
- **Target Persona:** CTOs, Solo Technical Founders, or Venture Partners evaluating deep technical bets and architectural architecture risks before deployment or investment.
- **Trigger Event:** Major architectural pivot, microservice vs monorepo dilemma, AI stack selection, or technical due diligence.

### 2. Core Problem
Founders and engineering leaders suffer from confirmation bias and decision fatigue when evaluating technical architecture, frequently choosing over-complex stacks that drain runway.

### 3. Concrete Deliverable
- **Adversarial Dialectical Brief:** A structured, formal debate document examining Thesis, Antithesis, and Synthesis for the proposed architecture.
- **Gap & Technical Debt Ledger:** Quantitative accounting of architectural coupling, dependency risks, and maintenance surface area.
- **Executive Architecture Decision Record (ADR):** Actionable, bounded recommendation with explicit stop conditions and rollback criteria.

### 4. Pricing Model & Payment
- **Executive Architecture Brief:** $6,000 fixed price.

### 5. Support Boundary
- **Included:** 1 comprehensive written debate packet, 2 review rounds, and 1 executive presentation call (60 minutes).
- **Out of Scope:** Hands-on software development or project management.

### 6. Maintained Source Surface
- `packages/python/arcana` (adversarial debate protocols, ecosystem contracts, gap analysis).

### 7. Demand Validation Step
- **Smoke Test:** Engage 3 venture funds or founder networks with sample blinded dialectical briefs.
- **Success Gate:** 1 paid brief commissioned.

---

## Governance & Operational Invariants

1. **Zero New Platform Infrastructure**: All offerings are delivered using existing git repositories, command-line scripts, standard library Python, and Stripe payment links. No custom billing portals, microservices, or databases shall be deployed to support sales until cash flow is positive.
2. **Pre-Paid Diagnostics**: Micro-audits and intake reviews are 100% pre-paid via Stripe before work commences. Sprints are 50% upfront / 50% on deliverable acceptance.
3. **Hermetic Delivery**: Deliverables must be reproducible and self-contained, delivered as git commits, PRs, or standalone markdown/JSON reports.
4. **Epistemic Honesty**: Marketing and deliverables must distinguish verified computational evidence from analytical assumptions, preserving the HUMMBL reputation for technical rigor.
