# Receipt: `addyosmani/adverse` Benchmark

## Metadata

- **Date**: 2026-07-05
- **Agent**: claude-code (Claude Fable 5, model id `claude-fable-5`)
- **Operator**: Reuben Bowlby (handoff-directed; async execution)
- **Target repo**: `hummbl-io/hummbl-governance` (relocated from home-repo working tree per operator decision 2026-07-05; original audit staging was a local Windows worktree on a feature branch (redacted), uncommitted)
- **Target branch**: `docs/claude/adverse-benchmark` (based on `github/main` @ `df9b7de`)
- **External repo inspected**: https://github.com/addyosmani/adverse
- **External repo commit**: `4b9eb7b764a9d55ea08dff4f1c960926e0691f2a` (2026-06-20, package version 0.2.1) — shallow clone, read-only, at scratchpad temp path

> **Provenance note (per second-pass review, 2026-07-05)**: The commit hash
> `4b9eb7b`, Node v22.22.2, and the 118/124 test result are **local execution
> receipt facts** from Anvil (observed via `git log -1` and `npm test` on the audit
> clone), not independently verified from a fetched public GitHub page. Publicly
> corroborable facts (v0.2.1, Node >=20 engine, MIT, `node --test` script) are
> visible in the repo's `package.json`.
- **Runtime**: Windows 11 (Anvil), git-bash, Node v22.22.2
- **Models/agents used**: claude-fable-5 only (this session). **No LLM review runs of adverse were executed** — no `claude -p`/`codex`/`ollama` invocations, zero agent spend
- **Network/tooling used**: `git clone --depth 1` (GitHub, read-only), local `node --test`

## Scope

Static source audit of all 40 non-.git files in the adverse repo + one offline test
execution. Deliverable: 7-file benchmark packet at
`docs/benchmarks/addyosmani-adverse/`. Explicitly out of scope (honored): CI wiring,
canon changes, new official terminology, production-repo mutation, live LLM review
runs.

## Files inspected

Read in full: `README.md`, `package.json`, `src/personas.mjs`, `src/synthesis.mjs`,
`src/runner.mjs`, `src/parse.mjs`, `src/prompts.mjs`,
`skills/adverse-review/SKILL.md`.
Read partially (targeted grep/head): `src/cli.mjs`, `src/collect.mjs`,
`skills/adverse-review/scripts/prompts/round1.txt`, `round2.txt`, test suite names +
failing-test output. Not read line-by-line: `src/html.mjs`, individual test bodies,
fixture files (existence + role confirmed via file listing and README).

## Claims preserved

| Claim | Evidence | Confidence | Notes |
|---|---|---|---|
| Two-round structure: 3 parallel reviewers → cross-examination → synthesis | README architecture diagram; `src/prompts.mjs` PHASE1/PHASE2; SKILL.md Phases 2–4 | Verified (source) | |
| Ships as CLI and Claude Code Skill sharing one Node core | `package.json` files list; `skills/adverse-review/scripts/*.mjs` re-export `src/`; README | Verified (source) | |
| CLI wraps `claude -p`, `codex exec --quiet`, `gemini`, `ollama run llama3.1`; markdown/JSON/HTML outputs | README CLI usage; `src/runner.mjs`; `src/cli.mjs` flags; `src/html.mjs` exists | Verified (source) | Invocation shapes not live-tested this audit |
| Three lenses = Auditor (correctness), Adversary (security/abuse/trust boundaries), Pragmatist (maintainability/design fit) | `src/personas.mjs` full text | Verified (source) | |
| Repo explicitly states single-model/three-personas ≠ decorrelated multi-provider review | README "Why this design" + "Limitations" | Verified (source, verbatim) | "Don't pretend this is the same thing as two-provider review" |
| Synthesis is deterministic Node code, not a 4th LLM call; classes = cross-validated / consensus / disputed / solo from report/validate/challenge edges | `src/synthesis.mjs:1-24, 129-134`; SKILL.md "do not run a fourth LLM judge pass" | Verified (source) | Self-validation excluded (`:115`) |
| Exit code 1 = CI gate signal | README exit-code table; `src/cli.mjs:53` | Verified (source) | **Precision**: fires only on consensus label starting `BLOCK` (mean verdict < 0), not on any single reject (`src/cli.mjs:240,270`) |
| Source caps 250 KB total / 30 KB per file; truncation not recorded in report | `src/collect.mjs:7-8,159-160`; absence of cap fields in `toJsonReport` (`src/synthesis.mjs:288-308`) | Verified (source) | Basis for Gap 3 finding |
| One anti-injection clause in round-1 prompt; round-2 embeds round-1 JSON | `src/prompts.mjs:56, 127-134` | Verified (source) | Second-order injection channel is my analysis, not a repo claim |
| Test suite: 124 tests, no framework deps, contract fixtures pin Claude CLI wrapper shapes | `npm test` run + `tests/fixtures/claude-cli/` listing | Verified (executed) | |
| adverse default run ≈ assurance L2 | Analysis over the above | Analysis | Consistent with repo's own limitation statement |

