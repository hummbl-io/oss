# Cross-Repo Identifier and URI Policy v0.1

Status: **candidate — non-canonical — no automatic enforcement**

## Purpose

Define bounded identifier ownership and reference rules for the candidate cross-repo contract layer without taking ownership of domain payload identifiers.

## Identifier classes

### Contract identifier

```text
crc:<authority-namespace>:<contract-name>
```

Example:

```text
crc:hummbl-dev:research-source-packet
```

Rules:

- `crc` identifies the cross-repo contract class.
- The middle segment identifies the authority namespace responsible for the contract declaration.
- The final segment is stable across compatible contract revisions.
- Breaking contract semantics require a new major contract version or a new contract identifier with an explicit migration.
- A contract identifier does not identify an individual payload instance.

### Compatibility-manifest identifier

```text
crm:<authority-namespace>:<manifest-name>
```

A compatibility manifest records a bounded producer/consumer decision set. It does not grant authority beyond the referenced contract.

### Domain artifact identifier namespace

`interface.identifier_namespace` is owned by the producing repository. The cross-repo layer records the namespace but does not redefine its grammar.

Examples may include:

```text
rsp:<producer-defined-id>
claim:<producer-defined-id>
receipt:<producer-defined-id>
```

These examples are not universal reserved namespaces unless separately admitted by the owning repositories.

## Ownership and collision rules

1. A repository may declare only namespaces it owns or is explicitly delegated to operate.
2. Two producers must not independently claim the same namespace without a shared authority declaration.
3. Repository rename or transfer does not silently transfer namespace authority; a rebinding or migration record is required.
4. Identifier reuse after retirement is prohibited unless the identifier explicitly denotes a versioned lineage and the replacement is declared.
5. Human-readable labels may change; stable identifiers must not silently change with them.
6. Cross-repo contract IDs, payload IDs, receipt IDs, and canon/promotion IDs remain separate identifier classes.

## Reference classes

### Payload schema references

For candidate contracts, these are acceptable:

- immutable GitHub blob references containing a commit SHA;
- version-tag references where the producing repository governs tags;
- repository `main` references only while the contract remains candidate or fixture-only;
- stable published schema URLs with a documented release process.

For an effective contract, prefer an immutable content-addressed or commit-addressed reference.

### Authority references

Authority references may point to:

- a versioned authority declaration;
- a repository governance file;
- an approved issue or decision record;
- a signed or otherwise governed authority artifact.

An issue or PR reference proves only that the referenced GitHub object exists and contains the cited declaration. It does not make the declaration canonical by itself.

### Receipt references

Logical receipt identifiers such as `receipt:<type>:<id>` require a declared resolver or accompanying URI before they may be relied upon outside fixtures.

A receipt reference must preserve its type. An execution receipt cannot be re-labeled as verification, and a promotion receipt cannot be re-labeled as evidence.

### Repository-local fixture references

```text
repo://<path>
```

`repo://` is reserved for test and fixture paths resolved relative to the repository containing the contract implementation. It must not be used as a portable production locator.

## Public/private policy

Public contracts and manifests must not expose private or sensitive locators.

The v0.1 validator rejects bounded markers including:

```text
private://
github-private://
secret://
/private/
```

This is a narrow guard, not comprehensive secret scanning. Producers and reviewers remain responsible for broader disclosure review.

For public contracts:

- `privacy` must be `public_safe` or `metadata_only`;
- public metadata must not make a private payload retrievable;
- hashes of sensitive artifacts require a privacy analysis because hashes may enable correlation or confirmation attacks;
- public references to private repository names or paths require explicit approval and a safe disclosure rationale.

## Mutable versus immutable locators

| Locator | Candidate fixture | Declared contract | Effective contract |
|---|---:|---:|---:|
| branch such as `main` | allowed | discouraged | not sufficient alone |
| version tag | allowed | allowed with tag policy | allowed with immutability evidence |
| commit SHA | preferred | preferred | preferred |
| content digest | preferred where available | preferred | preferred with resolver |
| issue or PR | allowed for work/authority context | allowed for decision context | insufficient as payload schema locator |
| local path | allowed through `repo://` | repository-scoped only | insufficient for portable consumers |

## Hash and resolution posture

A locator and a digest answer different questions:

- locator: where the artifact is expected to be found;
- digest: which exact bytes are expected;
- authority reference: who is allowed to assert or release it;
- receipt: what action or decision occurred;
- verification record: what checks were performed and with what result.

The v0.1 validator validates reference shape and bounded disclosure rules. It does not dereference remote URLs or calculate remote hashes.

Any statement that a reference was resolved or hash-verified requires a dated execution or verification receipt.

## Version rules

- `contract_version` uses SemVer.
- `schema_version` identifies the candidate envelope schema.
- `payload_version` remains an opaque producer-owned identifier.
- Exact payload version matching is supported.
- A non-empty trailing-prefix wildcard may be used, for example `v0.*`.
- Bare `*` is prohibited because it declares no compatibility boundary.
- Consumer support declarations must not silently broaden when a producer changes version grammar.

## Supersession and rebinding

When a repository, namespace, schema URL, or artifact locator changes:

1. publish the replacement reference;
2. declare the old and new identifiers or locators;
3. state whether identity is preserved or a new identity is created;
4. provide a migration or rebinding reference;
5. record producer publication and consumer acceptance/rejection receipts;
6. retain the old reference long enough to support audit and rollback where lawful and practical.

## Non-goals

- universalizing every HUMMBL identifier;
- creating a global resolver in v0.1;
- treating GitHub URLs as permanent by default;
- publishing private references;
- asserting that a syntactically valid locator resolves;
- granting namespace authority through first use alone.
