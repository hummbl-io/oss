# HUMMBL AI Governance Field Mapping & Provider-Neutral Agent Architecture
## Conversation Preservation Record and Research Archive

**Date:** 2026-08-23  
**Time context:** Morning session, America/New_York  
**Purpose:** Preserve the context, research findings, architecture reasoning, terminology distinctions, corrections, open questions, and proposed next steps developed in this conversation.  
**Status:** Working research record; not a final specification.  
**Primary themes:** HUMMBL OSS, AI governance open questions, field mapping, surveys, provider adapters, plugins, skills, MCP, local/remote execution boundaries, provider neutrality, and a detailed normalization of Google’s AI/agent ecosystem.

---

# 0. Why this document exists

This document preserves the full conceptual arc of the conversation rather than only the final answers.

The discussion began with an inspection of the public HUMMBL surface and moved into a broader question:

> How can public sources of unresolved AI-governance questions become inputs to a systematic field-mapping system?

From there, the conversation expanded into:

- AI-governance research agendas and explicitly published open questions
- the user’s existing IDP protocol and field-mapping work
- surveys as an additional source of signal
- Google Forms and other survey providers
- provider-neutral harness design
- standard-library-only foundations with adapters as the creative/extension layer
- clean separation of semantics, transport, storage, and provider
- local and remote MCP servers
- the distinction between plugins, skills, tools, adapters, hooks, and MCP servers
- whether Anthropic should be treated as structurally exceptional
- a deep dive into Google’s rapidly expanding and overlapping AI/agent product surface
- a normalization of Google’s branded products into reusable architectural primitives

The strongest unifying idea is:

> **Do not model brands first. Model primitives, contracts, capabilities, boundaries, and provenance first; bind brands/providers afterward.**

This is especially important because Google, Anthropic, OpenAI, and other providers increasingly expose overlapping primitives under different names.

---

# 1. Initial HUMMBL public-surface inspection

The conversation opened with a request to inspect `hummbl.io/OSS`.

The public HUMMBL site currently presents HUMMBL as open-source governance infrastructure for agentic AI. The current public framing emphasizes:

- scoped delegation
- runtime containment
- kill switches
- circuit breakers
- capability fences
- cost governors
- append-only evidence
- HMAC-backed receipts
- local/framework-independent controls
- zero third-party runtime dependencies in the Python core
- reproducible test evidence
- an explicit assurance boundary

The current public homepage states:

> “Control what AI agents can do. Prove what they actually did.”

The public package is currently described as `hummbl-governance`, Apache 2.0 licensed, with a Python standard-library-only runtime foundation.

Important public positioning observed:

1. **Governance is presented as a runtime problem, not merely a policy or dashboard problem.**
2. **Evidence is intended to remain inspectable and customer-owned.**
3. **The public assurance language is deliberately constrained.**
4. **The library does not claim that cryptographic integrity proves the truth or completeness of the underlying evidence.**
5. **The system distinguishes technical governance support from legal certification or compliance determinations.**

The site also exposes broader HUMMBL surfaces, including Base120 and public research.

## 1.1 Public HUMMBL research surface

The research page presents:

- **The Governance Tuple: An Atomic Record for Auditable Agentic AI Decision-Making**
- forthcoming work on delegation depth
- forthcoming work on kill-switch state machines
- forthcoming work on authorization threat modeling

The Governance Tuple is presented as:

`T = (C, D, E)`

where:

- `C` = CONTRACT
- `D` = DCT / Delegation Capability Token
- `E` = EVIDENCE

The intended contribution is to bind authorization, execution, and evidence into an auditable record rather than treating each independently.

## 1.2 Relevant HUMMBL architectural posture

The public HUMMBL method strongly reinforces the design direction discussed later in this chat:

> **governance primitives, not governance platforms**

The method page explicitly favors:

- small composable runtime primitives
- local inspection
- customer-owned audit trails
- standard-library-only Python
- open-source implementation
- runtime enforcement over after-the-fact dashboards

This is directly compatible with the user’s later statement that adapters should be the creative extension layer around a strict standard-library foundation.

### Primary HUMMBL sources

- HUMMBL homepage: https://hummbl.io/
- HUMMBL research: https://hummbl.io/research
- HUMMBL method: https://hummbl.io/method
- HUMMBL services: https://hummbl.io/services
- HUMMBL pricing: https://hummbl.io/pricing
- HUMMBL delegation-token primitive: https://hummbl.io/primitives/delegation-tokens
- HUMMBL playground / Base120 surface: https://hummbl.io/playground

---

# 2. The governance-open-questions origin

The user connected the present field-mapping effort to the history of their IDP protocol.

The user explained that part of the original stimulus came from reading a Google DeepMind governance paper that did not merely present conclusions but explicitly surfaced **open questions**.

That observation is important.

A published open question is not just prose. It can be treated as a structured research object.

A field-mapping system can therefore ingest:

```text
PUBLIC SOURCE
    ↓
EXPLICIT OPEN QUESTION
    ↓
NORMALIZED QUESTION OBJECT
    ↓
RELATIONSHIPS
    ↓
STATUS / EVIDENCE / RESPONSES
    ↓
FIELD MAP
```

This provides an alternative to treating a literature review as a pile of PDFs or summaries.

---

# 3. Public sources that explicitly expose AI-governance questions

## 3.1 Google DeepMind — global AI governance institutions

Google DeepMind’s 2023 public piece **“Exploring institutions for global AI governance”** is directly relevant.

It frames three high-level questions:

1. What specific AI benefits and risks need international management?
2. What governance functions do those benefits and risks require?
3. What organizations can best provide those functions?

It then examines four possible institutional models:

- Commission on Frontier AI
- Advanced AI Governance Organisation
- Frontier AI Collaborative
- AI Safety Project

Most importantly for this conversation, the page explicitly states that **many important open questions remain** regarding the viability of the models.

Examples include questions concerning:

- scientific uncertainty about advanced AI trajectories
- whether standards can keep pace with capability development
- how states can be incentivized to adopt or accept monitoring
- how to balance beneficial access against dangerous proliferation
- what safety research is better conducted collaboratively versus independently
- whether external safety researchers can obtain sufficient access to frontier systems

This is exactly the kind of source that can seed a question graph.

Source:

- https://deepmind.google/blog/exploring-institutions-for-global-ai-governance/

## 3.2 Allan Dafoe / GovAI — AI Governance: A Research Agenda

Allan Dafoe’s **AI Governance: A Research Agenda** is another canonical example.

GovAI describes the agenda as an attempt to:

- orient researchers to the AI-governance field
- identify plausibly important problems
- be relatively comprehensive in posing pivotal questions
- connect those questions to existing research

This is more than a conventional literature review.

It is effectively a **question-oriented field map**, though represented as a report rather than a live structured system.

The report contains question families around topics such as:

- international cooperation
- institutions
- standards
- verification
- enforcement
- strategic stability
- races
- power transitions
- technical governance
- political economy
- deployment and control

Primary source:

- https://cdn.governance.ai/GovAI-Research-Agenda.pdf

Supporting GovAI description:

- https://www.governance.ai/post/govai-annual-report-2018

## 3.3 Additional Google DeepMind sources that reinforce the open-question pattern

Later DeepMind work continues to produce explicit governance and policy questions.

Examples found during the research pass include:

### Securing the future of AI agents

Google DeepMind published an AI Control Roadmap in 2026 focused on securing internal systems against increasingly capable and imperfectly aligned AI.

- https://deepmind.google/blog/securing-the-future-of-ai-agents/

### Conjecture Machines / validation bottleneck in science

A July 2026 DeepMind policy paper argues that AI agents may create a validation bottleneck in science and raises questions about:

- validating AI-generated hypotheses
- agent-ready data
- access to scientific agents
- peer-review capacity

- https://deepmind.google/public-policy/conjecture-machines-ai-agents-and-the-new-validation-bottleneck-in-science/

### From AGI to ASI

A June 2026 DeepMind report explicitly identifies concrete open research questions concerning possible pathways and bottlenecks between AGI and more general superintelligence.

- https://deepmind.google/research/publications/239142/

These reinforce a broader design insight:

> Open questions are already scattered across papers, white papers, blogs, standards, research agendas, release notes, governance letters, and institutional reports. A field-mapping system can normalize them into one queryable structure.

---

# 4. The user’s field-mapping direction

The user described work on what was spoken as **“Rum’s field mapping”**. The exact formal spelling or definition was not established in the conversation, so this document preserves the phrase without inventing an expansion.

The key conceptual move was:

> surveys can be included, but surveys should not define the entire field-mapping system.

Instead, the map should combine heterogeneous evidence sources.

A survey is one input type among many.

Candidate source classes discussed or implied:

- academic papers
- technical reports
- standards
- regulation
- regulatory consultations
- government reports
- think-tank research agendas
- lab governance papers
- conference proceedings
- issue trackers
- GitHub repositories
- surveys
- expert interviews
- public comments
- agent-generated candidate questions
- internal research artifacts
- structured evaluations

---

# 5. A proposed field-mapping pipeline

A useful normalized pipeline emerged:

