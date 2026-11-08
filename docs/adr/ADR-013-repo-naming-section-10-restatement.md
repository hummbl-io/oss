# ADR-013 — Repo Standard §10 restated: repository naming

- **Status:** accepted
- **Date:** 2026-11-05
- **Decision owner:** Reuben Bowlby
- **Steward:** HUMMBL
- **Supersedes:** ADR-006 (hummbl-governance, repo naming exception policy, status: proposed) — in substance
- **Superseded by:** none

## Context

Section 10 of the HUMMBL Repo Standard required every repository to use the `hummbl-` prefix unless it held an approved exception in one of four classes (`authored_artifact`, `protocol`, `reference_archive`, `research_object`), declared per-repo in a nine-field `hummbl.repo.yaml` naming block.

A review of that section against the live organisation found the rule did not describe reality and could not be enforced as written: at the 2026-11-05 census, 267 of 455 repositories in `hummbl-io` were non-prefixed (230 of them active), and no repository in the org carried a complete compliant exception block. The internal review record (Red Team attacks 1143–1149; Blue Team Sortie 12, concurring and drafting the repair) recommended rejecting §10 as binding and replacing it with a narrowed, honestly-labelled rule. The decision owner adopted the restated text on 2026-11-05 and ruled custody in the same motion: this repository's copy of the standard is canonical; the `hummbl-io/hummbl-governance` copy of §10 becomes a pointer to it.

## Decision

1. §10 of the Repo Standard in this repository is replaced with the adopted restated text: a **guideline with census detection**, plus one creation-time practice rule for agents. It claims no gate.
2. The `hummbl-` prefix is required only for **new** public product/framework repositories in `hummbl-io`, from 2026-11-05. All existing repositories are **grandfathered as they stand** — no renames, no per-repo approvals.
3. The four exception classes and the per-repo nine-field exception block are abolished. Bare names are governed by **populations P1–P6**, ruled once per population and recorded in one **central naming registry**, which wins on divergence; `hummbl.repo.yaml` naming blocks are optional mirrors, never authoritative.
4. The three historical exceptions (`whether-book`, approved 2026-06-25; `base120` and `idp-spec`, approved 2026-06-24) migrate into the registry with their original approval dates; no re-approval is required.
5. Scope: `hummbl-io` only. The `hummbl-dev` personal account is out of scope. Naming grammar for new names: lowercase kebab-case, single prefix, PyPI stem-collision check at creation.
6. Custody: this copy of the standard is canonical. The `hummbl-io/hummbl-governance` copy of §10 is replaced with a pointer to this file in a companion amendment PR.

## Census annotation (grandfathering baseline)

The grandfathering baseline is the organisation census of 2026-11-05. At adoption time the census recorded **455 repositories: 188 `hummbl-` prefixed, 267 non-prefixed, 230 of the non-prefixed active, 48 archived, 0 forks**.

Re-run at landing time (2026-11-05, this amendment): Re-run at landing time (2026-11-05, this amendment): **455 repositories: 188 `hummbl-` prefixed, 267 non-prefixed, 230 of the non-prefixed active, 48 archived, 0 forks — identical to the adoption baseline; no drift.**. Per-repo population assignment for the grandfathered non-prefixed repositories is maintained in the central naming registry, seeded alongside this amendment.

## Consequences

- **Positive:** the standard now describes enforceable reality — one prospective rule, one registry, no per-repo exception machinery that nothing complied with.
- **Positive:** custody is unambiguous: one canonical copy, one pointer; the registry wins on divergence.
- **Note:** §13 of the standard names `hummbl-io/hummbl-governance` as the PR venue for amendments. This amendment is executed under the 2026-11-05 custody ruling: the canonical text lands here, and a companion PR in `hummbl-io/hummbl-governance` reduces its §10 to the pointer, so the §13 path (PR + ADR + KRINEIA receipt + human approval) is satisfied in both repositories.
- **Note:** the standard's header in both copies still reads "draft v0.1" and names the governance copy as source of record. Correcting the header is outside this amendment's scope and is left to a follow-up amendment.
- **Note:** no repository is renamed, approved, or excepted by this amendment.

## Receipts

SHA-256 chain for this amendment:

- Restated §10 source text as adopted: `a6ecbe12713e549473f40f4b4984ddd103cc406c56dc3ea5f90cb792a2212a27`
- Standard before amendment (this repo, blob `17f97f86bd29546451c812bcd9de0f0854edaf8f`): `4e9a389d3afa308fd80403e353af59cec9565ca95cc82b0cf96390a2308a11ef`
- Standard after amendment (this repo): `b51c3b097ebc90f78fd601e69c430ffd7ff33c48059c001dea5206a46ae0176b`
- Adoption record (human approval, 2026-11-05): `7c3e9f8a564393300b4cc21456ff3c0ad73c44668905f1284c6fd87abcb82249`
- Naming registry seed (2026-11-05): `f21b9db476fc9cda1760213323e8e901fe833e94682117ff2dcd3111f73f3691`
- - Landing census (2026-11-05, `search_repositories` org:hummbl-io, 455 repos): `d5a133ddea97200d6d093671b0ca6e00b8b73ee01e7f68d2e9747102bdb5dfa6`

## References

- HUMMBL Repo Standard (this repo): `packages/python/hummbl-governance/docs/standards/HUMMBL_REPO_STANDARD.md`
- Companion pointer amendment: `hummbl-io/hummbl-governance`, `docs/standards/HUMMBL_REPO_STANDARD.md` §10
- Superseded policy ADR: `hummbl-io/hummbl-governance/docs/adr/ADR-006-repo-naming-exception-policy.md`
- Internal review record: Red Team attacks 1143–1149; Blue Team Sortie 12 (defense and restatement draft)
