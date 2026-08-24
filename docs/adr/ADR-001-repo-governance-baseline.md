# ADR-001 — hummbl-production repo governance baseline

- **Status:** accepted
- **Date:** 2026-06-23
- **Decision owner:** Operator
- **Steward:** HUMMBL Research Institute
- **Supersedes:** none
- **Superseded by:** none

## Context

`hummbl-io/hummbl-production` is the production surface for HUMMBL's public web presence, API, dashboard, and public claim data. It serves `hummbl.io` via Cloudflare Pages, Cloudflare Workers API, and hosts the canonical claims provenance manifest at `web/manifest/claims-provenance.json`.

A live audit of all 91 `hummbl-io` repos (hummbl-governance#72) found 0% `KRINEIA.md`, 0% `hummbl.repo.yaml`, and 1% `CONSTITUTION.md` coverage fleet-wide. This repo had a strong `AGENTS.md`, `README.md`, `CONTRIBUTING.md`, `SECURITY.md`, and `LICENSE` but was missing its governance artifact stack: `CONSTITUTION.md`, `KRINEIA.md`, `hummbl.repo.yaml`, `CODEOWNERS`, `_receipts/`, and `docs/adr/`.

This issue was tracked as hummbl-production#407 and prioritized because hummbl-production is a protected public surface that makes verifiable claims — the governance baseline should be explicit and receipt-backed.

## Decision

Adopt the HUMMBL Repo Standard v0.1 artifact stack for `hummbl-io/hummbl-production`.

### Files added

| File                              | Purpose                                                                                                                                                                                                        |
| --------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `CONSTITUTION.md`                 | 8 protected invariants: public claim honesty, no secrets, Cloudflare boundary discipline, claims provenance manifest integrity, Apache-2.0, receipt integrity, homepage snippet CI, public namespace integrity |
| `KRINEIA.md`                      | repo-local receipt manifest with public-claim and deployment-target governance extensions                                                                                                                      |
| `hummbl.repo.yaml`                | machine-readable manifest declaring 5 surfaces (hummbl.io, API, dashboard, public_claim_data, readiness_compliance)                                                                                            |
| `CODEOWNERS`                      | normative files require steward approval                                                                                                                                                                       |
| `docs/adr/ADR-001`                | this decision record                                                                                                                                                                                           |
| `_receipts/krineia/primary.jsonl` | genesis receipt                                                                                                                                                                                                |

### Files updated

| File              | Change                          |
| ----------------- | ------------------------------- |
| `README.md`       | pointer to governance artifacts |
| `CONTRIBUTING.md` | pointer to governance artifacts |

## Consequences

- **Positive:** hummbl-production is now self-compliant with the HUMMBL Repo Standard v0.1.
- **Positive:** 8 protected invariants are constitutionally protected, including the public claim honesty invariant that ties this repo to the claims remediation work.
- **Positive:** Public claim changes now require KRINEIA receipts, creating an auditable trail for claim status transitions.
- **Positive:** Deployment boundary changes (Cloudflare Pages/Workers) now require an ADR and human approval.
- **Note:** ADR numbering starts at ADR-001 for this repo.

## Receipts

- Genesis receipt: `_receipts/krineia/primary.jsonl` line 1.

## References

- HUMMBL Repo Standard: `hummbl-io/hummbl-governance/docs/standards/HUMMBL_REPO_STANDARD.md`
- Standard adoption ADR: `hummbl-io/hummbl-governance/docs/adr/ADR-003-hummbl-repo-standard.md`
- Self-compliance reference: `hummbl-io/hummbl-governance/docs/adr/ADR-004-repo-governance-baseline.md`
- Fleet audit: `hummbl-io/hummbl-governance#72`
- Issue: `hummbl-io/hummbl-production#407`
