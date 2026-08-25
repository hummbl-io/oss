# Public Trust Surface Audit

Status: active operating mode
Owner: HUMMBL operator
Applies to: hummbl.io, HUMMBL public repos, package surfaces, and agent-facing public metadata

## Definition

A Public Trust Surface Audit is a bounded review of public-facing HUMMBL surfaces for claim integrity, buyer trust, reputation risk, crawlability, and public/private boundary drift.

It is not a penetration test, vulnerability scan, exploit exercise, credential search, or private-system probe. The audit inspects public pages, repo-visible files, package metadata, registry pages, rendered previews, and source-controlled public artifacts.

## Role Split

| Role           | Responsibility                                                                                                      |
| -------------- | ------------------------------------------------------------------------------------------------------------------- |
| Claude / Fable | Public-surface critique, UX/readability review, claim/disclaimer/citation consistency, trust-risk finding discovery |
| ChatGPT        | Severity classification, strategy, acceptance criteria, public-risk judgment, final done/not-done call              |
| Codex          | Repository inspection, implementation, tests/build/lint, PRs, receipts, and exact file-level evidence               |
| Operator       | Public-claim approval, legal/privacy/security judgment, merge/deploy/package-publish authority                      |

No finding is complete until the implementation receipt records what changed, what was checked, and what remains unresolved.

## Allowed Scope

- `web/**/*.html`, `web/llms.txt`, `web/llms-full.txt`, `web/robots.txt`, `web/sitemap.xml`, OpenGraph/Twitter metadata, JSON-LD, canonical links, static assets, public fallback content, and public source registries.
- Public distribution surfaces: registry pages, package READMEs, package metadata, release receipts, install examples, and package-manager routes.
- Public GitHub surfaces: README files, repo descriptions, issue/PR templates, security/contact docs, public docs, and public repo maps.
- Public buyer trust surfaces: pricing, services, readiness, security, compliance, evidence, case studies, audit pages, newsletters, and assessment flows.
- Source-side CI and validation gates that prevent public-surface regressions.

## Excluded Scope

- Exploit attempts or active attacks against HUMMBL services.
- Private repo probing, credential discovery, token searches outside authorized local checkouts, or attempts to bypass access controls.
- DNS, Cloudflare dashboard, registry publishing, package release, or legal-policy changes without explicit operator approval.
- Claims that require legal, regulatory, trademark, privacy, or customer-consent judgment unless the operator provides the decision.

## Severity Rubric

| Severity | Definition                                                                                                                             | Examples                                                                                                                                                                                         |
| -------- | -------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| P0       | Live exposure or public claim that can materially damage trust, security, legal posture, or package integrity if left up.              | Public secret or live credential, fabricated or unsupported flagship statistic, private repo material copied to a public repo, public package impersonation risk with active install confusion.  |
| P1       | Public-surface defect that materially weakens buyer trust, search/crawl posture, compliance credibility, or public/private boundaries. | Stale registry metrics, homepage-to-registry count mismatch, broken PII form endpoint, duplicate analytics beacon, public links to private repos, robots policy contradicting citation strategy. |
| P2       | Strategic or quality issue that does not create immediate exposure but should be fixed before stronger claims or broader launch.       | Third-party font dependency, weak structured data, dense footer, inconsistent navigation, unscoped comparison language.                                                                          |
| P3       | Polish or future enhancement.                                                                                                          | Spacing token drift, optional copy tightening, visual rhythm, non-blocking interaction polish.                                                                                                   |

## Codex Receipt Requirements

Every implementation pass must record:

- Original finding text or issue URL.
- Severity assigned and why.
- Files changed.
- Exact before/after wording for public copy, metadata, JSON-LD, OpenGraph, `llms.txt`, `llms-full.txt`, package metadata, `robots.txt`, sitemap, README, or public repo descriptions.
- Tests, validators, build commands, formatters, and GitHub checks run.
- Whether the change touched human-readable page content, JSON-LD, metadata, `llms.txt`, `llms-full.txt`, OpenGraph, sitemap, `robots.txt`, README, package metadata, public assets, registry docs, or other public artifacts.
- Unresolved questions and residual risk.
- Whether operator/legal/security/privacy approval is still required.

## Repeatable Checklist

Use this checklist for `hummbl.io` and related public trust surfaces:

- Homepage and primary buyer paths: headline, nav, proof strip, CTA spine, pricing, services, readiness, compliance, security, evidence, and case studies.
- Public/private boundaries: no private repo links as public contribution routes; private surfaces marked `private/not-public`; no internal paths, workers.dev origins, rate-limit specs, passwords, or copied private docs.
- Claim consistency: homepage, registry pages, README, `llms.txt`, `llms-full.txt`, JSON-LD, OpenGraph, public docs, and package metadata agree or explicitly scope differences.
- Source support: external statistics, competitor comparisons, regulatory dates, package counts, test counts, and compliance claims point to primary sources, local receipts, or a source registry.
- Warranty language: avoid absolute claims such as `guarantee`, `tamper-proof`, `never`, `cannot`, `ensures`, or `100%` unless explicitly allowlisted and source-backed.
- Vocabulary: avoid retired public framing such as `multi-agent`, `sovereignty`, and title-like internal roles unless approved for that surface.
- Package safety: no advertised component name collides with third-party registry packages without a rename or explicit disclaimer.
- Robots and agent-facing files: `robots.txt`, `llms.txt`, and `llms-full.txt` express one coherent crawl/citation posture.
- Sitemap and canonical URLs: public links should use canonical clean paths where the site serves clean paths; avoid URLs that redirect.
- Analytics and beacons: authored pages should not double-load platform-injected analytics.
- PII flows: forms use HUMMBL-controlled endpoints, consent language, privacy links, retention/erasure language, and no personal-domain collection.
- Accessibility and UX basics: focus-visible styling, skip links where template supports them, reduced-motion handling, image dimensions, alt text, and no mobile clipping.
- Structured metadata: JSON-LD, OpenGraph, Twitter cards, canonical tags, theme color, and color scheme match the rendered surface.
- Public repo surfaces: repo descriptions, README routing, maturity labels, contribution paths, and status badges match current public/private state.

## Safe Prompt Wording

Use wording such as:

> Review the public trust surface for claim consistency, public/private boundary drift, package metadata drift, citation support, crawlability, accessibility, and buyer-trust issues. Stay within public pages, public repo metadata, checked-out source, and package registry pages. Do not probe private systems, search for credentials, attempt exploitation, or bypass access controls.

For a reviewer:

> Produce findings with severity, evidence, affected URLs/files, why it matters, and a concrete acceptance gate. Mark anything you cannot directly verify as inferred.

## Risky Wording To Avoid

Avoid using these terms unless the scope is explicitly authorized and bounded:

- red-team
- attack
- exploit
- vulnerability scan
- secret leakage
- credential hunt
- origin bypass
- penetration test

Preferred replacements:

- public-trust audit
- claim-integrity review
- public/private boundary review
- package metadata parity check
- crawlability check
- public-surface drift check

## Current Remediation Status

As of 2026-07-05:

- Homepage redesign, theme-toggle removal, duplicate authored Cloudflare beacon removal, clean-URL sitemap/security policy cleanup, homepage positioning rewrite, Krineia copy, and use-case grid rewrite have landed.
- Public-surface guardrails now cover duplicate authored beacons, `.html` redirecting URLs on key source surfaces, retired vocabulary on audited surfaces, homepage positioning drift, sourced `17.2x` claims, forbidden research overclaims, public warranty wording, pending `HUMMBL Certified` naming, PII endpoint/consent markers, focus/reduced-motion markers, robots citation policy markers, and image intrinsic dimensions.
- `web/sources.json` now carries source anchors for the `17.2x` research claim family.
- Newsletter and assessment forms now use HUMMBL-controlled endpoints and consent markers; privacy copy includes retention and erasure language.
- `og-home-dark.png` has been recompressed.
- `hummbl-agent` has been made private after public-boundary exposure; public routing should not present it as a public contributor entry point.
- `hummbl-production#557` remains the parent visibility/distribution trust tracker until final registry/site metric parity is closed or explicitly deferred.
- `hummbl-production#653` tracks this reusable audit-loop documentation.

## Closure Rule

Close a Public Trust Surface Audit issue only when every child finding is either:

- fixed with linked PR, commit, and validation evidence;
- explicitly deferred with owner, reason, and residual risk; or
- converted into a new narrow issue with acceptance criteria.

Do not close based on local tests alone. GitHub checks, deployed preview/live verification, or an explicit `CI unknown` receipt must be recorded.
