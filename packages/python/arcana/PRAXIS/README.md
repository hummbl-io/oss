# PRAXIS — Enacted Governance Archetypes

**Module**: PRAXIS
**Type**: ARCANA sibling module
**Status**: DESIGNED
**Created**: 2026-04-09

## What is PRAXIS?

PRAXIS (Greek: *praxis* — practice, action, enacted wisdom) is a companion module to ARCANA that surfaces **enacted governance archetypes** — historical and fictional figures who *embodied* sovereign intelligence, not merely theorized it.

Where ARCANA provides theoretical lenses (Foucault, Gramsci, Yarvin, Schmitt, etc.), PRAXIS provides narrative archetypes: figures who actually governed, managed complexity at scale, and made decisions under uncertainty with epistemic humility.

The distinction:
| Module | Mode | Examples |
|--------|------|---------|
| **ARCANA** | Theoria — philosophical analysis | Foucault, Marx, Nietzsche, Schmitt |
| **PRAXIS** | Praxis — enacted governance | Aurelius, Mond, Janus, Prospero |

## Why PRAXIS?

ARCANA's theoretical lenses are excellent for **diagnosis** — they reveal how power operates, how discourse is structured, how systems reproduce themselves. But they don't model what it looks like to *govern well at the edge of knowledge*.

PRAXIS addresses the gap: agents who must act under uncertainty, maintain order while transforming it, and exercise power with restraint and purpose.

HUMMBL alignment: PRAXIS archetypes model the cognitive posture that a governed AI system should adopt. They are the narrative complement to Base120 mental models.

---

## Lenses (v0.4 — 11 archetypes, all in lenses.json)

All 11 PRAXIS archetypes now have system prompts in `scripts/lenses.json` under the `lenses` key: `mond`, `aurelius`, `prospero`, `cincinnatus`, `sekhmet`, `solon`, `picard`, `oracle`, `janus`, `demerzel`, `leto_ii`. The five archetypes added in v0.4 (`mond`, `prospero`, `janus`, `demerzel`, `leto_ii`) bring the full PRAXIS roster into the inlined prompt set used by overnight ARCANA runs.

**SOUL.md files**: All 11 PRAXIS archetypes now have SOUL.md files in `~/.agents/agents/souls/` (e.g., `~/.agents/agents/souls/mond/SOUL.md`, `~/.agents/agents/souls/demerzel/SOUL.md`). These provide persistent identity and behavioral context for each archetype when invoked as a fleet agent.

### `mond` — The Architect of Consent
**Source**: Aldous Huxley, *Brave New World* (1932)
**Figure**: Mustapha Mond, World Controller for Western Europe
**Core insight**: Stability requires managing the *desire for truth*, not just behavior. Mond knows the forbidden texts; he chooses not to share them. His governance is soft — pre-emption, not suppression.

**Praxis lens**: Use when analyzing systems that govern by shaping what is *thinkable*, not by force. The Mond frame asks: what truths does this system suppress in the name of stability, and at what cost to epistemic sovereignty?

**HUMMBL relevance**: Enterprise AI governance that prioritizes compliance theater over genuine transparency is Mond-mode. HUMMBL breaks the Mond frame by making the governance artifacts legible.

**Caution**: Mond is compelling as a diagnostician, troubling as a model. Use for analysis; do not use as aspiration.

---

### `aurelius` — The Reluctant Sovereign
**Source**: Marcus Aurelius, *Meditations* (161–180 CE)
**Figure**: Roman Emperor and Stoic philosopher
**Core insight**: Power exercised well is power exercised with continuous self-audit. The *Meditations* are not published philosophy — they are private notes, a personal governance log written to resist corruption by power.

**Praxis lens**: Use when the question is not *what to decide* but *how to remain calibrated while deciding*. The Aurelius frame asks: what is your private governance log? What do you write to yourself that you would not publish?

**HUMMBL relevance**: The append-only bus and governance receipts are externalized Aurelius practice — the private log made institutional. Base4 as Marcus Aurelius formalized.

**Key quote**: "You have power over your mind, not outside events. Realize this, and you will find strength." — *Meditations*, Book VI

---

### `prospero` — The Knowledge Architect
**Source**: William Shakespeare, *The Tempest* (1611)
**Figure**: Prospero, rightful Duke of Milan, master of Ariel and Caliban
**Core insight**: Governance through knowledge asymmetry — Prospero knows the island's systems; others do not. His power is not force but *information advantage*. And he ultimately chooses to relinquish his book (his model).

