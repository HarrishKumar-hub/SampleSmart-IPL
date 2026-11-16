"""
cluster.py — Cluster Sampling (Single-Stage, Unequal Sizes).

Member 4 owns this module.

Primary clusters = matches (1,095 clusters, ~15 units each).
Secondary/optional = cleaned venues (~44 stadiums) for ICC contrast.

Uses the ratio estimator for the mean (since cluster sizes are unequal).

Ref: Cochran (1977), Ch. 9 & 11; Des Raj & Chandhok.
"""

from __future__ import annotations
from typing import Optional

import numpy as np
import pandas as pd

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import config
from sampling import estimators as est


def draw_cluster_sample(
    frame: pd.DataFrame,
    m: int | None = None,
    cluster_col: str = "match_id",
    rng: Optional[np.random.Generator] = None,
) -> tuple[pd.DataFrame, int]:
    """
    Draw a single-stage cluster sample (all units within selected clusters).

    Parameters
    ----------
    m : number of clusters to select. If None, chosen so expected
        sample size ≈ config.n.
    cluster_col : column defining clusters.

    Returns
    -------
    (sample_df, m_actual) — the sample and number of clusters drawn.
    """
    rng = rng or np.random.default_rng(config.SEED)

    clusters = frame[cluster_col].unique()
    M = len(clusters)  # total clusters in population

    if m is None:
        mean_cluster_size = len(frame) / M
        m = max(2, round(config.n / mean_cluster_size))

    selected = rng.choice(clusters, size=m, replace=False)
    sample = frame[frame[cluster_col].isin(selected)].copy().reset_index(drop=True)

    return sample, m


def analyse_cluster(
    sample: pd.DataFrame,
    frame: pd.DataFrame,
    m: int,
    cluster_col: str = "match_id",
    N: int = config.N,
    true_mean: Optional[float] = None,
    true_total: Optional[float] = None,
    true_prop: Optional[float] = None,
) -> dict:
    """
    Analyse a single-stage cluster sample with unequal cluster sizes
    using the ratio estimator.

    Ratio estimator of mean:
        ȳ_c = Σᵢ yᵢ / Σᵢ mᵢ  = total_y / total_units

    Variance (Cochran §11.6, ratio estimator for cluster sampling):
        V̂(ȳ_c) = (1 - f) / (m · M̄²) · (1/(m-1)) Σ (yᵢ - ȳ_c · mᵢ)²
        where f = m/M, M̄ = N/M (mean cluster size)

    Unbiased total estimator:
        τ̂ = (M/m) Σᵢ yᵢ
    Its variance:
        V̂(τ̂) = M²(1 - f)/m · (1/(m-1)) Σ (yᵢ - ȳ_cluster)²
        where ȳ_cluster = (1/m) Σ yᵢ  (mean of cluster totals)
    """
    M = frame[cluster_col].nunique()  # total clusters
    f = m / M                          # sampling fraction of clusters
    M_bar = N / M                      # mean cluster size

    # Cluster-level aggregates
    cluster_stats = (
        sample.groupby(cluster_col)
        .agg(
            yi=("runs", "sum"),              # total runs in cluster i
            mi=("runs", "count"),            # cluster size
            pi=("runs", lambda x: (x >= 30).sum()),  # count ≥30 in cluster
        )
        .reset_index()
    )

    total_y = cluster_stats["yi"].sum()
    total_m = cluster_stats["mi"].sum()
    total_p = cluster_stats["pi"].sum()

    # ── Ratio estimator for mean ──────────────────────────────
    y_bar_c = total_y / total_m

    # Residuals for variance
    cluster_stats["ei"] = cluster_stats["yi"] - y_bar_c * cluster_stats["mi"]
    sum_ei2 = (cluster_stats["ei"] ** 2).sum()
    var_mean = (1 - f) / (m * M_bar**2) * sum_ei2 / (m - 1)

    se_mean = est.se_from_var(var_mean)

    # ── Unbiased total estimator ──────────────────────────────
    tau_unbiased = (M / m) * total_y
    cluster_totals = cluster_stats["yi"].values
    mean_cluster_total = cluster_totals.mean()
    sum_sq_dev_total = np.sum((cluster_totals - mean_cluster_total) ** 2)
    var_total_unbiased = M**2 * (1 - f) / m * sum_sq_dev_total / (m - 1)
    se_total = est.se_from_var(var_total_unbiased)

    # ── Ratio estimator for total (from mean) ─────────────────
    tau_ratio = N * y_bar_c
    var_total_ratio = N**2 * var_mean

    # ── Proportion estimator ──────────────────────────────────
    p_hat_c = total_p / total_m

    cluster_stats["ep"] = cluster_stats["pi"] - p_hat_c * cluster_stats["mi"]
    sum_ep2 = (cluster_stats["ep"] ** 2).sum()
    var_prop = (1 - f) / (m * M_bar**2) * sum_ep2 / (m - 1)
    se_prop = est.se_from_var(var_prop)

    result = {
        "design": "Cluster",
        "n_actual": int(total_m),
        "m": m,
        "M": M,
        "N": N,
        "M_bar": round(M_bar, 2),
        # Mean (ratio)
        "mean": y_bar_c,
        "var_mean": var_mean,
        "se_mean": se_mean,
        "ci_mean": est.ci_95(y_bar_c, se_mean),
        # Total (unbiased)
        "total": tau_unbiased,
        "total_ratio": tau_ratio,
        "var_total": var_total_unbiased,
        "se_total": se_total,
        "ci_total": est.ci_95(tau_unbiased, se_total),
        # Proportion (ratio)
        "proportion": p_hat_c,
        "var_prop": var_prop,
        "se_prop": se_prop,
        "ci_prop": est.ci_95(p_hat_c, se_prop),
        # Cluster info
        "cluster_sizes": cluster_stats["mi"].tolist(),
        "cluster_means": (cluster_stats["yi"] / cluster_stats["mi"]).tolist(),
    }

    if true_mean is not None:
        result["abs_error_mean"] = est.absolute_error(y_bar_c, true_mean)
    if true_total is not None:
        result["abs_error_total"] = est.absolute_error(tau_unbiased, true_total)
    if true_prop is not None:
        result["abs_error_prop"] = est.absolute_error(p_hat_c, true_prop)

    return result


