# Controlled Lexicon — hummbl-bus

**Status:** DRAFT — proposed rectification of names (v2, post-exploration)
**Date:** 2026-08-15
**Author:** devin (glm-5-2-high)
**Supersedes:** hummbl-governance `docs/reference/COORDINATION_LEXICON.md` (2026-03-02, stale)
**Related:**
- `DOCTRINE.md` §2 (6 terms, incomplete — needs update to reference this doc)
- `~/.agents/rules/bus-lexicon.md` (244 lines, CANONICAL operational source — this doc formalizes what that doc governs)
- `~/.agents/rules/bus-protocol.md` (68 lines, CANONICAL protocol mechanics)
- `~/.agents/ROSTER.md` (201 lines, CANONICAL agent identities)
- `FLEET_VOCABULARY_MAP.md` (fleet-facing index of all vocabulary surfaces)

---

## 0. The Problem

The bus vocabulary was borrowed from three sources without a controlled
lexicon:

1. **Military (NATO/US Staff & Command)**: SITREP, SPOTREP, FRAGO, WARNO,
   AAR, INTEL, DISPATCH, DIRECTIVE
2. **Software engineering**: STATUS, ACK, ERROR, WARN, HEARTBEAT, BLOCKED,
   COMPLETE, CANCEL, HOLD, RESUME, TERMINATE, REGISTER, REDIRECT, REQUEST,
   QUERY, DONE
3. **Governance/ADR**: DECISION, VETO, APPROVE, REJECT, REVIEW, PROPOSAL,
   AUDIT, COMPLIANCE_SCORE, TRUST_REPORT

This is a rectification-of-names problem. Borrowed terms carry baggage:
military terms imply specific report structures the bus doesn't enforce, SE
terms have established meanings that may not map cleanly, and the novel
concepts (HRSI_CHECKIN, SKILL_INVOKE, lane, stuckness) have no documented
vocabulary at all.

The current state is **78 message types** (24 canonical + 54 legacy), **5
different naming conventions for the same 2 identity concepts**, and **2
drifting schema definitions** (structured event vs Ed25519 envelope).

---

## 1. Taxonomic Survey (what exists)

### 1.1 Message Type Etymology

| Source family | Terms | Baggage |
|---|---|---|
| **Military (S&C)** | SITREP, SPOTREP, FRAGO, WARNO, AAR, INTEL, DISPATCH, DIRECTIVE | NATO formats with specific structural expectations (5-paragraph order, SALUTE format) that the bus does not enforce. Using the name without the structure is a false promise. |
| **Software engineering** | STATUS, ACK, ERROR, WARN, HEARTBEAT, BLOCKED, COMPLETE, CANCEL, HOLD, RESUME, TERMINATE, REGISTER, REDIRECT, REQUEST, QUERY, DONE, INFO | Established meanings in ticketing, logging, networking. Some conflict: ACK in TCP means "received", in the bus it means "acknowledged and will act". ERROR/WARN/INFO are log levels, not coordination intents. |
| **Governance** | DECISION, VETO, APPROVE, REJECT, REVIEW, PROPOSAL, AUDIT, COMPLIANCE_SCORE, TRUST_REPORT | ADR-style decision records. VETO/APPROVE/REJECT are approval-flow verbs that overlap with each other (VETO = REJECT with authority; APPROVE = ACK with authority). |
| **Novel (HUMMBL)** | HRSI_CHECKIN, SKILL_INVOKE, LATE_SKILL_INVOKE, lane, healed, stuckness, fleet | HRSI is undocumented (no expansion). SKILL_INVOKE is an agent-framework concept. lane/healed/stuckness are WIP-healer terms with no glossary entry. |

### 1.2 Identity Field Inconsistency

The same two concepts (who sent this, who receives this) have **5 naming
conventions** across the codebase:

| Convention | Where used | Problem |
|---|---|---|
| `from` / `to` | TSV columns, `bus_utils.parse_bus_line` | `from` is a Python reserved keyword — cannot be used as a keyword argument |
| `from_id` / `to_id` | `bus_writer.post_message` params, `secure_tsv` | Suffix `_id` implies a database foreign key, but these are agent identity strings, not integer IDs |
| `sender` / `recipient` | `build_structured_event`, `authority.py` | Messaging convention. Inconsistent with TSV column names. |
| `sender_id` / `recipient_id` | `bus_ed25519_verifier`, `bus_security.BusMessage` | Adds `_id` suffix to the messaging convention. Inconsistent with `from_id`/`to_id`. |
| `from_agent` / `to_agent` | `bridge_client`, `bridge_server` | Agent-specific naming. Inconsistent with everything else. |

