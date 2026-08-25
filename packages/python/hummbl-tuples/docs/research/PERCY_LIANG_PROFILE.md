# Percy Liang Profile

Date: 2026-03-27
Status: draft
Primary lane: foundation models, evaluation, transparency, governance

## Question

Why does Percy Liang matter for HUMMBL?

## Bottom Line

Percy Liang matters because he has done some of the clearest work on making foundation models measurable, comparable, and governable. Through CRFM and HELM, he pushes the field toward broader evaluation, explicit incompleteness, and transparency as an operational requirement rather than a slogan.

For HUMMBL, he is the strongest contributor in this batch for benchmark design and evaluation discipline. He is also useful for framing the claim that governance requires what you can see, measure, and compare.

## Core Ideas

- foundation models are a broad sociotechnical paradigm, not just another model family
- evaluation should be holistic, standardized, and explicit about what is missing
- transparency is a precondition for accountability and public governance
- model-level benchmarks should capture multiple desiderata, not only accuracy
- safety evaluation should be broad, public, and standardized

## Primary Sources

- `Stanford profile`  
  https://profiles.stanford.edu/percy-liang
- `HELM: Holistic Evaluation of Language Models`  
  https://crfm.stanford.edu/2022/11/17/helm.html
- `HELM Instruct`  
  https://crfm.stanford.edu/2024/02/18/helm-instruct.html
- `HELM Safety v1.0`  
  https://crfm.stanford.edu/2024/11/08/helm-safety.html
- `CRFM Foundation Model Report`  
  https://crfm.stanford.edu/report.html
- `Foundation Model Transparency Index`  
  https://arxiv.org/abs/2310.12941
- `Foundation Model Transparency Reports`  
  https://arxiv.org/abs/2402.16268
- `Responses to NTIA's Request for Comment on AI Accountability Policy`  
  https://hai.stanford.edu/policy/responses-ntias-request-comment-ai-accountability-policy

## What HUMMBL Should Borrow

- make evaluation a first-class product surface rather than a side quest
- build benchmarks that acknowledge incompleteness instead of pretending coverage is total
- keep multiple metrics together when the system is sociotechnical
- treat transparency as a prerequisite for governance, not a cosmetic add-on
- separate evaluation of models from evaluation of downstream adaptation choices

## What HUMMBL Should Avoid

- assuming a single benchmark score can describe model quality
- treating “open” or “transparent” as sufficient without a structured evaluation story
- collapsing governance into policy language detached from artifacts and measurements
- building BaseN or tuple claims without comparable evaluation methods
- overfitting to language-only evaluation when the system has broader sociotechnical effects

## Relation To HUMMBL

- Base120 / BaseN  
  Percy reinforces that BaseN needs measurable evaluation and not just a richer taxonomy.
- tuples / governance  
  Tuples fit his agenda well because governance depends on inspectable artifacts, provenance, and comparable metrics.
- world models / reasoning traces  
  He is not a world-model theorist, but his work is relevant to evaluating reasoning traces and model behavior across contexts.
- readiness / BKI / mission-governed operation  
  Strong fit on readiness and governance, because he consistently emphasizes transparency, standardization, and accountability.

## Ranking Snapshot

- architecture relevance: medium
- research relevance: high
- governance relevance: high
- operator relevance: medium
- publication value: high

## Open Questions

- What would a HELM-like benchmark look like for HUMMBL reasoning paths, not just model outputs?
- How should HUMMBL define transparency and completeness for its own tuple-based artifacts?

## Confidence

High
