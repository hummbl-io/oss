# HUMMBL Chronology to Narrative Map

Date: 2026-06-24
Status: governed narrative-mapping artifact
Evidence label: `repo_local_observed` — this artifact is a framework document
constructed from local repo observation and a validation pass summary. It is
not itself `validator_backed` or `source_backed` unless specific claims
within it carry those labels.
Canonical home: `hummbl-governance/docs/ecosystem/`

Source basis:
- `hummbl-governance/docs/ecosystem/VALIDATION_PASS_1_SUMMARY_2026-06-24.md`
  (redacted public-safe validation-pass summary)
- Connector-visible `hummbl-io` repository chronology supplied in session
  context — `scratch_context`, non-reproducible. This chronology is not
  checked into any repo as a committed artifact. It must not be treated as
  canonical evidence. Pass 1 of the recommended extraction passes (§9)
  is to commit a `HUMMBL_REPO_CHRONOLOGY_EVIDENCE.csv` with GitHub
  `created_at` timestamps, at which point this source-basis entry will be
  replaced with a reference to that checked-in artifact.

This artifact is a map, not final public copy. It defines how chronological
repository data may be translated into governed narratives without converting
internal, unproven, stale, private, or quarantined material into public-safe
assertions.

## 1. Narrative Purpose

The purpose of this map is to turn repository chronology into structured
narrative options while preserving evidence boundaries.

It supports four uses:

1. Internal archaeology: explain how HUMMBL concepts, repos, and governance
   primitives emerged over time.
2. Refactor planning: decide which repos should be classified as canonical,
   derived, archive, fork/import, product surface, or scratch/context.
3. Doctrine tracking: identify where ideas first appeared, where they
   matured, and where they are now canonical.
4. Public-story preparation: generate candidate narrative projections that
   can later be evidence-checked before publication.

This map does not authorize external claims about compliance, certification,
partner status, production quality, revenue, market size, customer adoption,
medical readiness, or benchmark superiority.

## 2. Evidence Rules

All **narrative projections** (§7) and **claim-risk records** (§6) must carry
one of the following evidence labels. This section's labeling requirement
applies to downstream narrative outputs derived from this map, not to the
framework document itself (which is `repo_local_observed` as stated in the
header).

| Label | Meaning | Public-use posture |
|---|---|---|
| `validator_backed` | Supported by a local validator or structured check, such as claim/evidence manifest validation. | May be used internally. Public use requires dated command, repo path, commit or artifact reference, and reviewer. |
| `source_backed` | Supported by a primary or official source checked for the claim. | May be adapted for public use if the source is fresh, cited, and wording preserves attribution and caveats. |
| `repo_local_observed` | Observed in local repo files or manifests but not independently verified externally. | Internal-safe. Public use requires source packaging and review. |
| `internally_estimated` | Based on HUMMBL internal estimate, forecast, planning assumption, or target. | Not public-safe as fact. May be framed only as internal planning assumption if authorized. |
| `unproven` | Explicitly tracked as unproven or lacking sufficient evidence. | Do not publish as assertion. |
| `quarantined` | Explicitly blocked from reuse as factual assertion. | Do not publish. May appear only as an example of a rejected prior claim. |
| `stale_or_time_sensitive` | Potentially true at one time but requires refresh before reuse, especially legal, regulatory, pricing, benchmark, or product claims. | Do not publish without same-day or publication-window refresh from primary sources. |
| `private_requires_authorization` | Depends on private, confidential, customer, partner, local machine, or consent-gated evidence. | Do not externally verify or publish without explicit authorization and approved wording. |
| `scratch_context` | Exists outside canonical repo/admitted source paths or was produced as exploratory context. | Do not treat as canonical until admitted. |

### Validation-pass constraints

From the 2026-06-24 validation pass (see
`VALIDATION_PASS_1_SUMMARY_2026-06-24.md` for the full redacted summary):

- `hummbl-production` public claims manifest is structurally valid and
  evidence-linked (`validator_backed`), but 12 tier-C internal estimates are
  over-promoted as `validated` and should remain `unproven` until relabeled
  or externally supported.
