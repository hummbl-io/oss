# Base120 corpus distribution decision

**Status:** Operator operational disposition, 2026-09-07
**Issue:** [#141](https://github.com/hummbl-io/oss/issues/141)
**Architecture chosen:** 3 — explicit public corpus
**This is not legal advice and is not counsel-reviewed.** It records
the operator's instruction to match already-public facts.

## Decision

Treat the published Base120 corpus as published. Align rights text with
the surfaces that already carry it. Do not pull the wheel. Do not keep
trade-secret language for material that is on public GitHub and PyPI.

Pulling is the expensive fiction: `base120==3.0.0` is live, and
`operators.json` is on `main`.

## What is public (inventory)

| Surface | What is there |
| --- | --- |
| Public git `main` | `packages/python/base120/base120/data/operators.json` — 120 operators, six families, each with `code`, `name`, `transformation`, `definition` |
| Same tree | `packages/python/base120/Base120_Canonical_Model_Registry.yaml` |
| PyPI | [`base120==3.0.2`](https://pypi.org/project/base120/3.0.2/) live (NOTICE-aligned); [`3.0.0`](https://pypi.org/project/base120/3.0.0/) remains published and is not yanked |
| Copies | `hummbl-cognition` `base120_registry.json` (generated from the canonical registry) |

Those files are the **published corpus**.

## What the license already is

`packages/python/base120/pyproject.toml` declares `license = "Apache-2.0"`
and `license-files = ["LICENSE", "NOTICE"]`. The bundled corpus files are
part of that Work. Apache-2.0 already permits use of the Work, including
commercial use, subject to the License.

The prior NOTICE paragraph that called the definitions, names, codes, and
transformation framework a trade secret, and that required a separate
commercial license, contradicted those facts. That paragraph is removed.

## What this does not license

- Trademarks: HUMMBL™, BASE120™, and other marks in NOTICE. Apache-2.0
  does not grant trademark rights.
- Unpublished HUMMBL material that is not in this public tree.
- A new grant beyond Apache-2.0. This disposition does not relicense; it
  stops claiming secrecy for files that are already Apache-2.0 published.

## What this does not do

- Yank or unpublish `base120==3.0.0`. The 3.0.0 wheel keeps its original
  NOTICE. The aligned NOTICE ships in `base120==3.0.2`.
- Delete `operators.json` or the YAML registry from git.
- Auto-admit PR #138. Corpus-rights contradiction is resolved in text;
  that PR stays **draft + `requires-review`** until a human reviews
  (operator 2026-09-07). No agent merge.

## Follow-up

- `base120==3.0.2` is the NOTICE-aligned wheel (tag `python/base120/v3.0.2`).
  `3.0.1` was tagged but never published.
- Rights-boundary CI: fail if NOTICE again claims trade secret for the
  published corpus files (package test covers NOTICE text).
- PR #138 remains a human review item, not an agent sweep item.

## Related

- `packages/python/base120/NOTICE`
- `packages/python/base120/LICENSE`
- Issue #141, PR #138
