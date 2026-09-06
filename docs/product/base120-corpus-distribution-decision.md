# Base120 Corpus Distribution Decision

Status: **HOLD for new public redistribution**; effective: 2026-09-05
Applies to: `@hummbl/mcp-base120` and later artifacts that embed the Base120 corpus

## Decision

Do not publish a new downloadable package that embeds the Base120 names,
codes, definitions, or transformation structure under the current rights
record. Keep `@hummbl/mcp-base120` private and `UNLICENSED` while the software
and corpus boundaries are reconciled.

The preferred product architecture separates the Apache-2.0 implementation
from the proprietary corpus. A future public client may contain interfaces and
transport code, while corpus access is supplied by a governed service under
approved terms. That hosted route is also a HOLD until its contract, privacy,
provenance, and rights reviews pass.

## Basis

- The repository's Base120 `NOTICE` distinguishes Apache-2.0 software from a
  proprietary structured corpus.
- [Apache-2.0](https://www.apache.org/licenses/LICENSE-2.0) grants broad rights
  for the work to which it is applied. It does not by itself establish which
  separate content assets HUMMBL intended to include in that licensed work.
- [npm's package manifest documentation](https://docs.npmjs.com/files/package.json/)
  defines `"license": "UNLICENSED"` and `"private": true` as the controls for
  an unpublished package that grants no package-use license and must not be
  published.

This record is an operational release decision, not a new license or legal
opinion. It does not retroactively characterize existing website or package
exposures. Those exposures require a separate inventory and counsel-reviewed
rights reconciliation.

## Exit criteria

Before any manifest changes to `public_launch: true`:

1. Counsel-approved terms define the software, corpus, trademarks, permitted
   use, and redistribution rights without contradiction.
2. The distributable artifact contains only content approved for that channel,
   or the corpus is removed behind the governed service boundary.
3. Release provenance, hosted-contract parity, and privacy review are complete.
4. The product manifest is changed to `admit` with no remaining blockers and
   passes the repository admission validator.
