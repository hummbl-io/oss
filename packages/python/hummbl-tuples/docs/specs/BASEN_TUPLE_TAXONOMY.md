# BaseN Tuple Taxonomy

Status: draft  
Scope: reasoning-path tuples for HUMMBL BaseN systems

See also:

- `docs/specs/REASONING_SEMANTICS.md`
- `docs/specs/HUMAN_CONTROL_GLOSSARY.md`

## 1. Purpose

Base120 is one curated reasoning profile. BaseN is the more general framework.

BaseN means:

- any number of transformations
- any number of mental models within each transformation
- evolving registries over time
- explicit control over who selects reasoning paths

This taxonomy defines tuples for reasoning-path selection, not only governance and execution.

## 2. Core Principle

Reasoning should be representable as a typed path.

A path is made of:

- candidate generation
- selection
- rejection
- override
- execution
- comparison
- evidence

Tuples are the atomic records of that path.

## 3. BaseN Metadata

Every BaseN reasoning run should carry:

- `problem_id`
- `run_id`
- `base_profile`
- `transformation_registry_version`
- `mental_model_registry_version`
- `control_mode`
- `selector_identity`

## 4. Control Modes

Control mode is a first-class field, not informal metadata.

Allowed modes:

- `AI_AUTONOMOUS`
- `AI_PROPOSE_HUMAN_CONFIRM`
- `HITL_INFLUENCED`
- `HITL_CONTROLLED`
- `HOTL_SUPERVISED`

## 5. Reasoning Tuple Classes

### 5.1 TRANSFORMATION_CANDIDATE

Represents a proposed transformation for a given problem.

Required fields:

- `problem_id`
- `transformation_id`
- `candidate_rank`
- `proposed_by`
- `selection_rationale`

### 5.2 TRANSFORMATION_SELECTED

Represents the transformation actually chosen.

Required fields:

- `problem_id`
- `transformation_id`
- `selected_by`
- `control_mode`
- `selection_rationale`

### 5.3 TRANSFORMATION_REJECTED

Represents a considered but rejected transformation.

Required fields:

- `problem_id`
- `transformation_id`
- `rejected_by`
- `rejection_reason`

### 5.4 MODEL_CANDIDATE

Represents a proposed mental model within a transformation.

Required fields:

- `problem_id`
- `transformation_id`
- `mental_model_id`
- `candidate_rank`
- `proposed_by`

### 5.5 MODEL_SELECTED

Represents the mental model chosen under the active transformation.

Required fields:

- `problem_id`
- `transformation_id`
- `mental_model_id`
- `selected_by`
- `control_mode`
- `selection_rationale`

### 5.6 MODEL_REJECTED

Represents a mental model that was considered and discarded.

Required fields:

- `problem_id`
- `transformation_id`
- `mental_model_id`
- `rejected_by`
- `rejection_reason`

### 5.7 REASONING_PATH

Represents an ordered path through transformations and models.

Required fields:

- `problem_id`
- `path_id`
- `path_steps`
- `control_mode`
- `constructed_by`

### 5.8 HITL_OVERRIDE

Represents a human override of AI-proposed reasoning choices.

Required fields:

- `problem_id`
- `overridden_tuple_id`
- `override_type`
- `human_actor`
- `override_reason`

Allowed `override_type` values:

- `TRANSFORMATION_CHANGE`
- `MODEL_CHANGE`
- `PATH_PRUNE`
- `PATH_FREEZE`
- `FORCED_SELECTION`

### 5.9 PATH_COMPARISON

Represents comparison between candidate or executed reasoning paths.

Required fields:

- `problem_id`
- `path_a_id`
- `path_b_id`
- `comparison_basis`
- `preferred_path`
- `decided_by`

### 5.10 TRACE_EVIDENCE

Represents evidence produced by executing or evaluating a reasoning path.

Required fields:

- `problem_id`
- `path_id`
- `claim`
- `metric_bundle`
- `evidence_status`

## 6. Relationship to Existing Governance Tuples

BaseN reasoning tuples do not replace the governance tuple layer.

They compose with it.

- `CONTRACT`: defines bounded work
- `DCT`: defines delegated authority
- `DCTX`: defines lifecycle context
- `SYSTEM`: defines runtime control events
- `EVIDENCE`: defines execution proof

Reasoning tuples explain how the path was chosen.
Governance tuples explain how the path was authorized, executed, and evidenced.

## 7. Key Research Questions

- What is the minimum tuple vocabulary needed for reasoning-path governance?
- When should a reasoning choice become a tuple rather than stay internal?
- How much path visibility is necessary for trustworthy human oversight?
- Does BaseN flexibility improve outcomes or only increase path entropy?

## 8. Initial Claim

BaseN turns HUMMBL from a fixed reasoning library into a governed reasoning meta-framework.

Tuples are the substrate that makes the reasoning path inspectable, comparable, and experimentally tractable.
