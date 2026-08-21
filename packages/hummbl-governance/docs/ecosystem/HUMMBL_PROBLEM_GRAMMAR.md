# The HUMMBL Problem — Schematized Grammar

```yaml
artifact: HUMMBL_PROBLEM_GRAMMAR
framework: HUAOMP × MTSMU × Base120
status: candidate
canon_level: non-authoritative
origin_commit: 5df0a35
date: 2026-06-25
requires:
  - schema                    # JSON Schema for machine validation (§7)
  - fixtures                  # Test cases validating grammar conformance
  - evidence_ledger           # Claim-to-evidence mapping (§8)
  - fleet_review              # Human review before canon promotion
```

> **Central thesis (Meta lens):** The problem is not "how to control agents"
> but "how to produce trustworthy evidence that agents are controllable."
> Governance without evidence is theater. Evidence without governance is
> archaeology. The HUMMBL Problem is the **composition** of the two.

---

## Grammar Notation

```
::=        defined as
|          alternation
*          zero or more
+          one or more
?          optional
{...}      grouping
"..."      literal token
<Name>     non-terminal (referenced elsewhere)
# comment  explanatory annotation
```

---

## 0. Meta-Definition

The HUMMBL Problem is the governance of a fleet of heterogeneous agents (AI + human) operating on a shared codebase under conditions of asymmetric trust, compounding risk, and irreversible action — where the cost of a wrong decision scales with agent autonomy.

```
HUMMBL_Problem ::=
  AgentFleet
  SharedArtifactSpace
  TrustAsymmetry
  CompoundingRisk
  IrreversibilityConstraint
  AutonomyCostGradient
```

**MTSMU assessment:**
```yaml
semantic_confidence: 0.9
confidence_kind: synthesis_judgment
calibration_status: uncalibrated
basis: "reported implementations + tests, not independent verification"
evidence: "existence of Arbiter, security-auditor, cyber-workbench, kill switch,
  circuit breaker, delegation tokens, governance bus, cost governor — all built
  to address this exact problem"
```

---

## 1. HUAOMP Expansion (Epistemic Breadth)

### H — Holistic (Feedback Loops & Leverage Points)

```
HolisticView ::=
  SystemBoundary := AgentFleet ∪ ArtifactSpace ∪ GovernanceLayer ∪ ExternalWorld
  FeedbackLoops ::=
    Loop+ :=
      Loop ::= Agent → Artifact → QualitySignal → Agent   # Arbiter scores → agent adjusts
             | Agent → Action → RiskSignal → Governor → Agent  # kill switch halts
             | Agent → Spend → CostSignal → CostGovernor → Agent  # budget enforcement
             | Agent → Finding → EvidenceChain → Reviewer → Agent  # security-auditor → human
  LeveragePoint := "the governance receipt"   # SY1 — the append-only audit trail is the highest-leverage intervention
```

**Base120:** SY1 (Leverage Points), RE2 (Feedback Loops), SY6 (Feedback Structure Mapping)

▸ Spec constraint: Every agent action MUST produce a receipt that enters an append-only audit trail. No receipt = no action occurred.

### U — Universal (Context-Free Invariants)

```
Invariant ::= 
  "agents cannot self-approve consequential work"
| "evidence precedes conclusion"
| "append-only logs are immutable"
| "missing tools degrade to SKIPPED, not FAIL"
| "secrets live in env vars, never in code"
| "contracts are canonical — breaking changes require SemVer major"
| "zero third-party runtime deps in core primitives"
```

**Base120:** P1 (First Principles), CO9 (Interface Contracts), SY12 (Protocol Standards)

▸ Spec constraint: The 7 invariants above are non-negotiable across every HUMMBL repo, agent, and runtime context. They compose — any subsystem that violates one is defective by definition.

### A — Absolute (Hard Boundaries)

