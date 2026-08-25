# AI Vendor IP Risk Register

**Status:** initial governed register
**Owner:** Reuben Bowlby
**Steward:** HUMMBL Research Institute
**Last reviewed:** 2026-06-30

This register classifies AI vendors and agent tools for IP-sensitive HUMMBL work. It is not legal advice. It is an operational control for authorship, inventorship, trade-secret, copyright, and diligence risk.

Default rule: **unreviewed vendor = RED for Tier 2/Tier 3 work**.

## Risk levels

| Risk | Meaning | Sensitive-work policy |
|------|---------|-----------------------|
| GREEN | Terms and controls are clean enough for sensitive work, subject to HUMMBL provenance controls. | Allowed for Tier 2/Tier 3 if repo-local rules are met. |
| YELLOW | Terms are usable only with caveats, usually paid/API/business tier only. | Allowed for Tier 0/Tier 1. Tier 2/Tier 3 requires owner approval and source-term review. |
| RED | Terms, tier, or product surface is too ambiguous or permissive for sensitive work. | Not allowed for Tier 2/Tier 3. |

## Tier mapping

| Tier | Description |
|------|-------------|
| T0 | Low-IP tooling, examples, experiments, public commodity work. |
| T1 | Internal operations, non-product governance work, low-confidentiality docs. |
| T2 | Product IP, patent-sensitive, strategy-sensitive, or acquisition-diligence-sensitive work. |
| T3 | Regulated, medical, healthcare, security-sensitive, or high-liability ventures. |

## Vendor register

| Vendor | Product / tier | Risk | Output ownership | Training default | Human review / retention | Allowed tiers | Source URLs | Last reviewed | Notes |
|--------|----------------|------|------------------|------------------|--------------------------|---------------|-------------|---------------|-------|
| OpenAI | API / Business / Enterprise | YELLOW | Terms assign OpenAI right/title/interest in output to user as between parties, subject to law. | Business/API data not used to train by default per OpenAI business-data/data-usage materials. | Abuse/security retention and enterprise controls require tier-specific review. | T0,T1; T2/T3 owner approval only | https://openai.com/policies/row-terms-of-use/ ; https://openai.com/business-data/ ; https://openai.com/policies/how-your-data-is-used-to-improve-model-performance/ | 2026-06-30 | Use paid/API/business surfaces only for sensitive work; keep Git provenance human. |
| OpenAI | Consumer ChatGPT Free / Plus / Pro | RED | Output ownership language exists, but consumer training and account controls are not clean enough for sensitive IP by default. | Consumer content may be used to improve services unless controls/opt-out apply. | Consumer surface is not acceptable for confidential inventions. | T0,T1 | https://openai.com/policies/row-terms-of-use/ ; https://openai.com/policies/how-your-data-is-used-to-improve-model-performance/ | 2026-06-30 | Do not use for patent-sensitive or confidential repo context. |
| Anthropic | API / Claude for Work / commercial tier | YELLOW | Commercial terms/privacy materials indicate customer ownership/rights over outputs subject to terms. | Commercial inputs/outputs are represented as not used for training by default in Anthropic privacy materials. | Retention, support access, and indemnity need tier-specific review. | T0,T1; T2/T3 owner approval only | https://privacy.claude.com/en/articles/7996868-is-my-data-used-for-model-training ; https://www.anthropic.com/legal/commercial-terms | 2026-06-30 | Use only commercial/API surfaces for sensitive work; keep invention notes human-authored. |
| Anthropic | Consumer Claude | RED | Consumer terms are not sufficient for HUMMBL sensitive-work default. | Consumer training / preference settings require explicit user controls and are not a Tier 2/Tier 3 baseline. | Consumer surface is not acceptable for confidential inventions. | T0,T1 | https://www.anthropic.com/news/updates-to-our-consumer-terms ; https://privacy.claude.com/en/articles/7996868-is-my-data-used-for-model-training | 2026-06-30 | Do not use for patent-sensitive or confidential repo context. |
| GitHub | Copilot Business / Enterprise | YELLOW | GitHub does not claim ownership of code suggestions as between GitHub and user, but output similarity and third-party-license risk remain. | Business/Enterprise controls differ from individual tiers and require org setting review. | IDE/workspace context makes this a code-provenance risk surface. | T0,T1; T2/T3 owner approval only | https://docs.github.com/site-policy/github-terms/github-terms-of-service ; https://github.com/features/copilot | 2026-06-30 | Use with provenance lint, human commits, and no AI trailers. |
| GitHub | Copilot Free / Pro / Pro+ | RED | Output ownership is not enough to clear sensitive work. | Individual-tier telemetry/training controls and suggestion provenance are not acceptable for Tier 2/Tier 3. | IDE/workspace context can expose repo state. | T0,T1 | https://docs.github.com/site-policy/github-terms/github-terms-of-service ; https://github.com/features/copilot | 2026-06-30 | Do not use on PeptideCheck or other Tier 2/Tier 3 repos. |
| Google | Google Cloud / Vertex AI generative services | YELLOW | Google Cloud service terms state generated output is customer data and Google does not assert ownership in new IP created in generated output. | Cloud terms are stronger than unpaid consumer/dev surfaces; project settings still require review. | Retention and abuse monitoring require tier-specific configuration review. | T0,T1; T2/T3 owner approval only | https://cloud.google.com/terms/service-terms | 2026-06-30 | Prefer Cloud/enterprise surfaces over unpaid Gemini surfaces. |
| Google | Gemini API unpaid / Google AI Studio unpaid | RED | Output terms are not enough for sensitive work. | Unpaid terms warn not to submit sensitive/confidential data and may allow human review. | Not acceptable for confidential inventions. | T0,T1 | https://ai.google.dev/gemini-api/terms | 2026-06-30 | Do not use for Tier 2/Tier 3. |
| Cursor | Cursor IDE / agentic coding | RED | Not yet reviewed against HUMMBL sensitive-work criteria. | Unknown until terms and enterprise controls are captured. | Workspace-context access is inherently sensitive. | T0 only | REVIEW_REQUIRED | 2026-06-30 | Default RED until reviewed. |
| Cognition | Devin / Devin CLI / Devin app | RED | Not yet reviewed against HUMMBL sensitive-work criteria. | Unknown until terms and enterprise controls are captured. | Workspace-context access and autonomous repo operations are sensitive. | T0 only | REVIEW_REQUIRED | 2026-06-30 | Default RED until reviewed; no commit authorship. |
| Codeium | Windsurf / agentic coding | RED | Not yet reviewed against HUMMBL sensitive-work criteria. | Unknown until terms and enterprise controls are captured. | Workspace-context access is inherently sensitive. | T0 only | REVIEW_REQUIRED | 2026-06-30 | Default RED until reviewed. |

## Minimum review fields

Every vendor row must capture:

- vendor
- product / tier
- RED, YELLOW, or GREEN risk
- output ownership posture
- training default
- human review / retention posture
- allowed tiers
- source URLs or `REVIEW_REQUIRED`
- last reviewed date
- operational notes

## Standing rules

1. RED vendors are forbidden for Tier 2/Tier 3 work.
2. YELLOW vendors require owner approval for Tier 2/Tier 3 work.
3. GREEN vendors still require human commit authorship, no AI commit trailers, and repo-local provenance controls.
4. Unreviewed vendors are RED for Tier 2/Tier 3.
5. Consumer, free, or unpaid tiers are never acceptable for patent-sensitive or regulated work unless this register explicitly says otherwise.
6. Workspace-context agents are RED until their source-code access, retention, training, and output terms are reviewed.
