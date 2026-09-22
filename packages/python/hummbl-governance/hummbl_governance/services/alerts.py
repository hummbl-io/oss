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

"""Alerting Service for the fleet.

Multi-channel alerting for cost thresholds, agent failures, and other events.
Supports console, file, and webhook channels with easy extension.

Ported from the internal ``founder_mode`` codebase.

Usage:
    from hummbl_governance.services.alerts import AlertService, Alert, AlertLevel

    # Create service with channels
    service = AlertService()
    service.add_channel(ConsoleAlertChannel())
    service.add_channel(FileAlertChannel("alerts.log"))
    service.add_channel(WebhookAlertChannel("https://hooks.slack.com/..."))

    # Send alert
    alert = Alert(
        level=AlertLevel.WARN,
        source="cost-governor",
        title="Budget threshold reached",
        message="Spent $45 of $50 soft cap (90%)",
    )
    service.send(alert)

    # Convenience method
    service.cost_alert(projected=45.0, soft_cap=50.0, threshold_percent=90.0)
"""


import json
import logging
import urllib.error
import urllib.request
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class AlertLevel(Enum):
    """Alert severity levels."""
    INFO = "INFO"
    WARN = "WARN"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@dataclass(frozen=True, slots=True)
class Alert:
    """An alert to be sent through channels.

    Attributes:
    ----------
    level : AlertLevel
        Severity level.
    source : str
        Source of the alert (e.g., "cost-governor", "health-probe").
    title : str
        Short title/subject.
    message : str
        Detailed message.
    alert_id : str
        Unique identifier.
    timestamp : str
        ISO8601 timestamp.
    meta : dict
        Additional metadata.
    """
    level: AlertLevel
    source: str
    title: str
    message: str
    alert_id: str = field(default_factory=lambda: f"alert-{uuid.uuid4().hex[:8]}")
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    meta: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "alert_id": self.alert_id,
            "level": self.level.value,
            "source": self.source,
            "title": self.title,
            "message": self.message,
            "timestamp": self.timestamp,
            "meta": self.meta,
        }

    def to_slack_block(self) -> dict[str, Any]:
        """Convert to Slack Block Kit format."""
        level_emoji = {
            AlertLevel.INFO: ":information_source:",
            AlertLevel.WARN: ":warning:",
            AlertLevel.ERROR: ":x:",
            AlertLevel.CRITICAL: ":rotating_light:",
        }
        emoji = level_emoji.get(self.level, ":bell:")

        return {
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"{emoji} {self.title}",
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": self.message,
                    }
                },
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": f"*Source:* {self.source} | *Level:* {self.level.value} | *ID:* {self.alert_id}",
                        }
                    ]
                }
            ]
        }


class AlertChannel(ABC):
    """Base class for alert channels."""

    @abstractmethod
    def send(self, alert: Alert) -> bool:
        """Send an alert through this channel.

        Parameters
        ----------
        alert : Alert
            The alert to send.

        Returns:
        -------
        bool
            True if successfully sent.
        """

    @property
    @abstractmethod
    def name(self) -> str:
        """Channel name for logging."""


class ConsoleAlertChannel(AlertChannel):
    """Prints alerts to console/stdout."""

    @property
    def name(self) -> str:
        return "console"

    def send(self, alert: Alert) -> bool:
        """Print alert to console."""
        level_prefix = {
            AlertLevel.INFO: "ℹ️ ",
            AlertLevel.WARN: "⚠️ ",
            AlertLevel.ERROR: "❌",
            AlertLevel.CRITICAL: "🚨",
        }
        prefix = level_prefix.get(alert.level, "")
        print(f"{prefix} [{alert.level.value}] {alert.title}")
        print(f"   {alert.message}")
        print(f"   Source: {alert.source} | ID: {alert.alert_id}")
        return True


class FileAlertChannel(AlertChannel):
    """Writes alerts to a file (JSON Lines format)."""

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    @property
    def name(self) -> str:
        return f"file:{self.path}"

    def send(self, alert: Alert) -> bool:
        """Append alert to file as JSON line."""
        try:
            with open(self.path, "a") as f:
                f.write(json.dumps(alert.to_dict()) + "\n")
            return True
        except IOError:
            return False


class WebhookAlertChannel(AlertChannel):
    """Sends alerts to a webhook URL (Slack, Discord, etc.)."""

    def __init__(
        self,
        url: str,
        format: str = "slack",
        timeout: float = 10.0,
    ):
        """Initialize webhook channel.

        Parameters
        ----------
        url : str
            Webhook URL.
        format : str
            Payload format: "slack" (Block Kit), "discord", or "json".
        timeout : float
            Request timeout in seconds.
        """
        self.url = url
        self.format = format
        self.timeout = timeout
        self._validate_url()

    def _validate_url(self) -> None:
        """Validate webhook URL to reduce unsafe dynamic endpoint usage."""
        parsed = urlparse(self.url)
        if parsed.scheme not in {"http", "https"}:
            raise ValueError(f"Unsupported webhook URL scheme: {parsed.scheme}")
        if parsed.scheme == "http" and parsed.hostname not in {"127.0.0.1", "localhost"}:
            raise ValueError(f"Insecure non-loopback HTTP webhook URL: {self.url}")

    @property
    def name(self) -> str:
        # Don't expose full URL in logs
        return f"webhook:{self.format}"

    def send(self, alert: Alert) -> bool:
        """POST alert to webhook URL."""
        if self.format == "slack":
            payload = alert.to_slack_block()
        elif self.format == "discord":
            # Discord webhook format
            level_color = {
                AlertLevel.INFO: 3447003,  # Blue
                AlertLevel.WARN: 16776960,  # Yellow
                AlertLevel.ERROR: 15158332,  # Red
                AlertLevel.CRITICAL: 10038562,  # Dark Red
            }
            payload = {
                "embeds": [{
                    "title": alert.title,
                    "description": alert.message,
                    "color": level_color.get(alert.level, 0),
                    "footer": {"text": f"{alert.source} | {alert.alert_id}"},
                    "timestamp": alert.timestamp,
                }]
            }
        else:
            # Generic JSON
            payload = alert.to_dict()

        try:
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                self.url,
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=self.timeout) as response:  # nosemgrep: python.lang.security.audit.dynamic-urllib-use-detected.dynamic-urllib-use-detected
                return response.status < 400
        except (urllib.error.URLError, urllib.error.HTTPError):
            return False


