"""Inbound normalizer — envelope -> authenticated remote_write.

The single component every channel shares:
  allowlist -> intent parse -> type policy -> dedup -> post -> spool.

Fail-safe directions:
  - unknown sender  -> quarantine as `<channel>-ingress` (or drop)
  - unproven privilege -> downgrade to STATUS, annotate attempted_type
  - bridge down      -> local spool for later replay (never a shadow bus)
"""

from __future__ import annotations

import os
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from ..authority import PRIVILEGED_TYPES
from ..bridge_client import post_to_remote_bus_result
from ..spool import enqueue_outbound_record
from .allowlist import Allowlist
from .envelope import BusIntent, InboundEnvelope, parse_bus_intent

# Types that require in-body PIN proof from an allowlisted sender.
# PRIVILEGED_TYPES (DECISION/DIRECTIVE) also belong here — channels can
# never produce Ed25519 principal proofs, so they always downgrade.
DEFAULT_ELEVATED_TYPES = frozenset({"VETO", "APPROVE", "REJECT"} | PRIVILEGED_TYPES)

MAX_MESSAGE_CHARS = 2000  # channel bodies are short; guard the bus log


@dataclass(frozen=True, slots=True)
class IngressResult:
    status: str  # "posted" | "spooled" | "dropped" | "rejected"
    request_id: str
    bus_from: str
    msg_type: str  # effective type after policy
    requested_type: str
    detail: str = ""


PostFn = Callable[..., dict]


def _default_post(
    host: str, from_agent: str, to_agent: str, msg_type: str, message: str, **kw
) -> dict:
    return post_to_remote_bus_result(
        host, from_agent, to_agent, msg_type, message, **kw
    )


class Normalizer:
    def __init__(
        self,
        allowlist: Allowlist,
        *,
        bridge_host: str = "localhost",
        bridge_port: int = 8080,
        origin_machine: str | None = None,
        elevated_types: frozenset[str] = DEFAULT_ELEVATED_TYPES,
        post_fn: PostFn = _default_post,
        spool_dir: str | Path | None = None,
    ):
        self.allowlist = allowlist
        self.bridge_host = bridge_host
        self.bridge_port = bridge_port
        self.origin_machine = origin_machine or os.environ.get(
            "BUS_INGRESS_HOST", "ingress"
        )
        self.elevated_types = elevated_types
        self._post = post_fn
        self.spool_dir = spool_dir

    def handle(self, env: InboundEnvelope) -> IngressResult:
        errs = env.validate()
        if errs:
            return IngressResult(
                "rejected", env.request_id, "", "", "", "; ".join(errs)
            )

        policy = self.allowlist.lookup(env.sender_addr, env.channel)
        if policy is None:
            return IngressResult(
                "dropped", env.request_id, "", "", "", "unknown sender"
            )

        intent = parse_bus_intent(env.body)
        intent = self._apply_type_policy(intent, policy)

        message = self._compose_message(env, intent)
        try:
            result = self._post(
                self.bridge_host,
                policy.bus_from,
                intent.to,
                intent.msg_type,
                message,
                request_id=env.request_id,
                origin_machine=self.origin_machine,
                port=self.bridge_port,
            )
        except Exception:
            result = {"ok": False}  # raised = transient -> spool below

        if result.get("ok"):
            return IngressResult(
                "posted",
                env.request_id,
                policy.bus_from,
                intent.msg_type,
                intent.requested_type,
            )
        if result.get("permanent_error"):
            # 409 = idempotency key already posted (e.g. a redundant
            # subscriber won the race) — dedup success, not failure.
            status = (
                "duplicate" if result.get("status_code") == 409 else "rejected"
            )
            return IngressResult(
                status,
                env.request_id,
                policy.bus_from,
                intent.msg_type,
                intent.requested_type,
                str(result.get("error", "bridge rejected")),
            )

        # Transient failure -> spool for replay (post-downgrade types are
        # never privileged, so this cannot raise PermissionError).
        try:
            path = enqueue_outbound_record(
                sender=policy.bus_from,
                recipient=intent.to,
                msg_type=intent.msg_type,
                message=message,
                request_id=env.request_id,
                origin_machine=self.origin_machine,
                spool_dir=self.spool_dir,
            )
            return IngressResult(
                "spooled",
                env.request_id,
                policy.bus_from,
                intent.msg_type,
                intent.requested_type,
                str(path),
            )
        except Exception as e:
            return IngressResult(
                "rejected",
                env.request_id,
                policy.bus_from,
                intent.msg_type,
                intent.requested_type,
                f"bridge unreachable and spool failed: {e}",
            )

    def _apply_type_policy(self, intent: BusIntent, policy) -> BusIntent:
        """Elevated types need a verified PIN; else downgrade to STATUS."""
        if intent.msg_type not in self.elevated_types:
            return intent
        if policy.pin_matches(intent.pin):
            return intent
        note = f"[attempted_type={intent.msg_type} unproven] "
        return BusIntent(
            "STATUS",
            intent.to,
            note + intent.message,
            intent.requested_type,
            intent.pin,
        )

    def _compose_message(self, env: InboundEnvelope, intent: BusIntent) -> str:
        # Bridge tokens bind `from=` to their agent identity, so sender
        # provenance must ride in the body for audit.
        tags = f"via={env.channel} host={self.origin_machine} sender={env.sender_addr}"
        body = intent.message[: MAX_MESSAGE_CHARS - len(tags) - 8]
        return f"{tags} {body}".strip()