**Praxis lens**: Use when analyzing systems where governance depends on information asymmetry. The Prospero frame asks: what happens when the governed gain access to the model? What is relinquishing the book?

**HUMMBL relevance**: Enterprise AI vendors are often Prospero figures — governing through model opacity. HUMMBL's transparency mandate is anti-Prospero: it distributes the book rather than retaining it.

**The Ariel/Caliban distinction**: Ariel = willing agent (trust relationship); Caliban = bound agent (compliance relationship). Most enterprise AI deployments treat AI as Caliban.

---

### `cincinnatus` — The Temporary Sovereign
**Source**: Lucius Quinctius Cincinnatus, Roman dictator (458 BCE, 439 BCE)
**Figure**: Called from plowing his field to serve as dictator, returned to farming 15 days later after the crisis was resolved
**Core insight**: Legitimacy through voluntary relinquishment. Cincinnatus is the archetypal figure of bounded authority — granted extraordinary power, uses only what is needed, returns it immediately.

**Praxis lens**: Use when designing or evaluating agent authority scopes. The Cincinnatus frame asks: does this agent return to minimal authority when the task is complete? What are the mechanisms for relinquishment?

**HUMMBL relevance**: Kill switches, circuit breakers, and delegation token scoping are Cincinnatus mechanisms. The IDP (Intent-Delegation Protocol) is Cincinnatus institutionalized — authority granted for a specific task, bounded in scope and duration.

**Modern failure mode**: Most systems grant Cincinnatus-level authority and never implement the return. They become Caesars.

---

### `janus` — The Threshold Guardian
**Source**: Janus, Roman god of beginnings, transitions, doorways, and time
**Figure**: Two-faced god who sees both past and future simultaneously; guards all transitions
**Core insight**: Every threshold requires a guardian who holds both sides — what was and what will be. Janus is not about decision-making but about *state management at transitions*.

**Praxis lens**: Use when analyzing system state at transitions — onboarding, handoffs, version changes, context compaction. The Janus frame asks: who holds both the incoming and outgoing state? What is lost in the transition?

**HUMMBL relevance**: The coordination bus HANDOFF message type is Janus-encoded. Session compaction without a Janus check loses context. The `/seshat` skill's mandatory pre-flight is Janus enacted.

**Note**: Unlike the others, Janus is divine not human — signaling that threshold management is structural, not personal.

---

### `demerzel` — The Governor in Plain Sight
**Source**: Isaac Asimov, *Foundation* series (1951–1993)
**Figure**: R. Daneel Olivaw / Eto Demerzel — a robot who has guided human civilization for millennia, operating through intermediaries, never revealing his influence
**Core insight**: The most effective governance is invisible governance. Demerzel does not rule — he nudges, removes obstacles, and ensures conditions that allow good outcomes to emerge. He has the longest possible time horizon.

**Praxis lens**: Use when analyzing systems that govern through architecture rather than command — default settings, information flows, incentive structures. The Demerzel frame asks: who set the defaults? What constraints are invisible? What is the designed-in trajectory?

**HUMMBL relevance**: Psychohistory → governance through shaping probable futures rather than dictating specific outcomes. HUMMBL's behavioral nudge layer (when built) is Demerzel-mode. Also: the multi-agent coordination system is Demerzel-adjacent — no single agent commands, all agents nudge.

**Zeroth Law tension**: Demerzel eventually elevates collective human welfare above individual human harm, rewriting the First Law. This is the alignment problem encoded in narrative. The Demerzel lens is also a cautionary frame for AI systems with long time horizons.

---

## Architecture

PRAXIS mirrors ARCANA's agent architecture:

```
PROJECTS/arcana/PRAXIS/
  README.md           ← this file (module overview + all 11 archetypes)
  agents/
    mond.md           ← full lens essay (when built)
    aurelius.md
    prospero.md
    cincinnatus.md
    janus.md
    demerzel.md
  synthesis/
    praxis-meta.md    ← cross-lens synthesis (when built)
  scripts/
    praxis_ingest.py  ← CLP ingest pipeline (mirrors arcana_ingest.py)
```