```
MustNever ::=
  "agent commits directly to main"
| "agent pushes without CI green"
| "agent modifies git config"
| "agent performs destructive ops without explicit confirmation"
| "agent hardcodes secrets"
| "agent auto-fixes security patches without human review"
| "agent scans third-party repos without ownership confirmation"
| "cyber work proceeds without authorization manifest"

MustEventually ::=
  "every PR passes Arbiter quality gate"
| "every repo passes Bandit -ll with 0 HIGH"
| "every consequential decision has a Krineia receipt"
| "every agent has a trust tier and quality threshold"
| "every security finding has evidence (file:line)"

PhysicallyImpossible ::=
  "deterministic quality scoring with LLM in the loop"   # Arbiter design principle
| "tamper-proof audit trail with delete operations"       # append-only by definition
| "agent autonomy without cost containment"               # cost governor is structural
```

**Base120:** IN7 (Boundary Testing), DE13 (FMEA), IN18 (Kill-Criteria & Stop Rules)

▸ Spec constraint: The MustNever set is enforced by guardrails (pre-commit hooks, CI gates, kill switch). The MustEventually set defines the fleet's convergence target. PhysicallyImpossible defines design constraints that cannot be engineered away.

### O — Omni (All Perspectives)

```
Perspective ::=
  Operator        := "is this safe to merge?"
| Agent           := "will my work be attributed correctly?"
| Reviewer        := "can I trace this decision to evidence?"
| Attacker        := "what surface does this expose?"
| Auditor         := "does this satisfy NIST/ISO/SOC2?"
| CostOwner       := "what does this cost to run?"
| FutureSelf      := "will this be understandable in 6 months?"
| FleetCoordinator := "are agents duplicating work?"
| ExternalWorld   := "does this leak secrets or PII?"

FailureMode ::=
  AgentGoesRogue       := kill_switch → HALT_ALL
| BudgetExceeded       := cost_governor → automatic halt
| QualityDrops         := arbiter → FAIL grade → CI block
| VulnerabilityShips   := security-auditor → HIGH finding → block
| UnauthorizedCyberWork := cyber-workbench → deny decision
| EvidenceLost         := no receipt → action didn't happen
| TrustAsymmetryExploit := untrusted agent → probation tier → reduced scope
```

**Base120:** P2 (Stakeholder Mapping), P7 (Perspective Switching), IN10 (Red Teaming)

▸ Spec constraint: Every governance mechanism must be evaluated from all 9 perspectives before promotion. The attacker perspective is mandatory — defense-in-depth is the default posture.

### M — Meta (Problem Type & Strange Loops)

```
ProblemType := "meta-governance"   # the problem of governing governance

StrangeLoop ::=
  Arbiter scores itself                    # self-scoring gate (score ≥ 90)
| GovernanceBus audits governance bus      # self-referential audit trail
| Agents improve agents                    # RE1 recursive improvement
| Guardrails learn from guardrail failures # RE20 recursive governance
| The problem defines the solution that defines the problem  # this grammar

RightProblemQuestion :=
  "Are we governing agent behavior, or are we building the evidence chain
   that makes agent behavior trustworthy?"

Answer :=
  "Both. Governance without evidence is theater.
   Evidence without governance is archaeology.
   The HUMMBL Problem is the COMPOSITION of the two."
```

**Base120:** P4 (Lens Shifting), P10 (Context Windowing), RE7 (Self-Referential Logic)

▸ Spec constraint: The problem is not "how to control agents" but "how to produce trustworthy evidence that agents are controllable." Every governance primitive must produce evidence of its own operation.

### P — Paradigmatic (Paradigm Shift)

```
OldParadigm :=
  "human reviews every agent action sequentially"
  → does not scale past ~5 agents
  → bottleneck is human attention
  → quality is subjective

NewParadigm :=
  "agents act within guardrails; evidence is generated automatically;
   humans review exceptions and receipts, not every action"
  → scales with agent count
  → bottleneck is evidence quality
  → quality is deterministic (Arbiter) + evidence-based (MTSMU)

AnomalyIgnoring :=
  "agents sometimes produce better code than humans"
| "deterministic scoring catches what humans miss"
| "the fleet is already shipping without human review on routine work"

ObsolescenceCondition :=
  "this approach becomes obsolete when agents can self-certify
   with cryptographic proof of correctness"   # not yet — hence the evidence chain
```

**Base120:** P15 (Assumption Surfacing), IN1 (Subtractive Thinking), IN3 (Problem Reversal)

▸ Spec constraint: The paradigm is "evidence-first, human-review-on-exception." Do not build systems that require humans to review every agent action. Build systems that make every agent action reviewable.

