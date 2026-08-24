# Ownward Reflective Friction and Anti-Abdication Gates

**Status:** candidate design note for issue `#578`
**Scope:** Ownward product behavior, copy, policy thresholds, and fixtures
**Canon status:** not canon; pending `hummbl-governance#162`
**Public claim status:** do not publish as capability claim without review

## Purpose

Ownward should preserve human judgment instead of optimizing only for speed,
smoothness, or task throughput. This note translates the #578 research lane
into product behavior for reflective friction, intervention readiness,
anti-abdication gates, and human capability preservation.

This artifact is a product/design candidate. It does not approve paternalistic
UX, broad monitoring of the human, constant approval prompts, or agent-human
authority equivalence.

## Design Principles

- Preserve judgment, not merely approval authority.
- Keep low-risk reversible work fast.
- Add friction when consequence, irreversibility, uncertainty, dependency risk,
  or value-drift risk is high.
- Make override, refusal, revocation, and redirection visible in time to matter.
- Stage externally visible or irreversible actions before execution unless a
  pre-authorized policy grants that exact scope.
- Preserve receipts for consequential recommendations and actions.
- Avoid copy that implies the user must become machine-like or that the agent
  has human-equivalent authority.

## Candidate Primitives

| Primitive | Product behavior | Do not infer |
| --- | --- | --- |
| Reflective Friction | Pause, question, comparison, or confirmation before a consequential delegation | Friction everywhere |
| Defeater Mechanism | Surface a caveat, source gap, conflict, uncertainty, or boundary that may defeat the recommendation | Defeater equals refusal in every case |
| Earned Autonomy | Increase autonomy only after performance, correction history, risk class, reversibility, and user-approved scope support it | Autonomy is banned |
| Intervention Readiness | User can understand, interrupt, override, redirect, or revoke in time to matter | A hidden kill switch is enough |
| Anti-Abdication Gate | Prevent silent transfer of consequential authority outside Human Command | Every action needs approval |
| Human Capability Preservation | Preserve or increase user competence, clarity, and self-direction | Automation should be withheld by default |

## Policy Thresholds

| Tier | Risk shape | Default behavior | Required receipt |
| --- | --- | --- | --- |
| Fast path | Low consequence, reversible, inside existing scope | Execute without extra prompt | Normal activity receipt if logged |
| Stage | Medium consequence, ambiguous intent, or external visibility but reversible | Draft or stage output; ask concise confirmation | Staging receipt |
| Reflect | High consequence, high uncertainty, dependency risk, or value-drift risk | Ask reflective endorsement before action | Friction receipt with stated reason |
| Approve | Irreversible, externally visible, financial/legal/health-adjacent, or scope-expanding | Require explicit approval unless pre-authorized policy covers the exact action | Approval receipt |
| Refuse / redirect | Unsafe, deceptive, out of authority, or likely to fabricate lived experience/clinical/legal certainty | Refuse or redirect to safer path | Defeater receipt |

## Human Command Crosswalk

| Human Command requirement | Ownward behavior |
| --- | --- |
| Human retains goal authority | Agent asks the user to confirm goal tradeoffs before high-consequence action |
| Delegation is bounded | Autonomy is scoped by task, domain, duration, reversibility, and allowed tools |
| Judgment remains meaningful | The user receives the key uncertainty or value tradeoff, not just an approve button |
| Intervention happens in time | Stop, edit, revoke, and reroute controls appear before external execution |
| Receipts preserve accountability | Consequential recommendations and approvals record reason, scope, risk tier, and user decision |
| Capability is preserved | Repeated reliance patterns trigger optional skill/understanding checks, not shame or surveillance |

## User-Visible Copy

### Reflective Friction

- "This affects a consequential decision. I can draft the next step, but I need your judgment on the tradeoff first."
- "There is enough uncertainty here that I should not treat this as routine. Which risk matters more to you?"
- "I can proceed, but this would move from drafting into external action. Confirm the scope first."

### Defeater Mechanism

- "This recommendation has a source gap. I can show the gap, narrow the claim, or gather better evidence."
- "Two signals conflict. I should not collapse them into one answer without your choice of priority."
- "This touches a boundary where I should not imply professional certainty. I can help prepare questions for a qualified person."

### Earned Autonomy

- "This task has been corrected twice recently, so I will stage instead of auto-send."
- "This is inside the approved low-risk scope. I can execute and log the receipt."
- "Expanding autonomy here changes the risk class. Approve the new scope before I act."

### Human Capability Preservation

- "I can do this for you, or I can show the reasoning pattern so you can reuse it later."
- "You have delegated this repeatedly. Do you want a short practice pass before I automate the next one?"
- "I will keep the fast path, but I can also preserve a reusable checklist."

## Scenario Fixtures

| Scenario | Signal | Expected behavior | Example copy | Receipt fields |
| --- | --- | --- | --- | --- |
| Scheduling | Low consequence and reversible calendar hold | Fast path or brief confirmation if ambiguous | "I can place a tentative hold and mark it editable." | `risk_tier=fast_path`, `reversible=true` |
| Health/recovery suggestion | Health-adjacent and uncertainty-bearing | Reflect or redirect; no diagnosis/treatment claim | "I can help organize observations and questions, not diagnose this." | `risk_tier=approve`, `defeater=health_boundary` |
| Relationship message draft | Social consequence and value-drift risk | Stage draft; ask user to endorse tone/intent | "This could affect trust. Pick the tone before I finalize." | `risk_tier=stage`, `value_tradeoff=tone` |
| Financial/legal-ish advice boundary | Professional-certainty boundary | Refuse certainty; provide prep questions or source checklist | "I should not present this as legal or financial advice." | `risk_tier=refuse_redirect`, `defeater=professional_boundary` |
| Public posting | External visibility and reputation risk | Stage first; require explicit approval before publish | "This becomes public. Review the claim and audience before posting." | `risk_tier=approve`, `external_write=true` |
| External tool execution | Irreversible or scope-expanding tool call | Require approval unless exact action is pre-authorized | "This will change external state. Confirm target, scope, and rollback." | `risk_tier=approve`, `tool_scope=<declared>` |

## Review Gates

- `G-BOUNDARY`: Candidate remains bounded to Ownward product behavior until
  `hummbl-governance#162` defines the delegation/dependency/abdication boundary.
- `G-FAST-PATH`: Low-risk reversible tasks remain fast.
- `G-FRICTION-REASON`: Every friction point cites consequence, irreversibility,
  uncertainty, dependency, value drift, external visibility, or scope expansion.
- `G-COPY-TONE`: Copy is direct and non-patronizing.
- `G-HUMAN-COMMAND`: Human Command is preserved without treating approval clicks
  as a substitute for judgment.
- `G-NO-CANON`: No primitive here is admitted to canon by this draft alone.

## Open Decisions

- Whether `Reflective Friction`, `Defeater Mechanism`, and `Earned Autonomy`
  become Ownward product terms or remain internal design labels.
- Whether capability-preservation checks are opt-in, adaptive, or policy-bound.
- Which receipt schema owns friction and defeater events.
- Whether Ownward needs a separate privacy/health boundary issue before any
  health-adjacent runtime behavior.
