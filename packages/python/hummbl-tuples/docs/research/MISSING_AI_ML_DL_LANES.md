# Missing AI / ML / DL Lanes

Date: 2026-03-27
Status: draft

## Question

As the corpus drifts back toward AI, ML, and deep learning, what important lanes are still missing or underdeveloped?

## Bottom Line

The corpus is strong on:

- world models
- reasoning traces
- contributor profiles
- sociotechnical foundations
- governance, safety, and human control

The main gaps are now more specific. The most important missing lanes are:

1. mechanistic interpretability
2. post-training optimization and verifier systems
3. retrieval, memory, and agentic knowledge systems
4. multimodal and embodied foundation models
5. evaluation and benchmark design for agents, tools, and long-horizon behavior
6. data curation, synthetic data, and curriculum design
7. sparse architectures, mixture-of-experts, and systems efficiency
8. distillation, model compression, and capability transfer
9. neuroscience-inspired learning and representation hypotheses
10. data poisoning, memory poisoning, and training-time security

## Ranked Gaps

### 1. Mechanistic Interpretability

This is the clearest missing bridge between "reasoning traces" and "what the model is actually doing internally."

Why it matters:

- tests whether explicit traces correspond to internal circuits or are only post hoc rationalizations
- strengthens any claim that HUMMBL can govern reasoning rather than just record outputs
- creates a bridge from operator-visible path selection to hidden model internals

Useful entry points:

- Anthropic on circuit tracing and model internals  
  https://www.anthropic.com/research/mapping-mind-language-model  
  https://www.anthropic.com/research/tracing-thoughts-language-model

### 2. Post-Training Optimization And Verifier Systems

The corpus mentions post-training, but it does not yet have a dedicated note on RLHF, DPO, RLVR, verifiers, process reward models, or self-verification.

Why it matters:

- likely the most direct ML lane for your reasoning-trace thesis
- where explicit traces, process supervision, verifier selection, and reward shaping all converge
- directly relevant to AI vs HITL control comparisons

Useful entry points:

- `Trust, But Verify` on RLVR and self-verification  
  https://arxiv.org/abs/2505.13445
- EMNLP 2025 verification engineering work  
  https://aclanthology.org/2025.emnlp-main.1542.pdf

### 3. Retrieval, Memory, And Agentic Knowledge Systems

You have knowledge management at the sociotechnical level, but not yet a dedicated AI-side lane for RAG, agent memory, retrieval planning, or memory poisoning.

Why it matters:

- HUMMBL will likely rely on retrieval and memory more than on base-model training
- tuples can govern memory writes, retrieval decisions, and evidence lineage
- poisoning and drift risks are central if memory becomes part of reasoning

Useful entry points:

- Agentic RAG survey  
  https://arxiv.org/abs/2501.09136
- broader RAG survey  
  https://arxiv.org/abs/2506.00054
- memory poisoning on LLM agents  
  https://arxiv.org/abs/2512.16962

### 4. Multimodal And Embodied Foundation Models

The corpus has world-model and robotics-adjacent contributors, but not a dedicated lane for multimodal reasoning, VLMs, VLAs, or embodied evaluation.

Why it matters:

- world models become much more concrete in multimodal and physical settings
- BaseN may need to evolve beyond text reasoning operators
- tuples may need perception, actuation, and environment-state semantics

Useful entry points:

- robot learning survey in the foundation-model era  
  https://www.sciencedirect.com/science/article/pii/S0925231225006356
- CVPR 2026 embodied foundation-model workshop  
  https://wdfm-eai.github.io/CVPR26/

### 5. Evaluation And Benchmark Design For Agents

You have evaluation as a recurring theme, but no dedicated note for:

- tool-use evaluation
- long-horizon task success
- agent reliability
- realistic failure taxonomies
- benchmark contamination and ecological validity

Why it matters:

- BaseN and tuple claims need agent-level evaluation, not only model-level evaluation
- production usefulness depends on reliability under tools, memory, and handoffs

Useful entry points:

- HELM capabilities and safety efforts at CRFM  
  https://crfm.stanford.edu/2025/03/20/helm-capabilities.html  
  https://crfm.stanford.edu/2024/11/08/helm-safety.html

### 6. Data Curation, Synthetic Data, And Curriculum Design

This lane appears in the ML trace lifecycle spec, but there is no dedicated research note yet.

Why it matters:

- pretraining and post-training both depend on data quality and sequencing
- reasoning traces may be most valuable as synthetic curriculum and filtering artifacts
- HUMMBL needs a view on provenance, contamination, and curriculum shaping

### 7. Sparse Architectures, Mixture-Of-Experts, And Systems Efficiency

This is a real gap if you want the corpus to stay technically relevant.

Why it matters:

- frontier systems increasingly depend on routing, sparsity, and efficiency tradeoffs
- governance and operator systems may need to reason about heterogeneous capability paths

### 8. Distillation, Compression, And Capability Transfer

This matters because your research repeatedly touches explicit versus latent reasoning.

Why it matters:

- distillation is how explicit traces often become compressed capability
- this is central to whether readable traces remain faithful after training

### 9. Neuroscience-Inspired Learning Hypotheses

The corpus has cognitive science and consciousness, but not much on modern computational neuroscience as it bears on representation, memory, and planning.

Why it matters:

- useful for separating metaphor from architecture
- relevant to world models, predictive processing, and memory systems

### 10. Training-Time Security And Data Poisoning

You have governance and safety science, but not enough AI-native work on:

- data poisoning
- backdoors
- synthetic-data contamination
- retriever and memory poisoning

Why it matters:

- if traces, memories, or synthetic curricula become first-class, poisoning risks become structural

## Recommendation

Next batch should prioritize:

1. mechanistic interpretability
2. post-training plus verifiers
3. retrieval and memory systems
4. multimodal and embodied foundation models
5. agent evaluation and benchmark realism

That batch would reconnect the corpus to the actual current AI frontier while still fitting the HUMMBL thesis.

## Confidence

High. These gaps are clear from the current repo contents and from recent external research trends.
