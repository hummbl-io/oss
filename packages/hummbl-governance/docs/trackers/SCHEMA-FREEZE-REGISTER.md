# Schema Freeze Register

One row per schema that has or needs a freeze gate. Columns: schema, repo, current status,
freeze deadline, sign-off owner, acceptance artifacts required.

**Statuses**: DRAFT · FREEZE PENDING · STABLE (frozen) · SUPERSEDED

---

## Active freeze gates

### Krineia governance receipt schema
| Field | Value |
|-------|-------|
| Schema file | `krineia/RECEIPT_SCHEMA.md` |
| Repo | `HUMMBL/krineia` |
| Status | **FREEZE PENDING** |
| Deadline | **May 15, 2026** (LOI gate) |
| Sign-off owner | Reuben Bowlby |
| Acceptance artifacts | `RECEIPT_SCHEMA.md` status → STABLE v1.0; `INVARIANTS.md` written; `tools/verify_chain.py` passing; `daemon/verum_daemon.py` committed; `tests/test_verify_chain.py` passing; `git tag v1.0.0` |
| Blocking | LOI counterparty agreement; `hummbl-governance` receipt generation; `hummbl-legal` audit trail integration; `hummbl-gaas` Krineia API endpoint |
| Notes | Schema field resolution: `state.event` (dotted lowercase) is canonical; `state.type` (uppercase) from earlier draft is superseded |

---

## Upcoming / planned

### hummbl-bus message format
| Field | Value |
|-------|-------|
| Schema file | `hummbl-bus/contracts/bus_message.json` (proposed) |
| Repo | `HUMMBL/hummbl-bus` |
| Status | **DRAFT** |
| Deadline | TBD (blocking Chief-of-Staff v1) |
| Sign-off owner | Reuben Bowlby |
| Acceptance artifacts | Schema file exists; ADR written; `hummbl-bus` PyPI readiness confirmed |
| Notes | Bus file permissions (0600) must also be confirmed before PyPI claim |

### hummbl-contracts schema versions
| Field | Value |
|-------|-------|
| Schema file | `hummbl-contracts/contracts/` (directory) |
| Repo | `HUMMBL/hummbl-contracts` |
| Status | **DRAFT** |
| Deadline | TBD |
| Sign-off owner | Reuben Bowlby |
| Acceptance artifacts | All contract schemas versioned; breaking-change policy ADR written |
| Notes | SemVer major bump policy already in AGENTS.md but no formal ADR |

---

## Frozen (stable)

_(none yet)_
