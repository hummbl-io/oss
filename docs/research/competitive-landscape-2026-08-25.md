# HUMMBL OSS Competitive Landscape — Corrected Assessment

## Scope and method

This assessment inventories 287 active repositories in the `hummbl-io` GitHub
organization and compares HUMMBL's full capability surface against leading
adjacent open-source projects. The previous assessment (session 2026-08-25)
examined only the 1 public `oss` monorepo and incorrectly claimed HUMMBL
"refuses to do" several things that are built and running in private repos.
This document corrects that.

## HUMMBL capability inventory (287 repos)

### Governance (42 repos)

| Capability | Repos | Status |
|---|---|---|
| Governance kernel (K1-K11, D1-D7 invariants) | `hummbl-governance`, `hummbl-governance-kernel`, `kernel` | Published, in production use |
| Policy as code | `policy-as-code`, `governance-as-code`, `compliance-as-code` | Active |
| Runtime governance / safety envelopes | `agent-runtime-governance`, `hummbl-control`, `hummbl-interaction-control-plane` | Seed → active |
| Doctrine / constitution | `hummbl-doctrine` | Active |
| Cryptographic receipts for skill invocations | `krineia` | Active |
| Adversarial testing / wargaming | `hummbl-adversarial`, `hummbl-wargame`, `hummbl-worstcase`, `hummbl-premortem`, `adversary-emulation-playbook` | Active |
| Alignment / autonomy / RSI | `hummbl-alignment`, `hummbl-autonomy`, `hummbl-rsi`, `hummbl-agi` | Active |
| Compliance mapping (NIST, ISO, SOC 2, EU AI Act) | `hummbl-compliance`, `hummbl-legal`, `hummbl-transparency` | Active |
| Security auditing | `hummbl-security-auditor`, `security-as-code`, `hummbl-cyber`, `hummbl-cyber-workbench` | Active |
| Governance benchmarks | `governance-bench`, `assessment-lab` | Active |

### Integration adapters (hummbl-integrations, 40+ adapters)

| Category | Adapters |
|---|---|
| LLM providers | Anthropic, OpenAI, Azure OpenAI, Vertex AI, Vertex AI Search, Ollama, OpenRouter, Mercury |
| Agent protocols | A2A v1.0.1 (Agent Card publishing, discovery, task routing) |
| GitHub / DevOps | GitHub, Gitea CI supervisor, PR inspector |
| Google Workspace | Calendar, Docs, Drive, Sheets (OAuth) |
| Communications | Gmail, MS Graph, Resend, TTS |
| Financial | Stripe (incl. webhook handler), Alpaca (data + execution), Dune |
| Research | Supadata, BIF ingestion |
| Other | Linear, SecureClaw, security, mission mode, feed, cost tracker, arbiter |

Each adapter emits signed `AdapterReceipt`s on every call. Stdlib-only via
`urllib`. Circuit breaker integration via `hummbl_governance.circuit_breaker`.

### Cognition / memory (12 repos)

| Capability | Repos |
|---|---|
| Cognitive Ledger Protocol + Open Brain server | `hummbl-cognition` (published) |
| Living ledgers | `hummbl-living-ledgers` |
| Claim/evidence ledgers | `carnivore-claims-ledger`, `claim-evidence-ledger`, `peptide-evidence-ledger` |
| System prompt ledger | `hummbl-system-prompts` |
| Brainstorm / ideation | `hummbl-brainstorm` |

### Coordination / bus / mesh (9 repos)

| Capability | Repos |
|---|---|
| Append-only TSV coordination bus | `hummbl-bus` (published) |
| Multi-machine agent mesh (swarm dispatch, drift, health) | `hummbl-mesh` (3-machine operational) |
| Mesh ping / health | `hummbl-mesh-ping` |
| Chat bus | `chat-bus` |
| Corporate coordination | `hummbl-corporate` |
| Apex nexus | `apex-nexus` |

### Kernel / runtime (8 repos)

