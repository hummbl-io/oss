# HUMMBL Repo Standard

**Status:** draft v0.1
**Steward:** HUMMBL Research Institute
**Approving human:** Reuben Bowlby
**Source of record:** this file in `hummbl-io/hummbl-governance` (canonical); templates mirrored in `hummbl-io/.github`.

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

## 10. Naming convention and exceptions

Default rule: HUMBL repositories must use the `hummbl-` prefix unless they are explicit exceptions.

Allowed non-prefixed exceptions are constrained to these classes:

- `authored_artifact` — authored artifacts and public concepts whose repo is itself the object
- `protocol` — protocol/reference objects and standards
- `reference_archive` — historical, imported, or archive/reference repos
- `research_object` — bounded research artifacts where the repo name is the governed object

Exception records must be declared in `hummbl.repo.yaml` under `repo.naming`:

```yaml
repo:
  naming:
    hummbl_prefix_exception: true
    exception_class: authored_artifact | protocol | reference_archive | research_object
    exception_reason: "<short rationale>"
    approved_by: "Reuben Bowlby"
    approved_at: "YYYY-MM-DD"
    owning_standard: "HUMMBL Repo Standard"
    allowed_scope: "<explicitly allowed scope>"
    forbidden_scope: "<explicitly forbidden scope>"
    rename_or_archive_trigger: "<condition that removes the exception>"
```

Current approved non-`hummbl-` repo exceptions:

| Repo | Class | Approved by | Approved on |
|------|-------|-------------|-------------|
| `whether-book` | `research_object` | Reuben Bowlby | 2026-06-25 |
| `base120` | `protocol` | Reuben Bowlby | 2026-06-24 |
| `idp-spec` | `protocol` | Reuben Bowlby | 2026-06-24 |

Agents must not create additional non-prefixed repositories without an operator-approved `repo.naming` exception block.

## 11. RepoLM / RepoBit (forward reference)

A repo may declare a tiny local language/grammar/interpreter under `.hummbl/repo-lm/`. RepoLM interprets; validators and authority admit. Authority stack:

```
Git + receipts -> CONSTITUTION.md -> KRINEIA.md -> AGENTS.md -> schemas/tests -> RepoLM
```

RepoLM/RepoBit must never be sovereign. See `docs/standards/REPOLM.md` (to be drafted).

## 12. Validation

Each repo's `scripts/validate.*` is its deterministic admission gate. The standard does not mandate a specific language; it mandates that a deterministic, reproducible validator exists and is named in `hummbl.repo.yaml.validation.command`. Required before merge for spec/governance repos and before release for all.

## 13. Amendment

Changes to this standard require: a PR to `hummbl-io/hummbl-governance`, an ADR under `docs/adr/`, a KRINEIA receipt, and human approval (Reuben Bowlby). Breaking changes bump the standard version (SemVer) and trigger a fleet re-audit.
