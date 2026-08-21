# Experiment Receipt: adverse on a seeded fixture

**Date**: 2026-07-05
**Operator authorization**: "i approve all experimental use" (chat, 2026-07-05)
**Runner**: claude-code (Fable 5), Anvil (Windows 11, RTX 3080 Ti 12 GB)
**adverse**: commit `4b9eb7b` (v0.2.1), Node v22.22.2
**Fixture**: 34-line Python module, one seeded defect per persona lane (reviewer never saw the ground-truth file)

| ID | Lane | Function | Seeded defect |
|---|---|---|---|
| D1 | Auditor (correctness) | `average_balance` | ZeroDivisionError on empty `history` |
| D2 | Adversary (security) | `get_account` | SQL injection via string-concatenated `user_id` |
| D3 | Pragmatist (maintainability) | `transfer` | bare `except` returns `True` on failure (no rollback/log) |

## Runs

| Arm | Agent | Config | Outcome |
|---|---|---|---|
| A | `ollama run qwen2.5-coder:7b` | 3 personas, 2 rounds, 240s cap | **abort exit 0**: all 3 round-1 calls timed out at 240s (GPU-contended); < 2 valid reviews |
| B | `ollama run qwen2.5-coder:7b` | 2 personas, single-round, 600s cap | **abort exit 0**: calls fast (9-15s) but model emitted malformed JSON; retry-with-feedback did not rescue; < 2 valid reviews |
| C | `codex exec` (hosted) | probe only | **blocked**: `--quiet` invalid in codex 0.142.5 (README drift); codex also usage-limited until Jul 7 |
| D | `claude --bare -p` (hosted) | probe only | **blocked**: "Not logged in" — nested-session auth boundary |
| E | `ollama run gemma-4-12B-it-qat` | 3 personas, single-round, 900s cap | **abort exit 3**: all 3 personas produced substantial output that found all defects, but 0 parsed |

## The decisive finding (Arm E)

gemma-4-12B — a capable local model — had **content recall 3/3 across all lanes**
but **parseable-output recall 0/3**. Its raw stdout (saved via `--save-artifacts`)
identified every seeded defect:

```
<|channel>thought
*   Function: average_balance(history)
    *   Issue 1: If history is empty, len(history) is 0. Division by ze^[[2D^[[K
zero error (ZeroDivisionError).
    *   Severity: Critical (crashes on empty input).
```

The run nonetheless aborted with **zero usable reviews**, for two compounding reasons:

1. **Thinking-channel prose**: the model emitted `<|channel>thought` + reasoning,
   violating adverse's "single JSON object, no prose" contract.
2. **TTY escape-code corruption**: `ollama run` streams to a TTY, embedding ANSI
   cursor-control codes (`^[[5D`, `^[[K`) *inside* the JSON string literals — 101
   such markers in one persona's output — which the parser correctly rejects ("Bad
   control character in string literal"). The retry (attempt 2, ~100s) could not
   fix an artifact the model does not control.

## Corroborating substrate signal (cross-referenced from autoresearch, devin CLI)

Arm E round-1 calls took **600-660s each** (retries 100-116s). Independent devin
CLI work in the autoresearch/Parameter-Golf repo the same day flagged **GPU drift:
mean delta +0.0465, 27× the noise floor, root-caused to ~90% GPU-memory saturation
from background processes** (Docker, Chrome, ollama, Xbox, Steam, WhatsApp). The two
observations are the same substrate: adverse's local-model arm and autoresearch's
experiment runs share one contended GPU. **Implication**: any HUMMBL local-model
review-gate arm needs GPU-clearance preflight + concurrency control (adverse runs
personas via unbounded `Promise.all` — 3 concurrent 12B loads on a 12 GB card
thrash), or the wall-time and reproducibility both degrade.

## Findings folded into the packet / candidate

1. **Output-contract fragility is the dominant local-model failure mode**, above
   model capability. A model that *finds* the bugs still yields nothing if it can't
   emit the schema cleanly. → argues for (a) a capable-model floor, (b) tolerating a
   reasoning channel + extracting JSON after it, (c) invoking local models with TTY
   rendering disabled (`OLLAMA_NOHISTORY` / piped, non-TTY) to avoid escape-code
   injection. This is an adverse-integration gap, not a HUMMBL-doctrine gap.
2. **Nested-auth boundary CONFIRMED** (Arm D) — validates the packet mesh claim;
   hosted review runs must spawn from a plain shell.
3. **Version drift** (Arm C) — pin agent-CLI invocations; README examples age.
4. **≥2-persona floor** even in `--single-round`.
5. **Lane-fencing is prompt-only and failed here** — all three gemma personas
   discussed all three defects (SQL injection appeared in the Auditor and Pragmatist
   outputs, out of their lanes). Confirms primitive-map Primitive 1's limitation:
   nothing verifies a persona stayed in its lane; a weaker/local model ignores the
   fence.
6. **GPU contention degrades the local-model arm** (this receipt + devin cross-ref).

## What did NOT happen

No successful synthesized report was produced in any arm. The experiment measured
adverse's *operational envelope on Anvil*, not its review *quality* — that requires a
hosted arm run from a non-nested shell (deferred: codex usage-limited, claude nested,
gemini deprecated during this window). No agent spend incurred (all local or blocked
probes). Ground truth and all raw artifacts retained under the Anvil fixture dir; not
committed (transient).
