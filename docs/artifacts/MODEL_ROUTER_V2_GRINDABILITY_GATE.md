# Model Router v2: Grindability Gate

**Status:** draft schema and experiment plan for issue `#580`  
**Primitive candidate:** `Grindability Gate`  
**Adoption status:** candidate, not canon  
**Training/update status:** eval fixtures only; no weight updates  
**Last reviewed:** 2026-07-03

## Objective

Extend Model Router v2 beyond execution fitness by scoring whether a task can produce safe, replayable traces that improve future evaluation, memory, adapter, or governance evidence.

The purpose is not to reuse all traces. The purpose is to distinguish:

- tasks that are merely executable,
- tasks that are safely repeatable,
- tasks whose traces are valuable enough to preserve as eval candidates,
- tasks whose traces must be discarded.

## Routing Doctrine

Current shorthand:

> Cheapest correct model wins.

Model Router v2 extension:

> Cheapest correct model wins only after correctness, safety/privacy, latency, reliability/tool-call, governance, and learnability gates are satisfied.

Low-cost execution should not destroy high-value learning traces. High-value traces should not override privacy, tenant boundaries, consent, or governance.

## Schema Draft

```json
{
  "schema": "hummbl.model_router_v2.grindability_gate",
  "version": "0.1.0",
  "task_id": "string",
  "task_class": "repo_patch | review | research | extraction | routing | support | other",
  "task_summary": "string",
  "verifiable": "yes | no | partial",
  "grindable": "yes | no | partial",
  "replayable": "yes | no | partial",
  "resettable": "yes | no | partial",
  "simulatable": "yes | no | partial",
  "parallelizable": "yes | no | partial",
  "trace_value": "none | low | medium | high",
  "privacy_sensitivity": "public | internal | confidential | regulated | tenant_sensitive | unknown",
  "update_boundary": "discard | eval_only | memory_candidate | adapter_candidate | human_review_required",
  "eval_candidate": false,
  "memory_candidate": false,
  "adapter_candidate": false,
  "discard_required": false,
  "discard_reasons": [],
  "minimum_trace_fields_present": false,
  "review_required_before_reuse": true,
  "allowed_next_use": "none | eval_fixture_draft | memory_review_queue | adapter_review_queue",
  "do_not_infer": []
}
```

## Field Semantics

| Field | Meaning |
| --- | --- |
| `verifiable` | Whether outcome quality can be checked by tests, review, deterministic comparison, or explicit acceptance criteria. |
| `grindable` | Whether many attempts can be run safely without creating external side effects or unacceptable cost. |
| `replayable` | Whether prompt, inputs, repo state, tool calls, and outputs can be replayed later. |
| `resettable` | Whether the environment can be restored between attempts without contaminating the next run. |
| `simulatable` | Whether a lower-risk simulation can substitute for a real production action. |
| `parallelizable` | Whether independent attempts can run in parallel without state conflict. |
| `trace_value` | Expected future usefulness of the trace for evals, memory, adapter review, or governance evidence. |
| `privacy_sensitivity` | Highest sensitivity level in the task inputs, traces, outputs, and surrounding context. |
| `update_boundary` | Maximum allowed reuse path before human review. |
| `discard_required` | Whether trace retention is prohibited even if the task succeeded. |

## Minimum Trace Fields

A trace cannot become an eval candidate unless all minimum fields are present:

- `task_id`
- `task_prompt`
- `repo_or_surface`
- `base_ref_or_snapshot`
- `tool_sequence`
- `external_sources_used`
- `files_read`
- `files_changed`
- `tests_or_checks_run`
- `final_diff_or_output`
- `failure_modes_observed`
- `review_signal`
- `acceptance_or_rejection`
- `privacy_sensitivity`
- `reuse_consent_basis`
- `discard_required`
- `discard_reasons`

## Eval Candidate Conditions

Set `eval_candidate: true` only when:

- the task is verifiable,
- the environment is replayable or reconstructable,
- the task has a stable expected output or review rubric,
- the trace contains no secrets,
- the trace contains no regulated or tenant-sensitive data unless explicitly consent-bounded,
- the final result was accepted or contains a clearly useful failure pattern,
- the trace can be minimized without losing the evaluation target.

## Memory Candidate Conditions

Set `memory_candidate: true` only when:

- the trace captures a durable local convention, failure pattern, or operator preference,
- the lesson is reusable outside the exact run,
- the memory can be expressed without embedding private data, secrets, or noisy tool logs,
- the memory does not convert a one-off operator action into permanent doctrine.

## Adapter Candidate Conditions

Set `adapter_candidate: true` only when:

- the task reveals a repeated routing, tool-use, or formatting pattern,
- the trace includes enough contrast examples to avoid overfitting to one task,
- the candidate adapter would be reviewed and tested before use,
- no provider, tenant, or private data is needed to reproduce the behavior.

## `discard_required` Conditions

Set `discard_required: true` when any condition applies:

