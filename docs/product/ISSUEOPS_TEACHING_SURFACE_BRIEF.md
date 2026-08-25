# Product Brief — Public Agentic CI/CD & IssueOps Teaching Surface

**Status:** draft v0.1
**Owner:** Operator
**Steward:** HUMMBL Research Institute
**Date:** 2026-06-23
**Tracking:** hummbl-io/hummbl-production#410

## 1. Problem

HUMMBL sells AI governance infrastructure, but our public CI/CD surface is invisible. Prospects, evaluators, and curious developers who land on `hummbl.io` see marketing pages and a claims manifest — they cannot see _how an agent-governed fleet actually operates_. The thing we sell (deterministic agent governance with receipts) is the thing we don't show.

Two specific gaps:

1. **No public proof of agentic CI/CD.** Our internal fleet runs agent-driven CI (Devin, Claude Code, Codex) with KRINEIA receipts, bus coordination, and Arbiter scoring — but none of this is visible externally. A buyer evaluating "is this real" has only our word.
2. **No teaching surface for IssueOps.** IssueOps (managing repo work via issues, labels, and structured comments instead of tickets-as-email) is the entry point for agentic CI/CD. We use it internally; we don't teach it. Buyers who want to adopt HUMMBL need to learn the pattern, and right now they'd learn it from a competitor's blog post.

## 2. Audience

| Segment                       | What they want                                  | What we need to show                                       |
| ----------------------------- | ----------------------------------------------- | ---------------------------------------------------------- |
| AI governance buyers          | Proof that agentic CI/CD is real and governed   | Live receipt feed, agent activity log, deterministic gates |
| Developer advocates / DevRels | A teaching surface they can reference and share | IssueOps walkthrough, copyable patterns, glossary          |
| Open-source contributors      | How to participate in an agent-governed repo    | Issue templates, agent contract, receipt verification      |
| Internal HUMMBL operators     | A canonical reference for the pattern           | Single source of truth for the IssueOps protocol           |

## 3. Product surface

A new public page at `hummbl.io/issueops.html` (and possibly `hummbl.io/cicd.html` as a separate concern) that combines:

### 3.1 Live agent activity feed (read-only)

A real-time, read-only view of the HUMMBL fleet's agent-driven CI/CD activity. Sourced from the coordination bus and KRINEIA receipt chains. Shows:

- Recent agent dispatches (which agent, which repo, which task)
- Receipt emissions (event type, repo, hash, prev_hash)
- Deterministic gate decisions (pass/fail, validator, evidence link)
- Bus messages (MILESTONE, BLOCKED, STATUS, HANDOFF)

**Trust architecture:** the feed is read-only and signed. Each entry links to a verifiable receipt in the source repo's `_receipts/krineia/primary.jsonl`. Visitors can verify the chain themselves.

### 3.2 IssueOps teaching walkthrough

A structured, copyable walkthrough of the IssueOps pattern as HUMMBL practices it:

1. **Issue creation** — structured issue templates with required fields (problem, acceptance criteria, evidence request)
2. **Agent dispatch** — how an issue becomes an agent task (label triggers, dispatch manifest, scope boundary)
3. **Deterministic gates** — what the agent may do autonomously (schema validation, tests, lint) vs. what requires human approval (constitutional changes, public claims, deployment target)
4. **Receipt emission** — every state change gets a KRINEIA receipt with hash, prev_hash, and evidence link
5. **Bus coordination** — agents post to the coordination bus; humans and other agents can observe
6. **Human approval gate** — the authority layer: humans approve constitutional changes, releases, and public claim changes
7. **Closeout** — issue closed with receipt reference, ADR if applicable, and bus MILESTONE

Each step has:

- A copyable issue template or manifest
- A receipt example (real or sanitized)
- A "what can go wrong" callout (failure modes and how governance catches them)

### 3.3 Glossary

A short, authoritative glossary of the terms we use: KRINEIA, receipt, deterministic gate, IssueOps, agent operating contract, constitution, doctrine, steward, approving human, bus, dispatch manifest, etc.

### 3.4 Verification widget

A client-side widget that lets visitors paste a receipt hash and verify it against the published chain. This makes the "you can verify this yourself" claim concrete.

## 4. Trust and safety constraints

This is a public surface showing real fleet activity. Constraints:

