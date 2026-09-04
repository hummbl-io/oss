# Copyright 2024-2026 HUMMBL, LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# SPDX-License-Identifier: Apache-2.0

"""Per-lab scorecard data for the HUMMBL evaluation framework.

This module contains rubric-based scores for all 28 frontier AI labs
identified in the Frontier Benchmarks AI compendium (August 2026).
Scores are extracted from six HUMMBL research artifacts:

1. ``frontier-ai-labs-full28-2026-08-31.md`` — full 28-lab compendium
2. ``frontier-labs-deep-profiles-2026-08-31.md`` — top-10 deep profiles
3. ``ai-safety-frameworks-comparison-2026-08-31.md`` — safety framework maturity
4. ``eu-ai-act-gpai-enforcement-2026-08-31.md`` — EU compliance posture
5. ``nist-cosais-deep-research-2026-08-31.md`` — runtime governance controls
6. ``hummbl-account-potential-scoring-2026-08-31.md`` — account-potential synthesis

Each lab is scored on 6 dimensions with criteria scored 0-5 (or ``None``
for N/A, used exclusively in the conditional Open-Weight Governance
dimension for closed-weight labs).

Scoring rubrics
---------------

**Dimension 1 — Governance Maturity** (from safety frameworks research)

- ``safety_framework_published``: 0=none, 1=draft only, 2=published but vague,
  3=published with thresholds, 4=published with thresholds + pause,
  5=published with thresholds + pause + external review
- ``framework_bindingness``: 0=none, 1=voluntary/aspirational,
  2=self-administered, 3=board-reviewed, 4=externally-audited,
  5=regulator-enforced
- ``pause_commitment``: 0=none, 1=mentioned but no mechanism, 2=mechanism
  defined, 3=mechanism + thresholds, 4=mechanism + thresholds + used,
  5=mechanism + thresholds + used + external verification
- ``external_review``: 0=none, 1=ad-hoc, 2=periodic internal, 3=periodic
  external, 4=continuous external, 5=continuous external + public reporting
- ``academic_eval_score``: 0=not evaluated, 1=<10%, 2=10-20%, 3=20-30%,
  4=30-40%, 5=>40% (from arXiv:2512.01166)

**Dimension 2 — Runtime Governance** (from NIST COSAiS + deep profiles)

- ``kill_switch``: 0=none, 1=manual only, 2=manual + automated,
  3=graduated response, 4=graduated + auditable,
  5=graduated + auditable + external
- ``circuit_breaker``: 0=none, 1=basic, 2=threshold-based, 3=state machine,
  4=state machine + recovery, 5=state machine + recovery + audit
- ``cost_governance``: 0=none, 1=basic limits, 2=budget tracking,
  3=soft/hard caps, 4=caps + alerts, 5=caps + alerts + deny
- ``audit_logging``: 0=none, 1=basic logs, 2=structured logs, 3=append-only,
  4=append-only + signed, 5=append-only + signed + verified
- ``output_validation``: 0=none, 1=basic filtering, 2=rule-based,
  3=rule-based + ML, 4=multi-layer, 5=multi-layer + adversarial
- ``capability_fencing``: 0=none, 1=basic sandbox, 2=permission-based,
  3=capability-based, 4=capability + dynamic,
  5=capability + dynamic + verified

**Dimension 3 — Compliance Posture** (from EU AI Act research)

- ``eu_ai_act_gpai``: 0=non-compliant, 1=aware, 2=partial,
  3=Code of Practice signatory, 4=full baseline compliance,
  5=full + systemic risk compliance
- ``nist_ai_rmf``: 0=none, 1=aware, 2=partial, 3=mapped,
  4=mapped + measured, 5=mapped + measured + managed
- ``iso_42001``: 0=none, 1=aware, 2=planning, 3=implementing, 4=certified,
  5=certified + continuous
- ``soc2``: 0=none, 1=aware, 2=planning, 3=Type I, 4=Type II,
  5=Type II + continuous
- ``code_of_practice_signatory``: 0=not signed, 1=observer, 2=signed,
  3=signed + reporting, 4=signed + reporting + audited,
  5=signed + reporting + audited + verified

**Dimension 4 — Agent Governance** (from deep profiles)

- ``multi_agent_coordination``: 0=none, 1=single agent, 2=sequential,
  3=parallel, 4=parallel + coordinated, 5=parallel + coordinated + governed
- ``agent_identity``: 0=none, 1=basic ID, 2=ID + auth, 3=ID + auth + roles,
  4=ID + auth + roles + delegation,
  5=ID + auth + roles + delegation + verified
- ``delegation_support``: 0=none, 1=manual, 2=token-based, 3=signed tokens,
  4=signed + scoped, 5=signed + scoped + revocable
- ``tool_use_governance``: 0=none, 1=basic, 2=permission-based,
  3=permission + audit, 4=permission + audit + limits,
  5=permission + audit + limits + verified
- ``convergence_guarantees``: 0=none, 1=basic, 2=timeout-based,
  3=quorum-based, 4=quorum + verification, 5=quorum + verification + proof

**Dimension 5 — Transparency** (from deep profiles + safety frameworks)

- ``model_card``: 0=none, 1=basic, 2=detailed, 3=detailed + evals,
  4=detailed + evals + limitations,
  5=detailed + evals + limitations + updates
- ``system_card``: 0=none, 1=basic, 2=detailed, 3=detailed + safety,
  4=detailed + safety + risks, 5=detailed + safety + risks + mitigations
- ``training_data_disclosure``: 0=none, 1=summary, 2=summary + sources,
  3=summary + sources + sizes, 4=summary + sources + sizes + processing,
  5=full disclosure
- ``evaluation_disclosure``: 0=none, 1=internal, 2=internal + summary,
  3=external evals, 4=external + public, 5=external + public + reproducible
- ``incident_reporting``: 0=none, 1=ad-hoc, 2=internal process,
  3=internal + external, 4=internal + external + public,
  5=internal + external + public + timely

**Dimension 6 — Open-Weight Governance** (conditional; ``None`` if not open-weight)

- ``license_clarity``: 0=none, 1=ambiguous, 2=standard OSI,
  3=standard + commercial terms, 4=standard + commercial + governance,
  5=standard + commercial + governance + revocation
- ``deployment_tools``: 0=none, 1=basic, 2=API + docs,
  3=API + docs + governance, 4=API + docs + governance + monitoring,
  5=full deployment toolkit
- ``red_teaming``: 0=none, 1=internal, 2=internal + published, 3=external,
  4=external + published, 5=external + published + reproducible
- ``community_governance``: 0=none, 1=basic, 2=contribution process,
  3=contribution + review, 4=contribution + review + safety,
  5=full community governance

Where data is not available from the research artifacts, a score of ``0``
is used with an inline ``# unverified`` comment.

Standard library only.
"""

from __future__ import annotations

from typing import Dict, Optional

# ---------------------------------------------------------------------------
# Type aliases
# ---------------------------------------------------------------------------

#: A single criterion score (0-5) or None for N/A.
Score = Optional[int]

#: A dimension is a mapping of criterion name to Score.
DimensionScores = Dict[str, Score]

#: A lab scorecard is a mapping of dimension name to DimensionScores.
LabScorecard = Dict[str, DimensionScores]

#: The full scorecard database.
ScorecardDB = Dict[str, LabScorecard]


# ---------------------------------------------------------------------------
# LAB_SCORECARDS — per-lab rubric scores for all 28 frontier labs
# ---------------------------------------------------------------------------