| Capability | Repos |
|---|---|
| Orchestration kernel | `hummbl-kernel` (published), `kernel` |
| Kernel factory (domain-specific kernels) | `hummbl-kernel-factory`, `hummbl-kernel-forge` |
| Execution receipts | `execution-receipts` |
| Spacetime reasoning | `hummbl-spacetime` |
| Agent control plane patterns | `agent-control-plane-patterns` |
| Agentic engineering patterns | `agentic-eng-patterns` |

### Reasoning (15 repos)

| Capability | Repos |
|---|---|
| 120 reasoning operators | `base120` (published) |
| Base120 protocol | `hummbl-base120-protocol` |
| Domain-specific lattices | `hummbl-lattice` |
| Reasoning benchmarks | `hummbl-reasoning-bench`, `hummbl-fractional-bench` |
| Framework crosswalks | `hummbl-framework-crosswalks`, `hummbl-crosswalk-engine` |
| Unified frameworks | `unified-frameworks` (USNF, USF, UNF, UGF, UFR) |
| Theory / formal foundations | `hummbl-theory` |
| Gameboard / gamified reasoning | `hummbl-gameboard` |
| Free model registry | `hummbl-free-models` (1782 entries, 32 providers) |

### Tuples / events (3 repos)

| Capability | Repos |
|---|---|
| Typed governance tuples | `hummbl-tuples` (published) |
| BaseN tuple system | `baseN`, `axis` |

### Compression (governed-compression, published)

KV cache compression and quantization with governance receipts. No direct
competitor does governance-governed compression.

### Observability / dashboard / production (hummbl-asi + hummbl-dashboard + hummbl-production)

| Capability | Repos |
|---|---|
| ASI framework (50+ modules) | `hummbl-asi` — observability daemon, fleet arbiter, health bridges, security metrics, predictive resilience, swarm observer, compliance watcher, krineia watcher, cost governor bridge, self-monitoring, task dedup |
| Python dashboard | `hummbl-dashboard` — fleet health, agent metrics, security dashboard, coordination dashboard |
| Next.js dashboard | `hummbl-production/dashboard` — agents, governance, posture pages |
| Public web surface | `hummbl-production/web` — full website with API docs |
| Real-time observability | `tributary` — typed stream-query language |
| Observability as code | `observability-as-code` |
| Telemetry | `hummbl-telemetry` |

### Evaluation / benchmarks (5 repos)

`hummbl-benchmarks`, `governance-bench`, `hummbl-eval` (evidence-governed
contracts with immutable Record/Relation envelopes, SHA-256 identities,
GateBench fixtures), `hummbl-reasoning-bench`, `hummbl-fractional-bench`.

### Agent fleet / SDK (30 repos)

`hummbl-agent-sdk`, `hummbl-120-agents`, `hummbl-skills`, `fleet-manifests`,
`fleet-runbooks`, `fleet-standard`, `agent-identity-kit`, `agent-tools`,
`agent-handoffs`, `agent-instruction-format`, `idp-spec` (Intelligent
Delegation Profile), `wags` (polyglot air-gappable peer review protocol),
`hummbl-meta-agent-systems`, `hummbl-validation`, `edge-agent-bench`.

### Physical AI

`hummbl-physical-ai` — dedicated physical AI governance.

### Social simulation

`hummbl-social-sim` — fleet-scale governed social simulation harness with
mixture-of-models scaling and reproducibility measurement.

### MCP servers (9 repos)

`hummbl-mcp`, `mcp-server`, `workspace-mcp`, `hummbl-toolkit`, plus
homebrew-tap, scoop-bucket, nix, homebrew-hummbl for package distribution.

### Knowledge / protocol / infrastructure as code

`knowledge-as-code`, `protocol-as-code`, `infrastructure-as-code`,
`model-routing-as-code`, `hummbl-iac` (chezmoi dotfiles, package management).

## Competitive comparison — corrected

### vs Microsoft Agent Governance Toolkit (AGT)

