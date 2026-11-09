# HUMMBL Repo Standard

**Status:** draft v0.1
**Steward:** HUMMBL
**Approving human:** Human Principal Agent
**Source of record:** this file in `hummbl-io/oss` at `packages/python/hummbl-governance/docs/standards/HUMMBL_REPO_STANDARD.md` (canonical); templates mirrored in `hummbl-io/.github`. The copy in the archived `hummbl-io/hummbl-governance` repo is historical and read-only.

## 1. Purpose

Define the minimum, prescribed, and optional governance artifacts for every repository under `hummbl-io`. Each repo is a governed micro-jurisdiction: it declares its identity, authority, doctrine, agent operating contract, receipt requirements, schemas, validators, and source-of-record boundaries.

This standard is **global**: it informs every repo but does not replace repo-local law. Repo constitutions may be stricter than this standard, never weaker.

## 2. Routing doctrine

Models propose. Schemas constrain. Validators decide. Git records. KRINEIA proves. Humans authorize.

- Non-deterministic systems may discover what could be true.
- Deterministic systems decide what becomes durable.
- Humans / constitutions decide authority.
- Git records state.
- KRINEIA proves admission.

Deterministic spine, stochastic muscle.

## 3. Decision authority

| Class | Decides | May admit durable state? |
|-------|---------|--------------------------|
| Deterministic agent | validity (schema, test, hash, naming, presence, lint, gate) | yes, when rule is explicit, input machine-readable, outcome reproducible, jurisdiction held, consequence bounded, output validatable, receipt logged |
| Non-deterministic agent | plausibility (interpret, rank, classify, draft, critique, synthesize) | only provisionally — requires delegated authority, deterministic gate validation, bounded scope, reversibility/low-risk, no self-rule-change, receipt |
| Human | authority | yes |

Canonical rule: deterministic agents decide validity; non-deterministic agents decide plausibility; humans decide authority.

## 4. Required artifact stack

Every active non-fork repo carries this stack. Each file has one job; do not conflate them.

| File | Job | Governs |
|------|-----|---------|
| `README.md` | identity | what this repo is |
| `CONSTITUTION.md` | authority | binding repo law, scope, protected invariants, amendment, receipt-triggering changes, human approval |
| `DOCTRINE.md` | meaning | interpretive framework, thesis, vocabulary, design principles, boundaries, open questions |
| `AGENTS.md` | execution | agent operating contract: read order, allowed/risky/forbidden work, validation, receipts, provider-neutral |
| `KRINEIA.md` | receipts | repo-local receipt/governance manifest: chains, events, trust-root, verification (not the receipt schema itself) |
| `CONTRIBUTING.md` | contribution | how to propose changes |
| `SECURITY.md` | disclosure | vulnerability reporting |
| `LICENSE` | rights | license terms |
| `CHANGELOG.md` | history | released changes |
| `CODEOWNERS` | ownership | review authority per path |
| `hummbl.repo.yaml` | manifest | machine-readable registry atom |
| `_receipts/` | proof | KRINEIA receipt chains |
| `docs/adr/` | decisions | architecture decision records |
| `docs/handoffs/` | continuity | agent/session handoff notes |
| `scripts/validate.*` | gate | deterministic admission validator |

### Conflict precedence (within a repo)

1. Higher-authority operating constitution, if operating locally on that host
2. `CONSTITUTION.md`
3. `KRINEIA.md`
4. `AGENTS.md`
5. Schemas / tests / validators
6. `DOCTRINE.md`
7. `README.md`
8. Other docs

The global operating-environment constitution (e.g. `C:\_governance\OPERATING_ENVIRONMENT_CONSTITUTION.md`) governs the machine and is **not** duplicated into repos. Repo constitutions include a higher-authority reference section only.

## 5. Repo classes and weight

Not every repo carries the same weight. Class determines which artifacts are **required (R)**, **prescribed (P)**, or **optional (O)**.

### 5.1 Spec / governance repos
`krineia`, `base120`, `idp-spec`, `hummbl-governance`, `hummbl-doctrine`, `hummbl-theory`, `baseN`, `mtsmu`, `huaomp`

