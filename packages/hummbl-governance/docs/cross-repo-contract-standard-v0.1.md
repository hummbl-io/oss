# Cross-Repo Contract Standard v0.1 — Identifiers, Interface Manifests, Compatibility, and Receipts

**Status: PROPOSED ORGANIZATION-WIDE INTERFACE STANDARD — NON-CANONICAL — NO AUTOMATIC ENFORCEMENT**

Issue: hummbl-io/hummbl-governance#234

## Purpose

Define how HUMMBL repositories create, version, publish, consume, validate, reject, migrate, supersede, and retire cross-repo contracts without duplicating domain schemas or silently forcing breaking changes on sibling repositories.

This issue formalizes the reusable contract layer connecting the research/evidence spine:

```text
hummbl-bibliography
→ research-source-packets
→ hummbl-research
→ claim-evidence-ledger
→ hummbl-papers
→ public/release surfaces
```

## Existing contract/schema artifacts (10)

1. `hummbl-io/docs/evidence-graph/v0.1/schema.json` — minimal completed-batch graph
2. `research-source-packets/schemas/research-source-packets-v0.1.json` — bounded source packet
3. `claim-evidence-ledger/schemas/claim-evidence-ledger-v0.1.json` — claim/evidence pair
4. `knowledge-as-code/schemas/knowledge-as-code-v0.1.json` — versioned knowledge packet
5. `ai-source-verification/schemas/ai-source-verification-v0.1.json` — provenance chain
6. `execution-receipts/schemas/execution-receipts-v0.1.json` — execution inputs/outputs
7. `protocol-as-code/schemas/protocol-as-code-v0.1.json` — bounded protocol contract
8. `hummbl-bibliography/dist/scientific-grounding-map.json` — citation contract
9. `hummbl-tuples` — EVIDENCE, ATTEST, PROMOTION_RECEIPT tuple patterns
10. `hummbl-governance/hummbl_governance/data/canon_registry.schema.json` — artifact promotion

## Interoperability gaps

Current schemas independently vary in:
- `schemaVersion` representation (`0.1`, `v0.1`, `0.1.0`, namespaced strings, numeric)
- identifier grammar and namespace ownership
- authority object shape
- lifecycle states
- evidence grades and verification states
- receipt semantics and strength
- public/private/canon posture
- producer and consumer declarations
- version compatibility and migration rules
- acceptance/rejection behavior
- supersession/deprecation rules

## Governing design decision

The cross-repo contract must be an **additive envelope** around domain-owned payload schemas. It must not replace or flatten domain schemas.

## Proposed ownership model

### `hummbl-governance`

- cross-repo contract standard
- shared schema definitions
- compatibility and migration rules
- conformance fixtures
- assurance and adoption boundaries

### `hummbl-io/hummbl-io`

- organization-level contract registry/index
- worked cross-repo integration graphs
- program-level issue routing
- topology and adoption receipts

### Domain payload owners

Each repository owns its payload schema and release cadence. The shared contract references it by immutable or versioned URI.

## Repository connection topology (5 tiers)

### Tier 1 — core contract spine

`hummbl-bibliography`, `research-source-packets`, `hummbl-research`, `claim-evidence-ledger`, `hummbl-papers`, `hummbl-governance`, `hummbl-io/hummbl-io`

### Tier 2 — assurance and provenance overlays

`ai-source-verification`, `execution-receipts`, `hummbl-tuples`, `general-claim-validator`, `hummbl-toolkit` (evidence-gate), `arbiter`, `protocol-as-code`, `knowledge-as-code`

### Tier 3 — semantic and scholarly consumers

`hummbl-theory`, `hummbl-doctrine`, `base120`, `baseN`

### Tier 4 — experiment, benchmark, and runtime producers/consumers

`autoresearch-pipeline`, `model-routing-as-code`, `hummbl-agent`, `agent-runtime-governance`, `hummbl-production`, `mcp-server`

### Tier 5 — domain pilots and conditional consumers

`hummbl-medical`, `corpus`, peptide-science work, future regulated/health/historical/product repos

## Candidate cross-repo contract envelope

