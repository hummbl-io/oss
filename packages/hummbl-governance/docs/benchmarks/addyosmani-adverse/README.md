# Benchmark Packet: `addyosmani/adverse`

**Status**: Tier 1 source-candidate / implementation benchmark — NOT HUMMBL canon
**Audited**: 2026-07-05
**Auditor**: claude-code (Fable 5), Anvil
**External repo**: https://github.com/addyosmani/adverse
**Commit inspected**: `4b9eb7b764a9d55ea08dff4f1c960926e0691f2a` (2026-06-20, v0.2.1)
**Target repo/branch**: `hummbl-io/hummbl-governance`, `docs/claude/adverse-benchmark`

## What this packet is

An audit of `adverse` — "multi-agent adversarial code review for any coding agent"
(single model, three personas, two rounds, deterministic synthesis) — as an external
implementation benchmark for a HUMMBL **Adversarial Review Gate** candidate pattern.

Candidate pattern names (none canonized):

```text
Adversarial Review Gate
Multi-Lens Merge Gate
Cross-Examined Review Gate
Adversarial Assurance Gate
Review-Edge Consensus Gate
```

## Thesis (supported by this audit)

> `adverse` is a strong public implementation benchmark for a HUMMBL Adversarial
> Review Gate, especially because it combines orthogonal review lenses, explicit
> cross-examination, deterministic synthesis, and report artifacts. However, default
> usage should be classified as **single-model multi-lens review (assurance level
> L2)**, not full independent multi-agent assurance. HUMMBL's differentiated layer is
> authority governance, receipt preservation, claim-evidence linkage, CI policy, and
> model/provider decorrelation.

The repo itself states this limitation honestly (README "Limitations": "Don't pretend
this is the same thing as two-provider review").

## Packet contents

| File | Contents |
|---|---|
| [source-map.md](source-map.md) | File-by-file map of the audited repo |
| [primitive-map.md](primitive-map.md) | 10 primitives → HUMMBL analogues |
| [governance-gap-analysis.md](governance-gap-analysis.md) | 5 gaps from HUMMBL's perspective |
| [assurance-levels.md](assurance-levels.md) | L0–L6 assurance ladder; adverse ≈ L2 |
| [recommendations.md](recommendations.md) | Immediate / near-term / not-yet actions |
| [receipt.md](receipt.md) | Audit receipt: files, commands, claims, evidence |

## Headline findings

1. **Strongest pattern**: deterministic synthesis (`src/synthesis.mjs`) — consensus is
   computed by counting validate/challenge edges between personas, deliberately NOT a
   fourth LLM judge call. This is the most directly HUMMBL-compatible primitive: an
   auditable, replayable, non-LLM governance step at the decision point.
2. **Honest self-limitation**: single-model persona diversity is explicitly named as
   correlated; decorrelation requires running with different agents.
3. **Gap**: report ≠ receipt. Output lacks commit SHA, agent/model identity, source
   cap disclosure, findings hash, and human-decision fields HUMMBL requires.
4. **Adoption constraint AC-1 (first-class)**: HUMMBL must not wire `adverse`'s raw
   exit code as a blocking security gate — it is a mean-of-verdicts consensus, and a
   lone critical Adversary reject with two approvals exits 0 (SHIP-WITH-CAVEATS). Any
   gate must be a severity/persona-aware HUMMBL policy over the JSON report. See
   recommendations.md § Adoption constraints.
5. **Empirical note**: on Anvil (Node v22.22.2), `npm test` → 118/124 pass, 3 skipped
   (live-Claude), 3 fail — all 3 failures are environment artifacts of Anvil's
   home-directory-as-git-repo layout (tests assume `os.tmpdir()` is not inside a git
   worktree), not core-logic defects. Exact failing test names + stderr excerpts in
   receipt.md. Commit hash, Node version, and test counts are local execution receipt
   facts, not independently web-verified public-source facts.

## Governance boundaries observed

- No HUMMBL canon changed; no new official terminology introduced.
- No CI gate wired anywhere; no production repo mutated.
- No live LLM review run executed (no silent agent spend); unit tests only.
- Audit clone: shallow, read-only, in scratchpad temp dir.
