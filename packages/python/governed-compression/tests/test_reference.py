from __future__ import annotations

import numpy as np
import pytest

from governed_compression.bench.distortion import mean_squared_error
from governed_compression.core.config import CompressionConfig
from governed_compression.core.reference import approximate_dot, quantize_reference


def test_quantize_reference_preserves_shape() -> None:
    vector = np.array([0.1, 0.4, 0.7], dtype=np.float32)
    config = CompressionConfig(method="scalar_baseline", bits_per_channel=4.0)

    result = quantize_reference(vector, config)

    assert result.shape == vector.shape


@pytest.mark.parametrize("bits_per_channel", [1.0, 16.0])
def test_quantize_reference_boundary_bit_widths(bits_per_channel: float) -> None:
    vector = np.array([-1.0, -0.25, 0.25, 1.0], dtype=np.float32)
    config = CompressionConfig(
        method="scalar_baseline",
        bits_per_channel=bits_per_channel,
    )

    result = quantize_reference(vector, config)

    assert result.dtype == np.float32
    assert result.shape == vector.shape
    assert float(result.min()) >= 0.0
    assert float(result.max()) <= 1.0


def test_one_bit_quantization_uses_two_levels() -> None:
    vector = np.array([0.0, 0.24, 0.76, 1.0], dtype=np.float32)
    config = CompressionConfig(method="scalar_baseline", bits_per_channel=1.0)

    result = quantize_reference(vector, config)

    np.testing.assert_array_equal(
        result,
        np.array([0.0, 0.0, 1.0, 1.0], dtype=np.float32),
    )


def test_quantize_output_range() -> None:
    rng = np.random.default_rng(42)
    vector = rng.standard_normal(256).astype(np.float32)
    config = CompressionConfig(method="scalar_baseline", bits_per_channel=4.0)

    result = quantize_reference(vector, config)

    assert float(result.min()) >= 0.0
    assert float(result.max()) <= 1.0


def test_quantize_uniform_vector_returns_zeros() -> None:
    vector = np.full(5, 3.14, dtype=np.float32)
    config = CompressionConfig(method="scalar_baseline", bits_per_channel=8.0)

    result = quantize_reference(vector, config)

    np.testing.assert_array_equal(result, np.zeros(5, dtype=np.float32))


def test_quantize_empty_vector_raises_value_error() -> None:
    config = CompressionConfig(method="scalar_baseline", bits_per_channel=8.0)

    with pytest.raises(ValueError):
        quantize_reference(np.array([], dtype=np.float32), config)


def test_quantize_nan_input_preserves_nan_signal() -> None:
    vector = np.array([0.0, np.nan, 1.0], dtype=np.float32)
    config = CompressionConfig(method="scalar_baseline", bits_per_channel=4.0)

    result = quantize_reference(vector, config)

    assert np.isnan(result).all()


def test_quantize_rejects_non_1d_vectors() -> None:
    config = CompressionConfig(method="scalar_baseline", bits_per_channel=8.0)

    with pytest.raises(ValueError, match="1D vector"):
        quantize_reference(np.zeros((2, 2), dtype=np.float32), config)


def test_approximate_dot_returns_float() -> None:
    left = np.array([1.0, 2.0], dtype=np.float32)
    right = np.array([3.0, 4.0], dtype=np.float32)

    result = approximate_dot(left, right)

    assert isinstance(result, float)
    assert result == 11.0


def test_approximate_dot_rejects_shape_mismatch() -> None:
    with pytest.raises(ValueError, match="same shape"):
        approximate_dot(
            np.array([1.0, 2.0], dtype=np.float32),
            np.array([1.0], dtype=np.float32),
        )


def test_mse_zero_for_identical() -> None:
    vector = np.array([1.0, 2.0, 3.0], dtype=np.float32)

    assert mean_squared_error(vector, vector) == 0.0


def test_mse_matches_expected_value_for_distinct_arrays() -> None:
    reference = np.array([1.0, 2.0, 3.0], dtype=np.float32)
    candidate = np.array([2.0, 4.0, 6.0], dtype=np.float32)

    assert mean_squared_error(reference, candidate) == pytest.approx(14.0 / 3.0)


def test_mse_rejects_shape_mismatch() -> None:
    with pytest.raises(ValueError, match="same shape"):
        mean_squared_error(
            np.array([1.0, 2.0], dtype=np.float32),
            np.array([1.0], dtype=np.float32),
        )


# ---------------------------------------------------------------------------
# CompressionConfig validation
# ---------------------------------------------------------------------------

def test_config_rejects_negative_bits_per_channel() -> None:
    with pytest.raises(ValueError, match="non-negative"):
        CompressionConfig(method="scalar_baseline", bits_per_channel=-1.0)


def test_config_accepts_zero_bits_per_channel() -> None:
    config = CompressionConfig(method="scalar_baseline", bits_per_channel=0.0)
    assert config.bits_per_channel == 0.0


def test_default_config_has_expected_values() -> None:
    from governed_compression.core.config import DEFAULT_CONFIG
    assert DEFAULT_CONFIG.method == "scalar_baseline"
    assert DEFAULT_CONFIG.bits_per_channel == 8.0
    assert DEFAULT_CONFIG.residual_enabled is False


# ---------------------------------------------------------------------------
# CompressionRun tuple
# ---------------------------------------------------------------------------

def test_compression_run_to_dict() -> None:
    from governed_compression.experiment.tuples import CompressionRun
    run = CompressionRun(
        run_id="R1", method="scalar_baseline", bits_per_channel=4.0,
        dataset="synthetic", benchmark="mse",
    )
    d = run.to_dict()
    assert d["run_id"] == "R1"
    assert d["method"] == "scalar_baseline"
    assert d["bits_per_channel"] == 4.0
    assert d["dataset"] == "synthetic"
    assert d["benchmark"] == "mse"


def test_compression_run_is_frozen() -> None:
    from governed_compression.experiment.tuples import CompressionRun
    run = CompressionRun(
        run_id="R1", method="scalar_baseline", bits_per_channel=4.0,
        dataset="synthetic", benchmark="mse",
    )
    with pytest.raises((AttributeError, TypeError)):
        run.run_id = "R2"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

def test_mse_with_empty_arrays_raises() -> None:
    with pytest.raises(ValueError):
        mean_squared_error(
            np.array([], dtype=np.float32),
            np.array([], dtype=np.float32),
        )


def test_approximate_dot_larger_vectors() -> None:
    a = np.arange(10, dtype=np.float32)
    b = np.ones(10, dtype=np.float32)
    assert approximate_dot(a, b) == 45.0
