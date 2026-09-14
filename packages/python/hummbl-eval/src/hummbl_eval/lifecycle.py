"""Append-only Question lifecycle projection."""

from __future__ import annotations

from dataclasses import dataclass


class LifecycleError(ValueError):
    """Question events do not form a valid lifecycle."""


@dataclass(frozen=True, slots=True)
class QuestionEvent:
    event_type: str
    text: str | None = None
    answer_ref: str | None = None
    reason: str | None = None


@dataclass(frozen=True, slots=True)
class QuestionState:
    question_id: str
    original_text: str
    current_text: str
    status: str
    events: tuple[QuestionEvent, ...]


def replay_question(question_id: str, events: list[QuestionEvent]) -> QuestionState:
    """Derive current Question state without rewriting original events."""

    if not events or events[0].event_type != "CREATED" or not events[0].text:
        raise LifecycleError("first event must create the question with text")
    original = events[0].text
    current = original
    status = "open"
    for index, event in enumerate(events[1:], start=1):
        if event.event_type == "REPHRASED":
            if not event.text:
                raise LifecycleError(f"event {index}: rephrase requires text")
            current = event.text
        elif event.event_type == "PARTIAL_ANSWER":
            if not event.answer_ref:
                raise LifecycleError(f"event {index}: partial answer requires reference")
            status = "partially_answered"
        elif event.event_type == "ANSWERED":
            if not event.answer_ref:
                raise LifecycleError(f"event {index}: answer requires reference")
            status = "answered"
        elif event.event_type == "REOPENED":
            if status not in {"answered", "partially_answered", "deferred"}:
                raise LifecycleError(f"event {index}: only a closed/scoped question can reopen")
            status = "open"
        elif event.event_type == "DEFERRED":
            if not event.reason:
                raise LifecycleError(f"event {index}: deferral requires reason")
            status = "deferred"
        else:
            raise LifecycleError(f"event {index}: unsupported event {event.event_type}")
    return QuestionState(question_id, original, current, status, tuple(events))
