# Forum Post: Hugging Face / smolagents

**Title:** Capability allowlists are necessary, but not sufficient: toward recomputable tool-call guardrail receipts

**Target:** Hugging Face Forum (smolagents category)

**Word count:** ~750 words

---

When building agent systems with `ToolCallingAgent` or `CodeAgent`, most of us reach for a capability allowlist: a list of tools the agent is permitted to call. This is necessary. It is not sufficient.

A capability allowlist answers one question: "is this tool permitted at all?" It does not answer: "is this tool call permitted right now, in this context, for this task?"

Consider a `CodeAgent` running `step()` with a `GuardrailProvider`. The agent has `file_read` and `file_write` in its allowlist. It generates a `file_write` call. The allowlist says "yes, `file_write` is permitted." But:

- Is the write in scope for the current task? (The agent was asked to summarize, not edit.)
- Are the arguments well-formed? (Path traversal, wrong encoding, oversized payload.)
- Is the context safe? (Concurrent operations, rate limits, user state.)
- What evidence supports the decision?

A tool-call guardrail should ideally return more than `allow` / `deny`. It should return a **receipt**:

```json
{
  "decision": "NEEDS_REVIEW",
  "reason_code": "scope_boundary",
  "evidence": {
    "task_scope": "summarize document",
    "tool_called": "file_write",
    "scope_match": false
  },
  "bound_inputs": {
    "tool": "file_write",
    "args": {"path": "/etc/hosts", "content": "..."},
    "declared_task_scope": "summarize document"
  },
  "verifier_depth": "static_scope_check",
  "recomputability_boundary": "deterministic_given_inputs",
  "candidate_hash": "sha256:...",
  "timestamp": "2026-07-01T00:00:00Z",
  "agent_identity": "agent-alpha"
}
```

The key fields:

- **decision**: `PROCEED`, `NEEDS_REVIEW`, or `SILENCE` (not just allow/deny)
- **reason_code**: machine-readable reason for the decision
- **evidence**: structured evidence supporting the decision
- **bound_inputs**: the tool, args, and declared task scope that were evaluated
- **verifier_depth**: how deep the verification went (static check, dynamic scope check, human review)
- **recomputability_boundary**: can the decision be recomputed from the inputs? (deterministic, probabilistic, non-recomputable)

Why does this matter?

**1. Debugging.** When an agent behaves unexpectedly, you need to know why the guardrail allowed or denied a call. A receipt gives you the evidence. `allow` / `deny` gives you nothing.

**2. Auditing.** If you're running agents in a governed environment, you need an audit trail. Receipts are auditable. Boolean decisions are not.

**3. Recomputability.** If a guardrail decision is deterministic given inputs, you can replay it. You can verify that the same inputs produce the same decision. This is essential for conformance testing.

**4. Human-in-the-loop.** `NEEDS_REVIEW` is a useful third state. It says "this might be okay, but a human should check." Binary allow/deny forces the human to either block everything or trust everything.

In smolagents terms, a `GuardrailProvider` could expose:

```python
class GuardrailProvider:
    def evaluate(self, tool_call, task_scope, context) -> GuardrailReceipt:
        ...
```

Instead of:

```python
class GuardrailProvider:
    def allow(self, tool_call) -> bool:
        ...
```

The receipt-based API is a small change with large implications for debuggability, auditability, and recomputability.

**Three questions for the community:**

1. Would a tiny provider-neutral conformance fixture be useful? (A standard set of test cases that any receipt-producing guardrail should pass.)

2. Should framework-level guardrails expose only `allow` / `deny`, or also structured evidence? What would the evidence schema look like for your use case?

3. How should dynamic task-scope judgments expose their recomputability boundary? If the guardrail uses a probabilistic model, the receipt should say so. If it's deterministic, the receipt should say that too.

I don't have a final answer on any of these. I'm interested in how others are thinking about it.

**Public artifact:** I've drafted a minimal receipt schema and a short essay on the "generation is not release authority" pattern. Link: `https://hummbl.dev/go/guardrail-receipts`

Feedback welcome.
