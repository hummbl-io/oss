# HUMMBL positions on AI progress, openness, and frontier financing

**Version:** candidate 1.0. **Evidence cutoff:** 2026-09-12.
**State:** proposed canonical baseline for company review. Publication of a
proposal does not establish company adoption or independent certification.

HUMMBL's proposed position is to judge AI by the work it can reliably complete, the
authority it is allowed to exercise, and the evidence left behind. We support
measured improvement and meaningful user control. We do not require an AGI
arrival date, a preferred financing structure, or a universal model winner to
build useful governance infrastructure.

This is a position paper, not a benchmark result. Statements marked **Position**
are HUMMBL policy proposals; the linked evidence supports their factual premises,
not their adoption or universal correctness. The [claim ledger](claims.json)
separates facts, attributed reports, forecasts, judgments, and untested business
hypotheses. [Public source notes](SOURCES.md) and the [source index](sources.json) carry
access dates, observations and limitations.

## POS-01 — Recognize bounded self-improvement; specify the boundary

**Position:** We recognize evidence that AI systems can improve agent software
and selected parts of AI research workflows. We reserve stronger claims about
autonomous successor development or sustained accelerating general improvement
for evidence that actually measures those things.

The [Darwin Gödel Machine paper](https://arxiv.org/abs/2505.22954v3) reports
improvement through agent-code modification. Its foundation models and outer
selection machinery remain fixed. [AlphaEvolve](https://deepmind.google/blog/alphaevolve-impact/)
reports useful algorithm and infrastructure optimization. Neither result alone
establishes unrestricted recursive acceleration. Anthropic's
[RSI account accessed on 2026-09-12](https://www.anthropic.com/institute/recursive-self-improvement)
also separates present R&D acceleration from fully autonomous successor development.

For HUMMBL, distinguish: human-directed workflow improvement; agent
self-modification under an external evaluator; successor-model development;
and improvement to the process of improvement across generations. These are
working evidence categories, not a universal intelligence taxonomy. A claim
must name which category it addresses. A revised evidence workflow does not by
itself demonstrate a performance benefit, improve an underlying model’s weights,
or prove general RSI.

**Revision trigger:** credible multi-generation results with lineage, fixed
evaluation conditions, full resource accounting, and independent replication.

## POS-02 — Evaluate AGI claims with an explicit definition

**Position:** AGI assertions must state the definition, domains, human comparison
group, reliability, autonomy, resources, and evaluation date. HUMMBL will not
infer general intelligence from a coding score, a product name, an economic
forecast, or an agent's description of itself.

[Levels of AGI](https://arxiv.org/abs/2311.02462v5) separates performance,
generality and autonomy. Google's
[cognitive measurement framework](https://blog.google/innovation-and-ai/models-and-research/google-deepmind/measuring-agi-cognitive-framework/)
calls for broader abilities and human baselines. These are useful proposals,
not a universally binding definition or proof that a particular system passed.
The reviewed evidence does not warrant HUMMBL certifying a system as AGI;
that is a bounded assessment, not proof that AGI is impossible or absent everywhere.

**Revision trigger:** a specified system is independently evaluated against a
declared broad standard with representative baselines and material gaps disclosed.

## POS-03 — Treat ASI dates as forecasts, not observations

**Position:** ASI denotes a stronger claim than narrow superhuman performance.
HUMMBL will label ASI predictions as attributed scenarios, preserve their
assumptions, and avoid selling services on a promised arrival date.

Sam Altman's [The Gentle Singularity](https://blog.samaltman.com/the-gentle-singularity)
is an influential superintelligence forecast. Dario Amodei's
[Machines of Loving Grace](https://darioamodei.com/essay/machines-of-loving-grace)
uses a defined “powerful AI” scenario; that term is not silently relabeled as
ASI here. Neither is a reproducible demonstration of broad superintelligence.
Expert outperformance in one task does not establish broad superintelligence,
and cognitive capability does not remove physical or institutional constraints.

**Revision trigger:** independently reproduced broad capabilities or new evidence
that changes an explicitly stated scenario assumption. Do not silently move a forecast's date.

## POS-04 — Classify openness at the artifact and license level

**Position:** Open source software, open weights, available training artifacts,
and reproducible training are distinct claims. State the model/version, license,
available artifacts, and definition used. We favor inspectability, portability,
and meaningful rights, while representing restrictions accurately.

The [Open Source AI Definition 1.0](https://opensource.org/ai/open-source-ai-definition)
requires more than downloadable weights. Its data-information requirement is
not a requirement to release every original training example. Meta's
[Llama 4 license](https://github.com/meta-llama/llama-models/blob/5fdf83110cc9daa7435dfba6eb304892cc0041b8/models/llama4/LICENSE)
has material conditions; OpenAI's [gpt-oss](https://openai.com/index/introducing-gpt-oss/)
uses Apache 2.0 for released weights. Ai2's [Olmo 3](https://allenai.org/blog/olmo3)
provides broader lifecycle artifacts. No full OSAID conformance or training-reproduction
audit is asserted by this paper.

**Revision trigger:** model/license changes or a new artifact-level conformance review.

## POS-05 — Reject a universal open-versus-frontier winner

**Position:** Choose systems by accepted task quality, full cost, latency,
privacy constraints, operational control, and exit options. Open weights and
frontier-lab origin are overlapping categories; gpt-oss is a direct counterexample
to treating them as opposites.

Self-hosting can permit pinning and local control but creates operating duties.
Hosted APIs can reduce some infrastructure work but retain provider and service
dependencies. Neither distribution regime guarantees safety, cheap operation,
reproducibility, or task superiority. Record evidence for the actual deployment.

**Revision trigger:** a workload, version, price, license, or control requirement changes.

## POS-06 — Separate capital-market events from capability evidence

**Position:** IPO announcements are financing evidence. They do not establish
AGI, ASI, profitability, deception, or the correctness of a lab's policy arguments.
We examine incentives as hypotheses and evaluate public claims on their evidence.

| Entity | Strongest event established in the reviewed receipts | What it does not establish |
| --- | --- | --- |
| Anthropic | [Announced confidential draft S-1 submission on 2026-06-01](https://www.anthropic.com/news/confidential-draft-s1-sec) | Completed IPO, public prospectus, price, or observed confidential draft |
| OpenAI | [Announced on 2026-06-08 that it had recently submitted a confidential S-1](https://openai.com/index/openai-submits-confidential-s-1/) | Exact submission day, final timing, public registration, or listing |
| Alphabet, Microsoft, Meta | Public parent-company investor/SEC records (CV-10–CV-12) | A separate IPO or standalone profits for each AI lab/division |
| xAI / SpaceX | [xAI acquisition announcement](https://x.ai/news/xai-joins-spacex) and [Nasdaq SpaceX listing event](https://www.nasdaq.com/events/spacex-rings-closing-bell) | A standalone xAI IPO or AI-segment profitability |

These are dated observed milestones, not an exhaustive finding about each
issuer's latest legal status. The confidential documents were not inspected.
The [SEC FAQ](https://www.sec.gov/about/divisions-offices/division-corporation-finance/voluntary-submission-draft-registration-statements-faqs)
distinguishes nonpublic draft submission from a filed registration statement.
Refresh issuer-specific public records immediately before reusing current-status wording.

**Revision trigger:** identifiable new issuer, SEC, or exchange evidence. A target date passing is insufficient.

## POS-07 — Evaluate policy proposals without inventing motives

**Position:** HUMMBL supports evidence-based scrutiny of both deployment and
release risks. We oppose treating company identity or licensing category as a
substitute for a threat model. Criticism must quote the proposal accurately and
separate measured effects from inferred incentives.

Anthropic's [July 2026 statement](https://www.anthropic.com/news/position-open-weights-models)
rejects a blanket open-weights ban while advocating other controls. That proves
what the company said, not every historical action or motive. Claims that open
release necessarily improves defense, or necessarily makes every deployment
less safe, require threat-specific evidence. Downloaded weights and revocable
API access have different control properties; neither removes operator responsibility.

**Revision trigger:** policy text, release conditions, or credible risk evidence changes.

## POS-08 — Receipts establish bounded provenance, not truth by themselves

**Position:** A receipt's assurance cannot exceed its identity, integrity,
observation, and trust assumptions. A file hash checks bytes. A shared-key MAC
authenticates within its shared-secret domain. Neither proves that a claim is
true, a test is adequate, an action was authorized, or every execution path was mediated.

The current [HUMMBL public explanation](https://hummbl.io/) distinguishes its
browser walkthrough from native enforcement and independent identity. Preserve
that boundary in AI capability and improvement claims. The services page still
uses broader proof wording in one process item; the
[surface correction map](SURFACES.md#services-process-wording)
proposes a consistent replacement. A successful validator for this package
proves structural checks only; source interpretation still requires review.

**Revision trigger:** trust model, key handling, observation path, or verification scope changes.

## POS-09 — Measure accepted value, including review and rework

**Position:** HUMMBL's improvement target is useful, accepted work per unit of
total cost. More code, tokens, agents, experiments, or passed tests are possible
inputs or proxies, not proof of customer value or profit.

METR's [early-2025 study](https://metr.org/blog/2025-07-10-early-2025-ai-experienced-os-dev-study/)
and [2026 update](https://metr.org/blog/2026-02-24-uplift-update/) show why
workflow, date, selection, measurement, and uncertainty matter. Preserve the
update alongside the original; neither supports a timeless universal productivity claim.
Our [commercial experiment](COMMERCIAL.md) measures review effort and delivery
cost alongside task acceptance. Its thresholds are proposed decisions, not observed results.

**Revision trigger:** measured paid-pilot outcomes or evidence that a proxy stopped tracking value.

## POS-10 — Govern improvement itself

**Position:** An improvement process needs a fixed comparison baseline within each evaluation,
versioned changes, external checks appropriate to the claim, cost accounting,
rollback or containment, and a stop rule. The proposing system must not silently
weaken the evaluator and count the easier test as progress. Evaluators may be
revised, but the revision needs a new version and bridge comparisons where
feasible; scores from different evaluation regimes are not directly interchangeable.

We apply LLL as an internal method: evidence-bound passage, typed relationships,
and recorded feedback. Base120 structures the inquiry. Neither method supplies
missing empirical evidence or proves its own superiority. The
[review method](METHOD.md) explains the reasoning structure and its limits.

**Revision trigger:** evaluator drift, regressions, exhausted budget, missing lineage,
or a new claim whose consequences exceed the existing control boundary.

## Use and review

Current headlines provide concrete applications. OpenAI's
[September Astra release](https://openai.com/index/gpt-6-astra/) distinguishes
benchmark versions and research configurations from production. Anthropic's
[September Fable/Mythos release](https://www.anthropic.com/claude-fable-and-mythos-5-1)
distinguishes safeguards/access despite shared underlying capability. Compare
the exact delivered configuration; neither a benchmark name containing “AGI”
nor zero failures in one test establishes general intelligence or zero deployment risk.

The [July open-weights industry letter](https://images.nvidia.com/pdf/Open-Weights-and-American-AI-Leadership.pdf)
argues for competition and defensive inspection while acknowledging release
risks. Together with Anthropic's response, it is a policy disagreement to evaluate,
not evidence of two mutually exclusive kinds of company. Receipts R-01–R-03
preserve the dates and limits of this current-source sweep.

Use the numbered positions as the common source for future public copy after
adoption. Preserve claim IDs, evidence dates and limitations. The
[surface inventory](SURFACES.md) distinguishes observed public copy from
inaccessible surfaces and the limits of public-page discovery; it does not claim
a census of all discourse.
[Review instructions](REVIEW.md) separate local consistency checks from source
interpretation and company adoption.

Before public adoption, review the factual clauses against the receipts and
confirm that the proposed value judgments express HUMMBL's intended position.
The PR is the reviewable delivery artifact. Research review, company adoption,
public deployment and measured business impact remain distinct states.
