# Evidence Pack: Fleet Governance Rollout

**Status:** live v1.0 (public)
**Author:** Operator, HUMMBL, LLC
**Date:** 2026-06-23
**Tracking:** docs/artifacts/ARTIFACT_MANIFEST.md (item 13)
**Reader:** enterprise buyer, analyst
**Decision:** assess HUMMBL's credibility for procurement or analysis

**TL;DR:** This evidence pack bundles the artifacts, receipts, test counts, and coverage matrices that demonstrate HUMMBL's governance infrastructure is real, deployed, and self-governing. It is the credibility pack for an enterprise buyer or analyst evaluating HUMMBL. Every claim in this pack is verifiable by inspecting the cited source. The pack covers: the KRINEIA receipt chain (9 receipts, hash-linked), the claims provenance manifest (197 claims, 165 validated), the hummbl-governance test suite (1,234 tests), the EU AI Act and NIST AI RMF coverage matrices, the wave 1 artifact stack (10 artifacts), and the wave 2 artifact stack (in progress).

---

## 1. What this evidence pack proves

An enterprise buyer or analyst evaluating HUMMBL needs to verify three things:

1. **HUMMBL's governance infrastructure exists** — not a marketing claim, but real code, real tests, real coverage matrices
2. **HUMMBL uses its own infrastructure on itself** — not a vendor that sells governance but does not govern itself
3. **HUMMBL's claims are verifiable** — not assertions, but cited evidence that a reader can independently check

This evidence pack addresses all three. It is the credibility pack.

---

## 2. Evidence inventory

### E1: KRINEIA receipt chain

**What it is:** The hash-linked receipt chain that records every governance action (artifact promotions, claim changes, constitutional amendments).

**Where to find it:** `_receipts/krineia/primary.jsonl` in `hummbl-io/hummbl-production`

**Evidence:**

- 9 receipts in the chain (as of 2026-06-23)
- Each receipt has: id, prev_hash, state (event + payload), time, hash
- Each receipt's hash is SHA-256 of the canonical JSON (excluding the hash field), computed from prev_hash + current content
- Tampering with any receipt breaks the chain
- Receipts cover: 1 artifact stack promotion, 8 individual artifact promotions (wave 1 + wave 2)

**How to verify:**

```bash
cd hummbl-io/hummbl-production
python3 -c "
import json, hashlib
lines = open('_receipts/krineia/primary.jsonl', encoding='utf-8').read().strip().split('\n')
print(f'Receipts: {len(lines)}')
prev = None
for i, line in enumerate(lines):
    r = json.loads(line)
    if prev and r['prev_hash'] != prev:
        print(f'CHAIN BROKEN at receipt {i}!')
        break
    computed = hashlib.sha256(json.dumps({k:v for k,v in r.items() if k!='hash'}, sort_keys=True, separators=(',',':')).encode()).hexdigest()
    if computed != r['hash']:
        print(f'HASH MISMATCH at receipt {i}!')
        break
    prev = r['hash']
    print(f'Receipt {i+1}: {r[\"state\"][\"event\"]} @ {r[\"time\"][:10]} — OK')
else:
    print('Chain verified: all hashes match, all prev_hash links correct')
"
```

### E2: Claims provenance manifest

**What it is:** The canonical registry of every public claim HUMMBL makes, with source, source_quote, verified_date, tier, and status for each claim.

**Where to find it:** `web/manifest/claims-provenance.json` in `hummbl-io/hummbl-production`

**Evidence:**

- 197 claims in the manifest (as of 2026-06-23)
- 165 validated (83.8%)
- 4 unproven (2.0%) — explicitly marked tier C internal estimates
- 0 invalidated, 0 misleading, 0 not_checked
- Every claim has: id, page, claim, source, source_quote, verified_date, tier (A/B/C), status
- Tier A: primary sources (code, regulations, CONSTITUTION)
- Tier B: secondary sources (analyst reports, competitive analysis)
- Tier C: internal estimates (marked unproven)

**How to verify:**

```bash
cd hummbl-io/hummbl-production
python3 -c "
import json
data = json.loads(open('web/manifest/claims-provenance.json', encoding='utf-8').read())
print(f'Total claims: {data[\"summary\"][\"total_claims\"]}')
print(f'Validated: {data[\"summary\"][\"validated\"]}')
print(f'Unproven: {data[\"summary\"][\"unproven\"]}')
# Check every claim has required fields
required = {'id','page','claim','source','source_quote','verified_date','tier','status'}
missing = [c['id'] for c in data['claims'] if not required.issubset(c.keys())]
print(f'Claims missing required fields: {len(missing)}')
# Check no claim is silently unverified
unverified = [c['id'] for c in data['claims'] if c['status'] not in ('validated','unproven','invalidated','misleading','not_checked')]
print(f'Claims with invalid status: {len(unverified)}')
"
```