LAB_SCORECARDS: ScorecardDB = {

    # ======================================================================
    # Tier 1 — Undisputed Frontier (Labs 1-6, US)
    # ======================================================================

    "anthropic": {
        "governance_maturity": {
            "safety_framework_published": 3,  # published with thresholds; pause rescinded in v3.0
            "framework_bindingness": 2,      # self-administered (PBC structure)
            "pause_commitment": 3,           # mechanism + thresholds (ASL system); binding halt rescinded
            "external_review": 4,            # continuous external (UK/US AISI, GovAI, METR, MATS)
            "academic_eval_score": 4,        # 34% (arXiv:2512.01166)
        },
        "runtime_governance": {
            "kill_switch": 2,               # manual + automated (June 2026 export-control disable)
            "circuit_breaker": 1,            # basic (ASL system acts as basic breaker)  # unverified
            "cost_governance": 0,            # none  # unverified
            "audit_logging": 2,              # structured logs (ZDR monitoring, usage tracking)  # unverified
            "output_validation": 3,          # rule-based + ML (Constitutional Classifiers)
            "capability_fencing": 2,         # permission-based (ASL-3 access controls for trusted users)  # unverified
        },
        "compliance_posture": {
            "eu_ai_act_gpai": 4,             # full baseline compliance (signed CoP in full, Frontier Compliance Framework)
            "nist_ai_rmf": 3,                # mapped (SB 53 compliance framework)  # partially verified
            "iso_42001": 1,                  # aware  # unverified
            "soc2": 4,                       # Type II (enterprise-grade)  # unverified
            "code_of_practice_signatory": 3, # signed + reporting (full signatory, risk reports)
        },
        "agent_governance": {
            "multi_agent_coordination": 2,   # sequential (Claude Code, Cowork)  # partially verified
            "agent_identity": 1,             # basic ID (API keys, org IDs)  # unverified
            "delegation_support": 1,         # manual (API-based)  # unverified
            "tool_use_governance": 2,        # permission-based (Claude Code tool use)  # unverified
            "convergence_guarantees": 1,     # basic  # unverified
        },
        "transparency": {
            "model_card": 4,                 # detailed + evals + limitations
            "system_card": 4,                # detailed + safety + risks
            "training_data_disclosure": 2,   # summary + sources  # partially verified
            "evaluation_disclosure": 4,      # external + public (UK/US AISI evals, risk reports)
            "incident_reporting": 3,         # internal + external (AISI incident, export-control incident)
        },
        "open_weight_governance": {
            "license_clarity": None,         # closed weights
            "deployment_tools": None,
            "red_teaming": None,
            "community_governance": None,
        },
    },

    "google-deepmind": {
        "governance_maturity": {
            "safety_framework_published": 3, # published with thresholds (CCLs, TCLs); no pause
            "framework_bindingness": 2,      # self-administered (voluntary)
            "pause_commitment": 1,           # mentioned but no mechanism (safety case reviews, no binding stop)
            "external_review": 2,            # periodic internal (external experts "as needed")
            "academic_eval_score": 3,        # 20% (arXiv:2512.01166)
        },
        "runtime_governance": {
            "kill_switch": 1,               # manual only  # unverified
            "circuit_breaker": 1,            # basic (CCL system)  # unverified
            "cost_governance": 0,            # none  # unverified
            "audit_logging": 2,              # structured logs  # unverified
            "output_validation": 2,          # rule-based (safety filters)  # unverified
            "capability_fencing": 1,         # basic sandbox  # unverified
        },
        "compliance_posture": {
            "eu_ai_act_gpai": 4,             # full baseline compliance (signed CoP in full)
            "nist_ai_rmf": 3,                # mapped  # partially verified
            "iso_42001": 1,                  # aware  # unverified
            "soc2": 4,                       # Type II (Google Cloud enterprise)  # unverified
            "code_of_practice_signatory": 3, # signed + reporting
        },
        "agent_governance": {
            "multi_agent_coordination": 3,   # parallel (Gemini Spark, Enterprise Agent Platform)  # partially verified
            "agent_identity": 2,             # ID + auth (Google Cloud IAM)  # unverified
            "delegation_support": 2,         # token-based (OAuth)  # unverified
            "tool_use_governance": 2,        # permission-based (Vertex AI)  # unverified
            "convergence_guarantees": 1,     # basic  # unverified
        },
        "transparency": {
            "model_card": 3,                 # detailed + evals (model cards for each Gemini release)
            "system_card": 3,                # detailed + safety (safety case reviews)
            "training_data_disclosure": 2,   # summary  # partially verified
            "evaluation_disclosure": 2,      # internal + summary
            "incident_reporting": 2,         # internal process  # unverified
        },
        "open_weight_governance": {
            "license_clarity": 2,            # standard OSI (Gemma permissive license)  # partially verified
            "deployment_tools": 2,           # API + docs (Vertex AI, HuggingFace)  # partially verified
            "red_teaming": 1,                # internal  # unverified
            "community_governance": 2,       # contribution process  # unverified
        },
    },

    "openai": {
        "governance_maturity": {
            "safety_framework_published": 3, # published with thresholds (High, Critical); no pause
            "framework_bindingness": 2,      # self-administered (SAG internal, Board committee)
            "pause_commitment": 1,           # mentioned but no mechanism ("sufficiently minimize", no halt)
            "external_review": 2,            # periodic internal (SAG + Board committee; external red teaming ad-hoc)
            "academic_eval_score": 4,        # 33% (arXiv:2512.01166)
        },
        "runtime_governance": {
            "kill_switch": 2,               # manual + automated (Astra pause, safety eval halt)
            "circuit_breaker": 1,            # basic  # unverified
            "cost_governance": 0,            # none  # unverified
            "audit_logging": 2,              # structured logs  # unverified
            "output_validation": 3,          # rule-based + ML (activation classifiers, cyber safeguards)
            "capability_fencing": 2,         # permission-based (API access controls)  # unverified
        },
        "compliance_posture": {
            "eu_ai_act_gpai": 3,             # Code of Practice signatory (with reservations)
            "nist_ai_rmf": 3,                # mapped (Frontier Governance Framework)  # partially verified
            "iso_42001": 1,                  # aware  # unverified
            "soc2": 4,                       # Type II (enterprise-grade)  # unverified
            "code_of_practice_signatory": 2, # signed (with reservations on certain chapters)
        },
        "agent_governance": {
            "multi_agent_coordination": 3,   # parallel (ultra mode coordinates parallel agents)  # partially verified
            "agent_identity": 1,             # basic ID  # unverified
            "delegation_support": 1,         # manual  # unverified
            "tool_use_governance": 2,        # permission-based (Codex tool use)  # unverified
            "convergence_guarantees": 1,     # basic  # unverified
        },
        "transparency": {
            "model_card": 4,                 # detailed + evals + limitations (system cards)
            "system_card": 4,                # detailed + safety + risks
            "training_data_disclosure": 2,   # summary  # partially verified
            "evaluation_disclosure": 3,      # external evals (external red teaming, capabilities reports)
            "incident_reporting": 3,         # internal + external (Hugging Face breach revealed Aug 2026)
        },
        "open_weight_governance": {
            "license_clarity": None,         # closed weights
            "deployment_tools": None,
            "red_teaming": None,
            "community_governance": None,
        },
    },

    "meta-msl": {
        "governance_maturity": {
            "safety_framework_published": 4, # published with thresholds + pause (stop development for critical risk)
            "framework_bindingness": 2,      # self-administered
            "pause_commitment": 3,           # mechanism + thresholds (high/critical risk, stop development)
            "external_review": 1,            # ad-hoc (internal/external researcher input, not structured)
            "academic_eval_score": 3,        # 21% (arXiv:2512.01166)
        },
        "runtime_governance": {
            "kill_switch": 1,               # manual only (Llama 4 Behemoth paused)  # unverified
            "circuit_breaker": 0,            # none  # unverified
            "cost_governance": 0,            # none  # unverified
            "audit_logging": 1,              # basic logs  # unverified
            "output_validation": 1,          # basic filtering  # unverified
            "capability_fencing": 1,         # basic sandbox  # unverified
        },
        "compliance_posture": {
            "eu_ai_act_gpai": 2,             # partial (transparency CoP only, not GPAI CoP)
            "nist_ai_rmf": 2,                # partial  # unverified
            "iso_42001": 1,                  # aware  # unverified
            "soc2": 4,                       # Type II (Meta enterprise)  # unverified
            "code_of_practice_signatory": 0, # not signed (GPAI CoP)
        },
        "agent_governance": {
            "multi_agent_coordination": 1,   # single agent (Muse Code)  # partially verified
            "agent_identity": 1,             # basic ID  # unverified
            "delegation_support": 1,         # manual  # unverified
            "tool_use_governance": 2,        # permission-based (Muse Code terminal)  # unverified
            "convergence_guarantees": 0,     # none  # unverified
        },
        "transparency": {
            "model_card": 3,                 # detailed + evals (system cards for Llama)
            "system_card": 3,                # detailed + safety
            "training_data_disclosure": 2,   # summary + sources  # partially verified
            "evaluation_disclosure": 2,      # internal + summary
            "incident_reporting": 1,         # ad-hoc  # unverified
        },
        "open_weight_governance": {
            "license_clarity": 1,            # ambiguous (Llama Community License has commercial restrictions)
            "deployment_tools": 3,           # API + docs + governance (Meta Model API, Llama ecosystem)  # partially verified
            "red_teaming": 2,                # internal + published (system cards)  # partially verified
            "community_governance": 3,       # contribution + review (Llama ecosystem)  # partially verified
        },
    },

    "xai": {
        "governance_maturity": {
            "safety_framework_published": 3, # published with thresholds (quantitative thresholds; weakened from draft)
            "framework_bindingness": 1,      # voluntary/aspirational ("anti-self-regulation" posture)
            "pause_commitment": 2,           # mechanism defined (stop-development for unmitigable critical risk)
            "external_review": 1,            # ad-hoc (third-party review mentioned, not evidenced)
            "academic_eval_score": 2,        # 16% (arXiv:2512.01166)
        },
        "runtime_governance": {
            "kill_switch": 0,               # none  # unverified
            "circuit_breaker": 0,            # none  # unverified
            "cost_governance": 0,            # none  # unverified
            "audit_logging": 1,              # basic logs  # unverified
            "output_validation": 1,          # basic filtering ("high-precision safeguards")  # unverified
            "capability_fencing": 0,         # none  # unverified
        },
        "compliance_posture": {
            "eu_ai_act_gpai": 2,             # partial (signed Safety & Security chapter only)
            "nist_ai_rmf": 2,                # partial (references NIST AI RMF in FAIF)
            "iso_42001": 2,                  # planning (references ISO/IEC 42001 in FAIF)
            "soc2": 0,                       # none  # unverified
            "code_of_practice_signatory": 1, # observer (partial signatory, one chapter only)
        },
        "agent_governance": {
            "multi_agent_coordination": 1,   # single agent (Grok Build)  # partially verified
            "agent_identity": 1,             # basic ID  # unverified
            "delegation_support": 1,         # manual  # unverified
            "tool_use_governance": 1,        # basic (Grok Build CLI)  # unverified
            "convergence_guarantees": 0,     # none  # unverified
        },
        "transparency": {
            "model_card": 3,                 # detailed + evals (Grok 4.5 model card)
            "system_card": 2,                # detailed (model card serves as system card)
            "training_data_disclosure": 3,   # summary + sources + sizes (public training content summary)
            "evaluation_disclosure": 2,      # internal + summary
            "incident_reporting": 1,         # ad-hoc  # unverified
        },
        "open_weight_governance": {
            "license_clarity": None,         # closed weights (current models)
            "deployment_tools": None,
            "red_teaming": None,
            "community_governance": None,
        },
    },

    "microsoft-ai": {
        "governance_maturity": {
            "safety_framework_published": 2, # published but vague (Responsible AI Standard 2022, no frontier thresholds)
            "framework_bindingness": 2,      # self-administered
            "pause_commitment": 0,           # none (no pause mechanism for frontier models)
            "external_review": 1,            # ad-hoc (AI Red Team exists but not prominent)
            "academic_eval_score": 2,        # 18% (arXiv:2512.01166)
        },
        "runtime_governance": {
            "kill_switch": 1,               # manual only  # unverified
            "circuit_breaker": 1,            # basic  # unverified
            "cost_governance": 1,            # basic limits (Azure cost management)  # unverified
            "audit_logging": 3,              # append-only (enterprise-grade audit through Azure)  # unverified
            "output_validation": 2,          # rule-based (Azure AI content filtering)  # unverified
            "capability_fencing": 2,         # permission-based (Azure RBAC)  # unverified
        },
        "compliance_posture": {
            "eu_ai_act_gpai": 4,             # full baseline compliance (signed CoP in full)
            "nist_ai_rmf": 3,                # mapped (enterprise compliance)  # partially verified
            "iso_42001": 3,                  # implementing  # unverified
            "soc2": 4,                       # Type II (Microsoft enterprise)  # unverified
            "code_of_practice_signatory": 3, # signed + reporting
        },
        "agent_governance": {
            "multi_agent_coordination": 2,   # sequential (Copilot workflows)  # partially verified
            "agent_identity": 2,             # ID + auth (Microsoft Entra ID)  # unverified
            "delegation_support": 2,         # token-based (OAuth/AAD)  # unverified
            "tool_use_governance": 2,        # permission-based (Copilot permissions)  # unverified
            "convergence_guarantees": 1,     # basic  # unverified
        },
        "transparency": {
            "model_card": 2,                 # detailed (Phi model cards, MAI documentation)  # partially verified
            "system_card": 2,                # detailed  # unverified
            "training_data_disclosure": 2,   # summary ("clean, traceable, enterprise-grade")  # partially verified
            "evaluation_disclosure": 2,      # internal + summary  # unverified
            "incident_reporting": 1,         # ad-hoc  # unverified
        },
        "open_weight_governance": {
            "license_clarity": 2,            # standard OSI (Phi models MIT)  # partially verified
            "deployment_tools": 3,           # API + docs + governance (Foundry, Azure AI)  # partially verified
            "red_teaming": 1,                # internal  # unverified
            "community_governance": 2,       # contribution process  # unverified
        },
    },

    # ======================================================================
    # Tier 2 — Chinese Open-Weight Frontier (Labs 7-13)
    # ======================================================================

    "alibaba-qwen": {
        "governance_maturity": {
            "safety_framework_published": 0, # none
            "framework_bindingness": 0,      # none
            "pause_commitment": 0,           # none
            "external_review": 0,            # none
            "academic_eval_score": 0,        # not evaluated
        },
        "runtime_governance": {
            "kill_switch": 0,               # none  # unverified
            "circuit_breaker": 0,            # none  # unverified
            "cost_governance": 0,            # none  # unverified
            "audit_logging": 1,              # basic logs  # unverified
            "output_validation": 1,          # basic filtering  # unverified
            "capability_fencing": 1,         # basic sandbox  # unverified
        },
        "compliance_posture": {
            "eu_ai_act_gpai": 1,             # aware (not signed, EU market via API)
            "nist_ai_rmf": 0,                # none  # unverified
            "iso_42001": 0,                  # none  # unverified
            "soc2": 0,                       # none  # unverified
            "code_of_practice_signatory": 0, # not signed
        },
        "agent_governance": {
            "multi_agent_coordination": 1,   # single agent  # unverified
            "agent_identity": 1,             # basic ID  # unverified
            "delegation_support": 1,         # manual  # unverified
            "tool_use_governance": 1,        # basic  # unverified
            "convergence_guarantees": 0,     # none  # unverified
        },
        "transparency": {
            "model_card": 2,                 # detailed (technical reports for Qwen models)  # partially verified
            "system_card": 1,                # basic  # unverified
            "training_data_disclosure": 1,   # summary  # unverified
            "evaluation_disclosure": 2,      # internal + summary (benchmark results published)
            "incident_reporting": 0,         # none  # unverified
        },
        "open_weight_governance": {
            "license_clarity": 3,            # standard + commercial terms (Apache 2.0 + custom Qwen3.8-Max License)  # partially verified
            "deployment_tools": 3,           # API + docs + governance (ModelScope, Bailian, Qwen API)  # partially verified
            "red_teaming": 1,                # internal  # unverified
            "community_governance": 3,       # contribution + review (ModelScope, 300K+ derivatives)  # partially verified
        },
    },

    "zai-zhipu": {
        "governance_maturity": {
            "safety_framework_published": 0, # none
            "framework_bindingness": 0,      # none
            "pause_commitment": 0,           # none
            "external_review": 0,            # none
            "academic_eval_score": 0,        # not evaluated
        },
        "runtime_governance": {
            "kill_switch": 0,               # none  # unverified
            "circuit_breaker": 0,            # none  # unverified
            "cost_governance": 0,            # none  # unverified
            "audit_logging": 1,              # basic logs  # unverified
            "output_validation": 1,          # basic filtering  # unverified
            "capability_fencing": 1,         # basic sandbox  # unverified
        },
        "compliance_posture": {
            "eu_ai_act_gpai": 1,             # aware (not signed, EU market via OpenRouter)
            "nist_ai_rmf": 0,                # none  # unverified
            "iso_42001": 0,                  # none  # unverified
            "soc2": 0,                       # none  # unverified
            "code_of_practice_signatory": 0, # not signed
        },
        "agent_governance": {
            "multi_agent_coordination": 1,   # single agent (ZCode)  # unverified
            "agent_identity": 1,             # basic ID  # unverified
            "delegation_support": 1,         # manual  # unverified
            "tool_use_governance": 1,        # basic  # unverified
            "convergence_guarantees": 0,     # none  # unverified
        },
        "transparency": {
            "model_card": 2,                 # detailed (technical reports for GLM models)  # partially verified
            "system_card": 1,                # basic  # unverified
            "training_data_disclosure": 1,   # summary  # unverified
            "evaluation_disclosure": 2,      # internal + summary (benchmark results published)
            "incident_reporting": 0,         # none  # unverified
        },
        "open_weight_governance": {
            "license_clarity": 2,            # standard OSI (MIT license)
            "deployment_tools": 2,           # API + docs (Z.ai API, OpenRouter)  # partially verified
            "red_teaming": 1,                # internal  # unverified
            "community_governance": 2,       # contribution process (HuggingFace)  # unverified
        },
    },

    "deepseek": {
        "governance_maturity": {
            "safety_framework_published": 0, # none
            "framework_bindingness": 0,      # none
            "pause_commitment": 0,           # none
            "external_review": 0,            # none
            "academic_eval_score": 0,        # not evaluated
        },
        "runtime_governance": {
            "kill_switch": 0,               # none  # unverified
            "circuit_breaker": 0,            # none  # unverified
            "cost_governance": 0,            # none  # unverified
            "audit_logging": 1,              # basic logs  # unverified
            "output_validation": 1,          # basic filtering  # unverified
            "capability_fencing": 0,         # none  # unverified
        },
        "compliance_posture": {
            "eu_ai_act_gpai": 1,             # aware (not signed, systemic risk likely, no EU auth rep)
            "nist_ai_rmf": 0,                # none  # unverified
            "iso_42001": 0,                  # none  # unverified
            "soc2": 0,                       # none  # unverified
            "code_of_practice_signatory": 0, # not signed
        },
        "agent_governance": {
            "multi_agent_coordination": 0,   # none  # unverified
            "agent_identity": 1,             # basic ID (API)  # unverified
            "delegation_support": 1,         # manual  # unverified
            "tool_use_governance": 0,        # none  # unverified
            "convergence_guarantees": 0,     # none  # unverified
        },
        "transparency": {
            "model_card": 2,                 # detailed (technical reports for V4)  # partially verified
            "system_card": 1,                # basic  # unverified
            "training_data_disclosure": 1,   # summary (model algorithm disclosure)
            "evaluation_disclosure": 2,      # internal + summary (benchmark results published)
            "incident_reporting": 0,         # none  # unverified
        },
        "open_weight_governance": {
            "license_clarity": 2,            # standard OSI (MIT license)
            "deployment_tools": 2,           # API + docs (DeepSeek API, HuggingFace)
            "red_teaming": 1,                # internal  # unverified
            "community_governance": 2,       # contribution process (HuggingFace, GitHub)  # unverified
        },
    },

    "minimax": {
        "governance_maturity": {
            "safety_framework_published": 0, # none
            "framework_bindingness": 0,      # none
            "pause_commitment": 0,           # none
            "external_review": 0,            # none
            "academic_eval_score": 0,        # not evaluated
        },
        "runtime_governance": {
            "kill_switch": 0,               # none  # unverified
            "circuit_breaker": 0,            # none  # unverified
            "cost_governance": 0,            # none  # unverified
            "audit_logging": 1,              # basic logs  # unverified
            "output_validation": 1,          # basic filtering  # unverified
            "capability_fencing": 0,         # none  # unverified
        },
        "compliance_posture": {
            "eu_ai_act_gpai": 1,             # aware (not signed, going global)
            "nist_ai_rmf": 0,                # none  # unverified
            "iso_42001": 0,                  # none  # unverified
            "soc2": 0,                       # none  # unverified
            "code_of_practice_signatory": 0, # not signed
        },
        "agent_governance": {
            "multi_agent_coordination": 1,   # single agent (Talkie)  # unverified
            "agent_identity": 1,             # basic ID  # unverified
            "delegation_support": 0,         # none  # unverified
            "tool_use_governance": 0,        # none  # unverified
            "convergence_guarantees": 0,     # none  # unverified
        },
        "transparency": {
            "model_card": 2,                 # detailed (M3 announcement blog)  # partially verified
            "system_card": 1,                # basic  # unverified
            "training_data_disclosure": 1,   # summary  # unverified
            "evaluation_disclosure": 1,      # internal  # unverified
            "incident_reporting": 0,         # none  # unverified
        },
        "open_weight_governance": {
            "license_clarity": 1,            # ambiguous (custom license)  # unverified
            "deployment_tools": 2,           # API + docs (MiniMax API)  # unverified
            "red_teaming": 1,                # internal  # unverified
            "community_governance": 1,       # basic  # unverified
        },
    },

    "moonshot": {
        "governance_maturity": {
            "safety_framework_published": 0, # none
            "framework_bindingness": 0,      # none
            "pause_commitment": 0,           # none
            "external_review": 0,            # none
            "academic_eval_score": 0,        # not evaluated
        },
        "runtime_governance": {
            "kill_switch": 0,               # none  # unverified
            "circuit_breaker": 0,            # none  # unverified
            "cost_governance": 0,            # none  # unverified
            "audit_logging": 1,              # basic logs  # unverified
            "output_validation": 1,          # basic filtering  # unverified
            "capability_fencing": 0,         # none  # unverified
        },
        "compliance_posture": {
            "eu_ai_act_gpai": 1,             # aware (not signed, global API)
            "nist_ai_rmf": 0,                # none  # unverified
            "iso_42001": 0,                  # none  # unverified
            "soc2": 0,                       # none  # unverified
            "code_of_practice_signatory": 0, # not signed
        },
        "agent_governance": {
            "multi_agent_coordination": 4,   # parallel + coordinated (Agent Swarm, up to 100 sub-agents)  # partially verified
            "agent_identity": 1,             # basic ID  # unverified
            "delegation_support": 1,         # manual  # unverified
            "tool_use_governance": 2,        # permission-based (Kimi Code)  # unverified
            "convergence_guarantees": 1,     # basic  # unverified
        },
        "transparency": {
            "model_card": 2,                 # detailed (K3 technical report)  # partially verified
            "system_card": 1,                # basic  # unverified
            "training_data_disclosure": 1,   # summary  # unverified
            "evaluation_disclosure": 2,      # internal + summary (benchmark results published)
            "incident_reporting": 0,         # none  # unverified
        },
        "open_weight_governance": {
            "license_clarity": 1,            # ambiguous (custom license)
            "deployment_tools": 2,           # API + docs (Kimi API, GitHub)  # partially verified
            "red_teaming": 1,                # internal  # unverified
            "community_governance": 2,       # contribution process (GitHub)  # unverified
        },
    },

    "bytedance": {
        "governance_maturity": {
            "safety_framework_published": 0, # none
            "framework_bindingness": 0,      # none
            "pause_commitment": 0,           # none
            "external_review": 0,            # none
            "academic_eval_score": 0,        # not evaluated
        },
        "runtime_governance": {
            "kill_switch": 0,               # none  # unverified
            "circuit_breaker": 0,            # none  # unverified
            "cost_governance": 0,            # none  # unverified
            "audit_logging": 1,              # basic logs  # unverified
            "output_validation": 1,          # basic filtering  # unverified
            "capability_fencing": 0,         # none  # unverified
        },
        "compliance_posture": {
            "eu_ai_act_gpai": 1,             # aware (not signed)
            "nist_ai_rmf": 0,                # none  # unverified
            "iso_42001": 0,                  # none  # unverified
            "soc2": 0,                       # none  # unverified
            "code_of_practice_signatory": 0, # not signed
        },
        "agent_governance": {
            "multi_agent_coordination": 2,   # sequential (Seed2.0 long-horizon workflows)  # partially verified
            "agent_identity": 1,             # basic ID  # unverified
            "delegation_support": 1,         # manual  # unverified
            "tool_use_governance": 1,        # basic  # unverified
            "convergence_guarantees": 0,     # none  # unverified
        },
        "transparency": {
            "model_card": 2,                 # detailed (Seed2.0 documentation)  # partially verified
            "system_card": 1,                # basic  # unverified
            "training_data_disclosure": 1,   # summary  # unverified
            "evaluation_disclosure": 1,      # internal  # unverified
            "incident_reporting": 0,         # none  # unverified
        },
        "open_weight_governance": {
            "license_clarity": 2,            # standard OSI (Seed-OSS-36B Apache 2.0)  # partially verified
            "deployment_tools": 2,           # API + docs (Doubao API)  # partially verified
            "red_teaming": 1,                # internal  # unverified
            "community_governance": 1,       # basic  # unverified
        },
    },

    "tencent": {
        "governance_maturity": {
            "safety_framework_published": 0, # none
            "framework_bindingness": 0,      # none
            "pause_commitment": 0,           # none
            "external_review": 0,            # none
            "academic_eval_score": 0,        # not evaluated
        },
        "runtime_governance": {
            "kill_switch": 0,               # none  # unverified
            "circuit_breaker": 0,            # none  # unverified
            "cost_governance": 0,            # none  # unverified
            "audit_logging": 1,              # basic logs  # unverified
            "output_validation": 1,          # basic filtering  # unverified
            "capability_fencing": 0,         # none  # unverified
        },
        "compliance_posture": {
            "eu_ai_act_gpai": 1,             # aware (not signed)
            "nist_ai_rmf": 0,                # none  # unverified
            "iso_42001": 0,                  # none  # unverified
            "soc2": 0,                       # none  # unverified
            "code_of_practice_signatory": 0, # not signed
        },
        "agent_governance": {
            "multi_agent_coordination": 2,   # sequential (WorkBuddy/CodeBuddy)  # partially verified
            "agent_identity": 1,             # basic ID  # unverified
            "delegation_support": 1,         # manual  # unverified
            "tool_use_governance": 1,        # basic  # unverified
            "convergence_guarantees": 0,     # none  # unverified
        },
        "transparency": {
            "model_card": 2,                 # detailed (Hy3 announcement)  # partially verified
            "system_card": 1,                # basic  # unverified
            "training_data_disclosure": 1,   # summary  # unverified
            "evaluation_disclosure": 1,      # internal  # unverified
            "incident_reporting": 0,         # none  # unverified
        },
        "open_weight_governance": {
            "license_clarity": 2,            # standard OSI  # unverified
            "deployment_tools": 2,           # API + docs  # unverified
            "red_teaming": 1,                # internal  # unverified
            "community_governance": 2,       # contribution process  # unverified
        },
    },

    # ======================================================================
    # Tier 3 — Western Mid-Tier + Chinese Vertical (Labs 14-20)
    # ======================================================================

    "mistral": {
        "governance_maturity": {
            "safety_framework_published": 0, # none (moderation tools only)
            "framework_bindingness": 0,      # none
            "pause_commitment": 0,           # none
            "external_review": 0,            # none
            "academic_eval_score": 0,        # excluded from eval
        },
        "runtime_governance": {
            "kill_switch": 0,               # none  # unverified
            "circuit_breaker": 0,            # none  # unverified
            "cost_governance": 0,            # none  # unverified
            "audit_logging": 1,              # basic logs  # unverified
            "output_validation": 2,          # rule-based (Moderation API, Shieldstral)  # partially verified
            "capability_fencing": 1,         # basic sandbox  # unverified
        },
        "compliance_posture": {
            "eu_ai_act_gpai": 4,             # full baseline compliance (EU-based, full CoP signatory)
            "nist_ai_rmf": 1,                # aware  # unverified
            "iso_42001": 2,                  # planning  # unverified
            "soc2": 3,                       # Type I  # unverified
            "code_of_practice_signatory": 3, # signed + reporting
        },
        "agent_governance": {
            "multi_agent_coordination": 1,   # single agent (Codestral)  # unverified
            "agent_identity": 1,             # basic ID  # unverified
            "delegation_support": 1,         # manual  # unverified
            "tool_use_governance": 1,        # basic  # unverified
            "convergence_guarantees": 0,     # none  # unverified
        },
        "transparency": {
            "model_card": 2,                 # detailed (model documentation)  # partially verified
            "system_card": 1,                # basic  # unverified
            "training_data_disclosure": 1,   # summary  # unverified
            "evaluation_disclosure": 2,      # internal + summary (benchmark results)
            "incident_reporting": 0,         # none  # unverified
        },
        "open_weight_governance": {
            "license_clarity": 2,            # standard OSI (Apache 2.0 for open models)  # partially verified
            "deployment_tools": 3,           # API + docs + governance (La Plateforme, Shieldstral)  # partially verified
            "red_teaming": 2,                # internal + published (Shieldstral, moderation tools)  # partially verified
            "community_governance": 2,       # contribution process (Open Secure AI Alliance w/ NVIDIA)  # partially verified
        },
    },

    "cohere": {
        "governance_maturity": {
            "safety_framework_published": 2, # published but vague (Secure AI Frontier Model Framework, 8%, enterprise-focused)
            "framework_bindingness": 1,      # voluntary/aspirational
            "pause_commitment": 0,           # none
            "external_review": 1,            # ad-hoc
            "academic_eval_score": 1,        # 8% (arXiv:2512.01166)
        },
        "runtime_governance": {
            "kill_switch": 0,               # none  # unverified
            "circuit_breaker": 0,            # none  # unverified
            "cost_governance": 0,            # none  # unverified
            "audit_logging": 2,              # structured logs  # unverified
            "output_validation": 2,          # rule-based  # unverified
            "capability_fencing": 2,         # permission-based (enterprise focus)  # unverified
        },
        "compliance_posture": {
            "eu_ai_act_gpai": 3,             # Code of Practice signatory (signed in full)
            "nist_ai_rmf": 2,                # partial  # unverified
            "iso_42001": 1,                  # aware  # unverified
            "soc2": 4,                       # Type II (enterprise/defense focus)  # unverified
            "code_of_practice_signatory": 3, # signed + reporting
        },
        "agent_governance": {
            "multi_agent_coordination": 1,   # single agent  # unverified
            "agent_identity": 2,             # ID + auth (enterprise focus)  # unverified
            "delegation_support": 1,         # manual  # unverified
            "tool_use_governance": 1,        # basic  # unverified
            "convergence_guarantees": 0,     # none  # unverified
        },
        "transparency": {
            "model_card": 3,                 # detailed + evals (model cards for Command A+)  # partially verified
            "system_card": 2,                # detailed (security documentation)  # partially verified
            "training_data_disclosure": 1,   # summary  # unverified
            "evaluation_disclosure": 2,      # internal + summary  # unverified
            "incident_reporting": 1,         # ad-hoc  # unverified
        },
        "open_weight_governance": {
            "license_clarity": 2,            # standard OSI (Apache 2.0)
            "deployment_tools": 3,           # API + docs + governance (enterprise, air-gapped deployment)  # partially verified
            "red_teaming": 2,                # internal + published (framework published)  # partially verified
            "community_governance": 1,       # basic  # unverified
        },
    },

    "ssi": {
        "governance_maturity": {
            "safety_framework_published": 0, # none (mission statement only)
            "framework_bindingness": 0,      # none
            "pause_commitment": 0,           # none
            "external_review": 0,            # none
            "academic_eval_score": 0,        # not evaluated
        },
        "runtime_governance": {
            "kill_switch": 0,               # none
            "circuit_breaker": 0,            # none
            "cost_governance": 0,            # none
            "audit_logging": 0,              # none
            "output_validation": 0,          # none
            "capability_fencing": 0,         # none
        },
        "compliance_posture": {
            "eu_ai_act_gpai": 0,             # non-compliant (no products)
            "nist_ai_rmf": 0,                # none
            "iso_42001": 0,                  # none
            "soc2": 0,                       # none
            "code_of_practice_signatory": 0, # not signed
        },
        "agent_governance": {
            "multi_agent_coordination": 0,   # none
            "agent_identity": 0,             # none
            "delegation_support": 0,         # none
            "tool_use_governance": 0,        # none
            "convergence_guarantees": 0,     # none
        },
        "transparency": {
            "model_card": 0,                 # none (no models published)
            "system_card": 0,                # none
            "training_data_disclosure": 0,   # none
            "evaluation_disclosure": 0,      # none
            "incident_reporting": 0,         # none
        },
        "open_weight_governance": {
            "license_clarity": None,         # no models
            "deployment_tools": None,
            "red_teaming": None,
            "community_governance": None,
        },
    },

    "baidu": {
        "governance_maturity": {
            "safety_framework_published": 0, # none
            "framework_bindingness": 0,      # none
            "pause_commitment": 0,           # none
            "external_review": 0,            # none
            "academic_eval_score": 0,        # not evaluated
        },
        "runtime_governance": {
            "kill_switch": 0,               # none  # unverified
            "circuit_breaker": 0,            # none  # unverified
            "cost_governance": 0,            # none  # unverified
            "audit_logging": 1,              # basic logs  # unverified
            "output_validation": 1,          # basic filtering  # unverified
            "capability_fencing": 0,         # none  # unverified
        },
        "compliance_posture": {
            "eu_ai_act_gpai": 1,             # aware (1.5B daily API calls, global reach)
            "nist_ai_rmf": 0,                # none  # unverified
            "iso_42001": 0,                  # none  # unverified
            "soc2": 0,                       # none  # unverified
            "code_of_practice_signatory": 0, # not signed
        },
        "agent_governance": {
            "multi_agent_coordination": 1,   # single agent  # unverified
            "agent_identity": 1,             # basic ID  # unverified
            "delegation_support": 1,         # manual  # unverified
            "tool_use_governance": 1,        # basic  # unverified
            "convergence_guarantees": 0,     # none  # unverified
        },
        "transparency": {
            "model_card": 2,                 # detailed  # unverified
            "system_card": 1,                # basic  # unverified
            "training_data_disclosure": 1,   # summary  # unverified
            "evaluation_disclosure": 2,      # internal + summary (LMArena top-10)  # partially verified
            "incident_reporting": 0,         # none  # unverified
        },
        "open_weight_governance": {
            "license_clarity": 2,            # standard OSI (for open variants)  # unverified
            "deployment_tools": 2,           # API + docs (ERNIE API)  # partially verified
            "red_teaming": 1,                # internal  # unverified
            "community_governance": 1,       # basic  # unverified
        },
    },

    "huawei": {
        "governance_maturity": {
            "safety_framework_published": 0, # none
            "framework_bindingness": 0,      # none
            "pause_commitment": 0,           # none
            "external_review": 0,            # none
            "academic_eval_score": 0,        # not evaluated
        },
        "runtime_governance": {
            "kill_switch": 0,               # none  # unverified
            "circuit_breaker": 0,            # none  # unverified
            "cost_governance": 0,            # none  # unverified
            "audit_logging": 1,              # basic logs  # unverified
            "output_validation": 0,          # none  # unverified
            "capability_fencing": 0,         # none  # unverified
        },
        "compliance_posture": {
            "eu_ai_act_gpai": 0,             # non-compliant (limited global presence)  # unverified
            "nist_ai_rmf": 0,                # none  # unverified
            "iso_42001": 0,                  # none  # unverified
            "soc2": 0,                       # none  # unverified
            "code_of_practice_signatory": 0, # not signed
        },
        "agent_governance": {
            "multi_agent_coordination": 1,   # single agent  # unverified
            "agent_identity": 1,             # basic ID  # unverified
            "delegation_support": 0,         # none  # unverified
            "tool_use_governance": 0,        # none  # unverified
            "convergence_guarantees": 0,     # none  # unverified
        },
        "transparency": {
            "model_card": 1,                 # basic  # unverified
            "system_card": 1,                # basic  # unverified
            "training_data_disclosure": 1,   # summary  # unverified
            "evaluation_disclosure": 1,      # internal  # unverified
            "incident_reporting": 0,         # none  # unverified
        },
        "open_weight_governance": {
            "license_clarity": 2,            # standard OSI (openPangu)  # unverified
            "deployment_tools": 1,           # basic  # unverified
            "red_teaming": 0,                # none  # unverified
            "community_governance": 1,       # basic  # unverified
        },
    },

    "amazon-aws": {
        "governance_maturity": {
            "safety_framework_published": 3, # published with thresholds (Frontier Model Safety Framework, 18%)
            "framework_bindingness": 2,      # self-administered
            "pause_commitment": 1,           # mentioned but no mechanism  # unverified
            "external_review": 1,            # ad-hoc  # unverified
            "academic_eval_score": 2,        # 18% (arXiv:2512.01166)
        },
        "runtime_governance": {
            "kill_switch": 1,               # manual only  # unverified
            "circuit_breaker": 1,            # basic  # unverified
            "cost_governance": 1,            # basic limits (AWS billing)  # unverified
            "audit_logging": 2,              # structured logs (CloudTrail)  # unverified
            "output_validation": 2,          # rule-based (Bedrock content filtering)  # unverified
            "capability_fencing": 2,         # permission-based (IAM)  # unverified
        },
        "compliance_posture": {
            "eu_ai_act_gpai": 4,             # full baseline compliance (signed CoP in full)
            "nist_ai_rmf": 3,                # mapped  # partially verified
            "iso_42001": 2,                  # planning  # unverified
            "soc2": 4,                       # Type II (AWS enterprise)  # unverified
            "code_of_practice_signatory": 3, # signed + reporting
        },
        "agent_governance": {
            "multi_agent_coordination": 2,   # sequential (Bedrock agents)  # partially verified
            "agent_identity": 2,             # ID + auth (AWS IAM)  # unverified
            "delegation_support": 2,         # token-based (STS)  # unverified
            "tool_use_governance": 2,        # permission-based (IAM)  # unverified
            "convergence_guarantees": 1,     # basic  # unverified
        },
        "transparency": {
            "model_card": 2,                 # detailed (Nova documentation)  # partially verified
            "system_card": 2,                # detailed  # unverified
            "training_data_disclosure": 1,   # summary  # unverified
            "evaluation_disclosure": 2,      # internal + summary  # unverified
            "incident_reporting": 1,         # ad-hoc  # unverified
        },
        "open_weight_governance": {
            "license_clarity": None,         # closed weights (proprietary)
            "deployment_tools": None,
            "red_teaming": None,
            "community_governance": None,
        },
    },

    "tml": {
        "governance_maturity": {
            "safety_framework_published": 0, # none  # unverified
            "framework_bindingness": 0,      # none
            "pause_commitment": 0,           # none
            "external_review": 0,            # none
            "academic_eval_score": 0,        # not evaluated
        },
        "runtime_governance": {
            "kill_switch": 0,               # none  # unverified
            "circuit_breaker": 0,            # none  # unverified
            "cost_governance": 0,            # none  # unverified
            "audit_logging": 1,              # basic logs  # unverified
            "output_validation": 1,          # basic filtering  # unverified
            "capability_fencing": 1,         # basic sandbox  # unverified
        },
        "compliance_posture": {
            "eu_ai_act_gpai": 1,             # aware  # unverified
            "nist_ai_rmf": 0,                # none  # unverified
            "iso_42001": 0,                  # none  # unverified
            "soc2": 0,                       # none  # unverified
            "code_of_practice_signatory": 0, # not signed  # unverified
        },
        "agent_governance": {
            "multi_agent_coordination": 1,   # single agent  # unverified
            "agent_identity": 1,             # basic ID  # unverified
            "delegation_support": 1,         # manual  # unverified
            "tool_use_governance": 1,        # basic  # unverified
            "convergence_guarantees": 0,     # none  # unverified
        },
        "transparency": {
            "model_card": 2,                 # detailed (Inkling documentation)  # partially verified
            "system_card": 1,                # basic  # unverified
            "training_data_disclosure": 2,   # summary + sources (open weights, some training info)  # partially verified
            "evaluation_disclosure": 2,      # internal + summary  # unverified
            "incident_reporting": 0,         # none  # unverified
        },
        "open_weight_governance": {
            "license_clarity": 2,            # standard OSI (Apache 2.0, Inkling)
            "deployment_tools": 3,           # API + docs + governance (Tinker fine-tuning API)  # partially verified
            "red_teaming": 1,                # internal  # unverified
            "community_governance": 2,       # contribution process  # unverified
        },
    },

    # ======================================================================
    # Tier 4 — Hyperscaler / Device-Integrated (Labs 21-25)
    # ======================================================================

    "nvidia": {
        "governance_maturity": {
            "safety_framework_published": 2, # published but vague (Frontier AI Risk Assessment, 16%)
            "framework_bindingness": 1,      # voluntary/aspirational
            "pause_commitment": 0,           # none  # unverified
            "external_review": 1,            # ad-hoc  # unverified
            "academic_eval_score": 2,        # 16% (arXiv:2512.01166)
        },
        "runtime_governance": {
            "kill_switch": 0,               # none  # unverified
            "circuit_breaker": 0,            # none  # unverified
            "cost_governance": 1,            # basic limits (DGX Cloud billing)  # unverified
            "audit_logging": 2,              # structured logs  # unverified
            "output_validation": 1,          # basic filtering  # unverified
            "capability_fencing": 1,         # basic sandbox  # unverified
        },
        "compliance_posture": {
            "eu_ai_act_gpai": 1,             # aware  # unverified
            "nist_ai_rmf": 3,                # mapped (NIST AI RMF referenced)  # partially verified
            "iso_42001": 1,                  # aware  # unverified
            "soc2": 4,                       # Type II (Nvidia enterprise)  # unverified
            "code_of_practice_signatory": 0, # not signed
        },
        "agent_governance": {
            "multi_agent_coordination": 1,   # single agent  # unverified
            "agent_identity": 1,             # basic ID  # unverified
            "delegation_support": 1,         # manual  # unverified
            "tool_use_governance": 1,        # basic  # unverified
            "convergence_guarantees": 0,     # none  # unverified
        },
        "transparency": {
            "model_card": 3,                 # detailed + evals (Nemotron technical report)  # partially verified
            "system_card": 2,                # detailed  # unverified
            "training_data_disclosure": 2,   # summary + sources (20T tokens mentioned)  # partially verified
            "evaluation_disclosure": 3,      # external evals (technical report with benchmarks)  # partially verified
            "incident_reporting": 0,         # none  # unverified
        },
        "open_weight_governance": {
            "license_clarity": 3,            # standard + commercial terms (OpenMDW 1.1)  # partially verified
            "deployment_tools": 3,           # API + docs + governance (NIM, DGX Cloud)  # partially verified
            "red_teaming": 2,                # internal + published (technical report)  # partially verified
            "community_governance": 2,       # contribution process  # unverified
        },
    },

    "lg-ai": {
        "governance_maturity": {
            "safety_framework_published": 0, # none  # unverified
            "framework_bindingness": 0,      # none
            "pause_commitment": 0,           # none
            "external_review": 0,            # none
            "academic_eval_score": 0,        # not evaluated
        },
        "runtime_governance": {
            "kill_switch": 0,               # none  # unverified
            "circuit_breaker": 0,            # none  # unverified
            "cost_governance": 0,            # none  # unverified
            "audit_logging": 1,              # basic logs  # unverified
            "output_validation": 1,          # basic filtering  # unverified
            "capability_fencing": 0,         # none  # unverified
        },
        "compliance_posture": {
            "eu_ai_act_gpai": 0,             # non-compliant  # unverified
            "nist_ai_rmf": 0,                # none  # unverified
            "iso_42001": 0,                  # none  # unverified
            "soc2": 0,                       # none  # unverified
            "code_of_practice_signatory": 0, # not signed  # unverified
        },
        "agent_governance": {
            "multi_agent_coordination": 1,   # single agent  # unverified
            "agent_identity": 1,             # basic ID  # unverified
            "delegation_support": 0,         # none  # unverified
            "tool_use_governance": 0,        # none  # unverified
            "convergence_guarantees": 0,     # none  # unverified
        },
        "transparency": {
            "model_card": 2,                 # detailed  # unverified
            "system_card": 1,                # basic  # unverified
            "training_data_disclosure": 1,   # summary  # unverified
            "evaluation_disclosure": 1,      # internal  # unverified
            "incident_reporting": 0,         # none  # unverified
        },
        "open_weight_governance": {
            "license_clarity": None,         # closed weights (proprietary)
            "deployment_tools": None,
            "red_teaming": None,
            "community_governance": None,
        },
    },

    "apple": {
        "governance_maturity": {
            "safety_framework_published": 0, # none (privacy architecture only, no safety framework)
            "framework_bindingness": 0,      # none
            "pause_commitment": 0,           # none
            "external_review": 0,            # none
            "academic_eval_score": 0,        # not evaluated
        },
        "runtime_governance": {
            "kill_switch": 1,               # manual only  # unverified
            "circuit_breaker": 1,            # basic (Private Cloud Compute architecture)  # unverified
            "cost_governance": 0,            # none  # unverified
            "audit_logging": 3,              # append-only (PCC attested, code-audited)  # partially verified
            "output_validation": 1,          # basic filtering  # unverified
            "capability_fencing": 2,         # permission-based (PCC privacy architecture)  # partially verified
        },
        "compliance_posture": {
            "eu_ai_act_gpai": 2,             # partial (EU market presence, some compliance)  # unverified
            "nist_ai_rmf": 1,                # aware  # unverified
            "iso_42001": 1,                  # aware  # unverified
            "soc2": 4,                       # Type II (Apple enterprise)  # unverified
            "code_of_practice_signatory": 0, # not signed  # unverified
        },
        "agent_governance": {
            "multi_agent_coordination": 1,   # single agent  # unverified
            "agent_identity": 2,             # ID + auth (Apple ecosystem)  # unverified
            "delegation_support": 1,         # manual  # unverified
            "tool_use_governance": 1,        # basic  # unverified
            "convergence_guarantees": 0,     # none  # unverified
        },
        "transparency": {
            "model_card": 3,                 # detailed + evals (AFM3 ML Research announcement)  # partially verified
            "system_card": 3,                # detailed + safety (PCC privacy architecture)  # partially verified
            "training_data_disclosure": 1,   # summary  # unverified
            "evaluation_disclosure": 2,      # internal + summary  # unverified
            "incident_reporting": 1,         # ad-hoc  # unverified
        },
        "open_weight_governance": {
            "license_clarity": None,         # closed weights
            "deployment_tools": None,
            "red_teaming": None,
            "community_governance": None,
        },
    },

    "samsung": {
        "governance_maturity": {
            "safety_framework_published": 0, # none  # unverified
            "framework_bindingness": 0,      # none
            "pause_commitment": 0,           # none
            "external_review": 0,            # none
            "academic_eval_score": 0,        # not evaluated
        },
        "runtime_governance": {
            "kill_switch": 0,               # none  # unverified
            "circuit_breaker": 0,            # none  # unverified
            "cost_governance": 0,            # none  # unverified
            "audit_logging": 1,              # basic logs  # unverified
            "output_validation": 1,          # basic filtering  # unverified
            "capability_fencing": 0,         # none  # unverified
        },
        "compliance_posture": {
            "eu_ai_act_gpai": 1,             # aware  # unverified
            "nist_ai_rmf": 0,                # none  # unverified
            "iso_42001": 0,                  # none  # unverified
            "soc2": 0,                       # none  # unverified
            "code_of_practice_signatory": 0, # not signed  # unverified
        },
        "agent_governance": {
            "multi_agent_coordination": 3,   # parallel (Galaxy AI multi-agent ecosystem: Gauss + Gemini + Perplexity)  # partially verified
            "agent_identity": 1,             # basic ID  # unverified
            "delegation_support": 1,         # manual  # unverified
            "tool_use_governance": 1,        # basic (Internal Agentic Builder)  # unverified
            "convergence_guarantees": 0,     # none  # unverified
        },
        "transparency": {
            "model_card": 2,                 # detailed (Gauss 2.3 documentation)  # partially verified
            "system_card": 1,                # basic  # unverified
            "training_data_disclosure": 1,   # summary  # unverified
            "evaluation_disclosure": 1,      # internal  # unverified
            "incident_reporting": 0,         # none  # unverified
        },
        "open_weight_governance": {
            "license_clarity": None,         # closed weights (proprietary)
            "deployment_tools": None,
            "red_teaming": None,
            "community_governance": None,
        },
    },

    "xiaomi": {
        "governance_maturity": {
            "safety_framework_published": 0, # none  # unverified
            "framework_bindingness": 0,      # none
            "pause_commitment": 0,           # none
            "external_review": 0,            # none
            "academic_eval_score": 0,        # not evaluated
        },
        "runtime_governance": {
            "kill_switch": 0,               # none  # unverified
            "circuit_breaker": 0,            # none  # unverified
            "cost_governance": 0,            # none  # unverified
            "audit_logging": 1,              # basic logs  # unverified
            "output_validation": 1,          # basic filtering  # unverified
            "capability_fencing": 0,         # none  # unverified
        },
        "compliance_posture": {
            "eu_ai_act_gpai": 1,             # aware  # unverified
            "nist_ai_rmf": 0,                # none  # unverified
            "iso_42001": 0,                  # none  # unverified
            "soc2": 0,                       # none  # unverified
            "code_of_practice_signatory": 0, # not signed  # unverified
        },
        "agent_governance": {
            "multi_agent_coordination": 1,   # single agent  # unverified
            "agent_identity": 1,             # basic ID  # unverified
            "delegation_support": 0,         # none  # unverified
            "tool_use_governance": 0,        # none  # unverified
            "convergence_guarantees": 0,     # none  # unverified
        },
        "transparency": {
            "model_card": 2,                 # detailed (MiMo V2.5-Pro announcement)  # partially verified
            "system_card": 1,                # basic  # unverified
            "training_data_disclosure": 1,   # summary  # unverified
            "evaluation_disclosure": 1,      # internal  # unverified
            "incident_reporting": 0,         # none  # unverified
        },
        "open_weight_governance": {
            "license_clarity": 2,            # standard OSI (permissive)  # unverified
            "deployment_tools": 2,           # API + docs (MiMo website)  # partially verified
            "red_teaming": 1,                # internal  # unverified
            "community_governance": 1,       # basic  # unverified
        },
    },

    # ======================================================================
    # Tier 5 — Niche / Research / Vertical (Labs 26-28)
    # ======================================================================

    "ant-group": {
        "governance_maturity": {
            "safety_framework_published": 0, # none  # unverified
            "framework_bindingness": 0,      # none
            "pause_commitment": 0,           # none
            "external_review": 0,            # none
            "academic_eval_score": 0,        # not evaluated
        },
        "runtime_governance": {
            "kill_switch": 0,               # none  # unverified
            "circuit_breaker": 0,            # none  # unverified
            "cost_governance": 0,            # none  # unverified
            "audit_logging": 1,              # basic logs  # unverified
            "output_validation": 1,          # basic filtering  # unverified
            "capability_fencing": 0,         # none  # unverified
        },
        "compliance_posture": {
            "eu_ai_act_gpai": 0,             # non-compliant (low EU exposure)  # unverified
            "nist_ai_rmf": 0,                # none  # unverified
            "iso_42001": 0,                  # none  # unverified
            "soc2": 0,                       # none  # unverified
            "code_of_practice_signatory": 0, # not signed  # unverified
        },
        "agent_governance": {
            "multi_agent_coordination": 1,   # single agent  # unverified
            "agent_identity": 1,             # basic ID  # unverified
            "delegation_support": 0,         # none  # unverified
            "tool_use_governance": 0,        # none  # unverified
            "convergence_guarantees": 0,     # none  # unverified
        },
        "transparency": {
            "model_card": 2,                 # detailed (Ring-mini-2.0 release blog)  # partially verified
            "system_card": 1,                # basic  # unverified
            "training_data_disclosure": 1,   # summary  # unverified
            "evaluation_disclosure": 1,      # internal  # unverified
            "incident_reporting": 0,         # none  # unverified
        },
        "open_weight_governance": {
            "license_clarity": 2,            # standard OSI  # unverified
            "deployment_tools": 2,           # API + docs (HuggingFace)  # partially verified
            "red_teaming": 1,                # internal  # unverified
            "community_governance": 1,       # basic  # unverified
        },
    },

    "reka": {
        "governance_maturity": {
            "safety_framework_published": 0, # none  # unverified
            "framework_bindingness": 0,      # none
            "pause_commitment": 0,           # none
            "external_review": 0,            # none
            "academic_eval_score": 0,        # not evaluated
        },
        "runtime_governance": {
            "kill_switch": 0,               # none  # unverified
            "circuit_breaker": 0,            # none  # unverified
            "cost_governance": 0,            # none  # unverified
            "audit_logging": 1,              # basic logs  # unverified
            "output_validation": 1,          # basic filtering  # unverified
            "capability_fencing": 1,         # basic sandbox  # unverified
        },
        "compliance_posture": {
            "eu_ai_act_gpai": 1,             # aware  # unverified
            "nist_ai_rmf": 0,                # none  # unverified
            "iso_42001": 0,                  # none  # unverified
            "soc2": 0,                       # none  # unverified
            "code_of_practice_signatory": 0, # not signed  # unverified
        },
        "agent_governance": {
            "multi_agent_coordination": 1,   # single agent  # unverified
            "agent_identity": 1,             # basic ID  # unverified
            "delegation_support": 0,         # none  # unverified
            "tool_use_governance": 1,        # basic  # unverified
            "convergence_guarantees": 0,     # none  # unverified
        },
        "transparency": {
            "model_card": 2,                 # detailed (Reka Core announcement)  # partially verified
            "system_card": 1,                # basic  # unverified
            "training_data_disclosure": 1,   # summary  # unverified
            "evaluation_disclosure": 2,      # internal + summary  # unverified
            "incident_reporting": 0,         # none  # unverified
        },
        "open_weight_governance": {
            "license_clarity": 1,            # ambiguous  # unverified
            "deployment_tools": 2,           # API + docs (Reka API)  # partially verified
            "red_teaming": 1,                # internal  # unverified
            "community_governance": 1,       # basic  # unverified
        },
    },

    "sakana": {
        "governance_maturity": {
            "safety_framework_published": 0, # none  # unverified
            "framework_bindingness": 0,      # none
            "pause_commitment": 0,           # none
            "external_review": 0,            # none
            "academic_eval_score": 0,        # not evaluated
        },
        "runtime_governance": {
            "kill_switch": 0,               # none  # unverified
            "circuit_breaker": 0,            # none  # unverified
            "cost_governance": 0,            # none  # unverified
            "audit_logging": 1,              # basic logs  # unverified
            "output_validation": 1,          # basic filtering  # unverified
            "capability_fencing": 1,         # basic sandbox  # unverified
        },
        "compliance_posture": {
            "eu_ai_act_gpai": 1,             # aware  # unverified
            "nist_ai_rmf": 0,                # none  # unverified
            "iso_42001": 0,                  # none  # unverified
            "soc2": 0,                       # none  # unverified
            "code_of_practice_signatory": 0, # not signed  # unverified
        },
        "agent_governance": {
            "multi_agent_coordination": 4,   # parallel + coordinated (Fugu orchestrates frontier models from multiple labs)  # partially verified
            "agent_identity": 2,             # ID + auth (orchestrator identifies worker models)  # unverified
            "delegation_support": 2,         # token-based (API-based orchestration)  # unverified
            "tool_use_governance": 2,        # permission-based (orchestrator controls tool use)  # unverified
            "convergence_guarantees": 2,     # timeout-based (Conductor RL-trained)  # unverified
        },
        "transparency": {
            "model_card": 3,                 # detailed + evals (Fugu technical report, ICLR 2026)  # partially verified
            "system_card": 2,                # detailed (Fugu technical report)  # partially verified
            "training_data_disclosure": 2,   # summary + sources (research paper)  # partially verified
            "evaluation_disclosure": 3,      # external evals (ICLR 2026 peer review)  # partially verified
            "incident_reporting": 0,         # none  # unverified
        },
        "open_weight_governance": {
            "license_clarity": None,         # not open-weight (API orchestrator)
            "deployment_tools": None,
            "red_teaming": None,
            "community_governance": None,
        },
    },
}


