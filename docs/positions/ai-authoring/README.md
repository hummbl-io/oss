# AI Authoring & Fleet Authoring — HUMMBL Position Package

**Status: v1.0.0 — issued and placed in hummbl-io/oss under Reuben Bowlby's public-use ruling (2026-11-14).**
**Doctrine status: ADOPTED 2026-11-12** (Fleet Authored argument, v1.0.0, Reuben Bowlby's ruling).
**Public placement: RULED AND EXECUTED.** Adoption of the doctrine did not clear public use; the separate, stricter ruling was given by Reuben Bowlby on 2026-11-14 (Main), after the HML-G010 public-use gate discharged (attacks 1732–1737, 6 CLOSED · 0 OPEN, delta II). This package is placed at docs/positions/ai-authoring/ via PR (number in REVIEW.md). The reservation's history is preserved in EVOLUTION.md (E-007, E-011).

## What this is

This package states HUMMBL's position on two related questions:

- **AI Authoring** — how work produced with AI systems is attributed, disclosed, and held accountable (Part I of `POSITION.md`).
- **Fleet Authoring** — what "Fleet Authored" means in this estate's governed sense: a *process mark* that shows its work, not a credential and not a warrant of truth (Part II of `POSITION.md`).

The Fleet Authoring doctrine is stated here **as adopted**. This package does not re-open, strengthen, or soften any of its claims. Where the doctrine's first draft (v0.1.0, 2026-11-12) used stronger rhetoric — "credential", "warrants" — those words were retired at the gate, and the adopted v1.0.0 governs.

## The living-document rule

Earlier position packages in `docs/positions/` are dated snapshots (e.g. `ai-2026-09-12/`, with `README.md`, `METHOD.md`, `REVIEW.md`, `SOURCES.md`, `claims.json`). This package **adapts that shape openly** for a position that is expected to change:

- `README.md` and `REVIEW.md` keep their usual roles (index; gate record).
- `POSITION.md` replaces the one-off method/sources statement: it is the current statement of the position, versioned.
- `EVOLUTION.md` replaces the static source list as the package's memory: it is the receipts ledger for the position itself.
- `claims.json` **is included**, generated from `POSITION.md` v0.1.0 in the repo's convention schema (gate attack 1737 closed the earlier deferral: the claims were already enumerated in `POSITION.md`, so the machine-readable form is included now rather than at first publication). The claims live in `POSITION.md`, their history in `EVOLUTION.md`, and their checkable form in `claims.json`.

The rule, stated in full in `EVOLUTION.md`: **no silent edits.** Every change to the position is a new version, a dated entry in `EVOLUTION.md`, the ruling that authorised it, the gate evidence behind it, and the superseded text quoted or hashed. Corrections are appended, never rewritten. A reader should be able to reconstruct what the position said at any past date, and why it changed.

## File map

| File | Contents |
|---|---|
| `README.md` | This index: status, the public-use ruling and its history, the living-document rule, the file map. |
| `POSITION.md` | The position itself, v1.0.0: Part I AI Authoring · Part II Fleet Authoring (adopted doctrine, stated faithfully) · Part III What we do not claim. |
| `EVOLUTION.md` | The receipts ledger: the standing no-silent-edits rule and the seeded lineage entries E-001 onward. |
| `REVIEW.md` | Gate record: the doctrine's completed Red Team gate (attacks 1642–1652 + delta), Blue Team I's matched read, and this package's own HML-G010 public-use gate (attacks 1732–1737, FIX-THEN-PUBLISH, fold recorded). |
| `claims.json` | The position's claims in the repo's convention schema (schema 1.0), generated from `POSITION.md` v0.1.0: each claim with its evidence class, disposition, sources, limitation, and revision trigger. |
| `evidence/` | The load-bearing evidence, lodged in the venue (gate attack 1732): the doctrine v1.0.0, its gate and delta reviews, Blue Team I's matched read of this package, and the HML-G010 public-use review. SHA-256 for each file is recorded in `REVIEW.md`. |

## Sources of record

- Doctrine: `FLEET-AUTHORED-ARGUMENT-2026-11-12-v1.0.0.md` (adopted; SHA-256 `0a01d5b9c0dd6ce00f30e26041fa27deb192457a8ccb7ffee67359921c1224cc`) — lodged in this package at `evidence/FLEET-AUTHORED-ARGUMENT-2026-11-12-v1.0.0.md`.
- Gate: Red Team G010 review of v0.1.0 (attacks 1642–1652, FIX-THEN-ADOPT) and delta review of v0.2.0 (DELTA CONFIRMED, 11 CLOSED · 0 OPEN) — both lodged in `evidence/`; full record in `REVIEW.md`.
- AI Authoring frame: the estate's authorship record of 2026-10-31 (ICMJE / COPE / journal-policy fences; author-of-record shape) and Reuben's fleet definition of 2026-10-20 — entries E-001 and E-002 in `EVOLUTION.md`.
- Related instrument (cited, not summarised): the Fleet Authoring rubric, filed as PR `hummbl-io/agents#1848`.
