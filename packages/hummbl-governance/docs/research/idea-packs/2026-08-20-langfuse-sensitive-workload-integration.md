# Langfuse Integration for Sensitive Workloads (PII, PHI, Executive Coaching)

| Field | Value |
|-------|-------|
| **Status** | RATIFIED-PENDING-IMPLEMENTATION — D1-D12 resolved by operator 2026-08-20T21:10Z (see §20) |
| **Author** | devin (glm-5-2-high, operator-seeded) |
| **Created** | 2026-08-20 |
| **Session** | continuation of langfuse triage (clp-7bd3c73f23f5) |
| **Bus seed** | DRAFT/local |
| **Triage precedent** | `clp-7bd3c73f23f5` (ADOPT, confidence 0.82) |
| **Decisions pending** | operator — deployment topology, consent framework, retention schedule |

---

## 0. Summary

Langfuse is an MIT-licensed LLM observability platform (YC W23, 32.8K stars) that
traces LLM calls, captures prompts/completions, scores evaluations, and manages
prompts. HUMMBL needs LLM observability for governance, debugging, evals, and
drift detection — but Langfuse's default behavior (capturing full prompt and
completion content) directly conflicts with privacy obligations for three
sensitive workload classes:

1. **PII** — CRM, outreach, stakeholder communications, business development
2. **PHI** — healthcare AI governance consulting (NIST AI RMF for healthcare clients)
3. **Executive coaching** — private client conversations, BKI sessions, performance reviews

This proposal defines a per-class tracing policy, deployment topology, consent
framework, and integration architecture that reconciles observability with
privacy. The core design principle: **Langfuse must never be the first surface
to receive raw sensitive content.** Sensitive content is either redacted,
de-identified, or encrypted before it reaches Langfuse, and the operator
controls the keys.

---

## 1. Problem Statement

HUMMBL's fleet agents make LLM calls across sensitive domains daily. Today
these calls are unobserved — no traces, no evals, no drift detection, no
prompt version history. This creates three problems:

1. **Governance gap**: HUMMBL sells AI governance but cannot observe its own
   agents' LLM calls. A client audit would find no observability infrastructure.
2. **Quality gap**: Agent outputs cannot be evaluated systematically. Drift
   detection (`/drift-detect` skill) has no trace data to analyze.
3. **Coaching fidelity gap**: Executive coaching sessions (BKI-informed) have
   no structured way to capture session metadata for client progress tracking
   without violating client confidentiality.

