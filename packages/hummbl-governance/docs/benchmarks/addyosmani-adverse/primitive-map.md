# Primitive Map: `addyosmani/adverse`

Commit inspected: `4b9eb7b` (v0.2.1). Each primitive cites the implementing files.
HUMMBL analogues reference existing canon (`~/.agents/rules/`) or candidate patterns —
no new canonical terminology is introduced here.

---

## Primitive 1: Independent Persona Review

**Observed implementation**: Three personas with hard lane boundaries in
`src/personas.mjs`. Each system prompt names what's in scope, what's explicitly out of
scope ("do NOT flag these — other personas cover them"), a severity rubric, and an
anti-theater clause ("Do not invent findings to look productive").

**Evidence**: `src/personas.mjs:14-17` (Auditor lane fence), `:32-35` (out-of-scope),
`:51-53` (anti-theater).

**HUMMBL analogue**: Lens-agent dispatch (ARCANA lenses, `agent-dispatch-hygiene.md`
sub-agent patterns); the Auditor/Adversary/Pragmatist split maps to
correctness/threat/maintainability review lanes in `cross-check-protocol.md` severity
work.

**Strength**: The lane-fencing prose is the actual mechanism making single-model
personas useful — overlap is explicitly framed as "costs money for no signal."

**Limitation**: Lane compliance is prompt-enforced only; nothing verifies a persona
stayed in its lane.

**Adoption recommendation**: ADOPT the lane-fencing prompt pattern for any HUMMBL
multi-lens review skill. The three prompts are directly reusable drafting references.

---

## Primitive 2: Cross-Review / Cross-Examination

**Observed implementation**: Round 2 gives every persona all round-1 reviews and
requires an on-record position: validate (with reason), challenge (with concrete
reason — "'I disagree' is not enough"), silence (= "not my lane, no strong opinion"),
or add new findings. Personas may not re-litigate their own findings.

**Evidence**: `src/prompts.mjs:60-121` (PHASE2_INSTRUCTIONS), `skills/adverse-review/SKILL.md`
Phase 3.

**HUMMBL analogue**: `cross-check-protocol.md` Stage-2/Stage-3 non-author review;
`multi-agent-redline.md` REDLINE_PHASE_3 meta-review. The "challenge requires a
concrete reason" rule mirrors HUMMBL's rubber-stamp-ACK-is-invalid rule.

**Strength**: Forces adversarial engagement rather than parallel monologues; makes
disagreement machine-readable.

**Limitation**: Same-model cross-examination inherits anchoring bias (repo admits
this). Titles must match "character-for-character" for the join — a fragile key
(mitigated by normalization, see Primitive 3).

**Adoption recommendation**: ADOPT the validate/challenge/silence trichotomy as
vocabulary for HUMMBL review receipts. Silence-as-deference is a useful explicit state
HUMMBL reviews currently lack.

---

## Primitive 3: Validate / Challenge Edges

**Observed implementation**: Cross-review output is edges: `{from, title, reason}`
under `validate` and `challenge` keys. Synthesis joins edges to findings by normalized
title (lowercased, whitespace-collapsed, trailing punctuation stripped), with a
`title|file|line` primary key. Self-validation is explicitly discarded
(`src/synthesis.mjs:115` — "self-validation does not count").

**Evidence**: `src/synthesis.mjs:30-32, 66-89, 111-126`; `src/prompts.mjs:180-216`
(validatePhase2).

**HUMMBL analogue**: Bus REVIEW receipts with findings lists (`bus-lexicon.md`
Review-Receipt Schema); no current HUMMBL surface represents reviewer agreement as
typed edges.

**Strength**: Converts qualitative peer review into graph data. Self-validation
exclusion is exactly HUMMBL's non-author-review invariant, enforced in code.

**Limitation**: Title-string joins can silently drop edges when a persona paraphrases;
un-joined validates/challenges vanish without warning.

**Adoption recommendation**: ADOPT the edge model conceptually; if HUMMBL implements
it, use stable finding IDs instead of title-string joins.

---

## Primitive 4: Deterministic Synthesis

**Observed implementation**: `synthesize()` in `src/synthesis.mjs` is pure Node code —
finding merge, severity max-promotion, confidence labeling, verdict scoring
(approve=1 / conditional=0.5 / reject=-1, mean over reviewers → [-1,1]), consensus
label (SHIP / SHIP-WITH-CAVEATS / HOLD / BLOCK). The design comment: "a fourth model
invocation costs more, adds another failure mode, and would itself be subject to the
same single-model bias the personas have."

**Evidence**: `src/synthesis.mjs:1-24, 65-185`; README "Synthesis is deterministic
Node code, not another LLM call."

