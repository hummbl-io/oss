"""Models stub — minimal data classes for MCP modules."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any


@dataclass
class AgentHealthReport:
    agent_id: str = ""
    status: str = ""
    message: str = ""
    timestamp: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
