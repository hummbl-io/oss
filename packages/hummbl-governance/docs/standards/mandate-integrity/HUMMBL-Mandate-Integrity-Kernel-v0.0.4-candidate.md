# HUMMBL Mandate Integrity Kernel v0.0.4

**Status:** CANDIDATE
**Identity:** HUMMBL Mandate Integrity Kernel (HMIK)
**Decision basis:** ADR-010 and operator approval on 2026-08-14
**Predecessor evidence:** immutable TierShift Semantic Kernel v0.0.3
**Relationship to TierShift:** none; existing TierShift execution-intensity
architecture remains unchanged

## 1. Purpose and boundary

HMIK defines semantic invariants for systems that convert heterogeneous source
material into authorized, evidence-backed work and must remain auditable when
interpretations conflict, objectives change, effects are uncertain, or support
is corrected.

HMIK is intentionally an ontology. It is not a workflow, storage model,
authorization mechanism, routing engine, governance system, security boundary,
or alignment solution. `MUST`, `MUST NOT`, `SHOULD`, and `MAY` are normative
when capitalized.

## 2. Semantic roles

| Role | Meaning |
| --- | --- |
| source content | Observed bytes or captured content |
| source occurrence | One provenance-bearing observation of source content |
| interpretation | A fallible, attributable assertion about meaning or relation |
| mandate | Stable logical identity of a desired outcome across revisions |
| mandate revision | Immutable scope, constraints, criteria, and assumptions |
| admission decision | Decision making one exact revision schedulable |
| authority basis | Scoped permission for a subject to perform actions |
| action and effect | Attempted operation and observed or unresolved result |
| evidence | Provenance-bearing observation offered as support |
| claim | Proposition asserted to follow from evidence |
| decision | Authorized scoped acceptance, rejection, or routing of a claim |
| receipt | Conclusion record with claims, support, authority, and unresolved state |
| correction assertion | Proposed append-only invalidation, supersession, or replacement |
| correction decision | Authorized scoped decision making a correction effective |

Implementations MAY project multiple roles from one event log or record type,
but MUST preserve distinctions whenever collapsing them would change identity,
authority, validity, effect state, or resolution. They MUST publish a mapping
from their representation to these roles.

## 3. Kernel invariants

### K1. Source is not mandate

Source material MAY express zero, one, or many candidate requests. A filename,
folder, label, document class, heading, delivery, or presentation to an agent
MUST NOT by itself admit work or grant authority.

### K2. Interpretation is fallible and attributable

Classification, extraction, equivalence, dependency, conflict, decomposition,
and supersession are interpretations unless established by an authorized
decision. An interpretation MUST retain producer or policy basis, source
support, and epistemic status. Competing interpretations MUST NOT be silently
merged or deleted.

### K3. Identity layers remain separate

Content, source occurrence, interpretation, mandate, revision, action/effect,
evidence, and receipt equality MUST NOT be inferred from one another. Filename,
model, executable, host, product surface, transport, and relayer are not
sufficient evidence of object equality or authorship. Unresolvable provenance
MUST be recorded as unavailable, not as successful traceability.

### K4. Mandate identity is revisioned

A mandate revision MUST be immutable after admission. A material change creates
a new revision and preserves predecessor and supersession relationships. It
MUST NOT silently rebase an active run or retroactively change prior meaning.

### K5. Admission is not authority

Admission makes one exact revision schedulable; it does not permit execution.
Authority permits a subject to perform scoped actions; it does not schedule an
objective. Neither source classification nor admission alone authorizes an
external effect.

### K6. Authority is scoped and attributable

An authority basis MUST resolve to subject, target revision or bounded standing
scope, permitted effects and prohibitions, issuer or policy authority, effective
interval, and current revocation status.

### K7. Effect uncertainty remains explicit

A material external effect MUST distinguish `not_attempted`, `attempted`,
`succeeded`, `failed`, and `ambiguous_pending_reconciliation`. An issued attempt
or lost response MUST NOT be represented as success. Required ambiguity blocks
a receipt from concluding full effect success.

### K8. Evidence, claim, decision, and closure remain distinct

Evidence is not automatically a claim; a claim is not an accepted decision;
and a scoped decision does not establish universal truth. A current resolution
MUST identify its criteria or accounting unit, current support, authority,
decision basis, and unresolved conditions. Partial completion MUST remain
representable and MUST NOT be coerced to full success or undifferentiated
failure.

