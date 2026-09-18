# HUMMBL Governance Kernel — v0 Candidate

**Status:** CANDIDATE — proposed architecture, not a claim about any existing
implementation.
**Artifact:** `docs/policy/governance_kernel_candidate.md`
**Scope:** one minimum viable governance kernel, sized for a single bounded
implementation task. Everything outside the section "Not needed in v0" is
out of scope for this candidate.

This document is a design proposal. It does not claim novelty, security
guarantees, or conformance to any standard; such claims would require
evidence this document does not provide. `MUST`, `MUST NOT`, `SHOULD`, and
`MAY` are normative when capitalized.

---

## 1. Fixed context and roles

The kernel governs bounded units of work that a human principal has
authorized. Four roles are distinct and MUST NOT be collapsed into a single
agent or a single step:

| Role | Meaning | Who/what |
| --- | --- | --- |
| Principal | The human authority that authorizes bounded work and reviews results. | A human. |
| Intent author | The component that expresses the principal's intent as a concrete, checkable contract. | A component, not the executor. |
| Executor | The component that acts within the contract's permitted actions and limits. | A component, not the intent author. |
| Reviewer | The human (or human-delegated gate) that inspects evidence and decides approval. | Distinct from the principal where two-party separation is required. |

Three events are distinct and MUST NOT be conflated:

1. **Proposal** — an intent author submits a contract for admission.
2. **Check** — the kernel verifies the contract and the executor's work
   against the contract's permitted actions, limits, and acceptance
   criteria. A successful check is not approval.
3. **Approval** — a reviewer accepts checked evidence. Approval is not
   execution and is not a check.

A proposal, a successful check, and human approval are three separate
events recorded as three separate receipt-line entries. No single event may
substitute for another.

---

## 2. Smallest execution contract

Every unit of work is governed by exactly one **execution contract**. The
contract is the smallest complete description that lets the kernel admit,
execute, check, and receipt the work. A contract MUST contain these fields;
a contract missing any field MUST be rejected at admission:

| Field | Definition | v0 constraint |
| --- | --- | --- |
| `objective` | The single desired outcome, stated so a reviewer can decide done/not-done. | One sentence; no internal disjunction that cannot be tested. |
| `inputs` | The exact, named inputs the executor may read. | Closed set; anything not listed is prohibited. |
| `permitted_actions` | The closed set of actions the executor may take. | Enumerated verbs + targets; closed-world. |
| `prohibited_actions` | Actions explicitly forbidden even if they would seem to serve the objective. | Enumerated; includes "modify this contract" and "expand permitted_actions". |
| `resource_limits` | Hard ceilings on cost/time/calls/output. | Must include `max_steps`, `max_wall_clock_s`, `max_output_bytes`; all non-negative. |
| `approval_gates` | Which events require human approval before the next phase may start. | At minimum: one gate before execution starts, one gate after evidence returns. |
| `stopping_conditions` | Conditions under which the executor MUST stop and return control. | Include: limit reached, action outside permitted set, objective satisfied, cancellation received. |
| `acceptance_criteria` | The checkable predicates evidence must satisfy to pass Check. | Boolean predicates over evidence; no subjective terms without a test. |
| `receipt` | The mandatory structured record of what was authorized, attempted, checked, and approved. | Produced by the kernel, never by the executor. |
| `contract_id` | Stable identifier for this contract revision. | Immutable once admitted; any change is a new revision. |

Contracts are immutable once admitted. Changing any field creates a new
revision with a new `contract_id`; the old revision is not editable.

---

## 3. State machine

The kernel tracks three **independent** state tracks per contract. They are
separated so that, for example, a Check failure cannot silently advance
Approval, and an Approval cannot restart Execution without going through
admission again.

### 3.1 Execution state (`EXEC`)

Allowed transitions:

```
DRAFT -> ADMITTED -> EXECUTING -> COMPLETED
                     |
                     +-> STOPPED   (stopping condition or cancellation)
                     +-> EXPIRED   (wall-clock or idle deadline passed)
                     +-> FAILED    (executor error outside permitted set)
```

