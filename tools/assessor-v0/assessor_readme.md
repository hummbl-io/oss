# Assessor Pack v0

**Status:** Alpha demo / competitive posture artifact  
**Maturity:** Not production-certified. Confers no compliance status.

Stdlib-only verifier for public `CONTRACT` × `DCT` × `EVIDENCE` JSONL
traces, aligned with the Governance Tuple Protocol and published
`hummbl-tuples` schemas in this monorepo.

## Contents

| Path | Role |
|------|------|
| `verify.py` | Stdlib-only structural + chain checks |
| `WHAT_THIS_PROVES.md` | Honest claim boundary |
| `assessor_readme.md` | This file |
| `fixtures/public/assessor_v0_sample.jsonl` | Sample three-tuple fixture |

## Quick start

```bash
python tools/assessor-v0/verify.py fixtures/public/assessor_v0_sample.jsonl
```

Exit code `0` means the fixture is structurally sound under Assessor v0
rules. Exit code `1` means one or more checks failed.

## Canon

- Zenodo Tuple v2.1: DOI [10.5281/zenodo.21957831](https://doi.org/10.5281/zenodo.21957831)
- Protocol note: `docs/research/2026-08-23_governance-tuple-protocol-spec.md`
- Schemas: `packages/python/hummbl-tuples/schemas/{contract,dct,evidence}.schema.json`
- Public claim ledger: `packages/python/hummbl-governance/docs/public-claims.md`

## Honesty

Public **C** means **CONTRACT** (not Atlas Constitution). This pack does
not import or require `hummbl-governance` at runtime so assessors can run
it in air-gapped or third-party CI without installing the package.

See `WHAT_THIS_PROVES.md` before citing results.
