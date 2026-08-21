# Constitution Bounded Remediation Packet v0.1

**Status: P1 BOUNDED REMEDIATION — RE-VERIFY BEFORE MUTATION — NON-CANONICAL**

Parent: hummbl-io/hummbl-governance#220
Issue: hummbl-io/hummbl-governance#221

## Objective

Repair current constitutional truth and incorporation defects without
broad constitutional redesign.

## Finding 1: hummbl-governance schema-count claim

### Pre-state

`hummbl-governance/CONSTITUTION.md` line 27:

> **Contracts are canonical.** The 78 governance schemas are the
> source of truth.

### Source-of-truth command

```bash
cd ~/projects/PROJECTS/hummbl-governance
find . -name "*.schema.json" -not -path "*/.git/*" 2>/dev/null | wc -l
# Result: 120
```

### Classification

**C1 — FALSE_CONSTITUTIONAL_CLAIM**

The hard-coded count "78" does not match the actual 120 schema files.
Furthermore, the `contracts/` symlink is broken (points to
`~/projects/PROJECTS/platform/agent-os/contracts` which does not
exist).

### Proposed correction

Replace the hard-coded count with an authoritative-source reference:

> **Contracts are canonical.** Governance schemas in the tracked
> schema directories are the source of truth. Code conforms to
> schemas; schemas are never silently mutated to satisfy code. The
> current schema count is governed by `docs/SCHEMA_COUNT_AUTHORITY.md`
> (to be created) or verified via
> `find . -name "*.schema.json" -not -path "*/.git/*" | wc -l`.

### Amendment authority

`hummbl-governance/CONSTITUTION.md` requires: a PR, an ADR under
`docs/adr/`, a KRINEIA receipt, and human approval (Reuben Bowlby).

### Post-state (target)

Constitution no longer contains a hard-coded schema count. Schema
count is derived from the authoritative source.

### Execution receipt

**NOT YET EXECUTED** — This packet proposes the correction. Execution
requires a repo-specific PR in `hummbl-governance` with ADR and KRINEIA
receipt.

## Finding 2: hummbl-governance broken normative references

### Pre-state

`hummbl-governance/CONSTITUTION.md` lines 43-45:

```
- `hummbl_governance/contracts/`
- `hummbl_governance/schemas/`
- `hummbl_governance/services/kill_switch_core.py`
```

### Source-of-truth commands

```bash
cd ~/projects/PROJECTS/hummbl-governance
ls -la hummbl_governance/contracts/
# Result: No such file or directory

ls hummbl_governance/schemas/
# Result: Exists (5 files)

ls hummbl_governance/services/kill_switch_core.py
# Result: No such file or directory

ls hummbl-governance/hummbl_governance/services/kill_switch_core.py
# Result: Exists (canonical path)

readlink contracts
# Result: ~/projects/PROJECTS/platform/agent-os/contracts (broken symlink)

ls ~/projects/PROJECTS/platform/agent-os/contracts/
# Result: No such file or directory
```

### Classification

**C2 — BROKEN_INCORPORATION_REFERENCE**

- `hummbl_governance/contracts/` — does not exist (broken symlink at root `contracts/`)
- `hummbl_governance/schemas/` — exists but is the stale root directory
- `hummbl_governance/services/kill_switch_core.py` — does not exist at this path
- Canonical kill_switch path: `hummbl-governance/hummbl_governance/services/kill_switch_core.py`

### Proposed correction

Update normative references to canonical paths:

```
- `hummbl-governance/hummbl_governance/schemas/`
- `hummbl-governance/hummbl_governance/services/kill_switch_core.py`
```

Remove reference to `hummbl_governance/contracts/` (the directory does not
exist and the symlink is broken). If contracts are canonical, identify
the actual canonical contract location or remove the claim.

### Amendment authority

Same as Finding 1: PR + ADR + KRINEIA receipt + Reuben approval.

### Post-state (target)

All normative references resolve from the declared repository root.

### Execution receipt

**NOT YET EXECUTED** — requires repo-specific PR in `hummbl-governance`.

## Finding 3: hummbl-governance amendment path reference

### Pre-state

`hummbl-governance/CONSTITUTION.md` line 70:

> Changes to this constitution require: a PR, an ADR under `docs/adr/`,
> a KRINEIA receipt, and human approval (Reuben Bowlby).

### Source-of-truth command

```bash
cd ~/projects/PROJECTS/hummbl-governance
ls docs/adr/
# Result: Exists (multiple ADR subdirectories)
```

### Classification

**No defect found.** `docs/adr/` exists and contains ADRs.

### Proposed correction

None needed.

## Finding 4: hummbl-research dependency invariant

### Pre-state

The 2026-07-10 audit reported that `hummbl-research/CONSTITUTION.md`
contained a "Stdlib-only runtime" invariant inconsistent with actual
runtime dependencies.

### Source-of-truth commands

