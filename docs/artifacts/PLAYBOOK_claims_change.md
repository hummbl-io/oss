# Playbook: Claims Change Protocol

**Status:** live v1.0 (public)
**Author:** Operator, HUMMBL, LLC
**Date:** 2026-06-23
**Tracking:** docs/artifacts/ARTIFACT_MANIFEST.md (item 14)
**Reader:** agents, operators
**Decision:** how to add, update, validate, retract, or remove a claim in HUMMBL's claims provenance manifest

**TL;DR:** This playbook is the step-by-step protocol for any change to HUMMBL's claims provenance manifest (`web/manifest/claims-provenance.json`). It covers 5 change types (add, update, validate, retract, remove), the roles involved (requester, validator, promoter), the receipts required, and the verification steps. Every claim change must follow this protocol; deviating from the protocol is a CONSTITUTION §3.1 violation. The playbook uses the helper scripts shipped in wave 2 (`scripts/add_claims.py`, `scripts/emit_receipt.py`, `scripts/update_manifest.py`).

---

## 1. When to use this playbook

Use this playbook whenever you need to:

- **Add** a new claim to the manifest (a new factual statement on a HUMMBL page, in an artifact, or in a public doc)
- **Update** an existing claim (correct a quote, change a status, refine the source)
- **Validate** a claim that was previously unproven (find a source, mark it validated)
- **Retract** a claim that is wrong (mark it invalidated or misleading)
- **Remove** a claim that is no longer relevant (archive it, do not silently delete)

Do NOT use this playbook for:

- Edits to non-claim content (prose, formatting, structure) — those are normal edits
- Edits to the manifest's summary counts — those are recomputed by `add_claims.py`
- Edits to the manifest's `generated_at` timestamp — those are recomputed by `add_claims.py`

---

## 2. Roles

| Role                | Who                                       | Authority                                                                 |
| ------------------- | ----------------------------------------- | ------------------------------------------------------------------------- |
| **Requester**       | Any agent or human                        | Proposes a claim change (draft the claim, propose the add/update/retract) |
| **Validator**       | Steward (Operator or delegated agent)       | Verifies the claim against the source, assigns tier and status            |
| **Promoter**        | Principal Agent (Operator)                  | Approves the change for promotion to live (public)                        |
| **Receipt emitter** | Steward (using `scripts/emit_receipt.py`) | Emits the KRINEIA receipt for the change                                  |

A single person can hold multiple roles. Operator as Principal Agent can be requester, validator, promoter, and receipt emitter. Agents can be requesters and receipt emitters; they cannot be promoters (per Doctrine Principle 7).

---

## 3. The 5 change types

### 3.1 Add a new claim

**When:** A new factual statement appears on a HUMMBL page, in an artifact, or in a public doc.

**Steps:**

1. **Draft the claim** — write the claim text, identify the source, extract the source quote, assign a tier (A/B/C), assign a status (validated/unproven).
2. **Pick an ID** — use the prefix convention (e.g., `DO-` for doctrine, `CH-` for charter, `EP-` for evidence pack, `WP-` for white paper). Number sequentially within the prefix.
3. **Write a claims JSON file** — a JSON list of claim dicts, each with: id, page, claim, source, source_quote, verified_date, tier, status. Optional: notes.
4. **Run the helper** — `python scripts/add_claims.py <claims_file.json>`. The helper:
   - Loads the manifest (utf-8, per AGENTS.md §8)
   - Sanitizes any non-ascii in existing claims
   - Checks for ID collisions
   - Extends the claims list
   - Recomputes the summary counts
   - Writes back as utf-8
5. **Validate** — the validator confirms the claim matches the source and the tier is correct.
6. **Promote** — the promoter (PA) approves the change for live.
7. **Emit receipt** — `python scripts/emit_receipt.py claims.added <payload.json>` where the payload documents the add.
8. **Commit** — `git add web/manifest/claims-provenance.json _receipts/krineia/primary.jsonl && git commit`.

**Example payload for the receipt:**

```json
{
  "promoter": "devin",
  "approving_human": "Operator",
  "change_type": "add",
  "claims_added": ["DO-001", "DO-002"],
  "total_claims_after": 197,
  "source_artifact": "docs/artifacts/DOCTRINE_ai_governance.md"
}
```

