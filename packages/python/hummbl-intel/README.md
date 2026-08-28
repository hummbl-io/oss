# hummbl-intel

INT taxonomy framework: intelligence discipline categorization, source reliability grading, collection posture, and all-source fusion for agent systems.

[![Runtime Deps](https://img.shields.io/badge/runtime%20deps-zero-brightgreen)]()

## What This Is

Categorizes agent intelligence collection into the canonical DoD/ODNI taxonomy (SIGINT, HUMINT, OSINT, GEOINT, MASINT, FININT, TECHINT, IMINT, ALL-SOURCE) and provides tools for source grading, collection posture, and structured all-source fusion.

Stdlib-only. Zero third-party runtime dependencies.

## Modules

- **taxonomy**: INT enum, discipline definitions, canonical collection surfaces
- **grading**: Source reliability (A-F) and content credibility (1-6) scales
- **posture**: Per-INT collection health (GREEN/YELLOW/RED)
- **fusion**: All-source methodology, competing hypotheses, estimative probability
- **managers**: INT steward role definitions and assignments

## Installation

```bash
pip install hummbl-intel
```

## Usage

```python
from hummbl_intel.taxonomy import IntelligenceDiscipline
from hummbl_intel.grading import SourceReliability, ContentCredibility
from hummbl_intel.posture import CollectionPostureReport, PostureStatus
from hummbl_intel.fusion import CompetingHypothesesAnalysis, EstimativeProbability

# Categorize a collection source
discipline = IntelligenceDiscipline.OSINT

# Grade a source
reliability = SourceReliability.A  # Completely reliable
credibility = ContentCredibility.ONE  # Confirmed

# Track collection posture
posture = CollectionPostureReport(discipline=discipline, status=PostureStatus.GREEN)

# Competing hypotheses analysis
analysis = CompetingHypothesesAnalysis(hypotheses=[...], evidence=[...])
```

## Testing

```bash
cd packages/python/hummbl-intel
pip install -e ".[test]"
python -m pytest tests/ -v
```

## License

Apache 2.0
