# hummbl-rubric-templates

Evaluation-rubric templates in YAML, with a validator that checks each template
for required fields, weight totals, and supported values.

A rubric here is structured, not prose: declared parameters, pass/fail **hard
gates**, **weighted dimensions** that must sum correctly, and **required
outputs**. The validator catches the failure mode where a rubric looks complete
but its weights don't add up or required gate fields are missing.

- MIT OR Apache-2.0
- Python >= 3.11, requires `pyyaml`

## Install

Not on PyPI as of 2026-11-01. From the monorepo root, install the source:

```bash
pip install -e packages/python/hummbl-rubric-templates
```

## Source templates

| Template | Evaluates |
|---|---|
| `agent-coordination.yaml` | Multi-agent coordination and fleet operations |
| `base120-protocol-run.yaml` | A Base120 protocol run |
| `nist-ai-rmf-compliance.yaml` | Coverage against NIST AI RMF v1.0 |
| `global-org-ranking.yaml` | Comparative organization ranking |
| `game-build-pipeline.yaml` | Illustrative Godot game build evaluation |

The game-build template uses illustrative weights, not empirical calibration.
An evaluator must assess its gates and apply score caps; the validator only
checks structure and supported values.

The schema they share is `schema/hummbl-rubric-master.yaml`. These paths are
relative to `packages/python/hummbl-rubric-templates`; run the examples below
from that directory.

## Validate a template

```python
from pathlib import Path
from hummbl_rubric_templates import validate_template

ok, errors = validate_template(Path("templates/agent-coordination.yaml"))
if not ok:
    for err in errors:
        print(err)
```

```bash
python -m hummbl_rubric_templates.validate_template templates/agent-coordination.yaml
```

Validation runs four independent checks, each returning its own error list:
`validate_parameters`, `validate_hard_gates`, `validate_weighted_dimensions`,
and `validate_required_outputs`. Call them individually when you want partial
validation during authoring.

## Writing a template

Start from a source template, keep `base_schema` pointing at the master
schema, and set `parameters` for your context — `context_name`,
`framework_reference`, `evaluation_scope` (`single_document`, `multi_phase`,
`fleet_wide`, or `cross_repo`), `artifact_types`, `governance_level`,
`stakeholder_type`, `risk_profile`, and `compliance_criticality`.

Then validate before use. An unvalidated rubric produces scores nobody can
defend later.

## Scope

This source tree contains templates and a validator. It does not run evaluations,
score artifacts, or store results.
