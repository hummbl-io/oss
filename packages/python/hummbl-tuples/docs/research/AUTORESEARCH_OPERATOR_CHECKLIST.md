# Autoresearch Operator Checklist

Use this checklist before promoting any new benchmark or frontier result.

## 1. Pre-Run

- Define the run category before launch:
  - `300s_canonical`
  - `600s_scaling`
  - `1200s_scaling`
  - `1800s_scaling`
  - `3600s_scaling`
  - `hf_mix_baseline`
  - `hf_mix_tuning`
  - `fineweb_gpt2`
  - `alignment`
  - `exploratory`
- Confirm the authoritative repo for this run:
  - `<local-path>` (active authority — see [issue #75](https://github.com/hummbl-dev/hummbl-tuples/issues/75))
  - `<local-path>` is archived/historical — do not use for new runs
  - use `autoresearch-yolo` only when intentionally running an exploratory derivative lane
- Record git state:
  - branch
  - commit
  - dirty/clean
- Record dataset and tokenizer:
  - dataset name
  - tokenizer family
  - split/validation definition if non-default
- Record hardware context:
  - GPU model
  - VRAM policy
  - expected thermal condition
  - whether background GPU/CPU load is intentionally present
- Freeze the claim target:
  - what exactly is this run trying to beat
  - current baseline value
  - current frontier value
- Decide ahead of time how the run will be scored:
  - `keep`
  - `discard`
  - `frontier`
  - `needs_reconciliation`

## 2. Launch

- Use a log filename tied to the run category and timestamp.
- Ensure stdout/stderr are captured to a raw log.
- Ensure the run writes:
  - final footer metrics
  - dataset
  - training seconds
  - total seconds
  - peak VRAM
  - MFU
  - params
  - depth
  - time budget
- If possible, write a structured JSON sidecar at completion.

## 3. During Run

- Verify the run is actually making progress:
  - log file is growing
  - step count is increasing
  - active training process exists
- Note any confounders:
  - Ollama or other local models running
  - CPU burn
  - thermal throttling
  - interruptions
- If the run is a stress test, mark that explicitly while it is happening.

## 4. Post-Run

- Copy the final footer metrics into a structured receipt.
- Append the result to the correct scoreboard:
  - canonical benchmark table
  - longer-budget table
  - dataset-specific sweep table
- Save or verify a sidecar JSON.
- Mark the run status:
  - `keep`
  - `discard`
  - `crash`
  - `needs_reconciliation`
- If the run changes the frontier, write a one-paragraph note:
  - what changed
  - why it likely helped
  - what still remains uncertain

## 5. Promotion Rules

Do not promote a run to a headline claim unless it has all of:

- raw log
- final metric footer
- scoreboard row
- repo/branch attribution

Prefer also having:

- JSON sidecar
- short markdown receipt
- note on confounders

## 6. Escalation Rules

Mark a run `needs_reconciliation` if any of the following are true:

- filename and footer disagree
- params/depth/dataset are inconsistent across artifacts
- the score appears only in prose, not in a raw receipt
- the run came from a scratch workspace but is being framed as canonical
- the benchmark class is ambiguous

## 7. Practical Rule

If a run is important enough to mention in a SITREP, it is important enough to preserve as a receipt packet.