```bash
cd ~/projects/PROJECTS/hummbl-research
grep "Stdlib-only\|stdlib-only\|standard library" CONSTITUTION.md
# Result: (no matches)

sed -n '29p' CONSTITUTION.md
# Result: 4. **Declared runtime dependencies.** Production code uses
# the dependencies declared in `pyproject.toml [project.dependencies]`.
# Adding an undeclared runtime dependency is a constitutional violation.

python3 -c "
import tomllib
with open('pyproject.toml','rb') as f:
    d = tomllib.load(f)
print(d['project']['dependencies'])
"
# Result: ['networkx>=3.2,<4.0', 'numpy>=1.24.0,<2.0', 'scipy>=1.10.0,<2.0',
#          'google-cloud-aiplatform>=1.38.0,<2.0', 'vertexai>=1.38.0,<2.0',
#          'google-generativeai>=0.3.0,<1.0']
```

### Classification

**No defect found (already remediated).**

The constitution correctly states "Declared runtime dependencies"
rather than "Stdlib-only runtime." The pyproject.toml declares 6
runtime dependencies (networkx, numpy, scipy, google-cloud-aiplatform,
vertexai, google-generativeai). The constitution is consistent with
the actual dependency posture.

### Proposed correction

None needed. The audit finding appears to have been already remediated.

## Summary of findings

| # | Repo | Finding | Classification | Status |
|---|------|---------|---------------|--------|
| 1 | hummbl-governance | "78 governance schemas" hard-coded count | C1 — FALSE_CONSTITUTIONAL_CLAIM | Proposed correction ready |
| 2 | hummbl-governance | Broken normative paths (contracts/, services/) | C2 — BROKEN_INCORPORATION_REFERENCE | Proposed correction ready |
| 3 | hummbl-governance | docs/adr/ amendment path | No defect | No action needed |
| 4 | hummbl-research | "Stdlib-only runtime" invariant | No defect (already remediated) | No action needed |

## Proposed repo-specific amendment PRs

### PR 1: hummbl-governance constitution amendment

**Scope**: Fix findings 1 and 2 in `hummbl-governance/CONSTITUTION.md`

**Changes**:
1. Replace "The 78 governance schemas" with authoritative-source reference
2. Update normative file paths to canonical locations
3. Remove or fix broken `contracts/` reference

**Requirements**:
- PR in `hummbl-governance` repo
- ADR under `docs/adr/`
- KRINEIA receipt
- Reuben approval

**NOT YET EXECUTED** — This packet proposes the correction. The
actual PR must be created in the `hummbl-governance` repo following its
amendment requirements.

## Prohibited shortcuts (verified not taken)

- [x] No empty `contracts/`, `schemas/`, `services/`, or `docs/adr/` paths created
- [x] No unverified count substituted for "78"
- [x] No valid dependency invariant weakened
- [x] No unrelated fleet constitution edits combined into one PR

## Verification expectations

For each finding:

| Finding | Pre-state | Source command | Classification | Correction | Authority | Post-state | Receipt |
|---------|-----------|---------------|---------------|-----------|-----------|-----------|---------|
| 1 | "78 schemas" | `find ... *.schema.json` → 120 | C1 | Replace with authoritative source | hummbl-governance PR+ADR+KRINEIA+Reuben | Pending | Pending |
| 2 | Broken paths | `ls` commands | C2 | Update to canonical paths | hummbl-governance PR+ADR+KRINEIA+Reuben | Pending | Pending |
| 3 | docs/adr/ | `ls docs/adr/` | No defect | None | N/A | N/A | N/A |
| 4 | Stdlib-only | `grep` + `tomllib` | No defect | None | N/A | N/A | N/A |

## Residual ambiguity escalated to Reuben

1. **Broken `contracts/` symlink**: The `contracts/` symlink at
   hummbl-governance root points to `~/projects/PROJECTS/platform/agent-os/contracts`
   which does not exist. Should this symlink be removed, or should
   the target be restored? This requires Reuben's decision.

2. **Canonical contract location**: If contracts are canonical (per
   the constitution), where is the actual canonical contract
   directory? The constitution references `hummbl_governance/contracts/`
   which does not exist. Reuben must identify the actual source of
   truth or confirm that contracts are no longer canonical.

3. **Schema count authority**: Should `hummbl-governance` create a
   `docs/SCHEMA_COUNT_AUTHORITY.md` file (similar to
   `docs/TEST_COUNT_AUTHORITY.md` in hummbl-governance) to govern
   the schema count? Reuben must decide.

## Acceptance criteria

- [x] Every scoped claim/path is re-verified and classified
- [ ] hummbl-governance no longer contains false hard-coded schema authority/count claims — **PROPOSED, NOT YET EXECUTED**
- [ ] hummbl-governance normative references resolve from declared repository root — **PROPOSED, NOT YET EXECUTED**
- [x] hummbl-research dependency invariant matches verified current runtime state
- [x] No empty placeholder paths are created
- [ ] Repo-specific amendment and receipt rules are satisfied — **PENDING EXECUTION**
- [x] Residual ambiguity is escalated to Reuben rather than guessed
- [ ] Parent #220 receives links to all PRs and post-merge verification receipts — **PENDING EXECUTION**

## References

- Parent: hummbl-io/hummbl-governance#220
- Issue: hummbl-io/hummbl-governance#221
- Authority packet: hummbl-io/hummbl-governance#222
- Archetype packet: hummbl-io/hummbl-governance#223