```text
SOURCE
  ↓
EXTRACT
  ↓
CLAIM / QUESTION
  ↓
NORMALIZE
  ↓
RELATE
  ↓
VERIFY
  ↓
MAP
  ↓
SURVEY
  ↓
AGGREGATE SIGNAL
  ↓
EVALUATE
  ↓
UPDATE / VERSION
```

This is deliberately not tied to a specific provider.

## 5.1 Possible minimal object model

The conversation proposed a first-pass schema containing entities such as:

```text
Source
Question
Claim
Evidence
Actor
Domain
Jurisdiction
Method
Response
Relationship
Evaluation
Version
```

Possible relationship vocabulary:

```text
SOURCE        → raises       → QUESTION
SOURCE        → supports     → CLAIM
SOURCE        → challenges   → CLAIM
QUESTION      → depends_on   → QUESTION
QUESTION      → decomposes   → QUESTION
QUESTION      → overlaps     → QUESTION
QUESTION      → contradicts  → QUESTION
QUESTION      → answered_by  → EVIDENCE
ACTOR         → proposes     → QUESTION
RESPONSE      → evaluates    → QUESTION
EVALUATION    → updates      → STATE
```

This turns a research agenda into a graph rather than a bibliography.

---

# 6. Surveys as one signal layer

The user asked whether Google Forms had improved and whether surveys could be incorporated.

The useful answer is yes, with an important qualification:

> Google Forms is useful as an ingestion surface, but it should be treated as an adapter-backed provider, not as the canonical data model.

Verified current Google Forms capabilities relevant to the conversation include:

- branching by response through **“Go to section based on answer”**
- storing form responses in a linked Google Sheet
- publishing/sharing forms
- prefilled links
- embedding forms
- response summaries
- using Forms with Sheets and other Google tooling

Google documents that branching is available for multiple-choice and dropdown questions.

Sources:

- Google Forms branching:
  https://support.google.com/docs/answer/141062
- Save responses in Google Sheets:
  https://support.google.com/docs/answer/2917686
- General Forms usage:
  https://support.google.com/docs/answer/6281888
- Updated Forms sharing model:
  https://support.google.com/docs/answer/16319311

### Important correction to the earlier voice discussion

Earlier in the conversation, file uploads were mentioned as one of Google Forms’ capabilities. This archive pass verified branching and Sheets integration directly but did **not** independently re-verify file-upload behavior. Therefore this document does not treat file upload as a verified finding from this research pass.

---

# 7. Survey-provider abstraction

The conversation proposed treating survey systems as interchangeable providers.

Candidate adapter family:

```text
survey/
├── google_forms
├── microsoft_forms
├── typeform
├── qualtrics
├── jotform
├── airtable_forms
├── custom_web
└── local
```

The important architectural principle is that HUMMBL should not ask:

```python
if provider == "google":
    ...
```

Instead, it should ask questions about capabilities:

```python
provider.supports("branching")
provider.supports("anonymous_response")
provider.supports("webhook")
provider.supports("file_upload")
provider.supports("update_form")
```

A conceptual capability manifest could include:

```text
create_form
read_schema
submit_response
read_responses
branching
anonymous_response
authenticated_response
file_upload
webhook
export
update_form
rate_limit
```

This separates **provider identity** from **capability semantics**.

---

# 8. Standard library foundation + adapters as creative layer

The user stated that they know how to build harnesses and adapters for third-party vendors and emphasized a standard-library-only foundation.

The architecture discussed here is strongly compatible with that stance.

A useful separation is:

```text
CORE
  ├── types
  ├── contracts
  ├── validation
  ├── provenance
  ├── policy primitives
  └── canonical interfaces

ADAPTER LAYER
  ├── vendor APIs
  ├── MCP implementations
  ├── survey providers
  ├── model providers
  ├── storage engines
  ├── knowledge systems
  └── specialized runtime bridges
```

The standard library becomes the stable semantic kernel.

Adapters absorb:

- vendor churn
- SDK churn
- authentication peculiarities
- transport differences
- API shape differences
- pagination
- retries
- provider-specific errors
- provider-specific metadata

This is a high-leverage architecture because it makes the **core contract stable while the edges remain replaceable**.

---

# 9. The three separations that should not collapse

The conversation identified several forms of coupling that should be actively prevented.

## 9.1 Semantics vs transport

“What does this capability mean?” must be independent from “how are messages moved?”

## 9.2 Semantics vs storage

A question, claim, evidence record, capability, or skill should not be defined by whether it happens to live in:

- JSON
- SQLite
- Neo4j
- Postgres
- a file
- Google Sheets
- Notion
- a remote API

## 9.3 Semantics vs provider

A “survey response” should not mean “Google Forms row.”

A “tool” should not mean “Anthropic tool.”

A “skill” should not mean “Google Antigravity SKILL.md.”

A “managed agent” should not mean “Google managed agent.”

The canonical model should survive provider replacement.

---

# 10. Raw, canonical, and derived data

One of the strongest architectural recommendations in the conversation was to distinguish three states of information.

## 10.1 Source / raw data

Exactly what was observed.

Examples:

- a sentence in a paper
- a survey response
- a vote
- a raw API event
- an agent output
- a source URL
- a retrieved timestamp

## 10.2 Canonical representation

The normalized internal representation.

Example:

```text
question_id
source_id
question_text
domain
jurisdiction
stakeholder
confidence
provenance
timestamp
```

## 10.3 Derived knowledge

Anything created by transformation or inference.

Examples:

- clusters
- rankings
- summaries
- inferred edges
- embeddings
- novelty scores
- urgency scores
- tractability scores
- consensus measures
- disagreement measures
- agent-generated taxonomies

### Invariant

> Derived data must not silently overwrite source data.

This is central to auditability.

---

# 11. Provenance as a first-class primitive

Every meaningful object should be able to answer:

> Where did this come from?

A useful baseline provenance record:

```text
source
source_type
creator
retrieved_at
published_at
extract_location
ingestion_method
transformations
model_or_tool_involved
confidence
license
visibility
version
```

Additional useful fields:

```text
content_hash
parent_record
derived_from[]
valid_from
valid_to
superseded_by
verification_status
reviewer
```

This becomes especially important when human and agent contributions coexist.

---

# 12. Human/agent symmetry — with provenance asymmetry

The conversation proposed giving humans and agents access to the same contribution verbs.

For example:

```text
propose
comment
challenge
rank
cluster
evaluate
revise
```

This can be useful because it makes human and machine participation comparable.

However, **their provenance must remain distinguishable**.

The resulting principle is:

> **same action vocabulary, different provenance**

That enables future research questions such as:

- Where do humans and agents converge?
- Where do they systematically disagree?
- Which governance problems do agents miss?
- Which “open” questions do agents correctly identify as already answered?
- Which issues are rated urgent by practitioners but neglected in published literature?
- How does question importance change across time?
- How does model-generated prioritization differ from expert prioritization?

The field map could therefore become a research instrument, not merely a knowledge base.

---

# 13. Plugins, skills, tools, adapters, hooks, and MCP servers

A central part of the conversation was terminology disambiguation.

These concepts should **not** be merged.

## 13.1 Core / standard library

**Question answered:** What does the system itself guarantee?

Core responsibilities might include:

- canonical types
- contract validation
- provenance
- stable lifecycle semantics
- capability manifests
- governance records
- extension boundaries

Core should have the lowest churn.

---

## 13.2 Adapter

**Question answered:** How does an external thing look like a canonical internal interface?

An adapter translates.

Examples:

```text
Google Forms API → SurveyProvider interface
Gemini API       → ModelProvider interface
Neo4j            → GraphStore interface
Remote MCP       → ToolProvider interface
```

An adapter is not necessarily a “capability” in the user-facing sense.

It is translation glue.

---

## 13.3 Tool

**Question answered:** What concrete operation can be invoked?

Examples:

```text
search_web()
create_issue()
send_email()
query_database()
run_test()
```

A tool may be:

- local
- remote
- built-in
- custom
- MCP-exposed
- native SDK
- shell-backed
- REST-backed

“Tool” should therefore be semantic, not transport-specific.

---

## 13.4 Skill

**Question answered:** What reusable expertise/procedure/context can an agent load or invoke?

A skill may contain:

- instructions
- workflow guidance
- references
- scripts
- examples
- schemas

A skill does not inherently imply:

- network transport
- a running server
- a process boundary
- a vendor

This distinction is increasingly supported by real provider ecosystems.

---

## 13.5 MCP server

**Question answered:** What tools/resources/capabilities are exposed across the Model Context Protocol boundary?

An MCP server is a protocol endpoint or process.

It may expose:

- tools
- resources
- prompts or other MCP primitives depending on protocol revision
- metadata/capabilities

An MCP server does **not** have to be remote.

---

## 13.6 Plugin

**Question answered:** What packaged extension is being installed into a host?

A plugin is a packaging/distribution/host-extension concept.

A plugin can contain:

- skills
- rules
- MCP server definitions
- hooks
- configuration
- scripts

Therefore:

```text
plugin ≠ skill
plugin ≠ MCP server
plugin ≠ tool
```

A plugin can package those things.

---

## 13.7 Hook

**Question answered:** What deterministic behavior should intercept a lifecycle event?

A hook is commonly used for:

- pre-flight checks
- post-processing
- policy gates
- formatting
- audit emission
- security checks
- allow/deny decisions

