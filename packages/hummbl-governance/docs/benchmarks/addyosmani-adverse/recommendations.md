# Recommendations

Audit: `addyosmani/adverse` @ `4b9eb7b` (v0.2.1), 2026-07-05. All items below are
recommendations to the operator — nothing here is self-executing.

## Adoption constraints (first-class, binding on any HUMMBL use)

**AC-1 — No raw exit-code security gate.** HUMMBL must not use `adverse`'s raw exit
code as a blocking security gate. The exit code encodes a mean-of-verdicts consensus
(`consensusLabel.startsWith('BLOCK')` ⇔ mean verdict score < 0): a lone critical
security reject from the Adversary, with the other two personas approving, yields
SHIP-WITH-CAVEATS and **exit 0**. Any HUMMBL wrapper must apply severity/persona-aware
policy — e.g. block on any critical security finding from the Adversary unless that
finding is explicitly challenged/resolved — evaluated over the JSON report, never over
the upstream exit code. (Evidence: `src/cli.mjs:240,270`; `src/synthesis.mjs:19-24,
171-185`. Detail: governance-gap-analysis.md Gap 4.)

**AC-2 — No assurance-level inflation.** Default runs are L2 single-model multi-lens
review and must be recorded as such in any receipt; labeling an L2 run as multi-agent
or independent assurance is a claim-honesty violation.

**AC-3 — No non-author-review substitution.** An adverse SHIP verdict never satisfies
HUMMBL's non-author review requirement (single-model mode can be the author-model
reviewing itself with three hats).

## Immediate

1. **Accept the thesis classification**: treat `adverse` as a Tier 1 implementation
   benchmark for an "Adversarial Review Gate" candidate pattern; classify its default
   runs as **L2 single-model multi-lens review** (see assurance-levels.md). Record the
   pattern as a candidate only — no canonical terminology.
