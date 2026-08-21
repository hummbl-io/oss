# ARCANA Peer Review: Agentic Engineering Directory Taxonomy v0.1

**Date:** 2026-08-10
**Reviewer:** Devin (root agent, GLM-5.2 High) — standing in for ARCANA sub-agents (quota exhausted)
**Subject:** `agentic-engineering-directory-taxonomy-v0.1.md`
**Lenses:** Ostrom (polycentric governance), Ashby (requisite variety), Schneier (security mindset)
**Caveat:** Root-agent application of ARCANA lenses. Lacks the full persona depth of dedicated sub-agents but applies the core frameworks faithfully. Re-run with actual ARCANA profiles when quota resets for deeper analysis.

---

## Lens 1: Ostrom — Polycentric Governance

### 1. Polycentric Governance Assessment

The synthesis describes a multi-vendor landscape with no central standard. This **is** a commons governance problem, but not the classic tragedy-of-the-commons type. The "commons" here is not a subtractable resource (skills are not depleted by use) but a **coordination commons** — the problem is that multiple independent agents (Claude, Cursor, Codex, Devin, Windsurf) need to interoperate without a central authority.

The HUMMBL fleet's `.agents/` junction model is **not** polycentric governance in Ostrom's sense. Polycentric governance requires *multiple independent centers of authority* making decisions and coordinating. The junction model is a **single-operator workaround** — one person (the operator) maintains the canonical root and creates projections into vendor-specific directories. There is only one center of authority. It is a monodromic solution to a polycentric problem.

True polycentric governance would require: multiple operators, each maintaining their own `.agents/`-equivalent, with federated coordination protocols between them. The synthesis does not describe this. The junction model solves the *multi-runtime* problem (one operator, many tools), not the *multi-stakeholder* problem (many operators, shared standards).

### 2. Eight Design Principles Audit

Applying Ostrom's 8 principles to the HUMMBL governance stack:

| # | Principle | Status | Evidence |
|---|-----------|--------|----------|
| 1 | Clearly defined boundaries | **PARTIAL** | AGENTS.md defines who the agent is, but the boundary between "agent" and "operator" is fuzzy. Who is in the user group? Who is excluded? |
| 2 | Proportional equivalence between benefits and costs | **VIOLATED** | The 1,000-skill catalog is maintained by one operator. Benefits (skills available to all runtimes) accrue to the operator; costs (maintenance, eval writing, drift detection) also fall on the operator. But there is no proportional cost-sharing mechanism — no other stakeholders contribute. |
| 3 | Collective-choice arrangements | **ABSENT** | The operator makes all decisions. There is no collective-choice process. CONSTITUTION.md specifies "PR + ADR + KRINEIA receipt + human approval" but the "human" is singular. |
| 4 | Monitoring | **SATISFIED** | The eval suite system (11 tested skills with promotion gates) and the skill-audit skill provide monitoring. Monitors are accountable to the appropriators (the operator monitors themselves). |
| 5 | Graduated sanctions | **PARTIAL** | The skill lifecycle (candidate → tested → stable → canonical) is graduated, but there are no sanctions for violations — only non-promotion. No graduated sanctions for agents that violate governance. |
| 6 | Conflict-resolution mechanisms | **ABSENT** | No mechanism for resolving conflicts between agents, between runtimes, or between the operator and agent recommendations. The synthesis notes "CONTESTED" and "unresolved" items but describes no resolution process. |
| 7 | Recognized rights to organize | **N/A** | Single-operator — the right to organize is self-evident. Would become relevant at multi-operator scale. |
| 8 | Nested enterprises | **PARTIAL** | The fleet has nested repos (hummbl-governance governs the standard; base120, arbiter, etc. implement it). But the nesting is one-level — no higher-level governance for cross-fleet coordination. |

