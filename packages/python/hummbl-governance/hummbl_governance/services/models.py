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

"""Data models for Founder Mode services.

Contract-aligned models for briefing assembly and agent coordination.
Governance models aligned with hummbl-agent JSON schemas (v1.0.0).
"""

from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

__all__ = (
    "AgentStatus",
    "CostDecision",
    "GovernorDecisionType",
    "AgentType",
    "ArtifactType",
    "PriorityItem",
    "OvernightEvent",
    "CostProjection",
    "AgentHealthReport",
    "CalendarEntry",
    "KimiClawSummary",
    "BriefingContent",
    "BriefingGenerationEnvelope",
    "BriefingAuditRecord",
    "BriefingArtifact",
    "ProposedAction",
    "Artifact",
    "RepoContext",
    "InterAgentRequest",
    "GovernorDecision",
    "SecurityScanSummary",
    "DispatchEnvelope",
    "Receipt",
    "MissionState",
    "MissionType",
    "MissionPacket",
    "MissionCloseout",
    "MissionRegistry",
)


class AgentStatus(Enum):
    """Agent readiness states aligned with openclaw.health_status."""

    READY = "healthy"
    IDLE = "idle"  # session-based agent, not recently active, no action needed
    DEGRADED = "degraded"
    UNAVAILABLE = "unhealthy"
    UNKNOWN = "unknown"


class CostDecision(Enum):
    """Cost governor decision outcomes."""

    ALLOW = "ALLOW"
    WARN = "WARN"
    DENY = "DENY"


class GovernorDecisionType(Enum):
    """Governor decision outcomes aligned with governor_decision_record.schema.json."""

    AUTHORIZE = "AUTHORIZE"
    DENY = "DENY"
    REQUEST_CLARIFICATION = "REQUEST_CLARIFICATION"
    ESCALATE = "ESCALATE"
    TERMINATE_RUN = "TERMINATE_RUN"


class AgentType(Enum):
    """Agent classification for inter-agent requests."""

    EXECUTION = "execution"
    ANALYSIS = "analysis"
    INTERFACE = "interface"


class ArtifactType(Enum):
    """Artifact types for inter-agent request tracking."""

    FILE = "file"
    HASH = "hash"
    VERSION_TAG = "version_tag"
    RUN_ARTIFACT = "run_artifact"


@dataclass(frozen=True, slots=True)
class PriorityItem:
    """A ranked priority item for the briefing.

    Aligned with openclaw.routing_decision.
    """

    item_id: str
    title: str
    priority_rank: int
    source: str
    routing_id: str
    reason_codes: list[str]
    constraints: dict[str, Any] = field(default_factory=dict)
    confidence: str = "medium"  # ASI09: "high", "medium", "low"
    proof_url: str | None = None  # ASI09: link to source (issue, PR, etc.)
    collected_at: str | None = None  # ASI09: ISO timestamp of data collection

    @classmethod
    def create(
        cls,
        title: str,
        priority_rank: int,
        source: str,
        reason_codes: list[str],
        constraints: dict[str, Any] | None = None,
        confidence: str = "medium",
        proof_url: str | None = None,
    ) -> PriorityItem:
        """Factory method with auto-generated IDs."""
        return cls(
            item_id=f"item-{uuid.uuid4().hex[:8]}",
            title=title,
            priority_rank=priority_rank,
            source=source,
            routing_id=f"route-{uuid.uuid4().hex[:8]}",
            reason_codes=reason_codes,
            constraints=constraints
            or {"privacy_class": "internal", "latency_target_ms": 0},
            confidence=confidence,
            proof_url=proof_url,
            collected_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        )


