# HUMMBL Research Integrity & Scholarly Contribution Standard v0.1

**Status: PROPOSED ORGANIZATION-WIDE STANDARD — NON-CANONICAL UNTIL REVIEW AND RATIFICATION**

Issue: hummbl-io/hummbl-governance#225
Parent program: hummbl-io/hummbl-dev#153

## Purpose

Create a durable organization-wide standard governing when HUMMBL work may be described as research, scientific, novel, reproducible, authorial, publication-ready, or suitable for academic submission.

This standard applies across all HUMMBL projects, not only LLL Engineering.

## Governing principle

> HUMMBL should earn scholarly credibility through source honesty, falsifiability, reproducibility, transparent limitations, independent criticism, correction readiness, and restraint in public claims—not through volume, terminology, branding, or agent-generated polish.

## Reputation-risk model

```text
R1 — NOVELTY_OVERCLAIM
R2 — PRIOR_ART_OMISSION
R3 — EVIDENCE_STRENGTH_INFLATION
R4 — REPRODUCIBILITY_GAP
R5 — METHOD_OPACITY
R6 — AUTHORSHIP_OR_CONTRIBUTION_MISREPRESENTATION
R7 — UNDISCLOSED_AI_ASSISTANCE
R8 — CONFLICT_OR_INCENTIVE_NONDISCLOSURE
R9 — ETHICS_OR_HUMAN_SUBJECTS_BOUNDARY_FAILURE
R10 — DATA_RIGHTS_PRIVACY_OR_LICENSE_FAILURE
R11 — VENUE_POLICY_NONCOMPLIANCE
R12 — PUBLICITY_BEFORE_VALIDATION
R13 — FAILURE_TO_CORRECT_OR_RETRACT
R14 — DISCIPLINE_PRESTIGE_BORROWING
R15 — TERMINOLOGY_OR_NAMESPACE_COLONIZATION
```

All names are candidate operational labels, not canon.

## Maturity ladder

```text
IDEA
→ RESEARCH_NOTE
→ SOURCE-GROUNDED_CANDIDATE
→ INTERNAL_TECHNICAL_REPORT
→ REPRODUCIBLE_REPORT
→ PREPRINT_CANDIDATE
→ SUBMISSION_CANDIDATE
→ SUBMITTED
→ PEER_REVIEWED
→ CORRECTED / SUPERSEDED / RETRACTED
```

No project may skip states merely because the writing appears polished.

## Claim posture

Every scholarly artifact must distinguish:

```text
OBSERVATION
MEASUREMENT
EXPERIMENTAL_RESULT
INFERENCE
HYPOTHESIS
DESIGN_PROPOSAL
NORMATIVE_ARGUMENT
THEORETICAL_CLAIM
NOVELTY_CLAIM
EXTERNAL_FACT
UNVERIFIED
```

A project must not use "scientific," "validated," "proven," "novel," "state of the art," "formal," "general," or "reproducible" without an explicit gate defining what evidence warrants that term.

## Required controls

### 1. Prior-art and novelty discipline

- Search adjacent disciplines, not only the project's preferred vocabulary
- Record direct neighbors, partial precedents, convergent work, and disconfirming sources
- State novelty narrowly and compositionally
- Prefer "we did not find" over "no prior work exists"
- Require an independent novelty challenge before public novelty claims

### 2. Methods and reproducibility

- Preserve exact methods, versions, environments, data lineage, prompts where relevant, seeds, exclusions, and failure cases
- Separate executable reproducibility from conceptual replicability
- Preserve negative and null results
- State which parts cannot be reproduced and why

### 3. Authorship and contribution

- Human authorship and responsibility must be explicit
- Agents and models may be disclosed as tools, assistants, reviewers, or execution systems according to current venue policy, but must not be represented as human authors or sources of legitimacy
- Maintain a contribution record suitable for later mapping to a recognized contribution taxonomy
- Every listed author must accept responsibility for the submitted claims

