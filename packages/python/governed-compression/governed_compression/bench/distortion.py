"""Distortion metrics for reference experiments."""

from __future__ import annotations

import numpy as np


def mean_squared_error(reference: np.ndarray, candidate: np.ndarray) -> float:
    if reference.shape != candidate.shape:
        raise ValueError("arrays must have the same shape")
    if reference.size == 0:
        raise ValueError("arrays must be non-empty")
    diff = reference.astype(np.float32) - candidate.astype(np.float32)
    return float(np.mean(diff * diff))
