# BaseN x Levin Crosswalk v0.1

**Status:** `APPROVED_RESEARCH_CROSSWALK_NOT_CANON`
**Issue:** [hummbl-production#751](https://github.com/hummbl-io/hummbl-production/issues/751)
**Parent research packet:** [hummbl-research#65](https://github.com/hummbl-io/hummbl-research/issues/65)
**Prior-art record:** [hummbl-bibliography#91](https://github.com/hummbl-io/hummbl-bibliography/issues/91)
**Approved by:** Operator, 2026-07-11

## What this is

A source-grounded comparative semantic analysis between Michael Levin's
diverse-intelligence framework and the verified current HUMMBL/Base120/BaseN
lexicon. The crosswalk documents where Levin's experimentally grounded
constructs illuminate existing HUMMBL distinctions, where similarities are
only analogical, where the systems disagree, and which apparent matches are
terminology collisions rather than substantive equivalences.

## What this is not

- Not canon. No new BaseN transformation, Base120 model, or Domain120 set is
  promoted by this document.
- Not scientific validation of HUMMBL. Scientific analogy is not validation.
- Not a term adoption proposal. Each row carries a `proposed_action` field;
  none authorize canon promotion without separate approval.
- Not a substitute for the bibliography prior-art record
  (`hummbl-bibliography#91`, still open). Where attribution is unresolved,
  rows carry `INSUFFICIENT_EVIDENCE` rather than a confident disposition.

## Files

| File                              | Purpose                                                                                                                        |
| --------------------------------- | ------------------------------------------------------------------------------------------------------------------------------ |
| `README.md`                       | This file. Orientation and status.                                                                                             |
| `hummbl-source-inventory.md`      | Canonical HUMMBL/Base120/BaseN constructs used by the crosswalk, with authority locators.                                      |
| `levin-source-inventory.md`       | Levin-side constructs with primary-source locators and attribution posture.                                                    |
| `crosswalk-matrix.md`             | Full crosswalk matrix. One row per Levin construct, with disposition, non-equivalence, translation risk, and proposed action.  |
| `collision-attribution-report.md` | Terminology collisions, attribution obligations, and terms HUMMBL should cite, avoid, or treat as general scientific language. |
| `rejected-mappings.md`            | Mappings considered and rejected, with reasons.                                                                                |
| `namespace-audit.yaml`            | Namespace audit for any proposed new term. Machine-readable.                                                                   |
| `receipt.yaml`                    | Machine-readable receipt linking source claims, crosswalk rows, and downstream issues.                                         |

## Disposition vocabulary

Every crosswalk row receives exactly one primary disposition:

| Disposition             | Meaning                                                                           |
| ----------------------- | --------------------------------------------------------------------------------- |
| `MATCH`                 | Substantive equivalence with verified sources on both sides.                      |
| `PARTIAL_MATCH`         | Overlap on core structure; divergence on scope, evidence, or operational purpose. |
| `STRUCTURAL_ANALOGY`    | Similar shape (hierarchy, feedback, boundary) without semantic equivalence.       |
| `TERMINOLOGY_COLLISION` | Same or similar name, different meaning. Do not conflate.                         |
| `TENSION`               | The systems disagree in a way that creates design or governance friction.         |
| `NO_EQUIVALENT`         | No HUMMBL-side construct maps meaningfully.                                       |
| `INSUFFICIENT_EVIDENCE` | Cannot resolve disposition because source attribution is unresolved.              |
| `OUT_OF_SCOPE`          | Levin construct has no operational relevance to governed agent systems.           |

## Promotion gates

A mapping may be promoted beyond research only when:

1. The Levin-side construct has an exact primary-source locator.
2. The HUMMBL-side construct has a verified current authority locator.
3. Non-equivalence has been explicitly documented.
4. No earlier or broader prior art has been misattributed.
5. The mapping produces testable operational value.
6. Adversarial review does not find anthropomorphism, category error, or semantic capture.
7. Promotion is separately approved.

**No row in this crosswalk satisfies all seven gates.** This is a v0.1
research artifact, not a promotion proposal.

## Review status

- [ ] Independent review by one scientific-grounding reviewer.
- [ ] Independent review by one HUMMBL semantic-integrity reviewer.
- [ ] Closure approval by Operator.

Until both reviews are recorded, this crosswalk is `DRAFT_NOT_PROMOTED`.

## Provenance

Created 2026-07-21 by devin (research lane) on branch
`research/opencode/levin-crosswalk-v01`. Source artifacts: `api/src/base120.ts`
(SHA `5800ea8712b5e1a1b64d3e1687aab92b1895a78e`), public glossary pages, and
the open prior-art record at `hummbl-bibliography#91`.
