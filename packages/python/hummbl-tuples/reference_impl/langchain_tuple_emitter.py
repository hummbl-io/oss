#!/usr/bin/env python3
"""Emit HUMMBL tuple envelopes from LangChain-style stream events.

This module deliberately does not import LangChain. The portability claim is
stronger if a plain event dictionary with LangChain's public event shape can be
converted without depending on the runtime internals.
"""

from __future__ import annotations

import hashlib
import json
from base64 import b64encode
from collections.abc import Mapping
from datetime import date, datetime, timezone
from typing import Any

JsonObject = dict[str, Any]


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _jsonable(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, bytes):
        return {"__type": "bytes", "base64": b64encode(value).decode("ascii")}
    if isinstance(value, datetime):
        iso_value = value.isoformat()
        return {"__type": "datetime", "iso": iso_value}
    if isinstance(value, date):
        return {"__type": "date", "iso": value.isoformat()}
    if isinstance(value, Mapping):
        return {
            str(key): _jsonable(subvalue)
            for key, subvalue in sorted(value.items(), key=lambda item: str(item[0]))
        }
    if isinstance(value, (set, frozenset)):
        items = [_jsonable(item) for item in value]
        return {
            "__type": type(value).__name__,
            "items": sorted(items, key=_canonical_json),
        }
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    raise TypeError(
        f"Unsupported non-JSON-native value for stable tuple ID: {type(value).__name__}"
    )


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def _stable_id(record: JsonObject) -> str:
    stable = {key: value for key, value in record.items() if key not in {"id", "time"}}
    payload = _canonical_json(stable)
    return "lc-" + hashlib.sha256(payload.encode("utf-8")).hexdigest()[:24]


def _require_string_event(event: Mapping[str, Any]) -> str:
    event_name = event.get("event")
    if not isinstance(event_name, str) or not event_name:
        raise ValueError("LangChain event must include a non-empty string 'event'")
    return event_name


def _tuple_type_for_event(event_name: str) -> str:
    if event_name.endswith("_end") or event_name.endswith("_error"):
        return "EVIDENCE"
    return "SYSTEM"


def emit_langchain_event(
    event: Mapping[str, Any],
    *,
    intent_id: str,
    task_id: str,
    time: str | None = None,
) -> JsonObject:
    """Convert one LangChain-style event dictionary into a HUMMBL tuple.

    Expected input shape follows LangChain stream events loosely:
    `event`, `name`, `run_id`, `parent_ids`, `tags`, `metadata`, and `data`.
    Unknown fields are preserved under `tuple_data.raw_event`.
    """

    if not intent_id:
        raise ValueError("intent_id must be non-empty")
    if not task_id:
        raise ValueError("task_id must be non-empty")

    event_name = _require_string_event(event)
    tuple_type = _tuple_type_for_event(event_name)
    known_keys = {"event", "name", "run_id", "parent_ids", "tags", "metadata", "data"}

    tuple_data: JsonObject = {
        "event": event_name,
        "adapter": "langchain",
    }
    for source_key, target_key in (
        ("name", "runnable_name"),
        ("run_id", "source_run_id"),
        ("parent_ids", "source_parent_ids"),
        ("tags", "tags"),
        ("metadata", "metadata"),
        ("data", "data"),
    ):
        if source_key in event:
            tuple_data[target_key] = _jsonable(event[source_key])

    raw_event = {key: _jsonable(value) for key, value in event.items() if key not in known_keys}
    if raw_event:
        tuple_data["raw_event"] = raw_event

    record: JsonObject = {
        "tuple_type": tuple_type,
        "time": time or _utc_now(),
        "state": "ok",
        "drift": 0,
        "tier": 1,
        "agent": "langchain",
        "tool": "stream-events",
        "intent_id": intent_id,
        "task_id": task_id,
        "tuple_data": tuple_data,
    }
    record["id"] = _stable_id(record)
    return record


class LangChainTupleEmitter:
    """Small stateful wrapper for repeated events from one task lineage."""

    def __init__(self, *, intent_id: str, task_id: str) -> None:
        if not intent_id:
            raise ValueError("intent_id must be non-empty")
        if not task_id:
            raise ValueError("task_id must be non-empty")
        self.intent_id = intent_id
        self.task_id = task_id

    def emit(self, event: Mapping[str, Any], *, time: str | None = None) -> JsonObject:
        return emit_langchain_event(
            event,
            intent_id=self.intent_id,
            task_id=self.task_id,
            time=time,
        )

    def emit_many(
        self, events: list[Mapping[str, Any]], *, time: str | None = None
    ) -> list[JsonObject]:
        return [self.emit(event, time=time) for event in events]
