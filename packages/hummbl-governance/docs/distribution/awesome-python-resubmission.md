# awesome-python Resubmission Gate

Status: distribution gate
Last updated: 2026-07-08

This document records the awesome-python rejection of `hummbl-governance` as
an external adoption signal and defines the evidence required before any
resubmission.

## External Receipt

- Pull request: https://github.com/vinta/awesome-python/pull/3180
- Tracking issue: https://github.com/hummbl-io/hummbl-governance/issues/212
- Submitted: 2026-06-03
- Closed: 2026-06-04
- Rejection reason: "GitHub stars: 0 star (minimum 100 required, or strong
  justification for Hidden Gem)."
- Current public repo signal checked 2026-07-08:
  https://github.com/hummbl-io/hummbl-governance shows 0 stars, 1 fork,
  latest release `v1.2.2`, and package claims of 34 primitives and
  2,027 tests.

## Interpretation

The rejection is not evidence that the project is technically incoherent. It
is evidence that the public proof layer is not yet strong enough for
awesome-python's acceptance model.

The relevant acceptance path is either:

- **100+ GitHub stars**, which satisfies the explicit threshold cited in the
  rejection; or
- **Hidden Gem justification**, which requires a stronger packet of real-world
  usage, experienced-developer recommendation, maturity, activity, and clear
  explanation of the niche solved by the package.

## Resubmission Rule

Do not resubmit to awesome-python until one of these gates is met:

1. The repository has at least 100 GitHub stars.
2. A Hidden Gem packet exists with enough public evidence to justify
   submission below 100 stars.

The Hidden Gem packet must include all of the following:

- 3 to 5 public usage or endorsement receipts from people or projects outside
  the maintainer's direct control.
- Public examples for raw OpenAI, LangChain, CrewAI, AutoGen, and MCP usage.
- A concise problem statement explaining why zero-dependency runtime governance
  matters for AI agent systems.
- Evidence of project maturity: release history, current test-count receipt,
  install smoke receipt, README examples, and active maintenance.
- A comparison explaining why framework-native tooling does not cover the same
  runtime governance surface.

## Work Tracker

- [x] Add public examples for raw OpenAI, LangChain, CrewAI, AutoGen, and MCP.
  - `examples/openai_api_integration.py`
  - `examples/langchain_integration.py`
  - `examples/autogen_integration.py`
  - `examples/mcp_integration.py`
  - `docs/integrations/README.md`
- [x] Maintain the public mentions ledger as a source of qualified ecosystem
  insertion receipts.
- [ ] Collect 3 to 5 external adoption, usage, or endorsement receipts.
- [x] Create `docs/distribution/awesome-python-hidden-gem-packet.md` with the
  resubmission narrative and evidence.
- [ ] Add a distribution section to the README once receipts exist.
- [ ] Verify repo public surface before resubmission: stars, forks, latest
  release, topics, README, Issues, Discussions, Security policy, and project
  URLs.
- [ ] Recheck awesome-python `CONTRIBUTING.md` immediately before resubmission.
- [ ] Resubmit only after the star threshold or Hidden Gem packet is ready.

## Issue Draft

Title:

```text
Distribution gate: awesome-python rejection requires public adoption receipts before resubmission
```

Body:

```markdown
## Context

The awesome-python PR for `hummbl-governance` was closed on 2026-06-04 because
the repository had 0 stars and did not yet meet the 100-star threshold or
provide a strong Hidden Gem justification.

Receipt: https://github.com/vinta/awesome-python/pull/3180

## Definition of Done

- [ ] Add public examples for raw OpenAI, LangChain, CrewAI, AutoGen, and MCP.
- [ ] Collect 3 to 5 public external usage or endorsement receipts.
- [x] Create `docs/distribution/awesome-python-resubmission.md`.
- [x] Add public examples for OpenAI, LangChain, CrewAI, AutoGen, and MCP.
- [ ] Build a Hidden Gem packet explaining the niche, real-world usage,
      maturity, and differentiated value.
- [ ] Do not resubmit until the repo reaches 100 stars or the Hidden Gem packet
      is credible enough to submit below 100 stars.
```

## Notes

Public distribution claims must stay aligned with
[`docs/public-claims.md`](../public-claims.md). Do not promote production-use,
customer, adoption, benchmark, or third-party endorsement claims without a
receipt.
