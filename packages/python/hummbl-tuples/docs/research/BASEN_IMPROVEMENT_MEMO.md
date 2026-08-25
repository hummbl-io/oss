# BaseN Improvement Memo

Status: design memo  
Scope: how BaseN should improve beyond the current March 27 implementation

## Thesis

BaseN should not be treated as:

- a fancy prompt library
- a synthetic trace dump
- or a lightweight SFT label for any reasoning-like text

BaseN becomes compelling only if it does three things well:

1. separates reasoning structure from execution scaffolding
2. preserves path semantics rather than flattening them into text
3. makes path quality measurable

## What BaseN Needs Next

### 1. A stricter corpus contract

Every BaseN trace should carry at least:

- `task_id`
- `problem_class`
- `protocol_id`
- `protocol_family`
- `step_order`
- `step_type`
- `control_mode`
- `generator_identity`
- `generator_model`
- `rubric_version`
- `registry_version`
- `quality_status`

Without this, BaseN traces are too easy to confuse with generic synthetic CoT.

### 2. Path-conditioned supervision, not flat imitation

The current implementation mostly turns traces into text.

The stronger BaseN approach is:

- teach the model to predict the next path element given explicit prior path state
- mask loss to the supervised target span only
- distinguish:
  - path selection
  - path execution
  - path evaluation

This is closer to structured reasoning supervision than ordinary SFT.

### 3. Corpus quality gates before training

BaseN should have dataset validators that reject or quarantine traces when:

- step labels leak across protocols
- expected step order is violated
- protocol families are mixed
- content is empty, duplicated, or templated junk
- path length is outside protocol bounds

This should be a first-class gate, not a manual cleanup step.

### 4. A held-out challenge set

BaseN should not be evaluated only on the same style of tasks used to generate the traces.

It needs:

- held-out tasks
- adversarial tasks
- transfer tasks
- tasks where the correct protocol is not obvious
- human-rated path comparisons

This is the cleanest way to avoid “taxonomy overfitting.”

### 5. Distinguish protocol traces from rubric traces

Right now the line between:

- reasoning protocol execution
- wickedness/readiness/BKI scoring

is too blurry.

BaseN should model them as different supervision families:

- `PROTOCOL_TRACE`
- `RUBRIC_TRACE`
- `PATH_EVAL`
- `OVERRIDE_EVENT`

That lets the system learn different things from each class instead of collapsing them into one bucket.

### 6. Add provenance and comparator fields to every aligned artifact

Every aligned model should declare:

- source checkpoint
- exact trace files used
- trace counts by family
- training steps
- effective batch size
- response masking policy
- eval packet location

Without this, aligned outputs are hard to compare and easy to overclaim.

## How I Would Improve BaseN Conceptually

### BaseN should evolve from “reasoning library” to “reasoning operating system”

That means:

- transformations are operators
- mental models are operator specializations or operand handlers
- control mode governs who can choose or veto operators
- tuples record path state transitions
- evidence records what the path actually achieved

So the real object is not a list of models.

It is a governed path machine.

### BaseN should have three explicit layers

#### Layer 1: Registry layer

- transformations
- mental models
- protocol families
- rubric families

#### Layer 2: Path layer

- candidate generation
- selection
- rejection
- override
- execution order

#### Layer 3: Evidence layer

- path outcome
- quality score
- failure mode
- human preference
- transfer result

This is much stronger than treating everything as “trace text.”

### BaseN should support learning from disagreement

One major improvement opportunity is to preserve disagreement explicitly:

- AI proposed path
- human-modified path
- human-rejected path
- competing protocol families

That turns BaseN into a system for studying reasoning governance, not just reasoning output.

### BaseN should include negative traces

The current tendency is to store “good-looking” traces.

BaseN will become more valuable if it also stores:

- malformed paths
- overfit paths
- redundant paths
- misleading but plausible paths
- human-corrected bad paths

That creates the substrate for failure-aware alignment.

## Recommended Build Order

1. corpus validator
2. response-masked trainer
3. path-conditioned dataset format
4. held-out challenge set
5. pre/post eval packet
6. disagreement-aware tuple classes

## Stronger Long-Term Framing

BaseN is most interesting when it becomes:

- a structured reasoning-path substrate
- a mixed-control experiment surface
- a failure-aware supervision layer
- and a governed evidence system

That is substantially stronger than “Base120 but larger.”