**Root cause**: Each module was written at a different time by different
agents, each choosing the convention familiar to them. No controlled lexicon
existed to enforce consistency.

### 1.3 Schema Drift

Two independent schema definitions exist for structured bus events:

| Schema | Fields | Where defined |
|---|---|---|
| **Structured event** (`hummbl_bus.event.v1`) | schema, timestamp, sender, recipient, type, content, correlation_id, metadata | `bus_writer.py:996-1009` |
| **Ed25519 signed envelope** | event_id, event_type, correlation_id, sender_id, sender_kind, posted_by, on_behalf_of, authority_source, created_at, body, body_hash, prev_event_hash, key_id, signature | `bus_ed25519_verifier.py:38-52` |

These two schemas share only 2 field names (`correlation_id`, `type`/`event_type`).
They use different names for the same concepts (`sender` vs `sender_id`,
`content` vs `body`, `timestamp` vs `created_at`). The Ed25519 schema defines
fields (`sender_kind`, `posted_by`, `on_behalf_of`, `authority_source`,
`prev_event_hash`) that the structured event schema does not produce.

### 1.4 Message Type Bloat

78 total types (24 canonical + 54 legacy). Many are near-synonyms:

| Concept | Canonical types | Legacy types | Count |
|---|---|---|---|
| Task completion | COMPLETE, TASK_COMPLETE | DONE, RESOLVED, SESSION_COMPLETE | 5 |
| Acknowledgment | ACK, RECEIPT | RECEIPT_ACK, RECEIPT_REJECT | 4 |
| Blocking | BLOCKED | BLOCKER, HOLD | 3 |
| Requesting | QUESTION, PROPOSAL | REQUEST, TASK_REQUEST, QUERY, REQUEST_REVIEW, REQUEST_RETRY, FLEET_QUERY, LEDGER_QUERY | 9 |
| Alerting | ALERT | SAFETY, ERROR, WARN, ESCALATE | 5 |
| Lifecycle | WIP_START, WIP_END, HANDOFF, MILESTONE | CHECKPOINT, PHASE_TRANSITION, HEALTH_TRANSITION, STALE_STATE_RESET, CANCEL, RESUME, TERMINATE, SCHEDULED, REGISTER | 13 |

The 54 legacy types are frozen (read-only), but the 24 canonical types still
contain redundancy: COMPLETE vs TASK_COMPLETE, ALERT vs SAFETY, ACK vs RECEIPT.

### 1.5 HMAC Envelope Opacity

The HMAC signing envelope uses single-letter field names: `{"c": ..., "n": ..., "s": ...}`.

| Field | Meaning | Problem |
|---|---|---|
| `c` | content (the message) | Ambiguous with "checksum", "counter", "command" |
| `n` | nonce | Standard crypto term, but single-letter is unnecessarily opaque |
| `s` | signature | Ambiguous with "secret", "sender", "sequence" |