A useful distinction is:

```text
skill
    model-mediated guidance / expertise

tool
    invokable operation

hook
    lifecycle interception

plugin
    package / extension bundle

adapter
    translation boundary

MCP server
    protocol-exposed capability surface
```

---

# 14. MCP local vs remote — corrected model

The user correctly remembered that local MCP commonly uses **STDIO** and remote MCP commonly uses an HTTP transport.

The precise current terminology matters.

## 14.1 Standard transports

MCP historically standardized:

1. **stdio**
2. **Streamable HTTP**

Streamable HTTP replaced the older HTTP+SSE transport.

A 2025 MCP specification states:

- stdio: client launches server as subprocess and exchanges JSON-RPC via stdin/stdout
- Streamable HTTP: server runs independently and accepts HTTP requests at an MCP endpoint

Source:

- https://modelcontextprotocol.io/specification/2025-06-18/basic/transports

## 14.2 2026-07-28 MCP change: stateless HTTP core

The July 28, 2026 MCP release made a major change to remote operation.

The protocol-level HTTP design became stateless:

- the old initialization handshake was retired for the new revision
- `Mcp-Session-Id` was removed from the new remote core
- requests carry protocol/client/capability information directly
- capability discovery can be requested explicitly
- requests can land on arbitrary server instances
- standard load balancing becomes easier
- session-like application state can be represented explicitly rather than hidden in the transport

Source:

- https://blog.modelcontextprotocol.io/posts/2026-07-28/

This strongly supports the architectural rule:

> **MCP capability identity should not be defined by transport or deployment topology.**

## 14.3 Do not equate “local” with “stdio” ontologically

The useful practical mapping is:

```text
local MCP
    commonly → stdio

remote MCP
    commonly → Streamable HTTP
```

But the deeper abstraction is:

```text
MCP SERVER
    ↓
TRANSPORT
    ├── stdio
    └── Streamable HTTP
```

“Local” and “remote” describe topology/deployment.

“stdio” and “Streamable HTTP” describe transport.

Those dimensions should remain separate.

---

# 15. Capability extension vs boundary extension

A particularly useful distinction emerged:

## Axis A — capability extension

> What new thing can the system do?

Common mechanisms:

- skills
- tools
- plugins
- new workflows

## Axis B — boundary extension

> What new external system can the architecture communicate with?

Common mechanisms:

- adapters
- MCP
- APIs
- transport bindings
- provider connectors

These axes can intersect but should not be collapsed.

A new provider integration should not automatically create a new semantic capability.

A new semantic capability should not require a new provider.

---

# 16. Anthropic’s uniqueness — and why not to special-case it

The user asked whether Anthropic is more structurally unique than OpenAI, xAI, Google, or other model providers.

The conclusion was:

> Anthropic is historically distinctive, but should not be architecturally privileged.

Anthropic has had major influence through:

- MCP
- tool-use patterns
- explicit protocol thinking
- Claude Code extension patterns

But the broader ecosystem is converging around similar primitives:

- tools
- agent runtimes
- skills
- MCP
- plugins/extensions
- hooks
- evals
- observability
- managed execution
- capability registries

Therefore HUMMBL should avoid:

```text
if provider == "anthropic":
    special_architecture()
```

and prefer:

```text
capabilities = provider.describe_capabilities()
```

The durable rule is:

> **capabilities over vendors**

---

# 17. Google deep dive — why Google is confusing

Google is an excellent stress test for ontology design because the company exposes multiple overlapping AI stacks and repeatedly reuses terms such as:

- Gemini
- Agent
- Studio
- Platform
- Builder
- Runtime

The way to make Google understandable is to stop treating “Google AI” as one product.

A useful normalized stack is:

```text
model
  ↓
API
  ↓
framework / harness
  ↓
developer surface
  ↓
runtime
  ↓
enterprise control plane
  ↓
user-facing enterprise surface
  ↓
protocols / extensions
```

Google has products at nearly every layer.

---

# 18. Four useful Google pathways

A compact Google map:

```text
A. FAST EXPERIMENTATION
Google AI Studio
    ↓
Gemini API / Interactions API
    ↓
Gemini models + tools + managed agents


B. CODE-FIRST AGENT DEVELOPMENT
Antigravity IDE / Antigravity CLI
    ↓
ADK and/or Antigravity harness/SDK
    ↓
Agents CLI
    ↓
Cloud Run / Agent Runtime / GKE


C. ENTERPRISE AGENT PLATFORM
Gemini Enterprise Agent Platform
    ├── Agent Studio
    ├── Agent Runtime
    ├── Agent Gateway
    ├── Agent Registry
    ├── Agent Observability
    ├── Agent Identity
    ├── Agent Search
    ├── Skill Registry
    ├── Model Garden
    └── governance / IAM / evals / memory
          ↓
Gemini Enterprise app


D. SPECIALIZED PRODUCTS / FRAMEWORKS
Jules
Genkit
Firebase / Firebase AI
Deep Research
CodeMender
Data Agent Kit
etc.
```

This is not a perfect official taxonomy. It is a normalization layer intended to make the branded surface legible.

---

# 19. “Gemini” is a family name, not one product

The word “Gemini” can refer to fundamentally different layers.

| Name | Layer |
|---|---|
| Gemini models | foundation-model family |
| Gemini API | developer API |
| Interactions API | preferred interaction primitive for Gemini models/agents |
| Google AI Studio | browser developer/prototyping surface |
| Gemini app | end-user assistant |
| Gemini Enterprise | enterprise product family |
| Gemini Enterprise app | enterprise user-facing surface |
| Gemini Enterprise Agent Platform | cloud platform/control plane |

Therefore the phrase:

> “built on Gemini”

is under-specified.

A useful field map should always disambiguate the noun after “Gemini.”

---

# 20. Google AI Studio

Google AI Studio is now substantially more than a simple prompt playground.

Current Google documentation shows that Build mode can create:

- full-stack web apps
- native Android apps
- server-side Node.js environments
- React frontends by default
- GitHub-connected projects
- Cloud Run deployments
- server-side secrets
- multi-file projects

Google explicitly states that the Antigravity Agent / harness components power the Build mode experience.

Source:

- https://ai.google.dev/gemini-api/docs/aistudio-build-mode

Useful mental model:

> **Google AI Studio = low-friction browser development surface for Gemini applications and managed-agent experimentation.**

It should not be confused with **Agent Studio** in the enterprise platform.

---

# 21. Gemini API and the Interactions API

Google now recommends the **Interactions API** for new Gemini development.

The current documentation describes it as the preferred way to build with:

- Gemini models
- managed agents
- tool use
- multi-step orchestration
- stateful or stateless interactions
- observable execution steps
- background execution
- long-running tasks

Source:

- https://ai.google.dev/gemini-api/docs/interactions-overview
- https://ai.google.dev/gemini-api/docs/migrate-to-interactions

Key architectural features:

```text
Interaction
├── user input
├── execution steps
├── tool calls
├── tool results
├── model output
└── optional server-side state
```

Important current behavior:

- state can be chained with `previous_interaction_id`
- state storage can be disabled for stateless usage
- background execution can run long tasks
- models and agents share a common interaction surface

This represents a notable convergence toward a unified model/agent API.

---

# 22. Gemini API remote MCP

Google’s Interactions API can connect directly to remote MCP servers.

Current documented constraint:

- remote MCP must use **Streamable HTTP**
- legacy SSE MCP servers are not supported in this specific Gemini API remote-MCP integration

Source:

- https://ai.google.dev/gemini-api/docs/function-calling

This is an important distinction:

```text
MCP specification capability
    ≠
every provider’s MCP implementation capability
```

HUMMBL should therefore represent:

```text
provider
transport
supported_protocol_revision
supported_features
limitations
```

rather than assuming all MCP clients implement all MCP features.

---

# 23. Managed Agents on the Gemini API

Google now exposes **Managed Agents** through the Gemini API.

The main example is the **Antigravity agent**.

Google describes the managed-agent pattern as provisioning a hosted Linux sandbox where an agent can:

- reason
- execute code
- manage files
- use web tools
- persist working state
- run multi-step autonomous loops

Sources:

- https://ai.google.dev/gemini-api/docs/agents
- https://ai.google.dev/gemini-api/docs/antigravity-agent
- https://ai.google.dev/gemini-api/docs/custom-agents

The architecture matters because Google is exposing the **harness** itself as a managed primitive.

That means the stack is no longer merely:

```text
model + tool calling
```

It can be:

```text
managed harness
    ├── model
    ├── sandbox
    ├── tools
    ├── skills
    ├── files
    ├── execution loop
    └── environment
```

---

# 24. Antigravity

Google Antigravity is an agent-first development platform introduced in 2025 and expanded in 2026.

Google describes it as more than an editor: it combines a coding environment with a manager surface for deploying autonomous agents across:

- editor
- terminal
- browser

Source:

- https://developers.googleblog.com/build-with-google-antigravity-our-new-agentic-development-platform/
- https://www.antigravity.google/product/antigravity-2

Antigravity 2.0 emphasizes:

- parallel agents
- dynamic subagents
- scheduled tasks
- artifacts
- projects
- scoped permissions
- skills
- MCP
- hooks

A useful mental model is:

> **Antigravity = Google’s agent-first developer environment plus a shared agent harness.**

---

# 25. Gemini CLI → Antigravity CLI transition

Google announced on May 19, 2026 that it was transitioning the consumer/community Gemini CLI path toward **Antigravity CLI**.

Google’s reasoning was that workflows had moved beyond a terminal chatbot toward:

- asynchronous execution
- multiple agents
- shared backend/harness
- larger task-oriented workflows

Google states that Antigravity CLI preserves important Gemini CLI concepts including:

- Agent Skills
- Hooks
- Subagents
- Extensions, now represented as Antigravity plugins

Source:

- https://developers.googleblog.com/an-important-update-transitioning-gemini-cli-to-antigravity-cli/

This is highly relevant to field mapping because documentation may mention a historical name even when the underlying primitive continues under a new product.

Therefore each field-map object should consider:

```text
canonical_name
aliases[]
introduced_at
deprecated_at
superseded_by
valid_from
valid_to
```

---

# 26. Antigravity plugins

Google Antigravity’s plugin model gives strong real-world support to the distinctions developed earlier in the conversation.

Google documents plugins as **namespaced bundles** that can group:

- skills
- rules
- MCP servers
- hooks

Example conceptual structure:

```text
plugins/<plugin-name>/
├── plugin.json
├── mcp_config.json
├── hooks.json
├── skills/
│   └── <skill-name>/
│       └── SKILL.md
└── rules/
    └── <rule-name>.md
```

Source:

- https://antigravity.google/docs/plugins/

This is direct evidence that:

```text
plugin ≠ skill
plugin ≠ MCP server
plugin ≠ hook
```

The plugin is the bundle/host-extension boundary.

---

# 27. Google Agent Skills

Google’s tooling increasingly treats skills as portable contextual capability packages.

Agents CLI describes its own skills as context files installed into coding agents such as:

- Antigravity CLI
- Claude Code
- GitHub Copilot
- and, in tutorials, Codex

These skills teach the coding agent how to work with:

- ADK
- deployment
- evaluations
- observability
- publishing
- scaffolding
- the full agent lifecycle

Source:

- https://google.github.io/agents-cli/reference/skills/

This is especially important because the **coding agent can be non-Google** while the skill teaches it to operate Google infrastructure.

That is a concrete example of:

> skill semantics separated from model/provider identity.

---

# 28. Agent Plugins 1.0.0

On August 6, 2026 Google announced its participation as a core maintainer of **Agent Plugins 1.0.0**, described as an open, vendor-neutral specification.

The specification packages:

- Agent Skills
- MCP servers
- associated extension material

into portable plugins.

Google explicitly frames the problem as eliminating different wrappers/configuration formats across AI clients.

Source:

- https://developers.googleblog.com/agent-plugins-package-your-skills-tools-and-more/

This provides strong prior-art support for the architecture discussed in the conversation:

```text
Skill       = expertise / procedure
MCP server  = tool/resource interface
Plugin      = portable extension package
```

---

# 29. Hooks in Google’s architecture

Google Antigravity documents hooks as lifecycle interception mechanisms.

Hooks can run immediately before or after agent actions.

Examples include:

- policy checks
- formatting
- preflight validation
- post-generation formatting
- security controls

Google’s Antigravity CLI docs describe hooks as useful for automated pre-flight checks or post-generation actions.

Sources:

- https://antigravity.google/docs/cli/plugins
- https://developers.googleblog.com/evolving-spec-driven-development-conductor-now-supports-antigravity/

This supports a strong governance distinction:

> **skills are generally model-mediated context; hooks can be deterministic lifecycle enforcement.**

That is especially relevant to HUMMBL.

---

# 30. ADK — Agent Development Kit

ADK is Google’s agent-development framework.

Within the current Google stack, a useful abstraction is:

> **ADK = code-level framework for building and orchestrating agents.**

Agents CLI’s current ADK template builds a ReAct-style agent and automatically exposes A2A routes.

Source:

- https://google.github.io/agents-cli/guide/templates/

ADK supports concepts including:

- agents
- tools
- instructions
- sequential agents
- parallel agents
- loop agents
- state/context
- callbacks
- MCP tooling
- A2A interoperability

Therefore:

```text
ADK
    ≠ Antigravity
    ≠ Agents CLI
    ≠ Agent Runtime
```

They occupy different layers.

---

# 31. Agents CLI

Google’s **Agents CLI** is a different product from Antigravity CLI.

This distinction is easy to miss.

## Antigravity CLI

Primary role:

- coding-agent environment
- task execution
- multi-agent development work

## Agents CLI

Primary role:

- agent-development lifecycle toolchain

Current Agents CLI lifecycle:

```text
understand
scaffold
build
evaluate
deploy
publish
observe
```

Sources:

- https://google.github.io/agents-cli/guide/development/
- https://google.github.io/agents-cli/cli/
- https://google.github.io/agents-cli/guide/quickstart-tutorial/

One particularly important pattern:

```text
Codex / Claude Code / Antigravity
        ↓ loads Google skills
Agents CLI knowledge
        ↓
builds an ADK agent
        ↓
deploys to Cloud Run / Agent Runtime / GKE
```

The coding agent itself does not need to be Google’s.

---

# 32. A2A in current Google agent tooling

Agents CLI currently states that Python ADK agents expose the **Agent-to-Agent (A2A) protocol** automatically in its standard template.

Source:

- https://google.github.io/agents-cli/guide/templates/

This reinforces a clean separation:

```text
ADK
    builds agent implementation

A2A
    exposes agent-to-agent interoperability
```

A2A is not merely another tool protocol.

---

# 33. Gemini Enterprise Agent Platform

Google launched **Gemini Enterprise Agent Platform** on April 22, 2026.

Google explicitly describes it as the evolution of Vertex AI.

It combines:

- model access
- model building
- agent building
- orchestration
- DevOps
- security
- governance
- runtime
- observability
- enterprise integration

Source:

- https://cloud.google.com/blog/products/ai-machine-learning/introducing-gemini-enterprise-agent-platform

A useful abstraction:

```text
Vertex AI
    ↓ evolved into / incorporated into
Gemini Enterprise Agent Platform
```

This is a major reason Google documentation can appear contradictory across time.

---

# 34. Google rename map

Google’s current Agent Platform release notes explicitly list naming transitions.

Examples:

```text
Vertex AI Platform          → Agent Platform
Generative AI on Vertex AI  → Generative AI
Vertex AI Studio            → Agent Studio
Vertex AI API               → Agent Platform API
Vertex AI Model Garden      → Model Garden
Vertex AI Search            → Agent Search
Vertex AI Experiments       → Experiments on Agent Platform
Vertex AI Model Monitoring  → Model Monitoring
```

Agent Builder changes include:

```text
Agent Engine            → Agent Runtime
Agent Builder Sessions  → Agent Platform Sessions
Memory Bank             → Agent Platform Memory Bank
```

Source:

- https://docs.cloud.google.com/gemini-enterprise-agent-platform/release-notes

This validates the need for alias and temporal metadata in a field map.

---

# 35. Agent Runtime

**Agent Runtime** is the current managed production-runtime term that replaced the older **Agent Engine** name in the new Agent Platform nomenclature.

Useful distinction:

```text
ADK
    framework

Agent Runtime
    managed execution environment
```

Google currently supports multiple deployment targets around its tooling, including:

- Agent Runtime
- Cloud Run
- GKE

Source:

- https://google.github.io/agents-cli/cli/
- https://docs.cloud.google.com/gemini-enterprise-agent-platform/release-notes

---

# 36. Agent Gateway

Agent Gateway is one of the most important Google components for governance architecture.

Google defines Agent Gateway as the networking component that secures and governs connectivity across:

- users ↔ agents
- agents ↔ tools
- agents ↔ agents

The release notes show Agent Gateway reaching GA on June 18, 2026.

Source:

- https://docs.cloud.google.com/gemini-enterprise-agent-platform/release-notes

This maps naturally to a **boundary-control primitive**.

A provider-neutral ontology might classify Agent Gateway as:

```text
BoundaryEnforcement
ConnectivityPolicy
IdentityMediation
RoutingControl
```

rather than as “another agent product.”

---

# 37. Agent Registry

Google’s Agent Registry is described as a centralized catalog for storing, discovering, and governing:

- AI agents
- MCP servers
- tools

Source:

- https://docs.cloud.google.com/gemini-enterprise-agent-platform/release-notes

This is especially relevant to HUMMBL because a provider-neutral registry abstraction may eventually need to support all three object classes.

Potential normalized interface:

```text
register()
discover()
describe()
authorize()
deprecate()
version()
resolve_capabilities()
```

---

# 38. Agent Identity

Google’s Agent Platform release notes describe **Agent Identity** as a mechanism allowing an agent to authenticate:

- as itself
- or on behalf of an end user

and access:

- MCP servers
- cloud resources
- endpoints
- other agents

Source:

- https://docs.cloud.google.com/gemini-enterprise-agent-platform/release-notes

This is a crucial governance primitive because “agent identity” is not identical to:

- human user identity
- service account identity
- model identity
- session identity
- tool identity

A robust field map should distinguish these.

---

# 39. Agent Observability

Google’s Agent Observability provides visibility into:

- agent performance
- behavior
- health
- MCP server behavior
- traces
- resource use

Google also supports OpenTelemetry-aligned metrics for ADK agents.

Source:

- https://docs.cloud.google.com/gemini-enterprise-agent-platform/release-notes

This suggests another reusable primitive family:

```text
Trace
Span
Action
ToolCall
PolicyDecision
CostEvent
Evaluation
RuntimeMetric
```

These should not be Google-specific in HUMMBL.

---

# 40. Skill Registry

As of May 2026, Google’s Agent Platform includes a **Skill Registry** in preview for storing/discovering agent skills as self-contained packages containing:

- instructions
- code
- documentation

Source:

- https://docs.cloud.google.com/gemini-enterprise-agent-platform/release-notes

This is another strong indication that “skill” is stabilizing as an independent ecosystem primitive.

---

# 41. Managed Agents API on Agent Platform

Google also exposes a Managed Agents API in Agent Platform.

It can run agents built from configuration using the Antigravity harness inside managed isolated sandbox environments with tools and skills.

Source:

- https://docs.cloud.google.com/gemini-enterprise-agent-platform/release-notes

This means Google now has both:

- Gemini API managed-agent surfaces
- enterprise Agent Platform managed-agent surfaces

These should be treated as related implementations at different product/control-plane boundaries, not automatically as identical services.

---

# 42. Gemini Enterprise app

The **Gemini Enterprise app** should be separated from the developer platform.

Useful normalized distinction:

```text
Gemini Enterprise Agent Platform
    = build / deploy / govern / operate

Gemini Enterprise app
    = enterprise-facing consumption / discovery / orchestration surface
```

Google positions the Agent Platform as a backend/control plane for agent creation and governance and the Gemini Enterprise app as a front door for organizational use.

Sources:

- https://cloud.google.com/blog/products/ai-machine-learning/introducing-gemini-enterprise-agent-platform
- https://cloud.google.com/blog/products/ai-machine-learning/the-new-gemini-enterprise-one-platform-for-agent-development

---

# 43. AI Studio vs Agent Studio

These names are easy to confuse.

## Google AI Studio

- developer-focused
- lightweight
- Gemini API centered
- browser-based
- prototyping and app-building

## Agent Studio

- enterprise platform surface
- formerly associated with Vertex AI Studio naming transition
- part of the Gemini Enterprise Agent Platform context

Rule of thumb:

```text
AI Studio
    → Gemini API / rapid developer path

Agent Studio
    → enterprise Agent Platform path
```

---

# 44. Genkit

The conversation characterized Genkit as a separate framework with meaningful overlap with ADK.

A useful working distinction is:

```text
ADK
    agent-first framework

Genkit
    application-first AI framework with agentic capabilities
```

This distinction should remain a **working model**, not an ontological law.

The important point is that two frameworks can expose overlapping capabilities while optimizing for different developer contexts.

---

# 45. Firebase Studio sunset

Google’s current Firebase documentation confirms that Firebase Studio is being sunset.

Timeline:

- March 19, 2026: sunset announced
- June 22, 2026: new workspace creation and new signups disabled
- March 22, 2027: shutdown

Google explicitly directs developers toward:

- **Google AI Studio** for rapid browser-based prototyping
- **Google Antigravity** for code-first agentic development

Source:

- https://firebase.google.com/docs/studio/migrating-project

This is evidence of product-surface consolidation.

---

# 46. Jules

Jules is a specialized autonomous software-engineering agent.

Google describes Jules as able to:

- integrate with GitHub
- clone a repository into a cloud VM
- install dependencies
- modify code
- run tests
- create branches / PRs
- operate asynchronously
- expose API/CLI surfaces

Sources:

- https://jules.google/
- https://jules.google/docs/faq/

Jules also supports a curated list of MCP integrations and explicitly frames the limited allowlist as a security measure.

Source:

- https://jules.google/docs/changelog/2026-02-02/

Useful distinction:

```text
Antigravity
    developer environment / multi-agent harness

Jules
    delegated autonomous software-engineering worker
```

---

# 47. Google’s protocol map

Google published a useful 2026 guide distinguishing several agent protocols.

The guide treats them as complementary rather than competing.

The main boundaries:

```text
MCP
    agents/models ↔ tools and data

A2A
    agent ↔ agent

UCP
    commerce

AP2
    payment authorization

A2UI
    declarative agent-generated UI

AG-UI
    agent ↔ frontend event streaming
```

Source:

- https://developers.googleblog.com/developers-guide-to-ai-agent-protocols/

This is a very useful precedent for HUMMBL:

> A protocol should be named and modeled by the boundary/problem it solves, not merely by its popularity.

---

# 48. MCP vs A2A

The simplest normalized distinction is:

```text
MCP
    agent → capability/tool/data

A2A
    agent → agent
```

This matters because an agent communicating over A2A does not necessarily expose its internal tools, memory, or implementation details to the other agent.

Therefore:

```text
tool interoperability
    ≠
agent interoperability
```

That distinction should remain explicit in a provider-neutral ontology.

---

# 49. Plugins in Google are not one thing

The conversation identified an important terminology hazard.

Google currently uses “plugin” at multiple scopes.

Examples include:

1. **Antigravity plugins**
   - extend the Antigravity host
   - package skills, rules, MCP config, hooks

2. **Framework-level or application-level plugin concepts**
   - behavior added within an agent/application framework

3. **Agent Plugins specification**
   - portable, vendor-neutral extension package

Therefore a canonical plugin record should include qualifiers such as:

```text
plugin.scope
plugin.host
plugin.lifecycle
plugin.contents
plugin.specification
plugin.version
```

“Plugin” by itself is too ambiguous to function as a complete ontology primitive.

---

# 50. Google normalized into primitives

The branded surface can be simplified into a provider-neutral mapping.

| Primitive | Google example |
|---|---|
| Foundation model | Gemini / Gemma |
| Model API | Gemini API / Agent Platform API |
| Interaction primitive | Interactions API |
| Built-in tool | Search, Maps, Code Execution, URL Context, etc. |
| Tool protocol | MCP |
| Agent framework | ADK |
| Application AI framework | Genkit |
| Managed harness | Antigravity Agent / Managed Agents |
| Coding harness/environment | Antigravity |
| Specialized coding agent | Jules |
| Lifecycle tooling | Agents CLI |
| Skill | Agent Skill |
| Skill registry | Skill Registry |
| Extension package | Agent Plugin / Antigravity Plugin |
| Lifecycle interception | Hook |
| Agent protocol | A2A |
| Runtime | Agent Runtime |
| Boundary control | Agent Gateway |
| Agent/tool catalog | Agent Registry |
| Agent auth | Agent Identity |
| Observability | Agent Observability |
| Enterprise control plane | Gemini Enterprise Agent Platform |
| Enterprise user surface | Gemini Enterprise app |
| Rapid browser builder | Google AI Studio |
| Enterprise builder surface | Agent Studio |
| Agent-generated UI protocol | A2UI |
| Frontend event protocol | AG-UI |
| Commerce protocol | UCP |
| Payment authorization | AP2 |

This table is one of the highest-value outputs of the conversation.

---

# 51. What HUMMBL should not do

A provider-neutral HUMMBL architecture should probably avoid a single monolithic object like:

```text
GoogleAdapter
```

Google is too broad for that abstraction.

A better shape is capability-oriented:

```text
providers/
└── google/
    ├── models/
    ├── managed_agents/
    ├── runtimes/
    ├── enterprise/
    ├── forms/
    └── provider_specific_tools/
```

However, cross-provider standards should **not** be nested under Google merely because Google supports them.

For example:

```text
MCP
A2A
Agent Skills
Agent Plugins
```

should be represented as standards/capabilities in their own right whenever they are genuinely cross-provider.

Google then declares its support for them.

---

# 52. Proposed provider-neutral architecture

A useful high-level architecture from the conversation:

```text
                  HUMMBL CORE
                      │
               canonical contracts
                      │
              ┌───────┴────────┐
              │                │
           HARNESS          STORAGE
              │
       capability registry
              │
     ┌────────┼─────────┐
     │        │         │
   Skills   Plugins   Adapters
     │        │         │
     └────────┼─────────┘
              │
             MCP
          ┌───┴────┐
        STDIO    HTTP
```

This drawing is intentionally simplified.

A more rigorous version should separate:

- capability
- package
- process
- protocol
- transport
- topology
- runtime
- provider

rather than placing them in one inheritance tree.

---

# 53. Better multidimensional model

Instead of forcing everything into one hierarchy, represent an extension/capability using orthogonal dimensions.

Example:

```text
Capability
    semantic_id
    operations[]
    required_inputs
    outputs
    risk_class

Implementation
    provider
    runtime
    version

Exposure
    protocol
    transport
    endpoint_or_command

Packaging
    plugin
    skill
    distribution_format

Governance
    permissions
    provenance
    policy
    audit
    lifecycle
```

This avoids false equivalences.

For example, the same semantic tool can be:

- local Python function
- local MCP over stdio
- remote MCP over Streamable HTTP
- REST API
- provider-native tool

without becoming five different capabilities.

---

# 54. Capability manifest idea

A small capability manifest was proposed as a way for the harness to discover what a provider can do.