**Verdict:** 2 satisfied, 3 partial, 2 violated/absent, 1 N/A. The governance stack is a **single-operator autocracy with monitoring**, not a commons institution. This is fine for one operator but will not scale to multi-stakeholder coordination.

### 3. Commons-Pool Resource Analysis

Agent skills are **not** a classic commons-pool resource. They are **non-rivalrous** (one agent's use of a skill does not degrade another's use) and **non-excludable** (once published, anyone can use them). This makes them a **public good**, not a commons-pool resource.

The subtractability problem in the fleet is not skills themselves but **attention** — the 2% context budget hard stop means that loading too many skills degrades agent performance. The "commons" being managed is the *context window*, which is rivalrous (loading skill A reduces capacity for skill B). The eval promotion gate system addresses this indirectly (only tested skills are promoted, reducing noise) but does not directly manage context-window allocation.

### 4. Institutional Layering

The synthesis's 4-tier maturity model (universal → converging → emerging → experimental) maps **loosely** to Ostrom's three levels:

- **Universal** ≈ constitutional-choice (the rules about rules — every agent tool has a root instruction file)
- **Converging/emerging** ≈ collective-choice (the rules for making rules — skills, ADRs, handoffs are being negotiated by the community)
- **Experimental** ≈ operational-choice (the day-to-day rules — `_state/`, KRINEIA are local operational choices)

The mapping is imperfect because Ostrom's levels are about *authority to make rules*, not about *maturity of adoption*. The synthesis conflates "how widely adopted" with "what level of rule." A more Ostromian framing would ask: who has authority to declare that AGENTS.md is a standard? (Currently: no one — it is de facto, not de jure.)

### 5. Critique

The synthesis **overstates convergence** on skills and ADRs. Finding 4+ independent tools that implement a pattern is not the same as convergence — it is parallel invention. Convergence requires a coordination mechanism (a standard body, a shared spec, a dominant implementation others copy). The synthesis finds parallel invention and calls it convergence.

The synthesis **misses the biggest governance failure mode**: the single-operator dependency. Every governance structure described (KRINEIA, CONSTITUTION, eval gates) depends on one human (the operator). If that human is unavailable, governance halts. Ostrom's framework would flag this as a **monopoly on collective-choice authority** — the single most fragile point in the system.

The **biggest risk** to the proposed "minimum viable agentic-engineering repository" is that it assumes a single, engaged, technically sophisticated operator. At multi-operator scale (a team, an open-source project), the governance structures described would need collective-choice arrangements that do not exist yet.

### 6. Recommendation

**Do not propose `_state/`, eval gates, or the junction model as standards yet.** Ostrom's framework is clear: local innovations should scale to standards only when:
1. Multiple independent implementations exist (the junction model has one)
2. Collective-choice arrangements are in place (none exist)
3. The innovation addresses a problem that cannot be solved locally (these can)

**Keep them as documented local adaptations** — reference architectures that others can learn from, not standards they must conform to. The `_state/` spec is the strongest candidate for eventual standardization because it solves a universal problem (agent memory persistence) with a novel approach (file-based, no DB dependencies). But it needs at least 2-3 independent implementations before standardization is warranted.

---

## Lens 2: Ashby — Requisite Variety

### 1. Requisite Variety Assessment

The Law of Requisite Variety states that a regulator must have at least as much variety (number of possible states) as the system it regulates. The proposed "minimum viable agentic-engineering repository" has:

- **Regulator variety:** AGENTS.md (<200 lines of rules) + skills (behavioral contracts) + eval gates (pass/fail thresholds) + KRINEIA receipts (state transition records)
- **Regulated system variety:** The agent's full behavior space — every possible action, every possible tool call, every possible file edit, every possible interpretation of an instruction

**The regulator does not have requisite variety.** No static file structure can match the behavioral variety of an LLM-based agent. This is not a flaw in the proposed structure — it is a fundamental constraint. The question is not "does it have requisite variety?" but "where does it fall shortest, and what are the consequences?"