| Dimension | HUMMBL | Microsoft AGT |
|---|---|---|
| Governance primitives | Kill switch, circuit breaker, cost governor, delegation, audit, identity, schema validation, compliance mapper, capability fence, reasoning engine, health probe, lifecycle, physical governor, EAL + K1-K11 invariants, D1-D7 doctrine, contestability, canon registry, authority sweeper, trust adjuster | Agent SRE (kill switch, SLO, chaos), Agent Runtime (budget, privilege rings), Agent Mesh (discovery, trust), Agent Hypervisor (audit, delta), Agent Compliance (OWASP, policy lint), Agent OS (policy, lifecycle), Agent Control Spec (Rust core) |
| Framework adapters | 40+ adapters (Anthropic, OpenAI, Vertex, Azure, Ollama, OpenRouter, Google, GitHub, Linear, Stripe, Alpaca, Gmail, MS Graph, A2A, etc.) — each with signed AdapterReceipts | LangChain, CrewAI, OpenAI, AutoGen, Google ADK, Claude Code plugin |
| Agent protocols | A2A v1.0.1, MCP (7 MCP servers) | MCP, A2A |
| Policy DSL | Python objects + policy-as-code + governance-as-code + compliance-as-code repos | Rego (OPA) |
| Execution sandboxing | agent-runtime-governance (safety envelopes), hummbl-control, hummbl-interaction-control-plane | Four privilege rings (Rust core) |
| Compliance | NIST AI RMF, ISO 42001, SOC 2, EU AI Act crosswalks | OWASP Agentic Top 10 |
| Dashboard | Python dashboard + Next.js dashboard + public web surface | Not yet shipped |
| Observability | hummbl-asi (50+ modules), tributary (typed stream queries), observability-as-code | Agent SRE monitoring |
| Benchmarks | 5 benchmark/eval repos including evidence-governed contracts | Not yet shipped |
| Adversarial testing | 5 repos (adversarial, wargame, worstcase, premortem, adversary-emulation) | Chaos testing in Agent SRE |
| Physical AI | hummbl-physical-ai | Not shipped |
| Social simulation | hummbl-social-sim (fleet-scale, mixture-of-models) | Not shipped |
| Alignment / RSI / AGI | 4 repos (alignment, autonomy, rsi, agi) | Not shipped |
| Dependencies | Zero third-party runtime deps (stdlib only) in public packages | Rust core + Python + Rego |
| Air-gappable | Yes — public packages run with no network | No — requires external services |
| Multi-language | Python, JS/TS, Rust (planned), Homebrew, Scoop, Nix, winget | Python, Rust |
| Adoption | 0 stars, ~2,295 downloads/month (dogfooding) | Microsoft brand, new launch |
| Maturity | Alpha/Pre-Alpha (public), production (private fleet) | Public Preview |

**HUMMBL has broader scope.** AGT has deeper sandboxing (Rust privilege rings)
 and Rego integration. HUMMBL has formal invariant systems (K1-K11, D1-D7),
 regulatory compliance crosswalks, physical AI, social simulation, and
 alignment/RSI research that AGT doesn't ship.

**HUMMBL's constraint is visibility, not capability.** The public oss repo
 shows 9 packages. The 287-repo org shows a full system. AGT shows everything
 publicly because it's Microsoft. HUMMBL hides most of the system in private
 repos.

### vs Sponsio

| Dimension | HUMMBL | Sponsio |
|---|---|---|
| Runtime contract enforcement | Governance kernel with invariants + agent-runtime-governance safety envelopes | Linear Temporal Logic formulas, <0.01ms, zero LLM cost |
| OWASP coverage | hummbl-compliance + hummbl-security-auditor | All 10 OWASP Agentic Top 10 (2026) |
| Contract library | Policy-as-code + governance-as-code repos | 16 pre-built contract bundles |
| Framework adapters | 40+ adapters | LangChain, Claude, OpenAI, Google ADK, CrewAI, Vercel AI, MCP, Cursor, OpenClaw |
| Approach | Python objects + receipts | YAML contracts compiled to FSM |

**Sponsio is narrower but sharper.** HUMMBL has broader governance scope but
 Sponsio's LTL-based deterministic enforcement at <0.01ms is a deeper
 implementation of runtime contract checking than HUMMBL's Python-object
 approach.

### vs Mem0 / Letta (cognition)

