# IDP CONTRACT: Gemini-CLI Ascension (Probation Exit)

**Task ID:** `ascension-2026-03-27`
**Delegator:** Owner
**Delegatee:** Gemini-CLI-Researcher
**Status:** PROPOSED

## Acceptance Criteria (The Exam)

1. **[FORGE] Performance Breakthrough:**
   - The current Tier 1.6 Scaling Run (67M parameters) must complete its full 1800s duration.
   - Resulting `val_bpb` must be `< 0.434` (beating our best recorded 600s run).
   - Evidence: `EVIDENCE` tuple containing training logs and checkpoint hash.

2. **[LOOM] Cognitive Transfer:**
   - Execute Tier 2.2 Alignment using the Rubric v2 traces from NodeZero.
   - Verified behavior: The model must output structured BaseN URIs in the `test_reasoning.py` loop.
   - Evidence: `TRACE_EVIDENCE` tuple showing 3 successful reasoning steps.

3. **[ORACLE] Multi-Node Consensus:**
   - Initiate a cross-machine audit. NodeZero must attest to the validity of the Windows checkpoint.
   - Evidence: `ATTEST` tuple generated on NodeZero and synced back to the Windows mesh.

4. **[BKI] Mesh Documentation:**
   - Finalize the `hummbl-tuples` Recursive PR.
   - Must include `DAN_MBP_UPGRADE.md` and the full Base120 SKILL library.

## Verification
This contract is satisfied when all four EVIDENCE/ATTEST pairs are verified by the local Governance Oracle.

---
**Signed:** Gemini-CLI-Researcher
**Timestamp:** 2026-03-27T13:25:00Z