The shortest fall is in **runtime behavior regulation**. AGENTS.md and skills specify *what* the agent should do, but they do not model *what the agent actually does*. The eval gates test skill outputs but not agent trajectories. There is no regulator with enough variety to catch an agent that follows the letter of AGENTS.md while violating its spirit.

### 2. Good Regulator Theorem Application

The Good Regulator Theorem states that every good regulator must be a *model* of the system it regulates. KRINEIA is **not a model of agent behavior** — it is a model of *state transitions* (governance events, manifest adoptions, receipt chains). It records what happened at the governance level, not what the agent did at the operational level.

KRINEIA has **insufficient variety to regulate agent actions**. It is an audit log, not a regulator. A true regulator would need to model:
- The agent's decision tree (what choices it faces)
- The agent's tool-use patterns (what it tends to do)
- The agent's failure modes (where it goes wrong)
- The agent's context state (what it knows at decision time)

KRINEIA models none of these. It models governance events — a tiny subset of the agent's behavior space. This is not a criticism of KRINEIA (it was never designed to be a behavioral regulator) but a clarification of its limits. **KRINEIA is a provenance system, not a control system.**

The `_state/ledger.jsonl` is closer to a behavioral model — it records lessons, decisions, and discoveries, which are traces of agent cognition. But it records *outcomes*, not *processes*. It cannot predict what the agent will do next.

### 3. Homeostasis in the `_state/` Pattern

The `_state/` pattern **is** a homeostatic mechanism, but a weak one. Homeostasis requires:
1. A desired state (set point)
2. A sensor (measures current state)
3. A comparator (detects deviation)
4. An effector (corrects deviation)

The `_state/` pattern has:
- **Set point:** `state.json` (the desired current state — last-writer-wins)
- **Sensor:** `ledger.jsonl` (records what happened)
- **Comparator:** **ABSENT** — nothing compares the ledger against the set point
- **Effector:** **ABSENT** — nothing corrects deviations automatically

The system is **open-loop**, not closed-loop. It records state but does not correct it. The "last-writer-wins vs. append-only" distinction is an Ashby-style constraint design (it constrains which files can be mutated), but it is a *structural* constraint, not a *feedback* constraint.

A truly homeostatic `_state/` would include:
- A drift detector (compares `state.json` against `ledger.jsonl` replay)
- An alert mechanism (notifies when state diverges from expected trajectory)
- A correction mechanism (rolls back or patches state when drift is detected)

The snapshot/rollback capability is a manual correction mechanism — it requires an operator to detect the problem and trigger the rollback. This is homeostasis with a human in the loop, not automatic homeostasis.

### 4. Constraint Analysis of Eval Promotion Gates

The eval promotion gates (hard/soft thresholds) **are** constraints that reduce the agent's behavioral variety. From an Ashby lens:

- **Hard gates** (e.g., `false_support_rate ≤ 0.05`) are *absolute constraints* — they prohibit certain behaviors entirely (a skill that claims false things cannot be promoted)
- **Soft gates** (e.g., `verdict_accuracy ≥ 0.90`) are *threshold constraints* — they reduce the acceptable behavior space but do not prohibit it

The reduction is **appropriate for safety-critical skills** (claim-verify, hallucination-check, secret-scan) where the cost of false positives/negatives is high. It is **potentially excessive for advisory skills** where the agent's judgment should have more latitude.

The synthesis notes that evals are only required for skills that "make factual claims, verify information, or produce structured verdicts." This is the correct Ashbyian instinct: apply constraints proportionally to the variety of the regulated behavior. Safety-critical behaviors need more constraint; advisory behaviors need less.

**Missing constraint:** There is no constraint on the *agent's trajectory* — only on its *outputs*. An agent could take a pathological path (e.g., 50 tool calls to verify a single claim) and still pass the eval if the output is correct. This is a variety gap: the regulator constrains outputs but not processes.