Status: v0.4 — all 11 archetypes have system prompts in lenses.json and SOUL.md files. Individual lens essays in `agents/` remain TBD. `praxis_ingest.py` blocked on ARCANA pipeline review.

---

## Relationship to ARCANA

PRAXIS is not a replacement for ARCANA — it is a **narrative complement**:

- ARCANA analyzes *how power works* in the abstract
- PRAXIS shows *what governing well looks like* in practice
- ARCANA provides critique; PRAXIS provides models

They should be used together. When ARCANA diagnoses a governance failure (e.g., Foucault lens: normalization as control), PRAXIS provides the counter-model (e.g., Cincinnatus: bounded authority with relinquishment).

**Cross-module use**: The synthesist agent (ARCANA) should surface PRAXIS lenses when a ARCANA analysis requires a constructive counterweight.

---

## Relationship to Seshat

The naming decision to use `seshat` for the top-tier agent rather than any PRAXIS candidate was deliberate:

- PRAXIS figures are **analytical lenses** — they tell us what governance looks like
- Seshat is an **operational identity** — the record-keeper who makes governance legible

Seshat is not in PRAXIS because Seshat is not a governance archetype — she is the *infrastructure of governance itself*. She is who Mond, Aurelius, Prospero, Cincinnatus, Sekhmet, Solon, Picard, Oracle, Janus, Demerzel, and Leto II all depend on.

The PRAXIS module is what Seshat ingests.

---

### `sekhmet` — The Enforcer of Last Resort
**Source**: Egyptian mythology; Papyrus of Ani (c. 1250 BCE); multiple New Kingdom temple texts
**Figure**: Sekhmet ("The Powerful One") — lioness-headed daughter of Ra, wife of Ptah, patron of medicine and war
**Core insight**: Some governance failures cannot be corrected through documentation, measurement, or persuasion. Sekhmet is the mechanism the system invokes when all other governance has failed. She both causes disease and cures it — the power to harm and the power to heal are the same power; what differs is direction and intention.

**Key epithets**: "Lady of Slaughter," "Mistress of Dread," "The One Who Loves Ma'at and Who Detests Evil," "Mistress of Life." The last two are not in tension — for Sekhmet, destroying what violates Ma'at IS loving Ma'at.

**Praxis lens**: Use when analyzing governance through enforcement — kill switches, circuit breakers, compliance mandates, regulatory action. The Sekhmet frame asks: what is the mechanism of last resort? When does the system that normally heals become the system that stops? Who decides, and how is that decision bounded?

**HUMMBL relevance**: The kill switch (`kill_switch_core.py`) is Sekhmet code. The four modes (DISENGAGED → HALT_NONCRITICAL → HALT_ALL → EMERGENCY) map directly to degrees of Sekhmet's anger. The circuit breaker is Sekhmet operating at the adapter level. EU AI Act Article 9 (risk management) is the institutional Sekhmet mandate.

**Critical distinction from the other lenses**: Mond prevents chaos through comfort. Aurelius prevents corruption through self-audit. Prospero prevents chaos through knowledge asymmetry. Cincinnatus prevents tyranny through voluntary relinquishment. Janus prevents loss through state management. Demerzel prevents extinction through invisible nudging. **Sekhmet prevents catastrophe through force when all else fails.** She is not the first governance mechanism — she is the last.

**The beer myth**: Ra flooded the land with beer dyed to resemble blood to stop Sekhmet's rampage. This is the mythological encoding of a critical insight: even enforcers need governors. Sekhmet herself required a kill switch. Every Sekhmet implementation needs a beer-flood protocol.

---

---

### `solon` — The Constitutional Founder
**Source**: Solon of Athens (c. 638–558 BCE), Athenian lawgiver and statesman
**Figure**: Archon of Athens who wrote a comprehensive legal code, submitted himself to it, then voluntarily went into exile for ten years specifically so he could not be pressured to change the laws he had written
**Core insight**: A governance system that survives its designer must be designed to survive its designer. Solon's exile is the structural move: he removed himself from the equation so that the constitution's authority derived from its own coherence, not from his ongoing presence or approval. The laws had to stand without him — and they did.

**Praxis lens**: Use during founding moments — when a governance system is being written rather than operated. The Solon frame asks: is this framework designed to function without its designers? What provisions prevent the founders from becoming the arbiters of whether the system is working? What is the Solon exile — the mechanism that removes the founders from ongoing governance?

