# TierShift Declaration Gate

Status: candidate gate definition for issue #156.
Last updated: 2026-07-03.

`TierShift` remains a candidate public term. This document defines a draft
declaration gate for high-consequence PRs and issues; it does not approve public
product naming, CI enforcement, release behavior, or automatic execution.

## Purpose

The TierShift declaration gate forces explicit routing when work touches
high-consequence surfaces:

- namespace, lexicon, or candidate term ledgers;
- governance primitives or gates;
- public docs, package metadata, or source-of-record artifacts;
- schema identifiers, migrations, or compatibility surfaces;
- security posture, credentials, private mesh details, or release workflows;
- agent routing policy;
- clinical, legal, financial, or other high-consequence claim surfaces.

## Required Declaration

```yaml
tier_shift_declaration:
  selected_tier: Instant|Medium|High|XHigh|Hold
  consequence_surface:
    - public_docs
    - namespace
    - schema
    - package_metadata
  rationale: "Why this tier matches the consequence surface"
  receipts_required:
    - source_of_record
    - operator_approval
    - peer_review
  downgrade_allowed: true
  escalation_conditions:
    - public_use_or_package_name_detected
    - schema_breaking_change_detected
    - security_sensitive_surface_detected
```

## Tier Semantics

| Tier | Meaning | Gate posture |
|---|---|---|
| `Instant` | Low consequence; reversible; no shared authority change. | Record rationale and validation. |
| `Medium` | Reviewable shared docs or local governance wording. | Require source-of-record and peer-review route. |
| `High` | Public docs, metadata, schema, or governance primitive surface. | Require operator or delegated approval plus non-author review. |
| `XHigh` | Security, release, package, legal/clinical/financial, or authority-changing surface. | Require explicit approval, non-author review, receipt, and hold option. |
| `Hold` | Evidence, authority, source-of-record, or reviewer capacity is insufficient. | Do not promote or merge until the blocker is resolved. |

TierShift is not an intelligence ranking. It is a consequence and routing
posture. Downgrade remains allowed when evidence shows the actual consequence is
lower than first assumed.

## Trigger Gates

| Gate | Purpose | Pass condition | Fail condition |
|---|---|---|---|
| `G-NAMESPACE-AUDIT` | Avoid premature public term promotion. | Candidate or approved namespace status is recorded. | Public term is introduced as canon without audit. |
| `G-TIERSHIFT-DECLARED` | Force explicit consequence routing. | Declaration exists for triggered surfaces. | PR or issue touches a trigger surface with no declaration. |
| `G-CONSEQUENCE-SURFACE-MATCH` | Prevent under-tiering. | Selected tier matches changed surfaces and risk. | Security, schema, release, or public-claim work is declared too low. |
| `G-NO-SELF-APPROVAL` | Avoid author-only approval of high-consequence work. | High/XHigh declarations have non-author review or operator approval. | Author approves their own high-consequence declaration. |
| `G-SOURCE-OF-RECORD` | Keep authority anchored. | Source-of-record artifact, issue, PR, or operator instruction is identified. | Declaration relies on memory or implied context alone. |
| `G-RECEIPT-EMITTED` | Preserve auditability. | Receipt records declaration, validation, reviewer route, and residual risk. | No durable declaration receipt exists. |

## Fail / Warn / Pass Behavior

| Situation | Result | Required action |
|---|---|---|
| No trigger surface touched | `pass` | No declaration required; optional note allowed. |
| Trigger surface touched with complete declaration | `pass` | Continue normal review flow. |
| Declaration exists but tier may be too low | `warn` | Reviewer must either raise tier or record downgrade rationale. |
| High/XHigh surface self-approved by author | `fail` | Add non-author review or operator approval. |
| Source of record missing | `fail` | Hold until authority and evidence are identified. |
| Reviewer capacity unavailable | `Hold` | Keep draft or blocked until capacity exists. |

## Examples

| Example | Declaration |
|---|---|
| Fix typo in non-canonical docs page | `Instant`; no shared authority change. |
| Add candidate gate definition doc | `Medium`; source issue and review comment required. |
| Add schema identifier or package metadata wording | `High`; source-of-record and non-author review required. |
| Modify release workflow, credential policy, or public legal/clinical claim | `XHigh`; explicit approval, review, receipt, and hold option required. |

## Related References

- hummbl-io/hummbl-production#540: candidate namespace audit.
- hummbl-io/hummbl-production#541: namespace source-of-record draft PR.
- hummbl-io/hummbl-production#560: HUMMBL TierShift governed execution-intensity architecture.
- hummbl-io/hummbl-governance#1185: Ownward TierShift coaching application.
- hummbl-io/hummbl-music#2: HUMMBL TierShift sound family.

## Out of Scope

- No CI behavior change.
- No bot enforcement.
- No public product naming approval.
- No merge or release policy mutation.
- No automatic execution escalation.