- `hummbl-production` has 8 explicitly `unproven` claims (`MA-013`,
  `MA-014`, `GE-004`, `GE-005`, `EP-011`, `BB-009`, `SO2-007`, `AD5-010`).
  These must not become public-safe assertions.
- `hummbl-governance` coverage matrix has 0 unresolvable local evidence
  references by its validator (`validator_backed` for resolvability). This
  supports resolvability, not blanket truth of every mapped claim.
- The DeepSeek dataset ledger is static-only and not live-validated
  (`repo_local_observed`). It contains 4 duplicate exact URLs that are
  invalidated for ingestion until deduplicated. It must not be represented
  as a live-verified ingestion allowlist.
- Opus/Devin claims `ODG-C9`, `ODG-C10`, and `ODG-C11` remain `quarantined`.
- Opus/Devin claims `ODG-C2`, `ODG-C3`, `ODG-C7`, and `ODG-C8` are
  `stale_or_time_sensitive` — benchmark values rely on system-card PDF or
  SWE-Bench Pro paper extractions that were not reopened in this pass. They
  need direct source refresh before external use.
- Opus/Devin claims `ODG-C12` through `ODG-C16` are `repo_local_observed`
  — repo-local implementation/absence claims that require file/test audit
  before external promotion.
- EU AI Act enacted-law baseline claims are `source_backed` (EUR-Lex), but
  Digital Omnibus timeline claims are `stale_or_time_sensitive` and need
  fresh official-source verification before external use.
- Private/internal claims require authorization before external verification
  or publication.

## 3. Chronology Strata

The connector-visible `hummbl-io` repo order can be used as a creation-order
proxy, not as exact `created_at` evidence unless refreshed through GitHub
metadata.

| Stratum | Approx. chronology indexes | Working name | Narrative function | Evidence posture |
|---|---:|---|---|---|
| `S1` | 1-15 | Research, primitives, runtime genesis | Original research, Base120, governance runtime, production, agent runtime, hummbl-governance, Arbiter. | `repo_local_observed` until each repo is inspected. |
| `S2` | 16-35 | Identity, archives, imports, tooling | Credentialing/profile/org defaults, archives, forks/imports, brand/tooling. | Mixed; likely contains archive and fork/import material requiring classification. |
| `S3` | 36-60 | Autoresearch, doctrine, evidence surfaces | Autoresearch, spacetime/doctrine, KRINEIA, stylized archive/public-surface experiments, applied evidence/product repos. | High narrative value, high overclaim risk. |
| `S4` | 61-80 | Skills, validators, HUAOMP/MTSMU, corpus | Skills, agent/showcase/import surfaces, claim validators, HUAOMP, MTSMU, BaseN, corpus. | Requires doctrine-emergence extraction before public use. |
| `S5` | 81-95 | Public/product/spec/fleet surfaces | Music/jobs/spec/docs/toolkit/kernel/fleet/gameboard/public-docs/cyber workbench. | Likely best for outward-facing projections after claim review. |

### Stratum boundary evidence

The stratum index boundaries (1-15, 16-35, 36-60, 61-80, 81-95) are
`internally_estimated` — they are planning heuristics constructed by the
artifact author, not validated classifications. The boundary numbers reflect
approximate grouping by observed repo themes, not deterministic thresholds.
Any narrative use of stratum assignments should treat them as provisional
until a repo-role classification pass (§9, Pass 2) validates them.

### Chronology rule

Use oldest-to-newest for archaeology and refactor integrity. Use
newest-to-oldest only for doctrine propagation after canonicality has been
classified.

Do not infer intentional design from order alone. A repo appearing earlier
means only that it appears earlier in connector-returned order, unless
confirmed by GitHub `created_at`, commits, or admission records.

## 4. Repo-Role Classification Schema

Each repo should be classified before it is used as narrative evidence.