| Dimension | HUMMBL | Mem0 | Letta |
|---|---|---|---|
| Memory architecture | Cognitive Ledger Protocol, 5-pool retrieval, append-only ledgers, claim/evidence ledgers | Persistent personalized memory | MemFS (git-backed), sleep-time compute |
| Provenance | Receipt-based on every operation | Basic provenance | Basic |
| Vector embeddings | Not in public packages (BM25 instead) | Yes | Yes |
| Cloud hosting | No | Yes | Yes |
| Framework adapters | Via hummbl-integrations | LangChain, LangGraph, CrewAI | Custom |
| UI | hummbl-dashboard + Next.js dashboard | Cloud dashboard | Desktop, web, TUI, Slack, Telegram, Discord |
| Adoption | ~200 downloads/month (cognition) | 62K stars | 18K stars |

**HUMMBL's cognition is architecturally distinctive (receipt provenance,
 append-only ledgers, 5-pool model) but lacks vector embeddings and cloud
 hosting.** The claim/evidence ledger pattern is unique — no competitor has
 structured claim tracking with contestability and confidence scoring.

### vs A2A Protocol

| Dimension | HUMMBL | A2A |
|---|---|---|
| Protocol implementation | A2A v1.0.1 adapter in hummbl-integrations (Agent Card, discovery, task routing) | Reference implementation, 5 SDKs |
| Transport | stdlib urllib | HTTP, gRPC, SSE |
| Governance overlay | Append-only TSV bus + trust tiers + Lamport clocks + receipts | None (protocol only) |
| Adoption | 0 external | 25K stars, Linux Foundation, AWS/Microsoft/IBM/SAP |

**A2A has won the protocol standardization war.** HUMMBL's A2A adapter
 correctly adopts the standard rather than competing. The differentiation is
 the governance overlay — trust tiers, Lamport clocks, and receipts on top of
 A2A messages. Position as "A2A + provenance + trust hierarchy," not
 "alternative to A2A."

### vs Temporal / DBOS (kernel)

| Dimension | HUMMBL | Temporal | DBOS |
|---|---|---|---|
| Durable execution | hummbl-kernel + execution-receipts | 9 years production | Postgres-backed library |
| Governance invariants | K1-K11, D1-D7, contestability, canon registry | None | None |
| Distributed | hummbl-mesh (3-machine operational) | Distributed | Single-process library |
| Languages | Python | Go, Java, Python, TS, PHP, .NET | Python, TS |
| UI | hummbl-dashboard | Web UI | None |
| Adoption | ~100 downloads/month (kernel) | 22K stars | 1.5K stars |

**HUMMBL kernel is not competing on workflow orchestration.** Its value is
 governance-guaranteed execution — the invariant system wrapped around
 execution. Position as "Temporal/DBOS + governance invariants," not
 "alternative to Temporal."

### vs CloudEvents / AG-UI (tuples/events)

| Dimension | HUMMBL | CloudEvents | AG-UI |
|---|---|---|---|
| Event format | Typed governance tuples + TupleSchemaRegistry | Spec 1.0 | ~16 event types |
| Governance semantics | AdversarialTupleGenerator, MerkleAnchor | None | None |
| Agent-user interaction | hummbl-interaction-control-plane | N/A | Bi-directional, real-time |
| Adoption | ~11 downloads/month (tuples) | 5.9K stars, CNCF graduated | New, CopilotKit/LangChain/CrewAI partnership |

**Tuples should align with CloudEvents format.** The governance typing layer
 (AdversarialTupleGenerator, MerkleAnchor, TupleSchemaRegistry) is the
 differentiator, not the tuple format itself.

## What's actually differentiated (corrected)

After inventorying all 287 repos, the real HUMMBL differentiation is:

1. **Formal invariant system (K1-K11, D1-D7)** — no competitor has
   mathematically-specified execution invariants with contestability and
   doctrine amendment. This is the governance kernel's core contribution.

2. **Receipt-governed provenance on every operation** — adapters emit
   AdapterReceipts, skill invocations emit Krineia receipts, executions emit
   execution receipts, memory operations emit ledger entries. No competitor
   has end-to-end receipt provenance across governance, cognition, bus, and
   integration layers.

3. **Zero-dependency + air-gappable public packages** — the oss repo's
   stdlib-only constraint means the core packages run anywhere with no
   network. No competitor offers this. AGT requires Rust + Python + Rego.
   Mem0 requires a database. Temporal requires a server.