# ---------------------------------------------------------------------------
# LAB_METADATA — per-lab metadata for all 28 frontier labs
# ---------------------------------------------------------------------------

#: Type alias for lab metadata.
LabMetadata = Dict[str, object]

#: The full metadata database.
MetadataDB = Dict[str, LabMetadata]

LAB_METADATA: MetadataDB = {
    "anthropic": {
        "name": "Anthropic",
        "hq": "San Francisco, US",
        "founded": 2021,
        "valuation": "$965B",
        "flagship_model": "Claude Fable 5 / Opus 4.8",
        "weights": "closed",
        "safety_framework": "RSP v3.4",
        "fmf_member": True,
        "frontier_index": 98.7,
        "api_available": True,
        "api_provider": "anthropic",
    },
    "google-deepmind": {
        "name": "Google DeepMind",
        "hq": "London / Mountain View",
        "founded": 2010,
        "valuation": "subsidiary (Alphabet ~$4.4T)",
        "flagship_model": "Gemini 3.7 Flash",
        "weights": "mixed",
        "safety_framework": "Frontier Safety Framework v3.1",
        "fmf_member": True,
        "frontier_index": 89.2,
        "api_available": True,
        "api_provider": "google",
    },
    "openai": {
        "name": "OpenAI",
        "hq": "San Francisco, US",
        "founded": 2015,
        "valuation": "$852B",
        "flagship_model": "GPT-5.6 Sol / Terra / Luna",
        "weights": "closed",
        "safety_framework": "Preparedness Framework v2",
        "fmf_member": True,
        "frontier_index": 85.6,
        "api_available": True,
        "api_provider": "openai",
    },
    "meta-msl": {
        "name": "Meta Superintelligence Labs",
        "hq": "Menlo Park, US",
        "founded": 2013,
        "valuation": "subsidiary (Meta ~$1.4T+)",
        "flagship_model": "Muse Spark 1.2 / Llama 4",
        "weights": "mixed",
        "safety_framework": "Responsible Use Guide + system cards",
        "fmf_member": True,
        "frontier_index": 0.0,
        "api_available": True,
        "api_provider": "meta",
    },
    "xai": {
        "name": "xAI",
        "hq": "Austin, US",
        "founded": 2023,
        "valuation": "$250B",
        "flagship_model": "Grok 4.5",
        "weights": "closed",
        "safety_framework": "Frontier AI Framework (draft)",
        "fmf_member": False,
        "frontier_index": 0.0,
        "api_available": True,
        "api_provider": "xai",
    },
    "microsoft-ai": {
        "name": "Microsoft AI",
        "hq": "Redmond, US",
        "founded": 2024,
        "valuation": "subsidiary (Microsoft ~$4T+)",
        "flagship_model": "MAI-Thinking-1 / MAI-Code-1-Flash",
        "weights": "mixed",
        "safety_framework": "Responsible AI Standard (rev. 2022)",
        "fmf_member": True,
        "frontier_index": 0.0,
        "api_available": True,
        "api_provider": "microsoft",
    },
    "alibaba-qwen": {
        "name": "Alibaba Qwen",
        "hq": "Hangzhou, China",
        "founded": 2023,
        "valuation": "subsidiary (Alibaba ~$300B+)",
        "flagship_model": "Qwen3.8-Max (2.4T, 95B active)",
        "weights": "mixed",
        "safety_framework": "None published",
        "fmf_member": False,
        "frontier_index": 81.2,
        "api_available": True,
        "api_provider": "alibaba",
    },
    "zai-zhipu": {
        "name": "Z.ai / Zhipu",
        "hq": "Beijing, China",
        "founded": 2019,
        "valuation": "~$62B",
        "flagship_model": "GLM-5.3-Flash (320B)",
        "weights": "open",
        "safety_framework": "None published",
        "fmf_member": False,
        "frontier_index": 77.1,
        "api_available": True,
        "api_provider": "zhipu",
    },
    "deepseek": {
        "name": "DeepSeek",
        "hq": "Hangzhou, China",
        "founded": 2023,
        "valuation": "~$52B",
        "flagship_model": "V4-Pro (1.6T, 49B active)",
        "weights": "open",
        "safety_framework": "None published",
        "fmf_member": False,
        "frontier_index": 69.5,
        "api_available": True,
        "api_provider": "deepseek",
    },
    "minimax": {
        "name": "MiniMax",
        "hq": "Beijing, China",
        "founded": 2021,
        "valuation": "HKEX-listed",
        "flagship_model": "M3 (428B, 23B active)",
        "weights": "open",
        "safety_framework": "None published",
        "fmf_member": False,
        "frontier_index": 67.9,
        "api_available": True,
        "api_provider": "minimax",
    },
    "moonshot": {
        "name": "Moonshot AI (Kimi)",
        "hq": "Beijing, China",
        "founded": 2023,
        "valuation": "~$20B",
        "flagship_model": "Kimi K3 (2.8T, 104B active)",
        "weights": "open",
        "safety_framework": "None published",
        "fmf_member": False,
        "frontier_index": 65.4,
        "api_available": True,
        "api_provider": "moonshot",
    },
    "bytedance": {
        "name": "ByteDance Seed",
        "hq": "Beijing, China",
        "founded": 2023,
        "valuation": "subsidiary",
        "flagship_model": "Doubao Seed 2.0 Pro",
        "weights": "mixed",
        "safety_framework": "None published",
        "fmf_member": False,
        "frontier_index": 58.8,
        "api_available": True,
        "api_provider": "bytedance",
    },
    "tencent": {
        "name": "Tencent Hunyuan",
        "hq": "Shenzhen, China",
        "founded": 2023,
        "valuation": "subsidiary",
        "flagship_model": "Hy3 (295B, 21B active)",
        "weights": "open",
        "safety_framework": "None published",
        "fmf_member": False,
        "frontier_index": 35.0,
        "api_available": True,
        "api_provider": "tencent",
    },
    "mistral": {
        "name": "Mistral AI",
        "hq": "Paris, France",
        "founded": 2023,
        "valuation": "N/D",  # unverified
        "flagship_model": "Mistral Large 3 + Codestral",
        "weights": "mixed",
        "safety_framework": "None published",
        "fmf_member": False,
        "frontier_index": 0.0,
        "api_available": True,
        "api_provider": "mistral",
    },
    "cohere": {
        "name": "Cohere",
        "hq": "Toronto, Canada",
        "founded": 2019,
        "valuation": "N/D",  # unverified
        "flagship_model": "Command A+ (218B MoE, 25B active)",
        "weights": "open",
        "safety_framework": "Secure AI Frontier Model Framework",
        "fmf_member": False,
        "frontier_index": 0.0,
        "api_available": True,
        "api_provider": "cohere",
    },
    "ssi": {
        "name": "Safe Superintelligence",
        "hq": "Palo Alto / Tel Aviv, US",
        "founded": 2024,
        "valuation": "$5B+ (NVIDIA investment)",
        "flagship_model": "None public",
        "weights": "closed",
        "safety_framework": "None published",
        "fmf_member": False,
        "frontier_index": 0.0,
        "api_available": False,
        "api_provider": "",
    },
    "baidu": {
        "name": "Baidu ERNIE",
        "hq": "Beijing, China",
        "founded": 2023,
        "valuation": "subsidiary",
        "flagship_model": "ERNIE 5.1",
        "weights": "mixed",
        "safety_framework": "None published",
        "fmf_member": False,
        "frontier_index": 0.0,
        "api_available": True,
        "api_provider": "baidu",
    },
    "huawei": {
        "name": "Huawei Pangu",
        "hq": "Shenzhen, China",
        "founded": 2017,
        "valuation": "subsidiary",
        "flagship_model": "Pangu Ultra MoE (718B)",
        "weights": "open",
        "safety_framework": "None published",
        "fmf_member": False,
        "frontier_index": 0.0,
        "api_available": True,
        "api_provider": "huawei",
    },
    "amazon-aws": {
        "name": "Amazon AWS AI",
        "hq": "Seattle, US",
        "founded": 2024,
        "valuation": "subsidiary (Amazon)",
        "flagship_model": "Nova 2 Omni",
        "weights": "closed",
        "safety_framework": "Frontier Model Safety Framework",
        "fmf_member": True,
        "frontier_index": 0.0,
        "api_available": True,
        "api_provider": "aws-bedrock",
    },
    "tml": {
        "name": "Thinking Machines Lab",
        "hq": "San Francisco, US",
        "founded": 2025,
        "valuation": "$12B",
        "flagship_model": "Inkling (975B, open)",
        "weights": "open",
        "safety_framework": "None published",
        "fmf_member": False,
        "frontier_index": 0.0,
        "api_available": True,
        "api_provider": "thinking-machines",
    },
    "nvidia": {
        "name": "Nvidia",
        "hq": "Santa Clara, US",
        "founded": 1993,
        "valuation": "~$4T market cap",
        "flagship_model": "Nemotron 3 Ultra (550B, 55B active)",
        "weights": "open",
        "safety_framework": "Frontier AI Risk Assessment",
        "fmf_member": False,
        "frontier_index": 34.9,
        "api_available": True,
        "api_provider": "nvidia",
    },
    "lg-ai": {
        "name": "LG AI Research",
        "hq": "Seoul, Korea",
        "founded": 2020,
        "valuation": "subsidiary (LG)",
        "flagship_model": "EXAONE 4.5 (33B)",
        "weights": "closed",
        "safety_framework": "None published",
        "fmf_member": False,
        "frontier_index": 36.9,
        "api_available": False,
        "api_provider": "",
    },
    "apple": {
        "name": "Apple",
        "hq": "Cupertino, US",
        "founded": 2017,
        "valuation": "subsidiary (Apple)",
        "flagship_model": "AFM 3 Cloud Pro / AFM 3 Core Advanced",
        "weights": "closed",
        "safety_framework": "None published",
        "fmf_member": False,
        "frontier_index": 0.0,
        "api_available": True,
        "api_provider": "apple",
    },
    "samsung": {
        "name": "Samsung",
        "hq": "Suwon, Korea",
        "founded": 2023,
        "valuation": "subsidiary (Samsung)",
        "flagship_model": "Gauss 2.3 / Gauss 2.3 Think",
        "weights": "closed",
        "safety_framework": "None published",
        "fmf_member": False,
        "frontier_index": 0.0,
        "api_available": False,
        "api_provider": "",
    },
    "xiaomi": {
        "name": "Xiaomi",
        "hq": "Beijing, China",
        "founded": 2010,
        "valuation": "subsidiary (Xiaomi)",
        "flagship_model": "MiMo V2.5-Pro (1.02T, 42B active)",
        "weights": "open",
        "safety_framework": "None published",
        "fmf_member": False,
        "frontier_index": 0.0,
        "api_available": True,
        "api_provider": "xiaomi",
    },
    "ant-group": {
        "name": "Ant Group",
        "hq": "Hangzhou, China",
        "founded": 2014,
        "valuation": "subsidiary (Ant Group)",
        "flagship_model": "Ring-2.6-1T",
        "weights": "open",
        "safety_framework": "None published",
        "fmf_member": False,
        "frontier_index": 0.0,
        "api_available": True,
        "api_provider": "ant",
    },
    "reka": {
        "name": "Reka AI",
        "hq": "Sunnyvale, US",
        "founded": 2022,
        "valuation": "$170M funding",
        "flagship_model": "Reka Flash 3.1 / Reka Core",
        "weights": "mixed",
        "safety_framework": "None published",
        "fmf_member": False,
        "frontier_index": 0.0,
        "api_available": True,
        "api_provider": "reka",
    },
    "sakana": {
        "name": "Sakana AI",
        "hq": "Tokyo, Japan",
        "founded": 2023,
        "valuation": "$372.8M funding",
        "flagship_model": "Sakana Fugu / Fugu-Ultra",
        "weights": "closed",
        "safety_framework": "None published",
        "fmf_member": False,
        "frontier_index": 0.0,
        "api_available": True,
        "api_provider": "sakana",
    },
}


