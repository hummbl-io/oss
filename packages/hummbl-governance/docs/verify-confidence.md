# verify-confidence

Status: planned gate
Last updated: 2026-07-03

`verify-confidence` is a planned verification gate for hummbl-governance changes.
It is not implemented automation yet.

## Purpose

Classify a change, require the right checks, collect receipts, and return a
human-readable disposition:

```text
diff -> risk classifier -> required checks -> receipt collection -> PASS/WARN/BLOCK
```

## Non-Goals

- Do not replace human review.
- Do not bypass CI, security review, or maintainer approval.
- Do not claim confidence scores without receipts.
- Do not mutate package publishing, repo settings, or external systems.

## Change Classes

| Change class | Required receipts |
|---|---|
| Code | Unit/integration tests, coverage where applicable, lint, security review for sensitive paths |
| Public API | Tests, API compatibility note, changelog or migration note when needed |
| Package/release | Build, wheel install smoke, metadata check, rollback path |
| Docs | Link check, public/private boundary check, claim receipt check |
| Public claims | Claim ledger update, source receipt, license/trademark/brand boundary check |
| Governance policy | Boundary review, adversarial review, operator approval when consequential |
| MCP/tooling | Tool schema review, allowed/forbidden action review, dry-run or fixture receipt |
| Examples/demo | Synthetic-data check, secret scan, quickstart execution receipt |

## Dispositions

`PASS`: Required receipts are present and no blockers remain.

`WARN`: Work may proceed only with explicit limitations, follow-up, or waiver.

`BLOCK`: Missing receipt, unsafe boundary, failing check, unverified public
claim, or unresolved security/legal/package risk blocks promotion.

## Minimum Output

A future implementation should emit:

- commit or diff identifier;
- changed files;
- inferred change class;
- required checks;
- observed receipts;
- missing receipts;
- public/private boundary result;
- claim-ledger result;
- disposition;
- reviewer notes.

## First Manual Use

Until automated, reviewers should apply this doc manually to:

1. README and public claim edits.
2. Release/package metadata edits.
3. Security policy edits.
4. Governance and boundary docs.
5. MCP or tool-surface changes.
