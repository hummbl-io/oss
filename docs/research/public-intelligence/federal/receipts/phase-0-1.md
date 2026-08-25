# Federal Entity Map Phase 0-1 Receipt

Status: candidate, non-canonical implementation receipt for
`hummbl-io/hummbl-production#764`.

## Architecture decision

This phase adds an explicit entity and source-to-entity mapping layer over the
existing public-intelligence source registry. Source access, terms, rate-limit,
sensitivity, receipt, and ingestion metadata remains canonical in
`sources.registry.yaml` and is not duplicated here.

## Primary evidence retrieved 2026-07-18

- Office of the Law Revision Counsel, `5 U.S.C. 101`:
  https://uscode.house.gov/view.xhtml?edition=prelim&num=0&req=granuleid%3AUSC-prelim-title5-section101
  - Establishes the closed list and canonical names of 15 statutory executive
    departments.
  - Does not establish Cabinet rank, subordinate agencies, leadership,
    administration overlays, or a universal federal-agency count.
- Office of the Law Revision Counsel, `15 U.S.C. 78d`:
  https://uscode.house.gov/view.xhtml?edition=prelim&num=0&req=granuleid%3AUSC-prelim-title15-section78d
  - Establishes the Securities and Exchange Commission as a separately
    constituted five-member commission.
  - Does not classify the SEC as a `5 U.S.C. 101` department or establish EDGAR
    authority outside SEC-published records.
- Securities and Exchange Commission, current private-company guidance:
  https://www.sec.gov/files/sec-private-co-building-blocks.pdf
  - Describes the SEC as an independent federal agency headed by a five-member
    Commission.
  - Does not establish executive-department status or authority for third-party
    investment conclusions.

## Seed boundary

- 15 active `executive_department` entities, exactly matching `5 U.S.C. 101`.
- One nondepartment control entity: Securities and Exchange Commission, typed
  `independent_regulatory_commission`.
- One bounded link: `sec_edgar` to the SEC with role `data_api` and authority
  limited to SEC filings and SEC-published filing metadata.
- Candidate records only. No overlays, aliases, subordinate components, change
  history, routing matrix, adapters, ingestion, subscriptions, crawlers,
  scheduled-task changes, or runtime behavior changes.

Credential posture: no credentials, tokens, cookies, account identifiers, or
account-specific headers are recorded in this receipt.

## Local validation

Run from the repository root on 2026-07-18:

- `python3 scripts/test_validate_public_intelligence_sources.py` - PASS, 6
  tests.
- `python3 scripts/validate_public_intelligence_sources.py --quiet` - PASS.
- `python3 scripts/test_validate_federal_entities.py` - PASS, 6 tests.
- `python3 scripts/validate_federal_entities.py --quiet` - PASS: 15
  departments, 1 SEC control, and 1 bounded link.
- YAML parse check - PASS, 6 files.
- Prettier 3.9.4 - PASS.
- Ruff check and format check - PASS.
- Scoped gitleaks scan - PASS, no leaks.
- Generated claim-risk triage freshness gate - PASS, with zero true public-risk
  defects and 200 unchanged human-review candidates.
- New-validator statement coverage - 72%.
- `python -m pytest -q scripts` - PARTIAL: 245 passed and 6 subtests passed;
  4 pre-existing failures remain in untouched `scripts/test_validate_claims.py`
  fixtures because they omit the validator's current `status_definitions` and
  `summary.fixed` fields.
- Root pytest collection - BLOCKED by unrelated package-path errors under
  `hummbl-governed-quest-sim` (`governance.adapter` and
  `governance.scenarios` cannot be imported from the repository root).