```yaml
repo_role_record:
  repo: "hummbl-io/example"
  chronology_index: 0
  chronology_evidence:
    source: "connector_order|github_created_at|git_history|manual"
    checked_at: "YYYY-MM-DD"
    confidence: "high|medium|low"
  stratum: "S1|S2|S3|S4|S5"
  role:
    primary: "canonical_runtime|canonical_primitive|research_root|doctrine_source|product_surface|public_docs|archive|fork_import|scratch_context|tooling|unknown"
    secondary: []
  canonicality:
    status: "canonical|derived|candidate|archive|fork_import|scratch|unknown"
    canonical_successor: ""
    admission_record: ""
  evidence_state:
    label: "validator_backed|source_backed|repo_local_observed|internally_estimated|unproven|quarantined|stale_or_time_sensitive|private_requires_authorization|scratch_context"
    basis: ""
  public_claim_risk: "low|medium|high|blocked"
  safe_narrative_use: ""
  blocked_narrative_use: ""
  next_check: ""
```

### Role definitions

| Role | Definition | Narrative use |
|---|---|---|
| `canonical_runtime` | Repo currently hosts operational runtime or system implementation. | Can anchor execution narrative if validated. |
| `canonical_primitive` | Repo currently hosts reusable governance, evidence, or safety primitives. | Can anchor doctrine/architecture narrative if versioned. |
| `research_root` | Repo captures early research, theory, notes, or conceptual seeds. | Useful for archaeology, not proof of current capability. |
| `doctrine_source` | Repo introduces or consolidates named doctrine, protocol, or vocabulary. | Useful for idea lineage. Requires first-appearance evidence. |
| `product_surface` | Repo presents user-facing or buyer-facing product surface. | High public-claim risk; requires claim audit. |
| `public_docs` | Repo hosts external documentation. | Requires strong freshness and public-claim review. |
| `archive` | Historical or superseded repo. | May show evolution; must not imply current status. |
| `fork_import` | Forked, imported, mirrored, vendored, or third-party-origin material. | Must not be used as original invention evidence without attribution. |
| `scratch_context` | Exploratory context outside admitted canonical paths. | Not canonical evidence. |
| `tooling` | Build, automation, connector, or developer workflow support. | Supports operational narrative only after validation. |
| `unknown` | Not yet classified. | Do not use externally. |

## 5. Doctrine-Emergence Schema

Narratives should track doctrines as evolving objects, not as timeless claims.

```yaml
doctrine_emergence_record:
  doctrine: "receipts|evidence_gates|claims_protocol|Base120|KRINEIA|MTSMU|HUAOMP|coordination_bus|governance_primitives|agent_fleet|registry|other"
  first_observed:
    repo: ""
    path_or_artifact: ""
    date_basis: "connector_order|commit_timestamp|file_date|handoff"
    evidence_label: "validator_backed|source_backed|repo_local_observed|internally_estimated|unproven|quarantined|stale_or_time_sensitive|private_requires_authorization|scratch_context"
  maturation_points:
    - repo: ""
      artifact: ""
      change: "renamed|implemented|validated|productized|retired|quarantined|superseded"
      evidence_label: "validator_backed|source_backed|repo_local_observed|internally_estimated|unproven|quarantined|stale_or_time_sensitive|private_requires_authorization|scratch_context"
  current_canonical_home:
    repo: ""
    path_or_package: ""
    evidence_label: "validator_backed|source_backed|repo_local_observed|internally_estimated|unproven|quarantined|stale_or_time_sensitive|private_requires_authorization|scratch_context"
  current_public_safe_wording: ""
  unsafe_wording: ""
  open_questions: []
```

### Doctrine states

| State | Meaning |
|---|---|
| `seed` | Early conceptual appearance; not yet implementation evidence. |
| `prototype` | Implemented or structured but not validated/admitted. |
| `validated_local` | Validator-backed or test-backed locally. |
| `governed` | Has policy, schema, acceptance, or review boundaries. |
| `canonicalized` | Has admitted canonical home and naming. |
| `public_ready_candidate` | May be transformed into public copy after claim review. |
| `blocked` | Must not be used as assertion. |
| `retired` | Superseded or no longer active. |

