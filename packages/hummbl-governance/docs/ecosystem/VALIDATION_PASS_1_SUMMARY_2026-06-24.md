# Validation Pass 1 Summary — 2026-06-24

Date: 2026-06-24
Status: `repo_local_observed` — redacted summary of a local validation pass
Evidence label: `validator_backed` for validator-run findings; `source_backed` for web-verified claims

This is a public-safe redacted summary of a claim/evidence validation pass
conducted on 2026-06-24. It replaces direct references to internal handoff
documents. Private paths, hostnames, and operator-identifying details have
been removed.

## Method

- Used existing local validators where present rather than inventing a new schema.
- Treated internal/private workspace claims as locally auditable only unless
  already tied to public/official sources.
- Used official/primary web sources for time-sensitive public legal/vendor
  claims sampled from the evidence ledgers.
- Did not treat archive copies, backup directories, generated manifests, or
  pycache files as canonical claim sources.

## Surfaces validated

### hummbl-production public claims manifest

Validators run: `validate_claims.py`, `validate_claim_evidence.py`,
`validate_compliance_claims.py`, `validate_manifest.py`.

Result: `PASS_WITH_WARNINGS`.

- Total claims: 331
- Validated: 295
- Fixed: 28
- Unproven: 8
- Invalidated: 0
- Misleading: 0
- Not checked: 0
- Hard evidence gate: pass (all public claim-surface sections carry evidence references)
- Compliance stale phrases: 0 hard failures
- Compliance drift findings: 0 advisory findings
- Artifact manifest: pass (25 artifacts tracked, 18 live, 7 live-private)

Warnings / required corrections:

- 12 tier-C internal-estimate claims are marked `validated`; validator warns
  these should be `unproven` per playbook section 4. This is a status
  overclaim — internal estimates are not validated facts.
- 8 explicitly `unproven` claims must not become public-safe assertions.

Explicit unproven claims (IDs):

- `MA-013`, `MA-014`, `GE-004`, `GE-005`, `EP-011`, `BB-009`, `SO2-007`, `AD5-010`

Verdict: structurally supported, but not clean for public publication until
tier-C status overclaims are relabeled. `validator_backed`

### hummbl-governance evidence coverage matrix

Validators run: `validate_evidence_cells.py`, `build_evidence_validation_report.py`.

Result: `PASS` for resolvability.

- Matrices scanned: 12
- Total backtick references classified: 106
- Valid local references: 25
- Unresolvable references: 0

Important interpretation:

- `valid=0` in many matrix rows is not an evidence failure by itself. The
  validator only marks specific local CLI/file/config references as `valid`;
  external references and uncategorized references are not counted as
  local-valid.
- The hard blocker this validator detects is `unresolvable`; current count
  is 0.

Verdict: locally resolvable evidence matrix, no invalidated local references.
`validator_backed` for resolvability; does not prove truth of every mapped
claim.

### DeepSeek dataset source validation ledger

Result: `NOT_LIVE_VALIDATED`.

- Rows: 487
- `CANDIDATE_PASS_STATIC`: 405
- `NEEDS_LIVE_URL_CHECK_HIGH_RISK`: 24
- `INVALID_DUPLICATE`: 4
- Other gated/partial categories: 54
- Dominant issue: not live-verified individually for 397 rows.
- Dominant required gate: live HTTP/redirect check, capture license/ToS,
  prefer API/catalog metadata endpoint over homepage.

Data-quality defect: 4 duplicate exact URLs are invalidated for ingestion
until deduplicated.

Verdict: static candidate ledger only. Must not be represented as
live-validated dataset evidence. `repo_local_observed`

### Opus / Devin / medical-governance claim registry

Local registry status:

- Usable claims: `ODG-C1`, `ODG-C2`, `ODG-C3`, `ODG-C5`, `ODG-C6`,
  `ODG-C7`, `ODG-C8`, `ODG-C12`, `ODG-C13`, `ODG-C14`, `ODG-C15`, `ODG-C16`
- Internal-only claim: `ODG-C4`
- Quarantined claims: `ODG-C9`, `ODG-C10`, `ODG-C11`

Validated against public primary sources during this pass:

- `ODG-C1` supported: Anthropic states Opus 4.7 uses an updated tokenizer.
  `source_backed`
- `ODG-C5` supported as vendor-reported: Cognition states SWE-1.6 achieved
  11 percent higher score than SWE-1.5 on SWE-Bench Pro. `source_backed`
  (vendor-reported, not independently verified)
- `ODG-C6` supported as vendor framing: Cognition frames model UX and
  overthinking/self-verification as active research issues. `source_backed`

Not fully revalidated in this pass — `stale_or_time_sensitive`:

- `ODG-C2` and `ODG-C3`: benchmark values rely on cited system-card
  extraction; not found in opened Anthropic news HTML. Need system-card PDF
  refresh before external use.
- `ODG-C7` and `ODG-C8`: rely on SWE-Bench Pro paper/local extraction; not
  reopened in this pass. Need direct paper refresh.
- `ODG-C12` through `ODG-C16`: repo-local implementation/absence claims;
  require file/test audit before external promotion.

Quarantined claims — `quarantined`, do not reuse as factual assertions:

- `ODG-C9`: Devin drops from ~50 percent public performance to ~18 percent
  proprietary performance.