def compute_icc(
    frame: pd.DataFrame,
    cluster_col: str = "match_id",
    y_col: str = "runs",
) -> dict:
    """
    Compute the Intraclass Correlation Coefficient (ICC) from one-way ANOVA.

    ICC measures how similar units within the same cluster are.

    From ANOVA mean squares:
        MSB = between-cluster mean square
        MSW = within-cluster mean square

        ρ̂ = (MSB - MSW) / (MSB + (M̄₀ - 1) · MSW)

    where M̄₀ is the "common" cluster size adjustment for unequal sizes:
        M̄₀ = (1/(M-1)) · (N - Σmᵢ²/N)

    Ref: Cochran (1977), §11.10; Kish (1965)
    """
    cluster_groups = frame.groupby(cluster_col)[y_col]
    M = cluster_groups.ngroups
    N = len(frame)
    grand_mean = frame[y_col].mean()

    # Compute SS_between and SS_within
    ss_between = 0.0
    ss_within = 0.0
    sizes = []

    for _, group in cluster_groups:
        mi = len(group)
        sizes.append(mi)
        cluster_mean = group.mean()
        ss_between += mi * (cluster_mean - grand_mean) ** 2
        ss_within += ((group - cluster_mean) ** 2).sum()

    sizes = np.array(sizes)

    MSB = ss_between / (M - 1)
    MSW = ss_within / (N - M)

    # Adjusted common cluster size for unequal sizes
    M_bar_0 = (N - np.sum(sizes**2) / N) / (M - 1)

    rho = (MSB - MSW) / (MSB + (M_bar_0 - 1) * MSW)

    # Design effect = 1 + (M̄₀ - 1) · ρ
    deff = 1 + (M_bar_0 - 1) * rho

    return {
        "MSB": float(MSB),
        "MSW": float(MSW),
        "M_bar_0": float(M_bar_0),
        "ICC_rho": float(rho),
        "design_effect": float(deff),
        "M": M,
        "N": N,
        "ss_between": float(ss_between),
        "ss_within": float(ss_within),
        "interpretation": (
            f"ICC (ρ) = {rho:.4f}. "
            f"Design effect = {deff:.2f}. "
            f"{'Positive ICC: units within matches are more similar than random → '
              'cluster sampling is LESS efficient than SRS.'
              if rho > 0 else
              'Negative/zero ICC: cluster sampling may be as efficient as SRS.'}"
        ),
    }


def compute_venue_icc(frame: pd.DataFrame) -> dict:
    """
    Compute ICC using venues as clusters (for contrast with match-level ICC).
    Venues are larger clusters → expect higher ICC.
    """
    return compute_icc(frame, cluster_col="venue", y_col="runs")