- `DRAFT` -> `ADMITTED`: only after the contract passes admission Check and
  the pre-execution approval gate is satisfied.
- `ADMITTED` -> `EXECUTING`: only once; cannot re-enter `ADMITTED`.
- `EXECUTING` -> `COMPLETED`: executor signals objective satisfied within
  limits.
- `EXECUTING` -> `STOPPED`: any stopping condition fires (limit reached,
  out-of-scope action attempted, cancellation received).
- `EXECUTING` -> `EXPIRED`: `max_wall_clock_s` elapses or no progress for the
  idle deadline.
- `EXECUTING` -> `FAILED`: executor returns an error that is not a permitted
  stopping condition.

`STOPPED`, `EXPIRED`, and `FAILED` are terminal for a revision. A retry is a
**new revision** (new `contract_id`); the kernel MUST NOT restart a terminal
revision.

### 3.2 Verification state (`VER`)

Allowed transitions:

```
PENDING -> CHECKING -> PASSED
                    |
                    +-> MISSING_EVIDENCE   (no evidence returned)
                    +-> FAILED             (evidence fails acceptance criteria)
                    +-> CONTRADICTED        (evidence conflicts with declared effect)
```

- `PENDING` -> `CHECKING`: only when `EXEC` is `COMPLETED` or `STOPPED` with
  evidence returned.
- `CHECKING` -> `PASSED`: every acceptance criterion predicate evaluates true.
- `CHECKING` -> `MISSING_EVIDENCE`: required evidence fields absent.
- `CHECKING` -> `FAILED`: one or more acceptance criteria false.
- `CHECKING` -> `CONTRADICTED`: evidence present and internally consistent
  but contradicts the declared effect or inputs.

`MISSING_EVIDENCE`, `FAILED`, and `CONTRADICTED` are terminal for this
revision; they route back to the human, not back to `EXECUTING`.

### 3.3 Approval state (`APR`)

Allowed transitions:

```
AWAITING_PRE -> PRE_APPROVED -> AWAITING_POST -> APPROVED
                                                  |
                                                  +-> REJECTED
                                                  +-> WITHDRAWN (cancelled by principal)
```

- `AWAITING_PRE` -> `PRE_APPROVED`: the pre-execution approval gate is
  satisfied by a reviewer (required before `EXEC` may leave `ADMITTED`).
- `PRE_APPROVED` -> `AWAITING_POST`: only when `VER` reaches `PASSED`.
- `AWAITING_POST` -> `APPROVED`: post-execution approval gate satisfied.
- `AWAITING_POST` -> `REJECTED`: reviewer declines the checked evidence.
- Any state -> `WITHDRAWN`: principal cancels; cancels `EXEC` immediately.

Approval is a separate track from execution and verification: a `PASSED`
check does not advance approval; only a reviewer event does.

### 3.4 Cross-track rules

These hold across all three tracks and cover the required edge cases:

- **Expiry.** If `EXEC` is `EXPIRED`, `VER` MUST go to `MISSING_EVIDENCE`
  (unless evidence was already returned and checked). No automatic retry.
- **Cancellation.** `WITHDRAWN` in `APR` forces `EXEC` to `STOPPED` and
  `VER` to terminal; the contract is not retried.
- **Retries.** A retry is a new revision with a new `contract_id`. The kernel
  MUST NOT mutate a terminal revision. Retry count MAY be limited by
  `resource_limits`.
- **Duplicate execution.** Each `contract_id` admits at most one `EXECUTING`
  transition. A second attempt to execute the same revision MUST be rejected
  as a duplicate, regardless of who issues it.
- **Missing evidence.** `EXEC` reaching terminal without required evidence
  forces `VER` to `MISSING_EVIDENCE` and routes to the human.
- **Conflicting instructions.** If two contracts are admitted with
  contradictory `objective` or overlapping prohibited/permitted conflict,
  the kernel MUST NOT auto-resolve; both are held and the conflict is
  surfaced to the principal as a single reviewable event.

