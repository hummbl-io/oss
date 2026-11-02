# hummbl-compass

Task router for the `hummbl-*` ecosystem. Given a natural-language task, it
suggests which repository in the topology should own the work, and explains why.

The routing data is a bundled topology file describing each repo's layer,
Base120 code, bridges, and status. It is a heuristic keyword-and-code router,
not a semantic model.

- MIT OR Apache-2.0
- Python >= 3.11, no runtime dependencies

## Install

Not on PyPI as of 2026-11-01. From the monorepo root, install the source:

```bash
pip install -e packages/python/hummbl-compass
```

## Library

```python
from hummbl_compass import Compass

compass = Compass()
print(compass.version, len(compass.repos))

for result in compass.route("validate agent governance receipts", top_k=3):
    print(result.repo.name, result.confidence, result.reasons)
```

`route()` returns `RouteResult` objects with `repo`, `confidence`, and
`reasons`. Each `Repo` carries `name`, `layer`, `layer_name`, `description`,
`bridges`, `status`, `size_category`, and its primary/secondary Base120 codes.

Pass your own topology to route against a different estate:

```python
from pathlib import Path

Compass(topology_path=Path("my-topology.json"))
```

## CLI

```bash
python -m hummbl_compass.compass "where does bus replay belong"
python -m hummbl_compass.compass --by-base120 SY20
python -m hummbl_compass.compass --by-layer L5
python -m hummbl_compass.compass --bridges hummbl-governance
python -m hummbl_compass.compass --gaps
python -m hummbl_compass.compass --stats
```

`--top-k` sets result count (default 3); `--topology` points at a custom file.

## Scope

The bundled topology covers a subset of the HUMMBL estate and is versioned
separately from the package. `--gaps` reports recommended repos only when the
topology declares them. The router is advisory: it does not create, move, or
modify repositories.
