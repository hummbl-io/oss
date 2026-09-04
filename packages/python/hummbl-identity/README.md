# hummbl-identity

Unified agent identity facade integrating design-tokens, heraldry, and garage.

## Overview

This package is the **spine** that connects the three HUMMBL design system packages:

- **hummbl-design-tokens** — agent colors, trust tier colors, typography
- **hummbl-heraldry** — SHA-256 procedural heraldic arms
- **hummbl-garage** — Agent Performance Index, livery, watch faces

All three dependencies are optional. The package degrades gracefully when any
are missing, using fallback defaults. This keeps the core stdlib-only while
enabling full integration when the ecosystem is installed.

## Usage

```python
from hummbl_identity import IdentitySystem

identity = IdentitySystem()
devin = identity.get_agent("devin")
print(devin.color, devin.blazon, devin.dial_finish)
```

## License

MIT OR Apache-2.0