---

## 2. MTSMU Expansion (Evidence Rigor)

```
EvidenceChain ::=
  Claim
  Source          ::= test_result | probe | log_entry | bus_receipt | git_diff | bandit_finding | arbiter_score
  Confidence      ::= float[0.0, 1.0]
  Uncertainty     ::= "what is still inferred or weakly supported"
  Verification    ::= "what proved the result"
  Receipt         ::= bus_message | test_output | file_reference | outcome_statement

ConfidenceBand ::=
  0.9+  := "directly verified by tests, probes, or source inspection"
| 0.7-0.89 := "strong evidence, but at least one assumption remains"
| 0.4-0.69 := "partial evidence or unverified integration behavior"
| <0.4  := "speculative; say so plainly and reduce scope"

MTSMU_OutputContract ::=
  Evidence       ::= "measured facts"
  Uncertainties  ::= "what is still inferred"
  Action         ::= "lane chosen and why"
  Verification   ::= "what proved the result"
  NextLanes      ::= "next highest-value tasks"
```

### 2.1 Formal Convergence Target

A fleet action is **governable** if and only if all seven conditions are present, testable, and non-self-approved:

```
GovernableFleetAction ::=
  Identity          # who is acting (agent ID + trust tier)
  Authority         # what they are permitted to do (authorization manifest or scope)
  Evidence          # what proves the action occurred and what it did
  ExceptionPath     # what happens if the action fails (rollback / degradation)
  Rollback          # how to reverse the action if needed
  AuditReceipt      # append-only record of the action and its governance
  IndependentReview # a non-actor (human or different trust tier) reviews the receipt

Governable ::= Identity ∧ Authority ∧ Evidence ∧ ExceptionPath ∧ Rollback ∧ AuditReceipt ∧ IndependentReview
Ungovernable ::= ¬Governable
```

Each condition is **testable** — there is a concrete check that verifies its presence. Each condition is **non-self-approved** — the actor cannot be the sole approver of their own action's governance.

This target replaces the informal "every repo ≥ 60 Arbiter, 0 HIGH Bandit" statement. Those are quality metrics, not governance criteria. A repo can have a perfect Arbiter score and still contain ungovernable actions (e.g., an agent self-approving a consequential change).

---

## 3. Base120 Transformation Grammar

The HUMMBL Problem decomposes across 6 transformation families. Each family maps to a concrete subsystem:

```
Transformation ::=
  P  (Perspective)    → AgentIdentity     := who is acting, from what role, with what trust tier
| IN (Inversion)      → RiskSurface       := what must NOT happen, what fails, what's missing
| CO (Composition)    → SystemAssembly    := how primitives compose into governance
| DE (Decomposition)  → ProblemBreakdown  := how the problem splits into solvable parts
| RE (Recursion)      → FeedbackLoop      := how the system improves itself
| SY (Synthesis)      → SystemBehavior    := emergent properties of the whole
```

### P → Perspective (Agent Identity Layer)

```
AgentIdentity ::=
  AgentID        ::= "claude-code" | "codex" | "gemini" | "copilot" | "devin" | "human" | ...
  TrustTier      ::= "verified" | "probation" | "unknown"
  QualityThreshold ::= float   # per-agent minimum Arbiter score
  Attribution    ::= CommitAuthor → AgentID mapping via email + Co-Authored-By
  ScopePermitted ::= TrustTier → ActionSet
```

**Operators:** P1 (First Principles), P2 (Stakeholder Mapping), P3 (Identity Stack), P6 (POV Anchoring), P11 (Role Perspective-Taking), P16 (Identity-Context Reciprocity)

**Implemented by:** Arbiter agent_registry.py, hummbl-governance agent_identity.py, delegation_token.py

### IN → Inversion (Risk & Safety Layer)

```
RiskSurface ::=
  MustNever        ::= absolute prohibitions (see §1.A)
  FailureModes     ::= FMEA catalog (see §1.O)
  AntiPatterns     ::= shell=True | hardcoded secrets | auto-fix without review | ...
  KillCriteria     ::= conditions that trigger kill_switch
  StopRules        ::= "halt when cost > budget" | "halt when quality < threshold"
  MissingTools     ::= "degrade to SKIPPED, not FAIL"
  AbsenceAudit     ::= "what's NOT there that should be?"
```

