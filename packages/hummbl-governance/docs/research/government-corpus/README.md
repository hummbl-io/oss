# Government Corpus Doctrine

**Status:** PROPOSED — requires human review for canonical status
**Origin:** hummbl-io/hummbl-governance#81
**Steward:** HUMMBL Research Institute

---

## 1. Purpose

The governance research lane needs a structured government corpus: one country dossier per included country and a bibliography shelf per continent. Government research extracts primitives for admission, authority, execution, receipts, dispute resolution, archives, succession, and failure modes.

**Core principle:** Government research extracts primitives and does not import political legitimacy claims wholesale.

---

## 2. Country Dossier Schema

```yaml
country_id: "country-001"
country_name: "Example"
iso_code: "EX"
continent: "Example Continent"
constitutional_form: "republic"  # republic, monarchy, federation, etc.
institutions:
  executive:
    name: "Executive Body"
    authority: "elected"
    term: "4 years"
  legislative:
    name: "Legislative Body"
    authority: "elected"
    term: "4 years"
  judicial:
    name: "Judicial Body"
    authority: "appointed"
    term: "lifetime"
source_stack:
  - "constitution"
  - "statutes"
  - "case law"
  - "regulations"
  - "treaties"
hummbl_primitive_mapping:
  admission: "citizenship process"
  authority: "separation of powers"
  execution: "executive orders"
  receipts: "official gazette"
  dispute_resolution: "judicial review"
  archives: "national archives"
  succession: "election process"
  failure_modes: "constitutional crisis"
transfer_limits:
  - "cultural context may not transfer"
  - "historical period may not apply"
failure_modes:
  - "constitutional crisis"
  - "coup d'état"
  - "succession dispute"
corpus_status: "candidate"  # candidate, source-seeded, primary-sourced, mapped, reviewed, canonical
```

---

## 3. Corpus Lifecycle Statuses

| Status | Meaning |
|--------|---------|
| `candidate` | Country identified for inclusion but not yet researched |
| `source-seeded` | Basic sources identified (constitution, key statutes) |
| `primary-sourced` | Primary sources read and indexed |
| `mapped` | HUMMBL primitive mapping completed |
| `reviewed` | Human review completed |
| `canonical` | Accepted as canonical reference |

---

## 4. Country Inclusion Gates

A country is included in the corpus when:

1. **Constitutional document is available** — written constitution or equivalent
2. **Institutional structure is identifiable** — executive, legislative, judicial
3. **Source stack is accessible** — primary sources can be read
4. **HUMMBL primitive mapping is feasible** — at least 5 of 8 primitives can be mapped

---

## 5. Continent Bibliography Shells

```
docs/research/government-corpus/
  README.md                    — this doctrine
  TEMPLATE.md                  — country dossier template
  africa/
    README.md                  — Africa bibliography
  americas/
    README.md                  — Americas bibliography
  asia/
    README.md                  — Asia bibliography
  europe/
    README.md                  — Europe bibliography
  oceania/
    README.md                  — Oceania bibliography
  antarctica/
    README.md                  — Antarctica bibliography
  global/
    README.md                  — Global and international sources
```

---

## 6. Minimum Canonical Packet

A country dossier must include all of the following before `canonical` status:

- [ ] Constitutional form identified
- [ ] All 3 institutions (executive, legislative, judicial) documented
- [ ] Source stack with at least 3 primary sources
- [ ] At least 5 of 8 HUMMBL primitives mapped
- [ ] Transfer limits documented
- [ ] At least 2 failure modes documented
- [ ] Human review completed

---

## 7. HUMMBL Primitive Extraction

Government research extracts the following primitives:

| Primitive | What to Extract |
|-----------|----------------|
| Admission | How new members are admitted (citizenship, membership) |
| Authority | How authority is structured and limited |
| Execution | How decisions are executed |
| Receipts | How actions are recorded and made verifiable |
| Dispute Resolution | How conflicts are resolved |
| Archives | How records are preserved |
| Succession | How power transitions occur |
| Failure Modes | How the system fails (crises, coups, collapse) |

---

## 8. Transfer Limits

Each country dossier must document transfer limits:

- **Cultural context** — what works in one culture may not transfer
- **Historical period** — what worked historically may not apply today
- **Scale** — what works at national scale may not work at agent scale
- **Enforcement** — government enforcement mechanisms differ from agent governance

---

## 9. Cross-References

- **Cosmic Corpus doctrine:** hummbl-governance#82
- **Simulation-governance prior-art corpus:** hummbl-governance#1018
- **Simulation Affordance template:** hummbl-governance#83
- **Memory Civilization registries:** hummbl-governance#79

---

**Last updated:** 2026-06-23
**Prepared by:** Devin
**Approval required:** Human review for canonical status
