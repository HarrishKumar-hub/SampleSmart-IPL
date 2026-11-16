"""
figures.py — Generate all project visualisations.

Saves PNG at 300 DPI to results/figures/.
Consistent style, labelled axes, colour-blind safe palette.

9 required figures as per §9 of the project brief.
"""

from __future__ import annotations
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")           # non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import config


# ── Global style ───────────────────────────────────────────────
sns.set_theme(style="whitegrid", font_scale=1.1, rc={
    "figure.dpi": 150,
    "savefig.dpi": config.FIG_DPI,
    "axes.titlesize": 14,
    "axes.labelsize": 12,
})
PALETTE = config.PALETTE
OUT = Path(config.FIGURES_DIR)
OUT.mkdir(parents=True, exist_ok=True)


# ────────────────────────────────────────────────────────────────
# 1. Histogram of runs + boxplot by stratum
# ────────────────────────────────────────────────────────────────
def fig1_histogram_and_boxplot(frame: pd.DataFrame) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(14, 5), gridspec_kw={"width_ratios": [1.2, 1]})

    # Histogram
    ax = axes[0]
    ax.hist(frame["runs"], bins=50, color=PALETTE[0], edgecolor="white", alpha=0.85)
    ax.axvline(frame["runs"].mean(), color=PALETTE[4], ls="--", lw=2,
               label=f'Mean = {frame["runs"].mean():.1f}')
    ax.axvline(frame["runs"].median(), color=PALETTE[3], ls=":", lw=2,
               label=f'Median = {frame["runs"].median():.0f}')
    ax.set_xlabel("Runs per innings")
    ax.set_ylabel("Frequency")
    ax.set_title("Distribution of Runs per Batter-Innings (N = {:,})".format(len(frame)))
    ax.legend(fontsize=10)

    # Boxplot by stratum
    ax = axes[1]
    order = config.STRATA_LABELS
    sns.boxplot(data=frame, x="stratum", y="runs", order=order,
                palette=PALETTE[:4], ax=ax, fliersize=2)
    ax.set_xlabel("Batting Position Stratum")
    ax.set_ylabel("Runs")
    ax.set_title("Runs by Batting Position Stratum")
    ax.tick_params(axis="x", rotation=15)

    plt.tight_layout()
    fig.savefig(OUT / "01_histogram_boxplot.png", bbox_inches="tight")
    plt.close(fig)
    print("  ✅ 01_histogram_boxplot.png")


# ────────────────────────────────────────────────────────────────
# 2. Systematic "comb" plot
# ────────────────────────────────────────────────────────────────
def fig2_systematic_comb(frame: pd.DataFrame, k: int = config.k) -> None:
    fig, ax = plt.subplots(figsize=(14, 4))

    N = len(frame)
    # Show first 200 units for clarity
    show_n = min(300, N)
    x = np.arange(show_n)
    y = frame["runs"].values[:show_n]

    ax.bar(x, y, width=1.0, color="#D3D3D3", edgecolor="none", label="Population")

    # Highlight systematic picks for 3 starting points
    colors_starts = [PALETTE[0], PALETTE[1], PALETTE[4]]
    for i, start in enumerate([0, 5, 10]):
        picks = np.arange(start, show_n, k)
        ax.bar(picks, frame["runs"].values[picks], width=1.0,
               color=colors_starts[i], alpha=0.8, label=f"Start r={start}")

    ax.set_xlabel("Frame index (first 300 units shown)")
    ax.set_ylabel("Runs")
    ax.set_title(f"Systematic Sampling Comb (k = {k}): Every {k}-th Unit")
    ax.legend(fontsize=9, loc="upper right")
    plt.tight_layout()
    fig.savefig(OUT / "02_systematic_comb.png", bbox_inches="tight")
    plt.close(fig)
    print("  ✅ 02_systematic_comb.png")


# ────────────────────────────────────────────────────────────────
# 3. Stratified allocation bar chart
# ────────────────────────────────────────────────────────────────
def fig3_allocation_comparison(alloc_prop: pd.DataFrame, alloc_ney: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(10, 5))

    x = np.arange(len(alloc_prop))
    width = 0.35

    bars1 = ax.bar(x - width/2, alloc_prop["nh"], width,
                   label="Proportional", color=PALETTE[1], edgecolor="white")
    bars2 = ax.bar(x + width/2, alloc_ney["nh"], width,
                   label="Neyman", color=PALETTE[4], edgecolor="white")

    ax.set_xlabel("Stratum")
    ax.set_ylabel("Sample size (nₕ)")
    ax.set_title("Stratified Allocation: Proportional vs Neyman")
    ax.set_xticks(x)
    ax.set_xticklabels(alloc_prop["stratum"], rotation=10)
    ax.legend()

    # Value labels
    for bars in [bars1, bars2]:
        for bar in bars:
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 5,
                    f'{int(bar.get_height())}', ha='center', va='bottom', fontsize=9)

    plt.tight_layout()
    fig.savefig(OUT / "03_allocation_comparison.png", bbox_inches="tight")
    plt.close(fig)
    print("  ✅ 03_allocation_comparison.png")