### 3.2 Update an existing claim

**When:** A claim's source quote needs correction, the source URL changed, the status needs to change (e.g., unproven -> validated), or the tier needs to change (e.g., B -> A after finding a primary source).

**Steps:**

1. **Identify the claim** — find the claim by ID in `web/manifest/claims-provenance.json`.
2. **Edit the claim** — update the relevant field(s). Do NOT change the ID. Do NOT silently change the status from validated to invalidated (that is a retraction, see §3.4).
3. **Update `verified_date`** — set to today's date (UTC).
4. **Add a `notes` field** if not present — explain what changed and why. Example: "Source URL updated; quote unchanged. Tier B -> A after finding primary source."
5. **Validate** — the validator confirms the update is correct.
6. **Promote** — the promoter (PA) approves.
7. **Emit receipt** — `python scripts/emit_receipt.py claims.updated <payload.json>`.
8. **Commit**.

**Example payload:**

```json
{
  "promoter": "devin",
  "approving_human": "Operator",
  "change_type": "update",
  "claims_updated": ["WP-014"],
  "update_description": "Tier B -> A after finding primary source (EU AI Act Article 14)",
  "total_claims_after": 197
}
```

### 3.3 Validate an unproven claim

**When:** A claim was marked `unproven` (tier C internal estimate) and a source has been found that supports it.

**Steps:**

1. **Identify the claim** — find the claim by ID; confirm status is `unproven`.
2. **Find the source** — locate a primary (tier A) or secondary (tier B) source that supports the claim.
3. **Extract the source quote** — copy the exact text from the source that supports the claim.
4. **Update the claim** — change `tier` to A or B, change `status` to `validated`, update `source` and `source_quote`, update `verified_date`.
5. **Add a `notes` field** — explain: "Validated from unproven. Source: <citation>."
6. **Validate** — the validator confirms.
7. **Promote** — the promoter (PA) approves.
8. **Emit receipt** — `python scripts/emit_receipt.py claims.validated <payload.json>`.
9. **Commit**.

### 3.4 Retract a wrong claim

**When:** A claim is wrong — the source does not support it, the source is retracted, or the claim is misleading.

**Steps:**

1. **Identify the claim** — find the claim by ID.
2. **Determine the new status** — `invalidated` (the claim is wrong) or `misleading` (the claim is technically true but misleading).
3. **Update the claim** — change `status` to `invalidated` or `misleading`, update `verified_date`, add a `notes` field explaining: "Retracted because <reason>. Source: <evidence of the error>."
4. **Do NOT delete the claim** — the claim stays in the manifest with the new status. This preserves the audit trail.
5. **Check downstream** — if the claim was cited in an artifact, update the artifact to remove or correct the citation.
6. **Validate** — the validator confirms the retraction is correct.
7. **Promote** — the promoter (PA) approves.
8. **Emit receipt** — `python scripts/emit_receipt.py claims.retracted <payload.json>`.
9. **Commit**.
10. **Bus STATUS** — post a bus STATUS message describing the retraction (transparency).

**Example payload:**

```json
{
  "promoter": "devin",
  "approving_human": "Operator",
  "change_type": "retract",
  "claims_retracted": ["XX-007"],
  "retraction_reason": "Source does not support claim; source quote was misread",
  "downstream_artifacts_updated": [
    "docs/artifacts/WHITE_PAPER_governance_infrastructure.md"
  ],
  "total_claims_after": 197
}
```

### 3.5 Remove an obsolete claim

**When:** A claim is no longer relevant — the page it was on no longer exists, the artifact was archived, or the claim is about a deprecated feature.

**Steps:**

1. **Identify the claim** — find the claim by ID.
2. **Confirm obsolescence** — the page no longer exists, or the artifact is archived, or the feature is deprecated.
3. **Move the claim to the archive** — add the claim to `web/manifest/claims-archive.jsonl` (append-only JSONL of removed claims, with `removed_date` and `removal_reason`).
4. **Remove from the manifest** — delete the claim from `web/manifest/claims-provenance.json`.
5. **Update the summary** — recompute the summary counts (or run `add_claims.py` with an empty list to recompute).
6. **Validate** — the validator confirms the removal is correct.
7. **Promote** — the promoter (PA) approves.
8. **Emit receipt** — `python scripts/emit_receipt.py claims.removed <payload.json>`.
9. **Commit**.