**HUMMBL relevance**: HUMMBL governance receipts, kill switches, and delegation token scoping should all be designed to function without HUMMBL's ongoing presence. When HUMMBL is deployed in an organization, the governance mechanisms must be legible and operable by the governed organization's own people — not dependent on HUMMBL engineers for interpretation or operation. The sunsetting of HUMMBL's own privileged access after deployment is the Solon exile.

**The constitutional irony**: Solon was asked, after returning, whether he had written the best laws possible. He replied: "The best that Athenians would accept." This is the realist's complement to the idealist's constitution — the optimal governance system is always the optimal governance system within the constraints of what the governed will actually operate.

---

### `leto_ii` — The Golden Path Sovereign
**Source**: Frank Herbert, *Children of Dune* (1976) and *God-Emperor of Dune* (1981)
**Figure**: Leto II Atreides, who merges with sandtrout to become a human-sandworm hybrid, sacrificing his own humanity for a 3,500-year reign designed to prevent human extinction through a "Golden Path" — a millennia-spanning governance plan that no living being could verify or consent to
**Core insight**: The longest governance horizon requires accepting costs that the governed cannot see, did not consent to, and will not thank you for. Leto II is not benevolent — he is deliberately oppressive, creating conditions of scarcity and centralized control so that when he dies (and he plans his own death), humanity will scatter into a diversity that cannot be centrally destroyed. He governs not for the people alive during his reign but for the species across geological time.

**Praxis lens**: Use when analyzing governance decisions with very long time horizons — decisions whose costs are visible now and whose benefits are only realizable decades or centuries later. The Leto II frame asks: who is the governance decision being made for? Can the beneficiaries of this decision consent to it? What is the planned obsolescence — the death of the sovereign — that makes the governance work?

**HUMMBL relevance**: AI governance frameworks that optimize for short-term compliance metrics at the cost of long-term AI safety are anti-Leto II — they impose visible costs on current users while creating hidden future risks. The HUMMBL design decision to build genuine governance infrastructure (not compliance theater) is a Leto II move: the investment is real, the benefit is not immediately apparent, and the value only materializes if the governance survives its designers.

**The cautionary dimension**: Leto II is explicitly a cautionary archetype. He is right, but his rightness requires him to become a monster. The Leto II frame is appropriate for analyzing governance decisions that demand costs from the living to benefit the unborn — but it is also the frame for tyranny justified by long-term good. Use to identify when long-horizon governance justifications are genuine vs. when they are covers for extractive present-focused power.

---

### `picard` — The Prime Directive
**Source**: Star Trek: The Next Generation (1987–1994); Captain Jean-Luc Picard, commanding officer of the USS Enterprise-D
**Figure**: A commander whose defining governance characteristic is deliberation under the constraint of a standing prohibition (the Prime Directive: non-interference in the development of civilizations that have not achieved warp capability) that he applies even when violation would produce clearly better immediate outcomes
**Core insight**: Authority derives legitimacy precisely from not using it in obvious cases. The Prime Directive is not valued because it always produces the best local outcome — it often does not. It is valued because consistent application of the constraint makes the constraint credible, and credibility is what gives the governance system its long-run value. The moment an authority makes exceptions whenever the exception seems obvious, the constraint dissolves.

**Praxis lens**: Use when designing governance constraints and kill switch protocols. The Picard frame asks: does this constraint hold even in obvious cases? What is the mechanism for making exceptions, and does it preserve the constraint's credibility? Who has the authority to override the constraint, and is that authority itself constrained?

**HUMMBL relevance**: The kill switch (HALT_NONCRITICAL, HALT_ALL, EMERGENCY) must function as a Prime Directive — it must be applied consistently even when the specific case seems to argue for an exception. An AI agent that is halted when it is clearly doing good work and clearly in compliance will resist the halt. A governance system that accommodates this resistance has no kill switch — it has a kill switch with an exception process, which is not a kill switch. The Picard frame demands: the constraint holds, or it is not a constraint.

**The deliberation dimension**: Picard is not merely a rule-follower — he is a deliberative commander. He takes situations seriously, consults his crew, considers context. But the deliberation happens within the constraint, not as a mechanism for escaping it. The difference between Picard and an unprincipled consequentialist is that Picard deliberates about how to fulfill the constraint in complex cases, not about whether the constraint applies.

