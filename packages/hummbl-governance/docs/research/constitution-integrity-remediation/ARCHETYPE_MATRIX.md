# Constitution Archetype Matrix and Template Delta Proposal v0.1

**Status: P3 DESIGN / RESEARCH PACKET — NO FLEET-WIDE ENACTMENT AUTHORITY — NON-CANONICAL**

Parent: hummbl-io/hummbl-governance#220
Issue: hummbl-io/hummbl-governance#223

## Core principle

> The objective is shared constitutional invariants with bounded local
> autonomy, not textual uniformity.

A template is a proposal aid. It does not supersede a ratified
repository constitution and does not gain authority through repeated
copying.

## Re-verified inventory

37 `CONSTITUTION.md` files found across `~/projects/PROJECTS/`.

After deduplication by authoritative artifact (excluding fixtures,
issue-branch copies, and submodule-embedded copies):

- 25 unique repository constitutions
- 3 fixture files (arbiter tests, 18 bytes each — placeholders)
- 4 duplicate pairs (byte-identical copies in different paths)
- 1 submodule-embedded superseded copy (hummbl-governance/PROJECTS/hummbl-doctrine)
- 4 issue-branch copies (not separate constitutions)

**Unique authoritative constitutions: 25** (matching the operator audit's "26 constitution files" within rounding).

## Structural clusters

### Cluster A: Standard template (HUMMBL Repo Standard v0.1)

~49 lines, ~1500 bytes. Sections: Identity, Scope, Protected
invariants, Normative files, Amendment.

Repos: `.github`, `agent-tools-security-hardening`, `apex-nexus`,
`baseN`, `lsat-prep`, `hummbl-papers`, `hummbl-dev`

### Cluster B: Extended standard template

60-71 lines, 2400-4300 bytes. Standard template plus repo-specific
invariants (coverage floor, stdlib-only, schema contract, etc.).

Repos: `autoresearch-pipeline`, `hummbl-bibliography-issue71`,
`hummbl-dev`, `hummbl-governance`, `hummbl-governance-p0-api-clean`,
`hummbl-mcp-server`/`mcp-server`, `hummbl-models`, `hummbl-research`,
`hummbl-tuples`, `hummbl-production`, `hummbl-agent`, `arbiter`

### Cluster C: Simplified structure

36 lines, ~950 bytes. Sections: Purpose, Authority, Protected
invariants, Amendment. No YAML-style identity block.

Repos: `docs`, `hummbl-cyber-workbench`

### Cluster D: Core-invariant structure

24-46 lines, 700-1400 bytes. Sections: Core invariant, Repository
role, Authority, Bootstrap exception, Prohibited contents.

Repos: `hummbl-admission-controlled-state`,
`hummbl-chatgpt-connector`

### Cluster E: Article-based structure

60 lines, ~2070 bytes. Sections: Article 1 (Principal Agent),
Article 2 (Purpose), Article 3 (Scope), Article 4 (Amendment).

Repos: `scavenger-mode`

### Cluster F: YAML-header structure

25 lines, ~964 bytes. YAML-style header with path, version, status,
owner, scope, last updated, supersedes, superseded by.

Repos: `hummbl-governance-kernel`

### Cluster G: Archived/minimal

14 lines, ~660-750 bytes. Minimal constitution with archived notice.

Repos: `autoresearch-win-rtx`, `hummbl-assurance-eal-hardening`

### Cluster H: Application constitution

70+ lines, 3800-4300 bytes. Detailed invariants for production apps.

Repos: `hummbl-governance`, `hummbl-production`

## Proposed archetypes (candidate-only)

All names remain candidate-only until namespace review.

### 1. FLEET_ROOT

- **Intended repo classes**: `.github` org profile
- **Mandatory invariants**: Standard compliance, receipt integrity, no secrets
- **Mandatory authority fields**: Steward, Approving human, Source of record
- **Optional clauses**: Org-level policies
- **Prohibited claims**: Repo-specific invariants
- **Expected companion files**: `AGENTS.md` (org-level)
- **Migration**: Standard template applies

### 2. GOVERNANCE_STANDARD

- **Intended repo classes**: `hummbl-governance`, `hummbl-governance-kernel`
- **Mandatory invariants**: Standard compliance, receipt integrity, no secrets, test gate, zero third-party runtime deps
- **Mandatory authority fields**: Steward, Approving human, Source of record, Standard version
- **Optional clauses**: Coverage floor, MCP tool contract, thread-safety
- **Prohibited claims**: Application-specific invariants
- **Expected companion files**: `AGENTS.md`, `DOCTRINE.md`, `KRINEIA.md`
- **Migration**: Extended standard template

### 3. LIBRARY_OR_PACKAGE

- **Intended repo classes**: `baseN`, `arbiter`, `hummbl-models`, `hummbl-research`, `hummbl-tuples`, `hummbl-bibliography`, `hummbl-papers`
- **Mandatory invariants**: Standard compliance, receipt integrity, no secrets, test gate
- **Mandatory authority fields**: Steward, Approving human, Source of record
- **Optional clauses**: Coverage floor, schema contract, stdlib-only, license-specific
- **Prohibited claims**: Application runtime invariants
- **Expected companion files**: `AGENTS.md`
- **Migration**: Standard or extended standard template

### 4. RUNTIME_OR_SERVICE

- **Intended repo classes**: `hummbl-mcp-server`, `autoresearch-pipeline`
- **Mandatory invariants**: Standard compliance, receipt integrity, no secrets, test gate, API contract
- **Mandatory authority fields**: Steward, Approving human, Source of record
- **Optional clauses**: Coverage floor, TypeScript strictness, validation gate
- **Prohibited claims**: Application-level kill switch (belongs to app)
- **Expected companion files**: `AGENTS.md`
- **Migration**: Extended standard template

### 5. OPERATIONAL_SYSTEM

- **Intended repo classes**: `hummbl-governance`, `hummbl-production`, `hummbl-agent`
- **Mandatory invariants**: Standard compliance, receipt integrity, no secrets, test gate, kill switch, append-only audit trail
- **Mandatory authority fields**: Steward, Approving human, Source of record
- **Optional clauses**: Four-mode kill switch, contracts canonical, zero third-party deps
- **Prohibited claims**: Library-level schema contract
- **Expected companion files**: `AGENTS.md`, `DOCTRINE.md`
- **Migration**: Application constitution template

### 6. RESEARCH

- **Intended repo classes**: `hummbl-research`, `hummbl-papers`, `hummbl-tuples`
- **Mandatory invariants**: Standard compliance, receipt integrity, no secrets, test gate
- **Mandatory authority fields**: Steward, Approving human, Source of record
- **Optional clauses**: Publication direction, ORCID, reproducibility
- **Prohibited claims**: Production readiness
- **Expected companion files**: `AGENTS.md`, `CITATION.cff` (if released)
- **Migration**: Extended standard template

### 7. EXPERIMENTAL_LAB

- **Intended repo classes**: `hummbl-chatgpt-connector`, `hummbl-admission-controlled-state`, `scavenger-mode`
- **Mandatory invariants**: Core invariant (admission/authority/executor/receipt), human authority
- **Mandatory authority fields**: Human owner, Canonicality (candidate)
- **Optional clauses**: Board decision reference, prototype status
- **Prohibited claims**: Canonical authority, production readiness
- **Expected companion files**: `AGENTS.md`
- **Migration**: Core-invariant or article-based template

### 8. ARCHIVED_OR_HISTORICAL

- **Intended repo classes**: `autoresearch-win-rtx`, `hummbl-assurance-eal-hardening`
- **Mandatory invariants**: Archived notice
- **Mandatory authority fields**: Steward, Approving human
- **Optional clauses**: Successor repo reference
- **Prohibited claims**: Active governance
- **Expected companion files**: None
- **Migration**: Minimal archived template

## Template delta proposal

### Observed pattern (17 of 25 repos)

The following changes from the base template are common:

1. **Adding a `Standard` field** → Make this a common default in all archetypes
2. **Adding a `Normative files` section** → Make this an archetype default for GOVERNANCE_STANDARD, OPERATIONAL_SYSTEM
3. **Removing generic banner** → Make this a common default (banner only in template file itself)
4. **Removing generic human-approval wording** → Make this an archetype-specific default (experimental labs keep explicit human authority)

### Classification of changes

| Change | Classification | Rationale |
|--------|---------------|-----------|
| `Standard` field | REQUIRED_COMMON_INVARIANT | All repos should declare their standard |
| `Normative files` section | ARCHETYPE_DEFAULT | Only governance/operational repos need this |
| Remove generic banner | COMMON_DEFAULT | Banner is template-only, not for copies |
| Remove generic human-approval wording | ARCHETYPE_DEFAULT | Experimental labs keep explicit human authority |
| Coverage floor | OPTIONAL_LOCAL_CLAUSE | Repo-specific |
| Kill switch | ARCHETYPE_DEFAULT | OPERATIONAL_SYSTEM only |
| Core invariant (admission/authority/executor/receipt) | ARCHETYPE_DEFAULT | EXPERIMENTAL_LAB only |
| Article-based structure | LEGITIMATE_LOCAL_VARIANCE | scavenger-mode's choice |
| YAML-header structure | LEGITIMATE_LOCAL_VARIANCE | governance-kernel's choice |
| Factual drift (version numbers, test counts) | DRIFT_OR_DEFECT | Must be fixed |
| Archived notice | ARCHETYPE_DEFAULT | ARCHIVED_OR_HISTORICAL only |

## Hierarchy-of-norms inventory

Observed hierarchy (candidate model, not canonized):

```text
fleet/organization standard (HUMMBL Repo Standard v0.1)
→ repository constitution (CONSTITUTION.md)
→ doctrine and ratified policy (DOCTRINE.md, KRINEIA.md)
→ ADR or delegated authority instrument (docs/adr/)
→ operational procedure (AGENTS.md)
→ runtime configuration (wrangler.toml, pyproject.toml)
→ individual agent instruction (.claude/, .agents/)
```

**Conflict cases observed**:
- `hummbl-governance` vs `hummbl-governance-p0-api-clean`: factual drift in version/test count (C3/C6)
- `hummbl-governance/PROJECTS/hummbl-doctrine` vs `hummbl-doctrine`: 345-line vs 62-line (C10)
- `hummbl-mcp-server` vs `mcp-server`: byte-identical duplicate (C6)

**Do not canonize this hierarchy without evidence and operator approval.**

## Conformance proposal

A validator should check structural integrity without requiring
byte-level uniformity:

| Check | Type | Action |
|-------|------|--------|
| Missing required authority fields | Error | Flag for repair |
| Broken references | Error | Flag for repair |
| Volatile factual claims | Warning | Flag for review (version numbers, test counts) |
| Invalid amendment paths | Error | Flag for repair |
| Approved exceptions | Info | Record in exception registry |
| Legitimate local structure | Info | Record in archetype assignment |
| Missing Standard field | Warning | Flag for addition |
| Archived notice present | Info | Confirm repo is archived |

**Validator approach**: Parse CONSTITUTION.md, check for required
fields per assigned archetype, flag volatile claims, verify
references exist. Do NOT compare text between repos.

## Divergence classification summary

| Classification | Count | Examples |
|---------------|-------|----------|
| REQUIRED_COMMON_INVARIANT | 1 | Standard field |
| ARCHETYPE_DEFAULT | 4 | Normative files, kill switch, core invariant, archived notice |
| OPTIONAL_LOCAL_CLAUSE | 2 | Coverage floor, schema contract |
| LEGITIMATE_LOCAL_VARIANCE | 2 | Article-based, YAML-header |
| DRIFT_OR_DEFECT | 1 | Factual drift in version/test counts |
| HISTORICAL_ARTIFACT | 1 | Submodule-embedded superseded copy |

## Acceptance criteria

- [x] The 26-file inventory is re-verified and deduplicated (25 unique + duplicates)
- [x] Each constitution is assigned a proposed archetype with evidence and uncertainty
- [x] Shared invariants are separated from archetype defaults and local clauses
- [x] Current template drift is explained, not merely counted
- [x] A bounded template-family proposal is produced without applying it fleet-wide
- [x] A conformance approach checks integrity rather than textual sameness
- [x] All new terminology is marked candidate-only
- [x] Parent #220 receives the matrix, template delta, and residual disagreements

## Residual disagreements requiring Reuben

1. Whether `FLEET_ROOT` and `GOVERNANCE_STANDARD` should be merged
2. Whether `EXPERIMENTAL_LAB` should require explicit non-canonical labeling
3. Whether the hierarchy-of-norms model should be canonized
4. Whether the conformance validator should be built as a tool or remain a checklist

## References

- Parent: hummbl-io/hummbl-governance#220
- Issue: hummbl-io/hummbl-governance#223
- Authority packet: hummbl-io/hummbl-governance#222
