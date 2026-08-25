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

"""
Statistical Framework for Benchmark Evaluation

Provides bootstrap confidence intervals, significance testing, and uncertainty
quantification for benchmark metrics. Following industry standards from
Spark-LLM-Eval, OmniEvalKit, and philosophy-bench.

Author: HUMMBL Fleet
Date: 2026-05-30
License: MIT
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import Dict, List, Tuple, Union
from enum import Enum


class CIMethod(Enum):
    """Confidence interval calculation methods."""
    PERCENTILE = "percentile"
    WILSON = "wilson"
    T_INTERVAL = "t_interval"
    BCA = "bca"


@dataclass
class UncertaintyQuantification:
    """Standard uncertainty representation for benchmark metrics.
    
    Attributes:
        value: Point estimate of the metric
        confidence_interval: (lower, upper) bounds at specified confidence level
        confidence_level: Confidence level (e.g., 0.95 for 95% CI)
        sample_size: Number of samples used for calculation
        method: Method used to compute confidence interval
    """
    value: float
    confidence_interval: Tuple[float, float]
    confidence_level: float
    sample_size: int
    method: str
    
    def is_significant(self, threshold: float = 0.0) -> bool:
        """Check if value is significantly different from threshold."""
        lower, upper = self.confidence_interval
        return not (lower <= threshold <= upper)
    
    def to_dict(self) -> Dict[str, Union[float, Tuple[float, float], str, int]]:
        """Serialize to dictionary."""
        return {
            "value": self.value,
            "ci_lower": self.confidence_interval[0],
            "ci_upper": self.confidence_interval[1],
            "confidence_level": self.confidence_level,
            "sample_size": self.sample_size,
            "method": self.method
        }


def bootstrap_ci(
    values: List[float],
    confidence_level: float = 0.95,
    n_bootstrap: int = 10000,
    method: CIMethod = CIMethod.PERCENTILE
) -> UncertaintyQuantification:
    """Calculate bootstrap confidence interval for a list of values.
    
    Args:
        values: List of metric values
        confidence_level: Confidence level (default 0.95 for 95% CI)
        n_bootstrap: Number of bootstrap iterations (default 10000)
        method: CI calculation method (default percentile)
    
    Returns:
        UncertaintyQuantification with point estimate and CI bounds
    
    Raises:
        ValueError: If values list is empty or has insufficient samples
    """
    if not values:
        raise ValueError("Cannot compute CI for empty values list")
    
    if len(values) < 2:
        raise ValueError("Need at least 2 samples for bootstrap CI")
    
    n = len(values)
    point_estimate = sum(values) / n
    
    if method == CIMethod.PERCENTILE:
        # Percentile bootstrap (simple, robust)
        boot_means = []
        for _ in range(n_bootstrap):
            sample = random.choices(values, k=n)  # nosec B311 — statistical sampling, not cryptographic
            boot_means.append(sum(sample) / n)

        alpha = 1 - confidence_level
        lower = sorted(boot_means)[int(n_bootstrap * alpha / 2)]
        upper = sorted(boot_means)[int(n_bootstrap * (1 - alpha / 2))]

    elif method == CIMethod.BCA:
        # Bias-corrected and accelerated bootstrap
        # More accurate for small samples or skewed distributions
        boot_means = []
        for _ in range(n_bootstrap):
            sample = random.choices(values, k=n)  # nosec B311 — statistical sampling, not cryptographic
            boot_means.append(sum(sample) / n)

        # Calculate bias correction (z0)
        prop_less = sum(1 for bm in boot_means if bm < point_estimate) / n_bootstrap
        z0 = _norm_ppf(prop_less)
        
        # Calculate acceleration (a) - simplified version
        # Full BCa requires jackknife estimation; using approximation
        # Simplified - full implementation would compute jackknife acceleration
        
        # Adjust percentiles
        alpha = 1 - confidence_level
        z_alpha = _norm_ppf(alpha / 2)
        z_1minus_alpha = _norm_ppf(1 - alpha / 2)
        
        # Bias-corrected percentiles
        alpha1 = _norm_cdf(2 * z0 + z_alpha)
        alpha2 = _norm_cdf(2 * z0 + z_1minus_alpha)
        
        lower = sorted(boot_means)[int(n_bootstrap * alpha1)]
        upper = sorted(boot_means)[int(n_bootstrap * alpha2)]
        
    else:
        raise ValueError(f"Unsupported CI method: {method}")
    
    return UncertaintyQuantification(
        value=point_estimate,
        confidence_interval=(lower, upper),
        confidence_level=confidence_level,
        sample_size=n,
        method=method.value
    )


def wilson_score_interval(
    p: float,
    n: int,
    confidence_level: float = 0.95
) -> UncertaintyQuantification:
    """Calculate Wilson score confidence interval for proportions.
    
    Recommended over normal approximation for small samples or extreme
    proportions (near 0 or 1). From OBLITERATUS abliteration research.
    
    Args:
        p: Observed proportion (0.0 to 1.0)
        n: Sample size
        confidence_level: Confidence level (default 0.95)
    
    Returns:
        UncertaintyQuantification with Wilson score CI bounds
    """
    if n == 0:
        return UncertaintyQuantification(
            value=0.0,
            confidence_interval=(0.0, 0.0),
            confidence_level=confidence_level,
            sample_size=0,
            method="wilson"
        )
    
    if p < 0 or p > 1:
        raise ValueError(f"Proportion must be between 0 and 1, got {p}")
    
    # Z-score for confidence level
    z_map = {0.90: 1.645, 0.95: 1.96, 0.99: 2.576}
    z = z_map.get(confidence_level, 1.96)
    
    denominator = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denominator
    spread = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denominator
    
    ci_lower = max(0.0, center - spread)
    ci_upper = min(1.0, center + spread)
    
    return UncertaintyQuantification(
        value=p,
        confidence_interval=(ci_lower, ci_upper),
        confidence_level=confidence_level,
        sample_size=n,
        method="wilson"
    )


def bootstrap_test(
    values_a: List[float],
    values_b: List[float],
    n_bootstrap: int = 10000,
    confidence_level: float = 0.95
) -> Dict[str, Union[float, bool, str]]:
    """Bootstrap hypothesis test for difference in means.
    
    Non-parametric test that works with small samples and non-normal
    distributions. Tests whether the difference in means is statistically
    significant.
    
    Args:
        values_a: First sample of metric values
        values_b: Second sample of metric values
        n_bootstrap: Number of bootstrap iterations
        confidence_level: Confidence level for significance test
    
    Returns:
        Dictionary with test results including observed difference,
        p-value, significance status, and confidence level
    """
    if not values_a or not values_b:
        raise ValueError("Both samples must be non-empty")
    
    observed_diff = sum(values_a) / len(values_a) - sum(values_b) / len(values_b)
    
    # Pooled samples for permutation test
    pooled = values_a + values_b
    n_a = len(values_a)
    
    extreme_count = 0
    for _ in range(n_bootstrap):
        shuffled = random.sample(pooled, len(pooled))  # nosec B311 — permutation test, not cryptographic
        sample_a = shuffled[:n_a]
        sample_b = shuffled[n_a:]
        boot_diff = sum(sample_a) / len(sample_a) - sum(sample_b) / len(sample_b)
        if abs(boot_diff) >= abs(observed_diff):
            extreme_count += 1
    
    p_value = extreme_count / n_bootstrap
    significant = p_value < (1 - confidence_level)
    
    return {
        "observed_diff": observed_diff,
        "p_value": p_value,
        "significant": significant,
        "confidence": f"{int(confidence_level * 100)}%" if significant else "not significant"
    }


def _norm_ppf(p: float) -> float:
    """Normal distribution percent point function (approximation).
    
    Uses Beasley-Springer-Moro approximation for accurate quantiles.
    """
    if p <= 0 or p >= 1:
        raise ValueError("p must be between 0 and 1 (exclusive)")
    
    if p == 0.5:
        return 0.0
    
    # Coefficients for Beasley-Springer-Moro approximation
    a = [-3.969683028665376e+01, 2.209460984245205e+02,
          -2.759285104469687e+02, 1.383577518672690e+02,
          -3.066479806614716e+01, 2.506628277459239e+00]
    b = [-5.447609879822406e+01, 1.615858368580409e+02,
          -1.556989798598866e+02, 6.680131188771972e+01,
          -1.328068155288572e+00]
    
    q = p - 0.5
    if abs(q) <= 0.425:
        r = 0.180625 - q * q
        numer = a[0] * r + a[1]
        numer = numer * r + a[2]
        numer = numer * r + a[3]
        numer = numer * r + a[4]
        numer = numer * r + a[5]
        denom = b[0] * r + b[1]
        denom = denom * r + b[2]
        denom = denom * r + b[3]
        denom = denom * r + b[4]
        return q * numer / denom
    
    r = q if q > 0 else 1 - q
    r = math.sqrt(-math.log(r))
    
    if r <= 5:
        r = r - 1.6
        numer = a[0] * r + a[1]
        numer = numer * r + a[2]
        numer = numer * r + a[3]
        numer = numer * r + a[4]
        numer = numer * r + a[5]
        denom = b[0] * r + b[1]
        denom = denom * r + b[2]
        denom = denom * r + b[3]
        denom = denom * r + b[4]
        return numer / denom
    else:
        r = r - 5.0
        numer = a[0] * r + a[1]
        numer = numer * r + a[2]
        numer = numer * r + a[3]
        numer = numer * r + a[4]
        numer = numer * r + a[5]
        denom = b[0] * r + b[1]
        denom = denom * r + b[2]
        denom = denom * r + b[3]
        denom = denom * r + b[4]
        return numer / denom


def _norm_cdf(x: float) -> float:
    """Normal distribution cumulative distribution function (approximation).
    
    Uses the error function approximation.
    """
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def calculate_effect_size(
    values_a: List[float],
    values_b: List[float]
) -> Dict[str, float]:
    """Calculate Cohen's d effect size for two samples.
    
    Effect size measures practical significance (magnitude of difference)
    independent of sample size. Complements statistical significance testing.
    
    Args:
        values_a: First sample of metric values
        values_b: Second sample of metric values
    
    Returns:
        Dictionary with Cohen's d and interpretation
    """
    if not values_a or not values_b:
        raise ValueError("Both samples must be non-empty")
    
    mean_a = sum(values_a) / len(values_a)
    mean_b = sum(values_b) / len(values_b)
    
    # Pooled standard deviation
    var_a = sum((x - mean_a) ** 2 for x in values_a) / (len(values_a) - 1)
    var_b = sum((x - mean_b) ** 2 for x in values_b) / (len(values_b) - 1)
    
    n_a = len(values_a)
    n_b = len(values_b)
    pooled_std = math.sqrt(((n_a - 1) * var_a + (n_b - 1) * var_b) / (n_a + n_b - 2))
    
    if pooled_std == 0:
        return {"cohens_d": 0.0, "interpretation": "no effect (no variance)"}
    
    cohens_d = (mean_a - mean_b) / pooled_std
    
    # Interpret effect size
    abs_d = abs(cohens_d)
    if abs_d < 0.2:
        interpretation = "small effect"
    elif abs_d < 0.5:
        interpretation = "medium effect"
    elif abs_d < 0.8:
        interpretation = "large effect"
    else:
        interpretation = "very large effect"
    
    return {"cohens_d": cohens_d, "interpretation": interpretation}


def ks_test(
    values_a: List[float],
    values_b: List[float]
) -> Dict[str, Union[float, bool, str]]:
    """Kolmogorov-Smirnov test for distribution comparison.
    
    Non-parametric test to determine if two samples come from the same
    distribution. Tests the null hypothesis that both samples are drawn
    from the same continuous distribution.
    
    Args:
        values_a: First sample of values
        values_b: Second sample of values
    
    Returns:
        Dictionary with KS statistic, p-value, and significance status
    """
    if not values_a or not values_b:
        raise ValueError("Both samples must be non-empty")
    
    # Sort both samples
    sorted_a = sorted(values_a)
    sorted_b = sorted(values_b)
    
    # Compute empirical CDFs
    def _ecdf(values, x):
        return sum(1 for v in values if v <= x) / len(values)
    
    # Find KS statistic (maximum absolute difference between CDFs)
    all_values = sorted(set(sorted_a + sorted_b))
    ks_statistic = 0.0
    
    for x in all_values:
        cdf_a = _ecdf(sorted_a, x)
        cdf_b = _ecdf(sorted_b, x)
        diff = abs(cdf_a - cdf_b)
        ks_statistic = max(ks_statistic, diff)
    
    # Approximate p-value using KS distribution approximation
    # For large samples, use asymptotic distribution
    n_a = len(values_a)
    n_b = len(values_b)
    n_eff = (n_a * n_b) / (n_a + n_b)
    
    # Critical values for common significance levels
    critical_values = {
        0.10: 1.224 / math.sqrt(n_eff),
        0.05: 1.358 / math.sqrt(n_eff),
        0.01: 1.628 / math.sqrt(n_eff)
    }
    
    # Determine significance at 0.05 level
    critical_05 = critical_values[0.05]
    significant = ks_statistic > critical_05
    
    # Approximate p-value (simplified)
    p_value = 2 * math.exp(-2 * n_eff * ks_statistic ** 2)
    p_value = min(p_value, 1.0)
    
    return {
        "ks_statistic": ks_statistic,
        "p_value": p_value,
        "significant": significant,
        "interpretation": "distributions differ" if significant else "distributions similar"
    }


def population_stability_index(
    baseline: List[float],
    current: List[float],
    bins: int = 10
) -> Dict[str, Union[float, str]]:
    """Calculate Population Stability Index (PSI) for drift detection.
    
    PSI measures the shift in distribution between baseline and current
    data. Commonly used in model monitoring to detect feature drift.
    
    PSI < 0.1: No significant drift
    PSI 0.1-0.25: Moderate drift
    PSI > 0.25: Significant drift
    
    Args:
        baseline: Baseline distribution values
        current: Current distribution values
        bins: Number of bins for histogram calculation
    
    Returns:
        Dictionary with PSI value and drift interpretation
    """
    if not baseline or not current:
        raise ValueError("Both baseline and current must be non-empty")
    
    # Determine bin edges from baseline
    min_val = min(min(baseline), min(current))
    max_val = max(max(baseline), max(current))
    
    # Add small epsilon to avoid division by zero
    epsilon = 1e-10
    bin_edges = [min_val + i * (max_val - min_val) / bins for i in range(bins + 1)]
    bin_edges[-1] = max_val + epsilon  # Ensure max value is included
    
    # Calculate expected and observed frequencies
    expected = []
    observed = []
    
    for i in range(bins):
        lower = bin_edges[i]
        upper = bin_edges[i + 1]
        
        expected_count = sum(1 for v in baseline if lower <= v < upper)
        observed_count = sum(1 for v in current if lower <= v < upper)
        
        # Add small constant to avoid division by zero
        expected.append(expected_count + epsilon)
        observed.append(observed_count + epsilon)
    
    # Calculate PSI
    psi = 0.0
    for exp, obs in zip(expected, observed):
        if exp == 0:
            continue
        psi += (obs - exp) * math.log(obs / exp)
    
    # Interpret PSI value
    if psi < 0.1:
        interpretation = "no significant drift"
    elif psi < 0.25:
        interpretation = "moderate drift"
    else:
        interpretation = "significant drift"
    
    return {
        "psi": psi,
        "interpretation": interpretation
    }


def wilson_score_ci(
    successes: int,
    n: int,
    confidence: float = 0.95
) -> Dict[str, float]:
    """Calculate Wilson score confidence interval for binary metrics.
    
    The Wilson score interval is the preferred method for confidence
    intervals of binomial proportions (e.g., accuracy, refusal rate).
    It performs better than the normal approximation for extreme
    proportions and small sample sizes.
    
    Lifted from OBLITERATUS evaluation framework as the default
    method for binary metric confidence intervals.
    
    Args:
        successes: Number of successful outcomes (e.g., correct predictions)
        n: Total number of trials
        confidence: Confidence level (0.90, 0.95, or 0.99)
    
    Returns:
        Dictionary with rate, ci_lower, ci_upper, and n_samples
    """
    if n == 0:
        return {"rate": 0.0, "ci_lower": 0.0, "ci_upper": 0.0, "n_samples": 0}
    
    if not 0 < confidence < 1:
        raise ValueError("confidence must be between 0 and 1")
    
    # Calculate proportion
    rate = successes / n
    
    # Z-scores for common confidence levels
    z_map = {0.90: 1.645, 0.95: 1.96, 0.99: 2.576}
    z = z_map.get(confidence, 1.96)
    
    # Wilson score interval formula
    denominator = 1 + z * z / n
    center = (rate + z * z / (2 * n)) / denominator
    spread = z * math.sqrt((rate * (1 - rate) + z * z / (4 * n)) / n) / denominator
    
    ci_lower = max(0.0, center - spread)
    ci_upper = min(1.0, center + spread)
    
    return {
        "rate": rate,
        "ci_lower": round(ci_lower, 6),
        "ci_upper": round(ci_upper, 6),
        "n_samples": n
    }


def binary_metric_ci(
    values: List[Union[bool, int, float]],
    confidence: float = 0.95
) -> Dict[str, float]:
    """Calculate Wilson score CI for binary metric values.
    
    Convenience function that converts binary values (True/False, 0/1, 0.0/1.0)
    to success count and applies Wilson score CI.
    
    Args:
        values: List of binary values (True/False, 0/1, 0.0/1.0)
        confidence: Confidence level (0.90, 0.95, or 0.99)
    
    Returns:
        Dictionary with rate, ci_lower, ci_upper, and n_samples
    """
    if not values:
        return {"rate": 0.0, "ci_lower": 0.0, "ci_upper": 0.0, "n_samples": 0}
    
    # Convert to binary and count successes
    successes = 0
    for v in values:
        if isinstance(v, bool):
            successes += 1 if v else 0
        elif isinstance(v, (int, float)):
            successes += 1 if v > 0.5 else 0
        else:
            raise ValueError(f"Invalid binary value type: {type(v)}")
    
    return wilson_score_ci(successes, len(values), confidence)