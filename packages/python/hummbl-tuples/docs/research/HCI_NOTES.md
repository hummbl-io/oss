# Human-Computer Interaction Notes

Date: 2026-03-27
Status: draft

## Question

What does HCI add to HUMMBL?

## Bottom Line

HCI gives HUMMBL its operator design constraints. A good system is not only capable; it is usable, steerable, contestable, and legible to the human in the loop.

For HUMMBL, HCI is the domain that makes Base120/BaseN and tuple-governed reasoning operational rather than merely descriptive.

## Core Ideas

- human-AI interaction needs explicit design guidelines
- mixed-initiative systems should interleave machine suggestion and human control
- evaluation must consider usability, not only model accuracy
- interactive systems combine algorithms, human judgment, and interface constraints
- trust, explainability, and user agency are design properties, not afterthoughts

## Primary Sources

- Amershi et al., `Guidelines for Human-AI Interaction`  
  https://www.microsoft.com/en-us/research/wp-content/uploads/2019/01/Guidelines-for-Human-AI-Interaction-camera-ready.pdf
- Horvitz, `People, Agents, and Interaction: Principles of Mixed-Initiative User Interfaces`  
  https://erichorvitz.com/uiact.htm
- ACM CHI 2019 proceedings  
  https://chi2019.acm.org/for-attendees/proceedings/
- ACM IUI call for papers  
  https://iui.acm.org/2019/call_for_papers.html
- Meredith Ringel Morris, Human-Centered AI Research  
  https://cs.stanford.edu/~merrie/ai.html

## What HUMMBL Should Borrow

- design mixed-initiative modes explicitly
- make state, options, and handoff points visible to the operator
- treat explanations as interface objects, not as proof objects
- optimize for contestability and recovery, not just success
- make evaluation include human workload and decision quality

## What HUMMBL Should Avoid

- full autonomy by default
- opaque outputs with no interrupt or override path
- treating human involvement as a bug instead of a control feature
- confusing a good model with a good interface
- assuming explainability alone solves trust

## Relation To HUMMBL

- Base120 / BaseN  
  Best used as operator-facing control vocabulary for decomposition and action selection.
- tuples / governance  
  Tuples are the right primitive for recording handoffs, overrides, and decision evidence.
- world models / reasoning traces  
  HCI helps ensure traces are usable and contestable, not just internally coherent.
- readiness / BKI  
  Strong fit. Readiness includes whether operators can understand, intervene, and coordinate with the system.

## Confidence

High
