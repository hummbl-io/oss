# hummbl-taxonomy

Canonical governed intelligence tiers, taxonomy classifications, and automated classification engine.

## Installation

```bash
pip install .
```

## Quickstart

```python
from hummbl_taxonomy.classifier import IntelligenceClassifier

classifier = IntelligenceClassifier()
result = classifier.classify("Deterministic rule-based agent with frozen verification gates")
print(result)
```