1. **No secrets.** The feed is sourced from public bus messages and receipt chains only. No private repo content, no internal customer data, no agent chain-of-thought.
2. **No self-grading.** The feed shows what happened; it does not score or rank agents. (Consistent with KRINEIA boundary: `observed_agent_may_write_receipts: false`, `receipts_may_train_agents: false`.)
3. **Read-only.** Visitors cannot dispatch agents or write to the bus from this page.
4. **Receipt-backed.** Every claim on this page (including the feed itself) must be receipt-backed or marked as illustrative.
5. **Provider-neutral.** Per Repo Standard §8, the page must not name a specific agent provider as a precondition of authority. Agent names can appear in the feed (they're observed facts) but the teaching surface must be provider-neutral.

## 5. Architecture

```
coordination bus (TSV) ─┐
                        ├──> cloudflare worker (read-only aggregator) ──> /issueops.html (live feed)
KRINEIA receipts (JSONL)┘                                              │
                                                                       ├──> teaching walkthrough (static)
                                                                       ├──> glossary (static)
                                                                       └──> verification widget (client-side JS)
```

- **Aggregator worker:** a Cloudflare Worker that reads from the coordination bus (via Tailscale tunnel to the bus file) and published KRINEIA receipt chains (via GitHub Git trees API). Caches for 60s. No write primitives.
- **Static content:** the teaching walkthrough, glossary, and widget are static HTML/CSS/JS served via Cloudflare Pages.
- **Verification widget:** client-side JS that fetches the published receipt chain and verifies a pasted hash. No server-side trust required.

## 6. Phasing

### Phase 1 — Static teaching surface (MVP)

- `/issueops.html` with walkthrough, glossary, and verification widget
- Receipt examples are static (real receipts from public repos, sanitized if needed)
- No live feed yet
- **Goal:** establish the teaching surface and the verification pattern

### Phase 2 — Live receipt feed

- Aggregator worker deployed to Cloudflare
- Feed shows recent KRINEIA receipts from public repos (hummbl-governance, hummbl-production, base120, mcp-server, etc.)
- 60s cache, read-only
- **Goal:** show that the receipts are real and current

### Phase 3 — Live bus feed

- Extend aggregator to read coordination bus messages (MILESTONE, BLOCKED, STATUS, HANDOFF)
- Filter to public-safe messages (no private repo content, no customer data)
- **Goal:** show that agent coordination is real and observable

### Phase 4 — Interactive verification

- Verification widget extended to fetch and verify any pasted receipt against its claimed chain
- "Submit a receipt" flow that lets visitors verify receipts from any hummbl-io public repo
- **Goal:** make the "you can verify this yourself" claim load-bearing

## 7. Success metrics

| Metric                                               | Phase 1 target | Phase 4 target |
| ---------------------------------------------------- | -------------- | -------------- |
| Unique visitors to /issueops.html                    | 100/month      | 1000/month     |
| Verification widget uses                             | 10/month       | 100/month      |
| Inbound discovery calls mentioning IssueOps          | 1/month        | 5/month        |
| External repos adopting the pattern (forks, copies)  | 0              | 5              |
| Time-to-first-receipt-verification for a new visitor | n/a            | < 2 minutes    |

## 8. Risks and mitigations

| Risk                                            | Mitigation                                                                                                   |
| ----------------------------------------------- | ------------------------------------------------------------------------------------------------------------ |
| Feed exposes private fleet activity             | Aggregator reads only public bus messages and public repo receipts; private repos are filtered               |
| Feed shows agent failures, damaging credibility | Show failures honestly with receipt evidence; frame as "governance working as designed" — the gate caught it |
| Teaching surface becomes stale                  | Walkthrough is versioned (v0.1, v0.2...); quarterly review by steward; ADR required for protocol changes     |
| Verification widget trusts server-side data     | Widget fetches the canonical chain from GitHub raw URLs and verifies client-side; no server trust            |
| Provider-neutrality violation                   | Page reviewed against Repo Standard §8 before publish; agent names appear only in observed-feed context      |

## 9. Relationship to existing artifacts

- **CONSTITUTION.md §3 invariant 1 (public claim honesty):** every claim on this page must have status and evidence in claims-provenance.json. Add claims for this page to the manifest.
- **KRINEIA.md:** the page demonstrates KRINEIA in action; the page itself is governed by KRINEIA (changes require receipts).
- **hummbl.repo.yaml `surfaces`:** add `issueops_teaching` as a new surface.
- **Claims provenance:** new claims added (e.g., "live receipt feed", "verification widget", "100+ external adoptions") must go through the claims protocol.

## 10. Open questions

1. Should the live feed include bus messages from private repos (filtered to public-safe content) or only public repos entirely? (Recommendation: public repos only, to keep the trust boundary simple.)
2. Should the verification widget support receipts from non-hummbl-io repos that adopt the KRINEIA schema? (Recommendation: yes, but phase 4+.)
3. Should we publish a "KRINEIA receipt explorer" as a separate tool, or keep it embedded in /issueops.html? (Recommendation: embedded first, separate tool if demand emerges.)
4. Should the teaching walkthrough be available as a downloadable PDF/epub for offline reference? (Recommendation: yes, phase 2+.)

## 11. Next steps

1. **This brief:** review by Board (Operator, Future Self, Governance Officer, Risk Officer, Stakeholder Proxy).
2. **On approval:** create ADR-002 in hummbl-production/docs/adr/ recording the decision to build this surface.
3. **Phase 1 implementation:** static `/issueops.html` with walkthrough, glossary, verification widget.
4. **Claims:** add claims for the new page to claims-provenance.json with status `pending` until verified.
5. **KRINEIA receipt:** emit a receipt when the page goes live.

## References

- Issue: hummbl-io/hummbl-production#410
- HUMMBL Repo Standard: hummbl-io/hummbl-governance/docs/standards/HUMMBL_REPO_STANDARD.md
- KRINEIA receipt schema: hummbl-io/krineia/RECEIPT_SCHEMA.md
- Coordination bus: hummbl-governance bus infrastructure
- Claims manifest: hummbl-production/web/manifest/claims-provenance.json
