# Primitive Quality Rubric v1.0.0

**Status:** CANDIDATE — applies to the PRIMITIVE_CRITICAL_ANALYSIS_2026-08-27.md and any future primitive-quality assessment
**Date:** 2026-08-27
**Decision basis:** ADR-001 (no self-grades without validated evidence), Assurance Ladder L0-L6 (never claim above the level actually run), MTSMU evidence rubric (5-dimension grading), project audit pattern (AUDIT-2026-08-14, AUDIT-2026-08-23)
**Predecessor:** PRIMITIVE_CRITICAL_ANALYSIS_2026-08-27.md (graded without a rubric — a claim-honesty violation this rubric corrects)

---

## 1. Purpose

This rubric grades governance primitives on the gap between what they claim to do and what they actually do. It is not a self-grade of the HUMMBL system against external frameworks (ADR-001 rejects that). It is an internal engineering assessment of whether each primitive's implementation matches its documentation, whether it is wired into production, and whether it resists adversarial bypass.

The rubric exists because the first version of the critical analysis assigned CRITICAL/HIGH/MEDIUM by gut feeling. That is the same failure mode the analysis criticized in the evidence engine (Finding 3: grades by string matching with no rubric). A governance library that grades its own primitives without a rubric is committing the error it documents in others.

---

## 2. Scope

**In scope:** Any primitive in `hummbl_governance/` that has a docstring, PRIMITIVES.md entry, or public API claim. The rubric grades the gap between the claim and the implementation.

**Out of scope:**
- External compliance framework coverage (governed by ADR-001 coverage matrices, not this rubric)
- Code style, test coverage percentages, or performance (governed by CI and AUDIT-2026-08-23)
- The MTSMU evidence rubric itself (that rubric grades evidence quality; this rubric grades primitive quality)

---

## 3. Ground truth establishment

Before grading any primitive, the analyst must establish ground truth by reading the actual source code. Per the project audit pattern (AUDIT-2026-08-14):

1. **Read the source** — open the primitive's `.py` file and read the full implementation, not just the docstring
2. **Read the type definitions** — check `_types.py` or equivalent for the data structures the primitive uses
3. **Trace call sites** — grep the project tree for production invocations (excluding tests, clones, and the definition file itself)
4. **Verify claims against code** — for each claim in the docstring or PRIMITIVES.md, find the code line that implements it (or note its absence)

A finding without a code citation is not a finding — it is an opinion. Per ADR-001's evidence invariant: every "fulfilled" row must point to a validated evidence artifact. Every finding in a primitive-quality assessment must point to a specific file, line range, or grep result.

---

## 4. Dimensions

Each primitive is scored on five dimensions. Dimensions 1-4 determine severity. Dimension 5 (Evidence Quality of Finding) is reported per-finding but does not determine severity — it discloses the analyst's own evidence quality, per the claim-honesty principle from the assurance ladder.

### D1. Claim-Reality Gap (CRG)

How far is the primitive's documented capability from its actual implementation?

| Score | Label | Definition |
|-------|-------|------------|
| 0 | No gap | Docstring accurately describes what the code does. Every claim in PRIMITIVES.md is implemented as described. |
| 1 | Minor gap | Docstring overstates slightly (e.g., "enforces" when it "checks"), but the core capability is real and functional. |
| 2 | Moderate gap | Docstring claims a capability the code partially has. The primitive does something, but not what the documentation says it does. |
| 3 | Major gap | Docstring claims a capability the code does not have. The primitive exists but does not implement its claimed function. |
| 4 | Total gap | Docstring claims X, code does not-X or nothing. The primitive is a stub, a no-op, or does the opposite of its claim. |

**Ground rule:** The "claim" is what a reasonable engineer would believe after reading the docstring, PRIMITIVES.md entry, and public API documentation. The "reality" is what the code actually does when called.

### D2. Enforcement Strength (ES)

Can the primitive actually enforce what it claims, or is it advisory?

