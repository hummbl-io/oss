"""CPU reference baseline for early experiments."""

from __future__ import annotations

import numpy as np

from governed_compression.core.config import CompressionConfig


def quantize_reference(vector: np.ndarray, config: CompressionConfig) -> np.ndarray:
    """Return a trivial reference quantized view.

    This is intentionally simple. It provides a correctness anchor and
    benchmark baseline before method-specific implementations are added.
    """
    if vector.ndim != 1:
        raise ValueError("reference quantizer expects a 1D vector")
    levels = max(2, round(2 ** min(config.bits_per_channel, 16)))
    vmin = float(vector.min())
    vmax = float(vector.max())
    if vmax == vmin:
        return np.zeros_like(vector)
    scaled = (vector - vmin) / (vmax - vmin)
    bins = np.round(scaled * (levels - 1)) / (levels - 1)
    return bins.astype(np.float32)


def approximate_dot(a: np.ndarray, b: np.ndarray) -> float:
    if a.shape != b.shape:
        raise ValueError("vectors must have the same shape")
    return float(np.dot(a.astype(np.float32), b.astype(np.float32)))