4. **40+ integration adapters with signed receipts** — no governance
   competitor ships this many adapters. Each one emits a signed receipt on
   every call with circuit breaker integration.

5. **Regulatory compliance crosswalks** — NIST AI RMF, ISO 42001, SOC 2,
   EU AI Act. AGT has OWASP. Sponsio has OWASP. Neither has the regulatory
   crosswalks.

6. **Physical AI + social simulation + alignment/RSI research** — no
   governance competitor ships these. These are research bets that may
   become differentiators as the field matures.

7. **Multi-package distribution** — Homebrew, Scoop, Nix, winget, PyPI.
   No governance competitor ships this many distribution channels.

## What's at risk (corrected)

| Risk | Severity | Note |
|---|---|---|
| Microsoft AGT absorbs the governance niche | High but mitigated | HUMMBL has broader scope; AGT has Microsoft's brand. The window is differentiation, not feature parity. |
| Mem0/Letta make cognition irrelevant | Medium | HUMMBL's provenance and claim/evidence ledgers are distinctive. Vector embeddings gap is real. |
| A2A makes bus irrelevant as a protocol | Low | HUMMBL already has an A2A adapter. The bus is the storage/provenance layer, not a competing protocol. |
| Self-referential vocabulary blocks adoption | High | K1-K11, D1-D7, BaseNTuple, Cognitive Ledger Protocol, Krineia — these need market-language translations. |
| 0 stars, no external contributors | Critical | The capability exists. The visibility doesn't. |
| Public/private boundary hides the system | High | Visitors see 9 packages. The 287-repo system is invisible. |

## Strategic priorities (corrected)

1. **Make the full system visible.** The oss README should link to the public
   repos that demonstrate breadth — hummbl-integrations (40+ adapters),
   hummbl-dashboard, hummbl-eval, agent-runtime-governance, hummbl-mesh.
   Visitors need to see that HUMMBL has A2A support, a dashboard, benchmarks,
   and an ASI framework.

2. **Benchmark against competitors.** Every claim needs a number:
   - Kill switch activation latency vs AGT
   - Receipt generation overhead vs Temporal workflow history
   - Cognitive ledger retrieval vs Mem0
   - Install size vs AGT (zero deps vs Rust+Python+Rego)

3. **Translate the vocabulary.** Map HUMMBL terms to market terms:
   - K1-K11 invariants → "execution guarantees"
   - Cognitive Ledger Protocol → "agent memory with provenance"
   - BaseNTuple → "typed governance event"
   - Krineia → "cryptographic skill receipts"
   - Doctrine amendment → "policy update with audit trail"

4. **Ship 3 demos that matter.**
   - HUMMBL governance + LangChain agent with kill switch, cost governor, audit
   - HUMMBL cognition + Mem0 — provenance layer on top of Mem0's memory
   - HUMMBL kernel + Temporal — governance invariants wrapping Temporal workflows

5. **Get 10 external users.** Not 287 repos. 10 strangers who install a
   package, file a bug, and get a response.

6. **Position against AGT explicitly.** "Like Microsoft AGT? HUMMBL adds:
   receipt-governed provenance, K1-K11 invariants, regulatory compliance
   mapping, zero dependencies, air-gappable. HUMMBL doesn't do: Rust
   privilege rings, Rego DSL. Use them together."

## PyPI download baseline (2026-08-25)

| Package | 30-day | Total |
|---|---|---|
| hummbl-governance | 1,429 | 9,019 |
| hummbl-bus | 204 | 204 |
| hummbl-cognition | 207 | 207 |
| base120 | 210 | 210 |
| hummbl | 104 | 104 |
| hummbl-kernel | 102 | 102 |
| hummbl-tuples | 11 | 210 |
| hummbl-bif | 16 | 343 |
| governed-compression | 12 | 210 |
| **Total** | **2,295** | — |

Most traffic is dogfooding (fleet CI installs). The download tracker
(`tools/scripts/pypi_download_tracker.py`) runs daily via GitHub Actions and
will flag when the baseline deviates from the dogfooding pattern — the signal
that someone outside the fleet started installing.