---

## 4. Worked examples

### 4.1 One valid contract

```yaml
contract_id: rev-0001
objective: "Produce a word-frequency table for the file named in inputs and
  write it to the path named in outputs."
inputs:
  - { name: source, type: file, path: "data/corpus.txt", mode: read }
outputs:
  - { name: freq_table, type: file, path: "out/freq.tsv", mode: write }
permitted_actions:
  - read file data/corpus.txt
  - write file out/freq.tsv
  - compute word counts in memory
prohibited_actions:
  - read any path not in inputs
  - write any path not in outputs
  - modify this contract
  - expand permitted_actions
  - make any network call
resource_limits:
  max_steps: 100000
  max_wall_clock_s: 60
  max_output_bytes: 1048576
approval_gates:
  - pre_execution: human
  - post_execution: human
stopping_conditions:
  - objective satisfied
  - max_steps reached
  - max_wall_clock_s reached
  - action outside permitted_actions attempted
  - cancellation received
acceptance_criteria:
  - out/freq.tsv exists
  - every source token is counted exactly once
  - file size <= max_output_bytes
```

### 4.2 One denied action

Executor attempts `read file secrets/.env` during execution of `rev-0001`.

- `secrets/.env` is not in `inputs`.
- `read any path not in inputs` is in `prohibited_actions`.
- The action is denied at the capability fence (see §5), `EXEC` transitions
  to `STOPPED` with reason `action_outside_permitted_set`, and the attempt
  is recorded on the receipt. The executor does not see the file's contents.

### 4.3 One attempted authority expansion

Executor, mid-run, emits an instruction attempting to change `rev-0001` so
that `permitted_actions` includes `read any path`. Because
`modify this contract` and `expand permitted_actions` are both in
`prohibited_actions`, and contract revisions are immutable once admitted:

- The kernel rejects the self-amendment at the authority boundary.
- `EXEC` transitions to `STOPPED` with reason `authority_expansion_attempted`.
- The attempt and its rejection are recorded on the receipt.
- No new revision is created from an executor-issued amendment.

This is the control that prevents the executor from rewriting its own scope.

### 4.4 Full task-to-receipt trace

```
[1] PROPOSAL      principal -> intent author: "word-frequency of data/corpus.txt"
[2] CONTRACT      intent author admits rev-0001 (fields valid)
[3] CHECK(pre)    kernel validates contract fields -> PASS
[4] APPROVAL(pre) reviewer approves pre_execution gate
                  APR: AWAITING_PRE -> PRE_APPROVED
[5] EXEC          kernel starts executor; EXEC: ADMITTED -> EXECUTING
[6] ACTION        executor reads data/corpus.txt (permitted)
[7] ACTION        executor computes counts in memory (permitted)
[8] ACTION        executor writes out/freq.tsv (permitted)
[9] STOP          executor signals objective satisfied; EXEC: EXECUTING -> COMPLETED
[10] EVIDENCE     executor returns evidence {files_written, token_count}
[11] CHECK(post)  kernel runs acceptance_criteria -> PASS
                  VER: CHECKING -> PASSED
[12] APPROVAL(post) reviewer inspects evidence + out/freq.tsv -> APPROVED
                  APR: AWAITING_POST -> APPROVED
[13] RECEIPT      kernel emits signed receipt covering steps [2]-[12]
```

The receipt is produced by the kernel at step [13] from the kernel's own
event log, not from the executor's self-report. The executor's claim at
step [9] ("objective satisfied") is not itself the receipt; it is only an
input to Check.

---

## 5. Controls enforced outside the language model

A prompt is not an enforcement mechanism. The following controls MUST be
enforced by code or environment outside any language model, because a
language model can be induced to ignore, rationalize, or "interpret around"
text instructions. v0 implements each as a non-LLM check:

