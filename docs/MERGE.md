# Merge hygiene

Repo-settings companion to [RELEASE.md](../RELEASE.md). This file names the
check contexts a human must require on `main`. GitHub branch protection and
rulesets are not in this git tree.

As of: 2026-09-02, follow-up to #91.

## What #91 got wrong after 2026-08-31

The 2026-08-31 write-up is a snapshot of `abb4df7`. It is no longer the
live merge-pipe description.

| #91 claim | 2026-09-02 |
|-----------|------------|
| `main` has not moved since Audit-1 | False. #76, #75, #105, #106 and others landed. HEAD was `8a02a6c` when this file was added. |
| All open PRs BLOCKED; nothing can land | False. Open PR count was 0 after #106. Squash-merge from a maintainer token works. |
| Only one reviewing identity | Incomplete. Collaborators with admin on this repo: `hummbl-dev`, `hummbl-agent`. |
| `publish-pypi.yml` and `RELEASE.md` disagree on tag shape | Fixed on main. Canonical tag is `python/<package>/v*`. |
| Boundary scan is filename-only | Partial. `check_boundary_patterns.py` now also flags non-placeholder CGNAT IPs. Hostname and `C:/Users` path classes from #91 are still out of that scanner. |
| Required checks are only `gitleaks` and `pattern-denylist` | Still the likely settings gap. This file exists so that gap can be closed without guessing job names. |

## Required status-check contexts

Require **job names**, not workflow names. Require only jobs that run on
every pull request.

Require:

| Context | Workflow | Always runs on PR? |
|---------|----------|--------------------|
| `gitleaks` | Boundary check | Yes |
| `pattern-denylist` | Boundary check | Yes |
| `ci-ok` | Tests | Yes, after this change |

Do **not** require:

| Context | Why |
|---------|-----|
| `test (<package>)` | 25 names. Adding a package would make protection stale or block merges. `ci-ok` already fails if any matrix cell fails. |
| `test (hummbl-governance, 3.11)` and siblings | Same. Folded into `ci-ok`. |
| `pip-audit` | Folded into `ci-ok`. |
| `validate` / Validate workflows | Path-filtered to workflow files. Missing on ordinary PRs. Requiring it starves docs and package PRs. |
| `dependency-review` | Path-filtered to lock/manifest changes. Same starvation class. |
| Supabase Preview, Cursor Automation, Devin Review | Third-party. Neutral/skipped is not a merge gate. |

## How `ci-ok` works

`.github/workflows/ci.yml` no longer path-filters. Every PR and every
push to `main` runs the 25-package 3.13 matrix, the governance 3.11-3.13
matrix, and pip-audit. `ci-ok` needs those three jobs and fails unless
each result is `success`.

That is the one Tests context to paste into branch protection or a ruleset.

## Human step this file cannot do

Add `ci-ok` to the required status checks on `main` (classic protection or
a repository ruleset). Until that settings change, an approved PR with a
red `ci-ok` can still merge. The YAML only makes the context exist.

## Out of scope here

- Hostname / local-path redaction listed in #91 (follow-up class, not merge hygiene).
- Changing review-count or `enforce_admins`.
- New primitives, new PyPI names, ledger unification.
