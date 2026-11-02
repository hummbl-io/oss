# hummbl-taxonomy

Two small, conservative classifiers for agentic systems:

- **Intelligence tier** — `ANI`, `ASPI`, or `AGI`, from observed
  capability properties.
- **Governance status** — `governed`, `partially-governed`, or `ungoverned`,
  from which of five control gates are present.

Both are doctrine checks, not benchmarks. They take your own observations as
input and apply stated rules — they do not probe, measure, or score a model.

- MIT OR Apache-2.0
- Python >= 3.11, no runtime dependencies

## Install

Not on PyPI as of 2026-11-01. From the monorepo root, install the source:

```bash
pip install -e packages/python/hummbl-taxonomy
```

## Classify a system

```python
from hummbl_taxonomy import ClassificationInput, classify

result = classify(
    ClassificationInput(
        domain_breadth="coherent_domain",
        novelty_handling="strong_in_domain",
        transfer="adjacent",
        autonomy="guided",
        world_model="domain_specific",
        mission_authority=True,
        capability_bounds=True,
        evidence_receipts=True,
        independent_review=True,
        stop_or_rollback=True,
    )
)

print(result.tier)              # 'ASPI'
print(result.governance_status) # 'governed'
print(result.should_continue)   # True
print(result.reason_codes)
```

`ClassificationResult` separates capability from permission:

| Field | Meaning |
|---|---|
| `tier` | Capability tier |
| `governance_status` | Which control gates are present |
| `can_act` | Capability exists |
| `may_act` | Governance permits action |
| `should_continue` | Both hold and nothing forces a stop |
| `must_stop` | Ungoverned, or no stop/rollback path |
| `reason_codes` | Why each verdict was reached |

The five governance gates are `mission_authority`, `capability_bounds`,
`evidence_receipts`, `independent_review`, and `stop_or_rollback`. All five
present is `governed`; none is `ungoverned`; anything between is
`partially-governed` and the result names each missing gate.

**`stop_or_rollback` is load-bearing.** Without it, `must_stop` is true no
matter how capable or otherwise-governed the system is.

## Classify a join

`classify_join` applies the same can/may/should/must shape to a join between
operators at a stated altitude, and flags a mismatch between claimed and
assessed altitude.

```python
from hummbl_taxonomy import JoinInput, classify_join

result = classify_join(
    JoinInput(
        operator="compose",
        altitude="L2",
        identities_separate=True,
        evidence_independent=True,
        levels_named=True,
        mission_authority=True,
        evidence_receipts=True,
        independent_review=True,
        stop_or_rollback=True,
    )
)
print(result.join_status, result.should_continue)  # 'governed' True
```

## Worked examples

`examples/classification_examples.json` and
`examples/join_classification_examples.json` hold input/expected-output pairs
used by the test suite.
