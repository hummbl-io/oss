# ADR-003 — HUMMBL Repo Standard v0.1

- **Status:** proposed
- **Date:** 2026-06-22
- **Decision owner:** Reuben Bowlby
- **Steward:** HUMMBL Research Institute
- **Supersedes:** none
- **Superseded by:** none

## Context

A live audit of all 91 `hummbl-dev` repositories (43 public + 48 private) found that the four files intended to form the core of a per-repo governance architecture are essentially unimplemented across the fleet:

| Artifact | Repos with it | Coverage |
|----------|--------------|----------|
| `CONSTITUTION.md` | 1 | 1% |
| `DOCTRINE.md` | 0 | 0% |
| `KRINEIA.md` | 0 | 0% |
| `hummbl.repo.yaml` | 0 | 0% |

The strongest repo (`hummbl-governance` itself) scores 8/15 against the proposed baseline. The modal HUMMBL repo sits at 5/15 (README + AGENTS + CONTRIBUTING + SECURITY + LICENSE). 23 forks carry no HUMMBL fork-boundary file. There is no global standard that defines what a governed HUMMBL repo must contain, which class of repo requires which artifacts, or how repo-local law relates to the operating-environment constitution.

A prior audit cited in the originating handoff was public-only and treated `krineia` (a private repo) as missing its `AGENTS.md`. Live inspection shows `krineia` already has a strong, repo-specific, provider-neutral `AGENTS.md`. The real krineia gaps are `CONSTITUTION.md`, `DOCTRINE.md`, `KRINEIA.md`, `hummbl.repo.yaml`, `_receipts/`, `docs/adr/`, `docs/handoffs/`, `CODEOWNERS`, and `CHANGELOG.md`.

## Decision

Adopt **HUMMBL Repo Standard v0.1** as the global baseline for all `hummbl-dev` repositories, with canonical home in `hummbl-io/hummbl-governance` and templates mirrored in `hummbl-io/.github`.

The standard defines:

1. A 15-item required artifact stack (`README`, `CONSTITUTION`, `DOCTRINE`, `AGENTS`, `KRINEIA`, `CONTRIBUTING`, `SECURITY`, `LICENSE`, `CHANGELOG`, `CODEOWNERS`, `hummbl.repo.yaml`, `_receipts/`, `docs/adr/`, `docs/handoffs/`, `scripts/validate.*`).
2. Five repo classes (spec/governance, code/library, docs/research, fork, archived) with per-class required/prescribed/optional weightings.
3. A conflict-precedence ladder rooted at the operating-environment constitution, then repo `CONSTITUTION.md`, `KRINEIA.md`, `AGENTS.md`, schemas/tests, `DOCTRINE.md`, `README.md`.
4. A machine-readable manifest (`hummbl.repo.yaml`) governed by `schemas/hummbl-repo-manifest.schema.json`.
5. A provider-neutrality constraint on all root governance files.
6. A routing doctrine: deterministic spine, stochastic muscle; models propose, schemas constrain, validators decide, git records, KRINEIA proves, humans authorize.

The standard is **global** (informs every repo) but **not templated** (each repo writes its own locally specific constitution, doctrine, agents, and KRINEIA manifest). Repo constitutions may be stricter than the standard, never weaker.

## Alternatives considered

- **Per-repo ad hoc governance (status quo).** Rejected: 0% `KRINEIA.md` and 0% `hummbl.repo.yaml` coverage means there is no machine-readable governance surface across the fleet. Agents cannot deterministically verify jurisdiction.
- **Single global constitution copied into every repo.** Rejected: duplicates authority, drifts, and conflates machine-level authority with repo-level scope. The standard explicitly forbids duplicating the operating-environment constitution into repos.
- **Standard lives in `.github` only.** Rejected: `.github` is the org-defaults repo (templates, labels, profile) but lacks the validator/ADR/coverage infrastructure that `hummbl-governance` has. The standard's canonical source belongs where the governance primitives live; templates mirror to `.github`.
- **Wait for krineia reference implementation before standardizing.** Rejected: krineia already has `AGENTS.md`; the real gap is the standard itself, not a single repo's docs. Top-down first grounds the reference implementation in a real standard.

## Consequences

- **Positive:** Every repo gains a deterministic, machine-readable governance surface (`hummbl.repo.yaml`) and a clear authority/conflict ladder. Agents can verify jurisdiction without parsing prose. The fleet re-audit becomes a one-command check against the schema.
- **Positive:** Provider neutrality is enforced in the schema (`model_provider_neutral: const true`), preventing vendor lock-in at the root governance layer.
- **Negative:** 56 active non-fork repos need new files (CONSTITUTION, DOCTRINE, KRINEIA, manifest, CODEOWNERS, CHANGELOG, `_receipts/`, `docs/adr/`, `docs/handoffs/`, `scripts/validate.*`). This is a multi-PR rollout, not a single change.
- **Negative:** 23 forks need a minimal fork-boundary layer (`HUMMBL_FORK.md` + `AGENTS.md` + `KRINEIA.md` + manifest).
- **Risk:** The standard could collapse into generic boilerplate if repos copy templates without localizing. Mitigation: the standard explicitly forbids blind global copies; the audit matrix scores repos on whether files are present, not whether they are locally specific. A future revision may add a specificity check.

## Validation

- `schemas/hummbl-repo-manifest.schema.json` validates against JSON Schema Draft 2020-12.
- The companion `hummbl-io/krineia/hummbl.repo.yaml` (to be added in a follow-up PR) is the reference instantiation.
- The fleet audit matrix (`/tmp/hummbl_repo_audit_matrix.md` at draft time; to be committed as `docs/standards/AUDIT_2026-06-22.md` in a follow-up) is the baseline against which rollout progress is measured.

## Receipts

- This ADR is a receipt-triggering change per the standard's §11 amendment process.
- A KRINEIA receipt will be appended to `hummbl-io/hummbl-governance/_receipts/` once the krineia manifest PR lands and the chain is bootstrapped. (Chicken-and-egg: the standard defines the receipt requirement; the first receipt proves the standard is in force.)
