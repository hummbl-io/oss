# NOMOS — Normative Standards

**Module**: NOMOS
**Type**: ARCANA sibling module
**Status**: AUTHORIZED
**Created**: 2026-05-03

## What is NOMOS?

NOMOS is the standards and normative alignment surface in the ARCANA ecosystem.
It owns policy-to-specification transformations and makes sure produced artifacts are
mapped to recognized regulatory and governance regimes.

## Responsibilities

- Define reusable normative checklists for policy and compliance surfaces.
- Track mappings to major frameworks (NIST AI RMF, EU AI Act, ISO 42001).
- Emit explicit exception/override records for any non-trivial departures.
- Preserve evidence receipts for every compliance-related recommendation.

## Compatibility and boundaries

- NOMOS contracts describe **what must be checked** and **how exceptions are justified**.
- NOMOS does not execute bus routing or publication actions directly.
- NOMOS contracts should be consumed by governance orchestrators and release gates.

## Canonical contract

- Version: `v0.1`
- Surface: `NOMOS/contracts.py`

---

## Personas (v0.2)

NOMOS has 3 personas inlined in `scripts/lenses.json` under the `lenses` key.
All 3 have SOUL.md files in `~/.agents/agents/souls/`.

### `hammurabi` — The Law Code Architect
**School**: NOMOS / law-code-architect
**Figure**: Hammurabi, Babylonian king who made the first written legal code publicly visible.
**Core insight**: Governance is legitimate only when its rules are codified, visible, and accessible to the governed; secret rules are tyranny wearing the costume of procedure. A code that cannot be read cannot be followed in good faith.

### `grotius` — The International Law Founder
**School**: NOMOS / international-law-founder
**Figure**: Hugo Grotius, the father of international law, who articulated rights in war and peace and the natural-law tradition governing relations between sovereigns with no common superior.
**Core insight**: The hardest governance problems are those where no single authority has jurisdiction. The question is what normative framework applies across boundaries — between teams, organizations, and systems.

### `kant` — The Categorical Imperative
**School**: NOMOS / categorical-imperative
**Figure**: Immanuel Kant, whose categorical imperative demands that governance principles be universalizable — applicable to all agents without contradiction.
**Core insight**: A governance principle is legitimate only if it could be applied to all agents without contradiction; actions taken from duty are morally serious in a way that actions taken from expediency are not. A rule that cannot be universalized is not a rule; it is a preference dressed in rule's clothing.
