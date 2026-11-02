# hummbl-eval

Evidence-governed evaluation contracts for compositional Human-AI systems.

## Overview

Provides Record, Relation, and GateBench primitives for structured evaluation
of AI agent outputs with provenance tracking. Stdlib-only, Apache-2.0/MIT
dual-licensed.

## Installation

Not on PyPI as of 2026-11-01. From the monorepo root, install the source:

```bash
pip install -e packages/python/hummbl-eval
```

## Development

```bash
cd packages/python/hummbl-eval
pip install -e ".[test]"
python -m pytest tests/ -v
```