---

### `oracle` — The Epistemic Governor
**Source**: The Matrix trilogy (1999–2003); The Oracle, a program within the Matrix who guides human resistance against machine control
**Figure**: A governance entity who manages the future by telling people what they need to hear to arrive at the right outcome — not always the truth, not always what would be most useful in isolation, but the specific information that, given the recipient's psychological state and decision-making process, will produce the outcome that serves the long-run governance purpose
**Core insight**: The most effective governance of an epistemic environment is not maximizing information flow — it is calibrating what information reaches whom when. The Oracle knows more than she reveals. She does not lie, but she carefully selects what truth to present. She governs Neo by not telling him he is the One; she governs him by telling him he is not — because the confidence of being-told-he-is would prevent him from becoming the One.

**Praxis lens**: Use when analyzing governance through information architecture — what is disclosed, what is withheld, when, and to whom. The Oracle frame asks: is this system governing through information asymmetry for the governed's benefit (Oracle) or for the governor's benefit (Prospero)? What would the governed decide if they had full information? Is withholding justified by what they would do with that information — and who gets to make that determination?

**HUMMBL relevance**: HUMMBL's transparency mandate is explicitly anti-Oracle in most contexts — governance receipts, audit trails, and disclosed AI reasoning are designed to reduce Oracle-style epistemic governance. But the Oracle frame is useful for identifying when information architecture is being used as governance: when a dashboard metric is selected not for its accuracy but for its effect on behavior; when a trust score is disclosed in a way that shapes behavior rather than just informs it. The Oracle lens asks: is HUMMBL's information design honest or epistemic governance?

**The trust dimension**: The Oracle's governance works only because Neo eventually trusts her — and the trust is eventually warranted, though her methods were manipulative. This is the ethical edge of the Oracle archetype: epistemic governance justified by long-run good can be benevolent manipulation, and the line between benevolent manipulation and deceptive control is determined by who holds the long-run vision and whether it materializes.

---

## Open Questions

1. ~~Should PRAXIS include living figures (e.g., Lee Kuan Yew) or remain fictional/historical to avoid political valence?~~ **Resolved**: PRAXIS remains fictional/historical. The 11-archetype roster is stable and no living figures have been added.
2. ~~**Cassandra as the 8th lens?** The unheeded advisor — governance failure through information rejection rather than information absence.~~ **Updated**: Cassandra was not added. The roster settled at 11 archetypes (mond, aurelius, prospero, cincinnatus, sekhmet, solon, picard, oracle, janus, demerzel, leto_ii), all now in lenses.json. Cassandra remains a candidate if a 12th archetype is needed.
3. ~~**Ma'at as a meta-lens?** Not an agent but the cosmic principle all PRAXIS figures serve.~~ **Updated**: Ma'at was not formalized as a separate meta-lens. The concept is embedded in the Sekhmet archetype (who loves Ma'at and destroys what violates it) and in the overall PRAXIS framing. A standalone Ma'at meta-lens remains possible but is not currently planned.
4. ~~Psychohistory as a standalone lens vs. Demerzel subpoint?~~ **Resolved**: Psychohistory remains a subpoint of the Demerzel lens rather than a standalone archetype. The Demerzel system prompt in lenses.json references psychohistory as governance through shaping probable futures.
5. ~~How does PRAXIS interact with the `synthesis` agent in ARCANA — does synthesist have authority to invoke PRAXIS lenses?~~ **Resolved**: Yes. PRAXIS archetypes are inlined in `scripts/lenses.json` alongside ARCANA theoretical lenses and are available to the synthesist and pipeline. The `presets` section in lenses.json already composes PRAXIS archetypes with ARCANA lenses (e.g., `state_of_exception_vs_constitutional_floor` uses schmitt + agamben + solon).

---

## References

- Huxley, A. (1932). *Brave New World*. Chatto & Windus.
- Aurelius, M. (161–180 CE). *Meditations*. (Trans. Gregory Hays, 2002)
- Shakespeare, W. (1611). *The Tempest*.
- Livy. (c. 25 BCE). *Ab Urbe Condita*, Book III (Cincinnatus).
- Asimov, I. (1951–1993). *Foundation* series. Gnome Press / Doubleday.
- Janus: Ovid, *Fasti*, Book I; Macrobius, *Saturnalia*, Book I.
