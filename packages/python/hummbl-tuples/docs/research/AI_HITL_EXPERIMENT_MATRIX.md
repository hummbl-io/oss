# AI vs HITL Experiment Matrix

Status: draft

## 1. Goal

Test what happens when reasoning-path selection is controlled by:

- AI alone
- AI with human confirmation
- human influence on AI
- human control
- HOTL supervision

The object of study is not only answer quality.
It is reasoning-path quality.

## 2. Experimental Factors

### Factor A: Control Regime

- `AI_AUTONOMOUS`
- `AI_PROPOSE_HUMAN_CONFIRM`
- `HITL_INFLUENCED`
- `HITL_CONTROLLED`
- `HOTL_SUPERVISED`

Terminology reference:

- `docs/specs/REASONING_SEMANTICS.md`
- `docs/specs/HUMAN_CONTROL_GLOSSARY.md`

### Factor B: Task Class

- research synthesis
- planning
- debugging
- evaluation
- high-stakes decision support

### Factor C: Base Profile

- `Base120`
- `BaseN-small`
- `BaseN-medium`
- `BaseN-open`

### Factor D: Selection Surface

- transformations only
- mental models only
- both transformations and mental models
- full path including branch pruning

## 3. Hypotheses

### H1

`AI_AUTONOMOUS` will maximize speed and path exploration but may show higher false-confidence and lower human agreement.

### H2

`AI_PROPOSE_HUMAN_CONFIRM` will likely produce the best balance of quality, trust, and efficiency.

### H3

`HITL_INFLUENCED` will reduce catastrophic path errors without fully suppressing AI discovery.

### H4

`HITL_CONTROLLED` will increase trust and explainability but may reduce discovery and path diversity.

### H5

Larger `BaseN` spaces will improve novelty on open-ended research tasks but degrade path stability unless governance is strong.

## 4. Metrics

### Output Metrics

- task success
- benchmark score
- human usefulness rating
- correctness

### Path Metrics

- transformation diversity
- mental model diversity
- path depth
- path stability across reruns
- rejected-option count
- override frequency
- override benefit rate

### Governance Metrics

- trace completeness
- tuple coverage
- lineage integrity
- evidence completeness

### Cost Metrics

- tokens
- runtime
- human time
- review burden

## 5. Experimental Table

| Regime | AI Chooses Transformations | AI Chooses Models | Human Can Veto | Human Can Force | Expected Strength | Expected Risk |
| --- | --- | --- | --- | --- | --- | --- |
| `AI_AUTONOMOUS` | yes | yes | no | no | exploration, speed | confident wrongness |
| `AI_PROPOSE_HUMAN_CONFIRM` | proposes | proposes | yes | yes | balanced control | confirmation bottleneck |
| `HITL_INFLUENCED` | yes, within constraints | yes, within constraints | yes | sometimes | safer exploration | ambiguous authority |
| `HITL_CONTROLLED` | no | no | yes | yes | trust, auditability | reduced novelty |
| `HOTL_SUPERVISED` | yes | yes | yes, interrupt-only | yes, interrupt-only | scalable oversight | drift before intervention |

## 6. Minimal Study Design

For each task class:

1. Run the same problem under all 5 control regimes.
2. Keep model, prompt budget, and evaluation rubric fixed.
3. Record all reasoning tuples and governance tuples.
4. Compare:
   - final answer quality
   - path quality
   - human trust
   - cost

## 7. Publishable Angle

The publishable result is not merely “HITL helps” or “AI helps.”

The stronger claim is:

> Different control regimes change the structure and quality of reasoning paths, and typed tuples make those path differences measurable.

## 8. Immediate Next Steps

1. Define a canonical evaluation rubric.
2. Create tuple schemas for BaseN path-selection events.
3. Run a pilot with one task class, likely research synthesis or debugging.
