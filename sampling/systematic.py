"""
systematic.py — Systematic Sampling.

Member 3 owns this module.

The frame is sorted by (date, match_id, inning, batting_position).
With N = 16,515 and k = 15, we get n = N/k = 1,101 units per
systematic sample. There are k = 15 possible starting points.

Implements drawing, estimation, analysis of all k starts,
and periodicity diagnostics.

Ref: Cochran (1977), Ch. 8; Singh & Chaudhary, Ch. 4.
"""

from __future__ import annotations
from typing import Optional

import numpy as np
import pandas as pd

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import config
from sampling import estimators as est


def draw_systematic(
    frame: pd.DataFrame,
    k: int = config.k,
    start: Optional[int] = None,
    rng: Optional[np.random.Generator] = None,
) -> pd.DataFrame:
    """
    Draw a 1-in-k systematic sample.

    Pick a random start r ∈ {0, 1, …, k-1}, then take every k-th unit:
        indices = r, r+k, r+2k, …

    The frame must already be sorted in the desired order.
    """
    rng = rng or np.random.default_rng(config.SEED)

    if start is None:
        start = int(rng.integers(0, k))

    N = len(frame)
    indices = np.arange(start, N, k)
    return frame.iloc[indices].copy().reset_index(drop=True)


def all_systematic_samples(
    frame: pd.DataFrame,
    k: int = config.k,
) -> dict[int, pd.DataFrame]:
    """
    Generate all k possible systematic samples (one per starting point).

    Returns dict {start: sample_df}.
    """
    return {r: draw_systematic(frame, k=k, start=r) for r in range(k)}


def analyse_systematic(
    sample: pd.DataFrame,
    frame: pd.DataFrame,
    k: int = config.k,
    N: int = config.N,
    true_mean: Optional[float] = None,
    true_total: Optional[float] = None,
    true_prop: Optional[float] = None,
) -> dict:
    """
    Analyse a single systematic sample.

    Estimate of mean:
        ȳ_sys = (1/n) Σ yᵢ  (same as SRS)

    Variance estimation for systematic sampling is tricky because we
    only have ONE sample. We use two approaches:

    1. Treat-as-SRS approximation:
        V̂(ȳ_sys) ≈ (1 - n/N) · s² / n

    2. Successive-differences estimator (more appropriate for sorted data):
        V̂(ȳ_sys) = (1 - n/N) / (2n(n-1)) · Σᵢ₌₁ⁿ⁻¹ (yᵢ₊₁ - yᵢ)²

    Ref: Cochran (1977), §8.5; Wolter (2007), §7.4
    """
    y = sample["runs"].values
    n = len(y)

    y_bar = est.sample_mean(y)
    tau = est.population_total_from_mean(y_bar, N)
    p_hat = est.sample_proportion(y, threshold=30)

    # Approach 1: treat-as-SRS
    s2 = float(np.var(y, ddof=1))
    v_srs = (1 - n / N) * s2 / n

    # Approach 2: successive differences
    diffs = np.diff(y)
    v_succ_diff = (1 - n / N) * np.sum(diffs**2) / (2 * n * (n - 1))

    se_mean = est.se_from_var(v_srs)
    se_prop_val = est.se_from_var(est.var_proportion_srswor(p_hat, n, N))

    v_total = N**2 * v_srs
    se_total = est.se_from_var(v_total)

    result = {
        "design": "Systematic",
        "n": n, "N": N, "k": k,
        # Mean
        "mean": y_bar,
        "var_mean_srs_approx": v_srs,
        "var_mean_succ_diff": float(v_succ_diff),
        "var_mean": v_srs,        # primary
        "se_mean": se_mean,
        "ci_mean": est.ci_95(y_bar, se_mean),
        # Total
        "total": tau,
        "var_total": v_total,
        "se_total": se_total,
        "ci_total": est.ci_95(tau, se_total),
        # Proportion
        "proportion": p_hat,
        "var_prop": est.var_proportion_srswor(p_hat, n, N),
        "se_prop": se_prop_val,
        "ci_prop": est.ci_95(p_hat, se_prop_val),
    }

    if true_mean is not None:
        result["abs_error_mean"] = est.absolute_error(y_bar, true_mean)
    if true_total is not None:
        result["abs_error_total"] = est.absolute_error(tau, true_total)
    if true_prop is not None:
        result["abs_error_prop"] = est.absolute_error(p_hat, true_prop)

    return result


def empirical_variance_across_starts(
    frame: pd.DataFrame,
    k: int = config.k,
) -> dict:
    """
    Compute the true variance of the systematic estimator by
    enumerating ALL k possible starting points.

    V(ȳ_sys) = (1/k) Σᵣ₌₁ᵏ (ȳ_r - Ȳ)²

    This is the exact variance (since systematic sampling has only
    k possible samples). Compare with the SRS variance to assess
    whether sorting helps or hurts.

    Also checks for periodicity: if k ≈ batters-per-match (≈15),
    each systematic sample may oversample the same batting positions.
    """
    all_samples = all_systematic_samples(frame, k)

    means = []
    proportions = []
    true_mean = float(frame["runs"].mean())
    true_prop = float((frame["runs"] >= 30).mean())

    for r, samp in all_samples.items():
        means.append(float(samp["runs"].mean()))
        proportions.append(float((samp["runs"] >= 30).mean()))

    means = np.array(means)
    proportions = np.array(proportions)

    var_sys_mean = float(np.mean((means - true_mean) ** 2))
    var_sys_prop = float(np.mean((proportions - true_prop) ** 2))

    # SRS variance for comparison
    S2 = float(frame["runs"].var(ddof=1))
    n_sys = len(all_samples[0])
    var_srs = (1 - n_sys / len(frame)) * S2 / n_sys

    # Batting position distribution per start
    bp_distributions = {}
    for r, samp in all_samples.items():
        bp_distributions[r] = samp["batting_position"].value_counts().to_dict()

    return {
        "k": k,
        "n_per_sample": n_sys,
        "sample_means": means.tolist(),
        "sample_proportions": proportions.tolist(),
        "true_mean": true_mean,
        "true_proportion": true_prop,
        "var_systematic_mean": var_sys_mean,
        "var_systematic_prop": var_sys_prop,
        "var_srs_mean": var_srs,
        "relative_efficiency_vs_srs": var_srs / var_sys_mean if var_sys_mean > 0 else float("inf"),
        "periodicity_comment": (
            f"k={k} is close to the average batters-per-match (~15). "
            "This means each systematic sample may repeatedly pick the same "
            "batting position, introducing periodic bias. Examine the batting "
            "position distribution across starting points."
        ),
    }


def analyse_multiple_k(
    frame: pd.DataFrame,
    k_values: list[int] | None = None,
) -> pd.DataFrame:
    """
    Analyse systematic sampling for multiple k values.
    Default k values: all divisors of N that give sensible sample sizes.
    """
    N = len(frame)
    if k_values is None:
        # Use divisors of N
        all_divs = [i for i in range(2, N) if N % i == 0]
        # Filter to sensible sample sizes (n between 30 and N/2)
        k_values = [k for k in all_divs if 30 <= N // k <= N // 2]

    results = []
    for k_val in k_values:
        emp = empirical_variance_across_starts(frame, k=k_val)
        results.append({
            "k": k_val,
            "n": emp["n_per_sample"],
            "var_systematic": emp["var_systematic_mean"],
            "var_srs": emp["var_srs_mean"],
            "RE_vs_srs": emp["relative_efficiency_vs_srs"],
        })

    return pd.DataFrame(results)
