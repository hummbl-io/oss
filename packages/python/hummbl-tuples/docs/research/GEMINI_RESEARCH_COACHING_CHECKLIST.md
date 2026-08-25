# Gemini Research Coaching Checklist

Status: operator checklist for steering Gemini research work without letting it drift

## Purpose

Use this checklist when assigning Gemini a research lane.

The goal is not to slow Gemini down.
The goal is to keep fast output from turning into weak output.

## Before You Hand Off

- define the concrete deliverable
- define the source standard
- define what counts as fact vs inference
- define the output shape you want back
- define what not to do

If those are missing, Gemini will usually fill the gap with plausible-looking but less rigorous material.

## What To Specify Up Front

Always tell Gemini:

- the exact topic
- the exact output artifacts
- whether primary sources are required
- whether recommendations or only facts are wanted
- whether this is exploratory or decision-support research
- what level of uncertainty marking is required

## Minimum Good Prompt Elements

Every serious Gemini research packet should include:

- `Goal`
- `Deliverables`
- `Required sections`
- `Source requirements`
- `Output style requirements`
- `Explicit non-goals`

## What To Watch For In Gemini Outputs

Common failure modes:

- too much breadth, not enough evidence
- source-light summaries
- blending fact and speculation
- weak distinction between primary and secondary sources
- elegant wording that outruns the actual evidence
- recommendations before benchmark/context discipline

## Quick Review Questions

Before accepting Gemini research, ask:

1. Are the core claims visibly tied to sources?
2. Are primary sources actually present?
3. Are speculative sections labeled?
4. Is the output useful for downstream action, not just interesting?
5. Would a skeptical reviewer know what is measured and what is inferred?

## Good Gemini Roles

Gemini is especially useful for:

- broad source gathering
- fast initial domain mapping
- generating candidate datasets / standards lists
- expanding adjacent topic surfaces quickly
- drafting first-pass memos that will later be tightened

## Bad Gemini Roles

Do not trust Gemini alone for:

- final metric validation
- subtle benchmark comparison
- novelty claims
- “world record” framing
- proof that a research thesis is actually defensible

Those need a second pass with stricter evidence discipline.

## How To Coach Mid-Stream

If the output starts drifting, redirect with short corrections:

- “use primary sources only”
- “separate measured facts from inference”
- “rank the opportunities instead of listing everything”
- “show exact dataset names and links”
- “do not recommend yet; first compare”
- “rewrite this as a research memo, not a narrative”

## Best Handoff Pattern

Use Gemini in this order:

1. map the space
2. gather sources
3. draft structured memo
4. tighten with follow-up constraints
5. hand the result to a stricter reviewer

## Acceptance Rule

Accept Gemini research only when:

- the output is specific
- the source base is visible
- uncertainty is marked
- and the result can be turned directly into the next artifact or experiment

If it is only “interesting,” it is not ready.
