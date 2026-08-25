# Cross-Repo Contract Migration and Deprecation Protocol v0.1

Status: **candidate — non-canonical — no automatic migration authority**

## Purpose

Define how a producer proposes, tests, publishes, migrates, deprecates, replaces, and retires a cross-repo contract while preserving consumer autonomy, rollback, and auditability.

## Change classes

### Compatible change

A change is compatible only when every declared required consumer can continue to process the contract and payload under its recorded support declaration without semantic reinterpretation.

Examples may include:

- clarifying descriptions without changing field meaning;
- adding optional documentation references;
- adding a fixture that does not change acceptance behavior;
- expanding a bounded patch-compatible contract implementation.

Compatibility must be demonstrated, not inferred solely from a small textual diff.

### Breaking contract change

A contract change is breaking when it changes cross-boundary obligations, including:

- required producer or consumer fields;
- identifier ownership or locator grammar;
- accepted contract-version semantics;
- privacy or visibility posture;
- receipt event requirements;
- assurance-reference meaning;
- acceptance/rejection behavior;
- lifecycle or replacement semantics.

Breaking contract changes require a new major `contract_version` or a new `contract_id`, plus migration guidance and consumer reacceptance.

### Breaking payload change

The producing repository decides whether a payload change is breaking under its own schema policy. The cross-repo layer records the resulting payload version and consumer support; it does not override the producer's domain decision.

A consumer must reject or conditionally accept a payload version it cannot safely process.

## Required migration packet

A migration packet should contain:

```yaml
migration_id:
from_contract:
  contract_id:
  contract_version:
to_contract:
  contract_id:
  contract_version:
producer:
  repo:
change_class:
reason:
affected_payload_versions: []
affected_consumers: []
field_or_semantic_changes: []
privacy_or_authority_changes: []
required_consumer_actions: []
validation:
  valid_fixtures: []
  invalid_fixtures: []
  adversarial_fixtures: []
rollback:
  supported:
  procedure_ref:
  deadline_or_boundary:
receipts:
  producer_publish_ref:
  consumer_decision_refs: []
lifecycle:
  proposed_at:
  effective_at:
  old_contract_deprecated_at:
  old_contract_retired_at:
```

Exact field names remain candidate until a migration schema is approved.

## Migration sequence

1. **Inventory consumers**
   - Identify required, optional, and advisory consumers.
   - Identify undeclared consumers where observable.
   - Do not assume the known consumer list is complete.

2. **Classify the change**
   - compatible contract change;
   - breaking contract change;
   - payload-only change;
   - authority/privacy change;
   - locator or namespace rebinding.

3. **Publish candidate materials**
   - candidate replacement contract;
   - migration note;
   - exact old/new version references;
   - valid, invalid, and adversarial fixtures;
   - rollback procedure;
   - disclosure and authority review.

4. **Validate in parallel**
   - Keep the old contract operable during the test window when practical.
   - Run compatibility checks for each required consumer.
   - Record failures and conditional acceptance rather than hiding them.

5. **Collect consumer decisions**
   - `accepted`;
   - `conditional` with explicit conditions;
   - `rejected` with reason.

6. **Set effective and deprecation dates**
   - A replacement must not become effective merely because it validates locally.
   - Required-consumer rejection blocks unqualified activation unless an explicit operator-approved exception is recorded.

7. **Observe and rollback**
   - Monitor declared compatibility and data-quality signals.
   - If rollback conditions trigger, restore the prior supported route or quarantine the new route.
   - Record the rollback execution separately from any conclusion about correctness.

8. **Retire**
   - Retire only after audit and support boundaries are satisfied.
   - Preserve lineage and receipts.
   - Do not reuse retired identifiers for unrelated semantics.

## Consumer decision semantics

### Accepted

The consumer declares that the exact contract and payload versions are supported under the recorded conditions and validation evidence.

Acceptance does not prove the payload is truthful or safe in every context.

### Conditional

The consumer can process the versions only under explicit limitations. Conditions must be machine- or human-checkable and must not be omitted from downstream routing.

### Rejected

The consumer cannot safely or correctly process the declared versions. A rejection must include a reason and should identify a supported alternative where known.

Silently ignoring an unsupported version is not acceptance.

## Deprecation rules

A deprecated contract must declare:

- `deprecated_at`;
- `replacement_contract_ref`;
- migration reference;
- affected consumers;
- continued support boundary;
- known unresolved compatibility failures.

Deprecation means “do not begin new reliance without review.” It does not mean deletion, invalidity, revocation of historical receipts, or automatic migration.

## Retirement rules

A contract may be retired when:

- the replacement route is effective or the capability is intentionally discontinued;
- required consumers have migrated, rejected, or received an approved exception;
- rollback and audit retention requirements are met;
- unresolved dependencies are disclosed;
- the retirement decision has an authority and receipt trail.

A retired contract remains part of historical lineage.

## Emergency changes

Emergency remediation may shorten normal review only when a declared security, privacy, integrity, legal, or operational condition requires it.

Emergency changes require:

- the triggering condition;
- authorized decision-maker;
- exact bounded scope;
- temporary compatibility posture;
- rollback or containment route;
- follow-up review deadline;
- execution and decision receipts.

Emergency execution does not grant permanent authority or automatically validate the replacement design.

## Adversarial cases

Migration validation must cover at least:

- producer labels a breaking change as compatible;
- required consumer omitted from the migration manifest;
- consumer accepts an unsupported payload version;
- replacement leaks a private reference into a public contract;
- old and new identifiers collide;
- mutable `main` reference changes after acceptance;
- rollback target is unavailable;
- deprecation occurs without a replacement or discontinuation rationale;
- execution receipt is presented as migration verification;
- migration silently changes canon or authority posture.

## Non-goals

- automatic migration across repositories;
- forced consumer acceptance;
- deletion of historical artifacts;
- changing domain payload schemas from the governance repository;
- treating migration completion as proof of factual correctness;
- bypassing operator authority for production, publication, canon, or security-sensitive changes.
