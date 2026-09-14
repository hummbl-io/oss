# Pressure-Test: PRAWN Work Stage vs. ARCANA Lens Battery

**Subject**: The `work` stage of the PRAWN cycle (v0.1-draft)
**Method**: Deep pressure-test against 3 ARCANA lenses chosen for maximal diagnostic tension — not the lenses most likely to *affirm* the stage, but the lenses most likely to *break* it.
**Purpose**: Validate that Work-as-sole-write-authority survives contact with the lenses most hostile to it, before committing the stage to a crosswalk synthesis run.

---

## The claim under test

> **Work is the ONLY stage with external write authority.** All other stages (Perceive, Reason, Account, Notate) operate on internal state or the audit record. Work alone touches the world. This concentration makes the blast radius auditable: every external effect traces to one stage, and every trace from that stage is an external effect.
>
> The contract's current definition: *"Execution — the only stage with external write authority; all other stages operate on internal state or the audit record."*

The strongest version of the opposing claim: *concentration of write authority is not a safety feature but a liability. A single write stage is a single point of failure, a single attack surface, and a single variety bottleneck. Distributing writes across stages with scoped authority would be safer than concentrating them in one — because a breach of Work is a breach of everything, and a Work that lacks the variety to model its own effects will write harm it cannot foresee.*

---

## Lens 1: Schneier — the security mindset

**The tension.** Schneier's lens asks not "does this work?" but "how does this break?" If Work is the sole stage with external write authority, then Work is also the sole attack surface. Every adversary who wants to affect the external world through the agent has exactly one target. Concentration is presented as an auditability feature; the security mindset reframes it as a *target-rich single point of failure*. The question is not whether the blast radius is auditable after the fact, but whether the blast radius is *defensible* before the fact.

**What this lens sees in Work.**
- The contract says "all other stages operate on internal state or the audit record." From a security view this is a privilege-separation claim: only Work holds the write capability. Privilege separation is good *when the privileged component is small, well-audited, and fails safe*. But the contract says nothing about Work's internal structure — it's a single undifferentiated "execution" stage. A monolithic privileged component is harder to audit than a decomposed one, even if there's only one of it.
- The concentration creates a *high-value target*. adversaries don't attack the stage with the most defenses; they attack the stage whose compromise yields the most. Compromising Reason produces bad plans that Account might catch. Compromising Account produces rubber-stamped plans that Work executes faithfully. Compromising Work produces *correct-looking plans executed as harm* — and because Work is the only write stage, there is no downstream stage that can refuse the write. Notate records the harm but cannot prevent it. The cycle has no write-stage redundancy.
- The deeper Schneier point: "auditable blast radius" is a *forensics* property, not a *prevention* property. It tells you what happened after the write landed. It does not stop the write from landing. A security architecture that optimizes for auditability over prevention is optimizing for the post-mortem, not for the patient.

**Does Work survive?** Yes, but the survival is conditional, not automatic. Schneier doesn't destroy the concentration claim — privilege separation (one write stage) is genuinely safer than no separation (every stage writes). But he forces the contract to admit that *concentration without internal decomposition is a brittle privilege boundary*. The contract currently treats Work as an atomic stage. Schneier says the write authority should be concentrated at the *stage boundary* but decomposed *inside* the stage: Work should have an internal separation between the decision-to-write and the execution-of-write, so that a compromised executor can't also compromise the authorization. This is the principle of least privilege applied *within* the privileged stage.

**Contract implication.** Add to the PRAWN contract: *Work's write authority is concentrated at the stage boundary but must be decomposed internally into write-authorization and write-execution, so that compromise of the executor does not yield compromise of the authorization. The blast radius is auditable only if the audit record distinguishes "what Work was authorized to write" from "what Work actually wrote."* This is the Schneier amendment: concentration is a boundary property, not an internal one; the inside of the privileged stage must still be defended.

---

## Lens 2: Ashby — requisite variety and the Good Regulator

**The tension.** Ashby's Law of Requisite Variety says a regulator must have at least as much variety as the system it regulates. Work *is* the regulator of the external world — it writes to the world, and every write is an act of governance over the world's state. But the variety of the external world is effectively unbounded (it includes every state the world could be in after the write, including states no one anticipated), and the variety of Work's write operations is constrained by the action space the agent was given. The variety gap is not a tuning error; it's structural. Work will *always* have less variety than the world it writes to.

