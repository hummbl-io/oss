# Architecture and Trust-Boundary Diagram

**DRAFT — NON-CANONICAL — NOT AUTHORIZED FOR DEPLOYMENT**

```mermaid
flowchart LR
  O[Operator / authority quorum] --> P[Policy decision domain]
  P --> I[Identity and capability issuer]
  I --> B[Typed effect broker]
  B --> E[Disposable execution cell agent root only here]
  E --> G[Effect gateways CAS + quotas + taint]
  G --> S[Target systems]
  G --> W[Evidence signer]
  W --> X[Evidence store + independent witness]
  R[Reviewer registry + attestation verifier] --> P
  H[Hypervisor management] --> E
  K[Separate recovery domain] --> E
  N[Network / egress enforcement] --> E
```

Trust boundaries are administrative as well as network boundaries. The guest
cannot reach policy keys, issuer keys, reviewer state, evidence custody,
hypervisor management, backup keys, or recovery credentials. Every gateway
request is bound to a mission, delegation lineage, plan hash, target version,
data mode, quota, nonce, and expiry. Policy loss, attestation drift, stale
state, partition, clock failure, or evidence-sink failure defaults to no
external write.
