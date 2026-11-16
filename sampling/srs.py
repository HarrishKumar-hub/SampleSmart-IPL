"""
srs.py — Simple Random Sampling (With and Without Replacement).

Member 1 owns this module.

Implements SRSWOR and SRSWR drawing, along with analytic variance
formulas, sample-size justification, and comparison of the two designs.
"""

from __future__ import annotations
from typing import Optional

import numpy as np
import pandas as pd

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import config
from sampling import estimators as est


def draw_srswor(
    frame: pd.DataFrame,
    n: int = config.n,
    rng: Optional[np.random.Generator] = None,
) -> pd.DataFrame:
    """
    Draw a Simple Random Sample Without Replacement.

    Every subset of size n has equal probability C(N,n)⁻¹.
    Uses numpy Generator.choice(replace=False).
    """
    rng = rng or np.random.default_rng(config.SEED)
    idx = rng.choice(len(frame), size=n, replace=False)
    return frame.iloc[idx].copy().reset_index(drop=True)


def draw_srswr(
    frame: pd.DataFrame,
    n: int = config.n,
    rng: Optional[np.random.Generator] = None,
) -> pd.DataFrame:
    """
    Draw a Simple Random Sample With Replacement.

    Each draw is independent with probability 1/N per unit.
    Uses numpy Generator.choice(replace=True).
    """
    rng = rng or np.random.default_rng(config.SEED)
    idx = rng.choice(len(frame), size=n, replace=True)
    return frame.iloc[idx].copy().reset_index(drop=True)


def analyse_srs(
    sample: pd.DataFrame,
    N: int = config.N,
    method: str = "srswor",
    true_mean: Optional[float] = None,
    true_total: Optional[float] = None,
    true_prop: Optional[float] = None,
) -> dict:
    """
    Compute all estimates, variances, SEs, CIs for a drawn SRS sample.

    Parameters
    ----------
    method : 'srswor' or 'srswr'

    Returns
    -------
    dict with keys: mean, total, proportion, var_mean, se_mean, ci_mean,
                    var_prop, se_prop, ci_prop, n, N, fpc, abs_error_mean, etc.
    """
    y = sample["runs"].values
    n = len(y)

    y_bar = est.sample_mean(y)
    tau    = est.population_total_from_mean(y_bar, N)
    p_hat  = est.sample_proportion(y, threshold=30)

    if method == "srswor":
        v_mean = est.var_srswor(y, N)
        v_prop = est.var_proportion_srswor(p_hat, n, N)
    else:
        v_mean = est.var_srswr(y, N)
        v_prop = est.var_proportion_srswr(p_hat, n)

    se_mean = est.se_from_var(v_mean)
    se_prop = est.se_from_var(v_prop)
    ci_mean = est.ci_95(y_bar, se_mean)
    ci_prop = est.ci_95(p_hat, se_prop)

    # Variance of total = N² * Var(mean)
    v_total  = N**2 * v_mean
    se_total = est.se_from_var(v_total)
    ci_total = est.ci_95(tau, se_total)

    result = {
        "design": method.upper(),
        "n": n,
        "N": N,
        "fpc": est.fpc(n, N),
        # Mean
        "mean": y_bar,
        "var_mean": v_mean,
        "se_mean": se_mean,
        "ci_mean": ci_mean,
        # Total
        "total": tau,
        "var_total": v_total,
        "se_total": se_total,
        "ci_total": ci_total,
        # Proportion
        "proportion": p_hat,
        "var_prop": v_prop,
        "se_prop": se_prop,
        "ci_prop": ci_prop,
    }

    if true_mean is not None:
        result["abs_error_mean"] = est.absolute_error(y_bar, true_mean)
    if true_total is not None:
        result["abs_error_total"] = est.absolute_error(tau, true_total)
    if true_prop is not None:
        result["abs_error_prop"] = est.absolute_error(p_hat, true_prop)

    return result


def sample_size_justification(S: float, P: float, N: int = config.N) -> dict:
    """
    Justify n ≈ 1,101 using the SRS sample-size formulas.

    Shows the achieved margin of error at n = 1,101 for both
    the mean and the proportion.
    """
    # For the mean
    margin_mean = est.achieved_margin(config.n, S, N)
    n_for_1 = est.sample_size_mean(S, e=1.0, N=N)
    n_for_1_5 = est.sample_size_mean(S, e=1.5, N=N)

    # For the proportion
    margin_prop = config.Z * np.sqrt((1 - config.n / N) * P * (1 - P) / config.n)
    n_for_p_02 = est.sample_size_proportion(P, e=0.02, N=N)

    return {
        "n_used": config.n,
        "S": S,
        "P": P,
        "margin_mean_at_n": round(margin_mean, 4),
        "n_needed_for_margin_1": n_for_1,
        "n_needed_for_margin_1.5": n_for_1_5,
        "margin_prop_at_n": round(margin_prop, 4),
        "n_needed_for_prop_margin_0.02": n_for_p_02,
        "interpretation": (
            f"At n={config.n}, the 95% CI for the mean is ±{margin_mean:.2f} runs "
            f"and for the proportion is ±{margin_prop:.4f}."
        ),
    }


def compare_wor_wr(frame: pd.DataFrame, rng: Optional[np.random.Generator] = None) -> dict:
    """
    Draw one SRSWOR and one SRSWR sample and compare their variances.

    Returns both analyses plus the variance ratio (N-n)/(N-1).
    """
    rng = rng or np.random.default_rng(config.SEED)

    N = len(frame)
    true_mean = float(frame["runs"].mean())
    true_total = float(frame["runs"].sum())
    true_prop = float((frame["runs"] >= 30).mean())

    s_wor = draw_srswor(frame, rng=rng)
    s_wr  = draw_srswr(frame, rng=rng)

    a_wor = analyse_srs(s_wor, N, "srswor", true_mean, true_total, true_prop)
    a_wr  = analyse_srs(s_wr,  N, "srswr",  true_mean, true_total, true_prop)

    ratio = est.var_ratio_wor_wr(config.n, N)

    return {
        "srswor": a_wor,
        "srswr": a_wr,
        "var_ratio_theory": ratio,
        "var_ratio_observed": a_wor["var_mean"] / a_wr["var_mean"] if a_wr["var_mean"] > 0 else None,
        "true_mean": true_mean,
        "true_total": true_total,
        "true_prop": true_prop,
    }
