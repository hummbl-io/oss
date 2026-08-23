# HUMMBL OSS

Public monorepo for HUMMBL open-source packages. Consolidation in progress.

## Packages

| Package | Language | PyPI | Status |
|---------|----------|------|--------|
| `hummbl-governance` | Python | [![PyPI](https://img.shields.io/pypi/v/hummbl-governance)](https://pypi.org/project/hummbl-governance/) | Live — governance primitives for AI agent orchestration |
| `hummbl-bus` | Python | [![PyPI](https://img.shields.io/pypi/v/hummbl-bus)](https://pypi.org/project/hummbl-bus/) | Live — secure append-only TSV coordination bus |
| `hummbl-cognition` | Python | [![PyPI](https://img.shields.io/pypi/v/hummbl-cognition)](https://pypi.org/project/hummbl-cognition/) | Live — Cognitive Ledger Protocol and Open Brain server |
| `hummbl-tuples` | Python | [![PyPI](https://img.shields.io/pypi/v/hummbl-tuples)](https://pypi.org/project/hummbl-tuples/) | Live — HUMMBL Typed Tuples governance model |
| `hummbl-bif` | Python | [![PyPI](https://img.shields.io/pypi/v/hummbl-bif)](https://pypi.org/project/hummbl-bif/) | Live — Batch Ingestion Framework |
| `hummbl` | Python | [![PyPI](https://img.shields.io/pypi/v/hummbl)](https://pypi.org/project/hummbl/) | Pending first release — structured reasoning framework for AI agents |
| `hummbl-kernel` | Python | [![PyPI](https://img.shields.io/pypi/v/hummbl-kernel)](https://pypi.org/project/hummbl-kernel/) | Pending first release — orchestration kernel for workflow execution |

## Why a monorepo

HUMMBL's "small libraries over platforms" mission produced 60+ repos. The
bloat made link maintenance, cross-package refactors, and CI hygiene
unsustainable. This monorepo consolidates the public-publishable packages
into one surface with shared tooling, one CI, and one source of truth for
links — without merging the private governance/agent infrastructure that
stays in `hummbl-io/*` private repos.

## Consolidation status

Migration is staged. Package source is being moved here incrementally;
each package links to this repo as its canonical home once migrated. During
the transition, some packages may still publish from their legacy repos
but point here for documentation and issues.

See `docs/MONOREPO-DESIGN.md` for the full structure, migration plan, and
per-language publishing workflow.

## License

Dual-licensed under MIT OR Apache-2.0. See [LICENSE](LICENSE), [LICENSE-MIT](LICENSE-MIT), and [LICENSE-APACHE](LICENSE-APACHE).

## Contact

- Web: [hummbl.io](https://hummbl.io)
- Issues: [github.com/hummbl-io/oss/issues](https://github.com/hummbl-io/oss/issues)
