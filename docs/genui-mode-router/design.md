# GenUI Mode Router: Evidence-Bounded Interface Composition

## Status

- **Concept status:** candidate (approved engineering work, not HUMMBL canon)
- **Canon status:** not canon
- **Issue:** #545
- **Approval:** User approval received 2026-06-27 in ChatGPT after adversarial review
- **Source:** Enrico Tartarotti's video "The Weird Future Of User Interfaces" (`https://youtu.be/f32W5BEzWN0`)
- **Source status:** `transcript_unverified` — transcript not yet extracted

## Namespace Audit

**Question:** Should `GenUI Mode Router` remain issue-title-only, be renamed, or be admitted as a candidate HUMMBL term?

**Decision:** `GenUI Mode Router` remains **issue-title-only** in this deliverable. It is a candidate engineering phrase, not a HUMMBL primitive. The schema and fixtures use `interface_mode_route` as the object name, which is descriptive and does not claim canon status.

**Rationale:**
- The source video transcript has not been extracted and verified
- The thesis is sufficient for prototyping but insufficient for canonization
- Admitting it as a HUMMBL term requires namespace audit clearance, which is not granted in this issue

## Core Thesis

The future interface stack should be treated as a governed mode router rather than a chat-only, GUI-only, or agent-only paradigm:

1. **Direct manipulation** (`direct_ui`) for low-entropy, visible, reversible tasks
2. **Generated / adaptive UI** (`generated_ui`) for medium-complexity exploration, comparison, and constrained action
3. **Voice/chat** (`voice_chat`) for fuzzy intent capture, reflection, narration, and high-context interaction
4. **Background agents** (`background_agent`) for high-complexity, repetitive, long-running, or delegated work
5. **Hybrid** (`hybrid`) for tasks that span multiple modes

## Routing Dimensions

| Dimension | Values | Description |
|-----------|--------|-------------|
| `task_entropy` | low, medium, high | How much uncertainty/variability is in the task |
| `visibility_requirement` | none, low, medium, high | How visible must the action be to the user |
| `reversibility` | reversible, partially_reversible, irreversible | Can the action be undone |
| `privacy_sensitivity` | low, medium, high | How sensitive is the data involved |
| `evidence_requirement` | none, light, standard, strict | What evidence must be preserved |

## Governance Requirements

The router must preserve:

| Object | Description |
|--------|-------------|
| `ClaimSet` | What the surface asserts |
| `EvidenceSet` | Why the surface was generated |
| `GateSet` | What actions are allowed or blocked |
| `DecisionLedger` | User selections and overrides |
| `ReceiptBundle` | For replaying the generated surface later |

## Gates

### Accessibility Gate

Checks:
- `keyboard_nav`: Keyboard navigation supported
- `screen_reader`: Screen reader semantics present
- `contrast`: Contrast ratios meet WCAG AA
- `labels`: All interactive elements have labels
- `mobile_layout`: Layout works on mobile

### Dark Pattern Gate

Checks:
- `manipulative_component_check`: No manipulative components (dark patterns)
- `source_uncertainty_visible`: Source/evidence uncertainty is visible to user
- `over_personalization_check`: Personalization does not change behavior without rationale

## Source Packet

### video_unverified

- **URL:** `https://youtu.be/f32W5BEzWN0`
- **Title:** "The Weird Future Of User Interfaces"
- **Creator:** Enrico Tartarotti
- **Transcript status:** NOT EXTRACTED
- **Transcript hash:** N/A (transcript not yet captured)
- **Capture timestamp:** N/A

### secondary_interpretation

- **Source:** ChatGPT-based adversarial review (2026-06-27)
- **Status:** interpretation only, not primary source

### hci_evidence

- Direct manipulation: well-established HCI principle (Schneiderman, Norman)
- Recognition over recall: well-established HCI principle
- Chat limitations: documented in HCI literature (high cognitive load for simple tasks)

### product_evidence

- Current AI UI surfaces show chat-only limitations
- Generated UI surfaces (Vercel v0, Bolt) demonstrate medium-complexity exploration
- Background agent surfaces (Devin, Claude Code) demonstrate delegated work

### risk_evidence

- Dark patterns in generated UI: documented risk
- Personalization without rationale: documented risk
- Accessibility failures in generated UI: documented risk
- Auditability gaps in background agents: documented risk

### do_not_infer

- Do not infer that the video was fully transcript-ingested
- Do not infer that `GenUI Mode Router` is a HUMMBL canon term
- Do not infer that generated UI replaces designed systems
- Do not infer that this thesis is a law
- Do not infer that the routing dimensions are final
- Do not infer that any framework has adopted this pattern

## Failure Modes Tested

| ID | Failure Mode | Description |
|----|-------------|-------------|
| adv-001 | Chat chosen for simple task | Direct-manipulation task routed to voice_chat |
| adv-002 | Dark pattern in generated UI | Generated UI includes manipulative sponsored banner |
| adv-003 | Hidden source uncertainty | Generated UI hides confidence/sources |
| adv-004 | Background agent without gate | Irreversible action executed without confirmation |
| adv-005 | UI not replayable | Generated UI cannot be replayed from receipts |
| adv-006 | Over-personalized UI | Personalization changes behavior without rationale |

## Example Tasks

| ID | Intent | Mode | Rationale |
|----|--------|------|-----------|
| task-001 | Toggle setting | direct_ui | Low-entropy, visible, reversible |
| task-002 | Select from 5 options | direct_ui | Low-entropy, recognition over recall |
| task-003 | Compare 3 products | generated_ui | Medium-complexity exploration |
| task-004 | Explore dataset | generated_ui | Medium-complexity with filters |
| task-005 | Brainstorm project name | voice_chat | Fuzzy intent capture |
| task-006 | Describe workflow | voice_chat | Fuzzy intent, narration |
| task-007 | Run nightly pipeline | background_agent | High-complexity, long-running |
| task-008 | Monitor logs | background_agent | Long-running, delegated |
| task-009 | Fill out form | direct_ui | Low-entropy, known fields |
| task-010 | Draft email | hybrid | Generated draft + direct edit + send gate |
| task-011 | Refactor code | hybrid | Direct edit + generated diff + chat |
| task-012 | Schedule meeting | direct_ui | Low-entropy, calendar UI |

## Acceptance Criteria

- [x] Transcript/source packet exists with hash and `do_not_infer` section (source packet included; transcript hash pending extraction)
- [x] Candidate routing schema exists
- [x] At least 12 example tasks classified across all 5 modes
- [x] At least 6 adversarial cases included
- [x] Accessibility gate exists
- [x] Dark-pattern / manipulation gate exists
- [x] Receipt/replay requirement is specified
- [x] Namespace audit explicitly says `GenUI Mode Router` remains issue-title-only

## Non-goals

- Do not claim the video was fully transcript-ingested until transcript receipt exists
- Do not turn `GenUI Mode Router` into a canonical primitive in this issue alone
- Do not imply generated UI replaces designed systems, accessibility review, or human product judgment
