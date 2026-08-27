# Repository Audit: `governed-compression`

**Repository Path:** [`<repo-root>/PROJECTS\governed-compression`](https://github.com/hummbl-io/governed-compression)  
**Published PyPI Designation:** `governed-compression` (v0.1.0)  
**License:** Apache 2.0  
**Test Status:** ✅ **14/14 tests passing** (`pytest tests/ -v` passed in 0.23s)  
**Date:** August 2026  

---

## 1. What is `governed-compression`?

`governed-compression` is a specialized research and implementation surface for **governed vector and KV-cache quantization**. 

While mainstream machine learning focuses on unconstrained lossy compression (such as TurboQuant, QJL, and extreme 1-bit / 2-bit quantization), `governed-compression` introduces **tuple-native governance constraints** to verify that quantized KV caches and embeddings preserve semantic invariants and maintain bounded distortion error.

---

## 2. Dependencies & Air-Gap Profile

```toml
[project]
name = "governed-compression"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
  "numpy>=1.26",
  "hummbl-governance>=1.1.0",
]
```

- **Runtime Dependencies:**
  - `numpy >= 1.26`: Core numerical tensor operations, dot products, and floating-point quantization level computations.
  - `hummbl-governance >= 1.1.0`: Universal governance tuple integration and evidence receipt logging.
- **Air-Gap Profile:**
  - Unlike `hummbl-governance` and `base120` (which have 0 external dependencies), `governed-compression` is a **specialized ML compute library** and requires standard offline `numpy` wheels if deployed in an air-gapped numerical inference pipeline.

---

## 3. Current Architecture & Code Structure

```
governed_compression/
├── core/
│   ├── config.py         --> CompressionConfig (bits_per_channel, dimension, bounds)
│   └── reference.py      --> CPU Reference Baseline:
│                             • quantize_reference() [Linear & Multi-bit Binning]
│                             • approximate_dot() [Inner Product Estimation]
│                             • compute_mse() [Distortion Metric Calculation]
│
├── experiment/
│   └── tuples.py         --> CompressionRun Tuple Payload
│                             (run_id, method, bits_per_channel, dataset, benchmark)
│
├── bench/                --> Benchmarking harness
├── governance.yml        --> Machine-readable governance and invariant contract
└── cli.py                --> Command-line interface entry point
```

---

## 4. Test Suite Audit

Ran `python -m pytest tests/ -v`:
- ✅ `test_quantize_reference_preserves_shape` (PASSED)
- ✅ `test_quantize_reference_boundary_bit_widths[1.0 & 16.0]` (PASSED)
- ✅ `test_one_bit_quantization_uses_two_levels` (PASSED)
- ✅ `test_quantize_output_range` (PASSED)
- ✅ `test_quantize_uniform_vector_returns_zeros` (PASSED)
- ✅ `test_quantize_empty_vector_raises_value_error` (PASSED)
- ✅ `test_quantize_nan_input_preserves_nan_signal` (PASSED)
- ✅ `test_quantize_rejects_non_1d_vectors` (PASSED)
- ✅ `test_approximate_dot_returns_float` (PASSED)
- ✅ `test_approximate_dot_rejects_shape_mismatch` (PASSED)
- ✅ `test_mse_zero_for_identical` (PASSED)
- ✅ `test_mse_matches_expected_value_for_distinct_arrays` (PASSED)
- ✅ `test_mse_rejects_shape_mismatch` (PASSED)

---

## 5. Strategic Role in the HUMMBL Ecosystem

1. **Hardware-Efficient Edge Execution:** Enables high-context LLMs to run with compressed KV-caches under provable bounds on local edge nodes.
2. **Deterministic Quality Receipts:** Emits cryptographic `CompressionRun` governance tuples logging the exact distortion metrics (MSE, cosine drift) for every compressed layer, ensuring that quantizing models for cost savings does not introduce silent degradation.
