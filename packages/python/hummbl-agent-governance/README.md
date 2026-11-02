# hummbl-agent-governance

Deterministic Runtime Safety Primitives for Multi-Agent AI Fleets.

## Overview

Provides kill switches, circuit breakers, computer-use boundaries, and audit
bus integration for agent runtimes. The `primitives` module is the core,
implementing safety controls that agent runtimes use to enforce operational
boundaries.

Stdlib-only, Apache-2.0/MIT dual-licensed.

## Installation

Not on PyPI as of 2026-11-01. From the monorepo root, install the source:

```bash
pip install -e packages/python/hummbl-agent-governance
```

## Development

```bash
cd packages/python/hummbl-agent-governance
pip install -e ".[test]"
python -m pytest tests/ -v
```