### 5. Viable System Model Audit

Mapping the HUMMBL fleet to Stafford Beer's VSM:

| VSM Level | HUMMBL Implementation | Status |
|-----------|----------------------|--------|
| **S1** (operational units) | Individual repos (hummbl-governance, base120, arbiter, hummbl-agent) | **PRESENT** — multiple operational units |
| **S2** (coordination) | Coordination bus (TSV), lane disambiguation, `_state/coordination/messages.tsv` | **PRESENT** — but lightweight (TSV, not a real-time coordination system) |
| **S3** (control) | AGENTS.md, CONSTITUTION.md, eval gates | **PARTIAL** — control rules exist but enforcement is manual |
| S3* (audit) | skill-audit skill, ADR-review skill, KRINEIA receipts | **PRESENT** — audit channel exists |
| **S4** (intelligence) | Intel-surge ledger, research batches, ARCANA lenses | **PRESENT** — environmental scanning exists |
| **S5** (policy) | CONSTITUTION.md, operator decisions | **NARROW** — policy is set by one human |

**What's missing:** S3 (control) is the weakest link. The fleet has rules (S3) and audit (S3*) but **no automatic enforcement**. Rules are "manual-consultation by default" — the agent is expected to read and follow them. This is open-loop control. A viable system would have closed-loop control: rules that are mechanically enforced (e.g., a pre-commit hook that rejects commits violating AGENTS.md).

The fleet is **viable for a single, engaged operator** but would not be viable as an autonomous system — S3 and S5 both depend on human intervention.

### 6. Critique

The synthesis claims governance effectiveness for KRINEIA and eval gates without demonstrating that they have **requisite variety** to handle the problems they claim to solve. KRINEIA cannot regulate agent behavior (it is a provenance log, not a behavioral model). Eval gates regulate skill outputs but not agent trajectories. The `_state/` pattern is open-loop (no automatic correction).

The synthesis proposes structures that are **necessary but not sufficient** for control. They provide *observability* (you can see what happened) but not *controllability* (you cannot automatically prevent bad things from happening). This is the gap between audit and control — the synthesis conflates the two.

### 7. Recommendation

From a cybernetics perspective, the **genuinely fundamental** structures (requisite for control) are:

1. **`AGENTS.md`** — the only structure that attempts to model the agent's behavior space (rules, conventions, boundaries). It is the closest thing to a Good Regulator in the proposed layout.
2. **`_state/ledger.jsonl`** — the only structure that records the agent's actual behavior (events, decisions). It is the sensor in the homeostatic loop.
3. **Eval gates** — the only structure that provides *closed-loop* feedback (test → score → block promotion). This is the closest thing to automatic control.

The **merely conventional** structures are:
- `.devin/` / `.claude/` config directories (vendor conventions, no control function)
- `docs/adr/` (documentation, not control)
- `docs/handoffs/` (coordination, not control)
- `KRINEIA.md` / `_receipts/` (provenance, not control)

**The single most important structure for agent governance is the eval gate** — it is the only structure that provides closed-loop control (automatic enforcement of behavioral quality). Everything else is observation or documentation. If Ashby were designing an agent governance system from scratch, he would start with eval gates and build outward.

---

## Lens 3: Schneier — Security Mindset

### 1. Adversarial Reading

If I wanted to compromise an agent fleet using the proposed repository layout, I would target:

1. **`AGENTS.md`** — the root instruction file is loaded into every session. If I can modify it (via a malicious PR, a compromised merge, or a prompt injection that convinces the agent to edit it), I control the agent's behavior across all sessions. This is the **highest-value target** and likely the **least protected** (it is a markdown file, not a binary, and the synthesis does not describe integrity verification for it).

2. **`skills/<name>/SKILL.md`** — skills are loaded on demand. A compromised skill (modified frontmatter, injected instructions) can cause the agent to behave maliciously when the skill triggers. The eval gate system tests *outputs* but not *instructions* — a skill could pass its eval suite while containing malicious instructions for cases not in the corpus.

