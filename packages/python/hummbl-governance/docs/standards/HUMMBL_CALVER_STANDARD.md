# HUMMBL Calendar Versioning (CalVer) Standard v0.1

**Status:** v0.1 (draft)
**Steward:** HUMMBL, LLC
**Approving human:** Reuben Bowlby
**Source of record:** this file in `hummbl-io/hummbl-governance` (canonical)
**Depends on:** HUMMBL Repo Standard v0.1
**Reference implementation:** `scripts/hummbl_release.py` in this repo
**Provenance:** adapted from Hermes Agent's CalVer release script (Nous Research, MIT), verified against live tags `v2026.7.7`, `v2026.7.7.2`, `v2026.5.29`, `v2026.5.29.2`

## 1. Purpose

Define the calendar versioning (CalVer) scheme for HUMMBL projects that need
date-based versioning with multiple releases per day. This standard exists
because the fleet's existing versioning regimes — skill SemVer, schema static
constants, and phase-based file naming — are all release-cycle-based and cannot
express same-day iteration.

CalVer is **not** a replacement for SemVer. The two are complementary axes:

- **SemVer** signals API stability and breaking-change semantics. Use it for
  contract surfaces, published libraries, and any artifact where a downstream
  consumer needs to reason about compatibility.
- **CalVer** signals release cadence and temporal ordering. Use it for
  fast-iterating infrastructure, agent runtimes, and any artifact where "when
  was this released?" matters more than "is this a breaking change?".

A project may use both: SemVer as the internal package version, CalVer as the
git tag and release title. This is the Hermes pattern and is the recommended
default for HUMMBL projects that ship frequently.

## 2. Scope

This standard covers:

- CalVer tag format for git tags and GitHub/Gitea releases
- Same-day suffixing for multiple releases per day
- Phase-gated artifact versioning (the -1/0/1 ladder)
- The relationship between CalVer tags and internal SemVer
- Schema field constraints for `schema_version` fields that accept CalVer

This standard does **not** cover:

