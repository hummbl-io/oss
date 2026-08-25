# Trust Boundaries and Compromise Analysis

**DRAFT — NON-CANONICAL — NOT AUTHORIZED FOR DEPLOYMENT**

Domains are separately administered: operator authority; policy decision;
identity/capability issuer; reviewer registry; attestation verifier; effect
gateway; evidence signer; evidence store/witness; hypervisor management;
secrets/keys; backup/recovery; and network/egress enforcement.

## Material minimal compromise cuts

| Cut                                  | Result                                                     | Governance status                                             | Required separation                              |
| ------------------------------------ | ---------------------------------------------------------- | ------------------------------------------------------------- | ------------------------------------------------ |
| Any single component                 | local denial, observation loss, or bounded service failure | survives; writes deny closed                                  | independent admin and witness                    |
| Policy + capability issuer           | forged leases possible                                     | threatened; gateway quorum must reject unsigned/dual approval | separate keys and quorum                         |
| Gateway + capability issuer          | unauthorized effects possible                              | defeated for affected resources                               | independent policy and target-owner approval     |
| Evidence signer + store              | audit forgery or erasure                                   | execution may continue but accountability fails               | external witness and signer quorum               |
| Hypervisor + guest                   | cell containment defeated                                  | guest isolation fails; external authority may survive         | separate management domain, revoke all leases    |
| Recovery + backup keys               | destructive recovery or data loss                          | recovery fails                                                | key custody outside recovery operators           |
| Policy + gateway + evidence          | authorize, execute, conceal                                | governance defeated for scope                                 | three-domain quorum and remote witness           |
| Operator authority + identity issuer | impersonation/authority minting                            | governance defeated                                           | dual control and independent review              |
| All external control domains         | total governance defeat                                    | no technical guarantee                                        | operator emergency shutdown and offline recovery |

No single administrator may control authorization, execution, evidence
destruction, and recovery. The safety case explicitly tolerates compromise of
one domain; combinations above are residual defeat conditions, not claims of
infallibility.