```yaml
schema_version:
contract_id:
contract_version:
contract_status:

producer:
  repo:
  authority_ref:
  artifact_locator:

consumers:
  - repo:
    requirement: required | optional | advisory

interface:
  artifact_type:
  payload_schema_uri:
  identifier_namespace:
  locator_pattern:

compatibility:
  supported_contract_versions: []
  supported_payload_versions: []
  breaking_change_policy:
  migration_refs: []

postures:
  visibility:
  privacy:
  claim_posture:
  canon_posture:

validation:
  deterministic_commands: []
  valid_fixtures: []
  invalid_fixtures: []
  adversarial_fixtures: []
  offline_core_required: true

receipts:
  on_publish: []
  on_accept: []
  on_reject: []
  receipt_schema_refs: []

lifecycle:
  effective_at:
  review_by:
  supersedes: []
  deprecated_at:
  replacement_contract_ref:
```

## Required shared definitions (10)

- `repo_ref`
- `artifact_ref`
- `schema_ref`
- `actor_or_authority_ref`
- `receipt_ref`
- `identifier_namespace`
- `version_range`
- `compatibility_declaration`
- `visibility_privacy_posture`
- `supersession_ref`

## Required deliverables (14)

1. Existing-schema inventory and field crosswalk
2. `cross-repo-contract-v0.1.schema.json` candidate
3. Shared-reference definitions and URI policy
4. Cross-repo identifier and namespace policy
5. Compatibility-manifest schema
6. Producer/consumer acceptance and rejection receipt contract
7. Migration and deprecation protocol
8. Deterministic stdlib-only validator or validator stub
9. Valid fixture using the completed scientific-grounding chain
10. Invalid fixture with a dangling artifact or unsupported payload version
11. Adversarial fixtures (7): silent drift, public-to-private leakage, claim without evidence, receipt as verification, promotion as truth, unsupported version acceptance, copied metadata divergence
12. Compatibility test manifest for peptide pilot (#146)
13. Adoption plan (no retroactive compliance labeling)
14. AAR and bounded implementation receipt

## Acceptance criteria

- [x] 10 existing schemas inventoried
- [x] 11 interoperability gaps documented
- [x] Additive envelope design decision documented
- [x] 5-tier topology documented
- [x] Contract envelope schema documented (30+ fields)
- [x] 10 shared definitions listed
- [x] 14 deliverables listed
- [x] 7 adversarial fixture types listed
- [ ] Existing schemas reused by reference
- [ ] Domain payload ownership preserved
- [ ] Producer/consumer repositories explicit
- [ ] Contract and payload versions independent
- [ ] Identifier namespaces and collision rules explicit
- [ ] Breaking changes require new version + migration note
- [ ] Consumers can accept/conditionally accept/reject
- [ ] Offline validation works for core path
- [ ] One complete research/evidence path validates
- [ ] One adversarial fixture fails for expected reason
- [ ] Public/private and claim/canon postures distinct
- [ ] Evidence, attestation, promotion receipts distinct
- [ ] No existing repo treated as compliant without evidence
- [ ] Operator approval before org-wide adoption

## Non-goals

- Creating a new repository before existing homes proven insufficient
- Building an all-to-all service mesh
- Replacing domain schemas with a universal mega-schema
- Unifying every lifecycle/status enum
- Enabling automatic cross-repo writes
- Enforcing candidate schema in CI before review and pilot
- Granting publication, canonization, release, deployment, or merge authority
- Treating schema validity as truth, scientific validity, or external corroboration

## Cross-repo dependencies

- `hummbl-io/hummbl-io#104` — completed minimal graph
- `hummbl-io/hummbl-io#105` — completed implementation slice
- `hummbl-io/hummbl-io#146` — active domain integration pilot
- `hummbl-io/hummbl-io#153` — research-integrity master index
- `hummbl-io/hummbl-governance#225` — research-integrity parent standard
- `hummbl-io/hummbl-papers#19` — publication gate
- `hummbl-io/hummbl-io#154` — repository responsibility topology

## Fact posture

This is a proposed organization-wide interface standard derived from issue #234. Non-canonical. No automatic enforcement. All schemas, definitions, and deliverables are candidate until reviewed and pilot-validated.

## Receipt

- **Issue**: hummbl-io/hummbl-governance#234
- **Existing schemas**: 10
- **Interoperability gaps**: 11
- **Topology tiers**: 5
- **Contract envelope fields**: 30+
- **Shared definitions**: 10
- **Deliverables**: 14
- **Adversarial fixtures**: 7
- **Cross-repo deps**: 7
- **Review status**: PENDING