| Artifact | Weight |
|----------|--------|
| README, CONSTITUTION, DOCTRINE, AGENTS, KRINEIA, CONTRIBUTING, SECURITY, LICENSE, CHANGELOG, CODEOWNERS, hummbl.repo.yaml | R |
| `_receipts/`, `docs/adr/`, `docs/spec/`, `schemas/`, `scripts/validate.*` | R |
| `docs/handoffs/` | P |

### 5.2 Code / library repos
`mcp-server`, `hummbl-agent`, `arbiter`, `hummbl-governance`, `hummbl-models`, etc.

| Artifact | Weight |
|----------|--------|
| README, CONSTITUTION, AGENTS, KRINEIA, CONTRIBUTING, SECURITY, LICENSE, CHANGELOG, CODEOWNERS, hummbl.repo.yaml | R |
| `tests/`, `scripts/validate.*`, `_receipts/`, `docs/adr/` | R |
| DOCTRINE, `docs/runbooks/`, `docs/handoffs/` | P |

### 5.3 Docs / research repos
`hummbl-bibliography`, `hummbl-papers`, `hummbl-theory`, `whether-book`

| Artifact | Weight |
|----------|--------|
| README, CONSTITUTION, AGENTS, KRINEIA, LICENSE, CHANGELOG, hummbl.repo.yaml | R |
| DOCTRINE, CONTRIBUTING, SECURITY | P |
| `docs/source-policy.md`, `docs/citation-policy.md`, `_receipts/` | R |

### 5.4 Forks / imported upstream repos
`vllm`, `paramiko`, `rich`, `markitdown`, `cli`, `deer-flow`, `awesome-*`, etc.

| Artifact | Weight |
|----------|--------|
| `HUMMBL_FORK.md`, `AGENTS.md`, `KRINEIA.md`, `hummbl.repo.yaml` | R |
| Everything else | O (preserve upstream) |

Fork boundary (canonical text for `HUMMBL_FORK.md`): _This repo is an upstream fork/import. Preserve upstream semantics unless explicitly creating a HUMMBL patch. Do not confuse upstream authority with HUMMBL authority. HUMMBL governance applies only to HUMMBL-authored additions._

### 5.5 Archived repos
Carry whatever they had at archival. No new required work. A `HUMMBL_FORK.md` or minimal `AGENTS.md` is prescribed only if the repo is still referenced as evidence.

## 6. `hummbl.repo.yaml` — manifest

Every active repo carries one. It is the machine-readable registry atom. Schema: see `schemas/hummbl-repo-manifest.schema.json` (companion to this standard). It declares: identity, purpose, authority, governance profile, validation command, and doc paths. It is **not** a receipt and **not** a constitution.

## 7. `KRINEIA.md` — repo-local manifest (not the schema)

`KRINEIA.md` declares how a repo participates in KRINEIA governance: chains, governed events, trust-root mode, allowed/forbidden operators, verification, and what changes require receipts. It does **not** redefine the canonical receipt schema (that lives in `hummbl-io/krineia/RECEIPT_SCHEMA.md`). Repo-specific data belongs inside receipt `state`, never as new top-level envelope fields.

Allowed first-class chain operators: `append`, `project`, `cut`. Forbidden: `update`, `delete`, `rewrite`, `summarize_and_replace`, `score_and_train`.

A chain can pass hash validation and still fail KRINEIA if the surrounding system violates the five invariants.

## 8. Provider neutrality

Root governance (`CONSTITUTION.md`, `AGENTS.md`, `KRINEIA.md`, `DOCTRINE.md`, `hummbl.repo.yaml`) must be model/provider/vendor neutral. No root governance file may depend on or name a specific provider (Claude, Codex, Devin, Gemini, Cursor, OpenAI, Anthropic, Cognition, Copilot, etc.) as a precondition of authority. Provider-specific guidance lives in adapter docs under `docs/` or `.hummbl/`, never in root governance.

## 9. Human authorship and AI assistance provenance

