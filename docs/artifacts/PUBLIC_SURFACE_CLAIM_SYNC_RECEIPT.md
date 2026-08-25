# Public Surface Claim Sync Receipt

**Status:** advisory receipt shape for issue `#571`  
**Scope:** static fallback pages, AI-crawler-visible pages, and enterprise diligence surfaces  
**Public copy changed:** no  
**Last reviewed:** 2026-07-03

## Objective

Define a `public_surface_claim_sync_receipt` so durable public/static surfaces can be checked against source evidence before they drift.

This receipt is not a public claim by itself. It is a pre-publication and review artifact that records whether a claim is allowed for public use, blocked, or allowed only with qualifiers.

## Receipt Shape

Use one receipt per public claim or tightly coupled claim family.

```json
{
  "receipt_type": "public_surface_claim_sync_receipt",
  "schema_version": "0.1.0",
  "surface_path_or_url": "web/llms.txt",
  "claim_text": "Exact public text or proposed public text.",
  "claim_category": "product-status | compliance | security | performance | package-state | public-boundary | governance | other",
  "evidence_source": "web/manifest/claims-provenance.json#<id> or source path/URL",
  "evidence_date": "YYYY-MM-DD",
  "source_of_truth_path": "canonical repo path or public URL",
  "last_reviewed_at": "YYYY-MM-DD",
  "reviewer": "agent or human reviewer",
  "allowed_public_use": "yes | no | qualified",
  "required_qualifier": "Required qualifier text, or empty string.",
  "blocked_phrases_scan": {
    "status": "pass | fail | not_run",
    "matches": []
  },
  "residual_risk": "none | low | medium | high",
  "do_not_infer": ["Explicit non-claims and boundaries."]
}
```

## Field Rules

- `surface_path_or_url`: must identify the static page, manifest, AI-crawler file, diligence page, or artifact being reviewed.
- `claim_text`: must quote or closely preserve the public/proposed wording.
- `claim_category`: should be narrow enough to route review. Compliance, security, certification, clinical, federal, and performance claims need stricter evidence than general product-status claims.
- `evidence_source`: must be a current source path or public URL. For claims already in the public claims manifest, reference `web/manifest/claims-provenance.json` and the relevant claim ID.
- `evidence_date`: must state when the evidence was observed, not when the claim was written.
- `source_of_truth_path`: should point to the repo, manifest, package registry, or public authority that controls the value.
- `allowed_public_use`: use `qualified` when the claim is true only with scope limits, dates, caveats, or source-bound wording.
- `required_qualifier`: required when `allowed_public_use` is `qualified`; empty only when `yes` or `no`.
- `blocked_phrases_scan`: must scan at minimum the blocked phrase families in `web/manifest/public-boundaries.json`.
- `residual_risk`: should reflect remaining drift risk after evidence review.
- `do_not_infer`: must block likely over-readings by buyers, crawlers, and agents.

## Blocked Claim Families

The receipt explicitly blocks unsupported public use of:

- certification, authorization, approval, or accreditation claims without named external authority evidence,
- security/compliance claims that imply guaranteed protection or legal sufficiency,
- performance or test-count claims without date, scope, and source,
- package-publication claims without registry evidence,
- customer, partner, deployment, case-study, clinical, federal, or government-use claims without public source evidence,
- internal fleet or private validation evidence presented as externally verifiable public proof.

The current blocked phrase source is `web/manifest/public-boundaries.json`. Any future validator should load that file rather than hard-coding the list in a second place.

## Pilot Surface

Selected surface: `web/llms.txt`

Why this surface:

- it is AI-crawler-visible,
- it summarizes HUMMBL capabilities in durable compact text,
- downstream agents can quote it without reading the full site,
- it already includes package-state, public-boundary, test-count, and source-install claims.

## Pilot Receipts

### Receipt 1: `hummbl-governance` package state