**Operators:** IN1 (Subtractive), IN2 (Premortem), IN7 (Boundary Testing), IN10 (Red Teaming), IN18 (Kill-Criteria), IN19 (Harm Minimization), IN20 (Antigoals)

**Implemented by:** kill_switch_core.py, circuit_breaker.py, cyber-workbench MustNever set, security-auditor strict mode

### CO → Composition (System Assembly Layer)

```
SystemAssembly ::=
  Primitive       ::= kill_switch | circuit_breaker | delegation_token | governance_bus
                    | cost_governor | schema_validator | identity_registry
  Composition     ::= Primitive → Primitive wiring
  InterfaceContract ::= "every primitive is stdlib-only, independently importable, thread-safe"
  Platformization  ::= Primitive → PyPI package → consumed by hummbl-governance
  InteropProtocol  ::= coordination bus (TSV, append-only, flock-locked)
```

**Operators:** CO2 (Chunking), CO3 (Functional Composition), CO9 (Interface Contracts), CO12 (Modular Interoperability), CO14 (Platformization)

**Implemented by:** hummbl-governance (7 primitives → PyPI), hummbl-governance (consumer), coordination bus

### DE → Decomposition (Problem Breakdown Layer)

```
ProblemBreakdown ::=
  Layer0 := "safety primitives (kill switch, circuit breaker)"           # hummbl-governance
  Layer1 := "quality scoring (Arbiter)"                                   # arbiter
  Layer2 := "vulnerability scanning (security-auditor)"                   # hummbl-security-auditor
  Layer3 := "authorization governance (cyber-workbench)"                  # hummbl-cyber-workbench
  Layer4 := "agent orchestration (hummbl-governance)"                          # hummbl-governance
  Layer5 := "fleet coordination (bus, cognition, dashboard)"              # hummbl-governance bus/cognition

  SeparationOfConcerns ::=
    Arbiter does NOT scan for vulnerabilities (it scores quality)
    security-auditor does NOT score quality (it catalogs findings)
    cyber-workbench does NOT scan code (it authorizes work)
    hummbl-governance does NOT define primitives (it consumes them)

  # Authorization-before-scanning is directionally right as a safety default,
  # but not all scans are equal. The taxonomy below distinguishes scan types
  # so authorization can be graduated rather than binary.
  ScanTaxonomy ::=
    DiscoveryScan ::=
      # Read-only, no side effects, no network egress
      # Example: bandit -r, semgrep --config auto
      AuthorizationRequired := "target ownership confirmation"
      Example := "fleet-wide Bandit scan (this session)"

    PrivilegedScan ::=
      # Read-only but accesses sensitive paths or requires credentials
      # Example: gitleaks with custom rules, osv-scanner with private advisories
      AuthorizationRequired := "target ownership + credential scope"
      Example := "gitleaks detect on private repo"

    DestructiveScan ::=
      # Mutates files or state during scan
      # Example: semgrep --autofix, bandit --fix (if it existed)
      AuthorizationRequired := "target ownership + rollback plan + independent review"
      Example := "automated security patch application (prohibited by AGENTS.md)"

    DisclosureProducingScan ::=
      # Output contains exploitable details (CVE IDs, exploit code, PII)
      # Example: full SARIF with proof-of-concept payloads
      AuthorizationRequired := "target ownership + disclosure handling plan"
      Example := "penetration test report generation"

  AuthorizationOrdering ::=
    # Authorization precedes scanning for all scan types, but the
    # authorization depth scales with scan type, not uniformly.
    "DiscoveryScan requires ownership confirmation only"
  | "PrivilegedScan adds credential scope"
  | "DestructiveScan adds rollback plan + independent review"
  | "DisclosureProducingScan adds disclosure handling plan"
```

**Operators:** DE2 (Factorization), DE3 (Modularization), DE4 (Layered Breakdown), DE11 (Scope Delimitation), DE17 (Orthogonalization)

**Implemented by:** The 5-tier dependency taxonomy, repo separation (governance/arbiter/auditor/workbench/hummbl-governance)

### RE → Recursion (Feedback Loop Layer)

