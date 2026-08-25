# Operations Research Notes

Date: 2026-03-27
Status: draft

## Question

What do operations research and decision analysis add to HUMMBL?

## Bottom Line

Operations research gives HUMMBL a disciplined way to think about resource allocation, constraints, uncertainty, tradeoffs, and decision quality under limited capacity. It is the clearest domain for turning “what should we do next?” into structured comparison rather than intuition alone.

For HUMMBL, this matters because reasoning systems often need to allocate attention, time, compute, budget, and authority under uncertainty.

## Core Ideas

- objectives, constraints, and tradeoffs should be explicit
- uncertainty should be modeled, not ignored
- resource allocation often matters more than isolated local optimization
- decision quality depends on problem structure, not only solver quality
- sensitivity analysis matters because assumptions change

## Primary Sources

- `Decision Analysis for the Professional`  
  https://books.google.com/books/about/Decision_Analysis_for_the_Professional.html?id=RTx2QgAACAAJ
- `Smart Choices`  
  https://books.google.com/books/about/Smart_Choices.html?id=jC-17jEwN6cC
- `The Foundations of Decision Analysis Revisited`  
  https://pubsonline.informs.org/doi/10.1287/deca.2014.0293
- `Operations Research`  
  https://www.britannica.com/science/operations-research
- `Decision Analysis and Behavioral Research`  
  https://books.google.com/books/about/Decision_Analysis_and_Behavioral_Resea.html?id=CI7ZAAAAMAAJ

## What HUMMBL Should Borrow

- make objectives, constraints, and tradeoffs explicit
- support option comparison rather than single-answer generation
- record assumptions and sensitivity to changed conditions
- use tuples to capture options, constraints, criteria, and selected actions
- treat uncertainty as a design input

## What HUMMBL Should Avoid

- pretending optimization is possible without clear objectives and constraints
- hiding tradeoffs behind a single recommendation
- conflating model confidence with decision quality
- using decision language without sensitivity or scenario analysis
- treating local optima as system optima

## Relation To HUMMBL

- Base120 / BaseN  
  Can help structure option generation, comparison, and reframing under constraint.
- tuples / governance  
  Very strong fit for assumptions, options, criteria, sensitivities, and chosen actions.
- world models / reasoning traces  
  OR helps distinguish scenario modeling and decision comparison from free-form explanation.
- readiness / BKI  
  Strong fit because readiness often depends on resource allocation, prioritization, and tradeoff management under uncertainty.

## Confidence

High on relevance; medium-high on exact HUMMBL mapping.
