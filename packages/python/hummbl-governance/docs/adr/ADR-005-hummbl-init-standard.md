# ADR-005 — HUMMBL Init Standard v0.1

- **Status:** accepted
- **Date:** 2026-06-22
- **Decision owner:** Reuben Bowlby
- **Steward:** HUMMBL, LLC
- **Supersedes:** none

## Context

The fleet rollout from 2026-06-22 initialized governance artifacts across
91 repos using ad-hoc Python scripts in `/tmp/hummbl-rollout/`. The process
exposed several issues:

1. **Inconsistency.** Different clusters used different generators
   (`generate_cluster.py`, `generate_cluster6.py`, inline scripts). File
   content varied slightly between runs.

2. **No grounding.** The 5/15 and 6/15 cluster generators used generic
   invariants for repos that had no README/AGENTS.md to ground from. Some
   repos got 3 invariants, others got 4, with no clear rule.

3. **Squash merge data loss.** The hummbl-governance PR #1009 lost governance
   files during squash merge because `.gitignore` deny-by-default blocked
   root-level files. The initializer did not check `.gitignore` before
   staging.

4. **No idempotency.** Running the initializer on an already-initialized
   repo created duplicate PRs (the `generate_cluster.py` import side-effect
   that created 8 duplicate PRs).

5. **No validation step.** Files were pushed but not verified on the
   default branch. The hummbl-governance issue was only caught by a post-merge
   tree check.

6. **Archived repo handling was ad-hoc.** The fork-boundary layer and
   archived non-fork repos used different procedures (un-archive, push,
   re-archive) with no documented standard.

## Decision

Adopt the HUMMBL Init Standard v0.1 as the canonical approach to
initializing every class of artifact in the HUMMBL fleet.

### Key decisions

1. **Deterministic file sets.** Each artifact class has a defined file set.
   The generator does not improvise.

2. **Grounded invariants.** Protected invariants in CONSTITUTION.md are
   derived from the repo's actual content (README, AGENTS.md, pyproject.toml,
   package.json). Minimum 3, maximum 8.

3. **Receipt-first.** Every initialization that creates normative files
   produces a KRINEIA genesis receipt before the PR.

4. **No blind templating.** The standard explicitly forbids blind
   templating (inherited from the HUMMBL Repo Standard).

5. **Idempotency.** Running the initializer on an already-initialized repo
   is a no-op.

6. **Single source of truth.** Standard docs in `hummbl-governance`,
   templates in `.github`, generator in `hummbl-governance/tools/`.

7. **Initialization order.** New repos follow: create → clone → package →
   governance → CI → inventory → PR → verify.

8. **Validation.** Every initialization is validated by API checks, hash
   chain verification, and file existence confirmation.

9. **Generator script.** A single `tools/init_repo.py` will consolidate
   the ad-hoc scripts. Status: not yet built — this ADR authorizes its
   construction.

## Alternatives considered

- **Keep using ad-hoc scripts.** Rejected: inconsistency and idempotency
  failures already caused duplicate PRs and data loss.

- **Use a generic repo template (cookiecutter, gh repo create --template).**
  Rejected: the HUMMBL Repo Standard explicitly forbids blind templating.
  Templates produce generic content; HUMMBL requires grounded invariants.

- **Wait for the generator before standardizing.** Rejected: the standard
  documents the procedure; the generator implements it. The standard can
  guide manual initialization before the generator exists.

## Consequences

- **Positive:** Future initializations are deterministic and auditable.
- **Positive:** The generator script has a clear spec to implement against.
- **Positive:** New repos can be initialized by any agent following the
  standard, without improvisation.
- **Negative:** The generator script (`tools/init_repo.py`) does not yet
  exist. Manual initialization following this standard is required until
  it is built.
- **Negative:** The standard adds a validation step that slows down
  high-volume rollouts. Acceptable: correctness > speed.

## Receipts

- Genesis receipt for this ADR: to be appended to
  `_receipts/krineia/primary.jsonl` upon merge.
