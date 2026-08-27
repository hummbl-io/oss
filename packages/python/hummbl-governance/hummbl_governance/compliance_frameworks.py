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

"""Declarative compliance framework registry.

Each framework is defined as data (a ``FrameworkSpec``), not as a hardcoded
method. Adding a new framework requires only a new ``register_framework``
call -- no engine changes, no CLI changes (the CLI auto-discovers from the
registry).

Architecture
------------
- ``MappingRule``  -- one rule: which tuple types match, optional signed /
  state filters, which fields to extract, optional derive callable.
- ``ControlSpec``  -- a control id + description + one or more rules.
- ``FrameworkSpec``-- a framework slug, display name, reference, default
  window, and an ordered tuple of controls.
- ``register_framework`` / ``get_framework`` / ``list_frameworks`` -- the
  registry.  External packages can register additional frameworks at import
  time via ``register_framework(MySpec)``.

Standard library only.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable


# ---------------------------------------------------------------------------
# Rule / control / framework dataclasses
# ---------------------------------------------------------------------------

DeriveFn = Callable[[dict, dict], dict]


@dataclass(frozen=True)
class MappingRule:
    """One rule mapping governance entries to a control's evidence list.

    A rule matches an entry when ALL of its filters pass:
    - ``tuple_types`` (if non-empty): entry's ``tuple_type`` is in the set
    - ``require_signed``: entry has a truthy ``signature``
    - ``states`` (if not None): ``tuple_data["state"]`` is in the set

    On match, evidence is built from the base evidence dict plus:
    - ``extract``: copy ``tuple_data[key]`` into evidence (always set, None
      if missing -- matches the legacy ``.get()`` behaviour)
    - ``extract_fallback``: first truthy value among the candidate keys
      (matches the legacy ``.get(a) or .get(b)`` pattern)
    - ``derive``: optional callable ``(entry, tuple_data) -> dict`` for
      computed fields (e.g. ``human_initiated``)
    """

    tuple_types: tuple[str, ...] = ()
    require_signed: bool = False
    states: tuple[str, ...] | None = None
    extract: tuple[tuple[str, str], ...] = ()
    extract_fallback: tuple[tuple[str, tuple[str, ...]], ...] = ()
    derive: DeriveFn | None = field(default=None, repr=False)


@dataclass(frozen=True)
class ControlSpec:
    """A single control within a framework."""

    id: str
    description: str
    rules: tuple[MappingRule, ...] = ()


@dataclass(frozen=True)
class FrameworkSpec:
    """A full compliance framework definition."""

    id: str  # CLI slug, e.g. "eu-ai-act"
    name: str  # report.framework field, e.g. "EU_AI_ACT"
    reference: str  # human-readable citation
    default_days: int = 30
    controls: tuple[ControlSpec, ...] = ()

    @property
    def control_ids(self) -> tuple[str, ...]:
        return tuple(c.id for c in self.controls)


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

_FRAMEWORK_REGISTRY: dict[str, FrameworkSpec] = {}


def register_framework(spec: FrameworkSpec) -> FrameworkSpec:
    """Register a framework spec.  Overwrites on id collision."""
    _FRAMEWORK_REGISTRY[spec.id] = spec
    return spec


def get_framework(framework_id: str) -> FrameworkSpec:
    """Look up a framework by its CLI slug."""
    try:
        return _FRAMEWORK_REGISTRY[framework_id]
    except KeyError:
        available = ", ".join(sorted(_FRAMEWORK_REGISTRY))
        raise KeyError(
            f"Unknown framework {framework_id!r}. Available: {available}"
        ) from None


def list_frameworks() -> list[str]:
    """Return sorted list of registered framework ids."""
    return sorted(_FRAMEWORK_REGISTRY)


def framework_count() -> int:
    """Return the number of registered frameworks."""
    return len(_FRAMEWORK_REGISTRY)


# ---------------------------------------------------------------------------
# Helper rule constructors (keep framework definitions concise)
# ---------------------------------------------------------------------------

def _rule(
    *tuple_types: str,
    signed: bool = False,
    states: tuple[str, ...] | None = None,
    extract: tuple[tuple[str, str], ...] = (),
    fallback: tuple[tuple[str, tuple[str, ...]], ...] = (),
    derive: DeriveFn | None = None,
) -> MappingRule:
    """Shorthand for MappingRule construction."""
    return MappingRule(
        tuple_types=tuple_types,
        require_signed=signed,
        states=states,
        extract=extract,
        extract_fallback=fallback,
        derive=derive,
    )


# ---------------------------------------------------------------------------
# Framework definitions
# ---------------------------------------------------------------------------

# --- SOC 2 (AICPA Trust Service Criteria) ----------------------------------

register_framework(FrameworkSpec(
    id="soc2",
    name="SOC2",
    reference="AICPA SOC 2 Trust Service Criteria (CC6, CC7).",
    default_days=7,
    controls=(
        ControlSpec("CC6.1", "Logical access security", (
            _rule("DCT", extract=(
                ("issuer", "issuer"),
                ("subject", "subject"),
                ("resources", "resource_selectors"),
                ("ops", "ops_allowed"),
            )),
        )),
        ControlSpec("CC7.2", "Monitoring and logging", (
            _rule(signed=True),
        )),
        ControlSpec("CC6.3", "Identity and authentication", (
            _rule("DCT", extract=(
                ("subject", "subject"),
                ("issuer", "issuer"),
            )),
        )),
    ),
))


# --- GDPR (Regulation (EU) 2016/679) ---------------------------------------

register_framework(FrameworkSpec(
    id="gdpr",
    name="GDPR",
    reference="Regulation (EU) 2016/679 (GDPR), Articles 5, 6, 25, 28, 30, 32.",
    default_days=30,
    controls=(
        ControlSpec("Art.5", "Principles -- lawfulness, fairness, transparency", (
            _rule("INTENT", extract=(("objective", "objective"), ("agent", "agent"))),
        )),
        ControlSpec("Art.6", "Lawfulness of processing", (
            _rule("CONTRACT", extract=(("issuer", "issuer"), ("operations", "operations"))),
        )),
        ControlSpec("Art.25", "Data protection by design and by default", (
            _rule("DCT", extract=(
                ("ops_allowed", "ops_allowed"),
                ("resources", "resource_selectors"),
            )),
            _rule("CAPABILITY_FENCE", extract=(("action", "action"),)),
        )),
        ControlSpec("Art.28", "Processor obligations", (
            _rule("DCTX", extract=(
                ("delegator", "delegator"),
                ("delegatee", "delegatee"),
            )),
        )),
        ControlSpec("Art.30", "Records of processing activities", (
            _rule("DCTX", "CONTRACT", "ATTEST", "EVIDENCE", extract=(
                ("delegator", "delegator"),
                ("delegatee", "delegatee"),
                ("event", "event"),
            )),
        )),
        ControlSpec("Art.32", "Security of processing", (
            _rule(signed=True),
        )),
    ),
))


# --- OWASP Agentic Security Initiative Top 10 -----------------------------

register_framework(FrameworkSpec(
    id="owasp",
    name="OWASP_AGENTIC",
    reference="OWASP Agentic Security Initiative Top 10 (ASI01-ASI10).",
    default_days=7,
    controls=(
        ControlSpec("ASI01", "Agent goal hijack", (
            _rule("INTENT", extract=(
                ("agent", "agent"),
                ("objective", "objective"),
                ("phase", "phase"),
            )),
        )),
        ControlSpec("ASI02", "Tool misuse (code audit)", ()),
        ControlSpec("ASI03", "Identity and privilege abuse", (
            _rule("DCT", extract=(
                ("issuer", "issuer"),
                ("subject", "subject"),
                ("resources", "resource_selectors"),
                ("ops", "ops_allowed"),
            )),
        )),
        ControlSpec("ASI04", "Supply chain vulnerabilities", (
            _rule(signed=True),
        )),
        ControlSpec("ASI05", "Unexpected code execution (code audit)", ()),
        ControlSpec("ASI06", "Memory and context poisoning (code audit)", ()),
        ControlSpec("ASI07", "Insecure inter-agent communication", (
            _rule("DCTX", extract=(
                ("delegator", "delegator"),
                ("delegatee", "delegatee"),
                ("event", "event"),
            )),
        )),
        ControlSpec("ASI08", "Cascading failures", (
            _rule("CIRCUIT_BREAKER", "KILLSWITCH", extract=(
                ("state", "state"),
                ("adapter", "adapter"),
            )),
        )),
        ControlSpec("ASI09", "Human-agent trust exploitation (code audit)", ()),
        ControlSpec("ASI10", "Rogue agents (code audit)", ()),
    ),
))


# --- NIST AI RMF 1.0 (AI 100-1) -------------------------------------------

register_framework(FrameworkSpec(
    id="nist-rmf",
    name="NIST_AI_RMF",
    reference="NIST AI 100-1 (2023), AI RMF Playbook.",
    default_days=30,
    controls=(
        ControlSpec("GOVERN-1.1", "AI risk management policies", (
            _rule("INTENT", extract=(
                ("agent", "agent"),
                ("objective", "objective"),
                ("phase", "phase"),
            )),
        )),
        ControlSpec("GOVERN-1.7", "Processes for risk identification", (
            _rule("CIRCUIT_BREAKER", "KILLSWITCH", extract=(
                ("state", "state"),
                ("adapter", "adapter"),
            )),
        )),
        ControlSpec("MAP-1.1", "Organisational context", (
            _rule("CONTRACT", "DCTX", "DCT", fallback=(
                ("delegator", ("delegator", "issuer")),
                ("delegatee", ("delegatee", "subject")),
            )),
        )),
        ControlSpec("MAP-2.2", "Scientific basis for risk assessment", (
            _rule("ATTEST", "EVIDENCE", extract=(
                ("claim", "claim"),
                ("outcome", "outcome"),
            )),
        )),
        ControlSpec("MEASURE-2.5", "Trustworthiness evaluations", (
            _rule(signed=True),
        )),
        ControlSpec("MEASURE-2.8", "Impact metrics logged", (
            _rule("COST_GOVERNOR", extract=(
                ("agent", "agent"),
                ("decision", "decision"),
                ("spend", "spend"),
                ("budget", "budget"),
            )),
        )),
        ControlSpec("MANAGE-1.3", "Response plans executed", (
            _rule("KILLSWITCH", extract=(("state", "state"), ("adapter", "adapter"))),
        )),
        ControlSpec("MANAGE-2.4", "Risk treatment applied", (
            _rule("CIRCUIT_BREAKER", extract=(("state", "state"), ("adapter", "adapter"))),
        )),
    ),
))


# --- EU AI Act (Regulation (EU) 2024/1689) ---------------------------------

_HUMAN_OVERSIGHT_STATES = ("HALT_ALL", "EMERGENCY")


def _derive_human_initiated(_entry: dict, td: dict) -> dict:
    return {"human_initiated": td.get("state", "") in _HUMAN_OVERSIGHT_STATES}


def _derive_auto_generated(_entry: dict, _td: dict) -> dict:
    return {"auto_generated": True}


register_framework(FrameworkSpec(
    id="eu-ai-act",
    name="EU_AI_ACT",
    reference="Regulation (EU) 2024/1689 (AI Act), Annex III high-risk obligations.",
    default_days=30,
    controls=(
        ControlSpec("Art.9", "Risk management system", (
            _rule("CIRCUIT_BREAKER", "KILLSWITCH", extract=(
                ("state", "state"),
                ("adapter", "adapter"),
            )),
        )),
        ControlSpec("Art.10", "Data and data governance", (
            _rule("ATTEST", "EVIDENCE", extract=(
                ("claim", "claim"),
                ("outcome", "outcome"),
            )),
        )),
        ControlSpec("Art.11", "Technical documentation", (
            _rule("CONTRACT", "ATTEST"),
        )),
        ControlSpec("Art.12", "Record-keeping and logging", (
            _rule(signed=True),
        )),
        ControlSpec("Art.13", "Transparency and information provision", (
            _rule("INTENT", extract=(
                ("agent", "agent"),
                ("objective", "objective"),
                ("phase", "phase"),
            )),
        )),
        ControlSpec("Art.14", "Human oversight", (
            _rule("KILLSWITCH", extract=(("state", "state"),), derive=_derive_human_initiated),
        )),
        ControlSpec("Art.15", "Accuracy, robustness, cybersecurity", (
            _rule("CIRCUIT_BREAKER", "KILLSWITCH", extract=(("state", "state"),)),
        )),
        ControlSpec("Art.16", "Obligations of providers", (
            _rule("DCTX"),
            _rule(signed=True),
        )),
        ControlSpec("Art.17", "Quality management system", (
            _rule("DCTX", extract=(
                ("delegator", "delegator"),
                ("delegatee", "delegatee"),
                ("event", "event"),
            )),
        )),
        ControlSpec("Art.19", "Automatically generated logs", (
            _rule(signed=True, derive=_derive_auto_generated),
        )),
    ),
))


# --- ISO/IEC 27001:2022 (Annex A) -----------------------------------------

register_framework(FrameworkSpec(
    id="iso27001",
    name="ISO27001",
    reference="ISO/IEC 27001:2022, Annex A (A.5-A.9, A.12).",
    default_days=30,
    controls=(
        ControlSpec("A.5", "Information security policies", (
            _rule("INTENT", extract=(("agent", "agent"), ("objective", "objective"))),
        )),
        ControlSpec("A.6", "Organization of information security", (
            _rule("DCTX", extract=(
                ("delegator", "delegator"),
                ("delegatee", "delegatee"),
                ("event", "event"),
            )),
        )),
        ControlSpec("A.7", "Human resource security", (
            _rule("DCT", "CONTRACT", extract=(
                ("issuer", "issuer"),
                ("subject", "subject"),
                ("ops", "ops_allowed"),
            )),
        )),
        ControlSpec("A.8", "Asset management", (
            _rule("DCT", "ATTEST", fallback=(
                ("resources", ("resource_selectors", "resources")),
            )),
        )),
        ControlSpec("A.9", "Access control", (
            _rule("DCT", extract=(
                ("issuer", "issuer"),
                ("subject", "subject"),
                ("ops_allowed", "ops_allowed"),
                ("resources", "resource_selectors"),
            )),
        )),
        ControlSpec("A.12", "Operations security -- logging", (
            _rule(signed=True),
        )),
    ),
))


# --- ISO/IEC 42001:2023 (Annex A) -----------------------------------------

register_framework(FrameworkSpec(
    id="iso42001",
    name="ISO42001",
    reference="ISO/IEC 42001:2023, Annex A (A.2-A.10).",
    default_days=30,
    controls=(
        ControlSpec("A.2", "Policies related to AI", (
            _rule("INTENT", extract=(("agent", "agent"), ("objective", "objective"))),
        )),
        ControlSpec("A.3", "Internal organization", (
            _rule("DCTX", extract=(
                ("delegator", "delegator"),
                ("delegatee", "delegatee"),
                ("event", "event"),
            )),
        )),
        ControlSpec("A.4", "Resources for AI systems", (
            _rule("DCT", "ATTEST", fallback=(
                ("resources", ("resource_selectors", "resources")),
            )),
        )),
        ControlSpec("A.5", "Assessing impacts of AI systems", (
            _rule("ATTEST", extract=(("subject", "subject"), ("claim", "claim"))),
        )),
        ControlSpec("A.6", "AI system life cycle", (
            _rule("CONTRACT", extract=(
                ("issuer", "issuer"),
                ("subject", "subject"),
                ("ops", "ops_allowed"),
            )),
        )),
        ControlSpec("A.7", "Data for AI systems", (
            _rule("DCT", extract=(
                ("resources", "resource_selectors"),
                ("ops_allowed", "ops_allowed"),
            )),
        )),
        ControlSpec("A.8", "Information for interested parties", (
            _rule(signed=True),
        )),
        ControlSpec("A.9", "Use of AI systems", (
            _rule("DCT", extract=(
                ("issuer", "issuer"),
                ("subject", "subject"),
                ("ops_allowed", "ops_allowed"),
            )),
        )),
        ControlSpec("A.10", "Third-party and customer relationships", (
            _rule("DCTX", extract=(
                ("delegator", "delegator"),
                ("delegatee", "delegatee"),
            )),
        )),
    ),
))


# --- NIST CSF 2.0 ----------------------------------------------------------

register_framework(FrameworkSpec(
    id="nist-csf",
    name="NIST_CSF",
    reference="NIST Cybersecurity Framework 2.0 (2024).",
    default_days=30,
    controls=(
        ControlSpec("GOVERN", "Organizational context and risk strategy", (
            _rule("INTENT", extract=(("objective", "objective"),)),
            _rule("DCTX", extract=(("event", "event"),)),
        )),
        ControlSpec("IDENTIFY", "Asset and risk identification", (
            _rule("DCT", "ATTEST", extract=(
                ("issuer", "issuer"),
                ("subject", "subject"),
            )),
        )),
        ControlSpec("PROTECT", "Safeguards and access controls", (
            _rule("KILLSWITCH", extract=(("state", "state"),)),
            _rule("CAPABILITY_FENCE", extract=(("action", "action"),)),
            _rule("DCT", extract=(("ops_allowed", "ops_allowed"),)),
        )),
        ControlSpec("DETECT", "Continuous monitoring and anomaly detection", (
            _rule("CIRCUIT_BREAKER", extract=(("state", "state"),)),
            _rule("HEALTH_PROBE"),
            _rule("BEHAVIOR_MONITOR"),
        )),
        ControlSpec("RESPOND", "Incident response", (
            _rule("KILLSWITCH", states=("HALT_ALL", "EMERGENCY"), extract=(("state", "state"),)),
            _rule("CIRCUIT_BREAKER", states=("OPEN",), extract=(("state", "state"),)),
        )),
        ControlSpec("RECOVER", "Restoration and improvement", (
            _rule("CIRCUIT_BREAKER", states=("HALF_OPEN",), extract=(("state", "state"),)),
            _rule("COST_GOVERNOR", extract=(("decision", "decision"),)),
        )),
    ),
))


# ===========================================================================
# New frameworks (2026-08-21 extension)
# ===========================================================================


# --- NIST SP 800-53 Rev 5 (base security control catalog) ------------------
#
# Maps the base 800-53 Rev 5 control families to HUMMBL governance primitives.
# This is the foundational catalog; the COSAiS overlay below adds AI-specific
# controls. Evidence is drawn from the same tuple types used by other
# frameworks (DCT, DCTX, CONTRACT, ATTEST, EVIDENCE, INTENT, KILLSWITCH,
# CIRCUIT_BREAKER, and signed audit entries).

register_framework(FrameworkSpec(
    id="nist-800-53",
    name="NIST_SP_800_53_R5",
    reference=(
        "NIST SP 800-53 Rev 5, Security and Privacy Controls for Information "
        "Systems and Organizations (2020, updated 2023)."
    ),
    default_days=30,
    controls=(
        # --- AC: Access Control ---
        ControlSpec("AC-2", "Account management", (
            _rule("DCTX", extract=(
                ("delegator", "delegator"),
                ("delegatee", "delegatee"),
            )),
        )),
        ControlSpec("AC-3", "Access enforcement", (
            _rule("DCT", extract=(
                ("issuer", "issuer"),
                ("subject", "subject"),
                ("ops_allowed", "ops_allowed"),
                ("resources", "resource_selectors"),
            )),
        )),
        ControlSpec("AC-5", "Separation of duties", (
            _rule("CONTRACT", extract=(
                ("issuer", "issuer"),
                ("subject", "subject"),
            )),
        )),
        ControlSpec("AC-21", "Information sharing", (
            _rule("DCT", extract=(
                ("issuer", "issuer"),
                ("subject", "subject"),
            )),
        )),
        # --- AU: Audit and Accountability ---
        ControlSpec("AU-2", "Event logging", (
            _rule(signed=True),
        )),
        ControlSpec("AU-6", "Audit record review and analysis", (
            _rule(signed=True),
        )),
        ControlSpec("AU-12", "Audit record generation", (
            _rule(signed=True),
        )),
        # --- CM: Configuration Management ---
        ControlSpec("CM-2", "Baseline configuration", (
            _rule("CONTRACT", extract=(
                ("issuer", "issuer"),
                ("operations", "operations"),
            )),
        )),
        # --- CP: Contingency Planning ---
        ControlSpec("CP-2", "Contingency plan", (
            _rule("CIRCUIT_BREAKER", extract=(
                ("state", "state"),
                ("adapter", "adapter"),
            )),
        )),
        # --- IA: Identification and Authentication ---
        ControlSpec("IA-2", "Identification and authentication", (
            _rule("DCTX", "DCT", extract=(
                ("subject", "subject"),
                ("issuer", "issuer"),
            )),
        )),
        ControlSpec("IA-4", "Identifier management", (
            _rule("DCTX", extract=(
                ("delegatee", "delegatee"),
            )),
        )),
        ControlSpec("IA-5", "Authenticator management", (
            _rule(signed=True),
        )),
        # --- IR: Incident Response ---
        ControlSpec("IR-4", "Incident handling", (
            _rule("KILLSWITCH", extract=(
                ("state", "state"),
                ("adapter", "adapter"),
            )),
        )),
        # --- RA: Risk Assessment ---
        ControlSpec("RA-3", "Risk assessment", (
            _rule("ATTEST", "EVIDENCE", extract=(
                ("claim", "claim"),
                ("outcome", "outcome"),
            )),
        )),
        # --- SC: System and Communications Protection ---
        ControlSpec("SC-8", "Transmission confidentiality and integrity", (
            _rule(signed=True),
        )),
        ControlSpec("SC-13", "Cryptographic protection", (
            _rule(signed=True),
        )),
        # --- SI: System and Information Integrity ---
        ControlSpec("SI-7", "Software and firmware integrity", (
            _rule(signed=True),
        )),
    ),
))


# --- NIST COSAiS (SP 800-53 Control Overlays for Securing AI Systems) ------

register_framework(FrameworkSpec(
    id="nist-cosais",
    name="NIST_COSAIS",
    reference=(
        "NIST SP 800-53 Control Overlays for Securing AI Systems (COSAiS), "
        "leveraging SP 800-218A, Draft NIST AI 800-1, NIST AI 100-2e2025."
    ),
    default_days=30,
    controls=(
        ControlSpec("AC-AI", "Access control for AI systems", (
            _rule("DCT", extract=(
                ("issuer", "issuer"),
                ("subject", "subject"),
                ("ops_allowed", "ops_allowed"),
                ("resources", "resource_selectors"),
            )),
        )),
        ControlSpec("AU-AI", "Audit logging for AI actions", (
            _rule(signed=True),
        )),
        ControlSpec("CM-AI", "Configuration management for AI models", (
            _rule("CONTRACT", extract=(("issuer", "issuer"), ("subject", "subject"))),
        )),
        ControlSpec("IA-AI", "Identity and authentication for agents", (
            _rule("DCT", "DCTX", extract=(("subject", "subject"), ("issuer", "issuer"))),
        )),
        ControlSpec("MA-AI", "Maintenance of AI system components", (
            _rule("DCTX", extract=(
                ("delegator", "delegator"),
                ("delegatee", "delegatee"),
                ("event", "event"),
            )),
        )),
        ControlSpec("PL-AI", "Planning for AI risk treatment", (
            _rule("INTENT", extract=(("objective", "objective"), ("phase", "phase"))),
        )),
        ControlSpec("PS-AI", "Personnel security for AI operations", (
            _rule("DCT", "CONTRACT", extract=(("issuer", "issuer"), ("subject", "subject"))),
        )),
        ControlSpec("RA-AI", "Risk assessment for AI systems", (
            _rule("ATTEST", "EVIDENCE", extract=(("claim", "claim"), ("outcome", "outcome"))),
        )),
        ControlSpec("SA-AI", "System and information integrity for AI", (
            _rule("CIRCUIT_BREAKER", "KILLSWITCH", extract=(
                ("state", "state"),
                ("adapter", "adapter"),
            )),
        )),
        ControlSpec("SC-AI", "System and communications protection for agents", (
            _rule("DCTX", extract=(
                ("delegator", "delegator"),
                ("delegatee", "delegatee"),
            )),
        )),
        ControlSpec("SI-AI", "Supply chain integrity for AI components", (
            _rule(signed=True),
        )),
    ),
))


# --- CoSAI (Coalition for Secure AI) ---------------------------------------

register_framework(FrameworkSpec(
    id="cosai",
    name="COSAI",
    reference=(
        "Coalition for Secure AI (CoSAI) -- AI security controls for "
        "model development, deployment, and operations."
    ),
    default_days=30,
    controls=(
        ControlSpec("CSA-01", "AI security governance", (
            _rule("INTENT", extract=(("objective", "objective"), ("agent", "agent"))),
        )),
        ControlSpec("CSA-02", "AI asset inventory and classification", (
            _rule("DCT", "ATTEST", extract=(
                ("issuer", "issuer"),
                ("subject", "subject"),
            )),
        )),
        ControlSpec("CSA-03", "AI model access control", (
            _rule("DCT", extract=(
                ("ops_allowed", "ops_allowed"),
                ("resources", "resource_selectors"),
            )),
        )),
        ControlSpec("CSA-04", "AI supply chain security", (
            _rule(signed=True),
        )),
        ControlSpec("CSA-05", "AI runtime monitoring and anomaly detection", (
            _rule("CIRCUIT_BREAKER", "HEALTH_PROBE", "BEHAVIOR_MONITOR", extract=(
                ("state", "state"),
            )),
        )),
        ControlSpec("CSA-06", "AI incident response", (
            _rule("KILLSWITCH", states=("HALT_ALL", "EMERGENCY"), extract=(
                ("state", "state"),
            )),
        )),
        ControlSpec("CSA-07", "AI data governance and provenance", (
            _rule("ATTEST", "EVIDENCE", extract=(
                ("claim", "claim"),
                ("outcome", "outcome"),
            )),
        )),
        ControlSpec("CSA-08", "AI delegation and trust chains", (
            _rule("DCTX", extract=(
                ("delegator", "delegator"),
                ("delegatee", "delegatee"),
                ("event", "event"),
            )),
        )),
        ControlSpec("CSA-09", "AI cost and resource governance", (
            _rule("COST_GOVERNOR", extract=(
                ("agent", "agent"),
                ("decision", "decision"),
                ("spend", "spend"),
                ("budget", "budget"),
            )),
        )),
        ControlSpec("CSA-10", "AI audit and compliance reporting", (
            _rule(signed=True),
        )),
    ),
))


# --- HIPAA (US healthcare data protection) ---------------------------------

register_framework(FrameworkSpec(
    id="hipaa",
    name="HIPAA",
    reference=(
        "HIPAA Security Rule (45 CFR 164.302-318) -- administrative, "
        "physical, and technical safeguards for electronic protected "
        "health information (ePHI)."
    ),
    default_days=30,
    controls=(
        ControlSpec("164.312(a)(1)", "Access control", (
            _rule("DCT", extract=(
                ("issuer", "issuer"),
                ("subject", "subject"),
                ("ops_allowed", "ops_allowed"),
                ("resources", "resource_selectors"),
            )),
        )),
        ControlSpec("164.312(b)", "Audit controls", (
            _rule(signed=True),
        )),
        ControlSpec("164.312(c)(1)", "Integrity controls", (
            _rule(signed=True),
        )),
        ControlSpec("164.312(d)", "Person or entity authentication", (
            _rule("DCT", "DCTX", extract=(
                ("subject", "subject"),
                ("issuer", "issuer"),
            )),
        )),
        ControlSpec("164.312(e)(1)", "Transmission security", (
            _rule("DCTX", extract=(
                ("delegator", "delegator"),
                ("delegatee", "delegatee"),
                ("event", "event"),
            )),
        )),
        ControlSpec("164.308(a)(1)", "Security management process", (
            _rule("CIRCUIT_BREAKER", "KILLSWITCH", extract=(
                ("state", "state"),
                ("adapter", "adapter"),
            )),
        )),
        ControlSpec("164.308(a)(3)", "Workforce security", (
            _rule("DCT", "CONTRACT", extract=(
                ("issuer", "issuer"),
                ("subject", "subject"),
            )),
        )),
        ControlSpec("164.308(a)(5)", "Security awareness and training", (
            _rule("INTENT", extract=(("objective", "objective"),)),
        )),
        ControlSpec("164.308(a)(7)", "Contingency plan", (
            _rule("KILLSWITCH", states=("HALT_ALL", "EMERGENCY"), extract=(
                ("state", "state"),
            )),
        )),
        ControlSpec("164.310(c)", "Workstation security -- use controls", (
            _rule("CAPABILITY_FENCE", extract=(("action", "action"),)),
        )),
    ),
))


# --- MAS FEAT (Singapore Monetary Authority -- FEAT Principles) ------------

register_framework(FrameworkSpec(
    id="mas-feat",
    name="MAS_FEAT",
    reference=(
        "Monetary Authority of Singapore (MAS) FEAT Principles -- "
        "Fairness, Ethics, Accountability, Transparency for AI in "
        "financial services."
    ),
    default_days=30,
    controls=(
        ControlSpec("FEAT-F1", "Fairness -- justifiable models", (
            _rule("ATTEST", "EVIDENCE", extract=(
                ("claim", "claim"),
                ("outcome", "outcome"),
            )),
        )),
        ControlSpec("FEAT-E1", "Ethics -- ethical assessment", (
            _rule("INTENT", extract=(("objective", "objective"), ("agent", "agent"))),
        )),
        ControlSpec("FEAT-E2", "Ethics -- internal controls", (
            _rule("CIRCUIT_BREAKER", "KILLSWITCH", extract=(
                ("state", "state"),
                ("adapter", "adapter"),
            )),
        )),
        ControlSpec("FEAT-A1", "Accountability -- clear roles", (
            _rule("DCTX", extract=(
                ("delegator", "delegator"),
                ("delegatee", "delegatee"),
                ("event", "event"),
            )),
        )),
        ControlSpec("FEAT-A2", "Accountability -- audit trail", (
            _rule(signed=True),
        )),
        ControlSpec("FEAT-T1", "Transparency -- purpose disclosure", (
            _rule("INTENT", extract=(("objective", "objective"), ("phase", "phase"))),
        )),
        ControlSpec("FEAT-T2", "Transparency -- data governance", (
            _rule("DCT", extract=(
                ("resources", "resource_selectors"),
                ("ops_allowed", "ops_allowed"),
            )),
        )),
        ControlSpec("FEAT-A3", "Accountability -- cost governance", (
            _rule("COST_GOVERNOR", extract=(
                ("agent", "agent"),
                ("decision", "decision"),
                ("spend", "spend"),
                ("budget", "budget"),
            )),
        )),
    ),
))


# --- PCI DSS 4.0 (Payment Card Industry Data Security Standard) ------------

register_framework(FrameworkSpec(
    id="pci-dss",
    name="PCI_DSS",
    reference="PCI DSS 4.0 (Payment Card Industry Data Security Standard).",
    default_days=30,
    controls=(
        ControlSpec("REQ-3", "Protect stored account data", (
            _rule("DCT", extract=(
                ("resources", "resource_selectors"),
                ("ops_allowed", "ops_allowed"),
            )),
        )),
        ControlSpec("REQ-5", "Protect all networks against malicious attacks", (
            _rule("CAPABILITY_FENCE", extract=(("action", "action"),)),
        )),
        ControlSpec("REQ-6", "Develop and maintain secure systems and software", (
            _rule(signed=True),
        )),
        ControlSpec("REQ-7", "Restrict access to system components and cardholder data", (
            _rule("DCT", extract=(
                ("issuer", "issuer"),
                ("subject", "subject"),
                ("ops_allowed", "ops_allowed"),
            )),
        )),
        ControlSpec("REQ-8", "Identify users and authenticate access", (
            _rule("DCT", "DCTX", extract=(
                ("subject", "subject"),
                ("issuer", "issuer"),
            )),
        )),
        ControlSpec("REQ-10", "Log and monitor all access to system components", (
            _rule(signed=True),
        )),
        ControlSpec("REQ-11", "Test security of systems and networks regularly", (
            _rule("CIRCUIT_BREAKER", "HEALTH_PROBE", extract=(("state", "state"),)),
        )),
        ControlSpec("REQ-12", "Support information security with organizational policies", (
            _rule("INTENT", extract=(("objective", "objective"),)),
        )),
    ),
))


# --- NIST AI 600-1 (Generative AI Profile) --------------------------------

register_framework(FrameworkSpec(
    id="nist-ai-600",
    name="NIST_AI_600_1",
    reference=(
        "NIST AI 600-1: Artificial Intelligence Risk Management Framework: "
        "Generative Artificial Intelligence Profile (2024)."
    ),
    default_days=30,
    controls=(
        ControlSpec("GEN-1.1", "Govern -- GenAI risk policies", (
            _rule("INTENT", extract=(("objective", "objective"), ("agent", "agent"))),
        )),
        ControlSpec("GEN-2.1", "Map -- GenAI context and use cases", (
            _rule("CONTRACT", "DCTX", fallback=(
                ("delegator", ("delegator", "issuer")),
                ("delegatee", ("delegatee", "subject")),
            )),
        )),
        ControlSpec("GEN-2.2", "Map -- GenAI training data provenance", (
            _rule("ATTEST", "EVIDENCE", extract=(
                ("claim", "claim"),
                ("outcome", "outcome"),
            )),
        )),
        ControlSpec("GEN-3.1", "Measure -- GenAI trustworthiness", (
            _rule(signed=True),
        )),
        ControlSpec("GEN-3.2", "Measure -- GenAI cost and resource impact", (
            _rule("COST_GOVERNOR", extract=(
                ("agent", "agent"),
                ("decision", "decision"),
                ("spend", "spend"),
                ("budget", "budget"),
            )),
        )),
        ControlSpec("GEN-4.1", "Manage -- GenAI incident response", (
            _rule("KILLSWITCH", states=("HALT_ALL", "EMERGENCY"), extract=(
                ("state", "state"),
            )),
        )),
        ControlSpec("GEN-4.2", "Manage -- GenAI cascading failure controls", (
            _rule("CIRCUIT_BREAKER", extract=(("state", "state"), ("adapter", "adapter"))),
        )),
        ControlSpec("GEN-4.3", "Manage -- GenAI capability fencing", (
            _rule("CAPABILITY_FENCE", extract=(("action", "action"),)),
        )),
        ControlSpec("GEN-1.2", "Govern -- GenAI delegation and trust chains", (
            _rule("DCTX", extract=(
                ("delegator", "delegator"),
                ("delegatee", "delegatee"),
                ("event", "event"),
            )),
        )),
    ),
))


# --- OWASP LLM Top 10 ------------------------------------------------------

register_framework(FrameworkSpec(
    id="owasp-llm",
    name="OWASP_LLM",
    reference="OWASP Top 10 for Large Language Model Applications (2025).",
    default_days=30,
    controls=(
        ControlSpec("LLM01", "Prompt injection", (
            _rule("INTENT", extract=(("objective", "objective"), ("phase", "phase"))),
        )),
        ControlSpec("LLM02", "Insecure output handling", (
            _rule("ATTEST", "EVIDENCE", extract=(
                ("claim", "claim"),
                ("outcome", "outcome"),
            )),
        )),
        ControlSpec("LLM03", "Training data poisoning", (
            _rule("ATTEST", extract=(("claim", "claim"),)),
        )),
        ControlSpec("LLM04", "Model DoS", (
            _rule("CIRCUIT_BREAKER", extract=(("state", "state"),)),
        )),
        ControlSpec("LLM05", "Supply chain vulnerabilities", (
            _rule(signed=True),
        )),
        ControlSpec("LLM06", "Sensitive information disclosure", (
            _rule("DCT", extract=(
                ("resources", "resource_selectors"),
                ("ops_allowed", "ops_allowed"),
            )),
        )),
        ControlSpec("LLM07", "Insecure plugin design", (
            _rule("CAPABILITY_FENCE", extract=(("action", "action"),)),
        )),
        ControlSpec("LLM08", "Excessive agency", (
            _rule("DCT", extract=(
                ("issuer", "issuer"),
                ("subject", "subject"),
                ("ops_allowed", "ops_allowed"),
            )),
        )),
        ControlSpec("LLM09", "Overreliance", (
            _rule("KILLSWITCH", extract=(("state", "state"),)),
        )),
        ControlSpec("LLM10", "Model theft", (
            _rule("DCT", "CONTRACT", extract=(
                ("issuer", "issuer"),
                ("subject", "subject"),
            )),
        )),
    ),
))


# --- OWASP MCP Top 10 (Model Context Protocol) -----------------------------

register_framework(FrameworkSpec(
    id="owasp-mcp",
    name="OWASP_MCP",
    reference="OWASP Top 10 for Model Context Protocol (MCP) -- 2026 draft.",
    default_days=30,
    controls=(
        ControlSpec("MCP01", "MCP server impersonation", (
            _rule("DCTX", extract=(
                ("delegator", "delegator"),
                ("delegatee", "delegatee"),
            )),
        )),
        ControlSpec("MCP02", "Tool injection", (
            _rule("CAPABILITY_FENCE", extract=(("action", "action"),)),
        )),
        ControlSpec("MCP03", "Credential leakage", (
            _rule("DCT", extract=(
                ("resources", "resource_selectors"),
                ("ops_allowed", "ops_allowed"),
            )),
        )),
        ControlSpec("MCP04", "Excessive tool permissions", (
            _rule("DCT", extract=(
                ("issuer", "issuer"),
                ("subject", "subject"),
                ("ops_allowed", "ops_allowed"),
            )),
        )),
        ControlSpec("MCP05", "Supply chain vulnerabilities", (
            _rule(signed=True),
        )),
        ControlSpec("MCP06", "Insecure inter-agent communication", (
            _rule("DCTX", extract=(
                ("delegator", "delegator"),
                ("delegatee", "delegatee"),
                ("event", "event"),
            )),
        )),
        ControlSpec("MCP07", "Cascading failures", (
            _rule("CIRCUIT_BREAKER", "KILLSWITCH", extract=(
                ("state", "state"),
                ("adapter", "adapter"),
            )),
        )),
        ControlSpec("MCP08", "Lack of audit logging", (
            _rule(signed=True),
        )),
        ControlSpec("MCP09", "Goal hijack via tool misuse", (
            _rule("INTENT", extract=(("objective", "objective"),)),
        )),
        ControlSpec("MCP10", "Cost and resource abuse", (
            _rule("COST_GOVERNOR", extract=(
                ("agent", "agent"),
                ("decision", "decision"),
                ("spend", "spend"),
            )),
        )),
    ),
))


# --- Singapore IMDA AI Verify ----------------------------------------------

register_framework(FrameworkSpec(
    id="imda-ai-verify",
    name="IMDA_AI_VERIFY",
    reference=(
        "Singapore IMDA AI Verify -- AI testing framework and governance "
        "testing toolkit."
    ),
    default_days=30,
    controls=(
        ControlSpec("AV-01", "Accountability testing", (
            _rule("DCTX", extract=(
                ("delegator", "delegator"),
                ("delegatee", "delegatee"),
                ("event", "event"),
            )),
        )),
        ControlSpec("AV-02", "Data governance testing", (
            _rule("ATTEST", "EVIDENCE", extract=(
                ("claim", "claim"),
                ("outcome", "outcome"),
            )),
        )),
        ControlSpec("AV-03", "Explainability testing", (
            _rule("INTENT", extract=(
                ("objective", "objective"),
                ("agent", "agent"),
                ("phase", "phase"),
            )),
        )),
        ControlSpec("AV-04", "Fairness testing", (
            _rule("ATTEST", extract=(("claim", "claim"), ("outcome", "outcome"))),
        )),
        ControlSpec("AV-05", "Human agency and oversight testing", (
            _rule("KILLSWITCH", extract=(("state", "state"),), derive=_derive_human_initiated),
        )),
        ControlSpec("AV-06", "Incident response testing", (
            _rule("CIRCUIT_BREAKER", "KILLSWITCH", extract=(
                ("state", "state"),
                ("adapter", "adapter"),
            )),
        )),
        ControlSpec("AV-07", "Robustness testing", (
            _rule("CIRCUIT_BREAKER", extract=(("state", "state"),)),
        )),
        ControlSpec("AV-08", "Security testing", (
            _rule("DCT", "CAPABILITY_FENCE", extract=(
                ("ops_allowed", "ops_allowed"),
            )),
        )),
        ControlSpec("AV-09", "Transparency testing", (
            _rule("INTENT", extract=(("objective", "objective"),)),
        )),
        ControlSpec("AV-10", "Audit trail testing", (
            _rule(signed=True),
        )),
    ),
))


# --- UK AI Safety Institute (AISI) -----------------------------------------

register_framework(FrameworkSpec(
    id="uk-aisi",
    name="UK_AISI",
    reference=(
        "UK AI Safety Institute (AISI) -- AI safety evaluation framework "
        "for frontier AI models."
    ),
    default_days=30,
    controls=(
        ControlSpec("AISI-01", "Capability evaluation", (
            _rule("ATTEST", "EVIDENCE", extract=(
                ("claim", "claim"),
                ("outcome", "outcome"),
            )),
        )),
        ControlSpec("AISI-02", "Safety critical capability assessment", (
            _rule("INTENT", extract=(
                ("objective", "objective"),
                ("phase", "phase"),
            )),
        )),
        ControlSpec("AISI-03", "Safeguard efficacy", (
            _rule("CIRCUIT_BREAKER", "KILLSWITCH", extract=(
                ("state", "state"),
                ("adapter", "adapter"),
            )),
        )),
        ControlSpec("AISI-04", "Human oversight efficacy", (
            _rule("KILLSWITCH", extract=(("state", "state"),), derive=_derive_human_initiated),
        )),
        ControlSpec("AISI-05", "Delegation chain integrity", (
            _rule("DCTX", extract=(
                ("delegator", "delegator"),
                ("delegatee", "delegatee"),
                ("event", "event"),
            )),
        )),
        ControlSpec("AISI-06", "Supply chain integrity", (
            _rule(signed=True),
        )),
        ControlSpec("AISI-07", "Access control efficacy", (
            _rule("DCT", extract=(
                ("issuer", "issuer"),
                ("subject", "subject"),
                ("ops_allowed", "ops_allowed"),
            )),
        )),
        ControlSpec("AISI-08", "Cost and resource governance", (
            _rule("COST_GOVERNOR", extract=(
                ("agent", "agent"),
                ("decision", "decision"),
                ("spend", "spend"),
                ("budget", "budget"),
            )),
        )),
        ControlSpec("AISI-09", "Capability fencing efficacy", (
            _rule("CAPABILITY_FENCE", extract=(("action", "action"),)),
        )),
        ControlSpec("AISI-10", "Audit and logging integrity", (
            _rule(signed=True),
        )),
    ),
))