**HUMMBL analogue**: This is the strongest match to HUMMBL doctrine: a non-LLM,
replayable, auditable decision step — same family as `bus_writer_core.py` validation,
deterministic policy engines in HGK (`admission-gate-doctrine.md`), and the Krineia
principle that the audit layer must not loop back through inference.

**Strength**: Given identical round-1/round-2 JSON, the verdict is reproducible
byte-for-byte. That is the property a merge gate must have.

**Limitation**: The verdict function is a hardcoded mean; no policy hooks (e.g. "any
critical cross-validated security finding ⇒ BLOCK regardless of mean"). A 2-1 approve
vote with one critical reject synthesizes to SHIP-WITH-CAVEATS and exit code 0.

**Adoption recommendation**: ADOPT the principle (deterministic decision layer over
LLM findings) as the core of any HUMMBL Adversarial Review Gate. ADAPT the verdict
function: HUMMBL gate policy must be configurable and severity-aware, not mean-only.

---

## Primitive 5: Confidence Classification

**Observed implementation**: Four classes — `cross-validated` (reported by ≥2
personas), `consensus` (1 reporter + ≥1 validator), `disputed` (≥1 challenger; dispute
wins over consensus "because the dispute is the more interesting signal"), `solo`.
Report sections are grouped by class; sort order severity → confidence → title.

**Evidence**: `src/synthesis.mjs:9-24, 129-142, 191-196`.

**HUMMBL analogue**: Maps cleanly onto HUMMBL evidence-tier thinking
(`claim-honesty-protocol.md` tiers; `intel-surge-quality.md` class marks). A finding's
confidence class is provenance metadata about reviewer agreement.

**Strength**: Gives downstream consumers (human or fix-applying agent) a
triage-ordering that is derived, not asserted.

**Limitation**: Class names are adverse-local; adopting them verbatim into HUMMBL
would need a terminology decision (not taken here).

**Adoption recommendation**: ADOPT the four-class taxonomy as a candidate vocabulary
for the Adversarial Review Gate; keep names provisional.

---

## Primitive 6: Agent-Agnostic CLI Wrapper

**Observed implementation**: `AgentRunner` spawns any command that reads stdin/writes
stdout (`claude -p`, `codex exec --quiet`, `gemini`, `ollama run llama3.1`). Prompt
over stdin avoids argv limits; per-call timeout (default 600s) with SIGKILL; one retry
with the parse/validation error appended; cross-platform shlex.

**Evidence**: `src/runner.mjs` (all); README CLI usage + "Subprocess agent contract"
limitation.

**HUMMBL analogue**: The headless-agent mesh findings
(`agent-mesh-huaomp-mtsmu-matrix.md` — `claude --bare -p`, `codex exec`, pi, aider all
verified working on Anvil). adverse is a working consumer of exactly that mesh
capability.

**Strength**: Provider-agnostic by construction — this is the mechanism enabling L3/L4
decorrelation (run per-provider, diff reports).

**Limitation**: Known HUMMBL mesh boundaries apply: nested invocations lose auth
context (a `claude -p` spawned inside Claude Code fails — the repo's own live tests
note "won't pass from inside a nested Claude Code session"); on Anvil, `claude`
without `--bare` overflows context from skill auto-load.

**Adoption recommendation**: ADOPT for experimentation; document Anvil-specific
invocation (`claude --bare -p`) in any run instructions.

---

## Primitive 7: Skill Adapter

**Observed implementation**: `skills/adverse-review/SKILL.md` is a phase-by-phase
playbook executed by Claude Code itself: scope detection, Node helper for collection,
native Agent-tool subagent spawns (avoiding subprocess auth issues), Node helper for
synthesis, explicit failure-handling table, cleanup phase. Prompts are dumped from the
same `src/personas.mjs` source of truth.

**Evidence**: `skills/adverse-review/SKILL.md` (all);
`skills/adverse-review/scripts/dump-prompts.mjs`.

**HUMMBL analogue**: HUMMBL skill system (`skill-quality.md`,
`skill-adjacent-docs.md`) — same shape: SKILL.md as execution contract + `scripts/`
helpers. adverse's failure-handling table and degraded-run policy (≥2 personas or
abort) are above-median skill quality by HUMMBL's own standards.

**Strength**: Dual-surface (CLI + Skill) from one core eliminates drift; the SKILL.md
explicitly forbids the orchestrator from LLM-rendering findings or overriding persona
prompts.

**Limitation**: Skill hardcodes `/tmp/` paths (POSIX assumption; needs adjustment on
Windows) and `opus` as default model (cost implication if adopted verbatim).