**What this lens sees in Work.**
- The Good Regulator Theorem says the regulator must be a *model* of the system. Work is not a model of the external world — it's an *actuator*. Reason is the model (it draws intent from perception via mental models); Work is the hand that moves on the model's instruction. If Work has no internal model of the world it's writing to, it cannot predict the effect of its writes, and unpredicted effects are ungoverned effects. The contract says Work executes; it doesn't say Work *understands what it's executing into*.
- The concentration claim ("only Work writes") makes the variety problem *worse*, not better. If write authority were distributed, each writing stage could carry a model of its own local world-slice, and the variety would be distributed across models. Concentrating writes in Work concentrates the variety burden in one stage that has no model. The auditability gain (one blast radius) is purchased at the cost of a variety deficit (one model trying to cover the whole world).
- The feedback gap: Work's variety is bounded by what it can *do*, but the world's variety is bounded by what it can *do back*. Work writes; the world responds. If Work cannot perceive the world's response (that's Perceive's job, next cycle), then Work is writing blind within its own stage. The cycle's design defers feedback to the next Perceive — which means Work's variety is always one cycle behind the world's. This is not a bug; it's the cost of a staged cycle. But the contract must name it.

**Does Work survive?** Yes, but with an explicit ceiling. Ashby doesn't say "don't act" — he says "no actuator has requisite variety over an unbounded world, so every write is a bet that the world's response stays within the variety the agent's model can absorb." The contract must not promise that Work *controls* its effects; it must promise that Work *writes under uncertainty*, and that the cycle's feedback loop (Work → Notate → Perceive) is the mechanism that closes the variety gap over time. The concentration claim survives only if the feedback loop is fast enough that the variety deficit doesn't accumulate into catastrophe before the next Perceive.

**Contract implication.** Add to the PRAWN contract: *Work does not have requisite variety over the external world; every write is a bet made under uncertainty. The cycle's feedback loop (Work → Notate → Perceive) is the variety-recovery mechanism — it does not eliminate the variety gap, it bounds the time over which the gap is uncorrected. Work's write authority is safe only if the feedback latency is shorter than the time it takes for an unpredicted effect to become irreversible.* This is the Ashby amendment: name the variety deficit, name the feedback mechanism, and make the latency-vs-irreversibility relationship explicit.

---

## Lens 3: Illich — counter-productivity

**The tension.** Illich's concept of counter-productivity identifies a threshold beyond which a tool produces the opposite of its intended effect. The tool doesn't just *fail* — it becomes *actively harmful* by doing exactly what it was designed to do, at a scale or intensity where the doing itself is the harm. Applied to Work: the PRAWN cycle is designed to produce *governed action*. Work is the stage that acts. But the cycle's very structure — Work as the sole write stage, the only stage that *does anything real* — creates an institutional pressure to *act*. If the only stage with world-effect is Work, then the cycle's output is measured at Work, and a cycle that doesn't Work has produced nothing. The question Illich forces: when does the pressure to have a Work output create pressure to act when not-acting would have been the better outcome?

**What this lens sees in Work.**
- The PRAWN cycle has no explicit *refrain* stage. Perceive, Reason, Account, Work, Notate — every stage produces something, and Work is the stage that produces *external effect*. If the cycle runs and Work doesn't fire, the cycle looks like it failed (it perceived, reasoned, accounted, and then... did nothing). But sometimes the correct output of a governance cycle is *a decision not to act*. The contract has no stage for that. Not-acting is an unmarked outcome — it shows up as the absence of Work, which shows up as a null cycle, which looks like a defect.
- The concentration claim amplifies the counter-productive pressure. Because Work is the *only* stage that touches the world, the cycle's entire relationship to the world is mediated through one valve. If that valve is open, the world is changed; if it's closed, the cycle is "just thinking." An institution that measures itself by world-changes will bias toward keeping the valve open. This is Illich's threshold: the tool (the governed cycle) becomes counter-productive when the governance pressure to *show output* exceeds the epistemic pressure to *wait for better information*.
- The deeper Illich point: counter-productivity is not a failure of the agent but a *structural* feature of the tool. The agent may correctly perceive, reason, and account — and still be pressured to Work because the cycle's design makes not-Working invisible. The harm is not that Work does bad things; it's that Work does *unnecessary* things, and unnecessary writes to the world accumulate into a world that is worse than the world where the cycle had the discipline to not-write.