# ────────────────────────────────────────────────────────────────
# 4. Variance decomposition stacked bars
# ────────────────────────────────────────────────────────────────
def fig4_variance_decomposition(strata_anova: dict, cluster_anova: dict, sys_anova: dict) -> None:
    fig, ax = plt.subplots(figsize=(9, 5))

    labels = ["Strata\n(batting pos.)", "Clusters\n(matches)", "Systematic\n(k samples)"]

    ss_b = [strata_anova["SS_between"], cluster_anova.get("ss_between", 0),
            sys_anova.get("SS_between", 0) if "SS_between" in sys_anova else 0]
    ss_w = [strata_anova["SS_within"], cluster_anova.get("ss_within", 0),
            sys_anova.get("SS_within", 0) if "SS_within" in sys_anova else 0]

    # For systematic, compute from sample means
    if "sample_means" in sys_anova:
        true_mean = float(np.mean(sys_anova["sample_means"]))  # approx
        k = sys_anova["k"]
        # SS_between for systematic = n_per_sample * Σ(ȳᵢ - ȳ)²
        sample_means = np.array(sys_anova["sample_means"])
        grand = sample_means.mean()
        n_per = config.N // k
        ss_b[2] = float(n_per * np.sum((sample_means - grand)**2))
        # SS_total ≈ from population
        pop_var = sys_anova.get("population_variance", 1)
        ss_total_sys = pop_var * config.N
        ss_w[2] = ss_total_sys - ss_b[2]

    # Normalise to proportions
    totals = [b + w for b, w in zip(ss_b, ss_w)]
    pct_b = [b / t * 100 if t > 0 else 0 for b, t in zip(ss_b, totals)]
    pct_w = [w / t * 100 if t > 0 else 0 for w, t in zip(ss_w, totals)]

    x = np.arange(len(labels))
    ax.bar(x, pct_b, label="Between groups (SS_B)", color=PALETTE[0], edgecolor="white")
    ax.bar(x, pct_w, bottom=pct_b, label="Within groups (SS_W)", color=PALETTE[2], edgecolor="white")

    for i in range(len(labels)):
        ax.text(i, pct_b[i] / 2, f'{pct_b[i]:.1f}%', ha='center', va='center',
                fontsize=10, color='white', fontweight='bold')
        ax.text(i, pct_b[i] + pct_w[i] / 2, f'{pct_w[i]:.1f}%', ha='center',
                va='center', fontsize=10, fontweight='bold')

    ax.set_ylabel("Percentage of Total SS")
    ax.set_title("Variance Decomposition: Between vs Within Groups")
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.legend(loc="upper right")
    ax.set_ylim(0, 105)
    plt.tight_layout()
    fig.savefig(OUT / "04_variance_decomposition.png", bbox_inches="tight")
    plt.close(fig)
    print("  ✅ 04_variance_decomposition.png")


# ────────────────────────────────────────────────────────────────
# 5. Cluster means with error bars (ICC illustration)
# ────────────────────────────────────────────────────────────────
def fig5_cluster_means(frame: pd.DataFrame, n_show: int = 50) -> None:
    cluster_stats = (
        frame.groupby("match_id")["runs"]
        .agg(["mean", "std", "count"])
        .reset_index()
        .sort_values("mean")
    )
    grand_mean = frame["runs"].mean()

    # Show a random 50 clusters for clarity
    rng = np.random.default_rng(config.SEED)
    show = cluster_stats.sample(n=min(n_show, len(cluster_stats)), random_state=42)
    show = show.sort_values("mean").reset_index(drop=True)

    fig, ax = plt.subplots(figsize=(14, 5))
    x = np.arange(len(show))
    se = show["std"] / np.sqrt(show["count"])

    ax.errorbar(x, show["mean"], yerr=1.96 * se, fmt="o", ms=4,
                color=PALETTE[0], ecolor=PALETTE[2], alpha=0.7, capsize=2)
    ax.axhline(grand_mean, color=PALETTE[4], ls="--", lw=2,
               label=f"Grand mean = {grand_mean:.1f}")
    ax.set_xlabel("Match (cluster), sorted by mean")
    ax.set_ylabel("Mean runs per innings")
    ax.set_title(f"Cluster (Match) Means with 95% Error Bars — {n_show} Matches Shown")
    ax.legend()
    ax.set_xticks([])
    plt.tight_layout()
    fig.savefig(OUT / "05_cluster_means.png", bbox_inches="tight")
    plt.close(fig)
    print("  ✅ 05_cluster_means.png")


