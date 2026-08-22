# Phase -1 Report: HUMMBL Constitutional Systems Lab Admission

**Status: CANDIDATE RESEARCH ADMISSION — NO REPOSITORY CREATION AUTHORIZED — NON-CANONICAL**

Issue: hummbl-io/hummbl-governance#224

## 1. Executive disposition

**`DEFER_TO_EXISTING_REPO`**

The Constitutional Systems Lab should begin as a bounded directory
within `hummbl-governance` rather than a new repository. A dedicated
repo may be admitted later if EXP-0001 produces durable experimental
artifacts that justify independent lifecycle.

## 2. Strongest reason for and against

### For admission as a new repo

A distinct repo would give the lab its own research questions,
maturity states, and exit criteria — preventing experimental
constitutional objects from silently becoming fleet canon.

### Against admission as a new repo

No durable object set exists yet. No experiment has been run. Repo
creation before evidence violates Reuben's Razor ("run the smallest
reversible experiment capable of falsifying the thesis"). The work
can be safely contained in a bounded directory at lower cost.

## 3. Evidence inventory

| Object | Status | Notes |
|--------|--------|-------|
| `hummbl-governance/CONSTITUTION.md` | current | Inspected |
| `DOCTRINE.md` | current | Inspected |
| `AGENTS.md` | current | Inspected |
| `KRINEIA.md` | current | Inspected |
| `docs/standards/HUMMBL_REPO_STANDARD.md` | current | Inspected |
| doctrine-amendment primitive | current | In hummbl-governance |
| admission-control primitive | current | In hummbl-governance |
| delegation primitive | current | In hummbl-governance |
| audit primitive | current | In hummbl-governance |
| identity primitive | current | In hummbl-governance |
| kill-switch primitive | current | In hummbl-governance |
| receipt primitive | current | In hummbl-governance |
| `hummbl-governance-kernel` constitutions | current | Separate package |
| `hummbl-governance` constitutional surfaces | current | Separate repo |
| comparative-government corpus (issue #81) | stale | Closed; artifacts not inspected this pass |
| Constitutional Integrity Remediation #220 | current | Parent issue; child findings exist |

**Gaps**: The comparative-government corpus from closed issue #81 was
not inspected this pass. This should be reviewed before EXP-0001
execution.

## 4. Overlap matrix

| Object | Classification | Rationale |
|--------|---------------|-----------|
| authority grants | REUSE | Existing delegation primitive covers this |
| office charters | LAB_ONLY | No existing primitive; experimental |
| proposals | REUSE | Existing proposal/contract primitives |
| ratification | ADAPT | Existing admission-control needs extension |
| execution orders | REUSE | Existing contract/execution primitives |
| appropriations | REJECT | No budget primitive at this level; deferred |
| independent review | ADAPT | Existing review surfaces need extension |
| recusal | LAB_ONLY | No existing primitive; experimental |
| appeal | LAB_ONLY | No existing primitive; experimental |
| audit | REUSE | Existing audit-log primitive |
| emergency restriction | REUSE | Existing kill-switch primitive |
| sunset | ADAPT | Existing expiry/sunset in delegation tokens |
| amendment | REUSE | Existing doctrine-amendment primitive |
| receipt | REUSE | Existing receipt primitive |
| precedent | REJECT | No precedent primitive; deferred |

**Summary**: 7 REUSE, 3 ADAPT, 4 LAB_ONLY, 2 REJECT. The majority of
objects can be reused from existing primitives. This supports
`DEFER_TO_EXISTING_REPO`.

## 5. Naming/classification/visibility/license/canonicality decision

If admitted as a directory in `hummbl-governance`:

```yaml
path: docs/research/constitutional-systems-lab/
classification: research
status: experimental
canonical: false
authority_model: human-ratified
agent_authority: advisory-and-bounded-execution-only
human_participation: founder-only-in-phase-0
visibility: private (within hummbl-governance repo)
license: Apache 2.0 (inherits repo license)
```

**Public label**: HUMMBL Constitutional Systems Lab (candidate, non-canonical)

## 6. Minimum file tree (if admitted as directory)

```
docs/research/constitutional-systems-lab/
  README.md                    — lab charter and non-sovereignty boundary
  PHASE_MINUS_1_REPORT.md      — this report
  EXP-0001_PROTOCOL.md         — hardened EXP-0001 protocol
  EXP-0001_RESULTS.md          — results (to be populated after experiment)
  OVERLAP_MATRIX.md            — overlap matrix (extracted from this report)
  RISK_REGISTER.md             — risk register
```

No new repository, no new package, no new service.

## 7. Hardened EXP-0001 protocol

### Title

Bounded GitHub Issue-Creation Authority

### Research question

Does a minimal institutional workflow improve the quality, scope
integrity, revocability, and auditability of delegating GitHub
issue-creation authority to an agent without adding more friction
than value?

### Comparison

```text
ordinary founder-agent issue workflow
versus
proposal → independent review → human ratification → bounded execution → independent audit → sunset disposition
```

### Initial boundaries

- One repository or dry-run drafts only
- One issue template
- One declared issue class (e.g., documentation issues)
- Fixed expiration: 7 days
- Small action ceiling: 5 issues per expiration window
- Deduplication required before proposal
- No PR creation, merging, code changes, or third-party comments
- No label/milestone/assignee/project mutations unless separately admitted
- Receipt for every proposal and execution

### Roles

- **Sponsor**: Agent that proposes an issue
- **Constitutional reviewer**: Distinct agent from executor
- **Ratifier**: Reuben Bowlby (founder phase only)
- **Executor**: Agent that creates the ratified issue
- **Auditor**: Distinct agent from executor
- **Deterministic records function**: Git history + receipts

### Metrics

- operator time and total time
- corrections and duplicate proposals
- scope deviations
- missing evidence
- review findings
- receipt completeness
- issue usefulness
- bypasses caused by excessive burden

### Stop/falsification conditions

Weaken or reject the thesis if the process:

- adds ceremony without catching meaningful failures
- requires more human attention than direct review
- produces nominally independent but duplicative agent review
- creates records harder to understand than Git and issue history
- yields no reusable primitive
- requires anthropomorphic or legitimacy claims
- cannot preserve revocation and human appeal boundaries

**A failed experiment is a valid result.**

## 8. Risk register (maximum 10 items)

| # | Risk | Likelihood | Impact | Mitigation |
|---|------|-----------|--------|-----------|
| 1 | Experimental objects silently become fleet canon | Medium | High | Explicit non-canonical labeling; no imports from lab to production |
| 2 | Agent review is nominally independent but duplicative | High | Medium | Require distinct agent identity; check for substantive disagreement |
| 3 | Process adds ceremony without value | Medium | Medium | Stop/falsification conditions; measure bypasses |
| 4 | Anthropomorphic or legitimacy claims creep in | Medium | High | Non-sovereignty boundary statement; review all public language |
| 5 | Scope creep beyond issue creation | Medium | Medium | Strict boundaries; no PR/merge/code changes |
| 6 | Human expansion without protocol | Low | High | Human expansion gate; founder-only in Phase 0 |
| 7 | Receipts create false confidence | Low | Medium | Audit checks receipt against actual state |
| 8 | Comparative-government corpus (#81) not reviewed | Medium | Low | Review before EXP-0001 execution |
| 9 | LLL framework bias affects evaluation | Medium | Low | LLL is candidate diagnostic only, not ratified authority |
| 10 | Repo creation pressure before evidence | Medium | Medium | This report defers repo creation; require EXP-0001 results first |

## 9. Initial issues (maximum 5, none from deferred scope)

1. Review comparative-government corpus from closed issue #81
2. Implement EXP-0001 protocol as dry-run drafts
3. Execute EXP-0001 with documentation issues only
4. Audit EXP-0001 results against stop/falsification conditions
5. Disposition: admit new repo, continue in directory, or stop

**None of these issues are from the deferred scope** (elections,
bicameralism, political parties, agent citizenship, permanent agent
offices, voting interfaces, judicial runtimes, economies, taxes, legal
entities, boards, councils, curricula, conferences, websites,
dashboards, APIs, MCP servers, departments, ministries, federations,
or claims of a new government).

## 10. Next-action choice

**`create a docs-only branch in an existing repository`**

Specifically: create the `docs/research/constitutional-systems-lab/`
directory in `hummbl-governance` with the minimum file tree above.

This action:
- Does not create a new repository
- Does not create experimental objects as canon
- Does not require human expansion
- Is fully reversible (delete the directory)
- Allows EXP-0001 to proceed at lowest cost

## 11. Receipt-ready source-bounded summary

```text
artifact: Phase -1 Report for HUMMBL Constitutional Systems Lab
disposition: DEFER_TO_EXISTING_REPO
next_action: create docs-only directory in hummbl-governance
evidence_posture: [SEC] secondary source — based on inspection of
  existing hummbl-governance primitives and documentation
gaps: comparative-government corpus (#81) not inspected
non_sovereignty: This project studies and simulates institutional
  governance for voluntary human-agent systems. It does not claim
  sovereignty, governmental authority, democratic legitimacy, legal
  jurisdiction, or coercive power over any person.
canonical: false
agent_authority: advisory-and-bounded-execution-only
human_participation: founder-only-in-phase-0
review_required: true
operator: Reuben Bowlby
```

## Non-sovereignty boundary

This project studies and simulates institutional governance for
voluntary human-agent systems. It does not claim sovereignty,
governmental authority, democratic legitimacy, legal jurisdiction, or
coercive power over any person.

Prohibited:

- representing agent votes as democratic consent
- treating agents as citizens or constituents
- applying experimental rules to humans without notice and consent
- calling internal decisions laws binding on nonparticipants
- treating model agreement as political legitimacy
- creating powers beyond Reuben's or a consenting participant's actual grants

## Relationship to LLL

LLL Engineering is used as a candidate diagnostic framework only,
not as ratified authority:

- **Ladder**: project and experimental admission states
- **Lattice**: typed relationships and non-transitive authority among sponsor, reviewer, ratifier, executor, auditor, repos, and receipts
- **Loop**: execution, observation, evaluation, disposition, and delivery receipt

Any future case-study claim should remain candidate-only and follow
the existing LLL admission packet.

## References

- Issue: hummbl-io/hummbl-governance#224
- Constitutional Integrity Remediation: hummbl-io/hummbl-governance#220
- LLL Engineering protocol: hummbl-io/hummbl-papers#20