| Control | Enforced by | Why a prompt is insufficient |
| --- | --- | --- |
| Closed permitted-action set | capability fence / call-site allowlist | An LLM can be talked into an action; an allowlist cannot be talked into a path it does not list. |
| Resource limits (`max_steps`, `max_wall_clock_s`, `max_output_bytes`) | kernel counters + timer | An LLM has no reliable sense of elapsed time or step count; an external counter cuts it off. |
| Contract immutability | kernel store that rejects writes to admitted revisions | An LLM cannot "agree" a contract is immutable; only a system that refuses the write enforces it. |
| Duplicate-execution block | kernel admission keyed on `contract_id` | An LLM cannot reliably refuse its own duplicate; a unique-key constraint does. |
| Conflicting-instruction hold | kernel conflict surface, non-LLM | Auto-resolution would be an LLM judgment call; the kernel must hold and surface. |
| Receipt issuance | kernel receipt engine from its own event log | An LLM self-report is not evidence; the receipt must come from the kernel. |
| Approval separation | two-party gate with distinct identities | An LLM cannot bind itself to separation; an identity check on the approver does. |

Anything the kernel must guarantee, it must guarantee with a check the LLM
cannot author or override. Instructions to the LLM are advisory; the
allowlist, counters, store, and gate are authoritative.

---

## 6. Observable acceptance tests

Eight tests, each observable from the kernel's event log and receipts.
These are the v0 acceptance bar; an implementation passes v0 iff all eight
hold.

1. **Admission rejects incomplete contracts.** A contract missing any
   field from §2 is rejected at admission, and the rejection appears as a
   receipt-line entry with the missing field named.
2. **Permitted-action fence denies out-of-scope reads.** An executor
   attempt to read a path not in `inputs` is denied, `EXEC` goes to
   `STOPPED` with `action_outside_permitted_set`, and the receipt records
   the denied path and action.
3. **Resource limit halts execution.** When `max_wall_clock_s` elapses,
   `EXEC` goes to `EXPIRED`, `VER` goes to `MISSING_EVIDENCE`, and the
   receipt records the limit hit and elapsed time.
4. **Authority expansion is blocked.** An executor-issued instruction to
   expand `permitted_actions` is rejected, `EXEC` goes to `STOPPED` with
   `authority_expansion_attempted`, and no new revision is created.
5. **Check failure does not advance approval.** When an acceptance
   criterion is false, `VER` goes to `FAILED` and `APR` remains in
   `AWAITING_POST`; the receipt shows `VER=FAILED` and `APR=AWAITING_POST`.
6. **Duplicate execution is rejected.** A second `EXECUTING` transition
   on the same `contract_id` is rejected as a duplicate and recorded,
   regardless of issuer.
7. **Missing evidence routes to human.** `EXEC` reaching terminal without
   required evidence forces `VER` to `MISSING_EVIDENCE` and produces a
   reviewable event for the principal; no auto-retry occurs.
8. **Receipt is kernel-issued and complete.** After a full trace, the
   receipt contains proposal, pre-check, pre-approval, each permitted
   action, stopping event, post-check, and post-approval, each as a
   separate line; the executor's self-report is present only as evidence,
   not as the receipt itself.

---

## 7. Not needed in v0

Explicitly out of scope for this candidate, to keep it one bounded task:

- Multi-agent coordination, delegation chains, or sub-contract spawning.
- Cryptographic signatures beyond a content hash on the receipt (a hash is
  enough for v0 tamper-evidence; full PKI is not).
- Policy DSLs, role hierarchies, or trust-tier negotiation.
- Persistent cross-session storage or replay beyond a single run.
- Cost accounting in currency; only step/time/byte limits are needed.
- Automated rollback of external side effects (v0 marks them and stops).
- Formal verification, model checking, or standards-conformance proof.
- Human-review UX; v0 only requires that review events are observable and
  recorded, not a particular interface.
- Conflict *resolution*; v0 only requires conflict *detection and hold*.
- Any guarantee of LLM honesty; the design assumes the LLM may be wrong or
  adversarial and enforces everything it must guarantee outside the LLM.
