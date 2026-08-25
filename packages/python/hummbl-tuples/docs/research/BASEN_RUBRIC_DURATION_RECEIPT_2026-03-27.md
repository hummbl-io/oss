# BaseN Rubric Duration Receipt 2026-03-27

Status: duration extension beyond the 2-epoch rubric record  
Scope: `C:\Users\Owner\PROJECTS\yolo-playground\autoresearch-yolo`

## Baseline Record Before This Pass

Best rubric free-generation record before the duration test:

- checkpoint: `hummbl_basen_aligned_codex_split_2ep.pt`
- `lr = 5e-5`
- `epochs = 2`
- anchored decode:
  - `--force-prefix target_step`
  - `--repetition-penalty 1.30`
- results:
  - `val_bpb = 0.394554`
  - `avg_teacher_forced_loss = 2.5600`
  - `starts_with_target = 8/8`
  - `avg_keyword_hit_rate = 0.2750`

## New Duration Test

Run:

- checkpoint: `hummbl_basen_aligned_codex_split_3ep.pt`
- `lr = 5e-5`
- `epochs = 3`

Evaluation settings:

- same anchored decode as the prior record
  - `--force-prefix target_step`
  - `--repetition-penalty 1.30`

Observed result:

- `val_bpb = 0.404546`
- `avg_teacher_forced_loss = 2.2597`
- `starts_with_target = 8/8`
- `avg_keyword_hit_rate = 0.2792`

## Interpretation

This sets a new rubric free-generation record:

- keyword-hit rate improved from `0.2750` to `0.2792`

It also improves teacher-forced fit:

- `2.5600 -> 2.2597`

But it spends more retention:

- `0.394554 -> 0.404546`

So the duration extension does not dominate the prior record.
It creates a new frontier point:

- better free-generation and teacher-forced structure learning
- worse BPB retention

## Current Best-Point Split

Best rubric free-generation record:

- `hummbl_basen_aligned_codex_split_3ep.pt`
- `lr = 5e-5`
- `epochs = 3`
- anchored decode with repetition penalty `1.30`
- `avg_keyword_hit_rate = 0.2792`

Best rubric balance point:

- `hummbl_basen_aligned_codex_split_2ep.pt`
- `lr = 5e-5`
- `epochs = 2`
- anchored decode with repetition penalty `1.30`
- better retention at `0.394554`

## Qualitative Note

The 3-epoch outputs are still not production-quality.
They continue to:

- open with the correct target step
- surface more relevant rubric concepts
- then drift into malformed or repetitive continuations

So this is a real record, but still a frontier-stage record rather than a finished decoding solution.
