# governed-compression

[![License](https://img.shields.io/badge/license-Apache%202.0-blue)](LICENSE)

Public research implementation surface for governed vector and KV-cache compression.

Learn more at [hummbl.io](https://hummbl.io).

## Purpose

This repo exists to provide a better implementation surface than the current fragmented TurboQuant-adjacent landscape.

Core goals:

- CPU reference implementation first
- reproducible benchmarks
- Windows via WSL2 first
- tuple-based experiment logging from day one
- method comparison across TurboQuant-style, QJL, and simple baselines

## Initial Scope

- vector encode / decode
- approximate dot product
- distortion metrics
- simple benchmark harness
- experiment logging

This repo is not yet a full inference-runtime integration project.

## Layout

```text
governed_compression/
  core/
  bench/
  logging/
tests/
examples/
docs/
```

## Quick Start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
python -m governed_compression.cli
```

## Repository Health

See [REPO_HEALTH.md](docs/REPO_HEALTH.md) for the authoritative repository
health contract and validation checks.

## Current Status

Stage 1 scaffold only.


## HUMMBL Ecosystem

This package is part of the [HUMMBL](https://github.com/hummbl-io/oss) open-source AI governance architecture.

| Package / Surface | Purpose |
|---|---|
| [hummbl-governance](https://pypi.org/project/hummbl-governance/) | Governance runtime — kill switch, circuit breaker, cost governor, 51 implemented primitives |
| [hummbl-mcp-base120](../hummbl-mcp-base120) | MCP server for Base120 mental models — 120 reasoning operators for Claude/Cursor |
| [base120](https://pypi.org/project/base120/) | 120 mental models for structured reasoning — stdlib-only Python library |
| [hummbl-tuples](../hummbl-tuples) | Governed typed-tuples and experiment logging |
| [hummbl-bus](../hummbl-bus) | Append-only TSV coordination bus for multi-agent systems |
| [Documentation](https://hummbl.io) | Canonical public documentation |

Learn more at [hummbl.io](https://hummbl.io).

---

## Author

**HUMMBL** — [hummbl.io](https://www.hummbl.io)

- GitHub: [@hummbl-io](https://github.com/hummbl-io)
- Website: [hummbl.io](https://www.hummbl.io)