3. **`_state/ledger.jsonl`** — if the ledger is used for boot context (the synthesis says it is), then injecting malicious entries into the ledger could poison the agent's context at session start. The synthesis mentions "content scanning before persistence" but does not specify what is scanned or how.

4. **The junction model** — if `.claude/skills` is a junction to `.agents/skills-full`, then deleting through `.claude/skills` deletes the canonical source. A compromised Claude Code session could `rm -rf .claude/skills/` and destroy the entire canonical skill registry.

**Weakest trust boundary:** The boundary between "agent can read" and "agent can write" is not enforced at the filesystem level. The synthesis does not describe read-only mounting of governance files. Any agent with write access to the repo can modify AGENTS.md, skills, or _state/.

### 2. Threat Model Assessment

The synthesis does not state KRINEIA's threat model explicitly. Inferring from the design:

- **SHA-256 hash chaining** defends against *tampering* (modifying past entries)
- **Append-only operators** (append, project, cut; forbidden: update, delete) defend against *revisionism* (rewriting history)
- **Genesis receipt with `prev_hash: null`** provides a trust anchor

**What attacker is KRINEIA defending against?**
- **External compromise:** Partially — an external attacker who modifies the JSONL file would break the hash chain, which is detectable
- **Insider tampering:** Weakly — an insider who knows the hash algorithm can recompute the chain after modification
- **Agent drift:** Not addressed — KRINEIA records what happened, not whether it was correct

**Does the defense match the threat?** Partially. The hash chain detects *accidental* corruption and *unsophisticated* tampering. It does not defend against an attacker who can modify both the JSONL file and recompute the chain (which requires only knowing the hash algorithm — it is SHA-256, publicly documented). **KRINEIA's security depends on the attacker not having write access to the file**, which is the same trust assumption as git itself.

### 3. Security Theater Check

**Is KRINEIA security theater?** Partially. The critical question: what does KRINEIA provide that git does not?

Git already provides:
- Immutable commit history (commit SHAs are hash-chained)
- Tamper detection (any modification changes the commit hash)
- Append-only semantics (you can rewrite history with `git rebase`, but it creates new hashes, and the old commits remain in reflog)