class AlertService:
    """Multi-channel alert service.

    Sends alerts to all registered channels.
    """

    def __init__(self):
        self._channels: list[AlertChannel] = []

    def add_channel(self, channel: AlertChannel) -> None:
        """Add an alert channel."""
        self._channels.append(channel)

    def remove_channel(self, channel: AlertChannel) -> None:
        """Remove an alert channel."""
        self._channels.remove(channel)

    @property
    def channels(self) -> list[str]:
        """List of channel names."""
        return [c.name for c in self._channels]

    def send(self, alert: Alert) -> dict[str, bool]:
        """Send alert to all channels.

        Parameters
        ----------
        alert : Alert
            The alert to send.

        Returns:
        -------
        dict[str, bool]
            Channel name -> success status.
        """
        results = {}
        for channel in self._channels:
            try:
                results[channel.name] = channel.send(alert)
            except Exception:
                logger.debug("Alert channel %s send failed", channel.name, exc_info=True)
                results[channel.name] = False
        return results

    def cost_alert(
        self,
        projected: float,
        soft_cap: float,
        threshold_percent: float,
        hard_cap: float | None = None,
        decision: str = "WARN",
        currency: str = "USD",
    ) -> Alert:
        """Send a cost threshold alert.

        Parameters
        ----------
        projected : float
            Projected spend.
        soft_cap : float
            Soft cap limit.
        threshold_percent : float
            Percentage of soft cap used.
        hard_cap : float, optional
            Hard cap limit.
        decision : str
            Cost governor decision (ALLOW, WARN, DENY).
        currency : str
            Currency code.

        Returns:
        -------
        Alert
            The sent alert.
        """
        if decision == "DENY" or threshold_percent >= 100:
            level = AlertLevel.CRITICAL
            title = "Budget limit reached"
        elif threshold_percent >= 80:
            level = AlertLevel.WARN
            title = "Budget threshold warning"
        else:
            level = AlertLevel.INFO
            title = "Cost update"

        message = (
            f"Projected spend: {currency} {projected:.2f}\n"
            f"Soft cap: {currency} {soft_cap:.2f} ({threshold_percent:.1f}% used)"
        )
        if hard_cap:
            message += f"\nHard cap: {currency} {hard_cap:.2f}"
        message += f"\nDecision: {decision}"

        alert = Alert(
            level=level,
            source="cost-governor",
            title=title,
            message=message,
            meta={
                "projected": projected,
                "soft_cap": soft_cap,
                "hard_cap": hard_cap,
                "threshold_percent": threshold_percent,
                "decision": decision,
                "currency": currency,
            },
        )

        self.send(alert)
        return alert

    def agent_alert(
        self,
        agent_name: str,
        status: str,
        message: str,
    ) -> Alert:
        """Send an agent status alert.

        Parameters
        ----------
        agent_name : str
            Name of the agent.
        status : str
            Agent status (READY, DEGRADED, UNAVAILABLE).
        message : str
            Status message.

        Returns:
        -------
        Alert
            The sent alert.
        """
        level_map = {
            "UNAVAILABLE": AlertLevel.ERROR,
            "DEGRADED": AlertLevel.WARN,
            "READY": AlertLevel.INFO,
        }
        level = level_map.get(status, AlertLevel.INFO)

        alert = Alert(
            level=level,
            source="health-probe",
            title=f"Agent {agent_name}: {status}",
            message=message,
            meta={
                "agent_name": agent_name,
                "status": status,
            },
        )

        self.send(alert)
        return alert


def create_default_alert_service(
    log_path: str | Path | None = None,
    webhook_url: str | None = None,
    webhook_format: str = "slack",
) -> AlertService:
    """Create an alert service with common channels.

    Parameters
    ----------
    log_path : str | Path, optional
        Path for file logging.
    webhook_url : str, optional
        Webhook URL for notifications.
    webhook_format : str
        Webhook format (slack, discord, json).

    Returns:
    -------
    AlertService
        Configured alert service.
    """
    service = AlertService()
    service.add_channel(ConsoleAlertChannel())

    if log_path:
        service.add_channel(FileAlertChannel(log_path))

    if webhook_url:
        service.add_channel(WebhookAlertChannel(webhook_url, format=webhook_format))

    return service