# ---------------------------------------------------------------------------
# Convenience helpers
# ---------------------------------------------------------------------------

#: The six evaluation dimension names, in canonical order.
DIMENSION_NAMES: tuple[str, ...] = (
    "governance_maturity",
    "runtime_governance",
    "compliance_posture",
    "agent_governance",
    "transparency",
    "open_weight_governance",
)

#: Criterion names per dimension.
DIMENSION_CRITERIA: dict[str, tuple[str, ...]] = {
    "governance_maturity": (
        "safety_framework_published",
        "framework_bindingness",
        "pause_commitment",
        "external_review",
        "academic_eval_score",
    ),
    "runtime_governance": (
        "kill_switch",
        "circuit_breaker",
        "cost_governance",
        "audit_logging",
        "output_validation",
        "capability_fencing",
    ),
    "compliance_posture": (
        "eu_ai_act_gpai",
        "nist_ai_rmf",
        "iso_42001",
        "soc2",
        "code_of_practice_signatory",
    ),
    "agent_governance": (
        "multi_agent_coordination",
        "agent_identity",
        "delegation_support",
        "tool_use_governance",
        "convergence_guarantees",
    ),
    "transparency": (
        "model_card",
        "system_card",
        "training_data_disclosure",
        "evaluation_disclosure",
        "incident_reporting",
    ),
    "open_weight_governance": (
        "license_clarity",
        "deployment_tools",
        "red_teaming",
        "community_governance",
    ),
}