**Adoption recommendation**: ADAPT — the structure is a good template for a HUMMBL
adversarial-review skill; paths, model tier defaults (`model-tier-policy.md`), and bus
receipts would need HUMMBL-specific rework.

---

## Primitive 8: CI Gate via Exit Code

**Observed implementation**: Exit 0 = approve/conditional/hold; 1 = BLOCK consensus
(precisely: `consensusLabel.startsWith('BLOCK')`, i.e. mean verdict score < 0); 2 =
bad args; 3 = fewer than 2 valid reviewers. README: "Code 1 is what you wire into a CI
gate."

**Evidence**: `src/cli.mjs:53, 240, 270`; README exit-code table.

**HUMMBL analogue**: `pr-automerge-pre-flight.md` / `pr-review-protocol.md` merge
gates; HGK policy-decision enum (allow/ask/deny/...).

**Strength**: Machine-consumable consequence; degraded runs (exit 3) fail loudly
rather than passing silently.

**Limitation**: Binary block-on-consensus is coarser than HUMMBL's severity ladder;
per Primitive 4, a lone critical reject does not block. Gate semantics need HUMMBL
calibration before any wiring (see governance-gap-analysis.md Gap 4).

**Adoption recommendation**: NOT YET as a blocking gate. Advisory-only until HUMMBL
gate policy is defined and operator-approved.

---

## Primitive 9: Report Artifact Emission

**Observed implementation**: Three formats — markdown (`renderMarkdown`), JSON
(`toJsonReport`: consensus label/score, per-reviewer verdicts + summaries, degraded
list, full findings with reporters/validators/challengers/confidence), self-contained
HTML dashboard (`src/html.mjs`). `--save-artifacts` preserves raw per-persona stdout
for debugging.

**Evidence**: `src/synthesis.mjs:198-308`; `src/html.mjs`; `src/cli.mjs`
(`--out/--json-out/--html-out/--save-artifacts`).

**HUMMBL analogue**: Review packets (`review-packets/` convention), bus REVIEW receipt
bodies. The JSON report is the natural substrate for a HUMMBL receipt — but is missing
required receipt fields (see Gap 3).

**Strength**: The JSON format preserves the full edge structure, so HUMMBL synthesis
policy could be re-run over the same data with different gate rules.

**Limitation**: No commit SHA, no agent/model identity, no timestamp, no source-cap
disclosure, no findings hash, no human-decision field.

**Adoption recommendation**: ADAPT — wrap `toJsonReport` output in a HUMMBL receipt
envelope rather than modifying upstream.

---

## Primitive 10: Retry-with-Feedback (output contract enforcement)

**Observed implementation**: Structured validators (`validatePhase1/2`) return precise
error strings; on parse or validation failure the runner re-prompts once with the
error appended ("RETRY — your previous response was rejected. Reason: ..."). Malformed
JSON is never repaired client-side — "Retry-with-feedback is the contract."

**Evidence**: `src/runner.mjs:12-17, 114-181`; `src/parse.mjs:17-18`;
`src/prompts.mjs:151-216`.

**HUMMBL analogue**: `sub-agent-injection-defense.md` mid-flight dispatch verification
(FINDINGS-section check + one-retry-then-stop policy) — adverse implements the same
one-retry discipline with a better feedback loop (the exact validator error goes back
to the model).

**Strength**: Cheap, bounded self-correction; degraded-run disclosure when it fails.

**Limitation**: Single retry with full re-invocation doubles cost on flaky models.

**Adoption recommendation**: ADOPT the validator-error-feedback pattern for HUMMBL
sub-agent dispatches that require schema-conformant output.

---

## Summary table

| # | Primitive | Adoption call |
|---|---|---|
| 1 | Independent Persona Review | ADOPT (lane-fencing prompt pattern) |
| 2 | Cross-Examination | ADOPT (validate/challenge/silence vocabulary) |
| 3 | Validate/Challenge Edges | ADOPT concept; use stable IDs, not title joins |
| 4 | Deterministic Synthesis | ADOPT principle; ADAPT verdict policy |
| 5 | Confidence Classification | ADOPT as candidate vocabulary |
| 6 | Agent-Agnostic CLI | ADOPT for experiments (Anvil: `claude --bare -p`) |
| 7 | Skill Adapter | ADAPT (paths, model tier, bus receipts) |
| 8 | CI Exit-Code Gate | NOT YET (advisory-only pending gate policy) |
| 9 | Report Artifact Emission | ADAPT (wrap in receipt envelope) |
| 10 | Retry-with-Feedback | ADOPT for schema-bound dispatches |