2. **Adopt three low-cost prompt/process patterns** into existing HUMMBL practice
   (no new infra required):
   - lane-fenced persona prompts with explicit out-of-scope lists + anti-theater
     clauses (`src/personas.mjs` is a direct drafting reference);
   - the validate / challenge / silence trichotomy as review-receipt vocabulary;
   - retry-with-validator-error-feedback for schema-bound sub-agent dispatches
     (upgrade to `sub-agent-injection-defense.md`'s one-retry rule).
3. **File the tracking issue** (body below) in the repo the operator designates
   (hummbl-governance is the natural home).

## Near-term

4. **Run the controlled experiment** (see "Suggested experiment") on a fixture repo
   with a seeded bug set, using a local model first (`ollama`) to avoid API spend,
   then one hosted-agent run. Preserve a scrubbed summary per the handoff's artifact
   rules. Requires operator approval for any hosted-model spend.
5. **Prototype the receipt envelope** (Gap 3): a small wrapper that runs
   `adverse review --json-out`, then wraps the untouched JSON with repo / branch /
   commit / diff-base / command / agent-model-provider / timestamp / source-cap /
   findings-hash / human-decision / CI-outcome / fix-PR-link fields (the full Gap 3
   required set) and posts a bus RECEIPT. Wrap, don't fork.
6. **Prototype the L4 decorrelation loop**: N runs across N providers from the
   verified Anvil mesh (devin, codex, `claude --bare -p`, pi, aider, ollama) + a
   cross-run finding differ. This is the highest-leverage extension adverse doesn't
   ship and plays directly to HUMMBL's existing multi-agent infrastructure.

## Not yet

7. **Do NOT wire any blocking CI gate.** See **AC-1** above (first-class adoption
   constraint). Gating, if ever, must be a HUMMBL policy function over the JSON
   report (severity × confidence-class) and requires separate operator approval.
8. **Do NOT canonize terminology** ("Adversarial Review Gate", the four confidence
   classes, L0–L6). All names stay candidates until the pattern earns promotion per
   `_candidates/README.md` discipline.
9. **Do NOT treat an adverse SHIP verdict as satisfying non-author review.** In
   single-model mode the reviewer can be the author-model with three hats;
   `cross-check-protocol.md` independence requirements are unaffected.
10. **Do NOT install the skill fleet-wide yet.** SKILL.md hardcodes `/tmp/` paths and
    an `opus` default model; needs Windows-path and `model-tier-policy.md` adaptation
    first (and skill-root hygiene per `skill-root-hygiene.md`).

## Suggested GitHub issues

Primary tracking issue title:

```text
Benchmark adverse: multi-lens adversarial review as governed merge-gate primitive
```

Body:

```markdown
## Purpose

Audit `addyosmani/adverse` as an external benchmark for HUMMBL governed agent review.

## Scope

- Source-map the repo.
- Map its review primitives to HUMMBL governance primitives.
- Identify gaps around authority, receipts, CI consequence, and model decorrelation.
- Propose an `Adversarial Review Gate` candidate pattern.
- Do not canonize terminology.
- Do not wire blocking CI without approval.

## Deliverables

- `docs/benchmarks/addyosmani-adverse/source-map.md`
- `docs/benchmarks/addyosmani-adverse/primitive-map.md`
- `docs/benchmarks/addyosmani-adverse/governance-gap-analysis.md`
- `docs/benchmarks/addyosmani-adverse/assurance-levels.md`
- `docs/benchmarks/addyosmani-adverse/recommendations.md`
- `docs/benchmarks/addyosmani-adverse/receipt.md`

## Definition of Done

- All claims cite repo evidence or explicit analysis.
- Default `adverse` run is classified as single-model multi-lens review, not full
  independent assurance.
- HUMMBL adoption recommendations are separated into advisory, experimental, and
  merge-gate categories.
- No CI mutation occurs without separate operator approval.
- Receipt includes repo URL, commit inspected, date, files reviewed, and agent/model
  used.
```

Follow-on issue candidates (file only if the operator advances the pattern):

- `Adversarial Review Gate: receipt envelope schema for adverse JSON reports` (Gap 3 + Gap 5)
- `Adversarial Review Gate: L4 decorrelation wrapper over the Anvil agent mesh` (assurance-levels L3→L4)
- `Adversarial Review Gate: severity×confidence gate policy function (advisory-mode pilot)` (Gap 4)

## Suggested experiment

Target: a **fixture repo with seeded defects** (one correctness bug, one injection
vulnerability, one maintainability smell — one per lane), NOT production code.

```bash
# Environment record
node --version          # v22.22.2 verified on Anvil
git rev-parse HEAD
git status --short

# Local-model run first (zero API spend)
npx adverse review ./src --agent "ollama run llama3.1" \
  --out adverse-review.md --json-out adverse-review.json --html-out adverse-review.html

# Then one hosted run (requires spend approval) — Anvil-specific: use --bare
npx adverse review ./src --agent "claude --bare -p" \
  --out adverse-review.md --json-out adverse-review.json
```

Measure: per-lane recall on seeded defects; confidence-class distribution; whether
cross-examination flips any verdict; runtime; parse-retry rate. Preserve only the
scrubbed summary, command shape, exit code, model used, and failure modes — not raw
reports. Note: an in-session `claude -p` spawn will fail on auth (nested-session
boundary); run from a plain shell.

**Why not run in this audit**: constraint #8 (no silent paid-agent usage) + the
handoff marks the experiment as conditional. The audit's empirical component was the
offline test suite instead (118/124 pass; see receipt.md).

## Decision needed from operator

1. **Home for the packet**: RESOLVED 2026-07-05 — operator approved relocation to
   `hummbl-io/hummbl-governance` on branch `docs/claude/adverse-benchmark`.
2. **Authorize the experiment** (item 4): local-model-only, or local + one hosted run?
3. **Advance the pattern?** If yes, the next artifact is a
   `_candidates/adversarial-review-gate.md` rule candidate (C2/M0, observation
   budget) + the receipt-envelope prototype. If no, this packet stands as reference.
4. **Issue filing**: approve filing the tracking issue above, and against which repo.
