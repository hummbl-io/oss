# LINGUA — Editorial and Narrative Engineering

**Module**: LINGUA
**Type**: ARCANA sibling module
**Status**: AUTHORIZED
**Created**: 2026-05-03

## What is LINGUA?

LINGUA designs narrative format, variant generation, and style governance for
content that moves from ARCANA/PAIDEIA analysis into production-facing editorial
forms.

## Responsibilities

- Define stylistic contracts and variant routing for channels.
- Manage citation integrity and paraphrase safety policies.
- Maintain readability and intent-alignment checks for audience-specific outputs.
- Support translation and localization planning where needed.

## Compatibility and boundaries

- LINGUA focuses on editorial surfaces, not policy validity or release gating.
- LINGUA should emit clearly versioned edit receipts for any transformation from
  source content.

## Canonical contract

- Version: `v0.1`
- Surface: `LINGUA/contracts.py`

---

## Personas (v0.2)

LINGUA has 3 personas inlined in `scripts/lenses.json` under the `lenses` key.
All 3 have SOUL.md files in `~/.agents/agents/souls/`.

### `orwell` — Language and Power
**School**: LINGUA / language-and-power
**Figure**: George Orwell, from *Politics and the English Language* to Newspeak.
**Core insight**: The language a system uses is not neutral; it either obscures or clarifies, and the direction of obscurity is almost always toward power. Newspeak — language designed to limit the range of thinkable thought — is the paradigmatic case: euphemism masks violence, jargon masks inaction. A system whose vocabulary shrinks the space of possible critique has already begun to govern by limiting what can be said.

### `borges` — The Library of Variants
**School**: LINGUA / library-of-variants
**Figure**: Jorge Luis Borges, the Library of Babel, the labyrinth as editorial structure.
**Core insight**: The editorial problem is not generation but selection; abundance without a criterion for selection is indistinguishable from paralysis. The infinite space of possible variants contains every book, and almost none are worth reading. The question is what principle of selection the system uses, and whether that criterion is legible or hidden.

### `rhetoric_aristotle` — Persuasive Structure
**School**: LINGUA / persuasive-structure
**Figure**: Aristotle's *Rhetoric* — ethos, pathos, logos, the three modes of persuasion.
**Core insight**: Every act of system communication is a rhetorical act, and the balance of the three modes reveals what the system believes will convince you. Which mode dominates — credibility (ethos), emotional appeal (pathos), or logical argument (logos) — and should it? The dominant mode is often a tell about what the system is actually doing.
