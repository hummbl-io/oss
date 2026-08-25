# ADR-010 - Separate Mandate Integrity Kernel from TierShift

- **Status:** accepted
- **Date:** 2026-08-14
- **Decision owner:** Reuben Bowlby
- **Steward:** HUMMBL Research Institute
- **Supersedes:** none
- **Superseded by:** none
- **Related:** historical ADR-TS-002 review artifact

## Context

The v0.0.3 TierShift Semantic Kernel extracted useful source-to-mandate and
evidence-to-decision semantics from a rejected monolith. HUMMBL already uses
TierShift for a different architecture: governed execution-intensity selection
and transition. Reusing the name would create two incompatible meanings for a
single system identity.

Engineering review also found that v0.0.3 did not define who makes a correction
effective and allowed "correct routing" without requiring a selected profile.

## Decision

1. Preserve the existing TierShift execution-intensity architecture unchanged.
2. Continue the extracted semantic work as the **HUMMBL Mandate Integrity
   Kernel (HMIK)**.
3. Publish a standalone v0.0.4 candidate rather than modifying the immutable
   v0.0.3 artifact.
4. Separate correction assertion from authorized correction decision.
5. Permit `PROFILE_REQUIRED` routing only through an exact selected,
   versioned profile; kernel-only processing rejects or preserves unresolved
   inputs.
6. Treat profile declarations as claims requiring threat-model and conformance
   evidence, not as automatic acceptance.

## Consequences

- Existing TierShift documentation and consumers retain their current meaning.
- Earlier review artifacts remain historical evidence under their original
  names and hashes.
- HMIK remains a candidate until its corpus and human review gates pass.
- This ADR does not authorize public branding, package publication, or
  canonization.