## 6. Claim-Risk Schema

Every narrative projection should classify its claims before drafting prose.

```yaml
claim_risk_record:
  claim_id: ""
  claim_text: ""
  claim_type: "chronology|capability|legal|regulatory|benchmark|market|revenue|partner|customer|production|medical|security|compliance|origin|doctrine|other"
  evidence_label: "validator_backed|source_backed|repo_local_observed|internally_estimated|unproven|quarantined|stale_or_time_sensitive|private_requires_authorization|scratch_context"
  risk: "low|medium|high|blocked"
  public_posture: "public_candidate|internal_only|consent_gated|requires_refresh|do_not_publish"
  required_evidence: []
  allowed_wording: ""
  disallowed_wording: ""
  reviewer_required: []
```

### Claim-risk defaults

| Claim type | Default risk | Notes |
|---|---|---|
| `chronology` | Medium | Connector order is a proxy until GitHub timestamps or git evidence are captured. |
| `capability` | Medium-high | Requires implementation path, version, and validation boundary. |
| `legal` | High | Requires primary legal source and legal review before external use. |
| `regulatory` | High | Time-sensitive; refresh before publication. |
| `benchmark` | High | Requires exact benchmark, model version, source, and attribution. |
| `market` | High | Internal estimates are not facts. |
| `revenue` | High | Private and time-sensitive. |
| `partner` | Blocked by default | Requires acceptance evidence and naming permission. |
| `customer` | Blocked by default | Requires consent, approved wording, and confidentiality review. |
| `production` | Medium-high | Requires dated runtime receipts and system-boundary caveats. |
| `medical` | High | Must not imply HIPAA/FDA/FHIR/DICOM readiness without domain evidence pack. |
| `security` | High | Avoid certification or assurance overclaims. |
| `compliance` | High | Evidence maps are not compliance determinations. |
| `origin` | Medium-high | Requires first-appearance evidence and fork/import exclusion. |
| `doctrine` | Medium | Internal doctrine can be described if scoped and not overclaimed. |

## 7. Candidate Narrative Projections

These are narrative projections, not final public stories. Each projection
must classify its claims using the §6 schema before drafting prose.

### Projection A: Archaeological Strata

Core move:

> HUMMBL can be understood as layered strata: research roots, governance
> primitives, runtime systems, evidence/claim surfaces, doctrine
> consolidation, and public/product projections.

Evidence posture:

- `repo_local_observed` from connector order.
- Stratum boundaries are `internally_estimated` (§3).
- Requires GitHub `created_at`, git history, or repo admission records
  before public chronology claims.

Safe internal use:

- Refactor sequencing.
- Repo classification.
- Doctrine extraction planning.

Unsafe public leap:

- Claiming deliberate long-range architecture solely from repo order.

### Projection B: Governance Primitive Emergence

Core move:

> The chronology suggests a movement from research and vocabulary toward
> reusable governance primitives, runtime receipts, claim validation, and
> public evidence surfaces.

Evidence posture:

- Partially `validator_backed` where current validators pass.
- Partially `repo_local_observed` until each primitive is traced to
  canonical implementation.

Safe internal use:

- Identify primitive lineage across `base120`, `hummbl-governance`,
  `hummbl-governance`, `krineia`, `hummbl-production`, and related repos.

Unsafe public leap:

- Claiming certification, compliance, or third-party assurance from
  self-issued receipts or local validators.

### Projection C: Evidence Discipline as Product Spine

Core move:

> Later repos increasingly express a product spine around evidence, claims,
> receipts, validators, and governed action.

Evidence posture:

- `hummbl-production` has validator-backed public claim gates with warnings
  (`validator_backed` for structure; 12 tier-C claims are `unproven`).
- `hummbl-governance` has validator-backed resolvability checks
  (`validator_backed` for resolvability, not truth).
- Public claim risk remains high until tier-C overclaims and unproven claims
  are corrected.

Safe internal use:

- Position evidence discipline as a design principle.
- Use validators as operational controls, not proof of market or compliance
  status.

Unsafe public leap:

- Saying HUMMBL claims are all verified, compliance-ready, or
  publication-ready.

### Projection D: Doctrine Propagation

Core move:

> Newer repos can be read as doctrine propagation surfaces; older repos can
> be mined to locate where each doctrine began and how it changed.

Evidence posture:

- `repo_local_observed` until first-appearance extraction is complete.

Safe internal use:

- Build a doctrine-emergence table for `receipts`, `claims`, `Base120`,
  `KRINEIA`, `MTSMU`, `HUAOMP`, `coordination bus`, `evidence gates`, and
  `agent fleet`.

Unsafe public leap:

- Treating all named doctrines as current, implemented, validated, or
  canonical.

### Projection E: Refactor Integrity Narrative

Core move:

> Chronology creates a refactor order: oldest-to-newest for archaeology,
> authority-first for canonical runtime and primitives, newest-to-oldest
> for doctrine propagation after classification.

Evidence posture:

- `internally_estimated` — internal planning projection.
- Not a public claim.

Safe internal use:

- Classify repos before merging, archiving, renaming, or publicizing them.

Unsafe public leap:

- Presenting refactor order as user-visible roadmap or commitment.

## 8. Blocked / Unsafe Narrative Moves

The following moves are blocked unless separately validated and approved.

| Unsafe move | Why blocked | Required before use |
|---|---|---|
| `All HUMMBL claims are validated.` | Validation pass found warnings, unproven claims, static-only ledgers, and quarantined claims. | Correct warnings, resolve unproven claims, and rerun validators. |
| `The DeepSeek dataset list is live-verified.` | Ledger is explicitly static-only and not live-verified individually. | Live URL, redirect, license, ToS, robots, and API checks per row. |
| `The DeepSeek dataset list is deduplicated.` | 4 duplicate exact URLs found; invalidated for ingestion until resolved. | Deduplicate the 4 duplicate URL rows and rerun the static validator. |
| `Tier-C estimates are validated facts.` | 12 tier-C claims are flagged as over-promoted. | Relabel as unproven or support with stronger evidence. |
| `HUMMBL is EU AI Act compliant.` | Evidence ledger disallows blanket compliance claims. | Legal review, role-specific evidence, and authoritative determination. |
| `Digital Omnibus timeline is final law.` | Time-sensitive political-agreement claims require refresh. | Same-day official Parliament, Council, and Official Journal review. |
| `HUMMBL has partner/customer/program status.` | Partner/customer claims are consent-gated and high risk. | Acceptance evidence, naming permission, approved wording. |
| `Medical readiness is proven.` | Medical-governance claims require domain evidence; current defensible claim is about general governance primitives. | Medical-specific evidence pack, review, and authorization. |
| `ODG-C9/C10/C11 are factual.` | These are `quarantined`. | New source packet and formal promotion out of quarantine. |
| `ODG-C2/C3/C7/C8 benchmark values are current.` | These are `stale_or_time_sensitive`; benchmark values rely on PDF/paper extractions not reopened in the validation pass. | Direct system-card PDF and SWE-Bench Pro paper refresh from primary sources. |
| `ODG-C12 through ODG-C16 are externally verified.` | These are `repo_local_observed` repo-local implementation/absence claims. | File/test audit for each claim before external promotion. |
| `All 95 repos form a single canonical architecture.` | Canonicality is unclassified and includes likely archives/forks/imports/scratch. | Repo-role classification pass. |
| `Connector order equals exact creation timestamp.` | Connector order is only a creation-order proxy. | GitHub `created_at` or git-history evidence. |
| `Local/private evidence can be used publicly.` | Private/internal claims require authorization. | Privacy review, consent, and public-safe artifact packaging. |
| `Workspace-level drafts are canonical repo proposals.` | Prior validation found proposal provenance ambiguity. | Explicit admission/import into canonical repo. |
| `Stratum boundaries (S1-S5) are validated classifications.` | Boundaries are `internally_estimated` planning heuristics. | Repo-role classification pass (§9, Pass 2) to validate or revise. |

