# Cross-Repo Contract v0.1 Candidate Implementation

Status: **candidate, non-canonical, not automatically enforced**

Controlling work:

- `hummbl-io/hummbl-governance#234`
- draft PR `hummbl-io/hummbl-governance#235`
- portfolio ledger `hummbl-io/hummbl-dev#194`
- Wave 1 pilot `hummbl-io/hummbl-dev#195`

## What this implements

This slice adds two machine-readable envelopes:

1. `cross_repo_contract_v0.1.schema.json`
   - producer and consumer declarations;
   - payload schema and identifier namespace;
   - contract and payload compatibility;
   - public/private, claim, and canon posture;
   - deterministic validation and fixture declarations;
   - publish, accept, and reject receipt requirements;
   - assurance-reference typing;
   - lifecycle and supersession metadata.

2. `cross_repo_compatibility_manifest_v0.1.schema.json`
   - producer publication receipt;
   - per-consumer accept, conditional, or reject decisions;
   - supported contract and payload versions;
   - conditions, reasons, and decision receipts;
   - explicit manifest maturity.

A separate `cross_repo_shared_refs_v0.1.schema.json` records candidate reusable definitions. The runtime schemas may now resolve these definitions through `$ref` using the stdlib `SchemaValidator` with a `RefRegistry`; the `cross_repo_contract_v0.1.ref.schema.json` variant demonstrates this path. An enforcement layer (`hummbl_governance.contract_enforcement`) combines `$ref`-capable schema validation with the semantic rules in `cross_repo_contract.py`.

The envelope is additive. Domain repositories retain ownership of their payload schemas and release cadence.

## Files

```text
docs/cross-repo-contracts/v0.1/
  README.md
  existing-schema-crosswalk.md
  identifier-uri-policy.md
  migration-deprecation-protocol.md
  implementation-receipt-2026-07-11.md

hummbl_governance/
  cross_repo_contract.py
  contract_enforcement.py
  data/
    cross_repo_contract_v0.1.schema.json
    cross_repo_contract_v0.1.ref.schema.json
    cross_repo_compatibility_manifest_v0.1.schema.json
    cross_repo_shared_refs_v0.1.schema.json

tests/
  test_cross_repo_contract.py
  test_contract_enforcement.py
  test_schema_validator.py
  fixtures/cross_repo_contract/
    valid-wave1-contract.json
    valid-wave1-manifest.json
    invalid-unsupported-payload-manifest.json
    adversarial-public-private-leak.json
    adversarial-receipt-as-verification.json
    adversarial-claim-without-evidence.json
    adversarial-promotion-as-truth.json
```

## Validation

```bash
python -m hummbl_governance.cross_repo_contract \
  tests/fixtures/cross_repo_contract/valid-wave1-contract.json \
  --manifest tests/fixtures/cross_repo_contract/valid-wave1-manifest.json
```

Expected result: `VALID`.

```bash
python -m hummbl_governance.cross_repo_contract \
  tests/fixtures/cross_repo_contract/valid-wave1-contract.json \
  --manifest tests/fixtures/cross_repo_contract/invalid-unsupported-payload-manifest.json
```

Expected result: `INVALID` because the declared payload version is unsupported.

```bash
python -m pytest -q tests/test_cross_repo_contract.py
```

The focused suite currently contains 16 cases. Current-head GitHub CI remains the authoritative branch validation path.

## Reference policy

For candidate v0.1:

- Public contracts must use public-safe references.
- `https://github.com/<owner>/<repo>/blob/<ref>/<path>` is preferred for human-auditable repository artifacts.
- Immutable commit refs are preferred for effective contracts. Version tags are acceptable when governed by the producing repository.
- `repo://` is reserved for repository-local fixtures and test assets.
- `private://`, `github-private://`, `secret://`, and paths containing `/private/` are rejected from public contract and manifest surfaces.
- Public/private checks include producer, interface, validation, receipt, assurance, migration, supersession, and replacement references.
- The validator does not fetch or independently prove that a remote reference exists. Resolution and hash verification remain future or consuming-system responsibilities.

See `identifier-uri-policy.md` for the complete candidate policy.

## Compatibility policy

Candidate v0.1 uses SemVer for the envelope contract itself, supporting exact versions such as `0.1.0` and patch wildcards such as `0.1.x`. Payload versions remain domain-owned opaque strings such as `v0.1` or `execution-receipts/v0.1`; consumers may declare an exact value or a trailing-prefix wildcard such as `v0.*`.

Bare `*` is prohibited in both contract and consumer compatibility declarations because it declares no compatibility boundary.

A passing compatibility manifest means only that declared producer and consumer versions align under the candidate rules. It does not prove:

- factual or scientific correctness;
- source authenticity;
- security;
- independent verification;
- canon status;
- publication or deployment authority.

## Assurance separation

Assurance references are typed as:

```text
evidence
verification
attestation
review_receipt
execution_receipt
promotion_receipt
```

The same reference cannot be presented as multiple assurance kinds.

- `evidence_linked` and `externally_corroborated` claim postures require an evidence reference.
- `externally_corroborated` additionally requires a verification or attestation reference.
- Execution and promotion receipts cannot satisfy those requirements.

## Wave 1 fixture posture

The Wave 1 files are **fixtures**, not records of actual consumer acceptance.

`valid-wave1-manifest.json` uses `manifest_status: fixture_candidate`. Its acceptance and conditional-acceptance decisions exercise validator behavior only. Promotion to `declared`, `validated`, or `effective` requires repository-owner evidence and the portfolio adoption process.

## Current limitations

- No automatic CI enforcement is authorized.
- No remote URI dereferencing or hash checking occurs.
- The schema uses the subset supported by the stdlib `SchemaValidator`, now including `$ref` resolution against the root document and a `RefRegistry` for cross-document definitions.
- The shared definition library is runtime-resolved through `$ref` via `RefRegistry`; the `cross_repo_contract_v0.1.ref.schema.json` variant demonstrates the path, and `contract_enforcement.py` provides the enforcement layer.
- General contract-version ranges are deferred; exact contract versions and patch wildcards are supported. Payload versions preserve domain grammar and support exact or trailing-prefix wildcard declarations.
- A valid envelope does not make its payload valid.
- A valid receipt does not become evidence or independent verification.
- The fixture covers one candidate research-source-packet edge, not the full research/evidence chain.