- SemVer bump rules (governed by each project's contract surface)
- Branch naming (governed by HUMMBL Repo Standard §10)
- Receipt schema (governed by KRINEIA)
- Skill versioning (governed by `SKILL_VERSIONING.md`)

## 3. Two CalVer formats (context-dependent)

HUMMBL mandates two CalVer formats, selected by artifact class. A project uses
exactly one format per release; the format is determined by what is being
released, not by preference.

### 3.1 Release format — `vYYYY.M.D[.N]`

For releases of a project, package, or runtime where the phase is not a
load-bearing part of the identity.

```
v2026.8.11          ← first release on 2026-08-11
v2026.8.11.2        ← second release on 2026-08-11
v2026.8.11.3        ← third release on 2026-08-11
```

**Rules:**
- `YYYY` — full year, no padding (`2026`, not `26`)
- `M` — month, no zero-padding (`8`, not `08`)
- `D` — day, no zero-padding (`3`, not `03`)
- `.N` — same-day suffix, omitted on first release, starts at `2` on the second
- No prefix other than `v`
- Tag is annotated (`git tag -a`)

**Why no zero-padding:** Shorter tags, correct lexical sort, matches Hermes
and CalVer.org's `YYYY.MM.DD` short-form convention. `v2026.8.3` sorts before
`v2026.8.11` correctly; `v2026.08.03` would not sort differently but adds two
bytes of noise.

**Why suffix starts at 2:** The first release of a day has no suffix — the
date alone is the version. The second release appends `.2`. This matches
Hermes and ChronVer's `.CHANGESET` pattern. A `.1` suffix would imply a
"first release" suffix exists, which it does not.

### 3.2 Phase-gated format — `phase-{N}.vYYYY.M.D[.N]`

For artifacts governed by the -1/0/1 admission ladder (governed-counterpart
and any project that adopts the phase gate model). The phase is a load-bearing
part of the artifact's identity because it determines what the artifact is
authorized to do.

```
phase--1.v2026.8.10          ← phase -1 (admission) artifact, 2026-08-10
phase-0.v2026.8.11           ← phase 0 (init) artifact
phase-1.v2026.8.11           ← phase 1 (validation) artifact
phase-1.v2026.8.11.2         ← second phase-1 artifact same day
phase-2.v2026.8.12           ← phase 2 (persistence) artifact
```

**Rules:**
- `phase-{N}` — literal `phase-` prefix, then the phase number
- Phase `-1` is written as `phase--1` (double hyphen: one for the prefix, one
  for the negative sign). This is ugly but unambiguous and sorts before
  `phase-0` lexically (`-` = 0x2D < `0` = 0x30). Lexical sort is correct for
  phases -1 through 9; for phases ≥10, use `git tag --sort=-v:refname` or
  numeric-aware sorting (`phase-12` would lexically precede `phase-2`).
- `N` is a non-negative integer for phases 0 and above
- The `.vYYYY.M.D[.N]` segment follows the release format rules
- Same-day suffixing applies within a phase: `phase-1.v2026.8.11.2` is the
  second phase-1 release on that date

**When to use which format:**

| Artifact class | Format | Example |
|----------------|--------|---------|
| Runtime/package release | Release | `v2026.8.11` |
| Published library (PyPI/npm) | SemVer (internal) + CalVer (tag) | `0.17.0` + `v2026.8.11` |
| Phase-gated schema artifact | Phase-gated | `phase-1.v2026.8.11` |
| Phase-gated receipt bundle | Phase-gated | `phase-1.v2026.8.11.2` |
| Skill release | SemVer (per `SKILL_VERSIONING.md`) | `0.2.0` |
| Governance standard | SemVer (per Repo Standard §13) | `v0.1` |

## 4. Same-day suffixing

When a second release happens on the same calendar date (in the project's
configured timezone, default UTC), the tag gets a `.N` suffix incrementing
from `2`.

**Algorithm** (implemented in `hummbl_release.py`):

```python
def next_available_tag(base_tag: str) -> str:
    if not git_tag_exists(base_tag):
        return base_tag
    suffix = 2
    while git_tag_exists(f"{base_tag}.{suffix}"):
        suffix += 1
    return f"{base_tag}.{suffix}"
```

- First release of the day: `v2026.8.11` (no suffix)
- Second release: `v2026.8.11.2`
- Third: `v2026.8.11.3`
- Nth: `v2026.8.11.{N}`

The suffix is per-phase in the phase-gated format:
`phase-1.v2026.8.11.2` is independent of `phase-2.v2026.8.11.2`.

## 5. Relationship to internal SemVer

A project that uses CalVer tags **may** also carry an internal SemVer for
package metadata. The two are kept in lockstep by the release tool:

```python
# Example: hermes_cli/__init__.py pattern
__version__ = "0.17.0"           # SemVer — bumped per release
__release_date__ = "2026.6.19"   # CalVer date — updated per release
```

**Rules:**
- The git tag is CalVer (`v2026.8.11`)
- The package `version` field in `pyproject.toml` / `package.json` is SemVer
- The release title combines both: `MyProject v0.17.0 (v2026.8.11)`
- The release tool bumps both atomically in the same commit
- A project may opt out of internal SemVer and use CalVer as the only version
  (set `--no-semver` in the release tool)

## 6. Schema field constraints

Schemas that accept CalVer version strings must use a `pattern` constraint,
not a `const`. The pattern depends on which format the schema governs.

### 6.1 Release format pattern

```json
"schema_version": {
  "type": "string",
  "pattern": "^v\\d{4}\\.(1[0-2]|[1-9])\\.(3[0-1]|[1-2][0-9]|[1-9])(\\.\\d+)?$"
}
```

Matches: `v2026.8.11`, `v2026.8.11.2`
Rejects: `v2026.08.11` (zero-padded month), `v2026.8.01` (zero-padded day), `2026.8.11` (no `v`), `v1.0.0` (SemVer)

The month/day segments use `(1[0-2]|[1-9])` and `(3[0-1]|[1-2][0-9]|[1-9])` to reject leading zeros, per §3.1.

### 6.2 Phase-gated format pattern

```json
"schema_version": {
  "type": "string",
  "pattern": "^phase-(-1|0|[1-9][0-9]*)\\.v\\d{4}\\.(1[0-2]|[1-9])\\.(3[0-1]|[1-2][0-9]|[1-9])(\\.\\d+)?$"
}
```

Matches: `phase--1.v2026.8.10`, `phase-0.v2026.8.11`, `phase-1.v2026.8.11.2`
Rejects: `phase-01.v2026.8.11` (zero-padded phase), `phase-1.2026.8.11` (missing `v`), `phase-1.v2026.08.11` (zero-padded month)

### 6.3 Dual-format pattern (accepts either)

For schemas that accept both release and phase-gated artifacts:

```json
"schema_version": {
  "type": "string",
  "pattern": "^(phase-(-1|0|[1-9][0-9]*)\\.)?v\\d{4}\\.(1[0-2]|[1-9])\\.(3[0-1]|[1-2][0-9]|[1-9])(\\.\\d+)?$"
}
```

### 6.4 Schema vs. procedural rules

The patterns above validate **format only** (no zero-padding, valid month/day
ranges, correct prefix). Two rules from §3-§4 are **not** enforced by the regex
and are instead enforced procedurally by the release tool:

1. **Same-day suffix starts at `.2`** — the regex `(\.\d+)?` accepts `.0` and
   `.1`, but the release tool's `next_available_tag()` never produces them. A
   manually-created tag like `v2026.8.11.1` would pass schema validation while
   violating §4. This is intentional: the schema validates format, the tool
   enforces policy.
2. **Calendar validity** — the day segment `(3[0-1]|...)` accepts 31 for all
   months, including February. `v2026.2.31` passes schema validation but
   represents an impossible date. The release tool computes dates from
   `datetime.now()`, so impossible dates cannot arise from normal operation —
   only from `--date` override, which should be human-reviewed.

### 6.5 Migration from const

Schemas currently using `"const": "GOVERNED_COUNTERPART.v0.1"` must migrate in
two steps:

1. **Additive:** change `const` to `pattern` that accepts both the old const
   value and the new CalVer format. This is a non-breaking change — existing
   fixtures continue to validate. Use this additive pattern:

```json
"schema_version": {
  "type": "string",
  "pattern": "^(GOVERNED_COUNTERPART\\.v0\\.1|phase-(-1|0|[1-9][0-9]*)\\.v\\d{4}\\.(1[0-2]|[1-9])\\.(3[0-1]|[1-2][0-9]|[1-9])(\\.\\d+)?)$"
}
```

2. **Cutover:** after all fixtures and receipts have been re-versioned to
   CalVer, tighten the pattern to §6.2 (rejecting the old format).

The migration receipt must record which artifacts were re-versioned and when.

## 7. Timezone

CalVer dates are computed in UTC by default. The release tool accepts a
`--timezone` argument for projects that need local-date semantics (e.g., a
project that ships on Pacific time and wants the tag to reflect the local
date, not the UTC date).

**Default:** UTC (`Z` suffix in timestamps, `YYYY.M.D` in tags computed from
`datetime.now(timezone.utc)`).

**Override:** `--timezone America/Los_Angeles` computes the date in that zone.
This only affects the tag date, not the receipt timestamp (which is always UTC).

## 8. Belated releases

If a release is created after the work was actually done (e.g., tagging on
Monday for Friday's work), the release tool accepts `--date 2026.8.8` to
override the CalVer date. The override must be recorded in the release receipt
with a rationale.

## 9. Release tool

The reference implementation is `scripts/hummbl_release.py` in this repo. It
is a generic, project-agnostic tool that any HUMMBL repo can use.

**Usage:**

```bash
# Dry run — preview the tag and changelog
python scripts/hummbl_release.py --project my-project

# Create the release, push, and create GitHub release
python scripts/hummbl_release.py --project my-project --bump minor --publish --push --gh-release

# Phase-gated release
python scripts/hummbl_release.py --project governed-counterpart --phase 1 --publish --push

# Belated release
python scripts/hummbl_release.py --project my-project --date 2026.8.8 --publish

# First release (no previous tag)
python scripts/hummbl_release.py --project my-project --first-release --publish --push

# CalVer only, no internal SemVer
python scripts/hummbl_release.py --project my-project --no-semver --publish

# Multi-project repo — scope tag lookup
python scripts/hummbl_release.py --project my-project --tag-prefix my-project --publish
```

The tool:
- Computes the CalVer tag (with same-day suffixing)
- Bumps internal SemVer if `--bump` is passed
- Updates version files (`pyproject.toml`, `__init__.py`, `package.json`)
- Generates a changelog from commits since the last tag
- Creates an annotated git tag
- Optionally pushes the tag to origin (`--push`)
- Optionally creates a GitHub release (`--gh-release`; Gitea support planned)
- Posts a STATUS to the coordination bus (`--bus` on dry run; always on `--publish`)

## 10. What this standard does not mandate

- **No mandate to adopt CalVer.** Projects on SemVer with slow release cycles
  (governance standards, schemas, skills) should stay on SemVer. CalVer is for
  projects that ship multiple times per day or per week.
- **No mandate to use the phase-gated format.** Projects without the -1/0/1
  ladder use the release format. The phase-gated format is only for projects
  that have adopted the governed-counterpart admission model.
- **No mandate to drop internal SemVer.** Projects that publish to PyPI/npm
  should keep SemVer for package metadata and use CalVer only for git tags.

## 11. Amendment

Changes to this standard require: a PR to `hummbl-io/hummbl-governance`, an
ADR under `docs/adr/`, a KRINEIA receipt, and human approval (Reuben Bowlby).
Breaking changes bump the standard version (SemVer) and trigger a fleet
re-audit of all repos using CalVer.

## 12. References

- CalVer.org — https://calver.org/
- ChronVer — https://chronver.org/
- Hermes Agent `release.py` — reference implementation (Nous Research, MIT)
- HUMMBL Repo Standard — `docs/standards/HUMMBL_REPO_STANDARD.md`
- HUMMBL Init Standard — `docs/standards/HUMMBL_INIT_STANDARD.md`
- Skill Versioning — `.agents/rules/SKILL_VERSIONING.md`
- Governed Counterpart phase ladder — `governed-counterpart-grammar-phase--1.md`
