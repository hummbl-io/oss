# CSCW Notes

Date: 2026-03-27
Status: draft

## Question

What does CSCW add to HUMMBL?

## Bottom Line

CSCW is the right domain if HUMMBL wants to move from smart reasoning to cooperative work that actually functions. The field is about how technology supports interdependent work: shared artifacts, coordination, awareness, handoffs, and mixed-initiative collaboration.

For HUMMBL, that means tuples and Base120/BaseN become most useful when they help people and agents coordinate on real work, not just generate good answers.

## Core Ideas

- CSCW centers social and collaborative work, not isolated individual use
- shared artifacts are coordination devices
- handoffs and division of labor are first-class problems
- awareness is a design requirement, not a bonus feature
- human-agent collaboration belongs in a cooperative-work framing, not only an automation framing

## Primary Sources

- `ACM CSCW 2026 scope and submission guidelines`  
  https://cscw.acm.org/2026/papers.html
- `Groupware and social dynamics: eight challenges for developers`  
  https://cacm.acm.org/research/groupware-and-social-dynamics/
- `Jonathan Grudin publications`  
  https://jonathangrudin.com/publications/
- `Collaborative affordances of records for coordination`  
  https://link.springer.com/article/10.1007/s10606-017-9298-5
- `Shared desktop / artifact awareness work`  
  https://grouplab.cpsc.ucalgary.ca/grouplab/uploads/Publications/Publications/2006-SharedDesktopVideo.CSCW.pdf
- `Concurrent Human-Agent Collaboration in Shared Artifact Systems`  
  https://arxiv.org/abs/2603.02050

## What HUMMBL Should Borrow

- make shared artifacts first-class
- design for mixed initiative
- treat handoff as a core protocol
- expose progress and uncertainty
- optimize for collaborative work, not just model autonomy

## What HUMMBL Should Avoid

- building systems that only optimize for a single user
- treating collaboration as an afterthought layered onto a solo-agent workflow
- hiding handoff points, ownership, or uncertainty inside opaque traces
- assuming that more autonomy automatically means better work
- using CSCW language for something that is really just individual prompting

## Relation To HUMMBL

- Base120 / BaseN  
  Should function as a collaborative reasoning and action vocabulary, not only an internal taxonomy.
- tuples / governance  
  Very strong fit, because CSCW needs shared artifacts, provenance, status, ownership, and recovery paths.
- world models / reasoning traces  
  CSCW makes traces operational for multiple humans and agents, not just inspectable in isolation.
- readiness / BKI  
  Very strong fit. Readiness is partly whether a group can coordinate around shared state, awareness, and handoff.

## Confidence

High
