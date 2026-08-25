# Richard Sutton Profile

Date: 2026-03-27
Status: draft
Primary lane: reinforcement learning, predictive knowledge, scale, representation

## Question

Why does Richard Sutton matter for HUMMBL?

## Bottom Line

Sutton matters because he gives HUMMBL a disciplined answer to a dangerous instinct: do not overbuild human knowledge into the system when scalable learning and interaction can do better. His RL work and the bitter lesson both push toward general methods, prediction, search, and learning from experience rather than brittle hand-coded structure.

For HUMMBL, that is a strong warning against turning Base120 or BaseN into a clever but overfitted taxonomy. The better use is as a control and reasoning scaffold over systems that still learn from experience.

## Core Ideas

- prediction is central to learning and control
- temporal-difference learning turns successive predictions into a learning signal
- general methods that scale with computation tend to outperform hand-crafted knowledge in the long run
- the contents of minds are complex, so we should build meta-methods that discover that complexity
- a common decision-maker model should include perception, decision-making, internal evaluation, and a world model

## Primary Sources

- `Learning to Predict by the Methods of Temporal Differences`  
  https://jmvidal.cse.sc.edu/library/sutton88a.pdf
- `Predictive Representations of State`  
  https://papers.neurips.cc/paper/1983-predictive-representations-of-state.pdf
- `Temporal-Difference Networks`  
  https://arxiv.org/abs/1504.05539
- `The Bitter Lesson`  
  https://www.incompleteideas.net/IncIdeas/BitterLesson.html
- `The Quest for a Common Model of the Intelligent Decision Maker`  
  https://incompleteideas.net/papers/RLDM22-quest-common-model.pdf
- `Reward and Related`  
  https://incompleteideas.net/Talks/reward-hypothesis.pdf
- `Reward-Respecting Subtasks for Model-Based Reinforcement Learning`  
  https://arxiv.org/abs/2202.03466
- `Multi-Step Average-Reward Prediction via Differential TD(lambda)`  
  https://incompleteideas.net/papers/RLDM22-NS-Differential_TDlambda.pdf

## What HUMMBL Should Borrow

- keep the focus on general methods that scale with computation and experience
- treat prediction as a learning signal, not just a byproduct
- use TD-style thinking and internal evaluation where applicable
- prefer meta-methods, search, and learning loops over hard-coded domain knowledge
- separate representation learning from control and evaluation

## What HUMMBL Should Avoid

- overfitting Base120/BaseN into a static clever ontology
- assuming human-crafted reasoning structure will dominate long-run performance
- using imitation as the only learning story
- collapsing prediction, evaluation, and control into a single undifferentiated layer

## Relation To HUMMBL

- Base120 / BaseN  
  Sutton argues against over-encoding human knowledge; BaseN should be a flexible reasoning-control layer, not a frozen theory of intelligence.
- tuples / governance  
  Tuples can record prediction, evaluation, reward structure, and evidence so experience becomes inspectable.
- world models / reasoning traces  
  His work strongly supports predictive representation and internal evaluation as distinct from surface reasoning traces.
- readiness / BKI / mission-governed operation  
  His common-model framing reinforces input/output/goal plus internal evaluation and world model, which aligns with a disciplined readiness layer.

## Ranking Snapshot

- architecture relevance: high
- research relevance: high
- governance relevance: medium
- operator relevance: low
- publication value: high

## Open Questions

- How much of Sutton's experience-driven learning can HUMMBL express without controlling the base learner?
- Which tuple types would best encode prediction, reward, and internal evaluation as governed artifacts?

## Confidence

High