Conceptual example:

```yaml
provider: example
version: 1

capabilities:
  tools:
    function_calling: true
    remote_mcp: true
    local_mcp: false

  agents:
    managed: true
    background_execution: true

  transport:
    streamable_http: true
    stdio: false

  surveys:
    create_form: false
    branching: false

  governance:
    audit_events: partial
    identity_delegation: true
```

The exact schema is not established.

The important idea is:

> the harness should discover support declaratively rather than infer behavior from a vendor name.

---

# 55. Governance field-map + survey experiment

A concrete experiment emerged.

## Phase 1 — literature-derived question map

Collect open questions from authoritative sources.

For every question capture:

```text
question_id
question_text
exact_or_derived
source
author
date
domain
jurisdiction
stakeholder
scope
dependencies
importance_claim
answer_status
confidence
provenance
```

## Phase 2 — practitioner survey

Ask experts/practitioners to:

1. nominate unresolved questions
2. rank existing questions
3. flag questions they believe are already resolved
4. identify missing domains
5. estimate urgency
6. estimate tractability

## Phase 3 — agent-generated question set

Have models/agents independently:

- propose missing questions
- rank the literature-derived set
- challenge whether questions are truly open
- identify dependencies
- attempt to locate existing answers

## Phase 4 — compare signal

Compare:

```text
literature signal
    vs
human survey signal
    vs
agent-generated signal
```

Possible measurements:

- overlap
- rank correlation
- novelty
- false-open rate
- missed-question rate
- domain coverage
- temporal persistence
- source diversity
- stakeholder diversity
- confidence calibration

This comparison could itself become a publishable research artifact.

---

# 56. Testing the divisor of responsibility: what belongs where?

A major architecture risk is hidden coupling.

The system should be tested against questions like:

- Can the same skill run against local and remote implementations?
- Can an MCP server change transport without changing semantic identity?
- Can a provider disappear without corrupting canonical records?
- Can two providers expose the same capability?
- Can one plugin package several skills and MCP servers?
- Can a skill exist without an MCP server?
- Can an MCP server exist without a HUMMBL plugin?
- Can raw survey data be reconstructed from derived results?
- Can every derived question be traced to its transformations?
- Can agent-generated content be distinguished from published-source content?
- Can a provider-specific feature be represented without contaminating core semantics?
- Can the field map function offline with only standard-library components?
- Can the canonical schema survive a provider rename?
- Can the system distinguish a product rename from a genuinely new product?
- Can one semantic capability have multiple simultaneous implementations?
- Can policy reject an implementation without deleting the underlying capability?

If these fail, the architecture probably has hidden provider coupling.

---

# 57. Temporal provenance is necessary

Google’s naming churn exposed a broader field-mapping requirement.

A source can be accurate when published and misleading later.

Therefore provenance should include at least two time concepts:

```text
retrieved_at
published_at
```

But for evolving concepts, add:

```text
valid_from
valid_to
superseded_at
superseded_by
```

This allows the system to answer:

- What was this called in 2025?
- What is it called now?
- Was the old name wrong, deprecated, or simply historical?
- When did the conceptual boundary change?

This is particularly important for AI governance because:

- products change
- standards change
- laws phase in
- models deprecate
- safety policies evolve
- terminology changes faster than academic publication cycles

---

# 58. Claim status should be explicit

This archive exposes a useful distinction among:

```text
VERIFIED
    directly supported by authoritative current source

SUPPORTED
    supported by credible source but with scope/temporal caveats

WORKING MODEL
    useful architectural interpretation

PROPOSAL
    architecture suggested in conversation

UNVERIFIED CHAT CLAIM
    stated earlier but not independently validated

DEPRECATED / SUPERSEDED
    historically true but no longer current
```

This status system should be considered for the field map itself.

---

# 59. Corrections and hardening from the chat

Several earlier conversational answers were directionally useful but required precision.

## 59.1 MCP remote transport

Earlier phrasing used “HTTPS or something like that.”

Corrected form:

- MCP standard transport is **Streamable HTTP**
- deployments will commonly use HTTPS in production
- “HTTPS” is not the protocol name
- legacy HTTP+SSE has been replaced/deprecated by Streamable HTTP

## 59.2 MCP server ≠ remote server

An MCP server can be:

- local child process over stdio
- remote service over Streamable HTTP
- implemented through other supported/custom transport patterns

Therefore “server” is a role, not a location.

## 59.3 Plugin ≠ skill ≠ MCP server

Google’s current Antigravity documentation directly confirms that one plugin can contain:

- skills
- rules
- MCP servers
- hooks

This strongly supports keeping those primitives distinct.

## 59.4 Anthropic should not be the ontology

Anthropic is influential but should not define HUMMBL’s internal schema.

The ecosystem is converging.

## 59.5 Google’s product names should not become primitives

Names like:

- Agent Studio
- Agent Builder
- Agent Runtime
- Antigravity
- Gemini Enterprise

should be mapped onto stable internal concepts.

---

# 60. Potential HUMMBL canonical terminology

A possible vocabulary for further work:

```text
Entity
Relation
Boundary
State
Perspective
Agency
Identity

Capability
Tool
Skill
Plugin
Hook
Adapter

Provider
Implementation
Runtime
Harness
Protocol
Transport
Topology

Source
Claim
Question
Evidence
Response
Evaluation

Provenance
Version
Policy
Permission
Authority
Receipt
Trace
```

This is not yet a final ontology.

The important rule is that a term earns its place by having a distinct job.

---

# 61. Proposed research matrix across providers

The conversation suggested repeating the Google normalization process across providers.

Candidate comparison set:

```text
Google
Anthropic
OpenAI
Microsoft
AWS
xAI
Cloudflare
```

Candidate matrix:

| Capability / Primitive | Google | Anthropic | OpenAI | Microsoft | AWS | xAI | Cloudflare |
|---|---|---|---|---|---|---|---|
| Foundation models |  |  |  |  |  |  |  |
| Tool calling |  |  |  |  |  |  |  |
| Built-in tools |  |  |  |  |  |  |  |
| MCP client |  |  |  |  |  |  |  |
| Remote MCP |  |  |  |  |  |  |  |
| Local MCP |  |  |  |  |  |  |  |
| Skills |  |  |  |  |  |  |  |
| Plugins/extensions |  |  |  |  |  |  |  |
| Hooks |  |  |  |  |  |  |  |
| Managed agents |  |  |  |  |  |  |  |
| Agent framework |  |  |  |  |  |  |  |
| Managed runtime |  |  |  |  |  |  |  |
| Agent identity |  |  |  |  |  |  |  |
| Agent registry |  |  |  |  |  |  |  |
| Agent gateway |  |  |  |  |  |  |  |
| Observability |  |  |  |  |  |  |  |
| Evals |  |  |  |  |  |  |  |
| A2A support |  |  |  |  |  |  |  |
| Background tasks |  |  |  |  |  |  |  |
| Sandboxed execution |  |  |  |  |  |  |  |
| Provider-neutral plugin format |  |  |  |  |  |  |  |

Recommended cell states:

```text
YES
PARTIAL
NO
UNKNOWN
DIFFERENT_ABSTRACTION
DEPRECATED
```

Every cell should carry:

- source
- retrieval date
- version
- scope
- confidence

---

# 62. Proposed agent-handoff sequence

The earlier After Voice Mode Report suggested a bounded implementation plan.

## Phase A — terminology audit

Formalize:

```text
core
standard_library
harness
adapter
plugin
skill
tool
hook
MCP_client
MCP_server
transport
provider
resource
prompt
agent
runtime
registry
gateway
```

For each term:

1. HUMMBL proposed definition
2. authoritative prior art
3. Google usage
4. Anthropic usage
5. OpenAI usage
6. MCP usage
7. collision risks
8. recommended canonical meaning

Acceptance criterion:

> No two primitives are distinguished only because two vendors happened to name them differently.

---

## Phase B — provider-capability matrix

Build the matrix with explicit citations and temporal metadata.

Do not infer unsupported cells.

---

## Phase C — minimal adapter contract

Define the smallest provider-neutral contract that can support:

- survey providers
- model providers
- document/research providers
- graph stores
- MCP servers

Deliverables:

```text
interfaces
types
capability manifest
error semantics
authentication boundary
provenance requirements
version semantics
```

Do not write all vendor adapters first.

Stabilize the contract first.

---

## Phase D — governance question schema

Create a structured schema for open AI-governance questions.

Seed it from public research agendas.

Every question should distinguish:

```text
explicit_source_question
derived_question
agent_generated_question
survey_nominated_question
```

---

## Phase E — survey experiment

Run the human survey only after a literature baseline exists.

This makes survey responses comparable rather than free-floating.

---

# 63. Recommended repository artifacts

A clean next-stage repository could include:

```text
docs/
├── terminology.md
├── architecture.md
├── field-map.md
├── provenance.md
└── provider-normalization.md

research/
├── sources/
├── open-questions.jsonl
├── claims.jsonl
├── provider-capability-matrix.csv
└── surveys/

schemas/
├── question.schema.json
├── source.schema.json
├── provenance.schema.json
├── capability.schema.json
├── provider.schema.json
└── plugin.schema.json

adrs/
├── 0001-provider-neutral-core.md
├── 0002-capability-vs-transport.md
├── 0003-raw-canonical-derived.md
├── 0004-plugin-skill-mcp-separation.md
└── 0005-temporal-provenance.md
```

