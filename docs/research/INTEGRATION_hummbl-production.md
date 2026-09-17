# Integration with hummbl-production

**Date:** 2026-09-09
**Status:** Active

---

## What this repo is

`hummbl-io/oss` is the ONLY public repository for publishing HUMMBL's open-source work. It replaces the archived `hummbl-governance` repository as the public source of truth for HUMMBL primitives.

## Relationship to hummbl-production

`hummbl-production` is the primary product repository (`hummbl.io`) and the estate authority. The relationship is publication-level:

1. **Claim ledger references** — hummbl-production's public surface claims (e.g., `docs/artifacts/PUBLIC_SURFACE_CLAIM_SYNC_RECEIPT.md`) reference HUMMBL's open-source work. The source of truth for those claims was `hummbl-io/hummbl-governance` (now archived); the current public source is this repo.

2. **Content claim audit** — `docs/audits/2026-08-26/06-content-claims.md` flags that `landing-claims.json` references `hummbl-io/hummbl-governance` but the OSS code is now at `hummbl-io/oss`. The commit hash and proof receipt are from the old repo. This drift needs reconciliation.

3. **White papers and strategic docs** — hummbl-production's `docs/artifacts/` directory references `hummbl-io/hummbl-governance` for the HUMMBL Repo Standard, fleet audit, and coverage matrices. These references should point to `hummbl-io/oss`.

4. **Repository topology** — The apex-nexus AGENTS.md declares `hummbl-governance` as ARCHIVED AND DEAD, with `oss` as its successor. hummbl-production's AGENTS.md tier system still references `hummbl-governance` in Tier 0 — this is stale.

## Deployment surface

`oss` may publish packages to PyPI and npm. It does not deploy a public web surface in the Cloudflare estate.

## What hummbl-production references about this repo

- Public surface claim sync receipts reference the OSS source of truth.
- White papers, strategic plans, and position papers reference governance docs that now live in `oss`.
- The content claim audit flags stale `hummbl-governance` references that should be updated to `oss`.

## What this repo should do

- Maintain the public open-source publishing surface for HUMMBL primitives.
- Keep the HUMMBL Repo Standard, coverage matrices, and governance docs that were migrated from `hummbl-governance`.
- When primitives are published or updated, coordinate with hummbl-production to update claim ledger references and proof receipts.
- The stale `hummbl-governance` references in hummbl-production's docs and claim ledgers should be reconciled to point to `oss`.