Adding Langfuse naively (default tracing) would capture raw PII/PHI/coaching
content in a third-party system, creating a **worse** problem than the gap it
fills: a privacy breach surface that contradicts HUMMBL's own doctrine
(`HUMAN_AI_AGENCY_BOUNDARY.md` §147: "Health and executive coaching language
must preserve personhood, consent, refusal, and self-authorship").

The problem is not *whether* to adopt Langfuse (triage verdict: ADOPT,
`clp-7bd3c73f23f5`). The problem is *how* to adopt it without making
observability a privacy liability.

---

## 2. Workload Classification

Every fleet LLM call is classified into one of four classes at trace emission
time. The class is determined by the agent's active context and is tagged as
a Langfuse trace attribute (`workload_class`).

| Class | Label | Examples | Default content capture | Retention | Legal basis |
|-------|-------|----------|------------------------|-----------|-------------|
| **A** | PHI | Healthcare AI governance consulting; NIST AI RMF work for healthcare clients; any LLM call referencing patient data, diagnoses, or covered-entity information | De-identified per HIPAA Safe Harbor (§164.514(b)(2)) before export | 6 years (HIPAA documentation) | BAA with Langfuse (HIPAA cloud) |
| **B** | Executive coaching | BKI sessions, performance reviews, client development conversations, somatic-linguistic belonging work | Encrypted at rest (client-key); metadata only visible to operator | Engagement + 90 days, then purge | Client engagement contract with tracing consent clause |
| **C** | PII | CRM outreach, stakeholder updates, discovery calls, proposal drafting, any LLM call containing names/emails/phone numbers of non-clients | PII redacted before export (names, emails, phones, addresses replaced with `[PERSON_1]`, `[EMAIL_1]`, etc.) | 90 days rolling | DPA under GDPR/CCPA |
| **D** | Non-sensitive | Fleet ops, research, public docs, code generation, skill authoring, bus posts, governance framework development | Full capture (content + metadata) | 90 days rolling | None required (internal ops) |

**Classification authority**: The agent emitting the trace declares the class.
Misclassification is a guardrail violation (see §9). The operator can override
class post-hoc via Langfuse UI.

---

## 3. Deployment Topology

### Option 1: Single self-hosted instance for all classes
- Pro: data sovereignty, single management surface, no vendor dependency
- Con: PHI on self-hosted requires BAA-incompatible posture (Langfuse self-hosted EE license needed for audit logging / data retention controls); coaching key management adds complexity

### Option 2: Langfuse Cloud (HIPAA variant) for everything
- Pro: BAA available for PHI, managed, no ops burden
- Con: coaching content leaves HUMMBL infrastructure; PII in third-party cloud; vendor lock-in; cost

### Option 3 (RECOMMENDED): Hybrid — self-hosted for B/C/D, HIPAA cloud for A

| Workload class | Deployment | Rationale |
|----------------|------------|-----------|
| A (PHI) | Langfuse Cloud HIPAA (`hipaa.cloud.langfuse.com`) | BAA available; HIPAA-compliant infrastructure; PHI never touches HUMMBL self-hosted |
| B (Coaching) | Self-hosted on UpCloud | Client content stays on HUMMBL-controlled infrastructure; client-key encryption; data sovereignty |
| C (PII) | Self-hosted on UpCloud | PII redacted before export anyway; self-hosted adds defense-in-depth |
| D (Non-sensitive) | Self-hosted on UpCloud | No privacy constraint; full observability value |

**Self-hosted location**: UpCloud VM (already planned in cloud migration —
`2026-08-19-infrastructure-cloud-migration-plan.md`). Managed DB is reserved
for Langfuse per `2026-08-19-session-handoff-cloud-mission.md:176`.

**Telemetry opt-out**: Self-hosted Langfuse instances disable PostHog telemetry
(`LANGFUSE_TELEMETRY=false`) per deployment. No usage statistics leave
HUMMBL infrastructure.

---

## 4. Tracing Policy per Workload Class

The tracing policy defines what fields are exported to Langfuse for each class.
The principle: **capture less by default, expand only with explicit consent.**

### 4.1 Class A (PHI) — De-identification before export

**Exported fields**:
- Trace metadata: `session_id`, `agent`, `workload_class=A`, `client_engagement_id` (opaque), `timestamp`
- LLM metadata: `model`, `provider`, `token_count`, `latency_ms`, `cost`
- Content: **de-identified** per HIPAA Safe Harbor (§164.514(b)(2)) — 18 identifiers removed/replaced before export

**De-identification method**: A pre-export redaction function (stdlib-only, part
of hummbl-governance) strips:
- Names, geographic subdivisions smaller than state, dates (except year), phone/fax/email/SSN/MRN/account numbers, device identifiers, URLs, IP addresses, biometric identifiers, full-face photos, any other unique identifying number

**What is NOT exported**: raw patient narratives, raw clinical notes, any field that cannot be reliably de-identified.

**Falsification test**: A sample of 100 PHI traces reviewed by a qualified
reviewer must achieve zero re-identifiable records. If any record is
re-identifiable, the de-identification function is failing and tracing
for Class A is suspended until fixed.

### 4.2 Class B (Executive coaching) — Encrypted content, client-key

**Exported fields**:
- Trace metadata: `session_id`, `agent`, `workload_class=B`, `client_id` (opaque hash), `engagement_id`, `timestamp`
- LLM metadata: `model`, `provider`, `token_count`, `latency_ms`, `cost`
- Content: **encrypted** with a per-client key (AES-256-GCM) stored in 1Password; Langfuse stores ciphertext only; operator holds decryption key

**What the operator sees in Langfuse UI**: metadata + ciphertext blob. To read
content, operator decrypts offline with client key.

**What agents see via MCP**: metadata only (no content). Agents cannot
decrypt coaching content.

**Consent gate**: Tracing for Class B is **off by default** per client. It
activates only when the client's engagement contract includes the tracing
consent clause (see §5.2). Clients can revoke tracing consent at any time;
revocation triggers immediate purge of that client's traces.

### 4.3 Class C (PII) — Redaction before export

**Exported fields**:
- Trace metadata: `session_id`, `agent`, `workload_class=C`, `timestamp`
- LLM metadata: `model`, `provider`, `token_count`, `latency_ms`, `cost`
- Content: **PII-redacted** — names → `[PERSON_N]`, emails → `[EMAIL_N]`, phones → `[PHONE_N]`, addresses → `[ADDR_N]`, org names retained (not PII under CCPA)

**Redaction method**: Same stdlib redaction function as Class A, configured
for PII patterns (regex-based, no ML dependency). Redaction is applied
before export; raw content never leaves the agent process.

**Falsification test**: A sample of 100 PII-redacted traces must contain zero
unredacted email addresses or phone numbers (regex-verified).

### 4.4 Class D (Non-sensitive) — Full capture

**Exported fields**:
- All metadata + full prompt + full completion + scores + evals

**Rationale**: No privacy constraint. Full observability value. This is where
Langfuse's eval, prompt management, and drift detection capabilities
deliver maximum return.

---

## 5. Consent and Legal Basis

### 5.1 PHI (Class A) — BAA required

- **Before any Class A tracing begins**: HUMMBL must execute a Business
  Associate Agreement (BAA) with Langfuse (Cloud HIPAA variant).
- **BAA scope**: covers PHI that reaches Langfuse after de-identification.
  Note: de-identified data per Safe Harbor is no longer PHI under HIPAA,
  so the BAA is a defense-in-depth layer, not a strict legal requirement
  for de-identified data. However, because de-identification can fail,
  the BAA is mandatory as a safety net.
- **Healthcare client consent**: HUMMBL's healthcare governance clients
  must consent to LLM call tracing in their engagement contract. The
  consent clause must disclose: what is traced, how it is de-identified,
  where it is stored, retention period, and the client's right to
  revoke.

### 5.2 Executive coaching (Class B) — Engagement contract clause

- **Before any Class B tracing begins**: the client's engagement contract
  must include the **Tracing Consent Clause** (drafted by legal-counsel
  agent, reviewed by operator's attorney):
  - Discloses that LLM-assisted coaching sessions will be traced for
    quality and progress tracking
  - Specifies that content is encrypted with a client-specific key
  - Specifies that the operator (Reuben) is the sole key holder
  - Specifies retention period (engagement + 90 days)
  - Specifies the client's right to revoke consent and trigger purge
  - Specifies that no agent or third party can decrypt content
- **Existing doctrine hook**: `HUMAN_AI_AGENCY_BOUNDARY.md` §147 requires
  that coaching language "preserve personhood, consent, refusal, and
  self-authorship." The consent clause implements this: tracing is
  opt-in, revocable, and client-controlled.

### 5.3 PII (Class C) — DPA under GDPR/CCPA

- **Data Processing Agreement** with Langfuse (self-hosted variant:
  HUMMBL is the data controller and processor; no subprocessor).
- For self-hosted deployment, the DPA is between HUMMBL and its clients
  (HUMMBL is processor). Langfuse is not a subprocessor because
  self-hosted = HUMMBL operates the instance.
- **CCPA notice**: HUMMBL's privacy policy must disclose LLM call tracing
  for business purposes, with redaction before storage.

---

## 6. Access Controls

### 6.1 Project isolation

Langfuse uses project-scoped API keys. HUMMBL creates one project per
workload class (minimum) or per client engagement (for Class A/B):

| Project | API key scope | Who can view | Agent MCP access |
|---------|---------------|--------------|------------------|
| `hummbl-phi` (or per-client) | Class A traces | Operator only | Metadata-only (scoped key) |
| `hummbl-coaching-<client>` | Class B traces | Operator only | Metadata-only (scoped key) |
| `hummbl-pii` | Class C traces | Operator + delegated agents | Redacted content (scoped key) |
| `hummbl-ops` | Class D traces | Operator + fleet agents | Full access (scoped key) |

### 6.2 Role-based access

- **Operator (Reuben)**: full access to all projects, sole holder of
  coaching decryption keys
- **Fleet agents (via MCP)**: scoped to `hummbl-ops` project for evals
  and prompt management; no access to Class A/B content; redacted-only
  access to Class C
- **Auditors (external)**: time-limited, read-only, metadata-only access
  to specific projects per engagement

### 6.3 MCP server integration

Langfuse becomes the **13th MCP server** in the fleet standard
(`mcp-fleet-config-12server` skill). Configuration:

```json
"langfuse": {
  "url": "https://<self-hosted-domain>/api/public/mcp",
  "transport": "streamableHttp",
  "headers": {
    "Authorization": "Basic <from 1Password: Langfuse MCP Auth Header>"
  }
}
```

Agent MCP access is scoped to the `hummbl-ops` project key by default.
Agents needing eval access to other projects receive project-specific
scoped keys with metadata-only permissions.

---

## 7. Integration Architecture

### 7.1 No SDK in hummbl-governance (stdlib-only constraint)

HUMMBL's ADR-001 blocks the Langfuse Python SDK as a runtime dependency
in `hummbl-governance` (stdlib-only). Integration uses two alternative
paths:

**Path 1: OpenTelemetry exports (preferred for agent runtimes)**
- Agents emit OTel traces with `gen_ai.*` semantic conventions
- OTel exporter sends traces to Langfuse endpoint (Langfuse accepts OTel natively)
- No `import langfuse` in any hummbl-governance code
- Redaction/de-identification/encryption happens in the OTel span processor (stdlib-only) before export

**Path 2: Direct API integration (for non-OTel contexts)**
- `urllib.request` (stdlib) posts trace events to Langfuse Public API
- Used where OTel is not available (e.g., lightweight scripts)
- Same pre-export redaction applies

### 7.2 Trace tagging schema

Every trace includes these attributes (OTel resource/span attributes):

| Attribute | Type | Example | Purpose |
|-----------|------|---------|---------|
| `workload_class` | enum | `A`/`B`/`C`/`D` | Drives redaction policy |
| `session_id` | string | `session-20260820T1600Z` | Cross-references bus lane |
| `agent` | string | `devin` / `codex` / `claude-code` | Attribution |
| `client_engagement_id` | opaque | `eng-<hash>` | Per-client isolation (Class A/B) |
| `skill` | string | `triage` / `bki-reframe` | Workflow context |
| `model` | string | `glm-5-2-high` | Model telemetry |
| `redaction_applied` | bool | `true` | Audit flag |
| `consent_status` | enum | `granted` / `revoked` / `n/a` | Consent gate state |

### 7.3 Pre-export redaction pipeline

```
LLM call completes
  → span processor classifies workload_class
  → if Class A: HIPAA Safe Harbor de-identification
  → if Class B: encrypt with client key (1Password-retrieved)
  → if Class C: PII regex redaction
  → if Class D: no transformation
  → export to Langfuse (OTel or API)
```

The redaction pipeline is a single stdlib Python module
(`hummbl_governance/observability/redaction.py`) with per-class functions.
It is the **only** code path that transforms content before Langfuse export.
It is tested with a golden fixture of sensitive samples (see §10).

---

## 8. Daily Fleet Operations

### 8.1 Which agents emit traces

| Agent runtime | Emits traces? | Default class | Notes |
|---------------|---------------|---------------|-------|
| Devin (CLI, all profiles) | Yes | D (ops) | Class changes per active skill/context |
| Codex | Yes | D | Same |
| Claude Code | Yes | D | Same |
| Background subagents | Yes | D | Inherit parent class |
| Scheduled/cron agents | Yes | D | Inherit task class |

### 8.2 Class escalation in skills

Skills that handle sensitive content declare their workload class:

| Skill | Default class | Rationale |
|-------|---------------|-----------|
| `/hrsi-checkin` | B (if coaching) / D (if personal) | Somatic belonging data |
| `/bki-reframe` | B | Coaching session content |
| `/bki-session-export` | B | Client session export |
| `/professor` | B (if coaching client) / D (if self-study) | Depends on context |
| `/discovery-call` | C | Prospect PII |
| `/follow-up` | C | Contact PII |
| `/stakeholder-update` | C | Stakeholder names |
| `/proposal-write` | C | Client info |
| `/healthcare-ai-watch` | A (if client work) / D (if research) | PHI context |
| `/incident-response-plan` | A (if healthcare client) / D | PHI context |
| All other skills | D | Default to non-sensitive |

### 8.3 Eval feedback loop

Langfuse evaluations feed back into fleet operations:

1. **Daily**: `/drift-detect` skill queries Langfuse for trace quality trends
2. **Weekly**: `/weekly-review` includes Langfuse eval scores in the review
3. **Per-release**: `/eval-suite` runs against Langfuse datasets for regression
4. **Per-engagement**: coaching clients receive a quarterly progress report
   generated from Langfuse metadata (no content, no decryption)

### 8.4 Incident response

During an incident (`/incident`, `/incident-response-plan`):
- Langfuse traces are evidence (trace IDs cited in incident timeline)
- For Class A/B incidents, the operator decrypts traces offline for review
- For Class C/D incidents, traces are directly reviewable
- Langfuse traces are admissible in postmortem (`/postmortem`) evidence packs

---

## 9. Privacy Safeguards

### 9.1 Redaction pipeline guarantees

- The redaction pipeline runs **before** any network export. No raw Class A/B/C
  content ever reaches Langfuse.
- The pipeline is deterministic (no ML-based redaction — regex + rules only).
  Deterministic means testable: the same input always produces the same
  redacted output.
- The pipeline is the **single chokepoint**. There is no alternate export
  path that bypasses redaction.

### 9.2 Misclassification guardrail

- If an agent declares `workload_class=D` but the content matches PII/PHI
  patterns, a guardrail flag is raised (not a block — agents may legitimately
  discuss PII patterns in abstract). The flag appears in the Langfuse trace
  as `redaction_applied=false` + `pii_pattern_detected=true`.
- The operator reviews flagged traces weekly. Repeated misclassification
  by an agent is a guardrail violation (`/agent-audit`).

### 9.3 Coaching key management

- Per-client encryption keys are stored in 1Password (`api-keys` vault)
  under `Langfuse Coaching Key - <client>`.
- Keys are retrieved only by the operator (not agents — agents never
  decrypt coaching content).
- Key rotation: per engagement renewal or on client request.
- Key revocation: on consent revocation, the key is destroyed and traces
  become permanently unreadable (ciphertext remains but is unrecoverable).

### 9.4 Self-hosted telemetry opt-out

- `LANGFUSE_TELEMETRY=false` set on all self-hosted instances.
- Verified post-deployment: no outbound traffic to PostHog from Langfuse VM.

---

## 10. Retention and Purge

| Class | Retention | Purge trigger | Purge method |
|-------|-----------|---------------|--------------|
| A (PHI) | 6 years | HIPAA documentation requirement | Langfuse API delete (verified) |
| B (Coaching) | Engagement + 90 days | Engagement end + 90d, or consent revocation | Langfuse API delete + key destruction |
| C (PII) | 90 days rolling | Age-based, automated | Langfuse retention policy (self-hosted) |
| D (Non-sensitive) | 90 days rolling | Age-based, automated | Langfuse retention policy (self-hosted) |

**Legal hold**: If any class is under legal hold, purge is suspended for
that class until hold is released. Hold is declared by operator and
recorded in the bus.

**Purge verification**: Purge operations emit a bus `STATUS` with the
count of deleted traces and verification that no traces remain for the
purged scope.

---

## 11. Risks

| Risk | Severity | Mitigation |
|------|----------|------------|
| De-identification failure (Class A) re-identifies patient | HIGH | Safe Harbor de-id + BAA + falsification test (zero re-identifiable in 100-sample) |
| Coaching key compromise | HIGH | 1Password storage, operator-only access, per-client keys, rotation on renewal |
| Agent misclassifies sensitive content as Class D | MED | Pattern-detection guardrail + weekly operator review + `/agent-audit` on repeat |
| Langfuse self-hosted VM compromise | MED | VM on tailnet only, no public exposure except MCP endpoint behind Cloudflare tunnel + auth |
| Cross-project contamination (trace lands in wrong project) | MED | Project-scoped API keys, one key per class, agent never holds multiple class keys |
| Consent revocation not honored (traces not purged) | HIGH | Automated purge job + bus receipt + quarterly audit of revocation compliance |
| Cost overrun from trace volume | LOW | Class D rolling 90d retention + self-hosted (no per-trace cost) + token-count monitoring |

---

## 12. Decision Gates (operator)

| # | Decision | Options | Recommendation |
|---|----------|---------|----------------|
| D1 | Deployment topology | Single self-hosted / Cloud HIPAA all / Hybrid | **Hybrid** (self-hosted for B/C/D, HIPAA cloud for A) |
| D2 | BAA execution with Langfuse | Execute now / defer until first healthcare client | **Defer until first healthcare client** — no Class A tracing until BAA is executed |
| D3 | Coaching consent clause | Draft now / defer until first coaching engagement | **Draft now** (legal-counsel agent), review with attorney, have ready before first engagement |
| D4 | MCP server addition | Expand to 13-server standard / replace underused server / defer | **Expand to 13** — Langfuse is additive, not redundant |
| D5 | Redaction pipeline implementation | Build in hummbl-governance / build as separate module | **Build in hummbl-governance** (`observability/redaction.py`) — stdlib-only, tested |
| D6 | Trace volume budget | Unlimited / cap per day / cap per class | **Cap per class** — Class D unlimited, Class A/B/C capped at 500 traces/day initially |
| D7 | Eval feedback loop cadence | Daily / weekly / per-release | **Daily drift-detect + weekly review + per-release eval-suite** |

---

## 13. Implementation Phases

### Phase 1: Self-hosted Langfuse + Class D only (week 1-2)
- Deploy Langfuse on UpCloud VM (per cloud migration plan)
- Disable telemetry (`LANGFUSE_TELEMETRY=false`)
- Wire OTel export from Devin CLI → Langfuse for Class D traces only
- Add Langfuse as 13th MCP server (scoped to `hummbl-ops` project)
- Validate: traces appear in Langfuse UI, evals work, prompt management works
- **Gate**: operator confirms Class D observability value before proceeding

### Phase 2: Redaction pipeline + Class C (week 3-4)
- Implement `hummbl_governance/observability/redaction.py` (stdlib-only)
- PII redaction function with regex patterns
- Golden fixture test: 100 PII samples → zero unredacted emails/phones
- Enable Class C tracing with redaction
- **Gate**: falsification test passes before enabling

### Phase 3: Coaching encryption + Class B (week 5-6)
- Implement encryption function (AES-256-GCM, stdlib `cryptography` — note: this is a test-extra dependency, not runtime; or use stdlib `hashlib` + `os.urandom` for a simpler scheme if stdlib-only is strict)
- Per-client key management via 1Password
- Draft coaching consent clause (legal-counsel agent → attorney review)
- Enable Class B tracing only after first coaching engagement with signed consent
- **Gate**: consent clause signed by client before any Class B tracing

### Phase 4: PHI de-identification + Class A (week 7-8, or on first healthcare client)
- Implement HIPAA Safe Harbor de-identification function
- Execute BAA with Langfuse (HIPAA cloud variant)
- Golden-fixture test: 100 PHI samples → zero re-identifiable records
- Enable Class A tracing only after BAA is executed AND first healthcare client consents
- **Gate**: BAA executed + client consent + falsification test passes

### Phase 5: Eval feedback loop (ongoing, after Phase 1)
- Wire `/drift-detect` to query Langfuse
- Wire `/weekly-review` to include eval scores
- Wire `/eval-suite` to run against Langfuse datasets
- Wire `/postmortem` to cite Langfuse trace IDs

---

## 14. Pre-existing infra check

Searched `hummbl-governance/docs`, `hummbl-governance/hummbl_governance`,
`~/.agents/skills`, `~/.agents/skills-full` for langfuse, observability,
telemetry, tracing, executive coaching, PHI, BAA, HIPAA on 2026-08-20.

**Found**:
- `docs/standards/1PASSWORD_CHARTER.md:111` — 7 Langfuse 1Password entries staged (public key, secret key, base URL, MCP auth header, [REDACTED: machine] key, note, langfuse credential)
- `docs/standards/HUMAN_AI_AGENCY_BOUNDARY.md:147` — "Health and executive coaching language must preserve personhood, consent, refusal, and self-authorship" (doctrine hook)
- `docs/research/idea-packs/2026-08-19-session-handoff-cloud-mission.md:176` — "Self-hosted PostgreSQL on dedicated VM; reserve managed DB for Langfuse" (cloud plan)
- `docs/research/idea-packs/2026-08-19-infrastructure-cloud-migration-peer-review.md:122,128` — peer review recommends reserving managed DB for Langfuse
- `docs/standards/FLEET_INVENTORY_2026-06-22.md:66` — `hummbl-theory` includes BKI (theoretical foundations for belonging work)
- `docs/ecosystem/PLAN.md:24` — `hummbl-bki` listed as RESEARCH stage
- `docs/gdpr-mapping.md` — GDPR control mapping exists (DPA foundation)
- `docs/soc2-mapping.md` — SOC 2 mapping exists (access control foundation)
- `docs/trackers/healthcare-ai-watch/` — healthcare AI regulation tracker (PHI context)
- `docs/coverage/ophthalmic-ai.md` — healthcare AI coverage (PHI context)
- `~/.agents/skills/mcp-fleet-config-12server/SKILL.md` — 12-server MCP fleet standard (Langfuse would be 13th)
- `~/.agents/skills/triage/SKILL.md:33` — langfuse listed as example triage candidate
- `~/.agents/skills/drift-detect/SKILL.md` — drift detection skill (Langfuse trace consumer)
- `~/.agents/skills/eval-suite/SKILL.md` — eval suite skill (Langfuse dataset consumer)
- Ledger entry `clp-7bd3c73f23f5` — triage verdict ADOPT (this proposal's precedent)

**Not found** (no conflicts):
- No existing LLM observability integration in `hummbl_governance/` code
- No existing `observability/` module in `hummbl_governance/`
- No existing ADR for LLM tracing or observability
- No existing BAA or DPA on file (would be new)
- No existing coaching consent clause (would be new)

---

## 15. Evidence (claim-strength ladder)

| Claim | Strength | Source tier | Evidence |
|-------|----------|-------------|----------|
| Langfuse is MIT-licensed (core) | Verified | T1 (primary source) | github.com/langfuse/langfuse LICENSE; langfuse.com/handbook/chapters/open-source |
| Langfuse has native MCP server with 79 tools | Verified | T1 | langfuse.com/docs/api-and-data-platform/features/mcp-server; mcp.reference.langfuse.com |
| Langfuse offers HIPAA-compliant cloud variant | Verified | T1 | hipaa.cloud.langfuse.com endpoint documented; langfuse.com/docs |
| Langfuse accepts OpenTelemetry exports natively | Verified | T1 | langfuse.com/docs/tracing (OTel integration) |
| Langfuse self-hosted reports telemetry to PostHog by default | Verified | T1 | github.com/langfuse/langfuse README; langfuse.com/self-hosting/security/telemetry |
| De-identification per Safe Harbor removes 18 identifier types | Verified | T1 | 45 CFR §164.514(b)(2) |
| HUMMBL doctrine requires coaching language to preserve consent | Verified | T1 (internal doctrine) | HUMAN_AI_AGENCY_BOUNDARY.md:147 |
| Cloud migration plan reserves managed DB for Langfuse | Verified | T1 (internal) | 2026-08-19-session-handoff-cloud-mission.md:176 |
| Coaching tracing requires client consent | Inferred | T2 (doctrine + legal reasoning) | HUMAN_AI_AGENCY_BOUNDARY.md §147 + general privacy law |
| Hybrid topology is optimal | Speculation | T3 (architectural reasoning) | This proposal §3 — requires operator review |

---

## 16. Non-goals and safety boundary

**Non-goals**:
- This proposal does not define the coaching curriculum or BKI session structure
- This proposal does not define healthcare AI governance deliverables
- This proposal does not replace existing audit log (`audit_log.py`) — Langfuse traces LLM calls; audit_log records governance events
- This proposal does not define a public-facing Langfuse dashboard (all projects are internal-only)

**Safety boundary**:
- No Class A (PHI) tracing until BAA is executed AND client consents AND de-id falsification test passes
- No Class B (coaching) tracing until client signs consent clause AND encryption is implemented
- No Class C (PII) tracing until redaction falsification test passes
- No raw sensitive content ever reaches Langfuse — redaction/de-id/encryption is mandatory before export
- The operator can suspend all tracing globally via kill switch (`/kill-switch`) — Langfuse export respects the kill switch state

---

## 17. Falsification tests

| Test | Pass criterion | Failure action |
|------|----------------|----------------|
| PII redaction (Class C) | 100 PII samples → 0 unredacted emails, 0 unredacted phones (regex-verified) | Suspend Class C tracing |
| De-identification (Class A) | 100 PHI samples → 0 re-identifiable records (qualified reviewer) | Suspend Class A tracing |
| Encryption (Class B) | Ciphertext cannot be decrypted without client key (verified with wrong-key test) | Suspend Class B tracing |
| Telemetry opt-out | No outbound traffic to PostHog from Langfuse VM (network capture) | Block VM egress, fix config |
| Kill switch | Engaging kill switch stops all Langfuse export within 1 trace cycle | Fix kill switch wiring |
| Consent revocation purge | Revoked client's traces deleted within 24h, verified via API count = 0 | Manual purge + audit |

---

## 18. Review ask

**Review ask**: Should HUMMBL adopt this per-class tracing policy and hybrid
deployment topology for Langfuse integration across PII, PHI, and executive
coaching workloads?

**Verdict options**:
- **ADOPT**: proceed with Phase 1 (self-hosted + Class D) immediately
- **ADAPT**: proceed with modifications (specify which decisions to change)
- **AVOID**: do not integrate Langfuse for sensitive workloads; identify alternative

**Specific decisions requiring operator input**: see §12 (D1-D7).

---

## 19. Verdicts

**Review opened**: 2026-08-20T16:25:02Z (bus PROPOSAL `becc15b3`)
**Review closed**: 2026-08-20T16:55:00Z (5-lane swarm, all `subagent_general`)

### 19.1 Lane verdicts

| Lane | Verdict | HIGH findings | Veto weight |
|------|---------|---------------|-------------|
| Privacy & Legal | ADAPT | 4 (F1-F4) | No |
| Security & Threat Model | ADAPT | 6 (F1-F6) | No |
| Architecture & Integration | ADAPT | 4 (F1-F4) | No |
| Operations & Daily Fleet | ADAPT | 5 (F1-F3, F6, F8) | No |
| Executive Coaching & BKI Fidelity | ADAPT | 5 (F1-F5) | **YES** |

**Consensus: ADAPT (unanimous, 5/5 lanes).** No lane returned AVOID; no lane returned
ADOPT. The coaching-fidelity lane exercised veto weight — its ADAPT is conditional:
Class B (Phase 3) is blocked until F1-F5 are resolved, or the lane escalates to AVOID.

### 19.2 Convergent findings (appearing in 2+ lanes)

| # | Finding | Lanes | Severity |
|---|---------|-------|----------|
| C1 | AES-256-GCM not achievable stdlib-only; `hashlib`+`os.urandom` fallback is not authenticated encryption | Security F3, Architecture F3, Ops F10, Coaching F10 | HIGH (4 lanes) |
| C2 | Redaction "single chokepoint" is a convention, not enforced; unreachable for Codex/Claude Code (no hummbl_governance import path) | Security F1, Architecture F1+F2, Ops F2 | HIGH (3 lanes) |
| C3 | Misclassification guardrail fails open — PHI/PII in Class D trace sits unredacted in Langfuse for up to 7 days | Security F2, Architecture F6, Ops F3 | HIGH (3 lanes) |
| C4 | Kill switch is in-process only, no distributed propagation; in-flight traces race the switch | Security F4, Ops F8 | HIGH (2 lanes) |
| C5 | Operator is single point of failure (sole key holder, sole reviewer, sole purge approver) | Ops F8, Coaching F1+F2 | HIGH (2 lanes) |
| C6 | Phase 1 timeline predicated on unratified cloud migration; OTel emission is greenfield, not wiring | Ops F1+F2, Architecture F8 | HIGH (2 lanes) |

### 19.3 Coaching-fidelity findings (veto lane, must resolve before Phase 3)

| # | Finding | Fix |
|---|---------|-----|
| CF1 | Operator sole key holder = power asymmetry, violates §147 self-authorship | Dual-key scheme: client holds Key A, operator holds Key B, both required to decrypt |
| CF2 | No client read path to own traces | Client-facing export/read tool (client-held key decrypts) |
| CF3 | Tracing candor effect (Panopticon) completely unacknowledged | Add candor degradation as HIGH risk; dual-key removes Panopticon; offer no-trace coaching mode |
| CF4 | No content repurposing prohibition | Explicit prohibition: no training, marketing, case studies, methodology development without separate consent |
| CF5 | §150 (trace-to-update governance) not cited — most directly relevant doctrine clause | Cite §150; add trace-to-update boundary subsection |

### 19.4 Privacy/legal findings (must resolve before Phase 2/4)

| # | Finding | Fix |
|---|---------|-----|
| PL1 | Safe Harbor 18-identifier list incomplete (missing health plan beneficiary #s, certificate/license #s, vehicle identifiers, zip code rule) | Enumerate all 18; add zip-code population threshold |
| PL2 | Missing upstream BAA (covered entity → HUMMBL) | Two BAA layers: upstream (client→HUMMBL) + downstream (HUMMBL→Langfuse) |
| PL3 | 6-year HIPAA retention misapplied to de-identified trace data | Replace with 90-180d rolling; retain HIPAA *documentation* 6yr separately |
| PL4 | GDPR sub-processor analysis omits UpCloud + managed DB | Disclose UpCloud as sub-processor; DPA with UpCloud; correct controller/processor roles |
| PL5 | Safe Harbor vs Expert Determination method confusion | Pick Safe Harbor as legal basis; run falsification test as voluntary defense-in-depth |
| PL6 | Backup retention not addressed in purge verification | Document backup cycle; restore-and-redelete procedure; note in purge receipt |

### 19.5 Security findings (must resolve before Phase 2)

| # | Finding | Fix |
|---|---------|-----|
| S1 | Redaction chokepoint unenforceable | Export shim requires workload_class + calls redaction internally; fail-closed on assertion |
| S2 | Misclassification fails open (7-day PHI exposure) | PHI/PII patterns in Class D trace must block export (quarantine buffer) |
| S3 | AES-GCM downgrade path + unspecified nonce management | Strike hashlib fallback; specify nonce strategy (counter or 96-bit random with cap) |
| S4 | Kill switch not distributed | Bus ALERT broadcast + flush-time check + exclude langfuse_export from critical_tasks |
| S5 | No supply chain story (provenance, SBOM, scanning, pinning) | Pin by digest; Trivy/Grype scan gate; SBOM; patching SLA |
| S6 | VM compromise severity underrated (HIGH not MED); prompt injection via prompt management | Upgrade to HIGH; prompt hash verification; VM hardening spec |

### 19.6 Architecture findings (must resolve before Phase 2)

| # | Finding | Fix |
|---|---------|-----|
| A1 | stdlib-only claim false for OTel path | ADR-002: where OTel lives + whether ADR-001 is amended |
| A2 | Redaction unreachable for Codex/Claude Code | Proxy architecture (local trace proxy = sole Langfuse network path) OR Devin-only for sensitive classes |
| A3 | No routing mechanism for hybrid topology | Proxy routes by workload_class; or multi-endpoint exporter config |
| A4 | MCP 13th-server cascade not scoped | Update skill + dual-config + validation; fix #11/#12 numbering bug; consider rename to `mcp-fleet-config` |

### 19.7 Ops findings (must resolve before Phase 1)

| # | Finding | Fix |
|---|---------|-----|
| O1 | Phase 1 timeline predicated on unratified cloud plan | Add Phase 0 prerequisite gate (cloud plan ratified + VM + DB provisioned) |
| O2 | OTel emission is greenfield, not wiring | Add Phase 0.5: build instrumentation shim (2-4 weeks); mark all runtimes GREENFIELD |
| O3 | Skill class escalation advisory, no enforcement | Skill frontmatter declares workload_class; runtime injects into trace context |
| O4 | Consent revocation purge underspecified | Consent registry + automated purge trigger + 24h SLA requires automation |
| O5 | Operator single point of failure | Deputy key holder; escalation for unreviewed flags; SLA for purge response |
| O6 | Cost model incomplete | VM cost, DB storage projection, HIPAA cloud pricing, IPv4 allocation |

### 19.8 Disposition

**PROPOSAL STATUS: ADAPT — revisions required before promotion.**

- **Phase 1 (Class D, self-hosted)**: BLOCKED on O1 (cloud plan ratification) + O2 (instrumentation build) + S5 (supply chain) + A4 (MCP cascade). Unblocks after these 4 are resolved.
- **Phase 2 (Class C, PII redaction)**: BLOCKED on S1-S2 (redaction enforcement) + A1-A2 (architecture) + PL1/PL4/PL6 (privacy fixes).
- **Phase 3 (Class B, coaching encryption)**: BLOCKED on CF1-CF5 (coaching fidelity, veto lane) + C1 (AES-GCM constraint) + O4 (purge automation) + O5 (operator SPOF). This is the most heavily gated phase.
- **Phase 4 (Class A, PHI de-identification)**: BLOCKED on PL2 (upstream BAA) + PL3 (retention fix) + PL5 (method clarification) + S2 (misclassification block).

**Operator decisions still required (§12 D1-D7) plus new decisions from review:**
- D8: ADR-002 — amend ADR-001 for observability exports? (architecture A1)
- D9: Proxy architecture vs Devin-only for sensitive classes? (architecture A2)
- D10: Dual-key scheme for coaching? (coaching CF1) — **veto-gated**
- D11: No-trace coaching mode + client-authored journals as default? (coaching CF3)
- D12: Consent registry location + purge automation approach? (ops O4)

---

## 20. Operator Ratification (2026-08-20T21:10Z)

**Ratified by**: operator (Reuben), session 2026-08-20, host=[REDACTED: machine]
**Bus receipt**: pending (will be posted as STATUS with ratification summary)

All 12 decisions resolved. D10 veto-gate cleared (dual-key accepted).

| # | Decision | Ratified option | Notes |
|---|----------|-----------------|-------|
| D1 | Deployment topology | **Hybrid** — self-hosted UpCloud for B/C/D, HIPAA cloud for A | Per recommendation §3 |
| D2 | BAA execution timing | **Execute now** — sign BAA with Langfuse before first healthcare client | Operator chose earlier than recommended; de-id still required as defense-in-depth |
| D3 | Coaching consent clause | **Draft now** — legal-counsel agent drafts, attorney reviews | Per recommendation §12 |
| D4 | MCP server addition | **Expand to 13** — Langfuse additive, update mcp-fleet-config skill | Per recommendation §12; rename skill to `mcp-fleet-config` per A4 |
| D5 | Redaction pipeline location | **Build in hummbl-governance** — `observability/redaction.py`, stdlib-only | Per recommendation §12 |
| D6 | Trace volume budget | **Cap per class** — D unlimited, A/B/C 500/day initial | Per recommendation §12 |
| D7 | Eval feedback cadence | **Daily+weekly+per-release** | Per recommendation §12 |
| D8 | ADR-002 (OTel vs stdlib-only) | **Amend ADR-001** — allow OTel SDK as test-extra for observability exports | Resolves architecture A1; OTel scoped to agent runtimes, not library code |
| D9 | Redaction reachability | **Proxy architecture** — local trace proxy is sole Langfuse network path | Resolves architecture A2; works for Codex/Claude Code |
| D10 | Coaching key scheme | **Dual-key** — client Key A + operator Key B, both required | **Veto-gate cleared**. Resolves CF1. Removes Panopticon, preserves §147 self-authorship |
| D11 | No-trace coaching mode | **No-trace mode + client-authored journals as default** | Resolves CF3. Tracing is opt-in, not default-on |
| D12 | Consent registry | **In hummbl-governance** — `observability/consent_registry.py`, JSONL-backed, auto-purge 24h SLA | Resolves ops O4 |

### Phase unblock status (post-ratification)

- **Phase 1 (Class D, self-hosted)**: Still BLOCKED on O1 (cloud plan ratification) + O2 (instrumentation build) + S5 (supply chain) + A4 (MCP cascade). Langfuse decisions resolved but cloud migration plan is a separate ratification gate.
- **Phase 2 (Class C, PII redaction)**: BLOCKED on S1-S2 (redaction enforcement in proxy) + PL1/PL4/PL6 (privacy fixes). D5+D9 resolved the architecture; implementation remains.
- **Phase 3 (Class B, coaching encryption)**: D10+D11 resolved the veto-gate. Still BLOCKED on C1 (AES-GCM — D8 amends ADR-001 but `cryptography` lib needs scoping) + O5 (operator SPOF — dual-key partially resolves, deputy key holder still needed).
- **Phase 4 (Class A, PHI de-identification)**: D2 (execute BAA now) unblocks the legal gate. Still BLOCKED on PL2 (upstream BAA) + PL3 (retention fix) + PL5 (method clarification) + S2 (misclassification block).

### Next actions

1. Post ratification STATUS to bus
2. Update idea-pack Status field from DRAFT to RATIFIED-PENDING-IMPLEMENTATION
3. Add to operator-owned work queue: (a) execute BAA with Langfuse, (b) draft coaching consent clause via legal-counsel, (c) ratify cloud migration plan (separate gate)
4. ADR-002 draft: amend ADR-001 to permit OTel SDK as test-extra for observability exports only

**Full reviewer outputs**: archived at
`C:\Users\Owner\AppData\Local\Temp\devin.exe-overflows\` (5 overflow files, one per lane).
Key findings extracted above; full prose preserved in overflow artifacts.

---

## References

- Triage verdict: `clp-7bd3c73f23f5` (ADOPT, confidence 0.82)
- Langfuse repo: https://github.com/langfuse/langfuse (MIT, 32.8K stars)
- Langfuse MCP: https://langfuse.com/docs/api-and-data-platform/features/mcp-server
- Langfuse open-source licensing: https://langfuse.com/handbook/chapters/open-source
- HIPAA Safe Harbor: 45 CFR §164.514(b)(2)
- Doctrine hook: `hummbl-governance/docs/standards/HUMAN_AI_AGENCY_BOUNDARY.md:147`
- Cloud migration plan: `hummbl-governance/docs/research/idea-packs/2026-08-19-infrastructure-cloud-migration-plan.md`
- Managed DB reservation: `hummbl-governance/docs/research/idea-packs/2026-08-19-session-handoff-cloud-mission.md:176`
- 1Password charter: `hummbl-governance/docs/standards/1PASSWORD_CHARTER.md:111`
- MCP fleet standard: `~/.agents/skills/mcp-fleet-config-12server/SKILL.md`
- GDPR mapping: `hummbl-governance/docs/gdpr-mapping.md`
- SOC 2 mapping: `hummbl-governance/docs/soc2-mapping.md`
