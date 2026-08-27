"""Configuration objects for governed compression experiments."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CompressionConfig:
    method: str
    bits_per_channel: float
    residual_enabled: bool = False

    def __post_init__(self) -> None:
        if self.bits_per_channel < 0:
            raise ValueError(f"bits_per_channel must be non-negative, got {self.bits_per_channel}")


DEFAULT_CONFIG = CompressionConfig(
    method="scalar_baseline",
    bits_per_channel=8.0,
    residual_enabled=False,
)