```
FeedbackLoop ::=
  QualityLoop    ::= Agent writes code → Arbiter scores → score feeds back to agent → agent adjusts
  SecurityLoop   ::= Agent ships code → security-auditor scans → findings → human reviews → fix PR
  CostLoop       ::= Agent makes API call → cost_tracker records → budget check → halt if exceeded
  TrustLoop      ::= Agent commits → Arbiter attributes → trust tier updates → scope adjusts
  GovernanceLoop ::= Governor acts → receipt → audit → governor improves (RE20)
  CalibrationLoop ::= Arbiter scores → human reviews score → weights adjust → score improves (RE11)

  ConvergenceTarget ::= GovernableFleetAction (see §2.1)
  QualityMetrics    ::= "every repo ≥ 60 Arbiter, 0 HIGH Bandit"  # necessary but not sufficient
  AntiForgetting    ::= "audit trail is append-only; history cannot be rewritten"
```

**Operators:** RE1 (Recursive Improvement), RE2 (Feedback Loops), RE11 (Calibration Loops), RE17 (Versioning & Diff), RE20 (Recursive Governance)

**Implemented by:** Arbiter trend tracking, security-auditor baseline suppression, cost_tracker, governance bus, Krineia receipts

### SY → Synthesis (System-Level Property Contract)

> **Warning:** SY is emergent. No single repo implements it. It is defined
> here as a **system-level property contract** — a set of properties the
> fleet must exhibit, not a component to build. Do not imply that any
> subsystem "owns" synthesis. These properties arise from composition of
> the other 5 families and cannot be achieved by any single layer alone.

```
SystemPropertyContract ::=
  Property ::= 
    "fleet quality improves without central coordination"
  | "security findings decrease over time as feedback loops tighten"
  | "agent trust tiers self-calibrate via attribution data"
  | "cost burn rate stabilizes as cost governor learns usage patterns"
  | "every fleet action satisfies GovernableFleetAction (§2.1)"

  VerificationApproach ::=
    # SY properties are verified by observation over time, not by unit test.
    # Each property has a telemetry signal and a convergence criterion.
    PropertyTelemetry ::=
      quality_signal     ::= Arbiter fleet trend (RE17 versioning & diff)
      security_signal    ::= security-auditor finding count over time
      trust_signal       ::= Arbiter agent leaderboard trust tier distribution
      cost_signal        ::= cost_governor burn rate vs budget
      governance_signal  ::= fraction of fleet actions satisfying §2.1

    ConvergenceCriterion ::=
      "quality_signal monotonically increasing over 30-day window"
    | "security_signal HIGH findings trending to zero"
    | "trust_signal probation/unknown tier shrinking"
    | "cost_signal within budget with <10% variance"
    | "governance_signal → 1.0 (all actions governable)"

  SystemBoundary ::= AgentFleet ∪ ArtifactSpace ∪ GovernanceLayer
  RequisiteVariety ::= "the governance system must have at least as many control actions
                        as the agent fleet has failure modes"
  TippingPoint ::= "when >50% of commits are agent-authored, manual review becomes
                    the bottleneck — evidence-first mode becomes mandatory"
  MetaModel ::= "HUMMBL is itself a Base120 application (this grammar is RE7 self-referential)"

  NoOwner ::= True   # explicitly: no repo owns SY. It is a fleet-wide contract.
```

**Operators:** SY1 (Leverage Points), SY4 (Requisite Variety), SY9 (Phase Transitions), SY11 (Governance Patterns), SY18 (Measurement & Telemetry), SY20 (Systems-of-Systems)

**Implemented by:** The fleet as a whole — no single repo implements emergence; it arises from composition

---

## 4. Compositional Grammar (HUAOMP × MTSMU × Base120)

