# SCAVENGE.md — hummbl-io/oss

This is the scavenge index for the `hummbl-io/oss` monorepo. It maps the
consolidation targets — repos whose content is being migrated here — and
documents where the valuable unmerged work lives.

## How to use this index

1. **Find the source repo** below.
2. **Check the valuable branches** — these have work not yet in `main` or `oss`.
3. **Cherry-pick or copy** the relevant files into `oss/packages/<lang>/<name>/`.
4. **Do not `git mv`** from private repos — use clean snapshots to avoid
   carrying private history (hostnames, paths, credentials) into the public
   monorepo.

## Consolidation targets

### hummbl-governance → oss/packages/python/hummbl-governance/

- **Status:** 1.4.1 already live on PyPI from this repo. Source migration to
  `oss` in progress (PR #1).
- **Actions:** Disabled. Repo is inert.
- **Valuable branches (not in main):**

| Branch | PR | What's there |
|--------|-----|-------------|
| `fix/devin/codeql-sha-pinning` | — | **Highest value.** Governance primitives clusters 16-22 + ASI-06 jailbreak detection. Most valuable unmerged work in the org. |
| `fix/devin/codeql-sha-pinning-v2` | — | V2 of the above. |
| `feat/devin/jailbreak-detection` | — | ASI-06 jailbreak detection primitives. |
| `docs/domain120-lattice-phase-neg1-discovery` | #345 | Domain120 lattice Phase -1 Discovery research program. |
| `docs/devin/compliance-vendor-reviews-2026-08-21` | #365 | Vendor AI review batch + Neon stack verification. |
| `docs/devin/idea-packs-redacted-2026-08-21` | #366 | Redacted UpCloud + Langfuse idea-packs. |
| `docs/codex/adr-010-lens-disclosure` | #294 | ADR-010 research-source metric disclosure. |
| `fix/codex/v1-readiness-drift` | — | V1 readiness drift fix. |
| `fix/devin/test-count-correction-20260817` | — | Test count correction. |
| `fix/opencode/b108-nosec-frozen-mcp` | — | nosec frozen MCP fix. |
| `fix/claude-code/remove-vendor-attribution` | — | Vendor attribution removal. |
| `docs/v1.2.0-metadata-alignment-155` | — | V1.2.0 metadata alignment. |
| `docs/devin/cloud-mission-idea-packs` | — | Cloud mission idea-packs. |

### hummbl-agent → oss/packages/typescript/hummbl-agent/

- **Status:** TypeScript agent SDK. Consolidation candidate.
- **Actions:** Disabled.
- **Valuable branches:**

| Branch | PR | What's there |
|--------|-----|-------------|
| `fix/devin/neutralize-hosted-ci-310` | #337 | CI runner neutralization + Node 22 contract reconciliation. |
| `fix/devin/router-fast-uri-vuln` | — | Router fast URI vulnerability fix. **Security-relevant.** |
| `fix/audit-chain-fail-closed` | — | Audit chain fail-closed fix. |
| `fix/ci-neutralize-runners` | — | CI runner neutralization (earlier attempt). |
| `fix/dependabot-ci-containment` | — | Dependabot CI containment. |

### hummbl-bibliography → oss/packages/typescript/hummbl-bibliography/

- **Status:** BibTeX citation corpus with 27-tier structure. Significant
  research corpus work in branches.
- **Actions:** Disabled.
- **Valuable branches (research content):**

| Branch | PR | What's there |
|--------|-----|-------------|
| `feat/base120-lang-bibliography` | #181 | T20 base120-lang design literature tier (20 entries). |
| `docs/T20-normative-computational-law` | #175 | T20 Normative Systems, Deontic Logic & Computational Law. |
| `docs/devin/ri-wave1-prior-art-evidence-matrix` | #172 | Wave 1 prior-art evidence matrix for Representation Integrity. |
| `fix/devin/tech-debt-cleanup` | #170 | 27-tier structure migration + ARCANA crosswalk population. |
| `feat/bib/wave2a-co-grounding` | — | Wave 2a co-grounding. |
| `feat/bib-agent-qualification-range-119` | — | Agent qualification range 119. |
| `feat/bib-ai-evolutionary-selection-118` | — | AI evolutionary selection 118. |
| `feat/bib-cosmological-finetuning-90` | — | Cosmological finetuning 90. |
| `feat/bib-coupled-intelligence-97` | — | Coupled intelligence 97. |
| `feat/bib-lexical-authority-benchmark-136` | — | Lexical authority benchmark 136. |
| `feat/bib-llm-wiki-registry-89` | — | LLM wiki registry 89. |
| `feat/bib-paper-only-packet-96` | — | Paper-only packet 96. |
| `feat/bib-wifi-sensing-evidence-127` | — | WiFi sensing evidence 127. |
| `feat/bib-world-labs-r2s2r-139` | — | World labs R2S2R 139. |
| `feat/gemini/bib-doi-enrichment` | — | DOI enrichment. |
| `preserve/multiscale-agency-grounding-v0.2` | — | Multiscale agency grounding v0.2. |
| `fix/security/token-env-and-permissions` | — | Token env and permissions security fix. |

### hummbl-doctrine → oss/packages/python/hummbl-doctrine/

- **Status:** Governance doctrine. Low unmerged value (dependabot + SHA-pinning).
- **Actions:** Disabled.
- **Valuable branches:** None significant. `fix/devin/pin-actions-sha` (#23)
  is SHA-pinning compliance (already applied org-wide by this session).

### hummbl-risk-contracts → oss/packages/python/hummbl-risk-contracts/

- **Status:** Risk contract definitions.
- **Actions:** Disabled.
- **Valuable branches:**

| Branch | PR | What's there |
|--------|-----|-------------|
| `docs/falsification-proxy-terminal-validation` | #17 | Terminal values and proxy validation for falsification-lane. |
| `docs/devin/discord-safety-boundary` | — | Discord safety boundary docs. |
| `fix/ci/shell-bash` | #22 | Shell: bash for self-hosted Windows runner. |

## Scavenge priority ranking

1. **hummbl-governance `fix/devin/codeql-sha-pinning`** — governance primitives
   clusters 16-22 + ASI-06 jailbreak detection. Highest value.
2. **hummbl-bibliography** research branches — 15+ feature branches with
   domain-specific research corpus entries.
3. **hummbl-agent `fix/devin/router-fast-uri-vuln`** — security fix.
4. **hummbl-risk-contracts `docs/falsification-proxy-terminal-validation`** —
   terminal values + proxy validation.
5. **hummbl-governance** research PRs (#345, #365, #366) — Domain120, vendor
   reviews, idea-packs.

## Topic search

Use `gh search repos --owner hummbl-io --topic=<topic>` to find repos:
- `consolidated` — repos being merged into oss
- `scavenge-target` — repos with valuable unmerged branches
- `active-ci` — repos with CI enabled (oss, hummbl-production, mcp-server, apex-nexus)
- `governance`, `agents`, `research`, `security`, `cli`, `web`, `mcp`,
  `personal`, `peptide`, `publishing`, `ai-safety`, `data`, `infrastructure`,
  `docs-only`