### 4. AI-use disclosure

- Record material model/tool assistance in research, coding, analysis, drafting, translation, figure generation, and review
- Do not fabricate citations or imply that model-generated synthesis was independently verified
- Venue-specific disclosure rules must be checked at submission time

### 5. Independent review and adversarial testing

- Require a reviewer who did not originate or execute the core work
- Review must inspect methods, calculations, evidence, limitations, novelty posture, reproducibility, and reputational risks—not only prose quality
- Preserve reviewer disagreements and unresolved objections

### 6. Ethics, privacy, and rights

- Require a human-subjects / participant / sensitive-data determination before research involving people, health, behavior, private communications, or identifiable records
- Require consent, privacy, retention, withdrawal, correction, and publication boundaries when relevant
- Verify dataset, code, figure, and source licenses

### 7. Publication and communication restraint

- Separate internal report, technical report, preprint, submission, acceptance, and peer-reviewed publication
- Never describe a preprint as peer reviewed
- Avoid press-style claims before evidence and review are stable
- Public summaries must preserve caveats and uncertainty from the underlying artifact

### 8. Correction and retraction

- Every publication-ready artifact needs a correction contact and version history
- Errors must be corrected promptly and visibly
- Materially invalidated claims require supersession or retraction rather than quiet edits

## Required outputs

1. `RESEARCH_INTEGRITY_STANDARD.md` or equivalent
2. Machine-readable artifact maturity and claim-posture schema
3. Research reputation-risk checklist
4. Contribution/authorship record template
5. AI-use disclosure template
6. Prior-art and novelty-review template
7. Reproducibility manifest template
8. Correction/supersession/retraction protocol
9. Venue-policy verification checklist with current-policy lookup required at submission time
10. Cross-repo adoption plan that does not retroactively relabel unreviewed work as compliant

## Relationship to LLL Engineering

LLL may be used as a candidate implementation grammar:

- **Ladder:** scholarly maturity and claim-admission states
- **Lattice:** authors, reviewers, evidence, data, code, venues, licenses, and authority relationships
- **Loop:** research, replication, review, correction, and supersession
- **Receipts:** methods, execution, review, disclosure, publication, and correction evidence

LLL itself must remain subject to this standard and may not define the standard in a self-validating way.

## Acceptance criteria

- [x] Risk classes documented (15)
- [x] Maturity ladder documented (10 states)
- [x] Claim posture documented (11 types)
- [x] 8 required controls documented
- [x] 10 required outputs listed
- [x] LLL relationship documented
- [ ] Existing HUMMBL research/publication controls inventoried
- [ ] Current external frameworks inspected from primary sources
- [ ] Machine-readable schema implemented
- [ ] Templates implemented
- [ ] Cross-repo adoption plan
- [ ] Reuben ratification

## Non-goals

- Guaranteeing journal acceptance or academic credibility
- Creating a prestige or publication-count incentive
- Treating arXiv posting as validation
- Importing academic bureaucracy without measurable risk reduction
- Preventing speculative, exploratory, or creative work when clearly labeled

## Related

- `hummbl-io/hummbl-dev#153` — master program index
- `hummbl-io/hummbl-papers#19` — Universal Publication Readiness Gate
- `hummbl-io/hummbl-papers#20` — LLL scholarly contribution program
- `hummbl-io/hummbl-governance#220` — constitutional integrity remediation

## Fact posture

This is a proposed standard derived from issue #225. It is non-canonical until reviewed and ratified by Reuben Bowlby. No claims about existing implementation beyond what is documented in the issue.

## Receipt

- **Issue**: hummbl-io/hummbl-governance#225
- **Risk classes**: 15
- **Maturity states**: 10
- **Claim postures**: 11
- **Required controls**: 8
- **Required outputs**: 10
- **Non-goals**: 5
- **Review status**: PENDING — requires Reuben ratification