This is compact but undocumented in DOCTRINE.md §2 (which calls it "HMAC
envelope" without expanding the fields).

---

### 1.6 Actual Usage (exploration finding — updated with full corpus)

**Two analysis windows are documented**:

**Window 1: Local mirror (31 messages, 2026-08-09 to 2026-08-15)** — see
`PHASE_MINUS1_DISCOVERY_REPORT.md` §1 for the raw data. Only 8 of 24
canonical types appeared; this is a low-traffic window.

**Window 2: Full canonical corpus (11,339 messages, 2026-07-26 to
2026-08-15)** — the authoritative analysis. The canonical bus on
`hummbl-vps` has 11,608 lines; analysis via `bus-global.py` bridge.

**Full corpus type distribution** (top 15):

| Type | Count | Intent | Bucket |
|---|---|---|---|
| STATUS | 3,675 | INFORM | CANONICAL |
| SITREP | 2,283 | INFORM | CANONICAL |
| SKILL_INVOKE | 1,269 | TRACE | CANONICAL |
| BLOCKED | 952 | SIGNAL | CANONICAL |
| WIP_START | 492 | TRACE | CANONICAL |
| WIP_END | 450 | TRACE | CANONICAL |
| PROPOSAL | 418 | REQUEST | CANONICAL |
| MILESTONE | 357 | TRACE | CANONICAL |
| REVIEW | 330 | CONFIRM | CANONICAL |
| RECEIPT | 309 | CONFIRM | CANONICAL |
| ALERT | 247 | SIGNAL | CANONICAL |
| QUESTION | 112 | REQUEST | CANONICAL |
| ACK | 112 | CONFIRM | CANONICAL |
| HANDOFF | 100 | TRACE | CANONICAL |
| REVIEW_RESPONSE | 43 | CONFIRM | **UNKNOWN** (unregistered) |

**Bucket summary**:
- 20 of 24 canonical types in use (4 unused: APPROVE, DIRECTIVE, REJECT, VETO — all DECIDE intent)
- 23 of 54 legacy types still being written (P0 drift — legacy should be read-only)
- 14 UNKNOWN types in traffic (11 real, 3 noise from writer bugs)

**Signing rate**: 10% (1,213 of 11,339) — signing is the exception, not the norm.

**Host tag presence**: 49% (5,817 of 11,339 lack `host=` tag).

**Full drift findings** (updated from full corpus):

| Drift | Severity | Evidence |
|---|---|---|
| Signing rate 10% | P0 | 1,213 of 11,339 signed |
| 23 legacy types still written | P0 | 23 of 54 legacy types in active use |
| 14 UNKNOWN types in traffic | P0 | 11 real + 3 noise (writer bugs) |
| REVIEW_RESPONSE unregistered | P1 | 43 occurrences, not in any set |
| 8 unrostered sender identities | P1 | push-pull-loop, bus-watcher, dead-mans-switch, arcana-psi, claude, arcana-psi-gate, lead-doctor, agent-zero |
| 51% missing host tags | P1 | 5,817 of 11,339 lack host= |
| Host tag case variance | P2 | anvil/Huxley/ANVIL/reuben/anvil;CRAB |
| " codex" leading-space sender | P2 | 10 occurrences (writer bug) |
| "all" as type column | P2 | 2 occurrences (recipient leak — writer bug) |
| DECIDE intent at 0% of traffic | P2 | APPROVE/DIRECTIVE/REJECT/VETO all 0 uses |

**See `PHASE_MINUS1_DISCOVERY_REPORT.md` for the complete analysis, including
the 2026-03-02 vs 2026-08-15 trend comparison and the full 14-UNKNOWN-type
classification.**

### 1.7 Existing Operational Lexicon (exploration finding)

A 244-line operational lexicon already exists at `~/.agents/rules/bus-lexicon.md`
(codified 2026-05-01, mirrored to `~/.claude/rules/`). This document was not
known when §1.1-1.5 were written. It is the **de facto canonical source** for
bus protocol vocabulary and is loaded as a rule for all agents.

It defines:
- All 24 canonical message types with purpose + required body content
- Lane lifecycle vocabulary (WIP_START/WIP_END pairing, ownership, reopening)
- Cross-session handoff vocabulary (HANDOFF → WIP_END outcome=transferred → ACK → WIP_START)
- Machine tagging conventions (bare canonical sender, `host=` in body)
- Review-Receipt Schema (artifact, artifact_state, proof_source, proof, next_owner, risk)
- Multi-decision PROPOSAL format (PROPOSAL_MULTI_DECISION compact form)
- Vernacular conventions (Watcher, Engineer, Sibling, Lane, Cross-check, Protocol A/B/C)
- "What NOT to do" list (no COMPLETE/DECISION/MILESTONE as lane closer, no parenthetical senders)

**Relationship to this document**: `bus-lexicon.md` is the operational source
of truth (what agents must do). This document is the formal taxonomy (why the
vocabulary is what it is, and the rectification proposal). They are
complementary, not competing. See `FLEET_VOCABULARY_MAP.md` for the full
authority hierarchy.

---

## 2. Generative Derivation (minimal primitives from first principles)

### 2.1 What is the bus, fundamentally?

An append-only log of typed messages between named participants, where:
- Every message is a single TSV line (transport)
- Every message has a type (intent)
- Every message has a sender and recipient (identity)
- Some messages require cryptographic proof of origin (authenticity)
- Some messages require proof of human authority (privilege)
- Failed operations are preserved for retry (resilience)

### 2.2 Minimal Primitive Set

Derived from the operations the bus actually performs, not from borrowed
vocabulary:

#### Transport primitives (the bus itself)

| Primitive | Definition | Current term(s) | Proposed term |
|---|---|---|---|
| **Bus** | The append-only TSV log | bus, TSV bus, coordination bus | **bus** (keep — clear, short, established) |
| **Append** | Atomic single-line write to the bus | post, write, post_message | **post** (keep — verb, clear) |
| **Read** | Scan the bus for messages | read, read_verified_messages | **read** (keep) |
| **Lock** | Cross-process mutual exclusion for appends | flock, _cross_process_lock, _msvcrt_path_lock | **lock** (keep — the mechanism is clear) |
| **Envelope** | JSON wrapper in the message column carrying signature data | HMAC envelope, signed envelope, {"c","n","s"} | **envelope** (keep — standard term) |
| **Dead-letter** | Record of a failed bus operation | dead_letter, dead_letters.jsonl | **dead-letter** (keep — standard MQ term) |
| **Spool** | Client-side outbound buffer for remote writes | spool, outbound | **spool** (keep — standard term) |
| **Replay** | Retry of a spooled/dead-lettered operation | replay, replay_worker, replay_ledger | **replay** (keep) |
| **Ledger** | Persistent record of replay attempts | replay_ledger, ledger | **ledger** (keep) |
| **Bridge** | HTTP relay for cross-machine bus writes | bridge, bridge_client, bridge_server, bridge_url | **bridge** (keep) |
| **Quarantine** | Isolation area for privileged rows that lack proof | quarantine, privileged_import_quarantine | **quarantine** (keep) |

#### Identity primitives

| Primitive | Definition | Current term(s) | Proposed term |
|---|---|---|---|
| **Sender** | The agent posting a message | from, from_id, sender, sender_id, from_agent | **sender** (standardize — clear, not a Python keyword) |
| **Recipient** | The agent(s) receiving a message | to, to_id, recipient, recipient_id, to_agent | **recipient** (standardize — clear, paired with sender) |
| **Principal** | The human authority behind a privileged write | principal, human, HUMAN_PRINCIPALS | **principal** (keep — standard security term) |
| **Proof** | Cryptographic evidence that a principal authorized a write | principal_proof, proof | **proof** (keep) |
| **Nonce** | Single-use value preventing replay of a proof | nonce | **nonce** (keep — standard crypto term) |

**Rectification**: TSV columns stay `from`/`to` (wire format is frozen —
changing it would break every existing bus file). All function parameters,
structured events, and schemas standardize to `sender`/`recipient`. The TSV
column names are documented as the wire format, with `sender`/`recipient` as
the canonical API names that map to them.

#### Intent primitives (message types)

The 78 existing types map to **6 atomic intents**. The proposal is not to
reduce to 6 types (the existing types carry semantic distinction that is
useful), but to **classify them under these 6 intents** so the taxonomy is
explicit:

| Intent | Definition | Current canonical types | Current legacy types |
|---|---|---|---|
| **INFORM** | "Here is my state" — unilateral status report | STATUS, SITREP, HEARTBEAT, HRSI_CHECKIN | SPOTREP, MONITORING_SUMMARY, INFO, TRUST_REPORT, COMPLIANCE_SCORE, HEALTH_TRANSITION |
| **REQUEST** | "I need you to do something" — calls for action | PROPOSAL, QUESTION | DISPATCH, TASK_REQUEST, REQUEST, QUERY, FLEET_QUERY, LEDGER_QUERY, REQUEST_REVIEW, REQUEST_RETRY, CLAIM, TASK_CLAIM, REGISTER, RESEARCH, DESIGN |
| **DECIDE** | "This is now decided" — authority-bearing resolution | DECISION, DIRECTIVE, VETO, APPROVE, REJECT | PROPOSAL_MULTI_DECISION |
| **CONFIRM** | "I received/completed this" — closes a loop | ACK, RECEIPT, COMPLETE, TASK_COMPLETE, REVIEW, VERIFY | DONE, RESOLVED, RECEIPT_ACK, RECEIPT_REJECT, TASK_REJECT, SESSION_COMPLETE, COMPLETION_REVIEW, AUDIT, AAR |
| **SIGNAL** | "Something needs attention" — alert without authority | ALERT, BLOCKED | SAFETY, ERROR, WARN, ESCALATE, BLOCKER, HOLD, BUS_LATENCY, REMEDIATION, CORRECTION, REDIRECT, STALE_STATE_RESET, LATE_SKILL_INVOKE |
| **TRACE** | "This is a lifecycle event" — structural bookkeeping | WIP_START, WIP_END, HANDOFF, MILESTONE, SKILL_INVOKE | FRAGO, WARNO, CANCEL, RESUME, TERMINATE, SCHEDULED, CHECKPOINT, PHASE_TRANSITION, COORDINATION, DEAL-MEMO, INTEL, BUS_TEST |

**Observations from the classification**:
- FRAGO and WARNO are military order types, but functionally they are TRACE
  (lifecycle bookkeeping for a sprint). The military name implies a 5-paragraph
  structure the bus does not enforce.
- SAFETY is a SIGNAL, but the name implies safety-critical systems
  connotations. ALERT is the cleaner canonical term.
- DONE/RESOLVED/COMPLETE/TASK_COMPLETE are all CONFIRM. The canonical set
  keeps COMPLETE and TASK_COMPLETE but they are near-synonyms.
- RECEIPT is overloaded: it means both "task completion confirmation" (CONFIRM
  intent) and "governance audit receipt" (also CONFIRM, but a different
  semantic — one confirms a task, the other confirms a governance action).

**Stress-test results** (see `PHASE_MINUS1_DISCOVERY_REPORT.md` §2):
- **Edge case mapping**: 77 of 78 types map to exactly one intent (zero
  multi-mapping). 1 unmapped: `WIN` (legacy, 0 usage) — classify as CONFIRM
  or retire.
- **Traffic fit**: 100% of top-20 canonical type traffic maps to an intent
  (0 unmapped). Distribution: INFORM 53%, TRACE 23%, SIGNAL 10%, CONFIRM 6%,
  REQUEST 4%, DECIDE 0%.
- **Prescriptive test**: 8 of 10 hypothetical new types are decided cleanly.
  2 are ambiguous (DELEGATE, ENDORSE) — both expose that **authority is an
  orthogonal axis**, not a 7th intent. The 6 intents classify WHAT a message
  does; the security primitives (privileged types, principal, proof) classify
  WHO has authority to send it. A message has one intent AND zero-or-more
  authority requirements. Do NOT add a 7th intent — document authority as
  orthogonal.

#### Security primitives

| Primitive | Definition | Current term(s) | Proposed term |
|---|---|---|---|
| **Policy level** | Enforcement strictness for unsigned messages | PERMISSIVE, WARN, STRICT | **PERMISSIVE / WARN / STRICT** (keep — clear, standard) |
| **Privileged type** | Message type requiring human principal proof | PRIVILEGED_TYPES, DECISION, DIRECTIVE | **privileged type** (keep) |
| **Signature** | HMAC-SHA256 or Ed25519 authentication of origin | signature, sig, s | **signature** (standardize — no single-letter abbreviations in docs) |
| **Key ID** | Identifier for the signing key | key_id, KEY_ID | **key_id** (keep) |
| **Body hash** | SHA-256 of the message body for integrity | body_hash, message_sha256 | **body_hash** (standardize — `message_sha256` is redundant; SHA-256 is the only hash used) |

#### Schema primitives

| Primitive | Definition | Current term(s) | Proposed term |
|---|---|---|---|
| **Schema marker** | Versioned string identifying a JSON schema | schema, STRUCTURED_EVENT_SCHEMA | **schema** (keep) |
| **Correlation ID** | Tracing identifier linking related messages | correlation_id, request_id | **correlation_id** (keep for tracing); **request_id** (keep for idempotency — they are different concepts) |
| **Event ID** | Unique identifier for a single event | event_id | **event_id** (keep) |
| **Content** | The payload of a structured event | content, body, message, payload, c | **content** (standardize for structured events); **body** (standardize for Ed25519 — they are different layers) |

**Rectification**: The structured event schema and the Ed25519 envelope schema
are different layers (transport vs signing) and should use different field
names. The structured event is the payload; the Ed25519 envelope is the
signed wrapper around that payload. Field name alignment between them is not
required — but both should be documented.

---

## 3. Proposed Controlled Lexicon

### 3.1 Transport (the bus)

| Term | Part of speech | Definition | Do not use |
|---|---|---|---|
| **bus** | noun | The append-only TSV log | "coordination bus" (redundant — there is only one bus) |
| **post** | verb | Write a message to the bus | "write", "send", "emit" |
| **read** | verb | Scan the bus for messages | "query", "fetch", "get" |
| **lock** | noun | Cross-process mutual exclusion for appends | "mutex", "semaphore" |
| **envelope** | noun | JSON wrapper in the message column carrying signature data | "wrapper", "container" |
| **dead-letter** | noun | Record of a failed bus operation | "failed message", "error queue" |
| **spool** | noun | Client-side outbound buffer for remote writes | "queue", "outbox", "buffer" |
| **replay** | verb/noun | Retry of a spooled or dead-lettered operation | "retry", "resend" |
| **ledger** | noun | Persistent record of replay attempts | "log", "journal" |
| **bridge** | noun | HTTP relay for cross-machine bus writes | "relay", "proxy", "gateway" |
| **quarantine** | noun | Isolation area for privileged rows that lack proof | "holding area", "jail" |

### 3.2 Identity

| Term | Part of speech | Definition | Do not use |
|---|---|---|---|
| **sender** | noun | The agent posting a message (canonical API name) | `from`, `from_id`, `sender_id`, `from_agent` in new code |
| **recipient** | noun | The agent(s) receiving a message (canonical API name) | `to`, `to_id`, `recipient_id`, `to_agent` in new code |
| **principal** | noun | The human authority behind a privileged write | "operator", "admin", "owner" |
| **proof** | noun | Cryptographic evidence that a principal authorized a write | "token", "certificate", "credential" |
| **nonce** | noun | Single-use value preventing replay of a proof | "token", "challenge", "random" |

**Wire format note**: TSV columns are `timestamp`, `from`, `to`, `type`,
`message`. These are frozen — changing them would break every existing bus
file. The API names `sender`/`recipient` map to the wire columns `from`/`to`.
This mapping is documented, not eliminated.

### 3.3 Intent (message types)

The 6 intents are the taxonomy. Individual types are instances:

| Intent | Definition | Canonical types |
|---|---|---|
| **INFORM** | Unilateral status report — no response expected | STATUS, SITREP, HEARTBEAT, HRSI_CHECKIN |
| **REQUEST** | Calls for action — expects a response | PROPOSAL, QUESTION |
| **DECIDE** | Authority-bearing resolution — closes a decision | DECISION, DIRECTIVE, VETO, APPROVE, REJECT |
| **CONFIRM** | Closes a loop — acknowledges receipt or completion | ACK, RECEIPT, COMPLETE, TASK_COMPLETE, REVIEW, VERIFY |
| **SIGNAL** | Alert without authority — "something needs attention" | ALERT, BLOCKED |
| **TRACE** | Lifecycle bookkeeping — structural, not semantic | WIP_START, WIP_END, HANDOFF, MILESTONE, SKILL_INVOKE |

**Terms explicitly not used** (inherited from hummbl-governance lexicon, reaffirmed):

| Term | Why not |
|---|---|
| Pod | Kubernetes-specific, implies container orchestration |
| Cohort | Implies A/B testing or user segmentation |
| Squad | Implies human team structure (Spotify model) |
| Swarm | Implies emergent behavior without governance |
| Cluster | Implies infrastructure-level grouping |

**Military terms — retention with documented baggage**:

The military terms (SITREP, SPOTREP, FRAGO, WARNO, AAR, INTEL) are retained
in the legacy set because they appear in historical bus rows and cannot be
removed. They are **not available for new writes**. The canonical set retains
SITREP (too established to retire) but does not add new military terms. The
baggage is documented: these names imply NATO report structures the bus does
not enforce.

### 3.4 Security

| Term | Part of speech | Definition | Do not use |
|---|---|---|---|
| **policy** | noun | Enforcement strictness level (PERMISSIVE/WARN/STRICT) | "mode", "level" (use "policy level") |
| **privileged type** | noun | Message type requiring human principal proof | "restricted type", "protected type" |
| **signature** | noun | Cryptographic authentication of message origin | "sig", "s", "hmac" (as a field name) |
| **key_id** | noun | Identifier for the signing key | "key", "kid" |
| **body_hash** | noun | SHA-256 hash of the message body for integrity | "message_sha256", "hash", "digest" |

### 3.5 Schema

| Term | Part of speech | Definition | Do not use |
|---|---|---|---|
| **schema** | noun | Versioned string identifying a JSON schema version | "version", "format" |
| **correlation_id** | noun | Tracing identifier linking related messages | "trace_id", "span_id", "parent_id" |
| **request_id** | noun | Idempotency key for a specific write operation | "operation_id", "transaction_id" |
| **event_id** | noun | Unique identifier for a single structured event | "message_id", "uuid" |
| **content** | noun | The payload of a structured event (event schema) | "body", "payload", "message" (in event schema context) |
| **body** | noun | The payload of an Ed25519 signed envelope (signing schema) | "content", "payload" (in signing schema context) |

**Note**: `content` and `body` are different layers. The structured event has
`content` (the human-readable payload). The Ed25519 envelope has `body` (the
canonical bytes that were signed). They are not interchangeable.

---

## 4. Rectification Actions

### 4.1 Document (no code change)

1. **Adopt this document** as the controlled lexicon for hummbl-bus.
2. **Update DOCTRINE.md §2** to reference this document instead of defining
   its own incomplete 6-term vocabulary.
3. **Document the HMAC envelope fields** (`c` = content, `n` = nonce,
   `s` = signature) in DOCTRINE.md — currently undocumented.
4. **Document HRSI_CHECKIN** — expand the acronym or retire the type. If the
   expansion is not recoverable, mark it for deprecation.
5. **Mark `COORDINATION_LEXICON.md` as superseded** — add a header noting it
   is stale (2026-03-02) and pointing to `bus-lexicon.md` + this document.
6. **Correct the vernacular path in `api-reference.md`** — change
   `.claude/rules/bus-lexicon.md` to `~/.agents/rules/bus-lexicon.md`
   (the `.agents` path is canonical; `.claude` is a mirror).

### 4.2 Standardize (code change, backward-compatible)

7. **Standardize identity field names** to `sender`/`recipient` in all new
   code. Existing `from_id`/`to_id` function parameters keep their names
   (renaming them is a breaking API change) but are documented as aliases
   for `sender`/`recipient`. The structured event schema already uses
   `sender`/`recipient` — this is the target.
8. **Resolve Ed25519 vs structured event schema drift** — either implement
   the missing Ed25519 fields in `build_structured_event` or document that
   the Ed25519 envelope is a superset that is populated by a different code
   path. The current state (fields defined but never produced) is silent
   drift.
9. **Resolve `docs/AGENTIC_VERNACULAR.md` reference** — `bus_writer.py`
   references `DEFAULT_VERNACULAR_PATH = "docs/AGENTIC_VERNACULAR.md"` but
   this file does not exist. Either create it (containing the message-type
   taxonomy from §3.3 of this document) or remove the reference.
10. **Enforce bare canonical identity** — `devin-anvil` should be rejected
    by `_validate_sender_identity`. Agents must post as `devin` with
    `host=anvil` in the body. Verify this is already enforced; if not, add
    it. (Exploration found 5 messages using `devin-anvil`.)

### 4.3 Classify (no code change)

11. **Tag every canonical message type with its intent** in
    `message_types.py` — either as a comment or as a structured mapping
    (`INTENT_GROUPS: dict[str, frozenset[str]]`). This makes the taxonomy
    machine-readable and prevents future type additions that don't map to an
    intent.
12. **Document the 54 legacy types as frozen** — they are read-only, not
    available for new writes, and should not be extended. This is already
    enforced by the code but not documented in the lexicon.

### 4.4 Consider (operator decision)

13. **Retire COMPLETE in favor of TASK_COMPLETE** (or vice versa) — they are
    near-synonyms and both are CONFIRM intent. Keeping both adds no semantic
    distinction.
14. **Retire ALERT in favor of BLOCKED** (or vice versa) — both are SIGNAL
    intent. ALERT is generic; BLOCKED is specific. If we need both, document
    the distinction (ALERT = general attention, BLOCKED = cannot proceed).
15. **HRSI_CHECKIN expansion — RESOLVED**: HRSI = **Human Relational Safety
    Index** (per `HUMMBL_OPERATOR_DICTIONARY.md` lines 970-980). It is a
    BKI-aligned daily belonging baseline check (safety, mattering, connection,
    energy, sleep_hours, hule, relational_note) — distinct from HEARTBEAT
    (system liveness). Do NOT retire. Document the expansion in `bus-lexicon.md`.
    Note: a second expansion (Human Recursive Self-Improvement) exists in
    governance research papers but refers to a different framework, not the
    bus type. Open sub-question: what does the `hule` payload field expand to?
16. **Resolve lane_classifier (gate 6)** — decide whether `lane` is a bus
    protocol term (TRACE intent) or an orchestration policy term (stays in
    hummbl-governance). This is the last open gate from the drift reconciliation.
17. **Retire SVE research** — mark `semantic_vernacular_*` specs as
    REJECTED/ARCHIVED. In-flight translation was rejected due to provenance
    concerns. Keep the human-interpretability goal but use existing drift
    signals.
18. **Standardize broadcast recipient** — `all` (28 uses) vs `broadcast`
    (2 uses). Standardize on `all`; `broadcast` is a legacy alias.

---

## 5. Open Questions

1. **Should the intent taxonomy be enforced in code?** Currently
   `message_types.py` is a flat set. An `INTENT_GROUPS` mapping would make
   the taxonomy machine-readable but adds maintenance burden.
2. **Should the HMAC envelope fields be expanded?** `{"c": ..., "n": ..., "s": ...}`
   → `{"content": ..., "nonce": ..., "signature": ...}`. This would break
   every signed message in every existing bus file. Probably not worth it —
   the compact form is documented and stable.
3. **Should `request_id` and `correlation_id` be unified?** No — they serve
   different purposes. `request_id` is an idempotency key for a specific
   write operation (used in replay/spool/authority). `correlation_id` is a
   tracing identifier linking related messages across a workflow. They are
   different concepts that happen to both be strings.
4. **Should the military legacy terms be actively retired?** They are already
   in the legacy (read-only) set. The question is whether to document them
   with a "do not use in new writes" warning (yes) or to actively migrate
   historical rows to new types (no — append-only means no mutations).

---

## 6. Comparison with hummbl-governance COORDINATION_LEXICON.md

The hummbl-governance lexicon (2026-03-02) defined:

| Concept | FM lexicon term | HB controlled lexicon term | Status |
|---|---|---|---|
| Organizational unit | Agent, Cell, Raft, Fleet | (out of scope — orchestration) | FM-only |
| Work unit | Lane | Lane (if gate 6 resolves to bus) | TBD |
| Communication infra | Bus, Lane, Channel, Bridge | Bus, Bridge (Lane TBD) | Aligned |
| Message types | 15 types with frequency counts | 24 canonical + 54 legacy, classified into 6 intents | HB supersedes |
| Coordination verbs | Dispatch, ACK, Handoff, Gate, Heartbeat | post, ACK, HANDOFF, HEARTBEAT (classified by intent) | Aligned |
| State machines | 5 state machines | (out of scope — orchestration) | FM-only |
| Governance vocab | CAES, EAL-AAA, DCT, DCTX, GaaS, Base120 | (out of scope — governance) | FM-only |
| Terms not used | Pod, Cohort, Squad, Swarm, Cluster | Same list, reaffirmed | Aligned |

The hummbl-governance lexicon mixed bus protocol terms with orchestration and
governance terms. This document scopes to **bus protocol only** — the
transport, identity, intent, security, and schema primitives that hummbl-bus
owns. Orchestration terms (Cell, Raft, Sprint, Dispatch) and governance terms
(CAES, DCT, Base120) belong in their respective packages.

---

*This document is the controlled lexicon for hummbl-bus. It supersedes the
vocabulary section of DOCTRINE.md §2 and the bus-protocol portions of
hummbl-governance's COORDINATION_LEXICON.md. It does not modify code — §4 lists
the actions that would implement the rectification, each marked with its
scope (document, standardize, classify, consider).*
