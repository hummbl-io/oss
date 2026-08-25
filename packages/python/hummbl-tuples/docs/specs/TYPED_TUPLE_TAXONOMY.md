# Typed Tuple Taxonomy

Status: draft  
Canonical version: `v0.1.0`  
Last updated: `2026-04-20`

This document is the canonical, versioned taxonomy for HUMMBL typed tuples.

It defines tuple classes by governance role, not by current implementation location. New tuple classes should be added here first, then reflected in schemas, examples, and runtime code.

## Versioning Rules

- The taxonomy version changes when the canonical set of tuple classes or their normative meanings change.
- Patch version:
  editorial clarification, examples, wording, non-semantic cleanup.
- Minor version:
  additive change to the taxonomy, such as a new tuple class or new normative field expectations.
- Major version:
  breaking semantic change, rename, split, merge, or removal of a canonical tuple class.

## Change Log

### v0.1.0 - 2026-04-20

- establishes the canonical typed tuple taxonomy
- recognizes `CONTRACT`, `DCT`, `DCTX`, `PROMOTION_RECEIPT`, `REVOCATION`, `SYSTEM`, `EVIDENCE`
- defines role-oriented meanings for each tuple class

## Canonical Classes

## CONTRACT

Role: bounded work definition

Core questions it answers:

- What is the objective?
- What tools or actions are allowed?
- What evidence must exist before the work is complete?

Normative meaning:
- A `CONTRACT` defines bounded authority in task form.
- It specifies permitted scope, expected outputs, and completion conditions.
- It should exist before delegation or execution.

## DCT

Role: delegated authority

Core questions it answers:

- Who issued authority?
- To whom?
- For which operations?

Normative meaning:
- A `DCT` is the authority-bearing token or record.
- It should bind subject, issuer, and scope.
- It must not exceed the governing `CONTRACT`.

## DCTX

Role: delegation lifecycle context

Core questions it answers:

- What state transition happened?
- How does child work relate to parent work?
- What depth or execution lineage applies?

Normative meaning:
- A `DCTX` tracks delegation state and lineage.
- It is the positional and lifecycle context for governed work.
- It should preserve the originating `CONTRACT` bound through transitions.

## PROMOTION_RECEIPT

Role: governed promotion decision

Core questions it answers:

- What was promoted from where to where?
- Who allowed, denied, held, or shadow-evaluated the promotion?
- Under which policy version and why?

Normative meaning:
- A `PROMOTION_RECEIPT` records a constitutional gate decision.
- It should bind the candidate, source rung, target rung, decision, and policy basis.
- It exists to prove that promotion was governed rather than merely executed.

## REVOCATION

Role: explicit withdrawal of delegated authority

Core questions it answers:

- Which authority grant was withdrawn?
- Who revoked it and for what reason?
- Does the revocation cascade to descendants?

Normative meaning:
- A `REVOCATION` records explicit authority withdrawal.
- It is distinct from passive expiry.
- It should support emergency halts, trust withdrawal, or policy-triggered invalidation.

## SYSTEM

Role: runtime control-plane event

Core questions it answers:

- What did infrastructure do?
- Was an adapter invoked or blocked?
- What enforcement mode applied?

Normative meaning:
- A `SYSTEM` tuple records runtime governance-relevant infrastructure behavior.
- It is not a generic application log.
- It should capture events that change enforcement, routing, or execution conditions.

## EVIDENCE

Role: proof of execution or completion

Core questions it answers:

- What happened?
- What proof artifact identifies it?
- What measurable execution details are available?

Normative meaning:
- An `EVIDENCE` tuple records what was actually done and what artifacts prove it.
- It should be the discharge path for exercised authority.
- It is the principal completion proof in the tuple family.

## Near-Canonical Extensions

These are plausible next canonical classes but are not yet part of `v0.1.0`:

- `ATTEST`
- `TRACE_EVIDENCE`
- `THRESHOLD_RECEIPT`
- `SAFE_STATE_RECEIPT`

They remain candidates until explicitly promoted in this document.

## Governance Rule

If another document disagrees with this file about tuple-class meaning or canonical status, this file wins.