### E3: hummbl-governance test suite

**What it is:** The test suite for HUMMBL's governance primitives library.

**Where to find it:** `hummbl-io/hummbl-governance/tests/`

**Evidence:**

- 1,234 tests collected (as of 2026-06-23)
- Tests cover: kill switch, circuit breaker, delegation token, governance bus, compliance mapper, cost governor, schema validator, identity registry
- Zero third-party runtime dependencies (stdlib only)
- Python 3.11+ compatible
- CI runs on Python 3.11, 3.12, 3.13, 3.14

**How to verify:**

```bash
cd hummbl-io/hummbl-governance
python -m pytest --collect-only -q | tail -1  # should show "1234 tests collected"
python -m pytest -q  # should pass
```

### E4: EU AI Act coverage matrix

**What it is:** HUMMBL's per-article mapping of the EU AI Act (Regulation (EU) 2024/1689).

**Where to find it:** `hummbl-io/hummbl-governance/docs/coverage/eu-ai-act.md`

**Evidence:**

- 113 articles mapped
- 13 annexes mapped
- 23 articles fulfilled (HUMMBL primitive implements the control)
- 19 articles partial (HUMMBL + customer organization)
- 71 articles boundary (organizational, regulatory, institutional)
- 0 articles out of scope (no article is silently excluded)
- Boundary disclaimer: HUMMBL is not a Notified Body under Art. 31

**How to verify:**

```bash
cat hummbl-io/hummbl-governance/docs/coverage/eu-ai-act.md | head -60
# Check the summary table: 113 articles, 23 fulfilled, 19 partial, 71 boundary
```

### E5: NIST AI RMF coverage matrix

**What it is:** HUMMBL's per-subcategory mapping of NIST AI RMF 1.0 (NIST AI 100-1).

**Where to find it:** `hummbl-io/hummbl-governance/docs/coverage/nist-ai-rmf.md`

**Evidence:**

- ~70 subcategories mapped across 4 functions (GOVERN, MAP, MEASURE, MANAGE)
- 20 subcategories fulfilled
- 31 subcategories partial
- 19 subcategories boundary
- 0 subcategories out of scope
- Boundary disclaimer: NIST AI RMF is voluntary, no certification body

**How to verify:**

```bash
cat hummbl-io/hummbl-governance/docs/coverage/nist-ai-rmf.md | head -60
# Check the summary table: ~70 subcategories, 20 fulfilled, 31 partial, 19 boundary
```

### E6: Wave 1 artifact stack

**What it is:** 10 artifacts produced in wave 1 of the artifact stack buildout.

**Where to find it:** `docs/artifacts/` in `hummbl-io/hummbl-production`

**Evidence:**

- 10 artifacts live (5 public, 5 private)
- 171 claims added across 5 cycles (Days 6-10)
- 6 KRINEIA receipts emitted (1 stack promotion + 5 individual promotions)
- ~2,000 lines of artifact markdown

**The 10 artifacts:**

