# HUMMBL Bus Phase −1, 0, and 1 Program

Status: PROPOSED

Sponsor and final decision authority: Reuben Bowlby

Canonical planning repository: `hummbl-dev-org/hummbl-bus`

Production reference implementation: hummbl-governance bus, retained until settlement

## Outcome

Produce an implementation-ready, evidence-backed plan for promoting
`hummbl-bus` from an incomplete extraction into the canonical coordination-bus
package without changing the production writer, bridge, bus history, or queue
state during these planning phases.

Completion means the operator can answer, from versioned evidence, what belongs
in the portable package, what stays in adapters, which compatibility promises
apply, which tests admit a release, how a one-writer canary works, and exactly
how to roll back. Activity, commits, and document count are not completion.

## Authority and boundaries

- The operator approves releases, production cutover, credential changes, and
  retirement of hummbl-governance surfaces.
- This program may research, model, test locally, and publish planning PRs.
- Phases −1 through 1 do not switch the canonical writer, deploy a bridge,
  replay queues, rotate secrets, restart services, or archive hummbl-governance.
- The current hummbl-governance implementation is a temporary behavioral reference,
  not automatically the desired neutral product contract.
- Historical TSV rows and queue evidence are immutable inputs.

## Reconciled starting state

- Standalone `hummbl-bus` declares package version `0.1.0`, has no Git tags or
  GitHub releases, and passes 33 tests.
- Its `AGENTS.md`, README, and May drift report all say extraction is incomplete.
- hummbl-governance has 31 bus Python modules versus 13 standalone modules. Every
  same-name implementation differs.
- The durable five-column TSV layout and HMAC canonical string remain compatible.
- The structured-event discriminator differs:
  `hummbl_bus.event.v1` versus `hummbl_governance.bus.event.v1`.
- The standalone bridge lacks production replay, spool, privileged-proof,
  freshness, provenance, and several path/security controls while documentation
  already describes some of those behaviors.
- The standalone bridge exposes reads without authentication and permits a
  shared bearer to assert arbitrary sender identity.
- The founder security-focused sample produced 79 passes and 10 failures; the
  failures reflect stale provenance expectations after automatic host rewriting.
- Delta still imports its signed writer from hummbl-governance. The old writer remains
  available while the standalone candidate is developed and shadow-tested.

## Phase −1 — Evidence and version freeze

Purpose: make the problem finite before designing the solution.

Deliverables:

1. Pin standalone HEAD, founder reference commit, and dirty-overlay fingerprint.
2. Enumerate every module, public symbol, direct import, CLI, environment
   variable, endpoint, schema marker, message type, queue, and deployment consumer.
3. Classify ownership as portable core, optional extension, founder adapter,
   operational wrapper, historical evidence, or retirement candidate.
4. Freeze a golden corpus of historical rows and requests without secret values.
5. Record current package, wire, schema, bridge API, deployment, and config versions.
6. Reconcile open PRs, bus receipts, old PRDs, drift reports, and live topology.
7. Define unresolved decisions and name the operator as their authority.

Exit gate P−1: the inventory is complete, hashes are reproducible, unknown
dependencies are explicit, and no claim relies on an unpinned dirty tree.

## Phase 0 — Contract and compatibility design

Purpose: define what the portable bus must mean before porting code.

Deliverables:

1. A versioned wire/security contract for the five-column TSV, HMAC envelope,
   structured events, timestamps, IDs, provenance, and error taxonomy.
2. A compatibility matrix covering readers, writers, bridge clients/servers,
   schemas, configuration, Python versions, Windows, and POSIX.
3. First-principles and derived-policy packet with operational whether-tests.
4. Threat model covering write and read paths, bearer identity, replay,
   privilege, SSRF/path injection, concurrency, crash durability, and logging.
5. Explicit public API and neutral package boundary.
6. Deprecation and dual-read policy for legacy schema IDs and direct imports.
7. Version negotiation rules that default to incompatible unless compatibility
   is explicitly tested and declared.

Exit gate P0: every normative `shall` has a source, test method, stakeholder
purpose, compatibility class, and decision owner. Contradictory documentation is
marked, not treated as implemented behavior.

## Phase 1 — Implementation-ready architecture

Purpose: turn the contract into independently reviewable work packages.

Deliverables:

1. Semantic port map for writer core/signing/CLI, bridge, replay ledger, spool,
   replay worker, seed import, verifier, security, TSV, manager, and MCP surfaces.
2. Founder adapter plan preserving the 15-name facade and legacy module/CLI paths.
3. Differential golden-vector harness shared by both repositories.
4. Cross-platform concurrency, crash, replay, freshness, authorization, and
   fault-injection test plan.
5. Single-writer/dual-reader shadow architecture with attributable telemetry.
6. Deployment manifest for Delta, Anvil, VPS, and applicable fleet consumers.
7. Rollback procedure that restores the previous writer without rewriting TSV
   history or replaying old queue entries.
8. Sized implementation backlog with dependencies, evidence, stop conditions,
   and separate PR boundaries.

Exit gate P1: every implementation tranche is independently reversible, testable,
and reviewable; the production cutover remains a later operator-authorized phase.

## Workstreams and ownership

| Workstream | Deliverable | Dependency | Done evidence |
|---|---|---|---|
| Semantic drift | Module/API/behavior map | pinned snapshots | reviewed inventory and differential fixtures |
| Protocol/security | normative contract and threat model | drift map | whether-tests and negative tests |
| Versioning | multi-axis compatibility registry | protocol contract | machine-readable version matrix |
| Packaging | neutral core and optional extras plan | ownership decisions | clean wheel/sdist plan |
| Deployment | consumer and topology map | version matrix | signed manifest and rollback |
| Validation | golden, concurrency, fault, restart tests | all contracts | gate report per release candidate |
| Governance | decisions, exceptions, receipts | operator review | signed approval bound to exact refs |

## Program status semantics

Allowed states are not started, active, blocked, in review, completed with
evidence, superseded, and canceled. A lane is completed only when its exit
evidence exists and its dependencies agree. Dates are planning targets unless
the operator separately declares a commitment.

## Stop conditions

Stop the current tranche on any schema ambiguity affecting historical rows,
identity impersonation path, privileged-message bypass, duplicate canonical
append, unsigned privileged acceptance, queue replay without live authority,
cross-platform corruption, secret exposure, or inability to restore the old
writer. Record the failed gate rather than weakening it.
