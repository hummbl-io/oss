# Social Post: LinkedIn/X Summary

## LinkedIn Post

When an AI agent calls a tool, the generated call is often treated as implicitly authorized.

But generation is not the same as release authority.

An agent can generate a tool call that is:
- Out of scope (asked to summarize, tried to delete)
- Malformed (right intent, wrong arguments)
- Drifting (started legitimate, drifted to unintended outcome)
- Unsafe in context (valid in isolation, unsafe given state)

The fix: separate candidate generation from release authority.

Three outcomes:
- PROCEED: in-scope, well-formed, safe → execute
- NEEDS_REVIEW: potentially valid → human/governed review
- SILENCE: out-of-scope → drop silently

Every decision produces a receipt: decision, reason code, evidence, candidate hash, timestamp, agent identity.

Receipts should be inspectable, recomputable, and auditable.

Open question: how portable should conformance vectors be across CrewAI, smolagents, LangChain, LangGraph, and local runtimes?

I wrote a short essay on this pattern. Link in comments.

How are you handling tool-call authorization today?

#AI #AIAgents #Guardrails #LLM #AgentFrameworks

---

## X/Twitter Thread

1/ Generation is not release authority.

When an AI agent calls a tool, the generated call is often treated as implicitly authorized. But generation ≠ execution permission.

2/ An agent can generate a tool call that is:
- Out of scope
- Malformed
- Drifting toward unintended outcomes
- Unsafe in current context

3/ The fix: separate candidate generation from release authority.

Three outcomes:
- PROCEED → execute
- NEEDS_REVIEW → human review
- SILENCE → drop silently

4/ Every release decision should produce a receipt:
- decision (PROCEED/NEEDS_REVIEW/SILENCE)
- reason_code
- evidence
- candidate_hash
- timestamp
- agent_identity

5/ Receipts should be:
- Inspectable (humans can read them)
- Recomputable (same inputs → same decision)
- Auditable (reviewable after the fact)

6/ Static allowlists are necessary but not sufficient. They answer "is this tool permitted?" but not "is this tool call permitted right now?"

Dynamic task-scope checks are needed.

7/ Open question: how portable should conformance vectors be across CrewAI, smolagents, LangChain, LangGraph, and local runtimes?

Start with a minimal common schema, allow framework-specific extensions.

8/ Full essay: [link]

How are you handling tool-call authorization? Reach out.

---

## HF/LangChain Forum Excerpt

**Title: Generation is not release authority — a pattern for tool-call authorization**

When building agent systems, I've found it useful to separate candidate generation from release authority. The agent generates tool calls; a separate release authority decides whether to execute them.

The pattern uses three outcomes:
- **PROCEED**: The call is in-scope, well-formed, and safe. Execute it.
- **NEEDS_REVIEW**: The call is potentially valid but requires review (scope boundary, state modification, external communication, low confidence).
- **SILENCE**: The call is out-of-scope or unsafe. Drop it silently.

Every decision produces a receipt with: decision, reason_code, evidence, candidate_hash, timestamp, agent_identity.

I'm curious how others are handling this. Specifically:
1. Do you separate generation from release authority in your framework?
2. What does your decision receipt look like?
3. Are your receipts portable across frameworks?

Full essay: [link]
