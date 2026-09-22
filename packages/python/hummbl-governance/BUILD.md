# BUILD.md — Reproducible Build

**Package**: `hummbl-governance` 1.5.0
**Runtime dependencies**: none (stdlib-only)
**Build backend**: `setuptools.build_meta`
**Verified**: 2026-09-22 on Anvil — two consecutive builds produced
bit-identical wheels.

## Pinned build toolchain

| Tool | Version used in verification |
|---|---|
| Python | 3.11+ (verified on the host interpreter) |
| setuptools | 78.1.0 |
| pip | 26.1.2 |

Wheel hashes are conditioned on the build-backend version: the expected
hash below is valid for setuptools 78.1.0. A different setuptools version
may produce a different (still internally reproducible) hash — record the
backend version alongside the artifact hash when comparing.

## Exact build commands

```bash
# From the package root (`packages/python/hummbl-governance` inside the oss monorepo)
SOURCE_DATE_EPOCH=1700000000 python -m pip wheel . \
    --no-deps --no-build-isolation --wheel-dir dist/
```

`SOURCE_DATE_EPOCH` fixes archive timestamps; `--no-build-isolation`
uses the ambient backend instead of fetching one (also the only mode that
works offline — see hummbl-compliance `docs/air-gap-execution-receipt.md`).

## Expected output hash (setuptools 78.1.0)

```
hummbl_governance-1.5.0-py3-none-any.whl
sha256: c91af4dee318e341e7a5ec114687baacfd83ac6360e74381fb1e8b28e97949b6
```

## Verification

```bash
SOURCE_DATE_EPOCH=1700000000 python -m pip wheel . \
    --no-deps --no-build-isolation --wheel-dir verify/

sha256sum verify/hummbl_governance-1.5.0-py3-none-any.whl
# or: python -c "import hashlib; print(hashlib.sha256(open('verify/hummbl_governance-1.5.0-py3-none-any.whl','rb').read()).hexdigest())"
```

Match the hash against the expected value above. A mismatch means either
the toolchain differs (check `setuptools.__version__` first) or the source
tree differs — both are meaningful signals, neither is silent.

## Known limitations

- sdist reproducibility was not verified in this pass (wheel-only claim).
- The hash is per-backend-version, not universal; this doc records the
  verified toolchain.
- Reproducibility covers this repo's packaging only; it does not attest
  the interpreter or OS.