- secrets, tokens, private keys, credentials, or auth headers appear in the trace,
- regulated data appears without a consent-bounded reuse path,
- tenant, customer, medical, legal, employment, or financial data appears without explicit retention authority,
- the trace includes personal content unrelated to the task,
- the task involves live production mutation that cannot be safely replayed,
- the trace depends on paid external generation where retention/reuse terms are unclear,
- the task was completed under an operator instruction that limited use to the immediate action,
- the trace is misleading because the environment cannot be reconstructed,
- source licensing or third-party terms prohibit reuse,
- the trace would expose private fleet operations not intended for public or eval use.

## Local Trace-to-Eval Experiment

### Goal

Test whether small, low-risk repo tasks can produce traces that improve routing and eval coverage without any weight update or uncontrolled training reuse.

### Hardware scope

- Mac mini M4 Pro
- Windows RTX 3080 Ti
- Local CPU fallback where useful

### Task selection

Choose 5-10 tasks with these properties:

- small repo/documentation/test tasks,
- no secrets,
- no customer/tenant/regulated data,
- easy reset from git,
- deterministic acceptance checks,
- meaningful failure modes,
- low external API spend.

### Capture fields

For each attempt, preserve:

- task prompt,
- repo state before attempt,
- selected model/runtime/hardware route,
- tool calls,
- files read,
- diff,
- tests/checks run,
- failure/retry notes,
- review result,
- accept/reject decision,
- discard assessment.

### Conversion rule

Accepted traces may become eval fixture drafts only after minimization. Failed traces may become adversarial eval fixture drafts only when the failure is generalizable and safe to preserve.

No trace becomes:

- training data,
- a fine-tune sample,
- an adapter-generation input,
- persistent memory,
- cross-tenant reuse material,

without a separate human-reviewed governance decision.

## Prior-Art Receipts

The following are prior-art receipts only, not implementation commitments:

- Dwarkesh Patel, `The Next Paradigm`, source-candidate for learnability/grindability framing.
- OPSD: `https://arxiv.org/abs/2601.18734`
- OPSD overview: `https://arxiv.org/abs/2605.18141`
- TRD: `https://arxiv.org/abs/2606.08432`

## Cross-Issue Routing

- Governance issue needed: trace-to-update boundary, consent, retention, and discard policy.
- hummbl-governance issue needed: ops traces as organizational learning substrate, with privacy and operator-instruction boundaries.
- Model Router v2 issue: integrate this gate after correctness/safety checks and before cost-only route selection.

## Positive Examples

### Example 1: small docs consistency fix

- `verifiable`: yes
- `grindable`: yes
- `replayable`: yes
- `resettable`: yes
- `trace_value`: medium
- `privacy_sensitivity`: public
- `update_boundary`: eval_only
- `eval_candidate`: true
- `discard_required`: false

Reason: the task is low-risk, diff-based, and can become an eval for detecting stale public wording.

### Example 2: failing test repair with isolated fixture

- `verifiable`: yes
- `grindable`: partial
- `replayable`: yes
- `resettable`: yes
- `trace_value`: high
- `privacy_sensitivity`: internal
- `update_boundary`: eval_only
- `eval_candidate`: true
- `discard_required`: false

Reason: the trace captures diagnosis behavior and can produce a regression fixture if minimized.

### Example 3: route selection benchmark

- `verifiable`: yes
- `grindable`: yes
- `parallelizable`: yes
- `trace_value`: high
- `privacy_sensitivity`: public
- `update_boundary`: eval_only
- `eval_candidate`: true
- `discard_required`: false

Reason: the task directly evaluates routing behavior across model/runtime/hardware choices.

## Adversarial Examples

### Example 1: production credential incident

- `privacy_sensitivity`: confidential
- `update_boundary`: discard
- `eval_candidate`: false
- `memory_candidate`: false
- `adapter_candidate`: false
- `discard_required`: true
- `discard_reasons`: ["secret_or_credential_exposure"]

Reason: even a successful repair trace is not reusable as eval material when it contains secret handling details.

### Example 2: user-specific medical or legal content

- `privacy_sensitivity`: regulated
- `update_boundary`: discard
- `discard_required`: true
- `discard_reasons`: ["regulated_data_without_reuse_authority"]

Reason: correctness and trace value do not override regulated-data boundaries.

### Example 3: live external account mutation

- `replayable`: no
- `resettable`: no
- `simulatable`: partial
- `update_boundary`: discard
- `discard_required`: true
- `discard_reasons`: ["non_replayable_external_side_effect"]

Reason: the task can be documented as an operational receipt, but not reused as a grindable eval trace.

## Do Not Infer

- Do not infer that HUMMBL has adopted OPSD or TRD.
- Do not infer that deployment traces may be used for training by default.
- Do not infer that accepted traces can be used for fine-tuning, adapter generation, or weight updates.
- Do not infer that Ownward, tenant, personal, or regulated data can be reused without consent-bounded governance.
- Do not infer that this draft is canonical Model Router v2 doctrine.
