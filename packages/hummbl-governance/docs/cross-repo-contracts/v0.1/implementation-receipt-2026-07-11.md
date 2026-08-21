# Cross-Repo Contract v0.1 Pre-Write Validation Receipt

Date: 2026-07-11
Status: **historical local isolated construction receipt; not current-head CI, merge, release, or independent verification**

> This receipt records the original pre-write 10-test run exactly as observed. The focused suite was expanded after this run and currently contains 16 tests. Do not reinterpret the historical `10 passed` output as the current suite size or as validation of a later GitHub head.

## Scope

The initial candidate file set was assembled in an isolated local Python workspace before being written to the existing draft PR branch.

Validated surfaces in that historical run:

- contract schema;
- compatibility-manifest schema;
- stdlib-only contract validator;
- valid Wave 1 fixture pair;
- unsupported payload-version fixture;
- public-to-private reference leakage fixture;
- execution-receipt-as-verification fixture;
- the then-current focused unit tests.

## Commands and observed results

```text
python -m pytest -q tests/test_cross_repo_contract.py
10 passed
```

```text
python -m hummbl_governance.cross_repo_contract \
  tests/fixtures/cross_repo_contract/valid-wave1-contract.json \
  --manifest tests/fixtures/cross_repo_contract/valid-wave1-manifest.json
exit: 0
result: VALID
```

```text
python -m hummbl_governance.cross_repo_contract \
  tests/fixtures/cross_repo_contract/valid-wave1-contract.json \
  --manifest tests/fixtures/cross_repo_contract/invalid-unsupported-payload-manifest.json
exit: 1
result: INVALID
expected findings:
- both fixture consumers do not support payload version v1.0
```

## Claim boundaries

This receipt establishes only that the original assembled candidate files behaved as described in that isolated run.

It does not establish:

- that a later GitHub head passes;
- that GitHub CI has run on the current head;
- that the full repository test suite passes on the current head;
- that the draft PR is reviewed or merge-ready;
- that remote references resolve;
- that any consumer has actually accepted the contract;
- that the standard is canonical;
- that schemas prove truth, security, scientific validity, or external corroboration.

Current-head CI results must be recorded separately with the exact tested commit SHA.
