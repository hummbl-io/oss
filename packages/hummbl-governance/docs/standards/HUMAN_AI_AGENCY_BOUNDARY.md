# Human Agency and AI Agency Boundary Model

Status: draft standard for issue #162.
Last updated: 2026-07-03.

## Purpose

HUMMBL uses agentic systems, but `agentic` must not blur the boundary between
human agency and AI/agent agency. This standard defines that boundary so
systems can preserve Human Command without dehumanizing people or
overhumanizing software agents.

## Core Distinction

Human agency is existential, ethical, embodied, temporal, relational, and
meaning-bearing. It includes intention, refusal, discernment, values, recovery,
relationship, creativity, self-authorship, and responsibility.

AI/agent agency is instrumental and delegated. It can plan, route, call tools,
execute tasks, and preserve receipts only inside bounded authority, policy, and
audit constraints.

## Boundary Stack

| Dimension | Human agency | AI/agent agency |
|---|---|---|
| Authority | Intrinsic and person-bearing | Delegated and bounded |
| Body | Embodied | Non-embodied or externally embodied through tools or robots |
| Time | Lived temporal experience | Scheduled, computed, or triggered execution |
| Values | Owned and accountable | Represented, inferred, or policy-constrained |
| Refusal | Moral and personal right | Policy behavior or escalation path |
| Responsibility | Human, legal, and social accountability | Traceable operational responsibility only |
| Meaning | Self-authored and relational | Modeled, retrieved, or assisted |
| Command | Human retains final authority where gates require it | Agent acts under granted scope |

## Definitions

- Human agency: the person's capacity for embodied judgment, meaning,
  responsibility, refusal, relationship, and self-authorship.
- AI/agent agency: delegated operational capability under bounded authority,
  policy, audit, and revocation constraints.
- Delegation: a human or authorized role grants bounded authority while
  retaining command, revocation, and responsibility gates.
- Dependency: reliance on a system increases and may reduce independent human
  competence, confidence, or optionality.
- Abdication: consequential authority moves outside meaningful Human Command.
- Escalation: a route that moves a decision or action to a higher-authority
  human, policy, or review path when risk, ambiguity, or boundary conditions
  require it.
- Revocation: withdrawal of delegated authority, capability, memory, access, or
  execution permission.
- Command: the human authority structure that grants, scopes, reviews,
  interrupts, overrides, or revokes agent action.
- Earned autonomy: expanded agent autonomy based on evidence, per-skill
  performance, correction history, reversibility, and risk gates.
- Reflective friction: an intentional pause, question, or check that preserves
  human judgment instead of merely slowing workflow.
- Defeater mechanism: a condition, signal, or explanation that tells the human
  when not to trust or follow the AI output.

## Delegation vs Dependency vs Abdication

| State | Boundary condition | Governance posture |
|---|---|---|
| Delegation | Human command remains meaningful; scope, duration, reversibility, receipts, and revocation are clear. | Allowed when risk gates pass. |
| Dependency | The human can still intervene, but repeated use may erode skill, judgment, or confidence. | Monitor and add reflective friction where needed. |
| Abdication | Consequential authority is effectively transferred to an agent or opaque workflow without meaningful human command. | Prohibited for consequential actions. |

Delegation can increase human agency when it expands capability without
removing command. Dependency requires monitoring. Abdication is a governance
failure.

## Mandatory Boundary Test for Consequential Actions

For any consequential agent action, the reviewer or gate must answer:

1. Authority: who granted permission, at what scope, for what duration?
2. Agency level: is the agent observing, advising, drafting, staging,
   committing, or executing externally?
3. Autonomy level: is execution human-commanded, approval-gated,
   exception-gated, monitored, or autonomous?
4. Reversibility: can the action be undone, reverted, or compensated?
5. Receipts: are inputs, reasoning summaries, tool calls, outputs, approvals,
   and state changes preserved?
6. Intervention readiness: can a human understand, interrupt, override, or
   redirect in time?
7. Competence preservation: does the workflow preserve human skill and judgment
   or silently deskill the user?
8. Value drift: could repeated suggestions shift user goals or preferences
   without reflective endorsement?
9. Dependency risk: does delegation increase capability or create abdication?
10. Human/nonhuman boundary: does language imply human-equivalent moral
    authority for the agent or machine-like expectations for the human?

Human Command must include override and revocation, but it does not require
constant human approval for low-risk reversible tasks.

## Human Command Preservation Tests

An agent action preserves Human Command when all required statements are true:

- The authority grant is explicit or traceable.
- The action is inside granted scope.
- The consequence level is known.
- The action is reversible or has accepted irreversible-risk documentation.
- A human can interrupt, override, or revoke when the risk gate requires it.
- The receipt trail identifies the actor, authority grant, tool calls, output,
  and state changes.
- The workflow does not disguise dependency or abdication as empowerment.
- Public or product language does not imply the agent has human-equivalent
  moral standing or authority.

If any required statement fails, route to escalation or deny execution.

## Public-Language Warning List

Avoid language that dehumanizes humans:

- "make humans more agentic" without naming judgment, values, consent, or
  self-authorship,
- "optimize the user" as if the person is a system component,
- "human in the loop" when the human has no real authority,
- "friction" for every reflective pause or refusal right.

Avoid language that overhumanizes agents:

- "the agent decided" when the system selected an output under delegated scope,
- "the agent owns responsibility" for legal, ethical, or social accountability,
- "autonomous authority" without scope, revocation, and receipts,
- "refusal" when the behavior is policy enforcement or escalation.

Preferred language:

- "delegated authority",
- "bounded autonomy",
- "human command",
- "review gate",
- "revocation path",
- "receipt-backed action",
- "agent-selected output",
- "human-accountable decision".

## Crosswalk

| Workstream | Boundary connection |
|---|---|
| Ownward language law | Health and executive coaching language must preserve personhood, consent, refusal, and self-authorship. |
| Agent authorization | Delegation tokens, capability fences, scopes, expiry, and revocation implement instrumental agency boundaries. |
| Contestability | Affected humans need challenge, review, override, and suspension paths for AI-mediated decisions. |
| Trace-to-update governance | Operational traces cannot become durable learning artifacts without consent, deletion, and authority boundaries. |
| EU AI Act / NIST AI RMF coverage | Human oversight, roles, responsibility, monitoring, and intervention map to Human Command tests. |

## Source Candidates

The issue intake for #162 cited these source candidates for later hardening:

- NIST AI RMF 1.0
- EU AI Act Article 14
- Autonomy by Design
- AI agency/autonomy/moral patiency research
- Agentic AI under EU law
- Agency/autonomy design-space research for regulated contexts
- Digital Apprentice
- Accountability Horizon

They support this draft as research context, not as separately adopted canon.

