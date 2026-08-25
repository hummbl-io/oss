# Bio-Cognitive Standards Memo

Date: 2026-03-27
Status: draft

## Question

Can `bio-cognitive`, `bio-operational`, and `bio-governance` be grounded in existing standards and official guidance rather than treated as branding?

## Bottom Line

Yes.

The terms are new, but the underlying standards backbone is real:

- physical activity and energy expenditure standards
- exercise and training guidance
- ergonomics and work-system design guidance
- occupational safety and health management

That means HUMMBL can treat this as a standards-backed research lane.

## Standards Backbone

### Physical Activity And Fitness

- `Compendium of Physical Activities`
  - practical taxonomy for activity types and energy expenditure
  - useful for encoding activity categories and effort assumptions
  - https://pacompendium.com/
  - https://pacompendium.com/adult-compendium
- `Youth Compendium of Physical Activities`
  - useful when age-specific interpretation matters
  - https://www.nccor.org/nccor-tools/youthcompendium/
- `WHO Guidelines on Physical Activity and Sedentary Behaviour`
  - official public-health baseline for recommended activity levels
  - https://www.who.int/publications/i/item/9789240014886
- `CDC / HHS Physical Activity Guidelines`
  - U.S. implementation and recommendations
  - https://www.cdc.gov/physical-activity/php/guidelines-recommendations/index.html

### Strength And Conditioning

- `NSCA Position Statements`
  - official evidence-based positions on strength and conditioning topics
  - https://www.nsca.com/about-us/position-statements/
- useful examples:
  - resistance training for older adults
  - long-term athletic development
  - youth resistance training

### Human Factors And Ergonomics

- `ILO Principles and guidelines for human factors / ergonomics design and management of work systems`
  - strongest official work-systems anchor
  - https://www.ilo.org/publications/principles-and-guidelines-human-factors-ergonomics-hfe-design-and
- `ILO-OSH 2001`
  - stronger on occupational safety management and controls
  - https://www.ilo.org/publications/guidelines-occupational-safety-and-health-management-systems-ilo-osh-2001

## How The Terms Map

### Bio-Cognitive

Grounded by:

- workload and human-state concepts from HFE
- exertion and activity categories from Compendium work
- physical activity and sedentary-risk baselines from WHO and CDC

Primary research questions:

- how does human state affect interaction quality, judgment, or learning?
- which signals are meaningful enough to model?
- when does physical load become cognitive or operational risk?

### Bio-Operational

Grounded by:

- exercise prescription and training-adaptation logic
- ergonomic redesign and workload adaptation
- readiness, recovery, and pacing concepts from training science

Primary research questions:

- how should systems adapt tasks, interfaces, or training in response to state?
- what counts as a safe versus unsafe adaptation?
- when should the system slow down, escalate, or hand off?

### Bio-Governance

Grounded by:

- HFE design-management principles
- OSH management principles
- organizational oversight and safety constraints

Primary research questions:

- who can act on physiological or workload signals?
- what evidence is needed before adaptation?
- what must be logged, explained, or overridden by a human?

## HUMMBL Relevance

This lane is useful for HUMMBL because it creates a path from:

- state sensing
- to adaptive action
- to governed and auditable intervention

That fits:

- tuples as decision and evidence records
- BaseN as a repertoire of intervention or reasoning choices
- human-control regimes for deciding when AI may act

## What To Avoid

- vague wellness language without measurable variables
- treating fitness metrics as if they were universally meaningful
- acting on weak proxies without governance
- importing coaching terminology without ergonomic or safety discipline

## Suggested Early Use Cases

- operator workload and fatigue adaptation in long AI sessions
- readiness-aware suggestion pacing
- ergonomic intervention logging
- training or recovery recommendation governance
- human override rules for bio-derived inferences

## Confidence

High on standards backing. Medium on immediate operationalization because measurement quality and permissions matter a lot.
