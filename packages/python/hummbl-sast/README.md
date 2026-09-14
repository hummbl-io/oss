# hummbl-sast

An experimental scanner with Python AST rules, secret-pattern matching, and
dependency vulnerability lookups. Python 3.11+ is required. The runtime uses
only the standard library.

Status: Alpha, available from this source tree. This import does not publish
a PyPI release.

## Install from this repository

From the monorepo root:

```bash
python -m pip install './packages/python/hummbl-sast[test]'
```

## Commands

```bash
hummbl-sast sast src/ --json
hummbl-sast secrets src/ --json
hummbl-sast deps . --json
hummbl-sast all .
```

`sast` checks Python syntax trees for selected calls and assignments, such
as `eval`, `exec`, `subprocess` with `shell=True`, and unsafe deserialization.
`secrets` checks supported text files against credential patterns and emits
redacted matches. These two modes operate locally.

`deps` and `all` send package names, version strings, and ecosystem names to
the OSV API at `https://api.osv.dev/v1/query`. They inspect supported
`pyproject.toml`, `requirements.txt`, `package.json`, and `go.mod` files.
Network errors and malformed lookup responses make the command return `2`;
they are not reported as an empty vulnerability result.

Exit codes: `0` means no HIGH findings in the completed checks, `1` means
HIGH findings, and `2` means invalid arguments, a missing target, or a
dependency lookup that could not complete. `--json` is supported for the
individual `sast`, `secrets`, and `deps` modes; `all` prints a combined text
report.

## Interpretation and limits

Rules are heuristics. Findings need review, and an empty result does not
establish that a program is secure. Static analysis does not resolve all
aliases or data flows. File size and extension filters limit coverage;
unreadable files or invalid Python syntax can be skipped by the original
local scanners. Secret patterns can miss credentials or flag harmless
fixtures. Review output handling before scanning sensitive material.

Dependency parsing is best effort: version ranges are reduced to version
fragments rather than resolved to the installed dependency graph. Unversioned
entries cannot be checked. Unsupported syntax and malformed manifests can
be skipped by the parsers. Severity mapping is a heuristic, not a complete
CVSS calculator. Use resolved inventories and the repository's existing
security checks for their respective coverage. No equivalence to CodeQL,
Dependabot, or GitHub secret scanning is claimed.

## Tests and provenance

Run `python -m pytest tests/ -q` from this package directory. Lookup tests use
mock responses and do not contact OSV. See [NOTICE](NOTICE) for the source
commit and import changes, and [LICENSE](LICENSE) for Apache-2.0 terms.