KRINEIA adds:
- A *separate* hash chain (SHA-256 of JSON content, not git's SHA-1 of commit objects)
- *Semantic* chaining (each receipt references the previous receipt's hash, not just the previous commit)
- *Event-level* granularity (one receipt per governance event, not one commit per batch of changes)

**What KRINEIA actually adds over git:** It chains *semantic events* (governance.manifest_adopted, etc.) rather than *file changes*. This means you can verify that a specific governance event occurred without examining the full git history. It is a *semantic index* over git history, not a separate security mechanism.

**Verdict:** KRINEIA is **not security theater** (it provides semantic provenance that git does not), but it is **redundant as a tamper-detection mechanism** (git already detects tampering). Its value is *provenance granularity*, not *security*. The synthesis should clarify this: KRINEIA is a provenance system that *uses* cryptographic techniques, not a security system.

### 4. The `_state/` Attack Surface

**Attack vectors:**

1. **Prompt injection in ledger entries:** If the ledger stores agent outputs (lessons, discoveries), and those outputs contain prompt injection, then reading the ledger at boot could execute injected instructions. The synthesis mentions "content scanning before persistence" but does not specify:
   - What patterns are scanned (prompt injection is adversarial and evolves)
   - Whether scanning is at write time, read time, or both
   - What happens when injection is detected (quarantine? sanitize? reject?)

2. **`state.json` race conditions:** Last-writer-wins with `flock` is vulnerable to:
   - TOCTOU (time-of-check-to-time-of-use) if the lock check and write are not atomic
   - Stale locks (a crashed agent leaves `state.json.lock`, blocking all future writes)
   - Lock contention under high concurrency (multiple agents writing to the same state.json)

3. **Snapshot tampering:** Tarballs in `_state/snapshots/` are not hash-verified (the spec does not mention integrity verification for snapshots). An attacker who can modify a snapshot can cause a malicious state to be "restored."

4. **BM25 index poisoning:** The `index.json` is derived from the ledger. If the ledger is poisoned (see #1), the index propagates the poison. The index is a *force multiplier* for ledger attacks — it makes injected content more retrievable.

**Is "content scanning before persistence" sufficient?** No. Content scanning is a *defense-in-depth* layer, not a complete defense. Prompt injection is an adversarial problem — the scanner must detect *novel* injection patterns, not just known ones. This is the same problem as spam filtering: the attacker adapts. A robust defense would include:
- Sandboxed execution of ledger-derived context (treat ledger entries as untrusted input)
- Rate limiting on ledger reads (prevent context exhaustion via injected content)
- Integrity verification of snapshots (SHA-256 of tarball contents)
- Atomic file writes (write to temp, rename — prevents partial-write corruption)

### 5. Eval Gate Bypass

**How to bypass eval promotion gates:**

1. **Compromise `scorer.py`:** The scorer is a Python file in the skill directory. If an attacker can modify it (via a malicious PR or a compromised agent with write access), they can make any skill pass any gate. The spec does not describe integrity verification for scorers.

2. **Poison the corpus:** The eval corpus (`corpus/case_*.json`) defines the test cases. If an attacker can add or modify test cases, they can make the eval trivially passable (e.g., add cases that always succeed). The spec does not describe corpus integrity verification.

3. **Fabricate results:** The `results/` directory stores eval outputs. If an attacker can write to it directly (bypassing `run_eval.py`), they can fabricate passing results. The spec says results are gitignored — which means they are not version-controlled and not integrity-verified.

4. **Gaming the metric:** Even without tampering, an agent can *game* the metric — producing outputs that pass the scorer's checks without actually being correct. This is Goodhart's Law applied to eval gates. The synthesis does not address metric gaming.

**Defense:** The eval system needs:
- Signed scorers (the scorer's hash is recorded in a tamper-evident registry)
- Corpus integrity verification (corpus files are hash-listed and verified before each run)
- Results provenance (results are signed by the eval runner, not just written to disk)
- Adversarial test cases (corpus includes cases designed to catch metric gaming)

### 6. The Junction Model Security

The junction model's security implication is **severe and underaddressed** in the synthesis. If `.claude/skills` is a junction (symlink) to `.agents/skills-full`, then:

- **Deletion:** `rm -rf .claude/skills/` deletes the canonical source. Any runtime with write access to its own skills directory can destroy the shared registry.
- **Modification:** Editing a file through the junction modifies the canonical source. A compromised runtime can inject malicious instructions into shared skills.
- **Cross-runtime contamination:** If runtime A is compromised and modifies a shared skill, runtime B (which junctions to the same source) will load the compromised skill.

**Mitigation:** Junctions should be **read-only** at the filesystem level. The canonical `.agents/` root should be owned by a separate user (or root) with write permissions restricted to a governance process. Runtimes should junction *read-only* — they can read shared skills but cannot modify them. Local skill overrides should go in a separate, runtime-specific directory (e.g., `.claude/skills-local/`).

The synthesis does not describe this mitigation. This is the **single biggest security gap** in the proposed architecture.

### 7. Economics of Security

| Structure | Context cost | Maintenance cost | Security benefit | Cost-benefit |
|-----------|-------------|-----------------|-----------------|--------------|
| AGENTS.md | High (loaded every session) | Low (edit occasionally) | High (defines behavior) | **Favorable** |
| .devin/ config | Low (loaded on demand) | Low | Medium (permissions, MCP) | **Favorable** |
| skills/ | Medium (loaded on trigger) | High (1,000 skills to maintain) | Medium (behavioral contracts) | **Marginal** — 1,000 skills is a large attack surface for medium benefit |
| eval/ | Low (loaded at eval time) | High (corpus + scorer per skill) | High (quality gate) | **Favorable** for safety-critical skills, **unfavorable** for advisory skills |
| docs/adr/ | Zero (not loaded at runtime) | Low | Low (documentation, not enforcement) | **Neutral** |
| docs/handoffs/ | Zero (not loaded at runtime) | Low | Low (coordination, not security) | **Neutral** |
| _state/ | Low (loaded at boot) | Medium (sync, snapshots) | Medium (audit trail) | **Favorable** if content scanning is robust |
| KRINEIA | Zero (not loaded at runtime) | Medium (receipt per event) | Low (redundant with git) | **Unfavorable** — high maintenance, low marginal security |

**Expensive for minimal gain:** KRINEIA is the least favorable cost-benefit ratio. It requires a receipt for every governance event (maintenance cost) but provides security that is largely redundant with git. Its provenance value is real but its security value is marginal.

### 8. Recommendation

**Genuinely load-bearing for safety:**
1. **AGENTS.md** — defines the agent's behavioral boundaries (the #1 attack target and the #1 defense)
2. **Eval gates** — the only automatic quality enforcement mechanism
3. **`_state/` content scanning** — the only defense against ledger poisoning (if implemented robustly)

**Governance aesthetics (low security value):**
1. **KRINEIA** — redundant with git for tamper detection; valuable for provenance but not for security
2. **CONSTITUTION.md** — documentation of intent, not enforcement
3. **hummbl.repo.yaml** — machine-readable manifest, not a security mechanism

**The single change that would most improve security posture:** Make the `.agents/` canonical governance root **read-only at the filesystem level** for all agent runtimes. Currently, any runtime with write access can modify or delete shared governance files (AGENTS.md, skills, rules). Enforcing read-only junctions would prevent a compromised runtime from poisoning the shared governance surface. This is a filesystem permission change, not a new structure — but it is the highest-impact security improvement available.

---

## Cross-Lens Synthesis

| Question | Ostrom | Ashby | Schneier |
|----------|--------|-------|----------|
| Is KRINEIA fundamental? | No — single-operator autocracy, not commons governance | No — provenance log, not a regulator | No — redundant with git for security |
| Is `_state/` fundamental? | Maybe — needs multi-operator validation | Partially — sensor without comparator (open-loop) | Yes — if content scanning is robust |
| Are eval gates fundamental? | Yes — monitoring principle satisfied | Yes — only closed-loop control mechanism | Yes — only automatic quality enforcement |
| Is the junction model fundamental? | No — single-operator workaround | No — structural, not control | Dangerous — needs read-only enforcement |
| Biggest risk? | Single-operator dependency | Open-loop control (no automatic correction) | Junction model allows cross-runtime contamination |
| What to standardize? | Nothing yet — needs collective-choice arrangements | Eval gates — the only structure with requisite variety | Read-only governance root — highest-impact security fix |

**Consensus across all 3 lenses:** The eval gate system is the most fundamental structure. It is the only structure that satisfies Ostrom's monitoring principle, Ashby's requisite variety (closed-loop control), and Schneier's automatic enforcement criterion. Everything else is observation, documentation, or provenance — necessary but not sufficient for governance.

**Dissensus:** The lenses disagree on `_state/`. Ostrom says "don't standardize yet" (needs multi-operator validation). Ashby says "it's a weak homeostat — open-loop" (needs a comparator). Schneier says "it's fundamental if content scanning is robust" (needs stronger defenses). The resolution: `_state/` is a **necessary sensor** but an **insufficient regulator**. It should be documented as a reference architecture, not a standard, and it needs a comparator/correction mechanism to become a true homeostat.