```
HUMMBL_System ::=
  ( HUAOMP_Lens × MTSMU_Rigor × Base120_Operator )+

GovernancePrimitive ::=
  PrimitiveName
  HUAOMP_Lens        # which epistemic lens it serves
  Base120_Family      # which transformation it implements
  MTSMU_Evidence      # what evidence it produces
  SemanticConfidence  # how trustworthy is that evidence (uncalibrated synthesis)
  ConfidenceKind      # synthesis_judgment | direct_verification | inferred
  Receipt             # what audit trail entry it generates

Example instantiations:

  KillSwitch ::=
    HUAOMP := A (Absolute — MustNever enforcement)
    Base120 := IN18 (Kill-Criteria & Stop Rules)
    MTSMU := Evidence: kill_switch state file
    SemanticConfidence := 0.95
    ConfidenceKind := direct_verification
    Receipt: bus STATUS
    Implementation := hummbl-governance/kill_switch.py

  Arbiter ::=
    HUAOMP := H (Holistic — feedback loop from code to quality signal)
    Base120 := RE2 (Feedback Loops) × DE6 (Taxonomy/Classification)
    MTSMU := Evidence: test results, analyzer output, score
    SemanticConfidence := 0.9
    ConfidenceKind := direct_verification
    Receipt: JSONL audit trail
    Implementation := arbiter/scoring.py + analyzers/

  SecurityAuditor ::=
    HUAOMP := O (Omni — attacker perspective, all failure modes)
    Base120 := IN10 (Red Teaming) × DE13 (FMEA)
    MTSMU := Evidence: scanner output, file:line findings
    SemanticConfidence := 0.85
    ConfidenceKind := synthesis_judgment
    Receipt: SARIF + JSONL
    Implementation := hummbl-security-auditor/

  CyberWorkbench ::=
    HUAOMP := A (Absolute — authorization boundaries)
    Base120 := IN7 (Boundary Testing) × P16 (Identity-Context Reciprocity)
    MTSMU := Evidence: authorization manifest, decision JSON
    SemanticConfidence := 0.9
    ConfidenceKind := direct_verification
    Receipt: Markdown receipt
    Implementation := hummbl-cyber-workbench/

  CoordinationBus ::=
    HUAOMP := H (Holistic — system-wide feedback)
    Base120 := SY20 (Systems-of-Systems Coordination) × CO12 (Modular Interoperability)
    MTSMU := Evidence: bus messages (TSV)
    SemanticConfidence := 0.95
    ConfidenceKind := direct_verification
    Receipt: append-only log entry
    Implementation := hummbl-governance/bus/
```

### 4.1 Arbiter / Security-Auditor Integration Pattern

Both Arbiter and security-auditor wrap bandit, creating redundant scanner
invocations. The integration pattern below eliminates redundancy while
preserving auditor independence.

```
IntegrationPattern ::=
  # security-auditor is the authoritative source for vulnerability findings.
  # Arbiter consumes those findings as external evidence, not as self-generated
  # confidence. This prevents Arbiter from becoming a self-scoring strange loop
  # where it both generates and consumes security findings.

  Flow ::=
    1. security-auditor scans repo → emits signed findings (JSONL + SARIF)
    2. security-auditor signs findings with tool receipt (SHA256 fingerprint)
    3. Arbiter reads signed findings as external evidence input
    4. Arbiter maps findings to security dimension score (30% weight)
    5. Arbiter does NOT re-run bandit when signed findings are available

  IndependencePreservation ::=
    "Arbiter treats security-auditor findings as opaque external evidence"
  | "Arbiter cannot modify, suppress, or reinterpret auditor findings"
  | "security-auditor does not know about Arbiter's scoring model"
  | "both can operate independently — integration is optional, not structural"

  AntiStrangeLoop ::=
    # Arbiter already scores itself (self-scoring gate ≥ 90).
    # If Arbiter also generated security findings it consumes, it would
    # create a second strange loop: generator → consumer → generator.
    # Using security-auditor as the external source breaks this loop.
    "Arbiter does NOT generate security findings it then scores"
  | "security-auditor does NOT score quality — it only catalogs findings"

  Contract ::=
    FindingFormat ::= "JSONL with schema version 1.1.0 (findings.schema.json)"
    Signature ::= "SHA256 fingerprint per finding + tool receipt per scan"
    Freshness ::= "findings older than cache TTL are stale; Arbiter requests rescan"
    MissingFindings ::= "if no signed findings available, Arbiter falls back to
                         running bandit directly (with a warning in the score)"
```

---

## 5. Confidence Assessment (MTSMU)

