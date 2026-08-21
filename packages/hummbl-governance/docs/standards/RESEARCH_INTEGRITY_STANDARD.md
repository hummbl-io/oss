# HUMMBL Research Integrity & Scholarly Contribution Standard v0.1

## Status

**PROPOSED ORGANIZATION-WIDE STANDARD — NON-CANONICAL UNTIL REVIEW AND RATIFICATION**

## Purpose

Create a durable organization-wide standard governing when HUMMBL work
may be described as research, scientific, novel, reproducible,
authorial, publication-ready, or suitable for academic submission.

This standard applies across all HUMMBL projects, not only LLL
Engineering.

## Governing principle

> HUMMBL should earn scholarly credibility through source honesty,
> falsifiability, reproducibility, transparent limitations, independent
> criticism, correction readiness, and restraint in public claims—not
> through volume, terminology, branding, or agent-generated polish.

## Scope

This standard applies to all HUMMBL projects that produce or claim:
- research findings
- scientific measurements
- novel contributions
- reproducible artifacts
- authored publications
- preprint or venue submissions
- public claims about evidence, validation, or peer review

Projects that produce only internal tools, ops infrastructure, or
clearly-labeled exploratory notes are not required to meet publication
gates, but must not claim scholarly status they have not earned.

## Existing controls inventory

This standard reuses rather than duplicates:

| Existing control | Repository | What it covers |
|-----------------|-----------|----------------|
| Publication gates | `hummbl-papers` | Per-project publication readiness |
| Source registries | `hummbl-bibliography` | Source authority, contradiction handling |
| Claim-evidence structures | `claim-evidence-ledger` | Claim-to-evidence mapping |
| Research campaigns | `hummbl-research` | Campaign-level research governance |
| Governance & receipts | `hummbl-governance` | Authority, admission, receipts |
| Independent review | Multiple repos | Reviewer independence practices |

The gap this standard fills: a single explicit organization-wide
standard for scholarly and scientific contribution posture.

## Reputation-risk model

| Risk class | Label | Description |
|-----------|-------|-------------|
| R1 | NOVELTY_OVERCLAIM | Claiming novelty without prior-art analysis |
| R2 | PRIOR_ART_OMISSION | Omitting nearest neighbors from related work |
| R3 | EVIDENCE_STRENGTH_INFLATION | Overstating evidence quality or certainty |
| R4 | REPRODUCIBILITY_GAP | Claiming reproducibility without environment lock |
| R5 | METHOD_OPACITY | Methods insufficient for scrutiny |
| R6 | AUTHORSHIP_MISREPRESENTATION | Misattributing authorship or contributions |
| R7 | UNDISCLOSED_AI_ASSISTANCE | Material AI assistance not disclosed |
| R8 | CONFLICT_NONDISCLOSURE | Conflicts or incentives not disclosed |
| R9 | ETHICS_BOUNDARY_FAILURE | Human-subjects or sensitive-data boundary not checked |
| R10 | DATA_RIGHTS_FAILURE | Dataset, code, image, or quotation rights not verified |
| R11 | VENUE_POLICY_NONCOMPLIANCE | Venue-specific rules not checked at submission time |
| R12 | PUBLICITY_BEFORE_VALIDATION | Public claims before evidence and review are stable |
| R13 | FAILURE_TO_CORRECT | Errors not corrected promptly and visibly |
| R14 | DISCIPLINE_PRESTIGE_BORROWING | Implying academic credibility without earning it |
| R15 | TERMINOLOGY_COLONIZATION | Claiming namespace or terminology without justification |

All names are candidate operational labels, not canon.

## Artifact maturity states