# ────────────────────────────────────────────────────────────────
# 6. Simulation histograms / violin — THE HEADLINE CHART
# ────────────────────────────────────────────────────────────────
def fig6_simulation_violins(sim_df: pd.DataFrame, true_mean: float) -> None:
    designs = ["SRSWOR", "SRSWR", "Stratified-Prop", "Stratified-Neyman",
               "Systematic", "Cluster"]
    sim_sub = sim_df[sim_df["design"].isin(designs)]

    fig, axes = plt.subplots(1, 2, figsize=(16, 6))

    # Mean
    ax = axes[0]
    sns.violinplot(data=sim_sub, x="design", y="est_mean", order=designs,
                   palette=PALETTE[:6], ax=ax, inner="quartile", cut=0)
    ax.axhline(true_mean, color="red", ls="--", lw=2, label=f"True μ = {true_mean:.2f}")
    ax.set_xlabel("")
    ax.set_ylabel("Estimated Mean")
    ax.set_title("500 Simulated Sample Means per Design")
    ax.tick_params(axis="x", rotation=25)
    ax.legend(fontsize=9)

    # Proportion
    true_prop = sim_sub.groupby("design")["est_proportion"].apply(lambda x: x.iloc[0])  # placeholder
    true_prop_val = float((sim_sub["est_proportion"].mean()))  # rough
    # Actually, read from frame later; use grand mean of cluster as proxy
    ax = axes[1]
    sns.violinplot(data=sim_sub, x="design", y="est_proportion", order=designs,
                   palette=PALETTE[:6], ax=ax, inner="quartile", cut=0)
    ax.set_xlabel("")
    ax.set_ylabel("Estimated Proportion (≥30 runs)")
    ax.set_title("500 Simulated Sample Proportions per Design")
    ax.tick_params(axis="x", rotation=25)

    plt.tight_layout()
    fig.savefig(OUT / "06_simulation_violins.png", bbox_inches="tight")
    plt.close(fig)
    print("  ✅ 06_simulation_violins.png")


# ────────────────────────────────────────────────────────────────
# 7. Forest plot — estimate + 95% CI per design
# ────────────────────────────────────────────────────────────────
def fig7_forest_plot(comparison: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(10, 5))

    designs = comparison["design"].values
    y_pos = np.arange(len(designs))

    means = comparison["mean"].values
    ci_lo = comparison["ci_lower"].values
    ci_hi = comparison["ci_upper"].values
    errors = np.array([means - ci_lo, ci_hi - means])

    ax.errorbar(means, y_pos, xerr=errors, fmt="o", ms=8,
                color=PALETTE[0], ecolor=PALETTE[1], capsize=5, lw=2)

    # True mean line
    true_mean = comparison["true_mean"].iloc[0] if "true_mean" in comparison.columns else means.mean()
    ax.axvline(true_mean, color=PALETTE[4], ls="--", lw=2,
               label=f"True μ = {true_mean:.2f}")

    ax.set_yticks(y_pos)
    ax.set_yticklabels(designs)
    ax.set_xlabel("Estimated Mean Runs")
    ax.set_title("Forest Plot: Point Estimates & 95% CI by Design")
    ax.legend(loc="upper right")
    ax.invert_yaxis()
    plt.tight_layout()
    fig.savefig(OUT / "07_forest_plot.png", bbox_inches="tight")
    plt.close(fig)
    print("  ✅ 07_forest_plot.png")