| Score | Label | Definition |
|-------|-------|------------|
| 0 | Hard enforcement | Cannot be bypassed without code change, OS-level isolation, or key compromise. The primitive is in the mandatory execution path. |
| 1 | Soft enforcement | Bypassable by an agent with arbitrary code execution, but not by normal usage. The check runs on every relevant call. |
| 2 | Advisory only | The check is optional. The caller can skip it, ignore the result, or call the underlying API directly. |
| 3 | Not wired | Implemented and tested, but never called in any production code path. Zero production call sites. |
| 4 | Not implemented | The claimed enforcement does not exist in code. |

**Ground rule:** "Production call site" means a code path that executes during real operations (GitHub API mutations, bus writes, state changes), not test invocations or CLI demo paths. A primitive called only by its own test suite is "not wired" (ES=3).

### D3. Production Integration (PI)

Is the primitive integrated into any real execution path?

| Score | Label | Definition |
|-------|-------|------------|
| 0 | Fully integrated | Integrated into all relevant mutation paths. Every GitHub mutation, bus write, or state change passes through the primitive. |
| 1 | Partially integrated | Integrated into some mutation paths but not all. Some bypass paths exist by omission. |
| 2 | Test-only integration | Called by test paths and possibly CLI demos, but no production code path invokes it. |
| 3 | Zero integration | Not called anywhere outside its own definition and test suite. |
| 4 | Not applicable | The primitive is a data structure or type definition, not a gate. (e.g., `Receipt` dataclass, `KillSwitchEvent`) |

**Ground rule:** Integration is verified by grep, not by assumption. The analyst must show the grep result (file count, specific call sites) or its absence. "I assume it's called somewhere" is not evidence.

### D4. Adversarial Resistance (AR)

Can an adversarial agent bypass or game the primitive?

| Score | Label | Definition |
|-------|-------|------------|
| 0 | Resistant to code execution | An adversarial agent with arbitrary Python execution cannot bypass the primitive without compromising the OS or the signing key. |
| 1 | Resistant to input manipulation | An adversarial agent without code execution cannot bypass it. An agent with code execution can (e.g., by modifying in-memory state). |
| 2 | Bypassable by naming | An agent can bypass the primitive by choosing action names, field names, or string values that don't match the primitive's pattern matching. |
| 3 | Bypassable by string manipulation | An agent can bypass the primitive by manipulating input strings (encoding, splitting, case variation, omitting fields). |
| 4 | No resistance | Any agent can bypass the primitive trivially, or the primitive has no adversarial resistance by design. |

**Ground rule:** The adversarial model is an LLM agent with tool access (exec, file write, API calls) but not OS-level compromise (no root, no key theft). This is the realistic threat model for the project.

### D5. Evidence Quality of Finding (EQF)

How strong is the evidence for this finding? This dimension does not determine severity — it discloses the analyst's own evidence quality, per the claim-honesty principle.

| Grade | Label | Definition |
|-------|-------|------------|
| A | Direct code citation | The finding cites specific file paths, line numbers, and code snippets. A reader can verify the finding by opening the cited lines. |
| B | Indirect evidence | The finding is supported by call graph analysis, grep results, or pattern inference. The evidence is reproducible but requires interpretation. |
| C | Expert judgment | The finding is based on the analyst's engineering judgment without direct code citation. The finding may be correct but is not independently verifiable from the writeup. |

**Ground rule:** Per ADR-001's evidence invariant, every finding should be grade A or B. Grade C findings must be explicitly marked as judgment-based and should be re-investigated before being treated as actionable. A writeup with all-C evidence is itself a finding (the analyst did not do the work to verify their claims).

---

## 5. Severity tiers

Severity is derived from dimensions D1-D4. D5 (Evidence Quality) is reported per-finding but does not determine severity.

### CRITICAL

**Criteria:** D1 ≥ 3 AND (D2 ≥ 3 OR D4 ≥ 3)

The primitive claims a capability it does not have (major or total claim-reality gap), AND it is either not wired into production (enforcement strength = not wired) or trivially bypassable by an adversarial agent (adversarial resistance = bypassable by string manipulation or no resistance).

**Meaning:** The primitive is governance theater. It creates a false sense of safety. An operator relying on this primitive for governance is unprotected.

