# Human Control Glossary

Status: draft

This glossary defines control and oversight terms used in `hummbl-tuples` so experimental regimes stay precise.

## Core Distinction

The most important distinction is not only whether a human is present. It is where the human sits relative to the reasoning and execution loop.

## HITL

`HITL` = `Human In The Loop`

Definition:

- The human directly participates inside the active decision loop.
- The system pauses, branches, or waits for human input before it can continue on certain decisions.

Typical HUMMBL uses:

- selecting a transformation
- approving a mental model
- confirming a ranked reasoning path
- overriding an AI-selected path before execution continues

Operational meaning:

- the human is a runtime decision participant, not just a reviewer

## HOTL

`HOTL` = `Human On The Loop`

Definition:

- The human supervises an active AI loop from outside the immediate step-by-step decision path.
- The AI can continue autonomously unless the human intervenes, vetoes, or stops it.

Typical HUMMBL uses:

- monitoring an autonomous run
- reviewing reasoning-path telemetry while the system continues
- interrupting only when drift, risk, or policy violations appear

Operational meaning:

- the human is a supervisor with interrupt authority, not a required participant for every decision

## HOOTL

`HOOTL` = `Human Out Of The Loop`

Definition:

- The system runs without human participation during the active decision and execution loop.
- Humans may have defined policy beforehand or may review results afterward, but they do not participate during runtime.

Typical HUMMBL uses:

- fully autonomous reasoning-path selection
- scheduled executions with no synchronous operator checkpoint

Operational meaning:

- no active runtime human control

## Human-Controlled

Definition:

- A stronger condition than generic HITL.
- The human selects the path logic directly rather than merely approving or vetoing AI proposals.

Typical HUMMBL meaning:

- human chooses transformation
- human chooses mental model
- AI executes within the chosen path

## Human-Influenced

Definition:

- The human shapes the available choice set or constraints, but the AI still performs the final selection within those boundaries.

Typical HUMMBL meaning:

- human whitelists transformations
- human bans specific models
- human sets confidence thresholds or policy constraints

## AI-Autonomous

Definition:

- The AI selects and executes the reasoning path without synchronous human participation.

Equivalent control location:

- usually HOOTL during runtime

## AI-Propose / Human-Confirm

Definition:

- The AI generates one or more candidate paths.
- A human selects or approves one before execution continues.

Equivalent control location:

- HITL

## Operator

Definition:

- The human or human-led role responsible for supervising, configuring, approving, interrupting, or auditing AI behavior in an operational setting.

Examples:

- founder
- analyst
- reviewer
- mission-control operator
- experiment owner

## Orchestrator

Definition:

- The entity that coordinates tasks, sequencing, constraints, and handoffs across models, agents, or humans.

Possible orchestrators:

- `nodezero`
- a human operator
- an AI coordinator
- a workflow runtime

Note:

- orchestrator does not imply final decision authority

## Coordinator

Definition:

- The entity that manages communication, alignment, and state synchronization across participants.

Difference from orchestrator:

- coordination is about alignment and messaging
- orchestration is about flow control and task structure

## Governor

Definition:

- The entity that sets or enforces allowed behavior, control regimes, or policy boundaries.

Typical HUMMBL meaning:

- `nodezero` as meta-governor
- policy service enforcing allowed control modes

## Supervisor

Definition:

- The entity watching a running system for quality, safety, or drift.

Typical control position:

- usually HOTL

## Reviewer

Definition:

- A human or AI that evaluates outputs or reasoning artifacts after a step or run completes.

Typical control position:

- post-hoc, unless given veto or approval authority

## Auditor

Definition:

- A human or system focused on evidence, lineage, policy compliance, and falsifiability.

Typical HUMMBL meaning:

- examines tuple records after or during execution to assess whether claims are supported

## Recommended HUMMBL Regime Terms

Use these labels for experiments and specs:

- `AI_AUTONOMOUS`
- `AI_PROPOSE_HUMAN_CONFIRM`
- `HITL_INFLUENCED`
- `HITL_CONTROLLED`
- `HOTL_SUPERVISED`

## Regime Mapping

- `AI_AUTONOMOUS`: AI selects and executes; human is out of the loop during runtime
- `AI_PROPOSE_HUMAN_CONFIRM`: AI proposes; human is in the loop for path approval
- `HITL_INFLUENCED`: human sets constraints; AI still selects within them
- `HITL_CONTROLLED`: human selects the path directly
- `HOTL_SUPERVISED`: AI runs while human monitors and can intervene if needed

## Working Rule

Do not use `HITL` and `HOTL` interchangeably.

- `HITL` means human participation is part of the active runtime decision loop.
- `HOTL` means human supervision exists, but the loop can continue without stepwise human participation unless intervention is triggered.
