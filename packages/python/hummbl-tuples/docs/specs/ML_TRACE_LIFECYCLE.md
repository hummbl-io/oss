# ML Trace Lifecycle

Status: draft  
Scope: reasoning traces across pre-training, post-training, evaluation, and test-time scaling

## 1. Why This Matters

Reasoning traces are appearing in more than one place in modern ML systems.

They now show up as:

- synthetic data during continued pretraining
- execution-derived supervision
- explicit chain-of-thought during SFT
- preference and reward signals during post-training
- latent or compressed reasoning during efficient inference research
- multi-trace sampling during test-time scaling

HUMMBL should treat these as governed lifecycle artifacts, not just transient model outputs.

## 2. Lifecycle Stages

### 2.1 Pre-training

Relevant uses:

- trace-derived synthetic corpora
- execution-derived reasoning data
- curriculum shaping
- provenance and filtering
- latent-thought or hidden-reasoning experiments

### 2.2 Continued Pretraining

Relevant uses:

- domain adaptation with reasoning-rich corpora
- process-heavy curriculum injections
- replayable trace provenance

### 2.3 Supervised Fine-Tuning

Relevant uses:

- explicit reasoning traces
- teacher-generated traces
- execution-to-rationale transformations
- trace quality scoring

### 2.4 Preference Optimization / RL / Process Supervision

Relevant uses:

- pairwise ranking of traces
- verifier judgments
- process reward signals
- trace-level failure attribution

### 2.5 Evaluation

Relevant uses:

- evidence-backed reasoning claims
- robustness checks across trace variants
- audit trails for evaluation datasets and trace selection

### 2.6 Test-Time Scaling

Relevant uses:

- multiple sampled traces
- selection and aggregation
- trace voting
- compression or latent reasoning fallback

## 3. Proposed HUMMBL Trace Dimensions

Every reasoning-trace artifact should be classifiable along these dimensions:

- `lifecycle_stage`: `pretraining`, `continued_pretraining`, `sft`, `preference_optimization`, `rl`, `eval`, `test_time`
- `trace_source`: `human`, `teacher_model`, `execution_derived`, `synthetic`, `latent`, `distilled`, `sampled`
- `trace_role`: `supervision`, `reward_signal`, `debug`, `evidence`, `safety`, `publication`
- `trace_visibility`: `explicit`, `compressed`, `latent`, `reconstructed`
- `governance_status`: `draft`, `trusted`, `provisional`, `sanitized`, `publishable`, `restricted`

## 4. Tuple Mapping

Suggested tuple usage:

- `CONTRACT`: define the bounded ML task or experiment
- `DCT`: authorize data generation, trace transformation, or reward-model access
- `DCTX`: preserve lineage between parent and child trace-producing steps
- `SYSTEM`: record training, filtering, verifier, or sampler actions
- `EVIDENCE`: record outcome claims, measured gains, and trace-backed experiment receipts

## 5. Immediate Research Questions

- Which trace classes belong in pretraining vs post-training?
- When is explicit trace storage worth the privacy and cost overhead?
- When should latent traces be reconstructed for audit?
- What is the minimum trace metadata needed for publishable claims?
- How should negative or misleading traces be represented?

## 6. Initial Position

Post-training is the fastest path to operational value.

Pre-training is the more novel frontier because trace provenance, latent-thought governance, and execution-derived curriculum design are still under-specified.

HUMMBL should support both.
