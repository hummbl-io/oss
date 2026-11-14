# Repository Health Contract — IN-TREE COPY (origin record)

This copy of governed-compression lives in `hummbl-io/oss` as the package's
**origin record**. It is not the source of truth.

## Identity

- **Repository**: `hummbl-io/oss` → `packages/python/governed-compression/` (in-tree copy)
- **Canonical host**: `https://github.com/hummbl-io/governed-compression` (standalone repo, ruled canonical 2026-11-14, C1)
- **Default branch**: `main`
- **Visibility**: This copy sits in the oss repo; the canonical repo is Private
- **Owner**: HUMMBL Team

## Canonical Relationship

- **Source of truth**: The standalone repo, `hummbl-io/governed-compression`.
  See `../POINTER-CANONICAL-HOME.md` in this package directory.
- An earlier version of this file named a Gitea host as source of truth and
  this copy's visibility as Public — both were unfilled template artefacts
  and are struck (corrected 2026-11-14 under ruling C1 / Red Team attack
  1711).
- **Audience**: Origin record only. Do not develop against this copy.

## Validation Contract

Validation runs in the canonical repo:

```bash
python -m pip install -e .
pytest
ruff check .
```