```json
{
  "receipt_type": "public_surface_claim_sync_receipt",
  "schema_version": "0.1.0",
  "surface_path_or_url": "web/llms.txt",
  "claim_text": "hummbl-governance (PyPI): PyPI v1.2.0; 26 core primitives and a historical 1032-test claim are scoped to the PyPI project description; current local source checkout collected 1937 tests on 2026-07-02; stdlib-only",
  "claim_category": "package-state",
  "evidence_source": "web/manifest/claims-provenance.json plus local/public package review captured in current public-surface remediation branch",
  "evidence_date": "2026-07-02",
  "source_of_truth_path": "https://pypi.org/project/hummbl-governance/ and hummbl-io/hummbl-governance source checkout",
  "last_reviewed_at": "2026-07-03",
  "reviewer": "codex",
  "allowed_public_use": "qualified",
  "required_qualifier": "Distinguish historical PyPI description counts from current local source checkout counts; include review date for source checkout counts.",
  "blocked_phrases_scan": {
    "status": "pass",
    "matches": []
  },
  "residual_risk": "medium",
  "do_not_infer": [
    "Do not infer that the PyPI release itself contains 1937 tests.",
    "Do not infer that private/internal aggregate validation counts are externally reproducible.",
    "Do not infer current package metadata without rechecking PyPI and the current source checkout."
  ]
}
```

### Receipt 2: Base120 package publication state

```json
{
  "receipt_type": "public_surface_claim_sync_receipt",
  "schema_version": "0.1.0",
  "surface_path_or_url": "web/llms.txt",
  "claim_text": "Base120 (source-install only): 120 reasoning operators; not published as base120 or hummbl-base120 on PyPI as of 2026-07-01",
  "claim_category": "package-state",
  "evidence_source": "web/manifest/public-release-state.json and public package-state review",
  "evidence_date": "2026-07-01",
  "source_of_truth_path": "https://github.com/hummbl-io/base120 and PyPI package lookup",
  "last_reviewed_at": "2026-07-03",
  "reviewer": "codex",
  "allowed_public_use": "qualified",
  "required_qualifier": "Keep source-install-only wording until package registry state is reverified and a release-state manifest is updated.",
  "blocked_phrases_scan": {
    "status": "pass",
    "matches": []
  },
  "residual_risk": "low",
  "do_not_infer": [
    "Do not publish a pip install command for base120 or hummbl-base120 until the package exists on PyPI.",
    "Do not infer package availability from source repository availability."
  ]
}
```

### Receipt 3: public/private boundary

```json
{
  "receipt_type": "public_surface_claim_sync_receipt",
  "schema_version": "0.1.0",
  "surface_path_or_url": "web/llms.txt",
  "claim_text": "HUMMBL does not publish self-issued compliance grades; public claims are limited to proof artifacts (mapping docs, test counts, framework coverage) and earned third-party validation.",
  "claim_category": "public-boundary",
  "evidence_source": "web/manifest/public-boundaries.json",
  "evidence_date": "2026-06-19",
  "source_of_truth_path": "web/manifest/public-boundaries.json",
  "last_reviewed_at": "2026-07-03",
  "reviewer": "codex",
  "allowed_public_use": "yes",
  "required_qualifier": "",
  "blocked_phrases_scan": {
    "status": "pass",
    "matches": []
  },
  "residual_risk": "low",
  "do_not_infer": [
    "Do not infer certification, legal compliance, government approval, or third-party audit completion from mapping documents.",
    "Do not infer that internal validation counts are public third-party evidence."
  ]
}
```

## Implementation Notes

A future validator can start with a small JSONL file, for example:

- `web/manifest/public-surface-claim-sync.jsonl`

Each line would be one receipt. A minimal validator should:

- parse UTF-8 JSONL,
- require all receipt fields above,
- scan `claim_text` and `required_qualifier` against `web/manifest/public-boundaries.json` blocked phrases,
- fail any `allowed_public_use: yes` receipt with blocked phrase matches,
- require `required_qualifier` when `allowed_public_use` is `qualified`,
- warn when `evidence_date` is older than the configured freshness window for package, test-count, compliance, security, or performance claims.

## Acceptance Mapping

- Receipt shape documented before copy changes: complete.
- One pilot surface selected: `web/llms.txt`.
- Internal evidence is distinguished from public claim language: complete through `evidence_source`, `source_of_truth_path`, `required_qualifier`, and `do_not_infer`.
- Unsupported certification, security, compliance, and performance claims are explicitly blocked: complete.
- Public copy changed by this issue: none.

## Do Not Infer

- This receipt shape does not approve new public claims.
- This receipt shape does not certify that `web/llms.txt` is currently perfect.
- This receipt shape does not replace `web/manifest/claims-provenance.json`; it is a review layer for public/static surfaces that may cite or summarize claims from that manifest.
- This receipt shape does not make private/internal evidence public.
