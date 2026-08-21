# Existing Schema Crosswalk — Cross-Repo Contract v0.1

Status: **candidate inventory — descriptive, not canonical**
Inspected: 2026-07-11

This crosswalk records actual differences among current HUMMBL public schemas. It supports the additive-envelope decision in `hummbl-governance#234`: shared contracts must map domain concepts without renaming or replacing domain-owned fields.

## Inspected schema snapshots

| Repository | Path | Inspected blob SHA |
|---|---|---|
| `hummbl-dev/hummbl-dev` | `docs/evidence-graph/v0.1/schema.json` | `9b2b7c29380c7e39aa0829744f31df651d65a958` |
| `hummbl-dev/research-source-packets` | `schemas/research-source-packets-v0.1.json` | `73087e604a0ed96b5e18ee891c5526c25fc6b888` |
| `hummbl-dev/claim-evidence-ledger` | `schemas/claim-evidence-ledger-v0.1.json` | `6d9f357a55ac2ddafdb0026ea3cd70950876a69b` |
| `hummbl-dev/knowledge-as-code` | `schemas/knowledge-as-code-v0.1.json` | `29452d84763103fbbc9fd37bb6c6ae3bf146bd47` |
| `hummbl-dev/ai-source-verification` | `schemas/ai-source-verification-v0.1.json` | `78226c3345ef7b5f5c4abe90ac4287ad6baad25b` |
| `hummbl-dev/execution-receipts` | `schemas/execution-receipts-v0.1.json` | `972cebdfabc3771bdba11d68974c7d2d5caecf93` |
| `hummbl-dev/protocol-as-code` | `schemas/protocol-as-code-v0.1.json` | `fae0a1797556671aa6488f6e844ec1512b65f4de` |
| `hummbl-io/hummbl-governance` | `hummbl_governance/data/canon_registry.schema.json` | `b0ef7af957a2f26b386af8742606b6239e4a147c` |

## Field-level crosswalk

| Concern | Evidence Graph | Source Packet | Claim-Evidence | Knowledge-as-Code | Source Verification | Execution Receipt | Protocol-as-Code | Canon Registry |
|---|---|---|---|---|---|---|---|---|
| Schema/version field | `version: 0.1` numeric | `schemaVersion: v0.1` | `schemaVersion: 0.1` | `schemaVersion: v0.1` | `schemaVersion: ai-source-verification/v0.1` | `schemaVersion: execution-receipts/v0.1` | `schemaVersion: v0.1` | `schema_version: 1.0.0`-style SemVer |
| Artifact lifecycle | `status` | `packetStatus` | `packetStatus` | `packetStatus` | `packetStatus` | `packetStatus` | `packetStatus` | `current_canon_level` + `proposed_canon_level` |
| Identity/manifest | `graph_id`, nodes | `packetManifest` | `ledgerManifest` | `knowledgeManifest` | `verificationManifest` | `receiptManifest` | `protocolManifest` | `artifact_id`, `artifact_type` |
| Authority shape | none at graph root | `producer`, `posture`, optional ORCID | `id`, `name`, optional URI | `owner`, `canActOnBehalfOf` | `producer`, `basis` | `assertedBy`, `posture`, optional timestamp | `owner`, `canActOnBehalfOf` | operator approval, approver, delegation chain |
| Domain payload | graph nodes/edges | `sourceContract` | `claimEvidenceContract` | `claims` | `verificationContract` | `receiptContract` | `protocolContract` | promotion request |
| Source/provenance | node locators and fact posture | citation + provenance | `sourceReference` | claim `source` and optional `evidence` | ordered provenance chain | input/output digests and environment | `protocolSource`, inputs | evidence/review/validation references |
| Evidence or verification | fact posture + evidence grade | evidence grade + verification status | evidence type + verification status | confidence + claim status | trust policy + verification status + attestation | verification chain records steps, not independent truth | checks and validation samples | promotion evidence and review verdict |
| Receipt semantics | graph receipt nodes | `onAccept`, `onReject`, optional `onCite` | receipt reference plus proof/timestamp requirements | source/retrieval/transform/review/accepted-state requirements | reviewer/signoff/format/reference | execution command, hashes, environment, exit status | completion and receipt contract | hash-chained promotion receipt |
| Consumer decision | none | consumer accept/reject requirements | none explicit | accepted/rejected claim states, not repo compatibility | review signoff, not repo compatibility | none | approvals, not repo compatibility | operator promotion decision |
| Supersession/deprecation | node/edge states and `supersedes` relation | `superseded` packet status | `superseded` or `withdrawn` | no shared migration field | `rejected`, no replacement field | `deprecated`, no replacement field | no explicit replacement field | lineage parent and deprecated canon level |

