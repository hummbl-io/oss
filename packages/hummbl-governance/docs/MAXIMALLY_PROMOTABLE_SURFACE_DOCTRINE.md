# Maximally Promotable Surface Doctrine

**Status:** PROPOSED — requires human review before binding
**Origin:** hummbl-io/hummbl-governance#92
**Steward:** HUMMBL Research Institute

---

## 1. Definition

A **Maximally Promotable Surface** (MPS) is a governance primitive for a repository, document, or artifact set designed from inception to be promotable from private to public without leaking internal operating state.

An MPS is not merely "a public repo." It is a surface where every artifact has a defined promotion status, every private reference has a redaction path, and every example has a synthetic replacement ready.

---

## 2. Key Distinctions

| Term | Definition |
|------|-----------|
| **Surface** | A repository or document set with a defined boundary and promotion target. |
| **Artifact** | A single file, document, schema, or code module within a surface. |
| **Receipt** | A cryptographic proof of an action, decision, or review. |
| **Example** | A synthetic or redacted artifact used for teaching or documentation. |
| **Canon** | An artifact elevated to reference status through review and ratification. |

---

## 3. Promotion Ladder

Every artifact in an MPS has a promotion status:

```
private → internal → redacted → synthetic → public → canonical
```

| Status | Meaning | Visibility |
|--------|---------|-----------|
| `private` | Contains sensitive data — no public form | Internal only |
| `internal` | OK in internal docs, not for public release | Internal only |
| `redacted` | Public form with redactions applied | Public (with redactions) |
| `synthetic` | Replaced with a synthetic fixture | Public (synthetic) |
| `public` | Safe to publish as-is | Public |
| `canonical` | Elevated to reference pattern through review | Public (reference) |

### Promotion Gates

Moving up the ladder requires:

1. **private → internal**: No gate (internal is the default for non-sensitive work)
2. **internal → redacted**: Redaction review — identify and remove private references
3. **redacted → synthetic**: Synthetic replacement — create a fixture that teaches the same pattern
4. **synthetic → public**: Public review — verify no private context leaked
5. **public → canonical**: Canon review — peer review and ratification

---

## 4. Required Fields for a Surface

Every MPS must declare:

| Field | Purpose |
|-------|---------|
| `purpose` | What this surface teaches or provides |
| `source_inputs` | What internal artifacts feed this surface |
| `private_boundaries` | What must never appear in any form (public or redacted) |
| `redaction_rules` | How private references are redacted |
| `example_policy` | Whether examples are synthetic, redacted, or original |
| `receipt_policy` | How receipts are handled (public, redacted, or internal-only) |
| `authority_owner` | Who has authority to change promotion status |
| `promotion_status` | Current status of the surface (private, internal, public) |

---

## 5. Redaction and Synthetic Example Policy

### Redaction Rules

1. **Real repo names** → replace with `hummbl-io/example` or `org/example-repo`
2. **Agent identities** → replace with `agent-alpha`, `agent-beta`, etc.
3. **Internal paths** → replace with `/path/to/repo` or `/path/to/artifact`
4. **Issue numbers** → replace with sequential synthetic numbers (#1, #2, #3)
5. **Commit SHAs** → replace with synthetic SHAs (`abc123def456...`)
6. **Timestamps** → replace with synthetic timestamps (`2026-01-01T00:00:00Z`)
7. **Bus messages** → replace with synthetic message content
8. **Cost data** → replace with synthetic budget amounts

### Synthetic Example Policy

- Synthetic examples must teach the **same pattern** as the original
- Synthetic examples must not contain **any** real data
- Synthetic examples must be **deterministic** (same input → same output)
- Synthetic examples must be **labeled** as synthetic in the artifact metadata

---

## 6. Examples

### IssueOps Controller (hummbl-governance#978)
- **Surface:** `hummbl-io/hummbl-issueops` (proposed)
- **Purpose:** Teach Agentic CI/CD patterns for issue management
- **Source inputs:** hummbl-governance IssueOps controller, run receipts, dispatch pods
- **Private boundaries:** Real issue content, agent identities, bus messages, cost data
- **Redaction rules:** Replace all real names, paths, and identifiers with synthetic equivalents
- **Example policy:** Synthetic required — no redacted internal receipts without synthetic replacement
- **Receipt policy:** Schema is public; receipt content is internal-only; synthetic receipts are public
- **Authority owner:** Reuben Bowlby (operator)
- **Promotion status:** private (proposed → public after redaction review)

### Repo Standard (arbiter#86)
- **Surface:** `hummbl-io/hummbl-governance` docs
- **Purpose:** Define HUMMBL Repo Standard v0.1 for all repos
- **Source inputs:** arbiter repo_standard_audit.py, fixture repos
- **Private boundaries:** None — this is already public doctrine
- **Redaction rules:** N/A
- **Example policy:** Original (fixture repos are already synthetic)
- **Receipt policy:** Public
- **Authority owner:** HUMMBL Research Institute
- **Promotion status:** public

### Governance ADRs
- **Surface:** `hummbl-io/hummbl-governance/docs/adr/`
- **Purpose:** Document architecture decisions
- **Source inputs:** Internal ADRs from hummbl-governance
- **Private boundaries:** ADRs that reference internal topology or strategy
- **Redaction rules:** Replace internal references with generic terms
- **Example policy:** Redacted where needed, otherwise original
- **Receipt policy:** Public (ADRs are decisions, not receipts)
- **Authority owner:** HUMMBL Research Institute
- **Promotion status:** public (individual ADRs may be private)

---

## 7. Anti-Patterns

1. **Dumping private receipts** — Publishing internal receipts without redaction or synthetic replacement. Receipts contain agent identities, issue content, and internal paths.

2. **Claiming public canon from unreviewed internal work** — Elevating an internal pattern to "canonical" without peer review and ratification. Canon requires explicit review.

3. **Exposing operator-only decision logs** — Publishing decision logs that contain operator reasoning, strategy, or private context. Decisions are public; reasoning is internal.

4. **Redaction without synthetic replacement** — Redacting content without providing a synthetic example that teaches the same pattern. Redaction alone creates gaps in teaching.

5. **Promotion without receipt** — Changing promotion status without a receipt documenting the review and decision. Every promotion requires a receipt.

6. **Mixing private and public in the same artifact** — Having private and public content in the same file without clear separation. Each artifact must have a single promotion status.

---

## 8. Cross-References

- **IssueOps repo creation packet:** hummbl-governance#1021
- **Promotion-safety rubric:** arbiter#89
- **IssueOps controller:** hummbl-governance#978
- **Review surface and write boundary:** hummbl-governance#981
- **Agentic GitHub Actions vocabulary:** hummbl-governance#196
- **Dispatch pod claim and receipt flow:** hummbl-governance#195
- **Extended IssueOps run receipts:** hummbl-governance#1023

---

**Last updated:** 2026-06-23
**Prepared by:** Devin
**Review required:** Human review before binding
