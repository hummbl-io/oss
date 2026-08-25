# Enterprise Connector Manifest Schema v0.1

## Status

- **Concept status:** candidate
- **Canon status:** not canon — namespace audit required before durable/public adoption
- **Issue:** #539
- **Upstream reference:** https://github.com/hummbl-io/hummbl-governance/issues/1115

## Purpose

Make connectors first-class governed objects rather than informal glue. A connector manifest declares authority, direction, data classification, allowed/prohibited actions, authentication, human approval gates, receipt emission, revocation, failure modes, testing, monitoring, and lifecycle state.

## Direction Semantics

| Direction | Meaning |
|-----------|---------|
| inbound | Data flows INTO HUMMBL from external system |
| outbound | Data flows OUT of HUMMBL to external system |
| bidirectional | Data flows in both directions |
| mirror_only | Read-only mirror of external data, no writes back |
| export_only | One-way export, no inbound data |
| human_mediated | Human operator facilitates the connection |

## Human Approval Gates

| Gate type | When required |
|-----------|---------------|
| none | No human approval needed |
| external_mutation | Before any write to external system |
| publish | Before publishing data externally |
| delete | Before deleting data |
| high_sensitivity_read | Before reading high-sensitivity data |
| all | All operations require approval |

## Receipt Emission Triggers

| Trigger | When receipt is emitted |
|---------|------------------------|
| state_change | Connector lifecycle state changes |
| external_mutation | Any write to external system |
| publish | Data published externally |
| delete | Data deleted |
| high_sensitivity_read | High-sensitivity data read |
| error | Error occurred during operation |

## Lifecycle States

| State | Meaning |
|-------|---------|
| candidate | Proposed, not yet active |
| active | Operational |
| degraded | Operational with issues |
| suspended | Temporarily disabled |
| deprecated | Superseded, will be retired |
| retired | No longer operational |

## Namespace Audit

The following terms require namespace audit before canonization:
- Connector Manifest
- Governed Port
- Agent-Legible Surface

Do not canonize these terms without namespace-audit receipt.

## Do Not Infer

- Do not infer that this schema is canon
- Do not infer that connector manifests are production-ready
- Do not infer that the namespace terms are approved
- Do not infer that this schema covers all connector scenarios

## Non-goals

- Not a connector implementation guide
- Not a protocol specification
- Not a production deployment guide