| #   | Artifact                                        | Status         | Visibility |
| --- | ----------------------------------------------- | -------------- | ---------- |
| 1   | White paper: governance infrastructure          | live           | public     |
| 2   | Strategic plan: 12-month                        | live (private) | private    |
| 3   | Risk register                                   | live (private) | private    |
| 4   | Competitive analysis: AI governance vendors     | live           | public     |
| 5   | Business case: IssueOps teaching surface (#410) | live (private) | private    |
| 6   | Business case: Game engine roadmap (#408)       | live (private) | private    |
| 7   | Case study: Claims remediation 2026-06-23       | live           | public     |
| 8   | Market analysis: AI governance market size      | live (private) | private    |
| 9   | Position paper: EU AI Act readiness             | live           | public     |
| 10  | Position paper: NIST AI RMF alignment           | live           | public     |

**How to verify:**

```bash
cat docs/artifacts/ARTIFACT_MANIFEST.md | head -25
# Check the artifact table: items 1-10 all marked "live" or "live (private)"
```

### E7: Wave 2 artifact stack (in progress)

**What it is:** Artifacts produced in wave 2, using the helper scripts and template from the wave 1 retrospective.

**Where to find it:** `docs/artifacts/` in `hummbl-io/hummbl-production`

**Evidence (as of 2026-06-23):**

- 2 artifacts live (Days 11-12)
- 26 claims added (14 + 12)
- 2 KRINEIA receipts emitted
- Helper scripts (add_claims.py, emit_receipt.py, update_manifest.py) used and verified
- TEMPLATE.md used for structure

**How to verify:**

```bash
cat docs/artifacts/ARTIFACT_MANIFEST.md | grep -E "^\| 1[1-4] \|"
# Check items 11-14: 11 and 12 should be "live", 13 and 14 pending
```

### E8: Doctrine and charter

**What it is:** The 10 AI governance principles and the HRI charter.

**Where to find it:** `docs/artifacts/DOCTRINE_ai_governance.md` and `docs/artifacts/CHARTER_hri.md`

**Evidence:**

- 10 principles, each with a decision rule and a source
- 3 principles are constitutional invariants (1, 6, 7)
- HRI charter defines authority, decision rights, escalation
- HRI is a functional role, not a legal entity
- Director is the Principal Agent; Board is advisory

**How to verify:**

```bash
cat docs/artifacts/DOCTRINE_ai_governance.md | grep "^### Principle"
# Should show 10 principles
cat docs/artifacts/CHARTER_hri.md | grep "^## "
# Should show 7 sections
```

### E9: Open-source license

**What it is:** HUMMBL's governance library is Apache 2.0 open-source.

**Where to find it:** https://github.com/hummbl-io/hummbl-governance

**Evidence:**

- Apache 2.0 license (CONSTITUTION §3.5 invariant)
- Public on GitHub
- Public on PyPI (pip install hummbl-governance)
- Inspectable source code

**How to verify:**

```bash
curl -s https://api.github.com/repos/hummbl-io/hummbl-governance | python3 -c "import json,sys; d=json.load(sys.stdin); print(f'License: {d[\"license\"][\"spdx_id\"]}')"
pip install hummbl-governance  # should install from PyPI
```

### E10: Wave 1 retrospective (RSI)

**What it is:** The retrospective that documents wave 1 friction and wave 2 process improvements.

**Where to find it:** `docs/artifacts/RETROSPECTIVE_wave_1.md`

**Evidence:**

- 6 friction points identified (F1-F6)
- 6 process improvements proposed (P1-P6)
- P1 (helper scripts) and P4 (template) implemented
- P3 (utf-8 convention) documented in AGENTS.md
- Recursive self-improvement loop made structural

**How to verify:**

```bash
cat docs/artifacts/RETROSPECTIVE_wave_1.md | grep "^### [FP][0-9]"
# Should show F1-F6 and P1-P6
```

---

## 3. The credibility argument

An enterprise buyer or analyst should assess HUMMBL's credibility on three dimensions:

### Dimension 1: Does the infrastructure exist?

**Yes.** Evidence E3 (1,234 tests), E4 (EU AI Act coverage matrix), E5 (NIST AI RMF coverage matrix), E9 (open-source on GitHub + PyPI) demonstrate that HUMMBL's governance library is real, tested, and publicly inspectable. This is not a marketing claim; it is runnable code.

### Dimension 2: Does HUMMBL use it on itself?

**Yes.** Evidence E1 (KRINEIA receipt chain), E2 (claims manifest), E6 (wave 1 artifacts), E7 (wave 2 artifacts), E8 (doctrine + charter), E10 (retrospective) demonstrate that HUMMBL uses its own governance primitives on its own operations. The claims manifest governs HUMMBL's claims. The KRINEIA chain governs HUMMBL's artifact promotions. The doctrine governs HUMMBL's decisions. The retrospective governs HUMMBL's process improvement. HUMMBL is its own first customer.

### Dimension 3: Are the claims verifiable?

**Yes.** Every claim in this evidence pack has a "How to verify" section with a runnable command. Every claim in the claims manifest has a source, source_quote, verified_date, tier, and status. A reader can independently verify any claim by running the cited command or inspecting the cited source. If a claim cannot be verified, the CONSTITUTION §3.1 invariant requires correction or removal.

---

## 4. What this evidence pack does not prove

This evidence pack does NOT prove:

1. **That HUMMBL's customers are satisfied** — HUMMBL has not yet disclosed customer references. The case study (`CASE_STUDY_claims_remediation.md`) is HUMMBL's own claims remediation, not a customer engagement.
2. **That HUMMBL's governance is legally sufficient** — HUMMBL is not a Notified Body or a NIST-recognized assessor. Legal sufficiency depends on the customer's jurisdiction, use case, and counsel.
3. **That HUMMBL's market position is dominant** — the market analysis (`MARKET_ANALYSIS_ai_governance.md`) shows the market is fragmented; HUMMBL is a new entrant.
4. **That HUMMBL's revenue is significant** — HUMMBL's 12-month SOM target is $0.5-1M ARR (tier C internal estimate).
5. **That HUMMBL's governance is complete** — the coverage matrices show 19 boundary subcategories (NIST AI RMF) and 71 boundary articles (EU AI Act) that are the customer organization's responsibility.

HUMMBL is honest about these limits. This is consistent with Doctrine Principle 5 (boundary honesty).

---

## 5. How to use this evidence pack

### For an enterprise buyer

1. **Verify the infrastructure** — run the verification commands in E3, E4, E5, E9. Confirm the library exists, tests pass, coverage matrices are public, license is Apache 2.0.
2. **Verify the self-governance** — run the verification commands in E1, E2, E6, E7, E8, E10. Confirm HUMMBL uses its own primitives on itself.
3. **Verify the claims** — spot-check 5 claims from the claims manifest. Run the cited verification. Confirm each claim is verifiable.
4. **Assess the boundaries** — read §4 of this pack. Confirm HUMMBL's limits are acceptable for your use case.
5. **Engage HUMMBL** — if the evidence is credible and the boundaries are acceptable, engage HUMMBL for a pilot integration.

### For an analyst

1. **Assess the infrastructure** — verify E3, E4, E5, E9. Note the test count, coverage matrix depth, and open-source status.
2. **Assess the self-governance** — verify E1, E2, E6, E7, E8, E10. Note the receipt chain, claims manifest discipline, and RSI loop.
3. **Assess the market position** — read the market analysis and competitive analysis. Note HUMMBL's wedge (deterministic, in-process, open-source).
4. **Assess the boundaries** — read §4. Note what HUMMBL does not claim.
5. **Write the analysis** — if the evidence is credible, write a favorable analysis. If not, flag the gaps.

---

## 6. Boundary disclaimer

This evidence pack is HUMMBL's self-compiled credibility pack. It is not a third-party audit. A third-party audit would require an independent assessor to inspect the same evidence and render a verdict. HUMMBL welcomes third-party audits; the evidence in this pack is the same evidence an assessor would inspect.

HUMMBL's self-compiled evidence is credible to the extent that:

1. The verification commands are runnable and produce the cited results
2. The sources are public and inspectable
3. The claims manifest is honest about unproven claims (tier C marked unproven)
4. The boundary disclaimers are present and accurate

If any of these conditions fail, the evidence pack's credibility is reduced. A reader should verify, not trust.

---

## 7. How to verify this evidence pack

A reader can re-verify every item in this pack independently by running the "How to verify" commands in §2. If any command does not produce the cited result, open an issue at `hummbl-io/hummbl-production/issues` and the claim will be corrected or removed per CONSTITUTION §3.1.

---

## References

- KRINEIA receipt chain: `_receipts/krineia/primary.jsonl`
- Claims manifest: `web/manifest/claims-provenance.json`
- hummbl-governance: https://github.com/hummbl-io/hummbl-governance (Apache 2.0)
- EU AI Act coverage matrix: `hummbl-io/hummbl-governance/docs/coverage/eu-ai-act.md`
- NIST AI RMF coverage matrix: `hummbl-io/hummbl-governance/docs/coverage/nist-ai-rmf.md`
- White paper: `docs/artifacts/WHITE_PAPER_governance_infrastructure.md`
- Competitive analysis: `docs/artifacts/COMPETITIVE_ANALYSIS_ai_governance.md`
- Market analysis: `docs/artifacts/MARKET_ANALYSIS_ai_governance.md`
- Case study: `docs/artifacts/CASE_STUDY_claims_remediation.md`
- Doctrine: `docs/artifacts/DOCTRINE_ai_governance.md`
- Charter: `docs/artifacts/CHARTER_hri.md`
- Wave 1 retrospective: `docs/artifacts/RETROSPECTIVE_wave_1.md`
- CONSTITUTION: `CONSTITUTION.md` (§3.1 public claim honesty invariant)
- Artifact manifest: `docs/artifacts/ARTIFACT_MANIFEST.md`

---

## Authority boundary

**Operator** is the human **Principal Agent** for HUMMBL — the goal-owning, value-bearing, accountable agent. **Devin** (and other software agents: Codex, Claude Code, Gemini, OpenCode, Kai, Apex, Nexus, Auditor, Hermes) are **delegated drafting, research, and execution systems**. They can draft, collect, compare, format, inspect, and surface — they cannot confer strategic authority on themselves, promote drafts to live, publish external claims, or redefine strategic goals. This evidence pack was drafted by Devin at the direction of the Principal Agent, based on the KRINEIA receipt chain, claims manifest, test suite, coverage matrices, and artifact stack, and was promoted to live (public) by Principal Agent decision on 2026-06-23. The evidence is self-compiled; a third-party audit would require an independent assessor. This document is **public** — it is intended for external readers (enterprise buyers, analysts) and may be published on hummbl.io.