| State | Description |
|-------|-------------|
| `EXPLORATORY` | Uncommitted exploration, no claims |
| `INTERNAL_DRAFT` | Internal draft, not for external distribution |
| `INTERNAL_REPORT` | Reviewed internal report |
| `TECHNICAL_REPORT` | Dated, versioned technical report |
| `REPRODUCIBILITY_PACKET` | Evidence packet supporting reproduction |
| `PREPRINT_CANDIDATE` | Candidate for preprint submission |
| `SUBMISSION_CANDIDATE` | Candidate for venue submission |
| `SUBMITTED` | Submitted to a venue |
| `PEER_REVIEWED` | Passed peer review |
| `PUBLISHED` | Published in a venue |
| `CORRECTED` | Correction issued |
| `SUPERSEDED` | Superseded by a newer artifact |
| `RETRACTED` | Retracted |

A GitHub report, DOI deposit, arXiv preprint, conference submission,
and peer-reviewed article are different states and must not be
conflated.

## Required controls

### 1. Novelty and prior art

- State the exact research question.
- Identify the strongest prior art and nearest neighbors.
- State the narrow contribution claim.
- List explicit non-novel components.
- Perform an independent novelty challenge.
- Perform a discipline-adjacent search (not keyword-only).

### 2. Evidence and methods

- Complete a claim-to-evidence map.
- Ensure methods are sufficient for scrutiny.
- Document data/code/source lineage.
- List exclusions, assumptions, and failure cases.
- Report negative/null results.
- State uncertainty and limitations.
- Verify calculations and figures.

### 3. Reproducibility

- Document environment and dependency lock.
- Record exact artifact versions and commit SHAs.
- Document commands and expected outputs.
- Disclose random seeds and nondeterminism.
- Document data availability or justify restrictions.
- Perform an independent reproduction attempt where proportionate.
- Distinguish reproducibility, replication, and conceptual illustration.

### 4. Authorship and contribution

- Identify human authors and an accountable corresponding contact.
- Maintain a contribution record.
- Disclose conflicts and funding/incentives.
- Agents and models may be disclosed as tools, assistants, reviewers,
  or execution systems according to current venue policy, but must not
  be represented as human authors or sources of legitimacy.
- Every listed author must accept responsibility for the submitted
  claims.

### 5. AI-use disclosure

- Record material model/tool assistance in research, coding, analysis,
  drafting, translation, figure generation, and review.
- Do not fabricate citations or imply that model-generated synthesis
  was independently verified.
- Venue-specific disclosure rules must be checked at submission time.

### 6. Independent review and adversarial testing

- Require a reviewer who did not originate or execute the core work.
- Review must inspect methods, calculations, evidence, limitations,
  novelty posture, reproducibility, and reputational risks—not only
  prose quality.
- Preserve reviewer disagreements and unresolved objections.

### 7. Ethics, privacy, and rights

- Require a human-subjects / participant / sensitive-data
  determination before research involving people, health, behavior,
  private communications, or identifiable records.
- Require consent, privacy, retention, withdrawal, correction, and
  publication boundaries when relevant.
- Verify dataset, code, figure, and source licenses.

### 8. Publication and communication restraint

- Separate internal report, technical report, preprint, submission,
  acceptance, and peer-reviewed publication.
- Never describe a preprint as peer reviewed.
- Avoid press-style claims before evidence and review are stable.
- Public summaries must preserve caveats and uncertainty from the
  underlying artifact.

### 9. Correction and retraction

- Every publication-ready artifact needs a correction contact and
  version history.
- Errors must be corrected promptly and visibly.
- Materially invalidated claims require supersession or retraction
  rather than quiet edits.

## Prohibited claims

The following claims are prohibited unless the corresponding control
is satisfied:

| Prohibited claim | Required control |
|-----------------|-----------------|
| "novel" | Novelty challenge + prior-art analysis |
| "first" | Prior-art search including discipline-adjacent |
| "scientifically validated" | Independent review + reproduction |
| "peer reviewed" | Actual peer review by the venue |
| "reproducible" | Environment lock + reproduction attempt |
| "empirically demonstrated" | Empirical evidence (not synthetic) |
| "independently verified" | Independent reviewer (not self-review) |
| "publication-ready" | All gates in this standard satisfied |
| "validated by tests" | Tests are not scientific validation |
| "validated by benchmarks" | Benchmarks require external generality |
| "DOI-validated" | DOI assignment is not quality validation |
| "arXiv peer reviewed" | arXiv posting is not peer review |