## 9. Recommended Next Extraction Passes

### Pass 1: Chronology Evidence Hardening

Goal: replace connector-order proxy with stronger chronology evidence.

Tasks:

1. Fetch GitHub `created_at`, default branch, archived/fork/private state,
   and latest push for each connector-visible repo.
2. Preserve connector order as `chronology_index` but add `created_at` and
   `repo_id` if available.
3. Flag chronology disagreements between connector order, GitHub creation
   time, and git first commit.

Output:

```text
HUMMBL_REPO_CHRONOLOGY_EVIDENCE.csv
```

### Pass 2: Repo-Role Classification

Goal: classify each repo before narrative use.

Tasks:

1. Assign `role.primary`, `canonicality.status`, and `public_claim_risk`
   for all 95 repos.
2. Mark forks/imports/archive/scratch explicitly.
3. Identify canonical successors where known.
4. Validate or revise the §3 stratum boundaries based on classification
   results.

Output:

```text
HUMMBL_REPO_ROLE_CLASSIFICATION.md
```

### Pass 3: Doctrine First-Appearance Extraction

Goal: trace concepts without overclaiming invention.

Candidate doctrines:

- receipts
- evidence gates
- claim provenance
- Base120
- KRINEIA
- MTSMU
- HUAOMP
- coordination bus
- governance primitives
- agent fleet
- registry/sync protocols
- claim validators
- public evidence packs

Output:

```text
HUMMBL_DOCTRINE_EMERGENCE_LEDGER.md
```

### Pass 4: Public-Claim Safety Sweep

Goal: keep narrative candidates from becoming unsafe copy.

Tasks:

1. Relabel or support the 12 tier-C over-promoted `hummbl-production`
   claims.
2. Preserve the 8 explicitly unproven claims as non-public assertions.
3. Keep quarantined Opus/Devin claims (`ODG-C9/C10/C11`) blocked.
4. Refresh `stale_or_time_sensitive` Opus/Devin claims (`ODG-C2/C3/C7/C8`)
   from primary sources (system-card PDF, SWE-Bench Pro paper).
5. Audit `repo_local_observed` Opus/Devin claims (`ODG-C12` through
   `ODG-C16`) with file/test checks.
6. Deduplicate the 4 duplicate DeepSeek dataset URL rows.
7. Refresh time-sensitive EU/regulatory claims from official sources before
   publication.

Output:

```text
HUMMBL_PUBLIC_NARRATIVE_CLAIM_GATE.md
```

### Pass 5: Portable Evidence Packaging

Goal: replace local-only evidence with reusable packets.

Tasks:

1. Convert local-only extraction paths into committed artifacts or refetch
   scripts.
2. Attach source, checked date, extraction method, and reviewer to each
   packet.
3. Separate private evidence from public-safe summaries.

Output:

```text
HUMMBL_PORTABLE_EVIDENCE_PACKET_INDEX.md
```

### Pass 6: Narrative Drafting After Classification

Goal: draft narratives only after the map, classification, and claim gates
exist.

Candidate outputs:

1. Internal archaeology narrative.
2. Investor/pitch narrative.
3. Public open-source narrative.
4. Refactor/roadmap narrative.
5. IP/invention chronology narrative.

Each draft must cite claim-risk records and preserve evidence labels.

## Current Bottom Line

The chronology is useful as a first refactor primitive and narrative
scaffold. It is not yet publication-grade evidence.

The safe current claim (`repo_local_observed`):

> HUMMBL has enough chronological and validator-backed material to build
> governed narrative maps, repo-role classifications, and
> doctrine-emergence ledgers. The validation pass confirms structural
> validity and resolvability for the inspected surfaces, with identified
> warnings, unproven claims, quarantined claims, stale claims, and
> data-quality defects that must be resolved before public publication.

The unsafe current claim (`unproven` — do not publish):

> HUMMBL's full public story is already validated across all repos,
> claims, datasets, and regulatory assertions.
