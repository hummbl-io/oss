# hummbl-gitops

Bidirectional multi-agent peer-review GitOps loop.

## Overview

Closes the loop between local GitOps and remote GitOps:

- **Forward** (local to remote): local CI contract runner, agent pre-review, pre-PR gate
- **Remote** (CI + PR review): review coverage matrix, meta-review, adaptive CI contract
- **Return** (remote to local): CI watcher, main-moved detector, receipt sync, auto-rebase

Stdlib-only (optional `hummbl-governance` extra for K11 receipt verification).
Apache-2.0/MIT dual-licensed.

## Installation

Not on PyPI as of 2026-11-01. From the monorepo root, install the source:

```bash
pip install -e packages/python/hummbl-gitops
# with governance receipt verification:
pip install -e "packages/python/hummbl-gitops[governance]"
```

## Development

```bash
cd packages/python/hummbl-gitops
pip install -e ".[test]"
python -m pytest tests/ -v
```
