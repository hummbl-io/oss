# CANON - Public Artifact Registry and Policy Baseline Mirror

**Module**: CANON
**Type**: ARCANA sibling module
**Status**: ROADMAP
**Created**: 2026-09-09

## What is CANON?

CANON is the public artifact registry and policy baseline mirror. It is the
canonical, deduplicated record of published artifacts and the normative
baseline (NOMOS standards, PAIDEIA rubrics) those artifacts are measured
against. It indexes and mirrors; it does not generate, score, or gate.

## Responsibilities

- Register and index published artifacts as the canonical record.
- Mirror the policy baseline as the normative reference.
- Track provenance and lineage: what generated what, from which inputs, under
  which contract version.

## Compatibility and boundaries

- CANON indexes and mirrors; it does not generate content (ARCANA / POIESIS),
  score artifacts (PAIDEIA), set normative policy (NOMOS), or gate
  publication (RELEASE).
- CANON is read-only with respect to the artifacts it registers: it records,
  it does not alter.
- Status is ROADMAP: contracts and personas are scaffolded, registry behavior
  is intentionally out of scope this phase (docs/platform-set.md §8).

## Canonical contract

- Version: `v0.1-draft`
- Surface: `CANON/contracts.py`

## Personas (initial scaffold)

CANON has 3 registry-stage personas inlined in `scripts/lenses.json` under
the `lenses` key (school `CANON / ...`), backed by the `CANON_STAGES` roster
in `CANON/contracts.py`:

- `registrar` - artifact registration
- `baseline` - policy baseline mirror
- `provenance` - provenance / lineage
