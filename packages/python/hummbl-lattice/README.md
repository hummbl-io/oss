# hummbl-lattice

**Domain-specific reasoning operator lattices — validation, rating, and cohort tooling for the Domain120 framework.**

[![Python](https://img.shields.io/badge/python-3.11+-blue)](https://pypi.org/project/hummbl-lattice/)
[![License: MIT OR Apache-2.0](https://img.shields.io/badge/License-MIT%20OR%20Apache--2.0-blue)](LICENSE)
[![Dependencies](https://img.shields.io/badge/dependencies-0-brightgreen)]()

## What is hummbl-lattice?

**hummbl-lattice** provides tools for building, validating, and rating [Domain120](https://hummbl.io/domain120) lattices — domain-specific reasoning operator sets that generalize [TRIZ](https://en.wikipedia.org/wiki/TRIZ)'s 40-principle structure across arbitrary domains of practice.

Each Domain120 lattice consists of 20–40 reasoning operators organized into six families:

| Code | Family | Description |
|------|--------|-------------|
| P | Perspective | Reason from a specific viewpoint or framing |
| IN | Inversion | Reverse the problem or assumption |
| CO | Composition | Combine multiple approaches |
| DE | Decomposition | Break into independent parts |
| RE | Recursion | Apply the same move recursively |
| SY | Synthesis | Find leverage points or emergent patterns |

## Quick Start

```bash
pip install hummbl-lattice
```

```python
from hummbl_lattice import Lattice, LatticeOperator, LatticeValidator, KappaCalculator

# Build a lattice
lattice = Lattice(domain="Structural Engineering")
lattice.add_operator(LatticeOperator(
    code="IN01",
    name="Seismic Load Path Inversion",
    family="IN",
    definition="Instead of designing for expected loads, trace the failure path backward.",
    base120_ancestor="IN3",
))

# Validate it
validator = LatticeValidator()
report = validator.validate(lattice)
print(report.summary())
# Passed: 5, Failed: 2, Warnings: 0, Ratification: NOT READY

# Compute inter-rater reliability (Severe Test 2)
calc = KappaCalculator()
result = calc.compute("ratings.csv")
print(result.summary())
# κ=0.7200 (substantial agreement), threshold 0.6: PASS, ambiguous: 2, outliers: 0
```

## CLI

```bash
# Validate a lattice JSON file
hummbl-lattice validate my_lattice.json

# Compute Fleiss' kappa from a ratings CSV
hummbl-lattice kappa ratings.csv

# Show lattice info
hummbl-lattice info my_lattice.json
```

## The Stopping Rule

The core challenge in building a Domain120 lattice is knowing when to stop. The **stopping rule** is:

> A Domain120 operator must describe a cognitive transformation ("how to think"), not a domain fact or procedure ("what to do").

- **Reasoning operator (how to think):** "Instead of designing for expected loads, trace the failure path backward." — changes how you approach the problem.
- **Domain knowledge (what to do):** "Use cross-laminated timber for mid-rise retrofits." — tells you what to choose, not how to reason.

The `KappaCalculator` validates this rule by computing Fleiss' κ across multiple raters.

## Severe Tests

Domain120 lattices are validated against three severe tests:

| Test | Question | Tool |
|------|----------|------|
| Flat-Bag | Does typed structure add information? | (structural analysis) |
| Rater-Reliability | Can raters distinguish reasoning from knowledge? | `KappaCalculator` |
| Adversarial Null | Are operators genuinely domain-specific? | (cross-contamination test) |

## Design Principles

- **Stdlib-only**: Zero third-party runtime dependencies. Python 3.11+.
- **Deterministic**: Same input, same output. No randomness.
- **Tuple-native**: Lattices serialize to canonical JSON with SHA-256 hashes.
- **MIT OR Apache-2.0**: Open source, no vendor lock-in.

## Related

- [base120](https://pypi.org/project/base120/) — the 120 generic reasoning operators that Domain120 specializes
- [hummbl-governance](https://pypi.org/project/hummbl-governance/) — governance primitives for AI agent orchestration
- [Domain120 framework](https://hummbl.io/domain120) — framework documentation and draft lattices

## License

MIT OR Apache-2.0 — see [LICENSE](LICENSE).