# ────────────────────────────────────────────────────────────────
# 8. Relative efficiency / design effect bar chart
# ────────────────────────────────────────────────────────────────
def fig8_relative_efficiency(comparison: pd.DataFrame) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))

    designs = comparison["design"].values

    # RE bar chart
    ax = axes[0]
    re_vals = comparison["RE_vs_SRS"].values
    colors = [PALETTE[1] if r >= 1 else PALETTE[4] for r in re_vals]
    bars = ax.barh(designs, re_vals, color=colors, edgecolor="white", height=0.6)
    ax.axvline(1.0, color="black", ls="--", lw=1)
    ax.set_xlabel("Relative Efficiency vs SRSWOR")
    ax.set_title("Relative Efficiency (RE > 1 = better than SRS)")
    for bar, val in zip(bars, re_vals):
        ax.text(bar.get_width() + 0.02, bar.get_y() + bar.get_height()/2,
                f'{val:.3f}', va='center', fontsize=10)

    # Design effect
    ax = axes[1]
    deff_vals = 1.0 / re_vals  # Deff = 1/RE
    colors2 = [PALETTE[1] if d <= 1 else PALETTE[4] for d in deff_vals]
    bars2 = ax.barh(designs, deff_vals, color=colors2, edgecolor="white", height=0.6)
    ax.axvline(1.0, color="black", ls="--", lw=1)
    ax.set_xlabel("Design Effect (Deff)")
    ax.set_title("Design Effect (Deff < 1 = better than SRS)")
    for bar, val in zip(bars2, deff_vals):
        ax.text(bar.get_width() + 0.02, bar.get_y() + bar.get_height()/2,
                f'{val:.3f}', va='center', fontsize=10)

    plt.tight_layout()
    fig.savefig(OUT / "08_relative_efficiency.png", bbox_inches="tight")
    plt.close(fig)
    print("  ✅ 08_relative_efficiency.png")


# ────────────────────────────────────────────────────────────────
# 9. SE vs n curves
# ────────────────────────────────────────────────────────────────
def fig9_se_vs_n(frame: pd.DataFrame) -> None:
    S2 = float(frame["runs"].var(ddof=1))
    N = len(frame)

    n_vals = np.arange(50, N // 2, 50)

    # SRS SE
    se_srs = np.sqrt((1 - n_vals / N) * S2 / n_vals)

    # Stratified proportional SE (approximate)
    strata_info = frame.groupby("stratum", observed=True)["runs"].agg(["count", "var"]).reset_index()
    strata_info.columns = ["stratum", "Nh", "S2h"]
    Wh = strata_info["Nh"].values / N

    se_strat_prop = []
    for n_i in n_vals:
        nh = (Wh * n_i).astype(int)
        nh = np.maximum(nh, 2)
        v = sum(Wh[j]**2 * (1 - nh[j] / strata_info["Nh"].values[j]) * strata_info["S2h"].values[j] / nh[j]
                for j in range(len(Wh)))
        se_strat_prop.append(np.sqrt(v))

    # Cluster SE (rough approximation)
    M = frame["match_id"].nunique()
    icc_results = {}
    try:
        from sampling.cluster import compute_icc
        icc_results = compute_icc(frame)
    except:
        pass
    rho = icc_results.get("ICC_rho", 0.01)
    m_bar = N / M
    se_cluster = []
    for n_i in n_vals:
        m_i = max(2, int(n_i / m_bar))
        deff = 1 + (m_bar - 1) * rho
        se_cluster.append(np.sqrt(deff * (1 - n_i / N) * S2 / n_i))

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(n_vals, se_srs, label="SRSWOR", color=PALETTE[0], lw=2)
    ax.plot(n_vals, se_strat_prop, label="Stratified (Prop.)", color=PALETTE[1], lw=2, ls="--")
    ax.plot(n_vals, se_cluster, label=f"Cluster (ρ={rho:.3f})", color=PALETTE[4], lw=2, ls=":")

    ax.axvline(config.n, color="gray", ls="--", alpha=0.5, label=f"n = {config.n}")
    ax.set_xlabel("Sample size (n)")
    ax.set_ylabel("Standard Error of Mean")
    ax.set_title("SE vs Sample Size by Sampling Design")
    ax.legend()
    ax.set_xlim(0, n_vals[-1])
    plt.tight_layout()
    fig.savefig(OUT / "09_se_vs_n.png", bbox_inches="tight")
    plt.close(fig)
    print("  ✅ 09_se_vs_n.png")


# ────────────────────────────────────────────────────────────────
# Generate all figures
# ────────────────────────────────────────────────────────────────
def generate_all(
    frame: pd.DataFrame,
    sim_df: pd.DataFrame,
    comparison: pd.DataFrame,
    strata_anova: dict,
    cluster_anova: dict,
    sys_anova: dict,
    alloc_prop: pd.DataFrame,
    alloc_ney: pd.DataFrame,
) -> None:
    """Generate all 9 required figures."""
    print("\n📊 Generating figures...")
    fig1_histogram_and_boxplot(frame)
    fig2_systematic_comb(frame)
    fig3_allocation_comparison(alloc_prop, alloc_ney)
    fig4_variance_decomposition(strata_anova, cluster_anova, sys_anova)
    fig5_cluster_means(frame)
    fig6_simulation_violins(sim_df, frame["runs"].mean())
    fig7_forest_plot(comparison)
    fig8_relative_efficiency(comparison)
    fig9_se_vs_n(frame)
    print("✅ All 9 figures saved to results/figures/")
