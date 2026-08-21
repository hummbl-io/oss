# RepoLM / RepoBit Authority-Boundary Standard

Status: candidate standard
Date: 2026-07-03
Scope: `hummbl-io/hummbl-governance#143`
Parent standard: `docs/standards/HUMMBL_REPO_STANDARD.md`
ADR basis: `docs/adr/ADR-003-hummbl-repo-standard.md`

RepoLM is a repo-local grammar, interpreter, or routing-hint surface under
`.hummbl/repo-lm/`. RepoBit is any compact unit emitted or consumed by that
surface. RepoLM and RepoBit may help agents interpret local vocabulary and
validation affordances, but they are never authority.

## Authority Stack

RepoLM sits at the bottom of the authority stack already forward-referenced by
the HUMMBL Repo Standard:

```text
Git + receipts -> CONSTITUTION.md -> KRINEIA.md -> AGENTS.md -> schemas/tests -> RepoLM
```

RepoLM interprets. Validators and authority admit. Human approval remains the
gate for standard amendments, root governance changes, merge/release authority,
and any expansion of RepoLM powers.

## Allowed Purpose

`.hummbl/repo-lm/` may contain repo-local artifacts for:

- local vocabulary and aliases;
- routing hints for where evidence, receipts, schemas, and tests live;
- deterministic parse rules for repo-local terms;
- validation affordance descriptions;
- examples of accepted and rejected local phrases;
- mappings from informal issue language to existing schemas or tests;
- read-only hints for agents preparing patches or reviews.

Allowed RepoBit outputs are advisory unless admitted by an existing validator,
schema, test, receipt, or human approval gate.

## Forbidden Powers

RepoLM and RepoBit must not:

- amend `CONSTITUTION.md`, `KRINEIA.md`, `AGENTS.md`, `DOCTRINE.md`,
  `hummbl.repo.yaml`, ADRs, schemas, tests, or this standard by themselves;
- bypass `scripts/validate.*`, CI, schema checks, tests, review gates, or human
  approval;
- rewrite, delete, backdate, or reinterpret receipts;
- handle raw credentials, secrets, private keys, tokens, or unredacted personal
  data;
- grant merge, release, deployment, production, spend, provider, or external
  API authority;
- declare canon, policy, doctrine, waiver, exception, or approval;
- override repo-specific `AGENTS.md` or operator instruction;
- infer consent, license permission, provider policy, data-class clearance, or
  sensitive-data approval;
- become a hidden prompt or model-provider dependency for root governance.

## Interface Contract

If a repo declares `.hummbl/repo-lm/`, it should document the contract in
`.hummbl/repo-lm/README.md` before adding executable tooling.

Minimum documented fields:

| Field | Requirement |
|---|---|
| `purpose` | What local interpretation problem the RepoLM surface solves. |
| `inputs` | File paths, issue labels, commands, or text classes it may read. |
| `outputs` | Advisory RepoBit shapes it may emit. |
| `deterministic_boundary` | Which outputs are deterministic and which are model-assisted. |
| `validation_command` | Existing validator/test command that admits or rejects outputs. |
| `receipt_hooks` | Where accepted outputs are recorded, if anywhere. |
| `failure_mode` | What happens on parse ambiguity, missing evidence, or validator failure. |
| `forbidden_scope` | Explicit restatement of powers not granted. |
| `owner_review_gate` | Human or non-author review required before expansion. |

The contract may be prose. A schema is required only if `.hummbl/repo-lm/`
introduces machine-readable files that agents or validators consume.

## Deterministic / Non-Deterministic Boundary

Deterministic RepoLM behavior may:

- parse declared aliases;
- map terms to existing files;
- check known enums;
- emit stable warnings;
- call existing validators.

Model-assisted RepoLM behavior may propose:

- candidate interpretations;
- missing-evidence questions;
- routing suggestions;
- draft RepoBits for review.

Model-assisted behavior must be marked candidate and must not write or admit
state without the normal repo validator and review path.

## Failure Modes

RepoLM must fail closed when:

- a term maps to multiple authority surfaces;
- a referenced schema, test, receipt, or file is missing;
- a parser output would weaken a higher authority;
- a model-generated interpretation is not reproducible;
- a RepoBit references secrets, raw credentials, private data, or unsupported
  public claims;
- validation cannot run;
- authority or reviewer identity is missing.

Failing closed means the output remains advisory and cannot be used as a merge,
release, routing, production, or canon gate.

## Human Approval Gate

Separate human approval is required before any future change that would make
RepoLM or RepoBit:

- executable in CI;
- required for merge or release;
- able to mutate repo files;
- able to create or update receipts;
- able to influence provider/model routing;
- able to admit schemas, tests, policy, canon, doctrine, or public claims;
- able to process secrets, personal data, client data, or regulated data.

## ADR Position

This candidate standard does not introduce new authority semantics beyond the
forward reference in `HUMMBL_REPO_STANDARD.md` and ADR-003. It documents the
boundary that ADR-003 already implies: deterministic spine, stochastic muscle;
models propose, schemas constrain, validators decide, git records, KRINEIA
proves, humans authorize.

No new ADR is required for this candidate boundary document. A new ADR is
required before RepoLM/RepoBit gains machine-readable mandatory status,
validator authority, CI authority, receipt authority, or any other power beyond
local interpretation.

## Next Gate

Review this candidate standard for #143. Do not implement a repo interpreter,
schema, validator hook, CI gate, or `.hummbl/repo-lm/` file from this issue
without a separate human-approved PR.
