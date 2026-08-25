# Cynthia Rudin Profile

Date: 2026-03-27
Status: draft
Primary lane: interpretable ML, high-stakes evaluation, transparent decision systems

## Question

Why does Cynthia Rudin matter for HUMMBL?

## Bottom Line

Rudin is the clearest contributor in this set for the claim that high-stakes AI should be inherently interpretable, not merely explained after the fact. Her work is a direct challenge to black-box-first system design in domains where people need to verify reasoning, troubleshoot decisions, and justify outcomes.

For HUMMBL, she is especially useful because she makes evaluation and transparency architectural requirements rather than optional features. That aligns strongly with tuples, evidence, and governed reasoning paths.

## Core Ideas

- for high-stakes decisions, use inherently interpretable models when possible
- post-hoc explanations for black boxes are often not a sufficient substitute for transparency
- interpretable models can be accurate enough in many regulated or safety-critical settings
- evaluation should compare transparent alternatives against opaque ones, not assume opacity is necessary
- model behavior should be inspectable enough that humans can verify, debug, and contest it

## Primary Sources

- `Cynthia Rudin`  
  https://users.cs.duke.edu/~cynthia/home.html
- `Stop Explaining Black Box Machine Learning Models for High Stakes Decisions and Use Interpretable Models Instead`  
  https://arxiv.org/abs/1811.10154
- `Interpretable machine learning: Fundamental principles and 10 grand challenges`  
  https://doi.org/10.1214/21-SS133
- `Interpretable Machine Learning: Fundamental Principles and 10 Grand Challenges`  
  https://users.cs.duke.edu/~cynthia/docs/PrinciplesOfInterpJSM2023ToPrint.pdf
- `What is Interpretable Machine Learning?`  
  https://www.informs.org/News-Room/INFORMS-Releases/Audio-Releases/What-is-Interpretable-Machine-Learning
- `Cynthia Rudin Receives 2025 IJCAI McCarthy Award`  
  https://stat.duke.edu/news/cynthia-rudin-receives-2025-international-joint-conference-artificial-intelligence-mccarthy
- `Is the Artificial Intelligence Boom a 'Runaway Train'?`  
  https://today.duke.edu/2023/02/artificial-intelligence-boom-runaway-train

## What HUMMBL Should Borrow

- make transparency a first-class requirement in high-stakes paths
- prefer models and workflows that humans can inspect, verify, and contest
- treat evaluation as a comparison among real model classes, not just explainability tooling
- use interpretable outputs as the default in decision-support contexts where precision and trust both matter
- design reasoning traces to be auditable, not decorative

## What HUMMBL Should Avoid

- assuming black-box explanations are an adequate substitute for transparent models
- treating interpretability as only a UX or policy layer
- hiding critical decisions behind opaque scoring when simpler transparent alternatives exist
- conflating model performance with decision legitimacy
- assuming a reasoning trace is valuable if it cannot be verified or used for troubleshooting

## Relation To HUMMBL

- Base120 / BaseN  
  Rudin pushes Base120 and BaseN toward transparent reasoning operators with clear semantics, not just expressive taxonomies.
- tuples / governance  
  Strong fit. Tuples are a natural way to encode interpretable decisions, evidence, rule sets, and contestable decision paths.
- world models / reasoning traces  
  She is less about world models than about the visibility of decision logic, but her work strongly supports making reasoning traces inspectable and faithful.
- readiness / BKI / mission-governed operation  
  Strong fit for readiness and governance: if the system is making high-stakes calls, the operator needs something better than post-hoc explanation.

## Ranking Snapshot

- architecture relevance: high
- research relevance: high
- governance relevance: high
- operator relevance: medium
- publication value: high

## Open Questions

- Which HUMMBL tasks can be served by fully interpretable models rather than explainable black boxes?
- How should HUMMBL measure whether a reasoning path is truly faithful, contestable, and useful for troubleshooting?

## Confidence

High
