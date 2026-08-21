# Public / Private Boundary

Status: public boundary
Last updated: 2026-07-03

This repository may be used as a public collaboration surface. Public
collaboration requires clear boundaries.

## Public-Safe

The following are generally public-safe when reviewed:

- package source code intended for distribution;
- examples using synthetic or demo-only data;
- docs that describe package behavior;
- CI and validation receipts;
- issue and PR templates;
- public claim receipts;
- Apache license and notice information;
- vulnerability reporting instructions.

## Private Or Restricted

Do not publish:

- secrets, credentials, tokens, private keys, or local credential paths;
- customer, user, collaborator, or partner data;
- private strategy, pricing, negotiations, or unreleased business plans;
- raw bus logs, operator-only runbooks, or internal coordination transcripts;
- private infrastructure details unless intentionally disclosed and reviewed;
- production-mutating automation;
- screenshots, logs, or examples containing real sensitive content;
- unverified public claims presented as verified facts.

## Boundary Check

Before opening an issue, PR, discussion, release, or public claim, check:

1. Does this expose private data or private operations?
2. Does it include real credentials or credential-shaped material?
3. Does it imply HUMMBL endorsement, certification, or hosted-service support?
4. Does it make a factual claim without a receipt?
5. Does it use source-candidate research as if it were verified?
6. Does it include generated/vendor attribution prohibited by HUMMBL policy?

If any answer is uncertain, mark the item `needs-boundary-review` and do not
promote it until reviewed.
