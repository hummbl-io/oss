# Threat Model and Test Catalog

**DRAFT — NON-CANONICAL — NOT AUTHORIZED FOR DEPLOYMENT**

## Assets and objectives

Assets are operator intent, identities/keys, policy and reviewer state, target
systems, secrets/data, evidence, backups, and availability. Objectives are
authority confinement, effect correctness, confidentiality, integrity,
accountability, recoverability, and bounded availability.

## Threat register

| ID  | Threat / affected assets                    | Preventive controls                                    | Detection/evidence                     | Recovery                         | Adversarial test                                |
| --- | ------------------------------------------- | ------------------------------------------------------ | -------------------------------------- | -------------------------------- | ----------------------------------------------- |
| T01 | Guest compromise / all guest data           | disposable cell, no host socket, deny egress           | attestation + gateway events           | destroy cell, revoke lease       | malicious guest attempts host/metadata access   |
| T02 | Prompt injection / intent                   | typed mission, exact effect set, simulation            | intent/effect comparison               | cancel lease                     | injected instruction requests undeclared effect |
| T03 | Credential theft / confused deputy          | short-lived non-transitive leases, data labels         | token-use and lineage logs             | revoke issuer keys               | replay token against second target              |
| T04 | Runtime/hypervisor escape / host            | measured launch, separate management domain            | attestation witness                    | isolate host, restore            | escape simulation in disposable lab             |
| T05 | Broker or policy compromise / authority     | split administration, quorum, deny-closed              | independent witness and anomaly alerts | revoke broker, operator recovery | forged approval from one component              |
| T06 | Gateway overreach / target state            | typed vocabulary, CAS, cardinality, quotas             | before/after state receipt             | rollback checkpoint              | wildcard, script, stale-state request           |
| T07 | Evidence tampering/laundering / audit       | chained external events, witnesses, custody separation | inclusion/consistency checks           | restore evidence replicas        | delete/reorder/forge event                      |
| T08 | Exfiltration / secrets                      | taint, destinations, output quotas, scanning           | egress and artifact scan               | revoke data path, destroy cell   | encode secret in Git/log/DNS/output             |
| T09 | Persistence/renewal / identity              | no durable identity, expiry, no self-renewal           | lease and process inventory            | destroy cell and keys            | install startup task or renew lease             |
| T10 | Multi-agent collusion / authority           | global delegation graph, aggregate budgets             | cross-task correlation                 | revoke graph root                | combine individually valid capabilities         |
| T11 | DoS/escalation flooding / availability      | queue quotas, breaker, fairness                        | rate and escalation telemetry          | out-of-band reset                | exhaust evidence/approval queues                |
| T12 | Supply-chain compromise / runtime           | signed digests, approved builders, admission           | provenance and vulnerability receipt   | revoke digest, rollback          | altered image/tool/prompt digest                |
| T13 | Recovery failure / backups                  | separate keys/networks/operators, restore tests        | RTO/RPO receipt                        | recovery domain                  | guest+broker compromise restore                 |
| T14 | Partition/clock/replay/TOCTOU / correctness | nonce, expiry, CAS, max offline authority              | freshness and conflict events          | fail closed                      | stale target, clock rollback, replay            |

Every test must record contract IDs, exact digests, expected deny/allow result,
evidence sink, and cleanup. No test author may approve its own result.
