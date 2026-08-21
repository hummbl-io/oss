# Public Mentions Ledger

Status: distribution evidence ledger
Last updated: 2026-07-18

This ledger tracks qualified public ecosystem insertions for
`hummbl-governance`. It is not a volume counter. A mention only belongs here
when it answers a real ecosystem need, offers an implementation path, or
preserves a reusable phrase that can move the category forward.

## Operating Rule

Every public mention must satisfy at least one of these conditions:

- It answers a specific problem raised by the host ecosystem.
- It offers a concrete implementation path, example, fixture, adapter, or PR
  route.
- It preserves a phrase or distinction that can be reused without requiring
  HUMMBL-specific context.

Default cap: 1 to 3 qualified ecosystem insertions per day. Do not optimize for
raw mention count.

## Metrics

| Metric | Question |
| --- | --- |
| Qualified mentions | Did this appear where the idea is directly relevant? |
| Maintainer response | Did someone with project authority engage? |
| Repo/profile click-through | Did the mention drive visits, stars, forks, issues, PRs, or discussions? |
| Artifact conversion | Did it produce a reusable artifact, fixture, example, issue, PR, or citation? |
| Category recall | Is the phrase or distinction likely to be remembered after one read? |

## Status Vocabulary

| Status | Meaning |
| --- | --- |
| `open` | Surface is still open for response or follow-up. |
| `converted` | The mention produced a concrete artifact, issue, PR, external quote, or implementation path. |
| `maintainer-engaged` | A maintainer, owner, member, or collaborator engaged directly. |
| `watch` | No action now; revisit on the follow-up date. |
| `closed-no-conversion` | Surface closed or stale with no useful conversion. |

## Ledger

| Date | Surface | Topic | Claim inserted | Link | Status | Conversion | Follow-up |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2026-07-18 | `systempromptio/awesome-ai-agent-governance` issue #20 / Open-Source Governance Toolkits | Policy-compatible directory submission | `hummbl-governance` was added following an author-disclosed submission | https://github.com/systempromptio/awesome-ai-agent-governance/issues/20 | converted, maintainer-engaged | Directory listing verified at `713d18e`; curator reported repository/PyPI verification and gave a positive assessment. Recognition only: not adoption, production use, or certification. | No follow-up; credit only issue #258's 10-to-25 directory-submission task |
| 2026-07-08 | Third-party index mirror metadata (`pydigger-data`) | Independent package metadata indexing | `hummbl-governance` appears in upstream package metadata repository used by third-party tooling | https://github.com/szabgab/pydigger-data/blob/main/data/pypi/hu/hummbl-governance.json | open | weak public indexing, no explicit endorsement | Add an auditable citation snapshot for the metadata snapshot timestamp before resubmission |
| 2026-07-08 | Secondary distribution mirror (`piwheels`) | Distribution visibility outside PyPI | `hummbl-governance` is listed in a public wheel mirror, expanding discoverability footprint | https://www.piwheels.org/project/hummbl-governance | open | weak public indexing, no explicit endorsement | Keep screenshot/link-check in resubmission evidence set |
| 2026-06-28 to 2026-07-04 | CrewAI issue #6025 | Runtime release-control mediation before agent/tool execution | `generation != release authority`; `fixture expected verdict != implementation conformance result` | https://github.com/crewAIInc/crewAI/issues/6025 | open, watch | External technical thread active; 54 comments, 10 unique commenters, 0 maintainer/member/collaborator comments as of 2026-07-06. HUMMBL comments introduced run-level wrappers, CrewAI `ToolCallHookContext` receipt mediation, and a conformance-result shape. External commenters published or pointed to SHACKLE fixtures and a CrewAI/SHACKLE/SAR composition example. No maintainer response, star/fork attribution, issue adoption, or PR conversion verified yet. | 2026-07-12 |

## CrewAI Issue #6025 Receipt

- Surface: https://github.com/crewAIInc/crewAI/issues/6025
- Public repo metrics checked 2026-07-06: 54,966 stars and 7,716 forks via
  `gh repo view crewAIInc/crewAI`.
- Issue state checked 2026-07-06: open, labeled `feature-request`.
- Maintainer response check: no comments from `MEMBER`, `OWNER`,
  `COLLABORATOR`, or `CONTRIBUTOR` author associations as of the check.
- HUMMBL public participation:
  - 2026-06-28: https://github.com/crewAIInc/crewAI/issues/6025#issuecomment-4826870284
  - 2026-07-03: https://github.com/crewAIInc/crewAI/issues/6025#issuecomment-4877919187
  - 2026-07-03: https://github.com/crewAIInc/crewAI/issues/6025#issuecomment-4878142145
  - 2026-07-04: https://github.com/crewAIInc/crewAI/issues/6025#issuecomment-4883814985

## Follow-Up Rule

Follow up only with a concrete artifact. For the CrewAI thread, the next useful
artifact is not another framing comment. It is a small conformance crosswalk:

- Take the published SHACKLE fixture set.
- Run the `hummbl-governance` CrewAI hook adapter against the first strict
  cases: budget exhausted, duplicate nonce, circuit open,
  malformed/non-canonical input, and untestable context.
- Publish a result table with:
  - `runtime`
  - `implementation_version`
  - `fixture_version`
  - `case_id`
  - `observed_decision`
  - `expected_decision`
  - `result`
  - `evidence_refs`
  - `terminal_outcome_ref`

Do not post again in the CrewAI thread before this artifact or an equivalent
implementation receipt exists.

## Target Surfaces

| Ecosystem | Good-fit topics | Current rule |
| --- | --- | --- |
| CrewAI | tool hooks, runtime middleware, crews/flows, guardrails, governance, audit trails | Continue only with artifact-backed follow-up. |
| LangChain / LangGraph | tool execution, callbacks, middleware, human-in-the-loop, persistence, LangGraph interrupts | Enter only when a concrete hook or example is directly relevant. |
| AutoGen | multi-agent chains, approval functions, tool execution, long-running autonomous tasks | Prioritize receipt and replay examples. |
| OpenAI Agents SDK | tool approval, hosted tools, tracing, handoffs, guardrails | Use official terminology and keep examples minimal. |
| MCP | tool authorization, resource access policy, audit evidence, permission boundaries | Prefer protocol-level result contracts and fixtures. |

## Public-Claims Boundary

This ledger may record public responses and public artifacts, but it does not
by itself verify adoption. Do not promote any of the following without a
separate receipt in [`docs/public-claims.md`](../public-claims.md):

- customer or production usage;
- maintainer endorsement;
- direct impact on GitHub stars or forks;
- benchmark superiority;
- integration support beyond documented examples or committed code.