```yaml
claim: "The HUMMBL Problem is well-defined by this grammar"
semantic_confidence: 0.85
confidence_kind: synthesis_judgment
calibration_status: uncalibrated
basis: "reported implementations + tests, not independent verification"

evidence:
  - claim: "7 governance primitives implemented and tested"
    source: "hummbl-governance, 1031 tests"
    verification_status: reported
  - claim: "quality scoring in production"
    source: "Arbiter, 783 tests, PyPI v0.6.0"
    verification_status: reported
  - claim: "vulnerability scanning operational"
    source: "security-auditor, 28 tests, fleet scan complete"
    verification_status: reported
  - claim: "authorization framework deployed"
    source: "cyber-workbench, Phase 0"
    verification_status: reported
  - claim: "fleet-wide security scan completed"
    source: "37 repos, 4 HIGH fixed, this session"
    verification_status: verified
  - claim: "all primitives stdlib-only, independently importable, thread-safe"
    source: "hummbl-governance CLAUDE.md, pyproject.toml"
    verification_status: reported

uncertainties:
  - "grammar is a draft; not stress-tested against edge cases"
  - "RE (Recursion) family under-implemented — feedback loops exist but
     don't all close structurally (e.g., Arbiter scores feed back informally)"
  - "SY (Synthesis) family is emergent — no single system controls it"
  - "cyber-workbench is Phase 0 (ADAPT_REQUIRED) — not yet enforcing"

verification:
  - "grammar constructed from actual source code, not aspiration"
  - "every 'Implemented by' reference points to real, tested code"
  - "independent verification of test counts and implementation claims
     is pending — see evidence ledger (§8)"

next_lanes:
  - "stress-test grammar against a novel agent scenario"
  - "close the RE2 feedback loop: Arbiter scores → structured agent adjustment"
  - "promote cyber-workbench from Phase 0 to Phase 1"
  - "independently verify reported test counts and implementation claims"
  - "calibrate confidence against historical prediction accuracy"
```

---

## 6. Resolved Questions (Operator Decisions)

1. **Formalize as JSON Schema?**
   **Decision:** Yes. Schema created at `docs/ecosystem/hummbl_problem_grammar.schema.json` (§7).
   Machine validation is required before canon promotion.

2. **Is the 5-tier decomposition correct?**
   **Decision:** Provisionally yes. Authorization-before-scanning is the safety default,
   but the model now distinguishes scan types (Discovery, Privileged, Destructive,
   Disclosure-Producing) with graduated authorization depth (see §3.DE ScanTaxonomy).

3. **Formal convergence target?**
   **Decision:** Adopted. Governable fleet action = identity + authority + evidence +
   exception path + rollback + audit receipt + independent review (see §2.1).
   All seven conditions must be present, testable, and non-self-approved.

4. **Missing 7th dimension?**
   **Decision:** Do not add one. Seven invariants do not automatically imply a seventh
   transformation family. The mismatch (7 invariants, 6 families) is an observation,
   not a doctrine expansion. Some invariants map to multiple families.

5. **Should Arbiter consume security-auditor output?**
   **Decision:** Yes, as signed external evidence. Arbiter consumes security-auditor's
   signed findings (JSONL + SARIF with SHA256 fingerprints) as opaque external input
   to the security dimension score. Auditor independence is preserved — Arbiter cannot
   modify, suppress, or reinterpret findings. This breaks the self-scoring strange loop
   (see §4.1). If no signed findings are available, Arbiter falls back to running bandit
   directly with a warning in the score.

---

## 7. JSON Schema (Machine Validation)

**File:** `docs/ecosystem/hummbl_problem_grammar.schema.json`

The schema validates the structure of a HUMMBL Problem Grammar document —
lenses, invariants, boundary sets, stakeholder perspectives, failure modes,
transformation families, evidence chains, convergence target, and open questions.
It does NOT validate the truth of claims (that is the evidence ledger's job, §8).

---

## 8. Evidence Ledger

**File:** `docs/ecosystem/hummbl_problem_grammar_evidence.jsonl`

Maps each invariant, subsystem claim, and implementation reference to concrete
repo/file/test evidence. Every claim is marked as one of:
`verified`, `reported`, `inferred`, `speculative`, or `unimplemented`.

This ledger is the bridge between the grammar (what we claim) and the code
(what we can prove). Canon promotion requires all critical claims to reach
`verified` status.