---

# 64. Architecture decision records worth creating

## ADR 0001 — Provider-neutral core

Decision:

> The standard library defines semantic contracts and does not directly encode provider identity into canonical types.

## ADR 0002 — Transport is orthogonal to capability

Decision:

> Capabilities are transport-independent; stdio and Streamable HTTP are implementation/exposure choices.

## ADR 0003 — Raw/canonical/derived separation

Decision:

> Source observations are immutable records; canonical normalization and derived inference are separate layers.

## ADR 0004 — Plugin, skill, MCP server, hook remain distinct

Decision:

> Packaging, expertise, protocol exposure, and lifecycle interception are orthogonal.

## ADR 0005 — Temporal provenance

Decision:

> Versioned/renamed provider concepts must be queryable historically.

## ADR 0006 — Humans and agents share action vocabulary but not provenance identity

Decision:

> Similar contribution verbs do not erase source type.

---

# 65. Strongest meta-observation from the Google deep dive

Google’s ecosystem initially looks chaotic because it exposes many brands.

Once normalized, the underlying primitives are surprisingly stable:

```text
MODEL
  ↓
INTERACTION
  ↓
HARNESS
  ↓
CAPABILITY
  ↓
PROTOCOL
  ↓
BOUNDARY
  ↓
RUNTIME
  ↓
OBSERVABILITY
  ↓
EVALUATION
  ↓
GOVERNANCE
```

Surrounding extension mechanisms:

```text
skills
plugins
hooks
tools
resources
agents
identities
registries
gateways
sessions
memory
provenance
```

This strongly supports a provider-neutral field map.

The real research question is not:

> What products does Google have?

It is:

> **Which primitives survive after Google’s product names are stripped away?**

That same operation can then be repeated for Anthropic, OpenAI, Microsoft, AWS, xAI, Cloudflare, and others.

---

# 66. Strongest governance-field-mapping observation

The most promising conceptual shift in this conversation is:

> Treat **open questions** as first-class objects with provenance, relationships, status, and lifecycle.

A conventional literature review produces text.

A field map can produce a dynamic structure where a question can be:

- raised
- decomposed
- merged
- challenged
- answered
- reopened
- deprecated
- ranked
- surveyed
- assigned
- evaluated
- linked to evidence
- linked to policy
- linked to an implementation
- linked to a new research question

This creates a possible bridge between:

```text
literature review
governance research
knowledge graph
survey research
agent evaluation
research operations
```

---

# 67. Potential question lifecycle

A question could have a lifecycle analogous to:

```text
DISCOVERED
    ↓
EXTRACTED
    ↓
NORMALIZED
    ↓
VERIFIED_AS_SOURCE
    ↓
RELATED
    ↓
RANKED
    ↓
INVESTIGATED
    ↓
PARTIALLY_ANSWERED
    ↓
ANSWERED / DISPUTED / SUPERSEDED / REOPENED
```

Additional states might include:

```text
DUPLICATE
OUT_OF_SCOPE
MALFORMED
NON_EMPIRICAL
POLICY_CHOICE
VALUE_CONFLICT
TECHNICAL_RESEARCH
GOVERNANCE_RESEARCH
```

This could prevent very different types of “open questions” from being treated as interchangeable.

---

# 68. Potential question taxonomy

A governance field map may eventually need to distinguish:

```text
descriptive
causal
predictive
normative
institutional
legal
technical
strategic
operational
measurement
evaluation
coordination
security
economic
sociotechnical
epistemic
```

It may also distinguish:

```text
open because unknown
open because disputed
open because unmeasured
open because under-specified
open because value-dependent
open because capability has not yet existed
open because evidence is inaccessible
open because institutions have not decided
```

This is important.

“Open” is not one state.

---

# 69. Signal vs noise opportunities

Although not fully developed in this specific chat, the field-map design naturally supports signal/noise measurements.

Potential signal measures:

- source independence
- expert agreement
- replication
- cross-institution recurrence
- citation density
- evidence quality
- predictive performance
- policy adoption
- implementation evidence

Potential noise indicators:

- duplicate questions
- branding-only distinctions
- outdated terminology
- unsupported claims
- circular citations
- source monoculture
- agent-generated hallucinated questions
- synthetic consensus
- low-information survey responses

This can make the map more than a catalog.

---

# 70. Security and governance implications of provider extensions

As adapters, skills, plugins, MCP servers, and hooks accumulate, the extension system itself becomes a governance surface.

Questions to preserve:

- Who can install a plugin?
- Who can activate a skill?
- Who can register an MCP server?
- Which tools can a server expose?
- What authentication does remote MCP require?
- Which hooks can block execution?
- Can a plugin alter governance hooks?
- Can an agent self-install capabilities?
- Can capabilities escalate authority?
- Is tool discovery itself authorized?
- Can a provider change capabilities without explicit re-approval?
- How are revoked capabilities removed?
- How is audit history retained?

This aligns naturally with the user’s earlier broader skill-lifecycle thinking:

```text
discover
→ verify provenance
→ authorize visibility
→ activate
→ grant tools/resources
→ execute
→ observe
→ evaluate
→ update/version
→ suspend/revoke
→ retain audit history
```

That lifecycle can be applied not only to skills but potentially to:

- plugins
- adapters
- MCP servers
- provider integrations
- agent identities
- field-map sources

---

# 71. A possible unifying extension lifecycle

A generalized extension lifecycle might be:

```text
DISCOVER
    ↓
IDENTIFY
    ↓
VERIFY PROVENANCE
    ↓
INSPECT MANIFEST
    ↓
RESOLVE CAPABILITIES
    ↓
ASSESS RISK
    ↓
AUTHORIZE
    ↓
ACTIVATE
    ↓
BIND PERMISSIONS
    ↓
EXECUTE
    ↓
OBSERVE
    ↓
EVALUATE
    ↓
VERSION / UPDATE
    ↓
SUSPEND / REVOKE
    ↓
RETAIN AUDIT HISTORY
```

This may eventually unify governance of:

- skills
- plugins
- adapters
- MCP servers
- remote services

without claiming they are the same object.

---

# 72. Research discipline for future passes

Future agents should be instructed to:

1. prefer official vendor documentation
2. record publication/retrieval dates
3. distinguish current from historical names
4. preserve deprecated names as aliases
5. avoid converting product names into ontology primitives too quickly
6. avoid inferring feature parity from similar branding
7. separately record:
   - specification support
   - product support
   - SDK support
   - preview/GA status
8. mark inferred architecture as inference
9. cite every provider-capability claim
10. actively look for counterexamples

---

# 73. Open questions created by this conversation

The conversation itself generated new questions.

## Field mapping

- What is the minimal canonical schema for an open question?
- When are two questions duplicates?
- Can a question be “answered” globally, or only relative to evidence/version/jurisdiction?
- How should normative questions differ from empirical questions?
- Can question importance be measured over time?
- How should source authority be represented without hard-coding institutional prestige?
- How should disagreement be represented?

## Surveys

- Which survey providers are worth supporting first?
- Should HUMMBL define a survey interface or a more general “human input” interface?
- How should anonymous responses be represented?
- How should identity, consent, and privacy be handled?
- How should survey-derived rankings be compared with literature-derived salience?

## Extensions

- Is “plugin” useful as a canonical primitive or only as a package type?
- Is “skill” sufficiently stable across providers to standardize?
- What is the minimal capability manifest?
- Should hooks be a core primitive?
- How should extension provenance be signed or attested?
- How should capability revocation propagate?

## MCP

- How should HUMMBL represent MCP protocol revisions?
- How should transport capability negotiation be represented?
- What security boundary distinguishes local stdio from local HTTP?
- What provider-specific MCP limitations must adapters expose?
- Should the same semantic server identity survive transport migration?

## Google

- Which Google products are truly distinct implementations versus renamed surfaces?
- Which pieces are stable platform primitives versus temporary product packaging?
- How should Agent Platform and Gemini API managed agents be normalized?
- What is the exact boundary between ADK, Antigravity SDK, and managed harnesses?
- Which Google concepts are likely to become cross-vendor standards?

---

# 74. Immediate next research moves

A sensible continuation is:

## Step 1
Freeze this document as the conversation-preservation artifact.

## Step 2
Create a machine-readable terminology table.

Suggested columns:

```text
term
canonical_definition
category
google_term
anthropic_term
openai_term
mcp_term
status
source
valid_from
valid_to
notes
```

## Step 3
Build the provider capability matrix.

Start with:

```text
Google
Anthropic
OpenAI
```

Only then add:

```text
Microsoft
AWS
xAI
Cloudflare
```

## Step 4
Build the first governance-question corpus.

Seed from:

- Google DeepMind global governance paper
- Dafoe / GovAI research agenda
- selected frontier-governance research agendas
- standards with explicit unresolved issues
- lab governance roadmaps

## Step 5
Create the first survey.

Use literature-derived questions as the baseline.

## Step 6
Run agents against the same question set.

Measure disagreement.

---

# 75. Suggested machine-readable artifacts

