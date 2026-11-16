"""
tests.py — ANOVA and F-tests for the sampling project.

Implements one-way ANOVA for strata, clusters, systematic samples,
F-tests between design variances, and normality checks.

Every test states H₀, H₁, α, F-value, p-value, and decision.

Ref: Montgomery (2017), Cochran (1977), Snedecor & Cochran.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import config


def _format_decision(p_value: float, alpha: float = config.ALPHA) -> str:
    """Return a plain-English decision string."""
    if p_value < alpha:
        return f"Reject H₀ (p = {p_value:.4e} < α = {alpha}). The difference is statistically significant."
    else:
        return f"Fail to reject H₀ (p = {p_value:.4f} ≥ α = {alpha}). No significant difference."


# ────────────────────────────────────────────────────────────────
# 1. Stratified ANOVA — one-way with strata as groups
# ────────────────────────────────────────────────────────────────
def anova_strata(frame: pd.DataFrame) -> dict:
    """
    One-way ANOVA: do mean runs differ across batting-position strata?

    H₀: μ_openers = μ_middle = μ_lower = μ_tail
    H₁: At least one stratum mean differs.
    α = 0.05

    Uses scipy.stats.f_oneway (equivalent to the textbook between/within SS).
    """
    groups = [
        group["runs"].values
        for _, group in frame.groupby("stratum", observed=True)
    ]

    F_val, p_val = stats.f_oneway(*groups)

    # Also compute between/within SS for reporting
    grand_mean = frame["runs"].mean()
    ss_between = sum(len(g) * (g.mean() - grand_mean) ** 2 for g in groups)
    ss_within = sum(((g - g.mean()) ** 2).sum() for g in groups)
    ss_total = ss_between + ss_within

    k = len(groups)
    N = sum(len(g) for g in groups)
    df_between = k - 1
    df_within = N - k

    MSB = ss_between / df_between
    MSW = ss_within / df_within

    return {
        "test": "One-Way ANOVA (Strata)",
        "H0": "μ_openers = μ_middle = μ_lower_middle = μ_tail",
        "H1": "At least one stratum mean differs",
        "alpha": config.ALPHA,
        "F_value": float(F_val),
        "p_value": float(p_val),
        "decision": _format_decision(p_val),
        "SS_between": float(ss_between),
        "SS_within": float(ss_within),
        "SS_total": float(ss_total),
        "df_between": df_between,
        "df_within": df_within,
        "MSB": float(MSB),
        "MSW": float(MSW),
        "eta_squared": float(ss_between / ss_total),
    }


# ────────────────────────────────────────────────────────────────
# 2. Cluster ANOVA — one-way with matches as groups
# ────────────────────────────────────────────────────────────────
def anova_clusters(frame: pd.DataFrame, cluster_col: str = "match_id") -> dict:
    """
    One-way ANOVA: do mean runs differ across matches (clusters)?

    H₀: μ_match₁ = μ_match₂ = … = μ_match_M
    H₁: At least one match mean differs.
    α = 0.05

    Also estimates ICC from the ANOVA mean squares:
        ρ̂ = (MSB - MSW) / (MSB + (M̄₀ - 1) · MSW)
    """
    groups = [
        group["runs"].values
        for _, group in frame.groupby(cluster_col)
    ]

    F_val, p_val = stats.f_oneway(*groups)

    grand_mean = frame["runs"].mean()
    N = len(frame)
    M = len(groups)
    sizes = np.array([len(g) for g in groups])

    ss_between = sum(len(g) * (g.mean() - grand_mean) ** 2 for g in groups)
    ss_within = sum(((g - g.mean()) ** 2).sum() for g in groups)

    MSB = ss_between / (M - 1)
    MSW = ss_within / (N - M)

    # Adjusted cluster size for ICC
    M_bar_0 = (N - np.sum(sizes**2) / N) / (M - 1)
    rho = (MSB - MSW) / (MSB + (M_bar_0 - 1) * MSW)

    return {
        "test": f"One-Way ANOVA (Clusters: {cluster_col})",
        "H0": f"All {cluster_col} group means are equal",
        "H1": f"At least one {cluster_col} group mean differs",
        "alpha": config.ALPHA,
        "F_value": float(F_val),
        "p_value": float(p_val),
        "decision": _format_decision(p_val),
        "M": M,
        "MSB": float(MSB),
        "MSW": float(MSW),
        "M_bar_0": float(M_bar_0),
        "ICC_rho": float(rho),
    }


# ────────────────────────────────────────────────────────────────
# 3. Systematic ANOVA — k systematic samples as groups
# ────────────────────────────────────────────────────────────────
def anova_systematic(frame: pd.DataFrame, k: int = config.k) -> dict:
    """
    One-way ANOVA with the k systematic samples as groups.

    H₀: All k systematic sample means are equal.
    H₁: At least one systematic sample mean differs.
    α = 0.05

    Implication: significant F → the frame ordering creates
    differences between systematic samples → periodicity or trend.
    """
    from sampling.systematic import all_systematic_samples

    all_samps = all_systematic_samples(frame, k=k)
    groups = [samp["runs"].values for samp in all_samps.values()]

    F_val, p_val = stats.f_oneway(*groups)

    means = [float(g.mean()) for g in groups]
    sds = [float(g.std(ddof=1)) for g in groups]

    # Within-sample variance vs population variance
    pop_var = float(frame["runs"].var(ddof=0))
    avg_within_var = float(np.mean([g.var(ddof=1) for g in groups]))

    return {
        "test": "One-Way ANOVA (Systematic Samples)",
        "H0": "All k systematic sample means are equal",
        "H1": "At least one systematic sample mean differs",
        "alpha": config.ALPHA,
        "k": k,
        "F_value": float(F_val),
        "p_value": float(p_val),
        "decision": _format_decision(p_val),
        "sample_means": means,
        "sample_sds": sds,
        "population_variance": pop_var,
        "avg_within_sample_variance": avg_within_var,
        "periodicity_comment": (
            "Significant F implies trend or periodicity in the sorted frame. "
            f"k={k} ≈ batters-per-match, so systematic samples may repeatedly "
            "pick the same batting positions."
            if p_val < config.ALPHA else
            "No significant difference between systematic samples — "
            "the frame ordering is not introducing systematic bias."
        ),
    }


# ────────────────────────────────────────────────────────────────
# 4. F-test on variance ratio between two designs
# ────────────────────────────────────────────────────────────────
def f_test_variance_ratio(
    var1: float,
    var2: float,
    df1: int,
    df2: int,
    label1: str = "Design 1",
    label2: str = "Design 2",
) -> dict:
    """
    F-test for equality of two variances.

    H₀: σ₁² = σ₂²
    H₁: σ₁² ≠ σ₂² (two-tailed)
    α = 0.05

    F = max(s₁², s₂²) / min(s₁², s₂²)

    The degrees of freedom come from the number of simulation
    replications (N_SIM - 1) or from the analytic formula.
    """
    if var1 >= var2:
        F_val = var1 / var2
        num_label, den_label = label1, label2
        df_num, df_den = df1, df2
    else:
        F_val = var2 / var1
        num_label, den_label = label2, label1
        df_num, df_den = df2, df1

    # Two-tailed p-value
    p_val = 2 * (1 - stats.f.cdf(F_val, df_num, df_den))
    p_val = min(p_val, 1.0)

    return {
        "test": f"F-test: {label1} vs {label2}",
        "H0": f"Var({label1}) = Var({label2})",
        "H1": f"Var({label1}) ≠ Var({label2})",
        "alpha": config.ALPHA,
        "F_value": float(F_val),
        "df_numerator": df_num,
        "df_denominator": df_den,
        "numerator": num_label,
        "denominator": den_label,
        "p_value": float(p_val),
        "decision": _format_decision(p_val),
    }


# ────────────────────────────────────────────────────────────────
# 5. Normality check
# ────────────────────────────────────────────────────────────────
def normality_check(
    data: np.ndarray,
    label: str = "runs",
    max_shapiro_n: int = 5000,
) -> dict:
    """
    Check normality of the data using Shapiro-Wilk test.

    H₀: The data is normally distributed.
    H₁: The data is NOT normally distributed.
    α = 0.05

    Note: Runs per innings are right-skewed with a spike at 0.
    Sample means (n ≈ 1100) are approximately normal by CLT.
    """
    n = len(data)

    # Shapiro-Wilk (max 5000 observations)
    if n > max_shapiro_n:
        subset = np.random.default_rng(config.SEED).choice(data, max_shapiro_n, replace=False)
        W, p_val = stats.shapiro(subset)
        note = f"Shapiro-Wilk run on random subset of {max_shapiro_n} (original n={n})"
    else:
        W, p_val = stats.shapiro(data)
        note = f"Shapiro-Wilk on full data (n={n})"

    skewness = float(stats.skew(data))
    kurtosis = float(stats.kurtosis(data))

    return {
        "test": f"Normality Check ({label})",
        "H0": f"{label} follows a normal distribution",
        "H1": f"{label} does NOT follow a normal distribution",
        "alpha": config.ALPHA,
        "W_statistic": float(W),
        "p_value": float(p_val),
        "decision": _format_decision(p_val),
        "skewness": skewness,
        "kurtosis": kurtosis,
        "note": note,
        "clt_comment": (
            "Individual runs are right-skewed (skewness > 0) with a spike near 0. "
            "However, by the Central Limit Theorem, sample means from n ≈ 1,100 "
            "will be approximately normally distributed regardless."
        ),
    }


# ────────────────────────────────────────────────────────────────
# Runner: execute all tests and save results
# ────────────────────────────────────────────────────────────────
def run_all_tests(frame: pd.DataFrame) -> dict[str, dict]:
    """Run all ANOVA and statistical tests on the frame."""
    results = {}

    results["strata_anova"] = anova_strata(frame)
    results["cluster_anova_match"] = anova_clusters(frame, "match_id")
    results["systematic_anova"] = anova_systematic(frame, config.k)
    results["normality_runs"] = normality_check(frame["runs"].values, "runs")

    return results


if __name__ == "__main__":
    from sampling.frame import load_frame
    import json

    frame = load_frame()
    results = run_all_tests(frame)

    print("=" * 70)
    print("STATISTICAL TESTS — RESULTS")
    print("=" * 70)
    for name, result in results.items():
        print(f"\n{'─' * 50}")
        print(f"  {result['test']}")
        print(f"{'─' * 50}")
        for k, v in result.items():
            if k == "test":
                continue
            if isinstance(v, list) and len(v) > 10:
                print(f"  {k}: [{v[0]:.4f}, {v[1]:.4f}, ... ({len(v)} values)]")
            else:
                print(f"  {k}: {v}")
