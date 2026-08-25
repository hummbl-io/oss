# Deterministic Agent Runtime And Event Ledger Crosswalk

Status: advisory spike
Date: 2026-07-03
Scope: `hummbl-io/hummbl-governance#158`
Parent context: `hummbl-io/hummbl-governance#1190`

This document maps deterministic runtime, intention/event-ledger, recovery, and
future MCP resource-bound access concepts into advisory HUMMBL governance
schemas and fixtures. It does not approve production implementation, MCP server
changes, CI enforcement, public claims, durable canon, release, deployment,
merge, or repo setting changes.

## Source Leads To HUMMBL Crosswalk

| Source lead | Governance interpretation | Advisory output |
|---|---|---|
| LLM-as-Code / Agentic Programming | Program/workflow owns control flow; model output stays bounded to classification, extraction, summary, proposal, or ranking. | `deterministic_runtime_decision_boundary.schema.json` |
| ESAA / Event Sourcing for Autonomous Agents | Agent intention must be separate from deterministic state mutation, projection hash, replay status, and compensation record. | `event_ledger_entry.schema.json` |
| Self-Healing Agentic Orchestrators | Recovery must be constrained by detector, allowed recovery, forbidden recovery, budget, verifier, side-effect mode, escalation, and receipt. | `recovery_policy.schema.json` |
| MCP Authorization specification | Future MCP access should be resource-bound and operation-scoped before server behavior changes. | `mcp_resource_access_policy.schema.json` |

## Deterministic Runtime Boundary

Forbidden model authority is explicit:

- loop control;
- termination;
- approval override;
- irreversible side-effect approval.

Allowed model outputs are advisory and bounded:

- classification;
- extraction;
- summary;
- proposal;
- ranking.

The control owner must be `program`, `workflow`, or `human_operator`; never a
model. High-consequence operations still require human approval gates.

## Event Ledger Boundary

An event-ledger entry records:

- actor;
- proposed effect;
- validation result;
- approval state;
- applied effect;
- projection hashes;
- replay status;
- compensation reference;
- receipt reference.

The intent is to preserve a replayable distinction between what the agent
proposed and what deterministic governance actually applied.

## Recovery Policy Boundary

Recovery is permitted only inside a declared budget and side-effect mode.
Retries, verifier bypass, and automated repair become unsafe when they can
mutate external state without review.

The advisory recovery classes are:

- timeout;
- schema violation;
- tool failure;
- state divergence;
- policy denial;
- unsafe output.

## Future MCP Conformance Policy

This pass proposes policy-only fixtures for resource-bound MCP access. It does
not change MCP server code.

An MCP policy record must declare:

- server ID;
- resource selector;
- allowed operations;
- denied operations;
- credential scope;
- operations requiring approval;
- audit receipt.

## Verified Facts

- `hummbl-governance#158` authorizes schemas, fixtures, tests, docs,
  crosswalks, and receipts in draft PR spike mode.
- The same issue keeps production/security changes, connector expansion, CI/CD
  mutation, public claims, canonization, release, deployment, merge, and repo
  settings out of scope.
- This PR adds only advisory docs, schemas, fixtures, and fixture validation
  tests.

## Hypotheses

- A small advisory schema set can expose deterministic-runtime design gaps
  before any runtime or server implementation.
- Separating intention from applied effect will make replay and compensation
  review easier for future runtime work.
- MCP resource-bound policy fixtures can reduce future over-broad server grants
  if reviewed before implementation.

## Fixtures Added

`tests/fixtures/runtime_event_ledger/runtime_event_ledger_fixtures.json`
contains one valid and one adversarial case for each proposed schema:

- deterministic runtime decision boundary;
- event ledger entry;
- recovery policy;
- MCP resource access policy.

## Residual Risk

- The schemas are advisory and intentionally minimal; they are not a complete
  runtime contract.
- The fixtures are synthetic and do not prove production behavior.
- Warning-mode or strict-mode validator behavior from adjacent repos is not
  imported here.
- Any runtime, MCP, CI, connector, or production enforcement remains behind a
  separate human gate.

## Lane Result

```yaml
lane_result:
  issue: hummbl-io/hummbl-governance#158
  draft_prs:
    - this PR
  what_changed:
    - advisory deterministic runtime decision-boundary schema
    - advisory event-ledger entry schema
    - advisory recovery-policy schema
    - advisory MCP resource-access policy schema
    - paired valid/adversarial fixture bundle
    - fixture validation tests
  verified_facts:
    - issue authorizes draft PR spike outputs only
    - issue excludes production, CI, public-claim, canon, release, deployment, merge, and repo-setting changes
  hypotheses:
    - schemas can de-risk future runtime work before implementation
    - event-ledger separation can improve replay and compensation review
  fixtures_added:
    - tests/fixtures/runtime_event_ledger/runtime_event_ledger_fixtures.json
  tests_run:
    - python -m pytest tests/test_runtime_event_ledger_crosswalk.py -q
    - python -m json.tool over advisory schema and fixture JSON
    - git diff --check
    - narrow credential-pattern scan over diff
  residual_risk:
    - advisory schemas are not runtime enforcement
    - synthetic fixtures are not connector or production evidence
  recommended_next_gate:
    - non-author review before any implementation, MCP server, CI, or canon promotion
```

## Next Gate

Review this advisory spike against `hummbl-governance#158`. Any production
runtime change, MCP server change, CI behavior change, public claim, canon
promotion, release, deployment, merge, or repo setting change requires a
separate human-approved PR.