@dataclass(frozen=True, slots=True)
class OvernightEvent:
    """An overnight event collected for the briefing.

    Aligned with openclaw.log_event.
    """

    event_id: str
    timestamp: str
    source: str
    event_type: str
    message: str
    level: str = "INFO"
    routing_id: str | None = None
    meta: dict[str, Any] = field(default_factory=dict)
    confidence: str = "medium"  # ASI09: "high", "medium", "low"
    proof_url: str | None = None  # ASI09: link to source data

    @classmethod
    def create(
        cls,
        source: str,
        event_type: str,
        message: str,
        level: str = "INFO",
        timestamp: datetime | None = None,
        meta: dict[str, Any] | None = None,
        confidence: str = "medium",
        proof_url: str | None = None,
    ) -> OvernightEvent:
        """Factory method with auto-generated IDs."""
        ts = timestamp or datetime.now(timezone.utc)
        return cls(
            event_id=f"evt-{uuid.uuid4().hex[:8]}",
            timestamp=ts.isoformat().replace("+00:00", "Z"),
            source=source,
            event_type=event_type,
            message=message,
            level=level,
            routing_id=f"route-{uuid.uuid4().hex[:8]}",
            meta=meta or {},
            confidence=confidence,
            proof_url=proof_url,
        )

    def to_log_event(self, task_id: str, trace_id: str) -> dict[str, Any]:
        """Convert to openclaw.log_event format."""
        result: dict[str, Any] = {
            "event_id": self.event_id,
            "timestamp": self.timestamp,
            "task_id": task_id,
            "trace_id": trace_id,
            "source": self.source,
            "level": self.level,
            "message": self.message,
            "event_type": self.event_type,
        }
        if self.routing_id:
            result["routing_decision_id"] = self.routing_id
        if self.meta:
            result["meta"] = self.meta
        return result


@dataclass(frozen=True, slots=True)
class CostProjection:
    """Daily cost projection aligned with openclaw.cost_governor.

    This is a projection/estimate, not the config itself.
    """

    projected_spend: float
    currency: str
    soft_cap: float
    hard_cap: float | None
    decision: CostDecision
    rationale: str
    breakdown: dict[str, float] = field(default_factory=dict)

    @property
    def threshold_percent(self) -> float:
        """Percentage of soft cap used."""
        if self.soft_cap <= 0:
            return 0.0
        return (self.projected_spend / self.soft_cap) * 100

    def to_decision_output(self) -> dict[str, Any]:
        """Convert to decision output format for logging."""
        return {
            "projected_spend": self.projected_spend,
            "currency": self.currency,
            "soft_cap": self.soft_cap,
            "hard_cap": self.hard_cap,
            "decision": self.decision.value,
            "rationale": self.rationale,
            "threshold_percent": self.threshold_percent,
            "breakdown": self.breakdown,
        }


@dataclass(frozen=True, slots=True)
class AgentHealthReport:
    """Health report for a single agent."""

    agent_name: str
    status: AgentStatus
    probe_type: str
    message: str
    duration_ms: float
    timestamp: str
    details: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class CalendarEntry:
    """A calendar entry for the day."""

    entry_id: str
    title: str
    start_time: str
    end_time: str
    location: str | None = None
    is_all_day: bool = False
    account_label: str | None = None

    @property
    def duration_display(self) -> str:
        """Human-readable duration."""
        if self.is_all_day:
            return "All day"
        return f"{self.start_time} - {self.end_time}"


@dataclass(frozen=True, slots=True)
class KimiClawSummary:
    """Kimi Claw verification summary for briefing integration.

    Captures verification results from Kimi Claw proof gate and
    coordination validation scripts.
    """

    request_id: str
    trace_id: str
    verification_status: str  # PASS, FAIL, PENDING
    checks_performed: int
    checks_passed: int
    artifact_ref: str
    timestamp: str
    details: dict[str, Any] = field(default_factory=dict)

    @property
    def all_checks_passed(self) -> bool:
        """True if all checks passed."""
        return self.checks_passed == self.checks_performed and self.checks_performed > 0

    @property
    def summary_text(self) -> str:
        """Human-readable summary."""
        if self.all_checks_passed:
            return f"All {self.checks_performed} checks passed"
        return f"{self.checks_passed}/{self.checks_performed} checks passed"


