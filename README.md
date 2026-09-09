# HUMMBL OSS

**Structured thinking at fleet scale. One operator, governed agents, any domain.**

HUMMBL is open-source infrastructure for governed agent fleets: a coordination
bus, governance primitives (kill switches, circuit breakers, delegation tokens,
verifiable receipts), executable mental models (Base120), and a cognition layer
that runs inside your Python environment.

That sentence is the public definition. It is the same sentence as
[hummbl.io](https://hummbl.io). Do not invent a second one in this README,
package blurbs, or agent briefs.

**HUMMBL** = **H**ighly **U**seful **M**ental **M**odel **B**ase **L**anguage.
Base120 (120 mental models across 6 transformation families) is the substrate
those governance primitives sit on. It is not a competing product story.

Public monorepo for HUMMBL open-source **Python** packages, a private Node
technical canary, and a Lean sketch under `packages/lean/`. Consolidation is
in progress. There is no `packages/rust/` tree in this repository yet.

Inventory below is the tree at HEAD. PyPI "Live" means a wheel exists on
the registry; it does not mean production-supported. Identity leftovers
(PyPI org blurb, `arbiter-dev` fate, foreign install names on other surfaces)
remain on `#79`.

## Packages

42 Python packages under `packages/python/<name>/`. Versions are
`pyproject.toml` on this branch.

| Package | Tree | PyPI | Status |
|---------|------|------|--------|
| `hummbl-governance` | 1.5.0 | [PyPI](https://pypi.org/project/hummbl-governance/) | Live 1.4.2 — tree 1.5.0 remains unreleased; see `RELEASE.md` |
| `base120` | 3.0.2 | [PyPI](https://pypi.org/project/base120/) | Live — 120 reasoning operators for structured thinking |
| `hummbl-bus` | 0.2.0 | [PyPI](https://pypi.org/project/hummbl-bus/) | Live — secure append-only TSV coordination bus |
| `hummbl-cognition` | 0.1.0 | [PyPI](https://pypi.org/project/hummbl-cognition/) | Live — Cognitive Ledger Protocol and Open Brain server |
| `hummbl-tuples` | 0.2.0 | [PyPI](https://pypi.org/project/hummbl-tuples/) | Live — HUMMBL Typed Tuples governance model |
| `hummbl-bif` | 1.0.1 | [PyPI](https://pypi.org/project/hummbl-bif/) | Live — Batch Ingestion Framework |
| `governed-compression` | 0.1.0 | [PyPI](https://pypi.org/project/governed-compression/) | Live — governed vector and KV-cache compression |
| `hummbl` | 0.1.0 | [PyPI](https://pypi.org/project/hummbl/) | On PyPI (0.1.0, 2026-08-25) — structured reasoning framework |
| `hummbl-kernel` | 0.1.0 | [PyPI](https://pypi.org/project/hummbl-kernel/) | On PyPI (0.1.0, 2026-08-25) — orchestration kernel |
| `hummbl-lattice` | 0.1.0 | — | In-tree — Domain120 operator lattices |
| `hummbl-contracts` | 0.1.0 | — | In-tree — contract schemas and stdlib JSON Schema validator |
| `hummbl-axis` | 0.1.0 | — | In-tree — Atlas contradiction ladder |
| `hummbl-intel` | 0.1.0 | — | In-tree — INT taxonomy for agent collection |
| `hummbl-lint-config` | 0.1.0 | — | In-tree — shared ruff config |
| `idp-spec` | 0.1.0 | — | In-tree — Intelligent Delegation Profile |
| `hummbl-compass` | 0.1.0 | — | In-tree — directional navigation and routing |
| `hummbl-free-models` | 0.1.0 | — | In-tree — open-weights / free-tier model registry |
| `hummbl-rubric-templates` | 0.1.0 | — | In-tree — evaluation rubric templates |
| `hummbl-taxonomy` | 0.1.0 | — | In-tree — intelligence-tier taxonomy |
| `hummbl-validation` | 0.1.0 | — | In-tree — invariant and schema validation primitives |
| `hummbl-design-tokens` | 0.1.0 | — | In-tree — fleet visual identity tokens |
| `hummbl-heraldry` | 0.1.0 | — | In-tree — procedural heraldic agent identity |
| `hummbl-garage` | 0.1.0 | — | In-tree — performance index, livery, failure aesthetics |
| `hummbl-identity` | 0.1.0 | — | In-tree — identity facade over tokens + heraldry + garage |
| `hummbl-validation-framework` | 0.1.0 | — | In-tree — external validation tests for the design system |
| `hummbl-agent-eval-harness` | 0.1.0 | — | In-tree — required and forbidden regex constraints for agent output |
| `hummbl-sast` | 0.1.0 | — | In-tree — static analysis, secret patterns, and OSV dependency lookups |
| `hummbl-evidence` | 0.1.0 | — | In-tree — evidence state and two-party approval primitives |
| `hummbl-mcp` | 0.1.0 | — | In-tree — MCP server framework: gateway, protocol, tools, and adapters |
| `hummbl-mcp-base120` | 0.1.0 | — | In-tree — MCP server exposing Base120 mental models engine |
| `hummbl-mcp-basen` | 0.1.0 | — | In-tree — MCP server exposing BaseN governance surface |
| `hummbl-mcp-bif` | 0.1.0 | — | In-tree — MCP server exposing BIF methodology tools |
| `hummbl-mcp-cognitive-ledger` | 0.1.0 | — | In-tree — MCP server shim for Cognitive Ledger Protocol |
| `hummbl-mcp-coordination-bus` | 0.1.0 | — | In-tree — MCP server shim for HUMMBL coordination bus |
| `hummbl-mcp-discord` | 0.1.0 | — | In-tree — local stdio MCP server for Discord |
| `hummbl-mcp-governance` | 0.1.0 | — | In-tree — MCP servers exposing HUMMBL governance primitives |
| `hummbl-mcp-onepassword` | 0.1.0 | — | In-tree — MCP server exposing 1Password CLI as tools |
| `hummbl-mcp-proton` | 0.1.0 | — | In-tree — local MCP server for Proton Mail, Drive, Calendar |
| `hummbl-mcp-signal` | 0.1.0 | — | In-tree — local stdio MCP server for Signal Messenger |
| `hummbl-mcp-utf` | 0.1.0 | — | In-tree — MCP server exposing HUMMBL Unified Tier Framework |
| `hummbl-mcp-omnichannel` | 0.1.0 | — | In-tree — omnichannel governance gate MCP server (stdlib http.server) |
| `hummbl-mcp-voice` | 0.1.0 | — | In-tree — MCP server for vendor-neutral voice interactions (Vapi adapter) |

Node packages:

| Package | Tree | npm | Status |
|---------|------|-----|--------|
| `@hummbl/mcp-base120` | 0.1.0-canary.0 | — | Private technical canary — read-only Base120 MCP catalog; not publishable while admission blockers remain |

Lean (not a PyPI package, not in the Python CI matrix):
`packages/lean/hummbl-formalization`.

Canonical install names owned by HUMMBL and recommended from this repo:

```text
pip install base120
pip install hummbl-governance
```

Do not document `pip install arbiter`, `agent-governance`, or
`base120-mcp` from this repo. Those names are not HUMMBL org projects
on PyPI (`#79`). Other live wheels from this tree (`hummbl-bus`,
`hummbl-cognition`, and the rest of the Live column) may be installed by
name; they are not the two names used on the public landing page.

## Why a monorepo

HUMMBL's "small libraries over platforms" mission produced a large private
fleet. Link maintenance, cross-package refactors, and CI hygiene did not
scale. This monorepo consolidates **public-publishable** packages into one
surface with shared tooling and one source of truth for links. Private
governance and agent infrastructure stays in private `hummbl-io/*` repos.

## Consolidation status

Migration is staged. Package source is moved here incrementally; each
package links to this repo as its canonical home once migrated. During
the transition, some packages may still have been published from a
legacy repo. See `docs/MONOREPO-DESIGN.md` and `docs/PACKAGES.md`.

Publish tags must be `python/<package>/v<version>` (see `RELEASE.md`).
Legacy tags of the form `<package>/v<version>` do not trigger
`.github/workflows/publish-pypi.yml`.

## Adoption tracking

Daily PyPI download stats are collected by
[`tools/scripts/pypi_download_tracker.py`](tools/scripts/pypi_download_tracker.py)
and stored on the
[`data/pypi-downloads` branch](https://github.com/hummbl-io/oss/blob/data/pypi-downloads/tools/data/pypi-downloads.csv).
A GitHub Actions workflow runs daily at 12:00 UTC, appends a snapshot, and
auto-creates an issue labeled `adoption-signal` if download patterns deviate
from the established baseline.

```bash
python tools/scripts/pypi_download_tracker.py          # collect today's stats
python tools/scripts/pypi_download_tracker.py --report  # print trend table
python tools/scripts/pypi_download_tracker.py --check   # flag anomalies
```

## Verify a release

Every Python package published from this repository is built by
[`publish-pypi.yml`](.github/workflows/publish-pypi.yml) from a
**hash-locked build environment**: the build backend, runtime dependencies,
test extra, build front-end, and SBOM generator are pinned by SHA-256 in each
package's `requirements-build.lock` and installed with `pip --require-hashes`.
The build runs with `--no-isolation`, so nothing enters the build job that is
not named and hashed in this repository. The release job then publishes via
PyPI trusted publishing (OIDC, no long-lived tokens), signs the artifacts with
Sigstore, records a GitHub build-provenance attestation, and attaches a
CycloneDX SBOM and SHA-256 checksums to the GitHub release.

To check a wheel you downloaded, verify its provenance attestation against this
repository with the GitHub CLI:

```bash
pip download --no-deps hummbl-governance==1.5.0 -d ./dl
gh attestation verify ./dl/hummbl_governance-1.5.0-py3-none-any.whl --repo hummbl-io/oss
```

A successful result means GitHub's Sigstore instance attests that this exact
file was produced by the `publish-pypi.yml` workflow in `hummbl-io/oss`. Then
compare its checksum with `checksums-sha256.txt` on the matching GitHub release
(tag `python/<package>/v<version>`), and inspect `sbom.json` there for the
runtime dependency set.

Lock maintenance: `python .github/scripts/lock_build_env.py lock <package>`
regenerates a lock after a `pyproject.toml` change; CI (`build-lock-check`)
and the publish workflow both fail closed on a missing or stale lock.

## License

Dual-licensed at the repo level: MIT OR Apache-2.0. See [LICENSE](LICENSE),
[LICENSE-MIT](LICENSE-MIT), and [LICENSE-APACHE](LICENSE-APACHE).
Individual packages ship under Apache-2.0 or `MIT OR Apache-2.0`; see each
package `pyproject.toml` and `LICENSE` file.

## Contact

- Web: [hummbl.io](https://hummbl.io)
- Issues: [github.com/hummbl-io/oss/issues](https://github.com/hummbl-io/oss/issues)
