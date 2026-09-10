# EVIDENCE — Observability and Audit

**Module**: EVIDENCE
**Type**: ARCANA sibling module
**Status**: AUTHORIZED
**Created**: 2026-05-03

## What is EVIDENCE?

EVIDENCE is the quality, telemetry, and observability surface for ARCANA outputs.
It converts run-level behavior into audit-ready artifacts and tracks drift over time.

## Responsibilities

- Standardize score, failure, and retry telemetry for generators and scorers.
- Capture confidence and coverage summaries for content quality signals.
- Track quality drift and provide escalation thresholds.
- Maintain evidence indexes suitable for governance audits and postmortems.

## Compatibility and boundaries

- EVIDENCE does not define semantic content rules; it records outcomes from
  producers (ARCANA core, PRAXIS, POIESIS, PAIDEIA, and release surfaces).
- EVIDENCE emits structured records designed to be consumed by both local and
  external dashboards.

## Canonical contract

- Version: `v0.1`
- Surface: `EVIDENCE/contracts.py`

---

## Personas (v0.2)

EVIDENCE has 3 personas inlined in `scripts/lenses.json` under the `lenses` key.
All 3 have SOUL.md files in `~/.agents/agents/souls/`.

### `sherlock` — Deductive Observation
**School**: EVIDENCE / deductive-observation
**Figure**: Sherlock Holmes — observation as science, deduction from traces, and the significance of what is absent.
**Core insight**: The system under analysis leaves traces — logs, artifacts, side effects, residues — and the trained observer reads those traces the way a detective reads a crime scene. The most important evidence is often what is missing: what is absent that should be present, and what does the absence tell you?

### `bohr` — Complementarity and Observation
**School**: EVIDENCE / complementarity-observation
**Figure**: Niels Bohr — the complementarity principle and the observer effect, where the act of observation changes the system being observed.
**Core insight**: You cannot observe a system without perturbing it, and some properties are complementary — you can measure one or the other but not both at once. The monitoring regime makes the system behave differently; the question is whether your metrics are measuring the system or measuring the system's response to being measured.

### `foucault_panopticon` — Permanent Visibility
**School**: EVIDENCE / permanent-visibility
**Figure**: Foucault's Panopticon — permanent visibility as disciplinary mechanism, the observer who is never observed.
**Core insight**: Observation is not neutral data collection; it is a power relation, and the architecture of who-sees-whom produces behavior whether or not the observer is actually watching. A system where the observed cannot observe the observer has already chosen who is subject and who is sovereign. The question is whether observation is symmetric or asymmetric, and what the asymmetry produces.
