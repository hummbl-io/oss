# Privacy Policy Surface Plan

**Status:** implementation and review packet for issue `#593`  
**Scope:** public disclosure surface, data-flow inventory, and linking requirements  
**Public copy changed:** contextual/discoverability links only  
**Legal policy drafting:** not completed by this packet  
**Last reviewed:** 2026-07-03

## Objective

Make the HUMMBL privacy-policy surface discoverable from the public flows that collect, route, or process user data, especially assessment and scheduling paths.

This packet separates:

- current public routes and data-touching flows,
- technical implementation requirements,
- content placement requirements,
- legal/operator review questions.

## Current route

The current checkout already contains `web/privacy.html` and `web/sitemap.xml` lists `https://hummbl.io/privacy.html`.

The live issue is therefore discoverability and policy-content alignment, not route creation from scratch.

## Relevant public data-touching flows

### Assessment page

Path: `web/assessment.html`

Observed data-touching behavior:

- `#email-input` captures an optional email address for report follow-up.
- `POST https://api.hummbl.io/assessment/capture` sends assessment/report data.
- `POST https://api.hummbl.io/assessment/checkout` starts a checkout/report flow.
- `POST https://api.hummbl.io/analytics/event` records lightweight funnel events.
- Cloudflare Web Analytics beacon is included.

Evidence paths:

- `web/assessment.html:801`
- `web/assessment.html:856`
- `web/assessment.html:1488`
- `web/assessment.html:1536`
- `web/assessment.html:1661`
- `docs/DEGRADATION_RUNBOOK.md:12`
- `docs/DEGRADATION_RUNBOOK.md:63`

### Readiness and scheduling page

Path: `web/readiness.html`

Observed data-touching behavior:

- primary calls to action route users to `https://cal.com/hummbl/30min`.
- Scheduling happens on Cal.com and is governed by Cal.com's own privacy policy once the user leaves `hummbl.io`.
- Cloudflare Web Analytics may apply to the page.

Evidence paths:

- `web/readiness.html:863`
- `web/readiness.html:870`
- `web/privacy.html:443`
- `web/privacy.html:578`

### Homepage, pricing, and about pages

Paths:

- `web/index.html`
- `web/pricing.html`
- `web/about.html`

Observed data-touching behavior:

- public CTAs route users to `https://cal.com/hummbl/30min`.
- These pages are natural discovery points for privacy-policy footer links because they contain scheduling, pricing, and contact context.

Evidence paths:

- `web/index.html:1785`
- `web/pricing.html:733`
- `web/pricing.html:758`
- `web/pricing.html:784`
- `web/pricing.html:946`
- `web/about.html:457`

### Contact form worker

Path: `workers/contact-form/`

Observed data-touching behavior:

- `GET /contact` serves a contact form.
- `POST /contact/submit` accepts name, email, message, optional company, optional project type, and Turnstile token.
- Submissions are emailed via Resend, logged to D1, and rate-limited by IP hash in KV.

Evidence paths:

- `workers/contact-form/README.md:15`
- `workers/contact-form/README.md:24`
- `workers/contact-form/README.md:35`
- `workers/contact-form/README.md:89`
- `workers/contact-form/README.md:231`

### Analytics and infrastructure services

Observed services:

- Cloudflare Pages for site hosting.
- Cloudflare Workers for API and form flows.
- Cloudflare KV for analytics, rate limiting, assessment capture, and queue-like storage.
- Cloudflare D1 for selected audit, contact, and operational records.
- Cloudflare Web Analytics for aggregate site analytics.
- Resend for email delivery.
- Cal.com for scheduling.
- Cloudflare Turnstile for contact-form anti-spam.

## Implementation requirements

### Route and metadata

- Retain public route: `https://hummbl.io/privacy.html`.
- Keep `web/privacy.html` in `web/sitemap.xml`.
- Keep canonical metadata on the privacy page.

### Footer discoverability

Minimum footer links should exist on:

- `web/index.html`
- `web/readiness.html`
- `web/assessment.html`
- `web/pricing.html`
- `web/about.html`
- `web/privacy.html`

### Contextual links

Minimum contextual links should exist near:

- assessment email/report capture,
- readiness gap-assessment scheduling CTAs,
- pricing scheduling CTAs if not already covered by a nearby footer,
- contact-form page if the worker-served form is promoted publicly from HUMMBL surfaces.

### Policy-content alignment blocker

`web/privacy.html` currently says HUMMBL does not collect email addresses or personal information through `hummbl.io`, while `web/assessment.html` contains an optional email capture and `/assessment/capture` flow.

This packet does not rewrite that policy text. It flags the mismatch for operator/legal review before any claim is made that the policy is legally sufficient.

## Minimal checklist

- [x] Confirm `web/privacy.html` exists.
- [x] Confirm `web/sitemap.xml` includes `https://hummbl.io/privacy.html`.
- [x] Add contextual link from `web/assessment.html` email/report capture to `privacy.html`.
- [x] Add contextual link from `web/readiness.html` scheduling CTA to `privacy.html`.
- [x] Add footer Privacy links on key public surfaces touched by assessment, scheduling, pricing, and contact context.
- [ ] Review and update policy language for assessment email capture, assessment storage, checkout/report flow, Resend, D1, KV, and contact-form handling.
- [ ] Decide whether `workers/contact-form` is part of the HUMMBL policy surface, the Operator personal-site policy surface, or both.
- [ ] Have operator/legal review final policy wording before treating the page as complete legal disclosure.

## Open questions

1. Should `web/privacy.html` cover only HUMMBL product/API flows, or also Operator personal-site contact flows?
2. Should the assessment email capture be retained if the policy is not yet updated?
3. What is the intended retention period for assessment captures, report emails, checkout sessions, and contact-form D1 rows?
4. Should Resend, Stripe or checkout provider details, Turnstile, and Cal.com be listed in the third-party table before the page is considered complete?
5. Should a short privacy notice be added directly above any email/contact field, or is a contextual policy link sufficient?

## Do not infer

- This packet does not provide legal advice.
- This packet does not certify the privacy policy as legally sufficient.
- This packet does not claim HUMMBL has no personal-data processing.
- This packet establishes the public surface and the implementation checklist needed for policy review.