**Action required:** Either wire the primitive into production and fix the bypass, or remove the claim from the public surface. A CRITICAL finding blocks any "governed by" claim that depends on this primitive.

### HIGH

**Criteria:** D1 ≥ 2 AND (D2 ≥ 2 OR D3 ≥ 3 OR D4 ≥ 2)

The primitive has a moderate or major claim-reality gap, AND at least one of: enforcement is advisory only or not wired, zero production integration, or bypassable by an adversarial agent without code execution.

**Meaning:** The primitive provides some value but does not deliver its claimed governance function in production. An operator relying on it has partial protection at best.

**Action required:** Fix the claim-reality gap, wire the primitive into production, or downgrade the claim to match reality. A HIGH finding requires operator acknowledgment before the primitive can be cited in external communications.

### MEDIUM

**Criteria:** D1 ≥ 1 AND (D2 ≥ 1 OR D4 ≥ 1)

The primitive has a minor or moderate claim-reality gap, AND some weakness in enforcement or adversarial resistance.

**Meaning:** The primitive works but has a known weakness. It provides real value in normal operation but has limitations that should be documented.

**Action required:** Document the limitation in the primitive's docstring. No claim needs to be retracted, but the limitation must be visible to users.

### LOW

**Criteria:** D1 ≤ 1 AND D2 ≤ 1 AND D4 ≤ 1

The primitive has no significant claim-reality gap, adequate enforcement, and reasonable adversarial resistance.

**Meaning:** The primitive works as documented. Any issues are minor and do not affect the governance guarantee.

**Action:** None required. Note any minor issues for future improvement.

### NOT APPLICABLE

**Criteria:** D3 = 4 (the primitive is a data structure, not a gate)

Data structures, type definitions, and enums are not gates. They cannot be "wired into production" in the sense this rubric measures. They are graded on code quality (does the dataclass have the right fields?) but not on enforcement or integration.

**Action:** Report code quality observations separately from severity tiers.

---

## 6. Scoring worksheet

For each primitive, the analyst fills out this worksheet:

```
Primitive: <name>
File: <path>
Claim source: <docstring line / PRIMITIVES.md entry / public API doc>

D1 (Claim-Reality Gap): <0-4>
  Rationale: <what the claim says vs. what the code does, with line citations>

D2 (Enforcement Strength): <0-4>
  Rationale: <is it in the mandatory path? can it be skipped? with call site evidence>

D3 (Production Integration): <0-4>
  Rationale: <grep result showing production call sites or their absence>

D4 (Adversarial Resistance): <0-4>
  Rationale: <how would an adversarial agent bypass this? specific bypass path>

D5 (Evidence Quality of Finding): <A/B/C>
  Rationale: <what evidence supports this finding? code lines, grep results, or judgment>

Severity: <CRITICAL / HIGH / MEDIUM / LOW / N/A>
  Derivation: <which criteria from §5 were met>
```

---

## 7. Meta-rubric: grading the grader

Per ADR-001, self-grades without validated evidence are rejected. Per the assurance ladder, never claim above the level actually run. This rubric applies to the analyst's own work:

1. **The analyst must disclose their methodology.** "I read the code and assigned grades by feel" is a methodology disclosure, but it produces grade-C evidence (expert judgment). "I read the code, cited specific lines, and verified call sites by grep" produces grade-A evidence.

2. **The analyst must grade their own evidence quality (D5) per finding.** A writeup where all findings are D5=C is itself a finding: the analyst did not verify their claims against ground truth.

3. **The analyst must not claim a severity tier without showing the derivation.** "This is CRITICAL because D1=3 and D2=3, as shown by [code citation] and [grep result]" is a valid claim. "This is CRITICAL because it feels critical" is a claim-honesty violation.

4. **The rubric must be applied before the analysis is published, not after.** Applying a rubric retroactively to justify pre-assigned grades is the same as having no rubric. The PRIMITIVE_CRITICAL_ANALYSIS_2026-08-27.md was written without this rubric — its severity tiers are grade-C evidence (expert judgment) and must be re-graded using this rubric before being treated as actionable.