AI systems may assist with research, drafting, review, patch preparation, and operational coordination. They must not be credited as commit authors or co-authors in HUMMBL repositories.

Git history is the human-authored project record. Agent activity belongs in internal bus, ledger, handoff, or receipt systems; it must not create durable ownership fingerprints in commit metadata.

Required rule for every active repo:

- Commit `author` and `committer` identities must be human/operator identities or approved human-controlled service identities.
- Commit messages must not include AI-related authorship trailers such as `Co-authored-by`, `Generated-by`, `Authored-with`, or equivalent vendor/agent attribution.
- Commit messages must not credit model providers, agent products, or agent instances as authors, co-authors, implementers, or generators.
- Agents may be referenced in internal operational receipts, PR bodies, handoffs, or review notes when useful for traceability, but not in Git authorship metadata.
- Product-IP, patent-sensitive, or regulated repositories must maintain human-authored conception/decision notes before external publication, pilots, releases, or patent-relevant disclosure.

Rationale: current U.S. patent and copyright posture centers natural-person inventorship and human authorship. Vendor terms may address output ownership as between vendor and customer, but they do not remove inventorship, authorship, trade-secret, third-party infringement, or diligence ambiguity. HUMMBL therefore separates operational AI assistance from legal/engineering provenance.

Prescribed enforcement:

- `AGENTS.md` must include the repo-local form of this rule.
- `commit-msg` hooks and CI provenance checks should reject AI authorship trailers and obvious provider/agent attribution in commit messages.
- Tier 2/Tier 3 IP-sensitive repos should use signed human commits, protected branches, human CODEOWNER approval, and private invention/disclosure notes.
- AI vendors and agent tools must be classified in `docs/standards/AI_VENDOR_IP_RISK_REGISTER.md` before use on Tier 2/Tier 3 work. Unreviewed vendors default to RED for sensitive work.

## 10. Repository naming

*Restated and adopted 2026-11-05; amendment recorded in `docs/adr/ADR-013-repo-naming-section-10-restatement.md`. The former text of this section (universal `hummbl-` default with per-repo exception classes) is superseded.*

**Force (labelled honestly).** This section is a **guideline with census detection**, plus one practice rule for agents at creation time (§10.4). It is not a gate: no validator exists, and none is claimed. Detection is by periodic census against the central registry (§10.3); a census finding is a report to the operator, not an automatic violation process.

**Beneficiary (named).** The `hummbl-` prefix exists for two readers: (1) a stranger meeting HUMMBL's public product/framework family on GitHub or PyPI, for whom the shared prefix makes the family recognisable as one body of work; (2) the fleet's own retrieval across a several-hundred-repo org. Where neither reader is served — internal codenames, infrastructure, platform names — the prefix is not required and may be affirmatively wrong (a coined name carries its own identity; see §10.2, population P3).

**Scope.** This section governs repositories in the **`hummbl-io`** organisation. The `hummbl-dev` personal account is **out of scope**; its repositories are named at the account owner's discretion (the registry notes cross-account rows where they exist, e.g. idp-spec, for findability only). GitHub platform names (`.github`, `.repo-template`, and the bare name `hummbl`) are **out of scope by construction**: they cannot take a prefix and need no exception.

### 10.1 The prospective family rule

A **new** repository created in `hummbl-io` after the ruling date of this section takes the `hummbl-` prefix **if** it is a public product or framework repository — a repo whose primary reader is the stranger in the beneficiary clause. All other new repositories are named under §10.2's populations. Repositories existing at the ruling date are **grandfathered as they stand**: the census at the ruling date is annotated once, centrally (§10.3); no renames and no per-repo approvals are required or implied by this section.

### 10.2 Populations (in place of exception classes)

Bare (non-prefixed) names are governed by **population**, decided once per population by operator ruling and recorded in the registry — never per-repo. A repo belongs to a population by its observable kind, not by a semantic class judgement:

