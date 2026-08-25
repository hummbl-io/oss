# ADR-009 — AI vendor IP risk register

- **Status:** proposed
- **Date:** 2026-06-30
- **Decision owner:** Reuben Bowlby
- **Steward:** HUMMBL Research Institute
- **Supersedes:** none
- **Superseded by:** none

## Context

ADR-008 separates AI assistance from Git authorship provenance. That protects repository metadata, but it does not decide which AI vendors and product tiers are acceptable for IP-sensitive work.

Different products from the same vendor can carry materially different training, retention, human-review, and output-ownership terms. Consumer/free surfaces are not equivalent to API, business, enterprise, or cloud-contract surfaces.

## Decision

Add `docs/standards/AI_VENDOR_IP_RISK_REGISTER.md` as the governed register for AI vendor IP risk. The register classifies vendors and product tiers as RED, YELLOW, or GREEN for HUMMBL work tiers.

Default rule: unreviewed vendor = RED for Tier 2/Tier 3 work.

The HUMMBL Repo Standard now requires AI vendors and agent tools to be classified in the register before use on Tier 2/Tier 3 work.

## Enforcement

Add `tools/vendor_ip_risk_lint.py`, a stdlib-only validator for the register. It checks:

- risk values are RED, YELLOW, or GREEN
- every row has source URLs or `REVIEW_REQUIRED`
- `last reviewed` fields are ISO dates
- RED vendors are not allowed for Tier 2/Tier 3
- YELLOW vendors allowing Tier 2/Tier 3 require owner-approval language

## Consequences

- Vendor policy becomes explicit instead of implicit.
- Sensitive projects such as PeptideCheck default to deny until terms are reviewed.
- Agent IDEs and workspace-context products remain RED until their terms and controls are captured.
- Register entries can evolve as enterprise terms, data controls, and indemnity posture change.

## Receipts

- Add/approve the associated PR and KRINEIA receipt in accordance with standard amendment requirements.
