# Consuming Base120 v1.0.0

**Status**: Canonical, Frozen, Audit-Clean
**Trust Anchor**: Sealed seed with SHA-256 + MRCC binding

---

## Overview

Base120 v1.0.0 is a deterministic governance substrate containing 120 canonical mental models across 6 domains. This document describes how downstream systems should consume Base120 as immutable infrastructure.

---

## Trust Surface

The following artifacts constitute the complete trust surface:

| Artifact | Path | Purpose |
|----------|------|--------|
| Seed JSON | `artifacts/base120.v1.0.0.seed.json` | Canonical 120-model corpus |
| SHA-256 Hash | `artifacts/base120.v1.0.0.seed.sha256` | Integrity verification |
| MRCC Binding | `compliance/base120.v1.0.0.seed.mrcc.json` | Governance claims and provenance |

---

## Verification (Required)

Before consuming Base120, downstream systems MUST verify integrity:

### Python
```python
import json
import hashlib
from pathlib import Path

def verify_base120_seed(base120_path: Path) -> bool:
    """Verify Base120 seed integrity. Returns True if valid."""
    seed_path = base120_path / "artifacts" / "base120.v1.0.0.seed.json"
    hash_path = base120_path / "artifacts" / "base120.v1.0.0.seed.sha256"
    mrcc_path = base120_path / "compliance" / "base120.v1.0.0.seed.mrcc.json"

    # Compute hash
    with open(seed_path, "rb") as f:
        computed = hashlib.sha256(f.read()).hexdigest()

    # Read declared hash
    declared = hash_path.read_text().strip()

    # Read MRCC hash
    with open(mrcc_path) as f:
        mrcc = json.load(f)["sha256"]

    # Verify all match
    if computed != declared or computed != mrcc:
        raise ValueError(f"Hash mismatch: computed={computed}, declared={declared}, mrcc={mrcc}")

    return True
```

### Shell
```bash
#!/bin/bash
set -e

COMPUTED=$(sha256sum artifacts/base120.v1.0.0.seed.json | cut -d' ' -f1)
DECLARED=$(cat artifacts/base120.v1.0.0.seed.sha256)
MRCC=$(jq -r '.sha256' compliance/base120.v1.0.0.seed.mrcc.json)

if [ "$COMPUTED" != "$DECLARED" ] || [ "$COMPUTED" != "$MRCC" ]; then
    echo "FAIL: Hash mismatch"
    exit 1
fi

echo "PASS: Seed integrity verified"
```

---

## Consumption Patterns

### Pattern 1: Direct Reference (Recommended)

Clone or fetch the seed directly from this repository:

```bash
git clone https://github.com/hummbl-io/oss.git
# Verify integrity before use
```

### Pattern 2: Cached Copy

Store a local copy with provenance:

```python
import json
from datetime import datetime, timezone

# After verification
provenance = {
    "source": "hummbl-io/base120",
    "version": "v1.0.0",
    "sha256": "74c51092b218dcf7b430569fffb36a23ae42aa07f7f1b900479b1721e585656d",  # pragma: allowlist secret -- public sha256 of base120 v1.0.0 seed artifact
    "acquired_at": datetime.now(timezone.utc).isoformat(),
    "verified": True
}
```

### Pattern 3: API Fetch

```python
import requests

SEED_URL = "https://raw.githubusercontent.com/hummbl-io/base120/main/artifacts/base120.v1.0.0.seed.json"
HASH_URL = "https://raw.githubusercontent.com/hummbl-io/base120/main/artifacts/base120.v1.0.0.seed.sha256"

# Fetch and verify before use
```

---

## Model Access

The seed contains 120 models across 6 domains:

| Domain | Prefix | Count | Description |
|--------|--------|-------|-------------|
| Perspective | P | 20 | P1-P20 |
| Inversion | IN | 20 | IN1-IN20 |
| Composition | CO | 20 | CO1-CO20 |
| Decomposition | DE | 20 | DE1-DE20 |
| Recursion | RE | 20 | RE1-RE20 |
| Systems | SY | 20 | SY1-SY20 |

### Lookup by ID

```python
import json

with open("artifacts/base120.v1.0.0.seed.json") as f:
    corpus = json.load(f)

# Build lookup index
models_by_id = {m["id"]: m for m in corpus["models"]}

# Access specific model
model = models_by_id["P1"]
print(model["name"])  # "First Principles Framing"
print(model["definition"])
```

### Lookup by Domain

```python
from collections import defaultdict

models_by_domain = defaultdict(list)
for m in corpus["models"]:
    models_by_domain[m["domain"]].append(m)

# Get all Composition models
composition_models = models_by_domain["CO"]
```

---

## Citation Format

When referencing Base120 models in downstream systems, use:

```
base120:v1.0.0:{model_id}
```

Examples:
- `base120:v1.0.0:P1` — First Principles Framing
- `base120:v1.0.0:IN5` — Negative Space Framing
- `base120:v1.0.0:CO7` — Network Effects

---

## Prohibited Actions

Downstream systems MUST NOT:

| Prohibition | Rationale |
|-------------|----------|
| Modify the seed JSON | Immutable trust anchor |
| Add or remove models | Governance violation |
| Rename or alias model IDs | Shadow vocabulary |
| Extend model definitions | Semantic purity |
| Provide feedback to Base120 | One-way consumption |
| Cache with TTL refresh | v1.0.0 is frozen |

---

## Integration Template

For comprehensive integration guidance, see the [90-Day Downstream Integration Template](https://github.com/hummbl-io/oss/tree/main/packages/base120-corpus-validator/blob/main/docs/downstream-integration-template.md) in System B.

---

## Support

Base120 v1.0.0 is frozen and governance-complete. For questions:

- Review [spec-v1.0.0.md](spec-v1.0.0.md) for scope clarification
- System B: [base120-corpus-validator](https://github.com/hummbl-io/oss/tree/main/packages/base120-corpus-validator) for consumption governance
