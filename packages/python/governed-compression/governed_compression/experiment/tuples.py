"""Tuple-like experiment run payloads for governed compression."""

from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class CompressionRun:
    run_id: str
    method: str
    bits_per_channel: float
    dataset: str
    benchmark: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)