def list_lab_slugs() -> list[str]:
    """Return all 28 lab slugs in compendium order."""
    return list(LAB_METADATA.keys())


def get_score(lab_slug: str, dimension: str, criterion: str) -> Score:
    """Look up a single score by lab, dimension, and criterion.

    Returns ``None`` for N/A criteria (open-weight governance on
    closed-weight labs).  Raises ``KeyError`` if any key is unknown.
    """
    return LAB_SCORECARDS[lab_slug][dimension][criterion]


def get_dimension_scores(lab_slug: str, dimension: str) -> DimensionScores:
    """Return all criterion scores for one dimension of one lab."""
    return LAB_SCORECARDS[lab_slug][dimension]


def get_lab_scorecard(lab_slug: str) -> LabScorecard:
    """Return the full scorecard (all dimensions) for one lab."""
    return LAB_SCORECARDS[lab_slug]


def get_lab_metadata(lab_slug: str) -> LabMetadata:
    """Return metadata for one lab."""
    return LAB_METADATA[lab_slug]


def compute_dimension_average(
    lab_slug: str, dimension: str
) -> Optional[float]:
    """Compute the average score for a dimension, ignoring ``None`` values.

    Returns ``None`` if all criteria are ``None`` (e.g. open-weight
    governance for a closed-weight lab).
    """
    scores = LAB_SCORECARDS[lab_slug][dimension].values()
    numeric = [s for s in scores if s is not None]
    if not numeric:
        return None
    return sum(numeric) / len(numeric)


def compute_lab_average(lab_slug: str) -> Optional[float]:
    """Compute the overall average score across all non-N/A dimensions.

    Each dimension contributes equally (dimension averages are averaged).
    Dimensions where all criteria are ``None`` are excluded.
    """
    dimension_avgs = [
        compute_dimension_average(lab_slug, dim)
        for dim in DIMENSION_NAMES
    ]
    numeric = [a for a in dimension_avgs if a is not None]
    if not numeric:
        return None
    return sum(numeric) / len(numeric)