@dataclass(slots=True)
class BriefingContent:
    """Assembled briefing content ready for rendering."""

    generated_at: str
    wake_time: str
    agent_status: list[AgentHealthReport]
    calendar_entries: list[CalendarEntry]
    priority_items: list[PriorityItem]
    overnight_events: list[OvernightEvent]
    cost_projection: CostProjection
    all_agents_ready: bool
    warnings: list[str] = field(default_factory=list)
    # Optional local-model draft section (advisory only).
    local_draft: str | None = None
    # Optional feedback summary from previous briefings.
    feedback_summary: dict[str, Any] | None = None
    # Optional security scan summary (Phase 2 Pillar 2.3).
    security_summary: SecurityScanSummary | None = None
    # Optional sprint recommendation summary (Phase 2 Pillar 3).
    sprint_recommendation: dict[str, Any] | None = None
    # Optional Kimi Claw verification summary (PR3 Integration).
    kimi_claw_summary: KimiClawSummary | None = None
    # Optional CRM pipeline summary (GaaS CRM module).
    crm_summary: Any | None = None
    # Optional Gmail inbox summary (unread_count, flagged_count, top_threads).
    inbox_summary: dict[str, Any] | None = None
    # Optional financial summary from Google Sheets.
    financial_summary: dict[str, Any] | None = None
    # Optional meeting prep docs (linked Google Docs for calendar events).
    meeting_prep_docs: dict[str, list[dict[str, Any]]] | None = None
    # Optional recent documents list.
    recent_documents: list[dict[str, Any]] | None = None
    # Optional synthesis output (executive_summary, action_items, risk_alerts).
    synthesis: dict[str, Any] | None = None
    # Optional TTS audio file path.
    audio_path: str | None = None
    # Optional research digest (findings + proposals summary).
    research_digest: dict[str, Any] | None = None
    # Optional intelligence feed digest (security advisories, releases, weather).
    intelligence_digest: dict[str, Any] | None = None
    # Optional DREAM log morning summary (HRSI HULE capture, Gap 4).
    dream_summary: dict[str, Any] | None = None
    # Optional collection posture summary (INT taxonomy from hummbl-intel).
    posture_summary: str | None = None
    # System incidents (bus BLOCKED/ERROR, circuit breaker trips, health failures).
    system_incidents: list[dict[str, Any]] = field(default_factory=list)
    # Fleet timeline digest (24h summary from all intel surfaces).
    timeline_digest: dict[str, Any] | None = None

    @property
    def agent_summary(self) -> dict[str, int]:
        """Count agents by status."""
        counts = {"ready": 0, "degraded": 0, "unavailable": 0, "unknown": 0}
        for agent in self.agent_status:
            key = agent.status.name.lower()
            counts[key] = counts.get(key, 0) + 1
        return counts


# ---------------------------------------------------------------------------
# Dual-observable briefing artifact -- provenance envelopes
# Implements the dual-observable artifact pattern from HUMMBL visualization
# research: every briefing carries _generation + _audit so downstream agents
# can query it without parsing prose.
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class BriefingGenerationEnvelope:
    """Records how this briefing artifact was produced.

    Mirrors the _generation envelope from the dual-observable pipeline spec.
    temperature and model are None when no LLM generation step is present
    in the current briefing pipeline.
    """

    pipeline_version: str
    generated_at: str
    adapters_invoked: list[str]
    model: str | None = None
    temperature: float | None = None
    governance_flags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "pipeline_version": self.pipeline_version,
            "generated_at": self.generated_at,
            "adapters_invoked": self.adapters_invoked,
            "model": self.model,
            "temperature": self.temperature,
            "governance_flags": self.governance_flags,
        }


@dataclass(frozen=True, slots=True)
class BriefingAuditRecord:
    """Full lineage record for a briefing artifact.

    Mirrors the _audit envelope from the dual-observable pipeline spec.
    artifact_id is a sortable timestamp-prefixed identifier (UUID v7 style).
    """

    artifact_id: str
    artifact_hash: str
    created_at: str
    data_lineage: list[str]
    agent_health_summary: dict[str, int]
    validation_gates_passed: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "artifact_id": self.artifact_id,
            "artifact_hash": self.artifact_hash,
            "created_at": self.created_at,
            "data_lineage": self.data_lineage,
            "agent_health_summary": self.agent_health_summary,
            "validation_gates_passed": self.validation_gates_passed,
        }


