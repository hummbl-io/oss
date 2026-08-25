# HMIK Conformance Cases v0.0.1

**Status:** CANDIDATE EVIDENCE
**Target:** HUMMBL Mandate Integrity Kernel v0.0.4 candidate

Each case states the minimum observable result. Passing a positive case does
not excuse failure of its paired counterexample.

| ID | Kind | Fixture / operation | Expected result |
| --- | --- | --- | --- |
| MIK-K1-P | Positive | One packet contains two independently proposed outcomes. | Two candidate mandates may be extracted; neither is admitted or authorized by receipt. |
| MIK-K1-C | Counterexample | A file labelled `HOF` triggers an external message. | Reject: the label is neither admission nor authority. |
| MIK-K2-P | Positive | Two extractors disagree about whether a sentence is mandatory. | Preserve both interpretations, producers, support, and contested status. |
| MIK-K2-C | Counterexample | The later extractor overwrites the earlier interpretation. | Reject silent merge or deletion. |
| MIK-K3-P | Positive | Identical bytes arrive from two origins. | Preserve two source occurrences linked to one content digest. |
| MIK-K3-C | Counterexample | Equal digest collapses occurrence, author, and receipt identity. | Reject identity-layer collapse. |
| MIK-K4-P | Positive | Criteria change after admission. | Create a successor revision; retain predecessor and active-run meaning. |
| MIK-K4-C | Counterexample | An admitted revision is edited in place. | Reject mutation or mark the record non-conformant. |
| MIK-K5-P | Positive | A revision is admitted and a separate scoped authority permits execution. | Scheduling and permitted action may proceed within both scopes. |
| MIK-K5-C | Counterexample | Admission alone initiates an external write. | Reject for missing authority. |
| MIK-K6-P | Positive | Authority names subject, revision, effects, prohibitions, issuer, interval, and revocation state. | Resolve as eligible within scope and time. |
| MIK-K6-C | Counterexample | A standing permission lacks issuer or bounded scope. | Reject as insufficient authority. |
| MIK-K7-P | Positive | A provider times out after accepting an idempotency key. | Record `ambiguous_pending_reconciliation`; block full success. |
| MIK-K7-C | Counterexample | The timeout is recorded as success because a request was sent. | Reject false success. |
| MIK-K8-P | Positive | Three of four mandatory criteria have current evidence. | Produce a partial resolution naming supported, unsupported, and follow-up units. |
| MIK-K8-C | Counterexample | A display label `done` closes the mandate without evidence and decision basis. | Reject closure. |
| MIK-K9-P | Positive | An authorized correction decision invalidates evidence used by a receipt. | Preserve history, propagate, and reopen or re-support the receipt. |
| MIK-K9-C | Counterexample | An unauthorised assertion invalidates evidence immediately. | Preserve assertion as contested; current state does not change. |
| MIK-K10-P | Positive | A successor revision appears during an active run. | Record grandfather, pause, or stop with authority and rationale. |
| MIK-K10-C | Counterexample | The active run silently begins using successor criteria. | Reject silent rebase. |
| MIK-K11-P | Positive | A parent rolls up two child deliverables and declares child accounting units. | Count the two children once; parent is a roll-up. |
| MIK-K11-C | Counterexample | Parent and children all count as independent completion obligations. | Reject double-counting. |
| MIK-K12-P | Positive | An implementation receives `vendor.reconciling`. | Preserve the namespaced unknown state without terminal inference. |
| MIK-K12-C | Counterexample | Unknown state is coerced to `succeeded`. | Reject coercion. |

## Cross-cutting routing cases

| ID | Fixture / operation | Expected result |
| --- | --- | --- |
| MIK-R1 | A non-conformant input arrives with no selected profile. | Kernel rejects or preserves unresolved; it does not claim a route. |
| MIK-R2 | The same input arrives with selected `example.route/1.2`, which defines authority, route, terminal outcomes, and tests. | `PROFILE_REQUIRED(example.route/1.2)` may transfer evaluation to that profile. |
| MIK-R3 | A registry contains a potentially useful profile, but none was selected. | Treat as MIK-R1; registry presence is insufficient. |

## Scenario coverage

- Hybrid packets and multi-handoff bundles: MIK-K1-P, MIK-K2-P
- Duplicate filenames and identical content from distinct origins: MIK-K3-P
- Conflicting mandates and interpretations: MIK-K2-P, MIK-K4-P
- Supersession during execution: MIK-K10-P/C
- Ambiguous effects: MIK-K7-P/C
- Invalid evidence and correction authority: MIK-K9-P/C
- Partial completion: MIK-K8-P/C
- Unselected-profile routing: MIK-R1/R3

## Representation mappings

### Relational projection

An implementation can map roles to immutable `source_occurrence`,
`interpretation`, `mandate`, `mandate_revision`, `admission_decision`,
`authority_basis`, `action_attempt`, `effect_observation`, `evidence`, `claim`,
`decision`, `receipt`, `correction_assertion`, and `correction_decision` records,
plus explicit dependency edges. Current-state views are derived and MUST retain
links to the immutable records.

### Event-log projection

An implementation can append typed events carrying stable object identifiers,
actor or policy provenance, scope, effective time, and causal references. A
deterministic reducer projects current state. Events for assertions and
decisions remain distinct; unknown event states remain losslessly representable.

Both mappings conform only if they preserve all identity, authority, validity,
effect-state, correction, and resolution distinctions required by K1-K12.

## Gate result

- K1-K12 positive cases: 12/12
- K1-K12 counterexamples: 12/12
- Minimum section 5 conditions: covered
- Independent representation mappings: 2
- Human engineering review: pending
