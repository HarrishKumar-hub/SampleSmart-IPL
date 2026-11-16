"""
stratified.py — Stratified Random Sampling (Proportional & Neyman Allocation).

Member 2 owns this module.

Strata are defined by batting position groups:
  Openers (1-2), Middle (3-5), Lower-Middle (6-7), Tail (8-11).

Implements allocation, drawing, and combined estimators with textbook
formulas from Cochran (1977), Ch. 5.
"""

from __future__ import annotations
from typing import Optional

import numpy as np
import pandas as pd

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import config
from sampling import estimators as est


# ────────────────────────────────────────────────────────────────
# Allocation
# ────────────────────────────────────────────────────────────────
def compute_allocation(
    frame: pd.DataFrame,
    n: int = config.n,
    method: str = "proportional",
) -> pd.DataFrame:
    """
    Compute stratum sample sizes under proportional or Neyman allocation.

    Proportional:  nₕ = n · (Nₕ / N)
    Neyman:        nₕ = n · (Nₕ · Sₕ) / Σ(Nₕ · Sₕ)

    Rounding uses largest-remainder method to ensure Σnₕ = n exactly.

    Returns DataFrame with columns: stratum, Nh, Wh, Sh, nh.
    """
    strata_stats = (
        frame.groupby("stratum", observed=True)["runs"]
        .agg(Nh="count", mean_h="mean", Sh="std")  # std with ddof=1
        .reset_index()
    )
    N_total = strata_stats["Nh"].sum()
    strata_stats["Wh"] = strata_stats["Nh"] / N_total

    if method == "proportional":
        strata_stats["nh_raw"] = n * strata_stats["Wh"]
    elif method == "neyman":
        strata_stats["NhSh"] = strata_stats["Nh"] * strata_stats["Sh"]
        total_NhSh = strata_stats["NhSh"].sum()
        strata_stats["nh_raw"] = n * strata_stats["NhSh"] / total_NhSh
    else:
        raise ValueError(f"Unknown method: {method}")

    # Largest-remainder rounding
    strata_stats["nh"] = _round_allocation(strata_stats["nh_raw"].values, n)

    return strata_stats


def _round_allocation(raw: np.ndarray, target: int) -> np.ndarray:
    """
    Largest-remainder method: floor all, then give +1 to the
    strata with the largest fractional remainders until Σnₕ = target.
    Ensures each stratum gets at least 2 (for variance estimation).
    """
    floored = np.floor(raw).astype(int)
    floored = np.maximum(floored, 2)  # minimum 2 per stratum
    remainders = raw - floored
    deficit = target - floored.sum()

    if deficit > 0:
        # give +1 to the largest remainders
        top_idx = np.argsort(remainders)[-deficit:]
        floored[top_idx] += 1
    elif deficit < 0:
        # take -1 from the smallest remainders (rare edge case)
        bot_idx = np.argsort(remainders)[:abs(deficit)]
        floored[bot_idx] = np.maximum(floored[bot_idx] - 1, 2)

    return floored


# ────────────────────────────────────────────────────────────────
# Drawing
# ────────────────────────────────────────────────────────────────
def draw_stratified(
    frame: pd.DataFrame,
    allocation: pd.DataFrame,
    rng: Optional[np.random.Generator] = None,
) -> pd.DataFrame:
    """
    Draw a stratified random sample (SRSWOR within each stratum).

    Parameters
    ----------
    allocation : DataFrame with columns stratum, nh.
    """
    rng = rng or np.random.default_rng(config.SEED)
    samples = []

    for _, row in allocation.iterrows():
        stratum_data = frame[frame["stratum"] == row["stratum"]]
        nh = int(row["nh"])
        idx = rng.choice(len(stratum_data), size=nh, replace=False)
        samples.append(stratum_data.iloc[idx])

    return pd.concat(samples, ignore_index=True)


