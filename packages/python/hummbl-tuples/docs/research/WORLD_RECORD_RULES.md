# World Record Rules

This file defines the categories under which HUMMBL may use record language for TinyStories training runs.

## Rule 1: No Unqualified Record Language

Do not say `world record` without naming the category.

Allowed examples:
- `best verified TinyStories validation BPB in our current corpus`
- `candidate unofficial TinyStories BPB record for ~33M params under ~600 seconds`
- `best verified TinyStories BPB under a 3600 second wall-clock budget`

Disallowed example:
- `world record` with no benchmark category

## Rule 2: Every Headline Metric Must Link to a Raw Receipt

A record claim must map directly to:

- exact log filename
- footer metrics
- time budget
- parameter count
- dataset
- model depth

If the run identifier only exists in prose and not in the raw receipt, the claim is incomplete.

## Rule 3: Hardware Must Be Named

At minimum include:

- GPU model
- VRAM class
- single-GPU vs multi-GPU

For the current Windows runs, the relevant hardware class is:
- `RTX 3080 Ti, 12GB`

## Rule 4: Category Must Be Explicit

Every record claim must specify one of:

- `best_absolute`
- `best_600s`
- `best_1800s`
- `best_3600s`
- `best_same_family`
- `best_efficiency_adjusted`

## Rule 5: Same-Family Comparisons Must Match These Fields

For `same family` comparisons, require:

- same dataset
- same tokenizer/vocab regime if known
- same parameter class
- same depth class where relevant
- same budget class

## Rule 6: Reconciliation Before Promotion

Do not promote a run to record status if:

- filename and footer disagree materially
- docs cite a metric but omit the source log
- a newer better run exists in the same category

Example current reconciliation issue:
- `pretrain_67M_1800s_final.log` footer says `191.9M`, not `67M`

## Rule 7: Preferred Wording Ladder

Use the strongest wording supported by the evidence:

1. `verified run`
2. `best in current corpus`
3. `candidate unofficial record in category X`
4. `record` only when external baseline memo exists

## Rule 8: Public Comparison Threshold

Before public use of stronger record language, create or update:

- [WORLD_RECORD_BASELINES.md](/Users/others/PROJECTS/hummbl-tuples/docs/research/WORLD_RECORD_BASELINES.md)
- [WORLD_RECORD_HISTORY.md](/Users/others/PROJECTS/hummbl-tuples/docs/research/WORLD_RECORD_HISTORY.md)
- [TRAINING_RUN_LEDGER.md](/Users/others/PROJECTS/hummbl-tuples/docs/research/TRAINING_RUN_LEDGER.md)

## Working Policy

As of this session, the safest wording is:

- `candidate unofficial TinyStories BPB record in our current verified corpus`

not:

- `unqualified TinyStories world record`
