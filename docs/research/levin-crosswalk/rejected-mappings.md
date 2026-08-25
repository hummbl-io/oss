# Rejected Mappings

Mappings considered and explicitly rejected, with reasons. Each rejection
documents the temptation, the reason it fails, and what would be needed to
reconsider.

---

## RM-001 — "Cognitive light cone" -> "Context Windowing (P10)" as a MATCH

- **Temptation:** Both define the bounded set of variables an agent can
  reason about. Both are about scope boundaries.
- **Why rejected:** Levin's cognitive light cone includes a moral-variable
  dimension (moral variables the agent can represent and protect). P10 has no
  moral dimension — it is a pure framing/boundary tool. A MATCH would
  silently drop the moral dimension, misrepresenting Levin's construct.
- **Disposition used instead:** `PARTIAL_MATCH` (CW-002).
- **What would change this:** If HUMMBL adds a moral-scope field to
  delegation or context windowing, this mapping could be reconsidered as a
  PARTIAL_MATCH with a smaller non-equivalence gap. It would still not be a
  MATCH unless HUMMBL explicitly claims agents represent moral variables.

---

## RM-002 — "Persuadability spectrum" -> "Kill Switch mode ladder" as a MATCH

- **Temptation:** Both are invasiveness spectra from least to most
  destructive. Both escalate from gentle intervention to force.
- **Why rejected:** Levin's persuadability is a property of the system being
  intervened upon (can this system be persuaded?). The kill-switch mode
  ladder is a property of the intervener (what mode am I switching to?).
  These are different axes. A MATCH would conflate system property with
  intervention property.
- **Disposition used instead:** `PARTIAL_MATCH` (CW-008), with the
  "persuadability as system property" framing flagged as a candidate.
- **What would change this:** If HUMMBL adds an "agent persuadability
  assessment" (can this agent's behavior be changed without restart?), the
  mapping could be reconsidered. It would still face the biological-vs-
  engineering substrate difference.

---

## RM-003 — "Basal cognition" -> "Base120 reasoning operators" as a STRUCTURAL_ANALOGY

- **Temptation:** Both describe cognitive processes in non-standard systems.
  Base120 gives reasoning operators to agents; basal cognition finds
  cognition in cells.
- **Why rejected:** Base120 is a prescriptive tool — agents use the operators
  because they are programmed to. Basal cognition is a descriptive claim —
  cells exhibit cognitive behavior without being programmed to. Calling this
  a structural analogy would imply Base120 is a model of basal cognition,
  which it is not. Base120 is a reasoning library, not a cognitive
  architecture.
- **Disposition used instead:** `NO_EQUIVALENT` (CW-003).
- **What would change this:** Nothing in HUMMBL's current scope. HUMMBL would
  need to make claims about inherent cognitive capacity of substrates, which
  it does not and should not.

---

## RM-004 — "Disease as altered scope" -> "Circuit Breaker OPEN state" as a PARTIAL_MATCH

- **Temptation:** Both describe a state where normal governance has broken
  down and the system is in a degraded/isolated mode.
- **Why rejected:** Circuit Breaker OPEN is a protective, intentional state
  — the system is isolated to prevent cascading failure. Disease (in Levin's
  framing) is a pathological, unintentional state — the system has lost its
  governance, not deliberately suspended it. Calling this a partial match
  would conflate protective isolation with pathological breakdown.
- **Disposition used instead:** `STRUCTURAL_ANALOGY` (CW-009), with explicit
  rejection of the disease framing for HUMMBL agents.
- **What would change this:** Nothing. The protective-vs-pathological
  distinction is fundamental and cannot be bridged.

---

## RM-005 — "Novel synthetic beings" -> "Agent admission" as a PARTIAL_MATCH

- **Temptation:** Both address the problem of governing agents whose nature
  is not fully known. Both require boundary-setting before interaction.
- **Why rejected:** Levin's "novel beings" carries moral-status implications
  (how should we treat this being?). HUMMBL's agent admission is an
  authority-scope decision (what is this agent allowed to do?). These are
  different questions. A PARTIAL_MATCH would imply HUMMBL addresses moral
  status, which it does not.
- **Disposition used instead:** `STRUCTURAL_ANALOGY` (CW-010), with explicit
  scoping away from moral-status claims.
- **What would change this:** If HUMMBL explicitly extends its scope to
  include moral-status reasoning (which would be a major scope change
  requiring operator approval), this could be reconsidered. The crosswalk
  recommends against such a scope extension.

---

## RM-006 — "TAME" -> "Base120" as a STRUCTURAL_ANALOGY

- **Temptation:** Both are frameworks that systematically describe diverse
  agents using structured taxonomies.
- **Why rejected:** TAME is a descriptive scientific framework for
  understanding diverse minds. Base120 is a prescriptive engineering toolkit
  for agent reasoning. Calling this a structural analogy would imply Base120
  is a software implementation of TAME, which it is not. The relationship is
  terminological (both use "mind/mental" language) not structural.
- **Disposition used instead:** `TERMINOLOGY_COLLISION` (CW-012).
- **What would change this:** Nothing. The frameworks serve different
  purposes and should be explicitly distinguished, not analogized.