- **P1 — Prefixed family.** Public product/framework repos under §10.1. (The existing 188 prefixed repos are this family's current membership.)
- **P2 — Flagships and canon.** Named bare repositories that are the estate's public roots: e.g. `oss`, `agents`, `docs`. Membership is by named list in the registry.
- **P3 — Coined names.** Venture and product names coined as names (e.g. `krineia`, `tagmeia`, `base120`, `gyre`, and the -eia family): bare by design, because the coined name *is* the identity the prefix would obscure.
- **P4 — Infrastructure and operations.** Fleet infrastructure, runners, and operations repos: bare or prefixed as they stand; new ones default bare unless they are public product-facing, in which case §10.1 applies.
- **P5 — Platform and reserved.** `.github`, `.repo-template`, bare `hummbl`: out by construction (§10, Scope).
- **P6 — Archives, imports, and forks.** Repositories preserving an upstream or historical name keep it (`reference_archive`'s honest residue); archived repos are never renamed for naming compliance.

A new bare name that fits no population requires **one registry row added by operator ruling** — a ruling may cover a named set of repos at once. This replaces the former per-repo 9-field exception block in full.

### 10.3 The central registry

The naming record is **one central registry table** maintained with this standard (and annotated alongside the Repo Consolidation census): one row per bare-named repo or named population — name, population, ruling date, one-line reason. **The registry wins on divergence.** A `hummbl.repo.yaml` naming block in an individual repo is an optional mirror for local convenience; it is never authoritative, and its absence is not a defect. The three exceptions approved under the former text (`whether-book`, `base120`, `idp-spec`) migrate into the registry as rows, carrying their original approval dates; no re-approval is required.

### 10.4 Creation-time practice rule for agents

An agent creating a repository in `hummbl-io` checks the registry first: public product/framework → prefixed (§10.1); a population fit → named per §10.2; no fit → the agent asks the operator, whose ruling adds the registry row in the same motion. Agents do not create bare names outside the populations on their own judgement. (This is the former closing line, restated at its true scope: creation, prospectively.)

### 10.5 Grammar (the part after the decision to prefix)

- Names are **lowercase kebab-case** (`a-z`, `0-9`, hyphens). Existing case anomalies are grandfathered; new names conform.
- The post-prefix stem is the product stem, stated once: `hummbl-<stem>`. No double prefixes (`hummbl-hummbl-…` is a defect on sight).
- Before creation, the stem is checked against **PyPI distribution names** and the registry for collision — a repo stem and a package stem that differ silently are a known confusion source in this org.
- Bare coined names (P3) follow the same case and collision rules; coinage itself follows the house practice (a name coined on a true root, ruled by the operator).

### 10.6 Brand fence

The prefix marks the public product/framework family only. It is not a stamp for internal codenames, experiments, or personal-account work, and this section takes no position on the operator's open brand-direction question: **if the brand direction is re-ruled, §10.1's family scope is revisited in the same motion** — the convention follows the brand ruling, never precedes it.

### 10.7 What this section no longer claims

No universal default over existing repos; no per-repo exception machinery; no gate. The former text's first sentence is corrected in passing: the brand is spelled **HUMMBL**.

## 11. RepoLM / RepoBit (forward reference)

A repo may declare a tiny local language/grammar/interpreter under `.hummbl/repo-lm/`. RepoLM interprets; validators and authority admit. Authority stack:

```
Git + receipts -> CONSTITUTION.md -> KRINEIA.md -> AGENTS.md -> schemas/tests -> RepoLM
```

RepoLM/RepoBit must never be the final authority. See `docs/standards/REPOLM.md` (to be drafted).

## 12. Validation

Each repo's `scripts/validate.*` is its deterministic admission gate. The standard does not mandate a specific language; it mandates that a deterministic, reproducible validator exists and is named in `hummbl.repo.yaml.validation.command`. Required before merge for spec/governance repos and before release for all.

## 13. Amendment

Changes to this standard require: a PR to `hummbl-io/oss` against `packages/python/hummbl-governance/docs/standards/HUMMBL_REPO_STANDARD.md`, an ADR under `docs/adr/`, a KRINEIA receipt, and human approval (Human Principal Agent). Breaking changes bump the standard version (SemVer) and trigger a fleet re-audit.
