# Safety Science Notes

Date: 2026-03-27
Status: draft

## Question

What does safety science add to HUMMBL?

## Bottom Line

Safety science gives HUMMBL a discipline for understanding accidents, safeguards, systemic risk, and high reliability. It shifts the question from who made the mistake to how the system created conditions for failure or recovery.

For HUMMBL, this matters because governed reasoning systems can fail through interface mismatch, governance drift, brittle assumptions, or bad escalation logic, not only through model error.

## Core Ideas

- accidents are often systemic, not isolated personal failures
- safety depends on defenses, constraints, and organizational learning
- high reliability organizing requires sensitivity to operations, reluctance to simplify, and commitment to resilience
- safeguards and control structures matter as much as local component quality
- learning from near-misses is essential

## Primary Sources

- `High Reliability` (AHRQ PSNet primer)  
  https://psnet.ahrq.gov/primer/high-reliability
- `High Reliability Organization (HRO) Principles and Patient Safety` (AHRQ PSNet)  
  https://psnet.ahrq.gov/perspective/high-reliability-organization-hro-principles-and-patient-safety
- `Managing the Risks of Organizational Accidents`  
  https://books.google.com/books/about/Managing_the_Risks_of_Organizational_Ac.html?id=9_9vQgAACAAJ
- `How Complex Systems Fail`  
  https://how.complexsystems.fail/
- `Safety-I and Safety-II`  
  https://erikhollnagel.com/onewebmedia/SAFETY-I-AND-SAFETY-II.pdf
- `System Safety and Artificial Intelligence`  
  https://arxiv.org/abs/2202.09292
- `Managing the Unexpected`  
  https://books.google.com/books/about/Managing_the_Unexpected.html?id=V4FQDwAAQBAJ

## What HUMMBL Should Borrow

- analyze accidents and failures as systemic events
- design explicit safeguards, constraints, and escalation paths
- pay attention to weak signals and near-misses
- encode operational defenses and safety checks in governance artifacts
- connect safety to ongoing learning rather than static compliance
- adopt high-reliability principles: preoccupation with failure, reluctance to simplify, sensitivity to operations, deference to frontline expertise, and commitment to resilience

## What HUMMBL Should Avoid

- blaming individual operators for system-level failures
- assuming local model quality guarantees system safety
- reducing safety to checklists detached from actual operations
- ignoring brittle interactions between humans, models, and workflows
- treating absence of incidents as proof of safety

## Relation To HUMMBL

- Base120 / BaseN  
  Should be part of a broader safety architecture, not treated as the whole safeguard story.
- tuples / governance  
  Strong fit for safeguards, incidents, mitigations, escalation logic, and verification evidence.
- world models / reasoning traces  
  Safety science reminds HUMMBL that coherent traces do not guarantee safe operation.
- readiness / BKI  
  Strong fit because safe operation depends on shared vigilance, escalation norms, and learning culture.

## Confidence

High on relevance; medium-high on the exact HUMMBL mapping.