The conversation can be decomposed into:

```text
chat-archive.md
terminology.jsonl
provider-map.jsonl
questions.jsonl
sources.jsonl
claims.jsonl
relationships.jsonl
capabilities.jsonl
```

Potential IDs:

```text
src_
q_
claim_
cap_
provider_
impl_
plugin_
skill_
mcp_
rel_
eval_
```

No ID scheme has been finalized.

---

# 76. Research source ledger

The following sources were used to verify and harden the conversation.

## HUMMBL

1. HUMMBL — Control and proof for agentic AI  
   https://hummbl.io/

2. HUMMBL Research  
   https://hummbl.io/research

3. HUMMBL Method  
   https://hummbl.io/method

4. HUMMBL Delegation Tokens  
   https://hummbl.io/primitives/delegation-tokens

5. HUMMBL Playground / Base120  
   https://hummbl.io/playground

---

## AI governance / open questions

6. Google DeepMind — Exploring institutions for global AI governance  
   https://deepmind.google/blog/exploring-institutions-for-global-ai-governance/

7. Allan Dafoe — AI Governance: A Research Agenda  
   https://cdn.governance.ai/GovAI-Research-Agenda.pdf

8. GovAI Annual Report 2018 description of the research agenda  
   https://www.governance.ai/post/govai-annual-report-2018

9. Google DeepMind — Securing the future of AI agents  
   https://deepmind.google/blog/securing-the-future-of-ai-agents/

10. Google DeepMind — Conjecture Machines / validation bottleneck  
    https://deepmind.google/public-policy/conjecture-machines-ai-agents-and-the-new-validation-bottleneck-in-science/

11. Google DeepMind — From AGI to ASI  
    https://deepmind.google/research/publications/239142/

---

## MCP

12. MCP 2025 Streamable HTTP / stdio transports  
    https://modelcontextprotocol.io/specification/2025-06-18/basic/transports

13. MCP 2026-07-28 specification release notes  
    https://blog.modelcontextprotocol.io/posts/2026-07-28/

14. MCP roadmap, post-2026-07-28 transport direction  
    https://blog.modelcontextprotocol.io/posts/mcp-roadmap/

---

## Google AI / agents

15. Google AI Studio Build mode  
    https://ai.google.dev/gemini-api/docs/aistudio-build-mode

16. Gemini API  
    https://ai.google.dev/gemini-api/docs

17. Gemini Interactions API overview  
    https://ai.google.dev/gemini-api/docs/interactions-overview

18. Migration to Interactions API  
    https://ai.google.dev/gemini-api/docs/migrate-to-interactions

19. Background execution  
    https://ai.google.dev/gemini-api/docs/background-execution

20. Gemini remote MCP / function calling  
    https://ai.google.dev/gemini-api/docs/function-calling

21. Managed Agents overview  
    https://ai.google.dev/gemini-api/docs/agents

22. Antigravity managed agent  
    https://ai.google.dev/gemini-api/docs/antigravity-agent

23. Building managed agents  
    https://ai.google.dev/gemini-api/docs/custom-agents

24. Google Antigravity announcement  
    https://developers.googleblog.com/build-with-google-antigravity-our-new-agentic-development-platform/

25. Antigravity 2.0  
    https://www.antigravity.google/product/antigravity-2

26. Gemini CLI → Antigravity CLI transition  
    https://developers.googleblog.com/an-important-update-transitioning-gemini-cli-to-antigravity-cli/

27. Antigravity plugins  
    https://antigravity.google/docs/plugins/

28. Antigravity CLI plugins / skills / hooks  
    https://antigravity.google/docs/cli/plugins

29. Conductor → Antigravity plugin  
    https://developers.googleblog.com/evolving-spec-driven-development-conductor-now-supports-antigravity/

30. Agent Plugins 1.0.0  
    https://developers.googleblog.com/agent-plugins-package-your-skills-tools-and-more/

31. Agents CLI templates  
    https://google.github.io/agents-cli/guide/templates/

32. Agents CLI quickstart tutorial  
    https://google.github.io/agents-cli/guide/quickstart-tutorial/

33. Agents CLI development guide  
    https://google.github.io/agents-cli/guide/development/

34. Agents CLI skills  
    https://google.github.io/agents-cli/reference/skills/

35. Agents CLI command reference  
    https://google.github.io/agents-cli/cli/

36. Gemini Enterprise Agent Platform introduction  
    https://cloud.google.com/blog/products/ai-machine-learning/introducing-gemini-enterprise-agent-platform

37. Gemini Enterprise Agent Platform latest overview  
    https://cloud.google.com/blog/products/ai-machine-learning/whats-new-in-gemini-enterprise-agent-platform

38. Gemini Enterprise Agent Platform release notes  
    https://docs.cloud.google.com/gemini-enterprise-agent-platform/release-notes

39. Gemini Enterprise Agent Platform remote MCP server  
    https://cloud.google.com/blog/products/ai-machine-learning/gemini-enterprise-agent-platform-remote-mcp-server/

40. Google Developer’s Guide to AI Agent Protocols  
    https://developers.googleblog.com/developers-guide-to-ai-agent-protocols/

41. Firebase Studio sunset and migration  
    https://firebase.google.com/docs/studio/migrating-project

42. Jules homepage  
    https://jules.google/

43. Jules FAQ  
    https://jules.google/docs/faq/

44. Jules MCP support  
    https://jules.google/docs/changelog/2026-02-02/

---

## Google Forms

45. Google Forms branching  
    https://support.google.com/docs/answer/141062

46. Google Forms → Google Sheets responses  
    https://support.google.com/docs/answer/2917686

47. Google Forms general documentation  
    https://support.google.com/docs/answer/6281888

48. Google Forms sharing updates  
    https://support.google.com/docs/answer/16319311

---

# 77. Claims that should remain explicitly provisional

The following should not be silently promoted to settled facts without a separate research pass:

1. **The final HUMMBL ontology.**  
   This chat generated candidates, not a final ontology.

2. **The exact meaning/name of “Rum’s field mapping.”**  
   The phrase was spoken but not formally defined.

3. **The precise boundary between ADK and Genkit.**  
   “Agent-first” vs “application-first” is a useful working distinction, not an official universal law.

4. **Whether every provider’s “skill” is semantically equivalent.**  
   There is strong convergence, but semantics and lifecycle still differ.

5. **Whether “plugin” deserves a canonical cross-provider primitive.**  
   It may be better modeled as packaging metadata.

6. **Whether local/remote MCP should be exposed as user-facing categories.**  
   They are useful operational categories but are not the same as transport identity.

7. **Any novelty claim about the user’s field-mapping approach.**  
   The architecture is distinctive, but novelty requires a formal prior-art search.

---

# 78. One-sentence handoff

If another agent receives only one sentence from this archive, use:

> **Build a provider-neutral, provenance-first field map in which open AI-governance questions are first-class versioned objects; keep core semantics separate from vendor adapters, keep skills/plugins/hooks/MCP/transport distinct, and use Google’s sprawling agent stack as the first adversarial normalization test.**

---

# 79. Compact architectural invariants

Preserve these unless evidence defeats them:

1. **Core semantics must not depend on provider names.**
2. **Transport must not define capability identity.**
3. **A server is not defined by being remote.**
4. **Raw source data must remain recoverable.**
5. **Derived knowledge must identify its derivation.**
6. **Human and agent contributions may share verbs but not provenance identity.**
7. **Plugin, skill, hook, tool, adapter, and MCP server are distinct dimensions.**
8. **Provider capability should be discovered/declared, not guessed from brand.**
9. **Historical names must remain queryable after renames.**
10. **Every research question should have a source/status/lifecycle.**
11. **Every vendor claim should have a time-bounded source.**
12. **The standard-library core should survive loss of every external provider.**

---

# 80. Final synthesis

The conversation began with HUMMBL’s public OSS governance surface and ended with a general architecture for mapping both AI governance and the agent ecosystem itself.

Two field maps are beginning to converge:

## Map A — governance knowledge

```text
sources
→ questions
→ claims
→ evidence
→ responses
→ evaluations
→ status
```

## Map B — agent infrastructure

```text
providers
→ capabilities
→ implementations
→ skills
→ tools
→ plugins
→ protocols
→ transports
→ runtimes
→ governance
```

The same architecture principles apply to both:

- stable canonical objects
- adapters at boundaries
- explicit provenance
- version history
- relation graphs
- capability discovery
- raw/canonical/derived separation
- lifecycle governance
- cross-provider normalization

The deeper opportunity is that these may not need to remain separate systems.

A governance question can eventually point directly to:

- the provider capability it concerns
- the protocol boundary involved
- the implementation being evaluated
- the test evidence
- the policy
- the runtime control
- the survey signal
- the unresolved research question

That produces a living map connecting:

```text
QUESTION
  ↕
EVIDENCE
  ↕
SYSTEM
  ↕
CONTROL
  ↕
OUTCOME
```

If implemented carefully, HUMMBL’s field mapping could become a structured way to ask not merely:

> “What do we know?”

but:

> **“What remains unresolved, who says so, what evidence bears on it, what systems instantiate the problem, what controls exist, and how has the answer changed over time?”**

That is the central research direction preserved from this conversation.

---

**End of preservation record.**
