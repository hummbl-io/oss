# Handoff: Intel Surge — Agentic Engineering Fundamentals

**Date:** 2026-08-10
**Agent:** Devin (root, GLM-5.2 High)
**Session type:** Research sweep + synthesis
**Status:** COMPLETE — synthesis delivered, ARCANA peer review complete, committed to repo

---

## Purpose

Rigorous research into fundamental directory structures for agentic engineering, building on previous work documenting `hummbl-basen` and `hummbl-mcp-basen` packages. Goal: formulate evidence-based plan for future work.

## What Was Done

### Stage 1: Sweep (13 sub-agents)
- 6 internal recon agents (subagent_explore, SWE-1.6) analyzed 8 local repos
- 7 external research agents (devin-researcher, GLM-5.2) provided knowledge syntheses
- Root agent executed 9 web searches (compensating for sub-agent web-tool limitations)
- Git archaeology across 8 repos × 14 structures (first-commit dates extracted)

### Stage 2: Quality Gate
- Source tiers classified (S1 primary, S2 secondary, S3 tertiary)
- All arxiv URLs from intel-surge ledger marked S3 (unverified)
- GLM sub-agent training-knowledge claims explicitly flagged
- 3 missing repos (hummbl-mcp-server, hummbl-eval, crab) — SSH unavailable, excluded from evidence

### Stage 3: Ingest
- DEFERRED — ledger writes need different runtime

### Stage 4: Synthesis
- 7 fundamental directory structures identified and classified by maturity
- Minimum viable agentic-engineering repository layout proposed (4 tiers)
- Novelty stress-test completed (what's inherited vs. what's genuinely novel)
- Open questions for arcana peer review documented

### Stage 5: ARCANA Peer Review
- 3 lenses applied (Ostrom, Ashby, Schneier) by root agent (sub-agent quota exhausted)
- Cross-lens consensus: eval gates are the most fundamental structure
- Cross-lens dissensus on `_state/`: necessary sensor, insufficient regulator
- Key recommendation: do not standardize yet — needs multi-operator validation

### Stage 6: Academic URL Verification
- 4 key academic papers verified via webfetch (MemGPT, Generative Agents, Memory Survey, CoALA)

### Stage 7: Commit
- All deliverables committed to hummbl-governance on branch `docs/devin/agentic-engineering-intel-surge`
- Sensitive data redacted (operator name, machine names, internal paths, sub-agent IDs)

## What's Left

1. **Verify remaining academic URLs** — intel-surge ledger's arxiv citations beyond the 4 verified need independent webfetch verification
2. **Document eval promotion gate pattern** — propose as extension to Anthropic's skill-creator standard
3. **Document junction model** — propose as reference architecture for multi-agent fleets
4. **Research 3 missing repos** when SSH access restored (hummbl-mcp-server, hummbl-eval, crab)
5. **Re-run ARCANA review with dedicated sub-agents** when quota resets — root-agent application lacks full persona depth
6. **Multi-operator validation of `_state/` pattern** — needed before standardization (per Ostrom lens)

## Key Files Touched

- `docs/research/agentic-engineering-directory-taxonomy-v0.1.md` (NEW — main synthesis, ~500 lines)
- `docs/research/agentic-engineering-arcana-peer-review-v0.1.md` (NEW — 3-lens peer review)
- `docs/research/state-directory-pattern-spec-v0.1.md` (NEW — `_state/` pattern spec)
- `docs/handoffs/2026-08-10-intel-surge-agentic-engineering.md` (NEW — this handoff)

## Gotchas & Context

- **devin-researcher profile lacks web_search/webfetch** in this runtime — only filesystem tools. This was discovered mid-sweep and compensated by root-agent web research.
- **devin-swe-recon profile (SWE-1.7) failed to launch** — invalid model ID. All internal recon used subagent_explore (SWE-1.6) instead.
- **SSH-based recon of 3 repos failed** — SSH access was unavailable. These repos are absent from the evidence base.
- **Sub-agent tool limitations are structural** — background subagents auto-deny unapproved tools; the devin-researcher profile would need its frontmatter updated to include web_search/webfetch for future web-research sweeps.
- **Intel-surge ledger URLs are unverified** — they were captured by prior research agents (2026-07-13 to 2026-07-15) but not independently verified this session (except the 4 key papers).
- **ARCANA review was root-agent application** — sub-agent quota was exhausted. The review applies the core frameworks faithfully but lacks the full persona depth of dedicated ARCANA sub-agents.

## Test Status

- N/A — research task, no code changes
- Synthesis and peer review files committed to repo

## Entry Points

- **Main deliverable:** `docs/research/agentic-engineering-directory-taxonomy-v0.1.md`
- **Peer review:** `docs/research/agentic-engineering-arcana-peer-review-v0.1.md`
- **State spec:** `docs/research/state-directory-pattern-spec-v0.1.md`
- **Next action:** Multi-operator validation of `_state/` pattern; re-run ARCANA with dedicated sub-agents when quota resets
