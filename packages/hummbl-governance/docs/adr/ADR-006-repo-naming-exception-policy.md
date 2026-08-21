# ADR-006 — HUMMBL repo naming exception policy

- **Status:** proposed
- **Date:** 2026-06-25
- **Decision owner:** Reuben Bowlby
- **Steward:** HUMMBL Research Institute
- **Supersedes:** none
- **Superseded by:** none

## Context

The fleet currently includes a few non-`hummbl-*` repositories that are intentionally outside the default naming convention (`whether-book`, `base120`, `idp-spec`). Existing governance documents did not define an explicit, schema-backed mechanism to justify these exceptions, which made enforcement inconsistent across repos.

## Decision

`docs/standards/HUMMBL_REPO_STANDARD.md` now requires a default `hummbl-*` name and defines the exception classes that can override this rule.

`schemas/hummbl-repo-manifest.schema.json` now accepts an optional `repo.naming` exception object in `hummbl.repo.yaml` so exception decisions are machine-readable.

## Required naming policy fields

When using an exception, `repo.naming` must include:

- `hummbl_prefix_exception` (boolean)
- `exception_class`
- `exception_reason`
- `approved_by`
- `approved_at` (YYYY-MM-DD)
- `owning_standard`
- `allowed_scope`
- `forbidden_scope`
- `rename_or_archive_trigger`

Exception classes are limited to:

- `authored_artifact`
- `protocol`
- `reference_archive`
- `research_object`

## Consequences

- Explicit exception records are now standardized across manifests that carry them.
- Agents have a documented constraint: non-prefixed repos are allowed only when explicitly recorded.
- Existing approved exceptions are inventory listed in the standard.

## Receipts

- Add/approve the associated PR and KRINEIA receipt in accordance with standard amendment requirements.