### K9. Correction authority is explicit and propagation is append-only

A correction assertion alone MUST NOT change current state. An effective
correction requires a correction decision identifying the target, reason,
asserting actor or policy, deciding authority, scope, effective time, and
invalidation, supersession, or replacement result.

Conflicting or unauthorized assertions remain contested or unresolved pending
an authorized decision. Effective corrections preserve history and require
dependent current claims, receipts, and resolutions to be re-evaluated. If
remaining support is insufficient, the dependent conclusion MUST be marked
unresolved, invalidated, or reopened; it MUST NOT remain current by silence.

### K10. Active supersession requires disposition

When a new revision supersedes one targeted by an active run, the run MUST
receive an authorized rationale-bearing disposition: time-bounded grandfather,
pause for new admission and authority, or stop. Silent continuation under new
meaning is non-conformant.

### K11. Decomposition does not double-count

A plan or receipt MUST declare its accounting unit. Parent and child mandates
MUST NOT both count as independent closure obligations when one rolls up the
other. Artificial splitting remains a finding even when arithmetic closes.

### K12. Unknown and extended states remain representable

An implementation MUST preserve unknown, contested, and unresolved state
without forcing it into known success or failure. Extensions MUST NOT redefine
existing values incompatibly and SHOULD use namespaces.

## 4. Correction reducer

When an authorized correction decision makes a correction effective, a
conforming reducer:

1. appends the assertion and decision without modifying their targets;
2. changes the direct target's current validity within the decision scope;
3. traverses current dependencies to claims, receipts, and resolutions;
4. re-evaluates current support and authority;
5. invalidates, marks unresolved, or reopens insufficient conclusions; and
6. preserves the prior conclusion and its historical current interval.

The result is normative; the graph, event-store, or traversal implementation is
not.

## 5. Conformance and routing

Kernel-only processing MUST reject a non-conformant input or preserve it as
contested or unresolved. It MUST NOT claim a successful route.

`PROFILE_REQUIRED` MAY be returned only when an exact, selected, versioned
profile defines the route, routing authority, terminal dispositions, and
conformance tests. The result MUST identify that profile. Merely having a
profile registry or declaring that some profile could route the condition is
insufficient.

At minimum, conformance evidence covers unauthorized execution from a label,
collapsed occurrences, out-of-scope effects, ambiguous results recorded as
success, invalid evidence with stale closure, silent active supersession,
partial outcomes reported as complete, double-counting, relayer misattribution,
unknown-state coercion, unauthorized correction, and unselected-profile
routing.

## 6. Profile contract

A profile MUST declare name, version, kernel compatibility, threat model,
scope, additional conditions, extension states, conformance cases, routing
authority, and lifecycle status. It MUST NOT weaken a kernel invariant.

If a profile introduces auto-admission, standing-authority matching, automated
routing, behavioral gates, numeric thresholds, or governance mechanisms, it
MUST also provide:

- a disposition of applicable blind-panel findings;
- abuse and failure cases in its threat model;
- negative conformance cases;
- an explicit disable or rollback path; and
- the authority and evidence required for acceptance.

Declaration is not acceptance. A profile remains candidate until its own gates
pass. Auto-admission is disabled unless an explicitly selected accepted profile
defines and authorizes it.

## 7. Non-goals and epistemic status

HMIK does not define organizational sanctions, authenticate actors, protect
against a malicious trusted operator, prescribe storage or transport, guarantee
exactly-once effects, choose routing or risk thresholds, set capacity limits,
or claim universal applicability.

HMIK does not redefine, replace, extend, or version the HUMMBL TierShift
execution-intensity architecture.

The name, roles, K1-K12, reducer, and profile contract are candidate. Operator
approval established the identity separation and successor direction, not
canonization. Storage, authority enforcement, evidence integrity, correction
traversal, profile registry, and multi-operator semantics remain open.

## 8. Validation and change control

The candidate remains non-canonical until:

1. each invariant has at least one positive case and one counterexample;
2. the corpus covers the twelve minimum conditions in section 5;
3. two representations preserve every semantic distinction;
4. review outputs are archived with provenance gaps stated explicitly; and
5. human engineering review finds no unresolved normative contradiction.

This file is immutable once accepted into review. Material changes produce a
new version; provenance corrections use an append-only erratum.