## Tests or commands run

| Command | Outcome | Notes |
|---|---|---|
| `git clone --depth 1 https://github.com/addyosmani/adverse <temp>` | OK | Read-only audit clone |
| `git log -1` (external repo) | `4b9eb7b…` 2026-06-20 | Commit pin |
| `find`/`wc -l`/`cat package.json` | OK | Inventory + line counts |
| `node --version` | v22.22.2 | Meets `>=20` engine requirement |
| `npm test` (offline unit+contract suite) | **118 pass / 3 fail / 3 skipped of 124** | Skipped = live-Claude tests (gated by `ADVERSE_LIVE=1`). All 3 failures in `tests/collect.test.mjs` |
| Failing-test inspection | Environment artifact | See "Failing tests" block below. Suites for parse/prompts/runner/synthesis/cli/combine all pass |
| Live review run (`npx adverse review …`) | **Not executed** | Deliberate: constraint #8 (no silent agent spend); experiment deferred to operator-approved follow-up (recommendations.md) |

### Failing tests (exact names + evidence)

```text
Failing tests (all in tests/collect.test.mjs):
- tests/collect.test.mjs::"collectDirectory excludes node_modules"   (line 40)
- tests/collect.test.mjs::"collectDirectory throws if no reviewable files" (line 71)
- tests/collect.test.mjs::"collectDiff requires a git repo"          (line 163)

Failure classification:
- environment/worktree assumption (tests create fixtures under os.tmpdir() and
  assume that path is NOT inside a git worktree; on Anvil, %TEMP% resolves under
  the operator home directory (redacted), which is itself a git repository, so collect.mjs's isGitRepo()
  returns true for the fixture dirs and collection switches to git ls-files
  semantics)
- not source-behavior failure
- not adverse core logic failure

Evidence (node --test output excerpts, 2026-07-05):
- not ok 34 "collectDirectory excludes node_modules" — failureType:
  testCodeFailure; "The expression evaluated to a falsy value"
- not ok 37 "collectDirectory throws if no reviewable files" —
  code: ERR_ASSERTION; "Missing expected exception."
- not ok 43 "collectDiff requires a git repo" — "The input did not match the
  regular expression /not a git repository/"
```

## Findings

1. Deterministic synthesis is the standout governance-compatible primitive (see
   primitive-map #4).
2. Verdict aggregation is mean-based: a lone critical security reject does not block
   (gap-analysis Gap 4). Sharpest calibration issue for any gate use.
3. Report ≠ receipt: no commit SHA, agent/model identity, timestamp, source-cap
   disclosure, or findings hash (Gap 3).
4. Prompt-injection posture is above-average for the category but has a second-order
   channel via round-1 JSON re-embedding (gap-analysis addendum).
5. Skill variant needs Windows-path + model-tier adaptation before HUMMBL use
   (`/tmp/` hardcoding, `opus` default).
6. Quality signals: zero runtime deps, honest limitations section, contract-test
   discipline against CLI wrapper drift, degraded-run disclosure, anti-theater
   persona instructions.

## Governance implications

adverse validates the architecture HUMMBL is converging on (multi-lens → cross-exam →
deterministic decision → artifact → consequence) and simultaneously demonstrates,
by its gaps, exactly where HUMMBL's differentiated layer sits: authority order,
receipts, claim-evidence linkage, gate policy, and provider decorrelation. Full
analysis in governance-gap-analysis.md.

## Adoption recommendation

Benchmark-adopt (patterns), not dependency-adopt (tool), yet. Immediate: L2
classification + three prompt/process patterns + tracking issue. Near-term:
fixture-repo experiment + receipt envelope + L4 decorrelation loop. Not yet: blocking
CI, terminology canonization, fleet skill install. Detail in recommendations.md.

## Non-adoption / caution notes

- An adverse SHIP verdict does not satisfy HUMMBL non-author review (single-model
  reviewer can be the author-model).
- Never label an L2 run as multi-agent assurance (claim-honesty violation class).
- Apply intake sanitization to adverse reports per `sub-agent-injection-defense.md`
  before treating them as ratified artifacts.
- Skill install deferred pending path/model-tier adaptation and skill-root hygiene.

## Follow-up issues recommended

See recommendations.md § Suggested GitHub issues: 1 primary tracking issue + 3
conditional follow-ons (receipt envelope, L4 wrapper, gate policy pilot). None filed
in this audit — filing awaits operator approval and repo designation.
