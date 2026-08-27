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

"""Human-in-the-Loop (HITL) Approvals -- gated execution with reviewer consensus.

Provides a governance primitive that requires explicit human approval before
an agent action proceeds.  Designed for high-risk operations (file deletion,
external API calls with side effects, production deploys, cost-intensive runs)
where autonomous execution is unsafe.

Features:
    - Risk-tiered approval requests (LOW, MEDIUM, HIGH, CRITICAL)
    - Configurable expiry / auto-expiration of stale requests
    - Pluggable notification hooks (webhook, Slack, email, custom)
    - Optional persistence (survives process restart)
    - Blocking and poll-based wait modes
    - Audit-log integration (emits governance events on every state change)
    - Thread-safe (RLock)

Usage:
    from hummbl_governance import ApprovalManager, RiskLevel

    mgr = ApprovalManager(webhook_url="https://hooks.slack.com/services/...")
    req = mgr.request_approval(
        agent_id="worker-1",
        action="delete_file",
        action_args="/data/production.db",
        risk_level=RiskLevel.HIGH,
        justification="Cleaning up stale backup per run-123",
        timeout_seconds=300,
    )

    # Poll-based (MCP / async):
    status = mgr.check_status(req.request_id)
    if status["status"] == "APPROVED":
        proceed()

    # Blocking (synchronous agent loop):
    decision = mgr.wait_for_decision(req.request_id, timeout=300)
    if decision["status"] != "APPROVED":
        abort()

Stdlib-only. Zero third-party dependencies.
"""

from __future__ import annotations

import json
import logging
import smtplib
import ssl
import threading
import time
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable
from urllib import request as urlrequest
from urllib.error import URLError

from hummbl_governance._types import ApprovalRequest, ApprovalStatus, RiskLevel

logger = logging.getLogger(__name__)


class ApprovalError(Exception):
    """Base exception for approval-related failures."""

    def __init__(self, reason: str, request_id: str | None = None):
        self.reason = reason
        self.request_id = request_id
        super().__init__(f"Approval error: {reason}")


class ApprovalExpiredError(ApprovalError):
    """Raised when an action is attempted on an expired request."""

    def __init__(self, request_id: str):
        super().__init__(f"Request {request_id} has expired", request_id)


class ApprovalNotFoundError(ApprovalError):
    """Raised when a request_id is not found in the manager."""

    def __init__(self, request_id: str):
        super().__init__(f"Request {request_id} not found", request_id)


class ApprovalAlreadyDecidedError(ApprovalError):
    """Raised when a decision is attempted on an already-terminal request."""

    def __init__(self, request_id: str, current_status: str):
        super().__init__(f"Request {request_id} already decided ({current_status})", request_id)


# Risk-level ordering for policy comparisons.
_RISK_ORDER = {
    RiskLevel.LOW: 0,
    RiskLevel.MEDIUM: 1,
    RiskLevel.HIGH: 2,
    RiskLevel.CRITICAL: 3,
}