- `ODG-C10`: Opus 4.7 vulnerability-rate claims at 0.29/kLOC or specific
  57/MLOC, 45/MLOC, 24/MLOC rates.
- `ODG-C11`: MRCR collapse values of -32.7pp at 256k or -46.1pp at 1M.

Verdict: registry is useful and quarantines the riskiest claims, but several
benchmark values still require direct PDF/paper refresh before external use.

### EU AI Act / public-claim evidence ledger

Validated against official EU sources during this pass:

- Supported: Regulation (EU) 2024/1689 is in force, published as OJ L
  2024/1689 on 2024-07-12. `source_backed`
- Supported: Article 113 says the regulation applies from 2026-08-02, with
  Chapters I and II applying from 2025-02-02. From 2025-08-02, Chapter III
  Section 4 (high-risk AI systems obligations), Chapter V (transparency
  obligations for certain AI systems), Chapter VII (post-market monitoring),
  Chapter XII (market surveillance and governance), and Article 78
  (confidentiality) apply, except Article 101. `source_backed`
  Source: https://ai-act-service-desk.ec.europa.eu/en/ai-act/article-113
- Supported: Blanket claims like "HUMMBL is EU AI Act compliant" are not
  justified by the ledger and should remain disallowed. `validator_backed`

Potential stale/high-risk item — `stale_or_time_sensitive`:

- The matrix references a 2026-05-07 Digital Omnibus political agreement and
  derived future dates. This was not fully refreshed in this pass. Treat any
  copy depending on that political-agreement timeline as
  `stale_or_time_sensitive` until rechecked against Parliament, Council, and
  Official Journal sources on the publication date.

Verdict: conservative safe-wording rules are supported; legal timeline
claims need refresh immediately before external publication.

## Aggregate verdicts

### Supported / validated

- `hummbl-production` public claims manifest is structurally valid and
  evidence-linked. `validator_backed`
- `hummbl-governance` coverage matrix has 0 unresolvable local evidence
  references. `validator_backed`
- EU AI Act enacted-law baseline and Article 113 application dates are
  supported by EUR-Lex. `source_backed`
- Opus 4.7 tokenizer expansion claim is supported by Anthropic primary
  source. `source_backed`

### Partially supported / caveated

- `hummbl-production` public claims are structurally valid, but 12 tier-C
  internal estimates are over-promoted as `validated`.
- SWE-1.6 11 percent SWE-Bench Pro improvement claim is vendor-reported
  (Cognition), not independently verified. `source_backed` as
  vendor-reported; should not be presented as independently validated.
- Opus/Devin benchmark registry is directionally sound, but benchmark values
  from PDFs/papers need direct source refresh before external publication.
- Public-claim EU Omnibus timeline guidance is time-sensitive and requires
  same-day refresh before reuse.
- DeepSeek dataset source ledger is a static candidate list, not a
  live-verified ingestion allowlist. Contains 4 duplicate URLs.

### Invalidated / quarantined

- DeepSeek dataset ledger: 4 duplicate exact URLs; invalid for ingestion
  until deduplicated.
- `ODG-C9`, `ODG-C10`, `ODG-C11` remain quarantined.
- Any public copy claiming HUMMBL legal compliance, partner status,
  certification, production-grade status, or self-issued grades without fresh
  evidence remains invalid under the public-claim ledger.

### Blockers to claiming full validation

- "all evidence and claims" is too broad for a single pass across the 95-repo
  HUMMBL surface; this pass covers canonical local high-signal ledgers and
  validators only.
- Private/internal claims cannot be externally verified without
  privacy/authorization decisions.
- Several source packets cite local extraction paths and need portable
  committed evidence or source refresh.
- The DeepSeek dataset ledger requires live URL/license/robots/API checks
  for hundreds of rows before it can become ingestion evidence.
- The 12 tier-C status warnings should be relabeled from `validated` to
  `unproven` or supported by stronger evidence.
- The EU political-agreement timeline claims must be rechecked against
  official sources before external use.

## Recommended next corrections

1. Relabel the 12 warned tier-C `hummbl-production` claims from `validated`
   to `unproven`, unless stronger non-internal evidence exists.
2. Keep the 8 explicitly unproven claims out of public copy.
3. Keep `ODG-C9`, `ODG-C10`, and `ODG-C11` quarantined.
4. Refresh `ODG-C2`, `ODG-C3`, `ODG-C7`, `ODG-C8` from primary sources
   (system-card PDF, SWE-Bench Pro paper) before external promotion.
5. Audit `ODG-C12` through `ODG-C16` with repo-specific file/test checks
   before external promotion.
6. Promote the DeepSeek dataset ledger only after live URL, license, ToS,
   robots, and API checks are captured per row. Deduplicate the 4 duplicate
   URLs first.
7. Convert local-only evidence extractions into committed source packets or
   re-fetchable scripts before external use.
8. Run a separate repo-by-repo pass if the intended scope is truly all 95
   `hummbl-dev` repositories.

## Sources checked

- EUR-Lex, Regulation (EU) 2024/1689 Official Journal page.
- European Commission AI Act policy page.
- Anthropic, "Introducing Claude Opus 4.7".
- Cognition, "An Early Preview of SWE-1.6 and Research Update".
- Local validators and ledgers listed above.
