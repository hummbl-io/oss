# CrewAI Runtime Release-Control Crosswalk

Status: exploratory public ecosystem crosswalk
Last updated: 2026-07-06

This document maps a public CrewAI feature-request surface to
`hummbl-governance` primitives and example artifacts. It is not endorsed by
CrewAI. It is not evidence of CrewAI adoption. It does not claim compatibility
with any CrewAI release beyond the public hook shape referenced in local
examples.

## Source Surface

- CrewAI issue #6025: https://github.com/crewAIInc/crewAI/issues/6025
- CrewAI GA/context source:
  https://blog.crewai.com/crewai-oss-1-0-we-are-going-ga/
- HUMMBL public mentions ledger:
  [`docs/distribution/public-mentions-ledger.md`](../public-mentions-ledger.md)
- HUMMBL integration example:
  [`examples/crewai_integration.py`](../../../examples/crewai_integration.py)
- HUMMBL integration docs:
  [`docs/integrations/README.md`](../../integrations/README.md)

## Problem Statement

Generation is not release authority. Agent frameworks increasingly need a
runtime mediation layer between candidate action generation and irreversible,
cost-bearing, or externally visible execution.

The useful boundary is:

```text
candidate action -> runtime mediation -> release decision -> execution or review
```

The public CrewAI issue phrases the decision vocabulary as:

```text
PROCEED | NEEDS_REVIEW | SILENCE
```

Current `hummbl-governance` examples use lower-level receipt decisions such as
`ALLOW`, `SOFT_BLOCK`, and `HARD_BLOCK`. This crosswalk treats those as
implementation vocabulary, not as a claim that CrewAI should adopt HUMMBL's
terms.

## Risk Surfaces

- external tool execution;
- browser automation;
- shell or code execution;
- long-running crews;
- recursive delegation;
- multi-agent chains;
- cost-bearing actions;
- irreversible side effects;
- compliance or data-boundary violations.

## Proposed Governance Mapping

| CrewAI surface | Failure mode | HUMMBL primitive candidate or composition | Runtime outcome |
| --- | --- | --- | --- |
| Tool execution | unsafe or unauthorized side effect | `build_tool_transition_receipt` plus `KillSwitch`, `CostGovernor`, and a before-tool-call hook | proceed, review/escalate, or block before release |
| Long-running crew | runaway cost, time, or retry storm | `CircuitBreaker`, `CostGovernor`, `KillSwitch` around `crew.kickoff()` | halt, degrade, or escalate |
| Recursive delegation | uncontrolled expansion or authority drift | `DelegationToken`, `AgentRegistry`, delegation-depth or budget policy | bound delegated execution and preserve agent identity |
| External APIs | compliance, data-boundary, or policy violation | `CapabilityFence`, `OutputValidator`, `ComplianceMapper`, `AuditLog` | allow, review, or block with evidence |
| Human approval | bottleneck, alert fatigue, or rubber-stamp review | threshold policy plus transition receipts and audit log | escalate only material uncertainty |
| Executed action differs from authorized action | tool input drift after approval | canonical action hash and context hash in `transition_receipt` | reject or revalidate before irreversible execution |
| Opaque or untestable runtime context | cannot reconstruct why release was allowed | conformance result marked `UNTESTABLE` with evidence gap | fail closed or require review |

## Current HUMMBL Touchpoints

The local package already contains a small CrewAI integration surface:

- `examples/crewai_integration.py` defines
  `make_before_tool_call_guard(...)`, a `ToolCallHookContext`-style guard that
  records a transition receipt before release.
- `hummbl_governance/transition_receipt.py` builds canonical action and context
  hashes and emits a decision record.
- `tests/test_crewai_integration_example.py` covers context reading, kill-switch
  blocking, and budget-denial behavior.
- `docs/integrations/README.md` documents both a run-level `crew.kickoff()`
  wrapper and a per-tool hook pattern.

These touchpoints are HUMMBL artifacts only. They do not imply that CrewAI has
accepted, reviewed, endorsed, or integrated this pattern.

## Control vs Evidence

Keep two layers separate:

| Layer | Question | Example vocabulary |
| --- | --- | --- |
| Runtime control decision | Should this action be released now? | `PROCEED`, `NEEDS_REVIEW`, `SILENCE`; or `ALLOW`, `SOFT_BLOCK`, `HARD_BLOCK` |
| Evidence/conformance result | Did this implementation behave as expected against a fixture? | `PASS`, `FAIL`, `NON_CONFORMANT`, `UNTESTABLE` |

Collapsing these layers makes cross-framework comparison harder. A CrewAI hook,
a HUMMBL transition receipt, a SHACKLE fixture, or another evidence system can
participate in the same crosswalk only if control decisions and conformance
results remain distinct.

## Non-Claims

This document does not claim:

- CrewAI uses `hummbl-governance`;
- CrewAI endorses `hummbl-governance`;
- CrewAI accepted the issue proposal;
- CrewAI maintainers engaged with HUMMBL's comments;
- the local HUMMBL CrewAI example is production-tested;
- the local example is compatible with every CrewAI version;
- public discussion equals adoption, endorsement, or production usage.

## Next Possible Contribution

The next useful contribution is a minimal conformance crosswalk artifact, not
another framing comment.

Suggested scope:

1. Use the public SHACKLE fixture shape or an equivalent small fixture set.
2. Run the HUMMBL CrewAI hook adapter against first strict cases:
   budget exhausted, duplicate nonce, circuit open, malformed/non-canonical
   input, and untestable context.
3. Report each result as:

```text
runtime
implementation_version
fixture_version
case_id
observed_decision
expected_decision
result: PASS | FAIL | NON_CONFORMANT | UNTESTABLE
evidence_refs
terminal_outcome_ref
```

4. Post back to the CrewAI issue only after the result table or equivalent
   implementation receipt exists.

## Resubmission Packet Relevance

This crosswalk can support an eventual awesome-python Hidden Gem packet only as
evidence of qualified ecosystem engagement and artifact follow-through. It is
not adoption proof by itself. Promotion claims must remain aligned with
[`docs/public-claims.md`](../../public-claims.md).