## Non-equivalent concepts that must remain separate

### Versioning

The following are not interchangeable:

- cross-repo contract version;
- payload schema identifier;
- packet/artifact version;
- manifest or ledger version;
- lifecycle state;
- canon level.

The cross-repo envelope therefore uses SemVer only for its own `contract_version`. `payload_version` remains a domain-owned opaque identifier.

### Authority

Current authority objects express different powers:

- who produced or asserted a packet;
- who owns a knowledge or protocol artifact;
- whom an actor may represent;
- the basis of a verification assertion;
- operator permission to promote canon status.

The shared envelope references an `authority_ref`; it must not translate these objects into one universal authority object without a separate authority-model review.

### Evidence, verification, attestation, execution, and promotion

These remain distinct:

- evidence supports a claim;
- verification evaluates evidence or an artifact against a policy;
- attestation is an assertion in a declared format and authority context;
- an execution receipt records what ran and what happened;
- a review receipt records a reviewer decision;
- a promotion receipt records a governed maturity/canon decision.

A reference cannot silently change kind across repositories.

### Lifecycle

`candidate`, `reviewed`, `verified`, `accepted`, `adopted`, and `canonical` do not form one universal ladder. Each belongs to a domain-specific state family. Cross-repo compatibility must map these states explicitly when needed rather than collapse them.

## Additive envelope mapping

| Cross-repo field | Mapping rule |
|---|---|
| `producer.repo` | Repository responsible for the payload schema or artifact release |
| `producer.authority_ref` | Resolvable reference to the domain authority declaration; never a copied replacement authority object |
| `interface.payload_schema_uri` | Versioned or immutable reference to the domain schema |
| `interface.identifier_namespace` | Namespace owned by the producer for artifacts governed by this contract |
| `compatibility.supported_payload_versions` | Domain-owned version identifiers accepted by the producer/consumer declaration |
| `postures.*` | Cross-boundary disclosure and claim posture; does not overwrite domain lifecycle or canon fields |
| `receipts.*` | Required receipt event classes; payload format remains referenced separately |
| `assurance.refs[].kind` | Explicit type preserving evidence/verification/attestation/review/execution/promotion distinctions |
| `lifecycle.*` | Lifecycle of the cross-repo contract itself, not the domain artifact |

## Known gaps

1. Current source references alternate among `github.com`, `raw.githubusercontent.com`, and GitHub Pages `$id` forms.
2. Several schemas use `format: uri` or `format: date-time`, while the stdlib validator intentionally supports only a subset of Draft 2020-12.
3. Evidence Graph uses local `$defs`/`$ref`; the existing stdlib validator does not currently implement reference resolution.
4. Some schemas require strict `additionalProperties: false`; others rely on nested strictness only.
5. Consumer acceptance/rejection is explicit in Source Packet receipt requirements but absent from most other domain schemas.
6. Migration, compatibility, and replacement declarations are not consistently machine-readable.
7. Verification-state vocabularies differ and cannot be safely compared without a domain mapping.

## Decision

Do not normalize existing domain payloads retroactively. Implement interoperability through:

1. a shared additive envelope;
2. versioned payload-schema references;
3. explicit producer/consumer compatibility manifests;
4. typed assurance references;
5. migration and replacement declarations;
6. validation fixtures and receipts.
