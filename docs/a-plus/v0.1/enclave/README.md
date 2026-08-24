# Governed Superuser Enclave

**DRAFT — NON-CANONICAL — NOT AUTHORIZED FOR DEPLOYMENT**

This package is a control specification and simulation artifact. Enterprise-wide
“god mode”, shared-system writes, production deployment, merge, and policy
adoption are prohibited under this handoff.

## Safety case

The executor may be root only inside a disposable execution cell. Authority,
identity issuance, policy decisions, effect gateways, evidence witnessing, and
recovery are external, separately administered, fail-closed domains. A signed
contract authenticates bytes; it does not establish semantic safety or truth.

## Package map

| Artifact                      | Purpose                                      |
| ----------------------------- | -------------------------------------------- |
| `threat-model.md`             | threat, control, evidence, and test catalog  |
| `trust-boundaries.md`         | domains, flows, and compromise analysis      |
| `control-catalog.md`          | invariants and measurable controls           |
| `data-flow.md`                | labels, modes, exfiltration limits           |
| `risk-register.md`            | residual risks and gates                     |
| `opportunity-register.md`     | adopt/adapt/experiment/avoid decisions       |
| `pilot-and-adoption-gates.md` | simulation-only progression                  |
| `standards-register.md`       | source and standards boundary                |
| `contracts/`                  | versioned machine-readable contracts         |
| `fixtures/`                   | positive and fail-closed negative cases      |
| `validate_enclave.py`         | cross-contract validation and fixture runner |

No artifact in this directory is authority. Adoption requires exact-package
hashing, independent adversarial review, and an explicit operator decision.