**Important:** Do NOT silently delete a claim. Every removal must go through this protocol, be archived, and emit a receipt. Silent deletion is a CONSTITUTION §3.4 violation (claims provenance manifest integrity).

---

## 4. Tier assignment guide

| Tier  | What it is        | Examples                                                            | Default status                                   |
| ----- | ----------------- | ------------------------------------------------------------------- | ------------------------------------------------ |
| **A** | Primary source    | Code, regulations, CONSTITUTION, official docs, the artifact itself | `validated`                                      |
| **B** | Secondary source  | Analyst reports, competitive analysis, news articles, blog posts    | `validated` (with refresh cadence note)          |
| **C** | Internal estimate | Inferences, projections, assumptions, calculations                  | `unproven` (with notes explaining the inference) |

### When to use which tier

- **Tier A** — the source is the thing itself. If the claim is "the CONSTITUTION §3.1 says X", the source is `CONSTITUTION.md §3.1` and the tier is A.
- **Tier B** — the source is a secondary report about the thing. If the claim is "the AI governance market is $X billion", the source is an analyst report and the tier is B. Mark with a refresh cadence note (e.g., "Refresh quarterly").
- **Tier C** — the source is HUMMBL's own inference. If the claim is "HUMMBL's SOM target is $0.5-1M ARR", the source is HUMMBL's market analysis (tier C internal estimate) and the status is `unproven`. Always mark tier C as `unproven` with notes explaining the inference.

### Tier upgrades

A tier C claim can be upgraded to tier B or A when a stronger source is found. Use the update protocol (§3.2) and note the upgrade in the `notes` field.

---

## 5. Receipt requirements

Every claim change must emit a KRINEIA receipt. The receipt event types:

| Change type                                   | Receipt event      |
| --------------------------------------------- | ------------------ |
| Add                                           | `claims.added`     |
| Update                                        | `claims.updated`   |
| Validate (unproven -> validated)              | `claims.validated` |
| Retract (validated -> invalidated/misleading) | `claims.retracted` |
| Remove                                        | `claims.removed`   |

The receipt payload must include:

- `promoter` — who is making the change (agent name)
- `approving_human` — the Principal Agent (Operator)
- `change_type` — add/update/validate/retract/remove
- The list of claim IDs affected
- `total_claims_after` — the new total
- A description of the change (what and why)
- For retractions: the retraction reason and any downstream artifacts updated

---

## 6. Verification

After any claim change, verify:

1. **The manifest is valid JSON** — `python3 -c "import json; json.loads(open('web/manifest/claims-provenance.json', encoding='utf-8').read())"`.
2. **The summary counts are correct** — `python3 -c "import json; d=json.loads(open('web/manifest/claims-provenance.json', encoding='utf-8').read()); print(d['summary'])"`.
3. **The receipt chain is intact** — run the chain verification script from `EVIDENCE_PACK_fleet_rollout.md` E1.
4. **No claim is silently unverified** — every claim has a status in {validated, unproven, invalidated, misleading, not_checked}.
5. **The change is committed** — `git status` shows the manifest, receipt chain, and any updated artifacts.

---

## 7. Common mistakes (and how to avoid them)

### M1: Forgetting `encoding="utf-8"`

**Mistake:** A Python script reads or writes the manifest without `encoding="utf-8"`. On Windows, this corrupts the file (cp1252 default).

**Fix:** Always use `encoding="utf-8"` (per AGENTS.md §8). The helper scripts enforce this. If writing a custom script, follow the convention.

### M2: Silently deleting a claim

**Mistake:** A claim is wrong, so the editor deletes it from the manifest.

**Fix:** Never delete. Retract (§3.4) or remove with archive (§3.5). The audit trail must be preserved.

### M3: Marking a tier C claim as `validated`

**Mistake:** An internal estimate is marked `validated` because the editor is confident.

