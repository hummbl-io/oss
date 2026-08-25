# Scaling Laws Notes

Date: 2026-03-27
Status: draft

## Question

What do scaling laws add to HUMMBL?

## Bottom Line

Scaling laws give HUMMBL a discipline for reasoning about predictable gains, diminishing returns, and where brute-force growth stops paying for itself. They are useful not because they settle AI theory, but because they force explicit tradeoffs among parameters, data, compute, and now test-time or post-training effort.

For HUMMBL, scaling laws matter as a caution against overcommitting to a single growth axis. They support a broader thesis that post-training, control, evaluation, and governance may become relatively more important as raw scale saturates.

## Core Ideas

- performance often improves with scale in predictable power-law-like ways
- data, parameters, and compute trade off against each other rather than scaling independently
- scaling laws are useful for planning investments, not only for describing curves after the fact
- more scale does not remove the need for control, evaluation, or alignment
- new scaling regimes increasingly include post-training and inference-time compute

## Primary Sources

- `Scaling Laws for Neural Language Models`  
  https://arxiv.org/abs/2001.08361
- `Training Compute-Optimal Large Language Models`  
  https://arxiv.org/abs/2203.15556
- `On the Origin of Neural Scaling Laws: From Random Graphs to Natural Language`  
  https://arxiv.org/abs/2601.10684
- `Implicit bias produces neural scaling laws in learning curves, from perceptrons to deep networks`  
  https://arxiv.org/abs/2505.13230
- `International AI Safety Report 2026`  
  https://internationalaisafetyreport.org/sites/default/files/2026-02/international-ai-safety-report-2026_1.pdf

## What HUMMBL Should Borrow

- model multiple scaling axes instead of assuming “bigger model” is the only lever
- treat post-training and test-time compute as first-class design levers
- use scaling expectations to decide where structure and governance add more value than brute-force growth
- make capability-growth assumptions explicit in governance and deployment planning
- keep cost, data, and energy constraints visible

## What HUMMBL Should Avoid

- assuming scaling alone solves reasoning, control, or safety
- treating empirical laws as timeless guarantees
- ignoring the possibility of scaling walls, saturation, or regime shifts
- using scaling language without resource accounting
- conflating better benchmark curves with better sociotechnical performance

## Relation To HUMMBL

- Base120 / BaseN  
  Useful as non-scale levers for control, reasoning organization, and human/agent coordination.
- tuples / governance  
  Can encode scaling assumptions, cost envelopes, post-training interventions, and deployment thresholds.
- world models / reasoning traces  
  Scaling laws help explain capability growth, but not necessarily whether traces are trustworthy or well-governed.
- readiness / BKI  
  Strong fit because scaling affects not just capability, but adoption cost, governance burden, and institutional trust.

## Confidence

High on relevance; medium-high on longer-term interpretation.
