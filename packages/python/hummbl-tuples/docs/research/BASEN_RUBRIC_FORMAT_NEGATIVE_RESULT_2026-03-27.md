# BaseN Rubric Format Negative Result 2026-03-27

Status: negative result  
Scope: `<local-path>`

## Hypothesis

After schema-normalized, target-step-trimmed rubric training, I tested whether adding a stricter format instruction to the rubric prompt would unlock the first nonzero field-level F1:

- training prompt change:
  - `Emit exactly one [TARGET_STEP] section using canonical comma-separated key=value pairs and no prose.`
- eval prompt matched the same contract

## Run

Checkpoint:

- `hummbl_basen_aligned_codex_fmt_2ep.pt`

Training:

- `lr = 5e-5`
- `epochs = 2`
- validated rubric split
- schema-normalized, target-step-trimmed targets
- explicit format instruction in the prompt

Evaluation:

- colon-anchored decode
  - `--force-prefix target_step_colon`
  - `--repetition-penalty 1.30`

Observed result:

- `val_bpb = 0.397045`
- `avg_teacher_forced_loss = 2.5896`
- `starts_with_target = 8/8`
- `avg_keyword_hit_rate = 0.3167`
- `avg_rubric_field_f1 = 0.0`

## Comparison To Current Leader

Current leader before this test:

- `hummbl_basen_aligned_codex_normtrim_2ep.pt`
- same retention class
- `avg_keyword_hit_rate = 0.3375`
- `avg_rubric_field_f1 = 0.0`

So the stricter format instruction:

- did **not** beat the current free-generation record
- did **not** unlock nonzero field-level F1

## Interpretation

This reduces uncertainty in a useful way:

- the next bottleneck is not just “ask more clearly for key=value pairs”
- the model still does not internalize canonical field emission strongly enough
- simple prompt tightening alone is not enough to cross the schema-compliance threshold

## Consequence

Do not treat prompt wording alone as the next frontier lever.

The stronger next candidates are:

1. explicit field-vocabulary constraints by target step
2. training targets with even more tightly limited value space
3. decoder-side field assembly or constrained token selection
