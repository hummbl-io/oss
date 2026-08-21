# Assurance Levels: Candidate Ladder for Agent Code Review

**Status**: DRAFT candidate ladder — not HUMMBL canon. Names provisional.

Framing rule this ladder encodes:

> `adverse` is not "full assurance" by itself. It is a strong review primitive that
> can become part of a larger governed assurance stack. What a review run *proves*
> depends on how decorrelated the reviewers are and what governance wraps the verdict.

## The ladder

| Level | Name | Description | Merge meaning |
|---|---|---|---|
| **L0** | No agent review | Human/self review only | No agent assurance claim |
| **L1** | Single-agent review | One coding agent performs ordinary one-shot review | Advisory only; one perspective with that perspective's blind spots |
| **L2** | Single-model multi-lens review | One model, multiple orthogonal personas, cross-examination round, deterministic synthesis | Useful but correlated — all lenses share one model's failure modes. Advisory |
| **L3** | Multi-agent same-provider review | Separate agent runs/sessions (possibly same provider), reports diffed | Better process independence; residual provider-level correlation |
| **L4** | Multi-provider decorrelated review | Claude / Codex / Gemini / local-model split across runs; findings intersected and unioned across the model boundary | Stronger independence; cross-provider agreement is meaningful signal |
| **L5** | Governed adversarial gate | L4 + deterministic synthesis under HUMMBL policy (severity × confidence rules, not mean-verdict) + receipt envelope + defined CI consequence + operator-approved gate policy | Candidate merge gate |
| **L6** | Full assurance packet | L5 + claim-evidence ledger rows per finding + replayable artifacts (round-1/round-2 JSON preserved, findings hash) + human approval receipt | High-confidence governed merge |

## Where `adverse` sits

**Default runs are L2.** Both surfaces:

- CLI default (`adverse review` → 1 agent command, 3 personas, 2 rounds) = L2.
- Claude Code Skill = L2, and SKILL.md *mandates* one model across personas
  ("different models across personas defeats the single-model design").
- `--single-round` is a degraded L2 (no cross-examination; every finding is
  effectively solo/cross-validated-by-coincidence).

The repo self-classifies consistently with this: README recommends "run `adverse`
twice with different agents and diff the reports" when "you genuinely need
decorrelated outputs across the model boundary."

## What moves it up the ladder

| Transition | What's required | Provided by adverse? |
|---|---|---|
| L2 → L3 | Repeated runs via `--agent`, separate processes/sessions; a report-diff step | Runs: YES (`--agent` + `--json-out`). Diff/merge across runs: NO — manual |
| L3 → L4 | Runs across ≥2 providers (e.g. `claude --bare -p`, `codex exec --quiet`, `ollama run …`); cross-run finding intersection | Invocation: YES. Cross-run synthesis: NO — `synthesize` merges personas within a run, not reports across runs (though the standalone `synthesize` subcommand could be fed combined multi-run JSON as a hack) |
| L4 → L5 | HUMMBL layer: receipt envelope (Gap 3), policy-based gate function (Gap 4), authority order (Gap 2), operator approval to gate | NO — this is HUMMBL's differentiated layer by design |
| L5 → L6 | Claim-evidence ledger rows (Gap 5), preserved replayable artifacts (`--save-artifacts` exists but is framed as debug), findings hash, human decision receipt | Partial raw material only |

## Practical notes for HUMMBL use

1. **Anvil L4 feasibility is already verified**: the agent-mesh audit
   (`~/.agents/rules/_candidates/agent-mesh-huaomp-mtsmu-matrix.md`) confirmed 5
   practically usable headless agents (devin, codex, `claude --bare`, pi, aider).
   An L4 wrapper is a loop over providers + a cross-run report differ — modest work,
   and the highest-leverage extension adverse doesn't ship.
2. **Never claim above the level actually run.** A receipt (Gap 3) must record
   agent/model per run precisely so the assurance level is auditable after the fact.
   An L2 run labeled "multi-agent review" is a claim-honesty violation
   (`claim-honesty-protocol.md` §3 tense/scope escalation class).
3. **L5/L6 are governance constructs, not tooling constructs.** No upstream feature
   request gets adverse to L5; the gate policy, authority order, and receipts are
   HUMMBL's to build regardless of which review engine sits underneath.