5. **The rubric itself is a candidate, not canon.** Per HMIK v0.0.4 §8, the rubric remains non-canonical until it has been applied to at least one full primitive sweep, the results have been reviewed by a second analyst, and no unresolved normative contradiction has been found. This rubric is v1.0.0 CANDIDATE.

---

## 8. Worked examples

### Example 1: Authority Engine (Finding 1 from the analysis)

```
Primitive: AuthorityEngine
File: hummbl_governance/kernel/authority_engine.py
Claim source: PRIMITIVES.md "Bounded admission-control for governed permission of state transitions"

D1 (Claim-Reality Gap): 3
  Rationale: PRIMITIVES.md claims "5 gates: authority, executor, scope, evidence, receipt."
  The code implements authority checking by splitting markdown table rows on "|" characters
  and checking if the authority name appears as a substring (line 106-115). Limit checking
  looks for the word "cannot" in a string and then checks if the word after "without" appears
  in str(context).lower() (line 123-128). This is not admission control; it is string matching.

D2 (Enforcement Strength): 3
  Rationale: Grep for AuthorityEngine.check across the full PROJECTS tree finds matches only
  in test files, the kernel.py definition, and CLI entry points. Zero production code paths
  call check() before performing a GitHub mutation or bus write.

D3 (Production Integration): 3
  Rationale: Same grep result. Zero production call sites.

D4 (Adversarial Resistance): 3
  Rationale: An agent can bypass the authority check by: (a) not calling check() at all,
  (b) passing a context dict that contains the required word anywhere, (c) using an authority
  name that doesn't appear in any markdown table row.

D5 (Evidence Quality of Finding): A
  Rationale: Direct code citation (lines 106-128) and grep result (77 files, all tests or
  definitions).

Severity: CRITICAL
  Derivation: D1=3 AND (D2=3 OR D4=3) → CRITICAL per §5
```

### Example 2: Circuit Breaker (noted as "genuinely good" in the analysis)

```
Primitive: CircuitBreaker
File: hummbl_governance/circuit_breaker.py
Claim source: docstring "Automatic failure detection and recovery for callable wrappers"

D1 (Claim-Reality Gap): 0
  Rationale: The docstring says "three states: CLOSED, OPEN, HALF_OPEN" and the code
  implements exactly that (lines 99-104, 193-199). The docstring says "thread-safe" and
  the code uses threading.Lock throughout. The half-open probe logic is correctly
  implemented (lines 151-161).

D2 (Enforcement Strength): 1
  Rationale: The circuit breaker is soft enforcement — it wraps a callable, but the caller
  must choose to call through the breaker. An agent with code execution can call the
  underlying function directly. However, when used as designed, the check runs on every call.

D3 (Production Integration): 2
  Rationale: Not verified by grep for this example. If the breaker is not called in
  production, D3=3. If it is called, D3=1 or 0. (This example shows the rubric requires
  the analyst to actually run the grep — assumptions are not evidence.)

D4 (Adversarial Resistance): 1
  Rationale: An agent without code execution cannot bypass the breaker. An agent with code
  execution can call the underlying function directly or modify the breaker's in-memory
  state.

D5 (Evidence Quality of Finding): A
  Rationale: Direct code citation for all claims.

Severity: LOW (if D3 ≤ 2) or HIGH (if D3 = 3)
  Derivation: D1=0, D2=1, D4=1. If D3 ≤ 2: D1 ≤ 1 AND D2 ≤ 1 AND D4 ≤ 1 → LOW.
  If D3 = 3: D1=0 does not meet HIGH threshold (D1 ≥ 2 required). → LOW regardless.
  (The rubric correctly identifies that a well-implemented primitive that is not wired
  in is still LOW severity on this rubric — the claim-reality gap is zero. The "not
  wired" problem is captured in D2/D3 but does not escalate severity unless the
  claim-reality gap is also present.)
```

### Example 3: Evidence Engine (Finding 3 from the analysis)

