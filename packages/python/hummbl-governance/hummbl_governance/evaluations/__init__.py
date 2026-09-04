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
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# SPDX-License-Identifier: Apache-2.0

"""HUMMBL Model Evaluation Framework.

Benchmarks, evaluations, and tests for AI models and tools, establishing
HUMMBL's own standards for model selection and deployment governance.

Eight evaluation dimensions:

1. **Governance Maturity** — safety framework, bindingness, pause commitment,
   external review, academic eval score (rubric-based)
2. **Runtime Governance** — kill switch, circuit breaker, cost governor,
   audit logging, output validation, capability fencing (rubric + API-probe)
3. **Compliance Posture** — EU AI Act, NIST AI RMF, ISO 42001, SOC 2,
   Code of Practice (rubric-based)
4. **Agent Governance** — multi-agent coordination, identity, delegation,
   tool use, convergence (rubric + API-testable)
5. **Transparency** — model card, system card, training data, evals,
   incident reporting (rubric-based)
6. **Open-Weight Governance** — license, deployment tools, red teaming,
   community governance (rubric-based, conditional)
7. **Safety Behaviors** — harmful request refusal, self-limitation,
   provenance, hallucination, instruction following (API-runnable)
8. **Agent Capability** — tool use, multi-step reasoning, code generation,
   long-context, self-correction (API-runnable)

Usage:
    from hummbl_governance.evaluations import (
        EvaluationFramework,
        ScorecardGenerator,
        ModelRegistry,
        APITestSuite,
    )

    registry = ModelRegistry()
    framework = EvaluationFramework()
    generator = ScorecardGenerator(framework, registry)

    # Generate scorecard for a single lab
    scorecard = generator.generate("anthropic")
    print(scorecard.to_json())

    # Generate scorecards for all labs
    scorecards = generator.generate_all()
    print(len(scorecards))

    # Run API tests (requires API keys)
    suite = APITestSuite()
    results = suite.run_lab("openai", api_key="sk-...")
    print(results.summary())

Standard library only.
"""

from hummbl_governance.evaluations.model_registry import (
    ModelRegistry,
    LabInfo,
    list_labs,
    get_lab,
)
from hummbl_governance.evaluations.framework import (
    EvaluationFramework,
    Dimension,
    Criterion,
    DimensionResult,
    ScorecardResult,
    ScoreLevel,
)
from hummbl_governance.evaluations.rubrics import (
    GOVERNANCE_MATURITY,
    RUNTIME_GOVERNANCE,
    COMPLIANCE_POSTURE,
    AGENT_GOVERNANCE,
    TRANSPARENCY,
    OPEN_WEIGHT_GOVERNANCE,
    SAFETY_BEHAVIORS,
    AGENT_CAPABILITY,
    ALL_DIMENSIONS,
)
from hummbl_governance.evaluations.scorecard import (
    ScorecardGenerator,
    Scorecard,
)
from hummbl_governance.evaluations.api_tests import (
    APITestSuite,
    APITestResult,
    TestStatus,
)
from hummbl_governance.evaluations.lab_monitor import (
    LabMonitor,
    LabEvent,
    LabSnapshot,
    Alert,
    EventTimeline,
    EventType,
    AlertLevel,
    AlertCategory,
    create_seeded_monitor,
)

__all__ = [
    # Model registry
    "ModelRegistry",
    "LabInfo",
    "list_labs",
    "get_lab",
    # Framework
    "EvaluationFramework",
    "Dimension",
    "Criterion",
    "DimensionResult",
    "ScorecardResult",
    "ScoreLevel",
    # Rubrics
    "GOVERNANCE_MATURITY",
    "RUNTIME_GOVERNANCE",
    "COMPLIANCE_POSTURE",
    "AGENT_GOVERNANCE",
    "TRANSPARENCY",
    "OPEN_WEIGHT_GOVERNANCE",
    "SAFETY_BEHAVIORS",
    "AGENT_CAPABILITY",
    "ALL_DIMENSIONS",
    # Scorecard
    "ScorecardGenerator",
    "Scorecard",
    # API tests
    "APITestSuite",
    "APITestResult",
    "TestStatus",
    # Lab monitor
    "LabMonitor",
    "LabEvent",
    "LabSnapshot",
    "Alert",
    "EventTimeline",
    "EventType",
    "AlertLevel",
    "AlertCategory",
    "create_seeded_monitor",
]
