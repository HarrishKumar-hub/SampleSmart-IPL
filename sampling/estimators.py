"""
estimators.py — Shared estimation functions for all sampling designs.

Implements textbook formulas from Cochran (1977) and Singh & Chaudhary.
Every function documents its formula in the docstring.
"""

from __future__ import annotations
from typing import Optional
import numpy as np

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import config


# ────────────────────────────────────────────────────────────────
# Finite Population Correction
# ────────────────────────────────────────────────────────────────
def fpc(n: int, N: int = config.N) -> float:
    """
    Finite Population Correction factor.

    Formula:  fpc = (N - n) / N
    """
    return (N - n) / N


# ────────────────────────────────────────────────────────────────
# Mean estimators
# ────────────────────────────────────────────────────────────────
def sample_mean(y: np.ndarray) -> float:
    """ȳ = (1/n) Σ yᵢ"""
    return float(np.mean(y))


def population_total_from_mean(y_bar: float, N: int = config.N) -> float:
    """τ̂ = N · ȳ"""
    return N * y_bar


# ────────────────────────────────────────────────────────────────
# Variance estimators
# ────────────────────────────────────────────────────────────────
def var_srswor(y: np.ndarray, N: int = config.N) -> float:
    """
    Variance of sample mean under SRSWOR.

    Formula:  V(ȳ) = (1 - n/N) · s² / n
    where s² = Σ(yᵢ - ȳ)² / (n - 1)

    Ref: Cochran (1977), Theorem 2.2
    """
    n = len(y)
    s2 = float(np.var(y, ddof=1))
    return (1 - n / N) * s2 / n


def var_srswr(y: np.ndarray, N: int = config.N) -> float:
    """
    Variance of sample mean under SRSWR.

    Formula:  V(ȳ) = σ² / n = S² / n
    (no finite population correction in with-replacement sampling)

    Ref: Cochran (1977), §2.6
    """
    n = len(y)
    s2 = float(np.var(y, ddof=1))
    return s2 / n


def var_ratio_wor_wr(n: int, N: int = config.N) -> float:
    """
    Ratio of SRSWOR variance to SRSWR variance.

    Formula:  V(SRSWOR) / V(SRSWR) = (N - n) / (N - 1) ≈ 1 - f

    This shows SRSWOR is always more precise than SRSWR.
    """
    return (N - n) / (N - 1)


# ────────────────────────────────────────────────────────────────
# Proportion estimators
# ────────────────────────────────────────────────────────────────
def sample_proportion(y: np.ndarray, threshold: float = 30.0) -> float:
    """p̂ = (number of yᵢ ≥ threshold) / n"""
    return float(np.mean(y >= threshold))


def var_proportion_srswor(p: float, n: int, N: int = config.N) -> float:
    """
    Variance of sample proportion under SRSWOR.

    Formula:  V(p̂) = (1 - n/N) · p̂(1 - p̂) / (n - 1)

    Ref: Cochran (1977), §3.3
    """
    return (1 - n / N) * p * (1 - p) / (n - 1)


def var_proportion_srswr(p: float, n: int) -> float:
    """
    Variance of sample proportion under SRSWR.

    Formula:  V(p̂) = p̂(1 - p̂) / n
    """
    return p * (1 - p) / n


# ────────────────────────────────────────────────────────────────
# Confidence interval
# ────────────────────────────────────────────────────────────────
def ci_95(estimate: float, se: float, z: float = config.Z) -> tuple[float, float]:
    """
    95 % confidence interval.

    Formula:  estimate ± z_{α/2} · SE
    """
    margin = z * se
    return (estimate - margin, estimate + margin)


# ────────────────────────────────────────────────────────────────
# Standard error
# ────────────────────────────────────────────────────────────────
def se_from_var(variance: float) -> float:
    """SE = √V"""
    return float(np.sqrt(variance))


# ────────────────────────────────────────────────────────────────
# Sample size determination
# ────────────────────────────────────────────────────────────────
def sample_size_mean(S: float, e: float, N: int = config.N,
                     z: float = config.Z) -> int:
    """
    Required sample size for estimating the mean with margin e.

    Formula:
        n₀ = (z · S / e)²
        n  = n₀ / (1 + n₀/N)         (finite population correction)

    Ref: Cochran (1977), §4.7
    """
    n0 = (z * S / e) ** 2
    n  = n0 / (1 + n0 / N)
    return int(np.ceil(n))


def sample_size_proportion(P: float, e: float, N: int = config.N,
                           z: float = config.Z) -> int:
    """
    Required sample size for estimating a proportion with margin e.

    Formula:
        n₀ = z² · P(1-P) / e²
        n  = n₀ / (1 + n₀/N)

    Ref: Cochran (1977), §4.8
    """
    n0 = z ** 2 * P * (1 - P) / e ** 2
    n  = n0 / (1 + n0 / N)
    return int(np.ceil(n))


def achieved_margin(n: int, S: float, N: int = config.N,
                    z: float = config.Z) -> float:
    """
    Margin of error achieved by sample size n for the mean.

    Formula:  e = z · S · √((1 - n/N) / n)
    """
    return z * S * np.sqrt((1 - n / N) / n)


# ────────────────────────────────────────────────────────────────
# Relative efficiency
# ────────────────────────────────────────────────────────────────
def relative_efficiency(var_srs: float, var_design: float) -> float:
    """
    Relative Efficiency of a design vs SRS.

    Formula:  RE = V(ȳ_SRS) / V(ȳ_design)
    RE > 1 means the design is MORE efficient than SRS.
    """
    if var_design == 0:
        return float("inf")
    return var_srs / var_design


def design_effect(var_design: float, var_srs: float) -> float:
    """
    Design Effect (Deff).

    Formula:  Deff = V(ȳ_design) / V(ȳ_SRS)
    Deff < 1 means the design is more efficient than SRS.
    """
    if var_srs == 0:
        return float("inf")
    return var_design / var_srs


# ────────────────────────────────────────────────────────────────
# Absolute error
# ────────────────────────────────────────────────────────────────
def absolute_error(estimate: float, true_value: float) -> float:
    """| estimate - true_value |"""
    return abs(estimate - true_value)