class ApprovalManager:
    """Manages human-in-the-loop approval requests.

    Args:
        state_dir: Directory for persistent state. None disables persistence.
        webhook_url: Generic webhook URL for notifications (POST JSON).
        slack_webhook_url: Slack incoming webhook URL (optional, dedicated).
        email_config: Dict with keys ``host``, ``port``, ``from``, ``to``,
            and optional ``username``, ``password``, ``use_tls`` for SMTP.
        audit_log: Optional AuditLog instance. If provided, every state change
            is recorded as a governance event.
        auto_expire_interval: Seconds between automatic expiration sweeps.
            0 disables background expiration (use expire_stale() manually).
        default_timeout: Default approval timeout in seconds if not specified
            per-request. None means no expiry.

    Examples:
        >>> mgr = ApprovalManager()
        >>> req = mgr.request_approval(
        ...     agent_id="agent-1",
        ...     action="send_email",
        ...     action_args="to=client@example.com",
        ...     risk_level=RiskLevel.MOW,
        ...     justification="Weekly report",
        ... )
        Traceback (most recent call last):
            ...
        ValueError: Unknown RiskLevel: MOW
        >>> req = mgr.request_approval(
        ...     agent_id="agent-1",
        ...     action="send_email",
        ...     action_args="to=client@example.com",
        ...     risk_level=RiskLevel.LOW,
        ...     justification="Weekly report",
        ... )
        >>> req.status
        <ApprovalStatus.PENDING: 1>
        >>> mgr.approve(req.request_id, decided_by="operator")
        >>> mgr.check_status(req.request_id)["status"]
        'APPROVED'
    """

    def __init__(
        self,
        state_dir: Path | None = None,
        webhook_url: str | None = None,
        slack_webhook_url: str | None = None,
        email_config: dict[str, Any] | None = None,
        audit_log: Any | None = None,
        auto_expire_interval: int = 0,
        default_timeout: float | None = None,
    ):
        self._requests: dict[str, ApprovalRequest] = {}
        self._state_dir = state_dir
        self._webhook_url = webhook_url
        self._slack_webhook_url = slack_webhook_url
        self._email_config = email_config
        self._audit_log = audit_log
        self._default_timeout = default_timeout
        self._lock = threading.RLock()
        self._expire_thread: threading.Thread | None = None
        self._expire_stop = threading.Event()

        if auto_expire_interval > 0:
            self._start_expire_loop(auto_expire_interval)

        if state_dir is not None:
            self._load_from_disk()

    # ------------------------------------------------------------------
    # Public API -- request lifecycle
    # ------------------------------------------------------------------

    def request_approval(
        self,
        agent_id: str,
        action: str,
        action_args: str,
        risk_level: RiskLevel,
        justification: str,
        timeout_seconds: float | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> ApprovalRequest:
        """Create a new approval request and notify reviewers.

        Args:
            agent_id: Agent requesting approval.
            action: Action/tool name requiring approval.
            action_args: Human-readable summary of arguments (redacted).
            risk_level: Risk classification (LOW/MEDIUM/HIGH/CRITICAL).
            justification: Agent's stated reason for the action.
            timeout_seconds: Seconds before auto-expiry. None uses
                default_timeout; if both are None, no expiry.
            metadata: Extra context (task_id, contract_id, etc.).

        Returns:
            ApprovalRequest with status PENDING.

        Raises:
            ValueError: If risk_level is not a RiskLevel enum.
        """
        if not isinstance(risk_level, RiskLevel):
            raise ValueError(f"Unknown RiskLevel: {risk_level}")

        now = datetime.now(timezone.utc)
        effective_timeout = timeout_seconds if timeout_seconds is not None else self._default_timeout
        expires_at = (now + timedelta(seconds=effective_timeout)).isoformat() if effective_timeout is not None else None

        request = ApprovalRequest(
            request_id=str(uuid.uuid4()),
            agent_id=agent_id,
            action=action,
            action_args=action_args,
            risk_level=risk_level,
            justification=justification,
            created_at=now.isoformat(),
            expires_at=expires_at,
            metadata=metadata or {},
        )

        with self._lock:
            self._requests[request.request_id] = request
            self._persist()

        # Notify outside the lock to avoid blocking on network I/O.
        channels = self._notify(request)
        with self._lock:
            request.notification_channels = channels
            self._persist()

        self._emit_audit(request, event="approval_requested")
        logger.info(
            "Approval request %s: agent=%s action=%s risk=%s",
            request.request_id,
            agent_id,
            action,
            risk_level.name,
        )
        return request

    def approve(
        self,
        request_id: str,
        decided_by: str,
        reason: str | None = None,
    ) -> ApprovalRequest:
        """Approve a pending request.

        Args:
            request_id: The request to approve.
            decided_by: Reviewer identity.
            reason: Optional reason for approval.

        Returns:
            Updated ApprovalRequest.

        Raises:
            ApprovalNotFoundError: If request_id is unknown.
            ApprovalExpiredError: If the request has expired.
            ApprovalAlreadyDecidedError: If the request is already terminal.
        """
        return self._decide(request_id, ApprovalStatus.APPROVED, decided_by, reason)

    def deny(
        self,
        request_id: str,
        decided_by: str,
        reason: str | None = None,
    ) -> ApprovalRequest:
        """Deny a pending request.

        Args:
            request_id: The request to deny.
            decided_by: Reviewer identity.
            reason: Optional reason for denial.

        Returns:
            Updated ApprovalRequest.

        Raises:
            ApprovalNotFoundError: If request_id is unknown.
            ApprovalExpiredError: If the request has expired.
            ApprovalAlreadyDecidedError: If the request is already terminal.
        """
        return self._decide(request_id, ApprovalStatus.DENIED, decided_by, reason)

    def cancel(
        self,
        request_id: str,
        decided_by: str,
        reason: str | None = None,
    ) -> ApprovalRequest:
        """Cancel a pending request (typically called by the requesting agent).

        Args:
            request_id: The request to cancel.
            decided_by: Who is cancelling (agent id or operator).
            reason: Optional reason.

        Returns:
            Updated ApprovalRequest.

        Raises:
            ApprovalNotFoundError: If request_id is unknown.
            ApprovalAlreadyDecidedError: If the request is already terminal.
        """
        return self._decide(request_id, ApprovalStatus.CANCELLED, decided_by, reason)

    def check_status(self, request_id: str) -> dict[str, Any]:
        """Get the current status of a request.

        Auto-expires stale requests before returning.

        Returns:
            Dict with request_id, status, decided_by, decided_at,
            decision_reason, and expired flag.

        Raises:
            ApprovalNotFoundError: If request_id is unknown.
        """
        with self._lock:
            req = self._requests.get(request_id)
            if req is None:
                raise ApprovalNotFoundError(request_id)
            self._expire_if_stale(req)
            return {
                "request_id": req.request_id,
                "status": req.status.name,
                "decided_by": req.decided_by,
                "decided_at": req.decided_at,
                "decision_reason": req.decision_reason,
                "expired": req.status == ApprovalStatus.EXPIRED,
            }

    def get_request(self, request_id: str) -> ApprovalRequest:
        """Get the full ApprovalRequest object.

        Raises:
            ApprovalNotFoundError: If request_id is unknown.
        """
        with self._lock:
            req = self._requests.get(request_id)
            if req is None:
                raise ApprovalNotFoundError(request_id)
            self._expire_if_stale(req)
            return req

    def wait_for_decision(
        self,
        request_id: str,
        timeout: float = 300.0,
        poll_interval: float = 1.0,
    ) -> dict[str, Any]:
        """Block until a decision is reached or timeout expires.

        Args:
            request_id: The request to wait on.
            timeout: Maximum seconds to wait.
            poll_interval: Seconds between status checks.

        Returns:
            Status dict (same as check_status).

        Raises:
            ApprovalNotFoundError: If request_id is unknown.
        """
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            status = self.check_status(request_id)
            if status["status"] != "PENDING":
                return status
            time.sleep(poll_interval)

        # Final check -- may have expired during the last sleep.
        return self.check_status(request_id)

    def list_pending(self) -> list[dict[str, Any]]:
        """List all pending approval requests (auto-expires stale first)."""
        with self._lock:
            self.expire_stale()
            return [req.to_dict() for req in self._requests.values() if req.is_pending]

    def list_all(self, limit: int | None = None) -> list[dict[str, Any]]:
        """List all requests (newest first)."""
        with self._lock:
            reqs = sorted(
                self._requests.values(),
                key=lambda r: r.created_at,
                reverse=True,
            )
            if limit:
                reqs = reqs[:limit]
            return [req.to_dict() for req in reqs]

    def expire_stale(self) -> int:
        """Expire all requests whose expiry time has passed.

        Returns:
            Number of requests expired.
        """
        now = datetime.now(timezone.utc)
        expired_count = 0
        with self._lock:
            for req in self._requests.values():
                if req.is_pending and req.expires_at is not None:
                    try:
                        exp = datetime.fromisoformat(req.expires_at)
                        if exp < now:
                            req.status = ApprovalStatus.EXPIRED
                            req.decided_at = now.isoformat()
                            req.decided_by = "system"
                            req.decision_reason = "Auto-expired (timeout)"
                            expired_count += 1
                            self._emit_audit(req, event="approval_expired")
                    except (ValueError, TypeError):
                        continue
            if expired_count > 0:
                self._persist()
        if expired_count:
            logger.info("Expired %d stale approval requests", expired_count)
        return expired_count

    def get_stats(self) -> dict[str, Any]:
        """Get aggregate statistics."""
        with self._lock:
            total = len(self._requests)
            by_status: dict[str, int] = {}
            by_risk: dict[str, int] = {}
            for req in self._requests.values():
                by_status[req.status.name] = by_status.get(req.status.name, 0) + 1
                by_risk[req.risk_level.name] = by_risk.get(req.risk_level.name, 0) + 1
            return {
                "total": total,
                "by_status": by_status,
                "by_risk": by_risk,
                "pending": by_status.get("PENDING", 0),
            }

    # ------------------------------------------------------------------
    # Policy helpers
    # ------------------------------------------------------------------

    @staticmethod
    def requires_approval(
        action: str,
        risk_level: RiskLevel,
        threshold: RiskLevel = RiskLevel.MEDIUM,
    ) -> bool:
        """Check if an action at a given risk level requires approval.

        Args:
            action: The action name (for logging/auditing).
            risk_level: The action's risk classification.
            threshold: Actions at or above this level require approval.

        Returns:
            True if approval is required.
        """
        return _RISK_ORDER[risk_level] >= _RISK_ORDER[threshold]

    def gate(
        self,
        agent_id: str,
        action: str,
        action_args: str,
        risk_level: RiskLevel,
        justification: str,
        threshold: RiskLevel = RiskLevel.MEDIUM,
        timeout_seconds: float | None = None,
    ) -> dict[str, Any]:
        """One-call gate: request approval if needed, block until decision.

        This is the convenience method for synchronous agent loops. If the
        risk level is below the threshold, returns immediately with APPROVED.
        Otherwise, creates a request, notifies, and blocks.

        Args:
            agent_id: Agent requesting the action.
            action: Action/tool name.
            action_args: Human-readable argument summary.
            risk_level: Risk classification.
            justification: Why this action is needed.
            threshold: Risk level at/above which approval is required.
            timeout_seconds: How long to wait for a decision.

        Returns:
            Dict with ``allowed`` (bool), ``status``, ``request_id``,
            and ``reason``.
        """
        if not self.requires_approval(action, risk_level, threshold):
            return {
                "allowed": True,
                "status": "AUTO_APPROVED",
                "request_id": None,
                "reason": f"Risk {risk_level.name} below threshold {threshold.name}",
            }

        req = self.request_approval(
            agent_id=agent_id,
            action=action,
            action_args=action_args,
            risk_level=risk_level,
            justification=justification,
            timeout_seconds=timeout_seconds,
        )

        effective_timeout = timeout_seconds or 300.0
        decision = self.wait_for_decision(req.request_id, timeout=effective_timeout)

        allowed = decision["status"] == "APPROVED"
        return {
            "allowed": allowed,
            "status": decision["status"],
            "request_id": req.request_id,
            "reason": decision.get("decision_reason"),
        }

    # ------------------------------------------------------------------
    # Notification hooks
    # ------------------------------------------------------------------

    def add_notification_hook(
        self,
        hook: Callable[[ApprovalRequest], None],
    ) -> None:
        """Register a custom notification callback.

        The callback receives the ApprovalRequest and is invoked on
        request creation. Exceptions are caught and logged.
        """
        if not hasattr(self, "_custom_hooks"):
            self._custom_hooks: list[Callable[[ApprovalRequest], None]] = []
        self._custom_hooks.append(hook)

    def _notify(self, request: ApprovalRequest) -> list[str]:
        """Send notifications via all configured channels.

        Returns:
            List of channel names that were notified successfully.
        """
        channels: list[str] = []

        if self._webhook_url:
            if self._send_webhook(self._webhook_url, request):
                channels.append("webhook")

        if self._slack_webhook_url:
            if self._send_slack(self._slack_webhook_url, request):
                channels.append("slack")

        if self._email_config:
            if self._send_email(self._email_config, request):
                channels.append("email")

        for hook in getattr(self, "_custom_hooks", []):
            try:
                hook(request)
                channels.append("custom")
            except Exception:
                logger.debug("Custom notification hook failed", exc_info=True)

        return channels

    @staticmethod
    def _send_webhook(url: str, request: ApprovalRequest) -> bool:
        """POST approval request as JSON to a generic webhook."""
        payload = json.dumps(
            {
                "event": "approval_requested",
                "request": request.to_dict(),
            }
        ).encode("utf-8")
        req = urlrequest.Request(
            url,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urlrequest.urlopen(req, timeout=10) as resp:  # nosec B310 - URL is operator-configured
                return resp.status == 200
        except (URLError, OSError, TimeoutError) as e:
            logger.warning("Webhook notification failed: %s", e)
            return False

    @staticmethod
    def _send_slack(webhook_url: str, request: ApprovalRequest) -> bool:
        """Send a Slack-formatted message to an incoming webhook."""
        risk_emoji = {
            RiskLevel.LOW: ":large_green_circle:",
            RiskLevel.MEDIUM: ":large_yellow_circle:",
            RiskLevel.HIGH: ":large_orange_circle:",
            RiskLevel.CRITICAL: ":red_circle:",
        }.get(request.risk_level, ":white_circle:")

        text = (
            f"{risk_emoji} *Approval Required* ({request.risk_level.name})\n"
            f"*Agent:* {request.agent_id}\n"
            f"*Action:* `{request.action}`\n"
            f"*Args:* {request.action_args}\n"
            f"*Justification:* {request.justification}\n"
            f"*Request ID:* `{request.request_id}`"
        )
        payload = json.dumps({"text": text}).encode("utf-8")
        req = urlrequest.Request(
            webhook_url,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urlrequest.urlopen(req, timeout=10) as resp:  # nosec B310 - URL is operator-configured
                return resp.status == 200
        except (URLError, OSError, TimeoutError) as e:
            logger.warning("Slack notification failed: %s", e)
            return False

    @staticmethod
    def _send_email(config: dict[str, Any], request: ApprovalRequest) -> bool:
        """Send an email notification via SMTP.

        Config keys: host, port, from, to, username, password, use_tls.
        """
        host = config.get("host")
        port = config.get("port", 587)
        sender = config.get("from")
        recipient = config.get("to")
        if not host or not sender or not recipient:
            logger.warning("Email notification skipped: incomplete config")
            return False

        subject = f"[HUMMBL] Approval Required: {request.action} ({request.risk_level.name})"
        body = (
            f"Approval request {request.request_id}\n\n"
            f"Agent: {request.agent_id}\n"
            f"Action: {request.action}\n"
            f"Arguments: {request.action_args}\n"
            f"Risk Level: {request.risk_level.name}\n"
            f"Justification: {request.justification}\n"
            f"Created: {request.created_at}\n"
        )
        if request.expires_at:
            body += f"Expires: {request.expires_at}\n"

        msg = f"From: {sender}\r\nTo: {recipient}\r\nSubject: {subject}\r\n\r\n{body}"

        try:
            use_tls = config.get("use_tls", True)
            if use_tls:
                context = ssl.create_default_context()
                with smtplib.SMTP(host, port, timeout=10) as server:
                    server.starttls(context=context)
                    if config.get("username") and config.get("password"):
                        server.login(config["username"], config["password"])
                    server.sendmail(sender, [recipient], msg)
            else:
                with smtplib.SMTP(host, port, timeout=10) as server:
                    if config.get("username") and config.get("password"):
                        server.login(config["username"], config["password"])
                    server.sendmail(sender, [recipient], msg)
            return True
        except (OSError, smtplib.SMTPException) as e:
            logger.warning("Email notification failed: %s", e)
            return False

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _decide(
        self,
        request_id: str,
        new_status: ApprovalStatus,
        decided_by: str,
        reason: str | None,
    ) -> ApprovalRequest:
        """Apply a decision to a request (shared by approve/deny/cancel)."""
        with self._lock:
            req = self._requests.get(request_id)
            if req is None:
                raise ApprovalNotFoundError(request_id)

            if req.is_terminal:
                raise ApprovalAlreadyDecidedError(request_id, req.status.name)

            self._expire_if_stale(req)
            if req.status == ApprovalStatus.EXPIRED:
                raise ApprovalExpiredError(request_id)

            req.status = new_status
            req.decided_by = decided_by
            req.decided_at = datetime.now(timezone.utc).isoformat()
            req.decision_reason = reason
            self._persist()

        event = {
            ApprovalStatus.APPROVED: "approval_granted",
            ApprovalStatus.DENIED: "approval_denied",
            ApprovalStatus.CANCELLED: "approval_cancelled",
        }[new_status]
        self._emit_audit(req, event=event)
        logger.info(
            "Approval %s: request=%s decided_by=%s reason=%s",
            new_status.name,
            request_id,
            decided_by,
            reason,
        )
        return req

    def _expire_if_stale(self, req: ApprovalRequest) -> None:
        """Expire a single request if its timeout has passed (no-op if terminal)."""
        if not req.is_pending or req.expires_at is None:
            return
        try:
            exp = datetime.fromisoformat(req.expires_at)
            if exp < datetime.now(timezone.utc):
                req.status = ApprovalStatus.EXPIRED
                req.decided_at = datetime.now(timezone.utc).isoformat()
                req.decided_by = "system"
                req.decision_reason = "Auto-expired (timeout)"
                self._emit_audit(req, event="approval_expired")
                self._persist()
        except (ValueError, TypeError) as exc:
            logger.warning("Could not parse expires_at for approval %s: %s", req.request_id, exc)

    def _emit_audit(self, req: ApprovalRequest, event: str) -> None:
        """Emit a governance audit event if an AuditLog is configured."""
        if self._audit_log is None:
            return
        try:
            self._audit_log.append(
                intent_id=req.metadata.get("intent_id", req.request_id),
                task_id=req.metadata.get("task_id", req.agent_id),
                tuple_type="SYSTEM",
                tuple_data={
                    "event": event,
                    "request_id": req.request_id,
                    "agent_id": req.agent_id,
                    "action": req.action,
                    "risk_level": req.risk_level.name,
                    "status": req.status.name,
                    "decided_by": req.decided_by,
                },
            )
        except Exception:
            logger.debug("Audit log emission failed for approval event", exc_info=True)

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def _state_file(self) -> Path:
        return self._state_dir / "approval_state.json"  # type: ignore[union-attr]

    def _persist(self) -> None:
        """Persist all requests to disk if state_dir is configured."""
        if self._state_dir is None:
            return
        try:
            self._state_dir.mkdir(parents=True, exist_ok=True)
            data = {
                "version": 1,
                "requests": [req.to_dict() for req in self._requests.values()],
            }
            tmp = self._state_file().with_suffix(".tmp")
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            tmp.replace(self._state_file())
            self._state_file().chmod(0o600)
        except OSError as e:
            logger.error("Failed to persist approval state: %s", e)

    def _load_from_disk(self) -> None:
        """Load persisted requests from disk."""
        if self._state_dir is None:
            return
        path = self._state_file()
        if not path.exists():
            return
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            for req_data in data.get("requests", []):
                req = ApprovalRequest.from_dict(req_data)
                self._requests[req.request_id] = req
            logger.info("Loaded %d approval requests from disk", len(self._requests))
        except (json.JSONDecodeError, KeyError, ValueError, OSError) as e:
            logger.error("Approval state file corrupt: %s", e)

    # ------------------------------------------------------------------
    # Background expiration
    # ------------------------------------------------------------------

    def _start_expire_loop(self, interval: int) -> None:
        """Start a background thread that periodically expires stale requests."""
        self._expire_thread = threading.Thread(
            target=self._expire_loop,
            args=(interval,),
            daemon=True,
            name="approval-expire",
        )
        self._expire_thread.start()

    def _expire_loop(self, interval: int) -> None:
        """Background loop calling expire_stale() at each interval."""
        while not self._expire_stop.wait(interval):
            try:
                self.expire_stale()
            except Exception:
                logger.debug("Background expire_stale failed", exc_info=True)

    def shutdown(self) -> None:
        """Stop the background expiration thread if running."""
        self._expire_stop.set()
        if self._expire_thread is not None:
            self._expire_thread.join(timeout=5)