@dataclass(frozen=True, slots=True)
class BriefingArtifact:
    """A dual-observable briefing artifact.

    Wraps BriefingContent with _generation and _audit envelopes so that
    downstream agents can query structured data without parsing markdown prose.
    The JSON sidecar (produced by to_json()) is written alongside the .md file.
    """

    content: BriefingContent
    _generation: BriefingGenerationEnvelope
    _audit: BriefingAuditRecord

    @classmethod
    def from_content(
        cls,
        content: BriefingContent,
        pipeline_version: str,
        adapters_invoked: list[str],
        rendered_markdown: str,
    ) -> "BriefingArtifact":
        """Construct a BriefingArtifact from assembled BriefingContent.

        Computes artifact_hash over the rendered markdown so the hash
        covers the final human-readable output, not just the data model.
        """
        now = datetime.now(timezone.utc).isoformat()
        artifact_hash = "sha256:" + hashlib.sha256(
            rendered_markdown.encode()
        ).hexdigest()
        # Timestamp-prefixed ID for chronological sort (UUID v7 style intent)
        artifact_id = f"{content.generated_at[:19].replace(':', '-')}-{uuid.uuid4().hex[:8]}"

        generation = BriefingGenerationEnvelope(
            pipeline_version=pipeline_version,
            generated_at=now,
            adapters_invoked=adapters_invoked,
        )
        audit = BriefingAuditRecord(
            artifact_id=artifact_id,
            artifact_hash=artifact_hash,
            created_at=now,
            data_lineage=adapters_invoked,
            agent_health_summary=content.agent_summary,
            validation_gates_passed=["schema", "assembly"],
        )
        return cls(content=content, _generation=generation, _audit=audit)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a machine-readable dict suitable for JSON export."""
        c = self.content
        return {
            "_generation": self._generation.to_dict(),
            "_audit": self._audit.to_dict(),
            "generated_at": c.generated_at,
            "wake_time": c.wake_time,
            "all_agents_ready": c.all_agents_ready,
            "agent_summary": c.agent_summary,
            "agent_status": [
                {
                    "agent_name": a.agent_name,
                    "status": a.status.name,
                    "probe_type": a.probe_type,
                    "message": a.message,
                    "duration_ms": a.duration_ms,
                    "timestamp": a.timestamp,
                }
                for a in c.agent_status
            ],
            "calendar_entries": [
                {
                    "entry_id": e.entry_id,
                    "title": e.title,
                    "start_time": e.start_time,
                    "end_time": e.end_time,
                    "is_all_day": e.is_all_day,
                }
                for e in c.calendar_entries
            ],
            "priority_items": [
                {"title": p.title, "priority_rank": p.priority_rank, "source": p.source}
                for p in c.priority_items
            ],
            "cost_projection": {
                "projected_spend": c.cost_projection.projected_spend,
                "currency": c.cost_projection.currency,
                "soft_cap": c.cost_projection.soft_cap,
                "hard_cap": c.cost_projection.hard_cap,
                "decision": c.cost_projection.decision.name,
            },
            "warnings": c.warnings,
        }

    def to_json(self, indent: int = 2) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=indent, default=str)


# ---------------------------------------------------------------------------
# Governance models -- aligned with hummbl-agent schemas v1.0.0
# See: governance/schemas/governor_decision_record.schema.json
#      governance/schemas/inter_agent_request.schema.json
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class ProposedAction:
    """A single action within an inter-agent request."""

    action: str
    scope: str


@dataclass(frozen=True, slots=True)
class Artifact:
    """An artifact referenced by an inter-agent request."""

    id: str
    type: ArtifactType
    ref: str

    def to_dict(self) -> dict[str, str]:
        return {"id": self.id, "type": self.type.value, "ref": self.ref}


@dataclass(frozen=True, slots=True)
class RepoContext:
    """Repository context for an inter-agent request."""

    repo: str
    branch: str
    commit: str

    def to_dict(self) -> dict[str, str]:
        return {"repo": self.repo, "branch": self.branch, "commit": self.commit}


@dataclass(frozen=True, slots=True)
class InterAgentRequest:
    """Structured request from one agent to another.

    Aligned with hummbl-agent inter_agent_request.schema.json v1.0.0.
    """

    request_id: str
    timestamp: str
    requesting_agent_id: str
    requesting_agent_type: AgentType
    supervisor: str
    declared_intent: str
    proposed_actions: list[ProposedAction]
    artifacts: list[Artifact]
    repo_context: RepoContext
    freeze_status_acknowledgment: bool = False

    @classmethod
    def create(
        cls,
        agent_id: str,
        agent_type: AgentType,
        intent: str,
        actions: list[ProposedAction],
        artifacts: list[Artifact],
        repo_context: RepoContext,
        freeze_ack: bool = False,
    ) -> InterAgentRequest:
        """Factory with auto-generated ID and timestamp."""
        return cls(
            request_id=f"req-{uuid.uuid4().hex[:8]}",
            timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            requesting_agent_id=agent_id,
            requesting_agent_type=agent_type,
            supervisor="HUMMBL_GOVERNOR",
            declared_intent=intent,
            proposed_actions=actions,
            artifacts=artifacts,
            repo_context=repo_context,
            freeze_status_acknowledgment=freeze_ack,
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dict matching the JSON schema."""
        return {
            "schema_version": "1.0.0",
            "request_id": self.request_id,
            "timestamp": self.timestamp,
            "requesting_agent": {
                "id": self.requesting_agent_id,
                "type": self.requesting_agent_type.value,
            },
            "supervisor": self.supervisor,
            "declared_intent": self.declared_intent,
            "proposed_actions": [
                {"action": a.action, "scope": a.scope} for a in self.proposed_actions
            ],
            "artifacts": [a.to_dict() for a in self.artifacts],
            "repo_context": self.repo_context.to_dict(),
            "freeze_status_acknowledgment": self.freeze_status_acknowledgment,
        }