**Fix:** Tier C claims are `unproven` by definition. If you have a source, it is tier A or B, not C. Upgrade the tier, do not validate a tier C claim.

### M4: Changing a status without a receipt

**Mistake:** A claim's status is changed from `validated` to `invalidated` without emitting a receipt.

**Fix:** Every status change requires a receipt (§5). Use `scripts/emit_receipt.py`.

### M5: Using a non-ascii character in a claim

**Mistake:** A claim contains an arrow (→), checkmark (✓), or em-dash (—). On Windows, this can corrupt the file if a script does not use `encoding="utf-8"`.

**Fix:** Use ascii equivalents (`->`, `[OK]`, `--`). The `add_claims.py` helper sanitizes non-ascii in existing claims, but new claims should be ascii from the start.

### M6: Picking a duplicate ID

**Mistake:** A new claim uses an ID that already exists.

**Fix:** The `add_claims.py` helper checks for ID collisions and refuses to add duplicates. Always use the helper, not manual edits.

---

## 8. Boundary disclaimer

This playbook is HUMMBL's internal protocol for claim changes. It is not a regulation or a standard. Other organizations may adopt different protocols. HUMMBL's protocol is designed to enforce CONSTITUTION §3.1 (public claim honesty) and §3.4 (claims provenance manifest integrity).

The playbook does not make HUMMBL's claims true. It makes HUMMBL's claims auditable. A reader can verify any claim by inspecting the cited source. If the source does not support the claim, the reader should open an issue and the claim will be retracted per §3.4.

---

## 9. How to verify this playbook

A reader can re-verify the playbook's claims by:

1. **The helper scripts exist** — `ls scripts/add_claims.py scripts/emit_receipt.py scripts/update_manifest.py`.
2. **The manifest is valid** — run the verification commands in §6.
3. **The receipt chain is intact** — run the chain verification from `EVIDENCE_PACK_fleet_rollout.md` E1.
4. **The CONSTITUTION invariants are present** — `grep "Public claim honesty" CONSTITUTION.md` and `grep "Claims provenance manifest integrity" CONSTITUTION.md`.
5. **The utf-8 convention is documented** — `grep "utf-8" AGENTS.md`.

If any verification fails, open an issue at `hummbl-io/hummbl-production/issues`.

---

## References

- CONSTITUTION: `CONSTITUTION.md` (§3.1 public claim honesty, §3.4 manifest integrity, §6 receipt-triggering changes)
- AGENTS.md: `AGENTS.md` (§8 utf-8 encoding convention)
- Helper scripts: `scripts/add_claims.py`, `scripts/emit_receipt.py`, `scripts/update_manifest.py`
- Claims manifest: `web/manifest/claims-provenance.json`
- Claims archive: `web/manifest/claims-archive.jsonl` (created when first claim is removed)
- KRINEIA receipt chain: `_receipts/krineia/primary.jsonl`
- Doctrine: `docs/artifacts/DOCTRINE_ai_governance.md` (Principle 1 honesty, Principle 6 receipts)
- Evidence pack: `docs/artifacts/EVIDENCE_PACK_fleet_rollout.md` (E1 receipt chain verification, E2 claims manifest verification)
- Supporting private records are omitted from this public tree; claims depending on them cannot be independently re-verified here.

---

## Authority boundary

**Operator** is the human **Principal Agent** for HUMMBL — the goal-owning, value-bearing, accountable agent. **Devin** (and other software agents: Codex, Claude Code, Gemini, OpenCode, Kai, Apex, Nexus, Auditor, Hermes) are **delegated drafting, research, and execution systems**. They can draft, collect, compare, format, inspect, and surface — they cannot confer strategic authority on themselves, promote drafts to live, publish external claims, or redefine strategic goals. This playbook was drafted by Devin at the direction of the Principal Agent, based on the CONSTITUTION, the wave 1 retrospective (F1, P1, P3), and the helper scripts shipped in wave 2, and was promoted to live (public) by Principal Agent decision on 2026-06-23. This playbook is the canonical protocol for claim changes; deviations are CONSTITUTION §3.1 violations. This document is **public** — it is intended for external readers (agents, operators, customers, assessors) and may be published on hummbl.io.