**Does Work survive?** Yes, but only if the contract makes *not-acting a first-class cycle outcome*. Illich doesn't say "don't have a Work stage" — he says "a tool whose only output is action will, past a threshold, produce action as its own end." The amendment is structural: the cycle must have an explicit *refrain* path — a way for Reason or Account to terminate the cycle with a notated decision to not-Work, such that the cycle counts as *complete* (not failed) when Work doesn't fire. Without this, the concentration of write authority in Work creates a structural bias toward action, and that bias is the counter-productive threshold.

**Contract implication.** Add to the PRAWN contract: *a cycle that terminates at Account (or Reason) with a notated decision not to act is a complete cycle, not a failed one. The absence of Work is a valid outcome when the cost of acting exceeds the cost of waiting. Notate must record refrain-decisions with the same weight as Work-decisions, so that the cycle's output metric does not bias toward action.* This is the Illich amendment: make not-acting visible, or the pressure to act becomes counter-productive.

---

## Synthesis: does Work survive the pressure-test?

**Yes, with three amendments the contract must absorb before the crosswalk run:**

| # | Amendment | Source lens | Contract change |
|---|---|---|---|
| 1 | Work's write authority is concentrated at the stage boundary but must be decomposed internally into write-authorization and write-execution | Schneier | Add internal privilege separation to the stage description; audit record must distinguish authorized-write from executed-write |
| 2 | Work does not have requisite variety over the external world; every write is a bet under uncertainty, and the feedback loop is the variety-recovery mechanism | Ashby | Name the variety deficit; make feedback-latency-vs-irreversibility explicit |
| 3 | A cycle that terminates without Work (a notated decision to refrain) is a complete cycle, not a failed one | Illich | Add explicit refrain-path; Notate must record refrain-decisions with equal weight to Work-decisions |

**The deepest finding.** The pressure-test reveals that Work's *structural claim* (concentration makes the blast radius auditable) is *not* the same as Work's *safety claim* (concentration makes the blast radius *defensible*). The structural claim survives all three lenses — auditability is real, and privilege separation at the stage boundary is genuinely better than no separation. But the safety claim has three holes the contract must patch:

1. **Schneier**: auditability is forensics, not prevention. The inside of the privileged stage must be defended, not just the boundary.
2. **Ashby**: the write stage has no model of the world it writes to, and the variety gap is structural. Safety depends on feedback latency, not on Work's own competence.
3. **Illich**: a cycle whose only world-effect is Work will, past a threshold, produce action as its own end. Not-acting must be a visible, notated, complete outcome — or the concentration of write authority becomes a pressure to act.

The contract should keep the concentration claim as the headline (it survives) and add the three caveats as load-bearing qualifications. Work is the sole write stage — and that is exactly why it must be decomposed internally (Schneier), honest about its variety ceiling (Ashby), and balanced by an explicit refrain-path (Illich).

**What this means for the crosswalk script.** The script's Phase 2 prompt should treat Work as a stage with *internal structure* (authorization vs. execution) rather than as an atomic executor. The refrain-path should be available as a valid cycle termination in the synthesis, so that the model is not structurally biased toward producing a Work output for every cycle. The feedback-latency parameter should be surfaced as a governance knob, not hidden as an implementation detail.

---

## Recommendation

Apply the three amendments to `ecosystem_contracts.py` before running the crosswalk synthesis. Specifically:
- Amend the `work` stage description to include internal privilege separation (write-authorization vs. write-execution) and the audit-record distinction between authorized and executed writes.
- Add the variety-deficit caveat: every write is a bet under uncertainty; the feedback loop (Work → Notate → Perceive) is the variety-recovery mechanism; safety depends on feedback latency being shorter than the time to irreversibility.
- Add the refrain-path: a cycle that terminates at Account or Reason with a notated decision not to act is complete, not failed. Notate records refrain-decisions with equal weight to Work-decisions.

These are contract refinements that make the crosswalk synthesis more honest — and they were discovered by pressure-testing before the synthesis run, which is exactly the use case the pressure-test validates.

---

*Pressure-test complete. Work stage survives with amendments. Ready for contract refinement and crosswalk run.*
