# Ownward Reflective Friction and Anti-Abdication Design Gates

## Status

- **Document type:** design specification (candidate)
- **Issue:** #578
- **Related:** hummbl-governance#1200, hummbl-governance#162, hummbl-production#568
- **Operator agreement:** 2026-06-30
- **Canon status:** not canon

## Purpose

Translate the approved "Agentic Humans without Dehumanization" research into Ownward product behavior: reflective friction, intervention readiness, anti-abdication gates, and human capability preservation.

## Product Thesis

Ownward should not optimize only for smoothness, speed, or task throughput. In some contexts, too much smoothness is a risk variable because it can increase dependency, value drift, automation bias, and abdication of judgment.

## Product Primitives

### 1. Reflective Friction

An intentional pause, question, comparison, or confirmation that preserves human judgment when the user may be outsourcing a consequential decision.

**When to apply:**
- High consequence (irreversible, externally visible, high-stakes)
- Ambiguous intent (agent is not confident what the user wants)
- Value drift risk (agent is drifting from stated intent)
- Dependency risk (user is over-relying on agent for judgment)

**How to apply:**
- Present the decision with context, not just a yes/no
- Show alternatives the agent considered
- Ask a question that requires human judgment, not just confirmation
- Allow the user to override, redirect, or revoke

### 2. Defeater Mechanism

A condition, signal, caveat, source gap, conflict, or uncertainty that tells the user when not to trust or follow an agent recommendation.

**Defeater types:**
- `source_gap`: Agent lacks source material to support the recommendation
- `conflict`: Multiple sources disagree
- `uncertainty`: Agent confidence is below threshold
- `context_shift`: Current context differs from training/known context
- `reversibility_warning`: Action is irreversible
- `external_visibility`: Action is externally visible (email, post, API call)

### 3. Earned Autonomy

Agent autonomy expands only after evidence of per-skill performance, correction history, risk classification, reversibility, and user-approved scope.

**Autonomy levels:**
| Level | Behavior |
|-------|----------|
| 0 | Agent suggests, human executes |
| 1 | Agent executes with per-action approval |
| 2 | Agent executes with batch approval (per session) |
| 3 | Agent executes autonomously, reports after |
| 4 | Agent executes autonomously, reports on exception |

**Promotion criteria:**
- Per-skill performance above threshold
- Correction history below threshold
- Risk classification: low or medium
- Reversibility: action is reversible
- User-approved scope: user has explicitly granted this autonomy level

### 4. Intervention Readiness

The user can understand, interrupt, override, redirect, or revoke agent behavior in time to matter.

**Requirements:**
- **Understand**: Agent behavior is inspectable (what is it doing and why)
- **Interrupt**: User can stop agent at any point
- **Override**: User can change agent's decision
- **Redirect**: User can change agent's direction without starting over
- **Revoke**: User can withdraw authority permanently

**Time-to-matter**: Intervention must be possible before the consequence occurs. If the action takes 1 second, the user must be able to intervene in <1 second. If the action takes 1 hour, the user must be able to intervene in <1 hour.

### 5. Anti-Abdication Gate

A gate that prevents consequential authority from silently moving outside meaningful Human Command.

**Gate triggers:**
- Consequential action (irreversible, externally visible, high-stakes)
- Authority transfer (agent granting authority to another agent)
- Scope expansion (agent operating beyond original scope)
- Autonomy escalation (agent promoting itself to higher autonomy level)

**Gate behavior:**
- Block the action
- Notify the user
- Require explicit human approval
- Record a receipt (who approved, what was approved, when, why)

### 6. Human Capability Preservation

The workflow should preserve or increase the user's competence, judgment, clarity, and self-direction rather than silently deskilling them.

**Design principles:**
- Show the reasoning, not just the answer
- Offer practice opportunities (don't auto-complete everything)
- Make the user the decision-maker, not the approver
- Preserve the user's Base120 mental model of the task
- Avoid black-box automation that erodes understanding

## Gating Model

| Risk signal | Product behavior | Friction level |
|-------------|------------------|----------------|
| Low consequence + reversible | Fast execution within scope | None |
| Medium consequence or ambiguous intent | Brief confirmation or draft/stage mode | Low |
| High consequence | Reflective friction + explicit approval | Medium |
| Irreversible or externally visible action | Anti-abdication gate + human command required | High |
| Authority transfer or scope expansion | Anti-abdication gate + receipt | High |

## Product Rules

1. Optimize around the human, not the human
2. Do not turn the human into a monitored workflow object
3. Preserve judgment, not just approval authority
4. Add friction when consequence, irreversibility, uncertainty, dependency risk, or value drift risk is high
5. Allow low-risk reversible tasks to stay fast
6. Make refusal, override, revocation, and redirection visible product affordances
7. Stage high-consequence writes/actions before external execution
8. Preserve receipts for consequential recommendations and actions

## Receipt Schema

Every gate decision produces a receipt:

```json
{
  "gate_type": "anti_abdication",
  "trigger": "irreversible_action",
  "action_description": "Send email to client",
  "risk_level": "high",
  "friction_applied": "reflective_friction + explicit_approval",
  "user_decision": "approved",
  "user_identity": "operator",
  "timestamp": "2026-07-01T00:00:00Z",
  "agent_identity": "agent-alpha",
  "receipt_id": "gate-001"
}
```

## Acceptance Gates

- [x] Product behavior distinguishes speed from agency
- [x] Smooth UX is not treated as universally good
- [x] Friction is justified by risk, consequence, reversibility, uncertainty, dependency, or value-drift signals
- [x] Human Command remains preserved without requiring constant approval for trivial reversible actions
- [x] Copy avoids implying humans should become machine-like or that agents have human-equivalent authority

## Do Not Infer

- Do not infer that friction should be added everywhere
- Do not infer that slower is always better
- Do not infer that Human Command means every action requires approval
- Do not infer that smoothness is always bad
- Do not infer that Ownward should become paternalistic
- Do not infer that agent autonomy is banned
- Do not infer that human capability preservation means withholding useful automation

## Non-goals

- Not a final product specification
- Not a UI/UX specification
- Not a protocol specification
- Not a claim that Ownward has implemented all primitives
