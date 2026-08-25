# governed-compression

[![License](https://img.shields.io/badge/license-Apache%202.0-blue)](LICENSE)
[![Last commit](https://img.shields.io/github/last-commit/hummbl-io/governed-compression/main)](https://github.com/hummbl-io/governed-compression/commits/main)

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

This repo is part of the [HUMMBL](https://github.com/hummbl-io) AI governance architecture.

| Repo | Purpose |
|------|---------|
| [hummbl-governance](https://github.com/hummbl-io/hummbl-governance) | Governance runtime — kill switch, circuit breaker, cost governor, 34 primitives |
| [mcp-server](https://github.com/hummbl-io/mcp-server) | MCP server for Base120 mental models — 120 reasoning operators for Claude/Cursor |
| [base120](https://github.com/hummbl-io/base120) | 120 mental models for structured reasoning — stdlib-only Python library |
| [crab](https://github.com/hummbl-io/crab) | CRAB protocol — Check, Reason, Act, Bus for multi-agent turn execution |
| [docs](https://github.com/hummbl-io/docs) | Canonical public documentation — Mintlify-powered |
| [hummbl-toolkit](https://github.com/hummbl-io/hummbl-toolkit) | HUMMBL utility toolkit |

Learn more at [hummbl.io](https://www.hummbl.io).

---

## Author

**HUMMBL, LLC** — [hummbl.io](https://www.hummbl.io)

- GitHub: [@hummbl-io](https://github.com/hummbl-io)
- Website: [hummbl.io](https://www.hummbl.io)