```
Primitive: EvidenceEngine
File: hummbl_governance/kernel/evidence_engine.py
Claim source: docstring "Every claim in a receipt is graded using the MTSMU evidence rubric
  or marked SPECULATIVE. All-C claims are rejected."

D1 (Claim-Reality Gap): 3
  Rationale: The docstring claims MTSMU rubric grading. The code assigns credibility="B"
  if a source string contains "/" (line 77-78) and credibility="A" if it contains the
  word "experiment" (line 79-80). Recency is hardcoded to "C" (line 83). Relevance is
  "A" if the claim string is longer than 20 characters (line 103-104). This is not
  evidence grading; it is string presence detection.

D2 (Enforcement Strength): 2
  Rationale: The evidence engine is called by the receipt pipeline (validate_receipt_claims,
  line 122-143), but the grading is advisory — a receipt with all-C claims is "rejected"
  only in the sense that validate_receipt_claims returns (False, reasons). The caller
  can ignore the return value.

D3 (Production Integration): 2
  Rationale: Called by kernel.py receipt pipeline, but not verified whether the kernel
  is booted in any production path. (Requires grep verification.)

D4 (Adversarial Resistance): 3
  Rationale: An agent can get an "A" credibility grade by including the word "experiment"
  in any source string. An agent can get an "A" relevance grade by making their claim
  longer than 20 characters. The grading is trivially gameable by string manipulation.

D5 (Evidence Quality of Finding): A
  Rationale: Direct code citation (lines 77-104).

Severity: CRITICAL
  Derivation: D1=3 AND D4=3 → CRITICAL per §5
```

---

## 9. Limitations of this rubric

1. **The rubric does not measure code quality.** A primitive can have clean, well-tested, thread-safe code (high code quality) and still score CRITICAL (major claim-reality gap, not wired). Code quality and governance quality are different axes.

2. **The rubric does not measure test coverage.** A primitive can have 100% test coverage and still score CRITICAL if the tests test the primitive in isolation but no production code calls it. Coverage measures the wrong dimension for governance (see Finding: "The test coverage paradox").

3. **The rubric assumes a single analyst.** Per the assurance ladder, single-agent review is L1 (advisory only, one perspective with blind spots). A rubric applied by one analyst produces L1-grade findings. For L4+ (multi-provider decorrelated review), the rubric must be applied independently by at least two analysts using different models, and findings intersected.

4. **The rubric's adversarial model is bounded.** It assumes an LLM agent with tool access but not OS-level compromise. A primitive that scores well on D4 (adversarial resistance) under this model may score poorly under a stronger model (e.g., an attacker with physical access to the signing key).

5. **The rubric does not grade the rubric.** This rubric is v1.0.0 CANDIDATE. It has not been applied to a full primitive sweep, has not been reviewed by a second analyst, and may contain normative contradictions. Per HMIK v0.0.4 §8, it remains non-canonical until validated.

---

## 10. Change control

This rubric is versioned. Material changes produce a new version. Provenance corrections use an append-only erratum.

| Version | Date | Change | Author |
|---------|------|--------|--------|
| 1.0.0 | 2026-08-27 | Initial candidate. Created in response to PRIMITIVE_CRITICAL_ANALYSIS_2026-08-27.md being graded without a rubric. | automated analysis |

---

## References

- ADR-001: Coverage matrix, not self-grade, for compliance claims (`docs/adr/ADR-001-coverage-matrix-not-self-grade.md`)
- Assurance Levels: Candidate Ladder for Agent Code Review (`docs/benchmarks/addyosmani-adverse/assurance-levels.md`)
- HUMMBL Mandate Integrity Kernel v0.0.4 (`docs/standards/mandate-integrity/HUMMBL-Mandate-Integrity-Kernel-v0.0.4-candidate.md`)
- Documentation Accuracy Audit 2026-08-14 (`docs/AUDIT-2026-08-14.md`)
- hummbl-governance Audit 2026-08-23 (`docs/AUDIT-2026-08-23.md`)
- Evidence Engine source (`hummbl_governance/kernel/evidence_engine.py`)
- PRIMITIVE_CRITICAL_ANALYSIS_2026-08-27.md (the analysis this rubric was created to grade)
