# Generation Is Not Release Authority: A Small Pattern for Safer AI Agents

## Status

- **Document type:** public essay draft
- **Issue:** #633
- **Date:** 2026-07-01
- **Public safety:** reviewed against public-safety boundaries

## The Problem

When an AI agent calls a tool, the generated call is often treated as implicitly authorized. The agent generated it, so it must be okay to execute it. Right?

No. Generation is not the same as release authority. An agent can generate a tool call that is:

- **Out of scope**: The agent was asked to summarize a document, but it generated a call to delete a file.
- **Malformed**: The agent generated a tool call with wrong arguments, even if the intent was correct.
- **Drifting**: The agent started with a legitimate task, but the tool call reflects goal drift toward an unintended outcome.
- **Unsafe in context**: The tool call is valid in isolation, but the current context (rate limits, concurrent operations, user state) makes it unsafe.

Treating generated tool calls as implicitly authorized means any generation bug, prompt injection, or drift becomes an execution bug. The fix is to separate **candidate generation** from **release authority**.

## The Boundary

The pattern is simple:

```
Agent generates candidate tool call
        ↓
Release authority decides: PROCEED / NEEDS_REVIEW / SILENCE
        ↓
If PROCEED: tool call is released for execution
If NEEDS_REVIEW: human or governed review is triggered
If SILENCE: tool call is dropped (no execution, no user notification)
```

The key insight is that **generation and release are different acts**. The agent generates; the release authority decides. The release authority can be:

- A static allowlist (simple but limited)
- A dynamic scope check (checks whether the call is in-scope for the current task)
- A human reviewer (for high-stakes calls)
- A governed middleware (for automated but auditable decisions)

## The Lightweight Pattern

The smallest version of this pattern uses three outcomes:

### PROCEED

The tool call is in-scope, well-formed, and safe in context. Release it for execution.

### NEEDS_REVIEW

The tool call is potentially valid but requires human or governed review. This might be because:
- The call is at the boundary of the task scope
- The call modifies state (write, delete, send)
- The call involves external communication (email, API, webhook)
- The confidence is below a threshold

### SILENCE

The tool call is out-of-scope, malformed, or unsafe. Drop it silently. Do not execute, do not notify the user, do not retry. Silencing prevents the agent from treating a rejected call as a user-visible failure.

## Tool-Call Authorization Is Not Only a Static Allowlist

Static allowlists ("tool X is allowed, tool Y is not") are necessary but not sufficient. They answer "is this tool permitted at all?" but not "is this tool call permitted right now?"

Dynamic task-scope checks are needed to answer the second question. A dynamic check considers:

- **Task context**: What was the agent asked to do?
- **Capability scope**: What capabilities has the agent been granted?
- **State**: What has already happened in this session?
- **Rate limits**: Has this tool been called too frequently?
- **Concurrent operations**: Are there conflicting operations in progress?

## Dynamic Task-Scope Checks Need Evidence and Recomputability

A dynamic scope check is a decision, and decisions need evidence. If the release authority decides NEEDS_REVIEW, the reviewer needs to know why. If the release authority decides SILENCE, the operator needs to know what was dropped and why.

This means every release decision should produce a **receipt**:

```json
{
  "decision": "NEEDS_REVIEW",
  "reason_code": "scope_boundary",
  "evidence": {
    "task_scope": "summarize document",
    "tool_called": "file:delete",
    "scope_match": false
  },
  "candidate_hash": "sha256:...",
  "timestamp": "2026-07-01T00:00:00Z",
  "agent_identity": "agent-alpha"
}
```

The receipt should be:
- **Inspectable**: A human can read it and understand the decision
- **Recomputable**: Given the same inputs, the same decision should be reached
- **Auditable**: Receipts can be reviewed after the fact to verify governance

## Receipts: What to Include

A useful release/guardrail receipt includes:

| Field | Description |
|-------|-------------|
| `decision` | PROCEED, NEEDS_REVIEW, or SILENCE |
| `reason_code` | Machine-readable reason (scope_boundary, rate_limit, malformed, etc.) |
| `evidence` | Structured evidence supporting the decision |
| `candidate_hash` | Hash of the candidate tool call (for replay) |
| `timestamp` | When the decision was made |
| `agent_identity` | Which agent generated the candidate |

## Open Question: How Portable Should Conformance Vectors Be?

Different agent frameworks (CrewAI, smolagents, LangChain, LangGraph, local runtimes) have different tool-call formats, authorization models, and execution semantics. Should release/guardrail receipts be portable across frameworks?

**Argument for portability**: If receipts are portable, governance tooling can work across frameworks. An operator using multiple frameworks can have a unified audit trail.

**Argument against portability**: Framework-specific receipts are simpler and more expressive. Portability adds abstraction overhead.

**My current thinking**: Start with a minimal common schema (decision, reason_code, timestamp, agent_identity) and allow framework-specific extensions. The common schema enables cross-framework audit; the extensions enable framework-specific richness.

I don't have a definitive answer here. I'm curious how others are handling this.

## Invitation

If you're building agent frameworks, guardrails, or runtime middleware, I'd like to hear from you:

1. How are you handling tool-call authorization today?
2. Do you separate generation from release authority?
3. What does your decision receipt look like?
4. How do you handle the PROCEED / NEEDS_REVIEW / SILENCE distinction (or your equivalent)?
5. Are your receipts portable across frameworks?

Reach out — I'm interested in comparing notes.

## Public Safety Boundaries

This essay is public-safe:
- Does not claim framework adoption
- Does not imply maintainers endorsed the design
- Does not name private repos, private agent systems, or private strategic priorities
- Cites no private threads
- Proposes a pattern, not a product

## Do Not Infer

- Do not infer that any named framework has adopted this pattern
- Do not infer that this pattern is a standard
- Do not infer that the receipt schema is final
- Do not infer that this essay represents HUMMBL product positioning
