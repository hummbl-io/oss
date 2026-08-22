# HMIK v0.0.4 Engineering Receipt

**Recorded:** 2026-08-14
**Lane:** `codex`, host `<machine>`, surface `desktop-codex`
**Disposition:** ready for human review; not canonical

## Authority and scope

The operator approved preserving the existing TierShift architecture, renaming
the semantic successor, defining correction authority and fail-closed profile
routing, and preparing one integration change. This receipt does not interpret
that approval as public-release or canonization authority.

## Content-addressed artifacts

| Artifact | SHA-256 |
| --- | --- |
| `HUMMBL-Mandate-Integrity-Kernel-v0.0.4-candidate.md` | `87710EBE22D97A77B02FF97481CE30C2EFFF1BD4F305D58C482EA95F5B4D1C73` |
| `HUMMBL-Mandate-Integrity-Kernel-Conformance-v0.0.1.md` | `6A907C8B2C9883C7F5881ABB0B2B640C592B226CF96A34666BCC0A59F8BDD6D2` |
| `ADR-010-separate-mandate-integrity-kernel-from-tiershift.md` | `67E9FC3BA8DAAE73F5800C4DC2E56297DC6831943D055D78386154A51DA420FD` |

## Findings disposition

| Prior finding | v0.0.4 disposition |
| --- | --- |
| Name collision with TierShift | Resolved by separate HMIK identity and explicit non-relationship |
| Undefined correction acceptance/authority | Resolved by distinct correction assertion and authorized correction decision |
| Unselected “correct routing” | Resolved by kernel reject/unresolved behavior and exact selected-profile requirement |
| Profiles could reintroduce rejected mechanisms | Constrained by threat model, finding disposition, negative cases, rollback, and acceptance evidence; profile safety still requires profile-specific review |
| Transcript-derived raw-review provenance | Preserved as a stated evidence limitation; not upgraded to dispatch-verbatim provenance |

## Validation evidence

Structural validation passed with:

```text
K invariants: 12
paired positive cases: 12
paired counterexamples: 12
cross-cutting routing cases: 3
representation mappings: 2
git diff --check: clean
```

A current exact-name search found no obvious GitHub collision; both queried
PyPI project endpoints returned not found. This is a namespace check only, not
legal or trademark clearance.

## Remaining gate

The v0.0.4 candidate deliberately leaves the kernel's human engineering review
gate pending. Acceptance of this review branch does not itself make HMIK
canonical. Canonization requires an explicit later decision after review finds
no unresolved normative contradiction.