# ────────────────────────────────────────────────────────────────
# Estimation
# ────────────────────────────────────────────────────────────────
def analyse_stratified(
    sample: pd.DataFrame,
    frame: pd.DataFrame,
    allocation: pd.DataFrame,
    N: int = config.N,
    true_mean: Optional[float] = None,
    true_total: Optional[float] = None,
    true_prop: Optional[float] = None,
) -> dict:
    """
    Compute stratified estimates of mean, total, and proportion.

    Combined mean:
        ȳ_st = Σ Wₕ · ȳₕ

    Variance of combined mean:
        V(ȳ_st) = Σ Wₕ² · (1 - nₕ/Nₕ) · sₕ² / nₕ

    Combined proportion:
        p̂_st = Σ Wₕ · p̂ₕ

    Variance of combined proportion:
        V(p̂_st) = Σ Wₕ² · (1 - nₕ/Nₕ) · p̂ₕ(1 - p̂ₕ) / (nₕ - 1)

    Ref: Cochran (1977), Theorem 5.1, 5.3
    """
    alloc = allocation.set_index("stratum")

    y_bar_st = 0.0
    v_mean_st = 0.0
    p_hat_st = 0.0
    v_prop_st = 0.0
    strata_details = []

    for stratum_name in alloc.index:
        Nh = int(alloc.loc[stratum_name, "Nh"])
        Wh = Nh / N
        nh = int(alloc.loc[stratum_name, "nh"])

        stratum_sample = sample[sample["stratum"] == stratum_name]["runs"].values

        y_bar_h = float(np.mean(stratum_sample))
        s2_h = float(np.var(stratum_sample, ddof=1))
        p_h = float(np.mean(stratum_sample >= 30))

        y_bar_st += Wh * y_bar_h
        v_mean_st += Wh**2 * (1 - nh / Nh) * s2_h / nh

        p_var_h = p_h * (1 - p_h) / (nh - 1) if nh > 1 else 0
        v_prop_st += Wh**2 * (1 - nh / Nh) * p_h * (1 - p_h) / max(nh - 1, 1)
        p_hat_st += Wh * p_h

        strata_details.append({
            "stratum": stratum_name,
            "Nh": Nh, "Wh": round(Wh, 4), "nh": nh,
            "y_bar_h": round(y_bar_h, 4),
            "s2_h": round(s2_h, 4),
            "p_h": round(p_h, 4),
        })

    tau_st = N * y_bar_st
    se_mean = est.se_from_var(v_mean_st)
    se_prop = est.se_from_var(v_prop_st)

    v_total = N**2 * v_mean_st
    se_total = est.se_from_var(v_total)

    result = {
        "design": f"Stratified-{allocation.attrs.get('method', 'unknown').title()}",
        "n": int(allocation["nh"].sum()),
        "N": N,
        # Mean
        "mean": y_bar_st,
        "var_mean": v_mean_st,
        "se_mean": se_mean,
        "ci_mean": est.ci_95(y_bar_st, se_mean),
        # Total
        "total": tau_st,
        "var_total": v_total,
        "se_total": se_total,
        "ci_total": est.ci_95(tau_st, se_total),
        # Proportion
        "proportion": p_hat_st,
        "var_prop": v_prop_st,
        "se_prop": se_prop,
        "ci_prop": est.ci_95(p_hat_st, se_prop),
        # Details
        "strata_details": strata_details,
    }

    if true_mean is not None:
        result["abs_error_mean"] = est.absolute_error(y_bar_st, true_mean)
    if true_total is not None:
        result["abs_error_total"] = est.absolute_error(tau_st, true_total)
    if true_prop is not None:
        result["abs_error_prop"] = est.absolute_error(p_hat_st, true_prop)

    return result


def variance_gain(var_srs: float, var_strat: float) -> dict:
    """
    Compute the gain in precision of stratified over SRS.

    Returns relative efficiency and percentage reduction in variance.
    """
    re = est.relative_efficiency(var_srs, var_strat)
    pct_reduction = (1 - var_strat / var_srs) * 100 if var_srs > 0 else 0

    return {
        "relative_efficiency": re,
        "pct_variance_reduction": round(pct_reduction, 2),
        "interpretation": (
            f"Stratified is {re:.2f}× more efficient than SRS "
            f"({pct_reduction:.1f}% variance reduction)."
        ),
    }
