# Durable Intelligence Doctrine v0.1

**Status: CANDIDATE DOCTRINE — REQUIRES REVIEW**

Issue: hummbl-io/hummbl-io#162

## Purpose

Preserve and operationalize the recommendation that durable
intelligence should be treated as a first-class component of HUMMBL
agent workflows, not as optional documentation after the fact.

## Core thesis

Durable intelligence makes problem-solving less difficult by reducing
repeated uncertainty. It converts an incoming agent's starting question
from:

> What happened, what is true, what was tried, what failed, what
> remains, and what am I allowed to do?

into:

> Here is the current state, the evidence, the unresolved edge, and
> the next bounded action.

The underlying technical problem may remain unchanged, but coordination
entropy, reconstruction cost, and error risk are reduced.

## Mental model

Treat durable intelligence as **state compression for future reasoning**.

A high-quality durable object compresses historical work into:

- current state
- provenance
- evidence
- claim posture
- decisions
- constraints
- failed paths
- unresolved questions
- next actions
- completion criteria

The goal is not maximum narrative detail. The goal is minimum
sufficient state for accurate continuation.

## Agent-session receipt schema

See `session-receipt.schema.json` for the JSON Schema.

### Required fields

| Field | Purpose |
|-------|---------|
| `schema_version` | `agent_session_receipt.v0.1` |
| `session_id` | Unique session identifier |
| `source_agent` | Agent identity |
| `environment` | Host, platform, Python version |
| `tools_available` | What tools the agent had access to |
| `repository_or_system_scope` | What repos/systems were in scope |
| `starting_state` | Branch, HEAD, open PRs/issues at start |
| `actions_attempted` | What was tried and the result |
| `mutations_made` | What artifacts were actually created |
| `claims` | Claims with explicit posture |
| `decisions` | Decisions with authority source |
| `negative_knowledge` | What did NOT happen or is NOT established |
| `open_questions` | What remains unresolved |
| `next_actions` | What should happen next |
| `authority_boundaries` | What was allowed and disallowed |
| `receipt_destination` | Where the receipt is preserved |
| `completion_status` | Final status of the session |

### Optional fields

| Field | Purpose |
|-------|---------|
| `handoff_disposition` | CONFIRMED / REFUTED / INCONCLUSIVE / BLOCKED / SUPERSEDED |

## Claim-posture vocabulary

Every claim must declare one of seven postures:

| Posture | Meaning |
|---------|---------|
| `observed` | Directly observed by the agent |
| `source_reported` | Reported by a source but not independently verified |
| `inferred` | Derived from other evidence |
| `provisional` | Tentative, subject to verification |
| `verified` | Independently confirmed against live state |
| `refuted` | Contradicted by evidence |
| `unresolved` | Neither confirmed nor refuted |

Agents must not infer that review implies mutation, discussion implies
verification, or a previous verdict implies independent confirmation.

## Mutation truthfulness

Every receipt must explicitly state whether branches, commits, PRs,
issues, files, deployments, or other artifacts were actually created.
No artifact may be implied without a confirmed identifier or receipt.

The `mutations_made` array uses `created: true/false` to make this
explicit. An empty array means no mutations were made.

## Environment capability disclosure

Agents must record whether they had:
- `shell` — command execution
- `filesystem` — file read/write
- `network` — network access
- `connector` — live connector access (GitHub, Linear, etc.)
- `browser` — browser automation
- `test_runner` — test execution
- `deployment` — deployment capability
- `write_access` — write to repos/systems
- `read_only` — read-only mode

Conclusions should be bounded by those capabilities. An agent without
`connector` access should not claim to have verified GitHub state.

## Negative knowledge

Record what did not happen and what is not established:

- no code changed
- no branch created
- no commit made
- hypothesis not confirmed
- environment lacked required tools
- authority source not found

This prevents repeated dead ends and fabricated continuity.

## Handoff dispositions

Where a session ends on a candidate defect or unresolved claim:

| Disposition | When to use |
|-------------|-------------|
| `CONFIRMED` | Claim verified and accepted |
| `REFUTED` | Claim contradicted by evidence |
| `INCONCLUSIVE` | Evidence insufficient |
| `BLOCKED_MISSING_AUTHORITY` | Cannot proceed without operator |
| `SUPERSEDED` | Overtaken by newer work |

## Approved durable sinks

Receipts should be preserved in one of:

- `github_issue` — GitHub issue
- `github_pr_comment` — PR comment
- `governed_receipt_dir` — governed receipt directory
- `claim_evidence_ledger` — claim-evidence ledger
- `task_registry` — task registry
- `handoff_index` — canonical handoff index

Chat-only preservation is insufficient for operational continuity.

## Re-entry verification

Incoming agents should verify live state before trusting stale
handoffs. At minimum confirm:

1. Current branch/HEAD
2. Active issue/PR state
3. Relevant file contents
4. Authoritative source versions

## Compounding returns

A preserved answer becomes a reusable pattern. A repeated pattern
becomes a candidate workflow. A validated workflow becomes automatable
infrastructure.

## Measurement indicators

Track practical indicators such as:

- time to first correct action
- repeated investigations avoided
- false assumptions caught
- duplicate issues or patches prevented
- handoffs completed without operator re-explanation
- percentage of sessions with valid receipts
- percentage of receipts independently revalidated

## Acceptance criteria

- [x] A canonical home for the doctrine is selected — `hummbl-governance/docs/durable-intelligence/`
- [x] A versioned agent-session receipt schema or template is drafted — `session-receipt.schema.json`
- [x] Claim-posture vocabulary is reused from existing HUMMBL governance work — 7 postures aligned with existing evidence-grade vocabulary
- [x] Mutation-truthfulness and environment-capability fields are mandatory — in schema required fields
- [x] At least one existing handoff is converted into the proposed format as a fixture or example — see fixtures
- [x] A validation path is defined, preferably machine-checkable and stdlib-first — see validator
- [x] Guidance identifies approved durable sinks and re-entry verification requirements — see sections above
- [x] No new canonical terminology is admitted without audit — "Durable Intelligence Doctrine" remains a working label until reviewed

## Non-goals

- Creating a new canonical terminology without audit
- Replacing existing handoff or receipt systems
- Requiring maximum narrative detail
- Treating durable intelligence as optional documentation

## References

- Issue: hummbl-io/hummbl-io#162
- Seed example: hummbl-io/hummbl-production#747
- Existing vocabulary: evidence-grade skill, claim-verify skill
