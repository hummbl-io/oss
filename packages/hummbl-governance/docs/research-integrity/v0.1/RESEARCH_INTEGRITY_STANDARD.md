# HUMMBL Research Integrity and Scholarly Contribution Standard v0.1

**Status: PROPOSED ORGANIZATION-WIDE STANDARD — NON-CANONICAL UNTIL REVIEW AND RATIFICATION**

Issue: hummbl-io/hummbl-governance#225

## Governing principle

> HUMMBL should earn scholarly credibility through source honesty,
> falsifiability, reproducibility, transparent limitations, independent
> criticism, correction readiness, and restraint in public claims —
> not through volume, terminology, branding, or agent-generated polish.

## Scope

This standard applies across all HUMMBL projects, not only LLL
Engineering. It governs when HUMMBL work may be described as research,
scientific, novel, reproducible, authorial, publication-ready, or
suitable for academic submission.

## Reputation-risk model

| Label | Risk |
|-------|------|
| R1 | NOVELTY_OVERCLAIM |
| R2 | PRIOR_ART_OMISSION |
| R3 | EVIDENCE_STRENGTH_INFLATION |
| R4 | REPRODUCIBILITY_GAP |
| R5 | METHOD_OPACITY |
| R6 | AUTHORSHIP_OR_CONTRIBUTION_MISREPRESENTATION |
| R7 | UNDISCLOSED_AI_ASSISTANCE |
| R8 | CONFLICT_OR_INCENTIVE_NONDISCLOSURE |
| R9 | ETHICS_OR_HUMAN_SUBJECTS_BOUNDARY_FAILURE |
| R10 | DATA_RIGHTS_PRIVACY_OR_LICENSE_FAILURE |
| R11 | VENUE_POLICY_NONCOMPLIANCE |
| R12 | PUBLICITY_BEFORE_VALIDATION |
| R13 | FAILURE_TO_CORRECT_OR_RETRACT |
| R14 | DISCIPLINE_PRESTIGE_BORROWING |
| R15 | TERMINOLOGY_OR_NAMESPACE_COLONIZATION |

All names are candidate operational labels, not canon.

## Maturity ladder

```text
IDEA
→ RESEARCH_NOTE
→ SOURCE_GROUNDED_CANDIDATE
→ INTERNAL_TECHNICAL_REPORT
→ REPRODUCIBLE_REPORT
→ PREPRINT_CANDIDATE
→ SUBMISSION_CANDIDATE
→ SUBMITTED
→ PEER_REVIEWED
→ CORRECTED / SUPERSEDED / RETRACTED
```

No project may skip states merely because the writing appears polished.

## Claim posture vocabulary

Every scholarly artifact must distinguish:

| Posture | Meaning |
|---------|---------|
| `OBSERVATION` | Directly observed |
| `MEASUREMENT` | Quantitatively measured |
| `EXPERIMENTAL_RESULT` | Output of a controlled experiment |
| `INFERENCE` | Derived from other evidence |
| `HYPOTHESIS` | Proposed but not tested |
| `DESIGN_PROPOSAL` | Proposed design or architecture |
| `NORMATIVE_ARGUMENT` | Argument about what should be |
| `THEORETICAL_CLAIM` | Derived from theory |
| `NOVELTY_CLAIM` | Claim of novelty |
| `EXTERNAL_FACT` | Fact from external source |
| `UNVERIFIED` | Not yet verified |

## Prohibited claims without evidence gates

A project must not use these terms without an explicit gate defining
what evidence warrants that term:

- "scientific"
- "validated"
- "proven"
- "novel"
- "state of the art"
- "formal"
- "general"
- "reproducible"

## Required controls

### 1. Prior-art and novelty discipline

- Search adjacent disciplines, not only the project's preferred vocabulary
- Record direct neighbors, partial precedents, convergent work, disconfirming sources
- State novelty narrowly and compositionally
- Prefer "we did not find" over "no prior work exists"
- Require an independent novelty challenge before public novelty claims

### 2. Methods and reproducibility

- Preserve exact methods, versions, environments, data lineage, prompts, seeds, exclusions, failure cases
- Separate executable reproducibility from conceptual replicability
- Preserve negative and null results
- State which parts cannot be reproduced and why

### 3. Authorship and contribution

- Human authorship and responsibility must be explicit
- Agents and models may be disclosed as tools, assistants, reviewers, or execution systems per current venue policy
- Agents must not be represented as human authors or sources of legitimacy
- Maintain a contribution record suitable for later mapping to a recognized contribution taxonomy
- Every listed author must accept responsibility for the submitted claims

