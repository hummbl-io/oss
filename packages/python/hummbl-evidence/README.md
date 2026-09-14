# hummbl-evidence

Shared evidence-state and two-party approval primitives for the HUMMBL fleet.

Extracted from `hummbl-observatory` so that both observatory (OSS adoption
intelligence) and `hummbl-signal` (public-signal intelligence) can import the
same governed-belief primitives without duplication.

## What's included

- **`EvidenceState`** — four-valued enum (`sufficient`, `partial`, `absent`,
  `contradictory`) for tracking evidence quality on every health-bearing
  record. Absence renders as *unknown*, never *clean*.
- **`render_health()`** — maps `EvidenceState` to a human-readable health
  label. `ABSENT` always renders as `"unknown"`, `CONTRADICTORY` as
  `"contested"` — never `"clean"` or `"healthy"`.
- **`Decision`** — typed approval decision (`approved`, `rejected`).
  Constrains the field so a typo cannot silently land.
- **`ApprovalRecord`** — frozen provenance record for a two-party approval
  event (approver, identity, timestamp, decision, evidence state).
- **`Proposable`** — structural protocol: anything with a `proposed_by`
  attribute can be approved.
- **`enforce_two_party()`** — raises `ValueError` if the approver is the same
  person as the proposer.
- **`approve()`** — convenience function that validates the decision type,
  enforces two-party separation, and returns an `ApprovalRecord`.

## Design constraints

These primitives encode the binding constraints from the observatory's
ARCANA peer review:

1. **Absence is a first-class signal.** `evidence_state` on every
   health-bearing record. Zero coverage = *unknown*, never *clean*.
2. **Authorship != approval.** The human who drafts a record must not sign
   the approval. Two-party review with independent signing.
3. **Typo-safe decisions.** `Decision` is an enum, not a free-form string.
   A typo like `"apporved"` raises `TypeError`, not silent acceptance.

## Installation

```bash
pip install .
```

## Usage

```python
from hummbl_evidence import EvidenceState, render_health, Decision, approve

# Evidence state on a health-bearing record
state = EvidenceState.ABSENT
label = render_health(state)  # "unknown" — never "clean"

# Two-party approval (approver must differ from proposer)
from dataclasses import dataclass

@dataclass(frozen=True)
class MyProposal:
    proposed_by: str

proposal = MyProposal(proposed_by="alice")
approval = approve(proposal, approved_by="bob", approver_identity="sigstore:bob@example.com")
# approval.approved_by == "bob", approval.decision == Decision.APPROVED

# Self-approval is rejected
try:
    approve(proposal, approved_by="alice", approver_identity="sigstore:alice@example.com")
except ValueError as e:
    print(e)  # "Two-party approval violated..."
```

## License

MIT OR Apache-2.0.