@dataclass(frozen=True, slots=True)
class GovernorDecision:
    """A governance decision record.

    Aligned with hummbl-agent governor_decision_record.schema.json v1.0.0.
    """

    decision_id: str
    request_id: str
    timestamp: str
    decision: GovernorDecisionType
    action: str
    reason: str
    violated_rule: str = "NONE"
    constraints: list[str] = field(default_factory=list)
    halt_required: bool = False

    @classmethod
    def create(
        cls,
        request_id: str,
        decision: GovernorDecisionType,
        action: str,
        reason: str,
        violated_rule: str = "NONE",
        constraints: list[str] | None = None,
        halt_required: bool = False,
    ) -> GovernorDecision:
        """Factory with auto-generated ID and timestamp."""
        return cls(
            decision_id=f"dec-{uuid.uuid4().hex[:8]}",
            request_id=request_id,
            timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            decision=decision,
            action=action,
            reason=reason,
            violated_rule=violated_rule,
            constraints=constraints or [],
            halt_required=halt_required,
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dict matching the JSON schema."""
        return {
            "schema_version": "1.0.0",
            "decision_id": self.decision_id,
            "request_id": self.request_id,
            "timestamp": self.timestamp,
            "governor": "HUMMBL_GOVERNOR",
            "decision": self.decision.value,
            "action": self.action,
            "reason": self.reason,
            "violated_rule": self.violated_rule,
            "constraints": self.constraints,
            "halt_required": self.halt_required,
        }


@dataclass(frozen=True, slots=True)
class SecurityScanSummary:
    """Security scan summary for briefing integration.

    Mirrors SecuritySummary from security_adapter.py for models-level
    access. Used by briefing.py to render the Security Scan section.

    Attributes:
    ----------
    last_scan : str
        ISO 8601 timestamp of when the summary was generated.
    tool : str
        Comma-separated list of tools (e.g. "bandit,semgrep").
    findings : dict[str, int]
        Counts by severity: critical, high, medium, low.
    dependencies : dict[str, int]
        Dependency health: outdated, vulnerable counts.
    """

    last_scan: str
    tool: str
    findings: dict[str, int] = field(
        default_factory=lambda: {
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0,
        }
    )
    dependencies: dict[str, int] = field(
        default_factory=lambda: {
            "outdated": 0,
            "vulnerable": 0,
        }
    )

    @property
    def total_findings(self) -> int:
        """Total number of findings across all severities."""
        return sum(self.findings.values())

    @property
    def has_critical_or_high(self) -> bool:
        """True if any critical or high-severity findings exist."""
        return self.findings.get("critical", 0) > 0 or self.findings.get("high", 0) > 0

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary for briefing assembly."""
        return {
            "last_scan": self.last_scan,
            "tool": self.tool,
            "findings": dict(self.findings),
            "dependencies": dict(self.dependencies),
            "total_findings": self.total_findings,
            "has_critical_or_high": self.has_critical_or_high,
        }

    @classmethod
    def from_security_summary(cls, summary: Any) -> "SecurityScanSummary":
        """Create from security_adapter.SecuritySummary."""
        return cls(
            last_scan=summary.last_scan,
            tool=summary.tool,
            findings=dict(summary.findings),
            dependencies=dict(summary.dependencies),
        )


@dataclass(frozen=True, slots=True)
class DispatchEnvelope:
    """Structured dispatch with scope fences for multi-agent task assignment.

    Posted as DISPATCH message payload on the coordination bus.
    Scope fences (scope, boundary, budget) constrain agent work
    to prevent scope creep in multi-vendor coordination.
    """

    dispatch_id: str
    task: str
    agent: str
    scope: list[str]           # Files/dirs the agent should touch
    boundary: list[str]        # Files/dirs the agent must NOT touch
    budget: int                # Max LOC (0 = unlimited)
    acceptance: list[str]      # Acceptance criteria
    correlation_id: str
    timestamp: str
    context: str = ""          # Optional background/instructions

    @classmethod
    def create(
        cls,
        task: str,
        agent: str,
        scope: list[str],
        boundary: list[str] | None = None,
        budget: int = 0,
        acceptance: list[str] | None = None,
        context: str = "",
    ) -> DispatchEnvelope:
        """Factory method with auto-generated IDs."""
        # Keep this data model independent of bus transports and their configuration.

        return cls(
            dispatch_id=f"dsp-{uuid.uuid4().hex[:8]}",
            task=task,
            agent=agent,
            scope=scope,
            boundary=boundary or [],
            budget=budget,
            acceptance=acceptance or [],
            correlation_id=f"dsp-{uuid.uuid4().hex[:12]}",
            timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            context=context,
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary for bus payload."""
        return {
            "dispatch_id": self.dispatch_id,
            "task": self.task,
            "agent": self.agent,
            "scope": list(self.scope),
            "boundary": list(self.boundary),
            "budget": self.budget,
            "acceptance": list(self.acceptance),
            "correlation_id": self.correlation_id,
            "timestamp": self.timestamp,
            "context": self.context,
        }


@dataclass(frozen=True, slots=True)
class Receipt:
    """Proof-of-work receipt for verifiable task completion.

    Posted as RECEIPT message payload on the coordination bus.
    Contains verifiable evidence (file list, diff stats, test results)
    that can be spot-checked by the coordinator.
    """

    receipt_id: str
    dispatch_id: str
    agent: str
    correlation_id: str
    timestamp: str
    status: str                          # COMPLETE, PARTIAL, FAILED, BLOCKED
    files_changed: list[str]
    files_created: list[str]
    diff_stat: str                       # e.g. "+142 -7 across 3 files"
    tests_added: int
    tests_passing: str                   # e.g. "12/12" or "46/46"
    verification_cmd: str                # Command to verify (e.g. pytest invocation)
    notes: str = ""

    @classmethod
    def create(
        cls,
        dispatch_id: str,
        agent: str,
        correlation_id: str,
        status: str,
        files_changed: list[str] | None = None,
        files_created: list[str] | None = None,
        diff_stat: str = "",
        tests_added: int = 0,
        tests_passing: str = "",
        verification_cmd: str = "",
        notes: str = "",
    ) -> Receipt:
        """Factory method with auto-generated receipt ID."""
        return cls(
            receipt_id=f"rct-{uuid.uuid4().hex[:8]}",
            dispatch_id=dispatch_id,
            agent=agent,
            correlation_id=correlation_id,
            timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            status=status,
            files_changed=files_changed or [],
            files_created=files_created or [],
            diff_stat=diff_stat,
            tests_added=tests_added,
            tests_passing=tests_passing,
            verification_cmd=verification_cmd,
            notes=notes,
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary for bus payload."""
        return {
            "receipt_id": self.receipt_id,
            "dispatch_id": self.dispatch_id,
            "agent": self.agent,
            "correlation_id": self.correlation_id,
            "timestamp": self.timestamp,
            "status": self.status,
            "files_changed": list(self.files_changed),
            "files_created": list(self.files_created),
            "diff_stat": self.diff_stat,
            "tests_added": self.tests_added,
            "tests_passing": self.tests_passing,
            "verification_cmd": self.verification_cmd,
            "notes": self.notes,
        }


