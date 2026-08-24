# Contract Requirement Crosswalk

**DRAFT — NON-CANONICAL — NOT AUTHORIZED FOR DEPLOYMENT**

All contracts must carry: schema version, stable ID, issuer, subject,
delegation lineage, signer/authentication method, canonicalization version,
exact artifact/plan/target binding, data tier, budgets and cardinality, issue,
expiry and freshness times, nonce/replay protection, invalidation and
supersession references, partition/failure semantics, evidence destinations,
and migration policy. The compact v1 schemas encode the minimum safety subset;
the following fields are mandatory before any stage beyond simulation:

| Contract    | Additional implementation gate                                            |
| ----------- | ------------------------------------------------------------------------- |
| Mission     | typed intent/effect vocabulary, pre/postconditions, simulation digest     |
| Lease       | delegation graph, signer, offline ceiling, revocation epoch               |
| Effect      | operation vocabulary, data-flow mode, downstream effects, CAS version     |
| Attestation | hypervisor/tool/plugin/prompt measurements and trust-root ID              |
| Evidence    | trusted timestamp, signer, retention/legal hold, redaction record         |
| Revocation  | propagation SLA, breaker state, retry ceiling, manual reset authority     |
| Recovery    | separate key/network/operator IDs, RTO/RPO evidence, restore result       |
| Review      | applicability matrix, conflict evidence, waiver/expiry, exact receipt     |
| Reviewer    | competency evidence, scope, data-tier authorization, qualification expiry |
| Manifest    | included-file hashes, ordering, canonicalization, package signature       |

This crosswalk is a fail-closed promotion condition, not permission to deploy.
