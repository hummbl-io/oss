# Andrej Karpathy Profile

Date: 2026-03-27
Status: draft
Primary lane: software paradigms, verifiability, model ergonomics, AI education

## Question

Why does Andrej Karpathy matter for HUMMBL?

## Bottom Line

Karpathy matters because he consistently translates frontier ML into usable operator vocabulary. He is one of the clearest public thinkers on the shift from explicit code to learned systems to promptable model-mediated software, and that makes him directly relevant to HUMMBL's operator, orchestration, and reasoning-interface story.

For HUMMBL, Karpathy is less about world models than about practical model use: how humans actually work with models, how software changes when the model is part of the stack, and how new interfaces should be built around probabilistic systems.

## Core Ideas

- `Software 2.0`: neural-network weights are programs trained from examples instead of handwritten logic
- model-mediated software needs new operator habits, debugging patterns, and educational scaffolding
- verifiability is the key accelerator for useful AI workflows
- LLMs are strange computational objects and should not be treated as stable human analogues
- useful agents need explicit state, resettable environments, bounded scopes, and visible intermediate state

## Primary Sources

- `Software 2.0`  
  https://karpathy.medium.com/software-2-0-a64152b37c35
- `A Recipe for Training Neural Networks`  
  https://karpathy.github.io/2019/04/25/recipe/
- `Visualizing and Understanding Recurrent Networks`  
  https://arxiv.org/abs/1506.02078
- `World of Bits: An Open-Domain Platform for Web-Based Agents`  
  https://proceedings.mlr.press/v70/shi17a.html
- `Verifiability`  
  https://karpathy.bearblog.dev/verifiability/
- `The space of minds`  
  https://karpathy.bearblog.dev/the-space-of-minds/
- `Animals vs Ghosts`  
  https://karpathy.bearblog.dev/animals-vs-ghosts/
- `Eureka Labs`  
  https://eurekalabs.ai/
- `Fave Tweets`  
  https://karpathy.ai/tweets.html
- `Andrej Karpathy: Software Is Changing (Again)` transcript mirror  
  https://gist.github.com/nate-selzer/842514625486c2ee816ea0edb429629d

## What HUMMBL Should Borrow

- use Base120 and BaseN as operator-facing control vocabularies, not as claims of complete cognition
- push reasoning tasks toward verifiable subproblems and typed checks
- use tuples as the native audit, reward, and replay substrate
- design for partial autonomy with strong human override and visible intermediate state

## What HUMMBL Should Avoid

- reducing HUMMBL to prompt engineering alone
- over-anthropomorphizing model behavior or treating fluent language as stable reasoning
- building agent loops that cannot be replayed, graded, or interrupted
- letting elegant promptcraft substitute for evals, data quality, or verification

## Relation To HUMMBL

- Base120 / BaseN  
  Karpathy reinforces the need for a crisp operator language around transformations and mental models.
- tuples / governance  
  HUMMBL can extend his software-paradigm framing by making model choices, overrides, and evidence explicit tuple objects.
- world models / reasoning traces  
  His work is more about using model systems well than about latent world-model architecture.
- readiness / BKI / mission-governed operation  
  He is strongest on operator readiness: how humans learn, steer, and collaborate with model systems in practice.

## Ranking Snapshot

- architecture relevance: high
- research relevance: medium
- governance relevance: medium
- operator relevance: high
- publication value: high

## Open Questions

- How should HUMMBL relate its BaseN and tuple language to Software 2.0 / 3.0 without collapsing into prompt-only rhetoric?
- Which parts of Karpathy's operator framing can become measurable HUMMBL evidence rather than just good intuition?

## Confidence

Medium