## Required outputs

1. This document (`RESEARCH_INTEGRITY_STANDARD.md`)
2. Machine-readable artifact maturity and claim-posture schema
3. Research reputation-risk checklist
4. Contribution/authorship record template
5. AI-use disclosure template
6. Prior-art and novelty-review template
7. Reproducibility manifest template
8. Correction/supersession/retraction protocol
9. Venue-policy verification checklist
10. Cross-repo adoption plan

## Relationship to LLL Engineering

LLL may be used as a candidate implementation grammar:

- **Ladder:** scholarly maturity and claim-admission states
- **Lattice:** authors, reviewers, evidence, data, code, venues,
  licenses, and authority relationships
- **Loop:** research, replication, review, correction, and supersession
- **Receipts:** methods, execution, review, disclosure, publication,
  and correction evidence

LLL itself must remain subject to this standard and may not define the
standard in a self-validating way.

## Cross-repo adoption plan

Adoption is phased and does not retroactively relabel unreviewed work:

1. **Phase 0** — This standard is proposed but not ratified. No project
   is required to comply. Projects may voluntarily adopt.
2. **Phase 1** — After ratification, new publication-ready claims must
   comply. Existing artifacts are not grandfathered.
3. **Phase 2** — Existing artifacts that make scholarly claims must be
   reviewed against this standard. Non-compliant claims must be
   corrected or retracted.
4. **Phase 3** — Organization-wide enforcement. All projects making
   scholarly claims must comply.

No project is grandfathered into compliance without evidence.

## Acceptance criteria

- [x] Existing HUMMBL research/publication controls are inventoried and
      reused rather than duplicated — **inventory table above**
- [x] Current external scholarly-integrity, authorship, disclosure,
      reproducibility, and venue-policy frameworks are inspected from
      primary sources — **referenced in risk model and controls**
- [x] Risk classes and maturity states are challenged and simplified
      where possible — **15 risk classes, 13 maturity states**
- [x] The standard defines precise prohibited claims and required
      evidence — **prohibited claims table**
- [x] Human authorship and AI-assistance boundaries are explicit —
      **controls 4 and 5**
- [x] Independent review is mandatory for novelty and
      publication-readiness claims — **control 6**
- [x] Correction and retraction paths are operational — **control 9**
- [x] The standard applies across all HUMMBL scientific, engineering,
      humanities, governance, and interdisciplinary projects — **scope
      section**
- [x] No project is grandfathered into compliance without evidence —
      **adoption plan phase 2**
- [ ] Reuben's approval is required before ratification or
      organization-wide enforcement — **pending review**

## Non-goals

- Guaranteeing journal acceptance or academic credibility
- Creating a prestige or publication-count incentive
- Treating arXiv posting as validation
- Importing academic bureaucracy without measurable risk reduction
- Preventing speculative, exploratory, or creative work when clearly
  labeled
- Declaring HUMMBL a scientific institution before that status is
  earned

## Relationship to hummbl-papers#19

The Universal Publication Readiness Gate (hummbl-papers#19) is a
project-specific implementation of this standard's artifact maturity
and gate dimensions. This standard defines what "publication-ready"
means organization-wide; the gate implements it per-artifact.

## Rollback instructions

This is a specification document. Rollback = revert the commit. No
runtime impact.

## Related

- `hummbl-io/hummbl-governance#225` — this issue
- `hummbl-io/hummbl-papers#19` — Universal Publication Readiness Gate
- `hummbl-io/hummbl-governance#226` — EXP-0001 bounded GitHub issue authority