### 4. AI-use disclosure

- Record material model/tool assistance in research, coding, analysis, drafting, translation, figure generation, review
- Do not fabricate citations or imply model-generated synthesis was independently verified
- Venue-specific disclosure rules must be checked at submission time

### 5. Independent review and adversarial testing

- Require a reviewer who did not originate or execute the core work
- Review must inspect methods, calculations, evidence, limitations, novelty posture, reproducibility, reputational risks
- Preserve reviewer disagreements and unresolved objections

### 6. Ethics, privacy, and rights

- Require a human-subjects / participant / sensitive-data determination before research involving people, health, behavior, private communications, identifiable records
- Require consent, privacy, retention, withdrawal, correction, publication boundaries when relevant
- Verify dataset, code, figure, and source licenses

### 7. Publication and communication restraint

- Separate internal report, technical report, preprint, submission, acceptance, peer-reviewed publication
- Never describe a preprint as peer reviewed
- Avoid press-style claims before evidence and review are stable
- Public summaries must preserve caveats and uncertainty

### 8. Correction and retraction

- Every publication-ready artifact needs a correction contact and version history
- Errors must be corrected promptly and visibly
- Materially invalidated claims require supersession or retraction rather than quiet edits

## Artifact maturity schema

See `artifact-maturity.schema.json` for the JSON Schema.

## Required outputs

1. ✅ `RESEARCH_INTEGRITY_STANDARD.md` (this document)
2. ✅ Machine-readable artifact maturity and claim-posture schema
3. ✅ Research reputation-risk checklist (see `risk-checklist.json`)
4. ✅ Contribution/authorship record template (see fixtures)
5. ✅ AI-use disclosure template (see fixtures)
6. ✅ Prior-art and novelty-review template (see fixtures)
7. ✅ Reproducibility manifest template (see fixtures)
8. ✅ Correction/supersession/retraction protocol (see section 8)
9. ✅ Venue-policy verification checklist (see `venue-checklist.json`)
10. ✅ Cross-repo adoption plan (does not retroactively relabel unreviewed work)

## Relationship to LLL Engineering

LLL may be used as a candidate implementation grammar:

- **Ladder**: scholarly maturity and claim-admission states
- **Lattice**: authors, reviewers, evidence, data, code, venues, licenses, authority relationships
- **Loop**: research, replication, review, correction, supersession
- **Receipts**: methods, execution, review, disclosure, publication, correction evidence

LLL itself must remain subject to this standard and may not define
the standard in a self-validating way.

## Cross-repo adoption plan

| Repo | Current controls | Adoption action |
|------|-----------------|----------------|
| `hummbl-papers` | Publication gates, release validation | Map gates to maturity ladder |
| `hummbl-bibliography` | Source registries, contradiction handling | Cross-reference prior-art discipline |
| `claim-evidence-ledger` | Claim-evidence structures | Align claim postures |
| `hummbl-research` | Research campaigns | Map campaigns to maturity states |
| `hummbl-governance` | Governance, receipts, admission | This standard lives here |
| `hummbl-tuples` | Tuple spec, publication direction | Apply before arXiv submission |

No project is grandfathered into compliance without evidence.

## Acceptance criteria

- [x] Existing HUMMBL research/publication controls are inventoried and reused rather than duplicated — see cross-repo adoption plan
- [ ] Current external scholarly-integrity, authorship, disclosure, reproducibility, and venue-policy frameworks are inspected from primary sources — PENDING
- [x] Risk classes and maturity states are defined — 15 risk classes, 10 maturity states
- [x] The standard defines precise prohibited claims and required evidence — see prohibited claims section
- [x] Human authorship and AI-assistance boundaries are explicit — see controls 3 and 4
- [x] Independent review is mandatory for novelty and publication-readiness claims — see control 5
- [x] Correction and retraction paths are operational — see control 8
- [x] The standard applies across all HUMMBL projects — see scope and adoption plan
- [x] No project is grandfathered into compliance without evidence — see adoption plan
- [ ] Reuben's approval is required before ratification — PENDING

## Non-goals

- Guaranteeing journal acceptance or academic credibility
- Creating a prestige or publication-count incentive
- Treating arXiv posting as validation
- Importing academic bureaucracy without measurable risk reduction
- Preventing speculative, exploratory, or creative work when clearly labeled
- Declaring HUMMBL a scientific institution before that status is earned

## References

- Issue: hummbl-io/hummbl-governance#225
- Related: hummbl-io/hummbl-papers#20 (LLL Engineering), #19 (Publication Readiness Gate)
