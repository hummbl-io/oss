"""Governance simulation prototype.

This is a Stage 1 rule-based simulator. It is deliberately scoped as a
*prototype for hummbl-governance*: the package has no external dependencies
beyond the Python standard library, the public API mirrors hummbl-governance
conventions, and the layout is designed for mechanical migration once Stage 2
(validation, sensitivity analysis, uncertainty quantification) is in place.

See:
* ``adrs/ADR-003-governance-simulation-mvp.md`` — scope / architecture record.
* ``research_notes/2026-04-10-simulation-mvp-design.md`` — staged roadmap,
  validation gap, and known limitations.
"""

from .core import (
    AgentConfig,
    AgentState,
    ContractConfig,
    Environment,
    LLMAdapter,
    Scenario,
    ScheduledAction,
    SimulationClock,
    trace_summary,
)
from .events import (
    contract_event,
    dct_event,
    dctx_event,
    evidence_event,
    system_event,
)
from .scenarios import gemini_probation_scenario
from .trust import ProbationPolicy, TrustModel

__all__ = [
    "AgentConfig",
    "AgentState",
    "ContractConfig",
    "Environment",
    "LLMAdapter",
    "ProbationPolicy",
    "Scenario",
    "ScheduledAction",
    "SimulationClock",
    "TrustModel",
    "contract_event",
    "dct_event",
    "dctx_event",
    "evidence_event",
    "gemini_probation_scenario",
    "system_event",
    "trace_summary",
]
