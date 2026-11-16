"""
generate_notebooks.py — Creates the 4 required student notebooks in notebooks/
with clean code, markdown explanations, and pre-configured execution cells.
"""

import json
from pathlib import Path

def create_notebook(cells):
    return {
        "cells": cells,
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3"
            },
            "language_info": {
                "name": "python",
                "version": "3.11.0"
            }
        },
        "nbformat": 4,
        "nbformat_minor": 5
    }

def md_cell(text):
    return {
        "cell_type": "markdown",
        "metadata": {},
        "source": [line + "\n" for line in text.strip().split("\n")]
    }

def code_cell(code):
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [line + "\n" for line in code.strip().split("\n")]
    }

def build_all_notebooks():
    nb_dir = Path("notebooks")
    nb_dir.mkdir(parents=True, exist_ok=True)

    # =========================================================================
    # Notebook 1: Frame and SRS (Member 1)
    # =========================================================================
    nb1_cells = [
        md_cell(r"""# 🏏 Member 1: Sampling Frame Construction & Simple Random Sampling (SRSWOR vs SRSWR)
**Project:** Design, Estimation and Efficiency Comparison of Sampling Techniques on IPL Batting Data (2008–2024)

### Objectives:
1. Construct the unified sampling frame from raw deliveries and match records (innings 1 & 2).
2. Clean and canonicalise franchise names, season identifiers, and venue names.
3. Verify target population metrics: $N = 16,515$, $\mu = 19.97$, $\sigma = 21.35$, $P(\\text{runs} \\ge 30) = 0.2488$.
4. Calculate sample size $n = 1,101$ with finite population correction (FPC).
5. Draw and compare Simple Random Sampling Without Replacement (SRSWOR) and With Replacement (SRSWR)."""),
        code_cell("""import sys, os
sys.path.insert(0, os.path.abspath(".."))

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

import config
from sampling.frame import build_frame, load_frame
from sampling import srs, estimators as est

print(f"Configured N: {config.N:,}, Common sample size n: {config.n:,}")"""),
        md_cell("""## 1. Frame Construction and Data Quality Verification"""),
        code_cell("""# Build or load the cleaned frame
frame, quality_log = build_frame(save=False)

print("Frame Shape:", frame.shape)
print("Unique Matches:", frame["match_id"].nunique())
print("True Mean Runs:", round(frame["runs"].mean(), 4))
print("True SD Runs (pop):", round(frame["runs"].std(ddof=0), 4))
print("True Proportion >= 30:", round((frame["runs"] >= 30).mean(), 4))
frame.head()"""),
        md_cell("""## 2. Sample Size Determination (Justifying $n = 1,101$)
Using Cochran's formula for a finite population:
$$n_0 = \\left( \\frac{z \\cdot S}{e} \\right)^2, \\quad n = \\frac{n_0}{1 + n_0 / N}$$
At $z = 1.96$ and $S \\approx 21.35$, setting margin $e = 1.22$ yields $n \\approx 1,101$."""),
        code_cell("""S = float(frame["runs"].std(ddof=1))
P = float((frame["runs"] >= 30).mean())

justification = srs.sample_size_justification(S, P, N=len(frame))
for k, v in justification.items():
    print(f"{k}: {v}")"""),
        md_cell("""## 3. SRSWOR vs SRSWR Estimation & Theoretical Ratio
Textbook variance ratio:
$$\\frac{V(\\bar{y}_{\\text{WOR}})}{V(\\bar{y}_{\\text{WR}})} = \\frac{N - n}{N - 1} \\approx 1 - f$$"""),
        code_cell("""comp_srs = srs.compare_wor_wr(frame, rng=np.random.default_rng(config.SEED))

print("=== SRSWOR Results ===")
for k in ["mean", "se_mean", "ci_mean", "var_mean", "fpc", "abs_error_mean"]:
    print(f"  {k}: {comp_srs['srswor'][k]}")

print("\\n=== SRSWR Results ===")
for k in ["mean", "se_mean", "ci_mean", "var_mean", "abs_error_mean"]:
    print(f"  {k}: {comp_srs['srswr'][k]}")

print(f"\\nTheoretical Variance Ratio (N-n)/(N-1): {comp_srs['var_ratio_theory']:.6f}")
print(f"Observed Variance Ratio: {comp_srs['var_ratio_observed']:.6f}")"""),
        md_cell("""## 4. Visualising the Population Distribution"""),
        code_cell("""fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# Histogram
axes[0].hist(frame["runs"], bins=50, color=config.PALETTE[0], edgecolor="white")
axes[0].axvline(frame["runs"].mean(), color="red", linestyle="--", label=f"Mean: {frame['runs'].mean():.2f}")
axes[0].set_title("Distribution of Runs per Batter-Innings")
axes[0].set_xlabel("Runs")
axes[0].set_ylabel("Frequency")
axes[0].legend()

# Boxplot by stratum
sns.boxplot(data=frame, x="stratum", y="runs", order=config.STRATA_LABELS, palette=config.PALETTE[:4], ax=axes[1])
axes[1].set_title("Runs by Batting Position Stratum")
axes[1].tick_params(axis="x", rotation=15)

plt.tight_layout()
plt.show()""")
    ]

    # =========================================================================
    # Notebook 2: Stratified Sampling (Member 2)
    # =========================================================================
    nb2_cells = [
        md_cell("""# 📊 Member 2: Stratified Random Sampling (Proportional vs Neyman Allocation)
**Project:** Design, Estimation and Efficiency Comparison of Sampling Techniques on IPL Batting Data (2008–2024)

### Objectives:
1. Define 4 strata using batting positions: Openers (1-2), Middle (3-5), Lower-Middle (6-7), Tail (8-11).
2. Compute Proportional ($n_h \\propto N_h$) and Neyman Optimal ($n_h \\propto N_h S_h$) allocations.
3. Draw stratified samples and calculate combined estimators $\\bar{y}_{st}$ and $V(\\bar{y}_{st})$.
4. Evaluate precision gains over Simple Random Sampling.
5. Conduct One-Way ANOVA across strata to test for differences in stratum means."""),
        code_cell("""import sys, os
sys.path.insert(0, os.path.abspath(".."))

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

import config
from sampling.frame import load_frame
from sampling import stratified, estimators as est
from sampling.tests import anova_strata

frame = load_frame()
print(f"Loaded frame with {len(frame):,} rows.")"""),
        md_cell("""## 1. Strata Characteristics and Allocations
Under Neyman allocation:
$$n_h = n \\cdot \\frac{N_h S_h}{\\sum N_h S_h}$$"""),
        code_cell("""alloc_prop = stratified.compute_allocation(frame, config.n, "proportional")
alloc_prop.attrs["method"] = "proportional"

alloc_neyman = stratified.compute_allocation(frame, config.n, "neyman")
alloc_neyman.attrs["method"] = "neyman"

comparison_alloc = pd.merge(
    alloc_prop[["stratum", "Nh", "Wh", "Sh", "nh"]].rename(columns={"nh": "nh_proportional"}),
    alloc_neyman[["stratum", "nh"]].rename(columns={"nh": "nh_neyman"}),
    on="stratum"
)
comparison_alloc"""),
        md_cell("""## 2. Drawing Stratified Samples & Estimation
Combined Stratified Mean and Variance:
$$\\bar{y}_{st} = \\sum_{h=1}^L W_h \\bar{y}_h, \\quad V(\\bar{y}_{st}) = \\sum_{h=1}^L W_h^2 \\left( 1 - \\frac{n_h}{N_h} \\right) \\frac{s_h^2}{n_h}$$"""),
        code_cell("""true_mean = float(frame["runs"].mean())
true_total = float(frame["runs"].sum())
true_prop = float((frame["runs"] >= 30).mean())

# Proportional
s_sp = stratified.draw_stratified(frame, alloc_prop, rng=np.random.default_rng(config.SEED + 2))
res_prop = stratified.analyse_stratified(s_sp, frame, alloc_prop, config.N, true_mean, true_total, true_prop)

# Neyman
s_sn = stratified.draw_stratified(frame, alloc_neyman, rng=np.random.default_rng(config.SEED + 3))
res_neyman = stratified.analyse_stratified(s_sn, frame, alloc_neyman, config.N, true_mean, true_total, true_prop)

# Reference SRS variance
var_srs = (1 - config.n / config.N) * float(frame["runs"].var(ddof=1)) / config.n

print("=== Proportional Allocation ===")
print(f"Mean: {res_prop['mean']:.4f}, SE: {res_prop['se_mean']:.4f}, 95% CI: {res_prop['ci_mean']}")
print(f"RE vs SRS: {var_srs / res_prop['var_mean']:.4f}")

print("\\n=== Neyman Allocation ===")
print(f"Mean: {res_neyman['mean']:.4f}, SE: {res_neyman['se_mean']:.4f}, 95% CI: {res_neyman['ci_mean']}")
print(f"RE vs SRS: {var_srs / res_neyman['var_mean']:.4f}")"""),
        md_cell("""## 3. One-Way ANOVA across Batting Position Strata"""),
        code_cell("""anova_res = anova_strata(frame)
print(f"Test: {anova_res['test']}")
print(f"F-value: {anova_res['F_value']:.4f}, p-value: {anova_res['p_value']:.4e}")
print(f"Eta-squared (η²): {anova_res['eta_squared']:.4f}")
print(f"Decision: {anova_res['decision']}")"""),
        md_cell("""## 4. Stratified Allocation Visualisation"""),
        code_cell("""x = np.arange(len(comparison_alloc))
width = 0.35

fig, ax = plt.subplots(figsize=(10, 5))
ax.bar(x - width/2, comparison_alloc["nh_proportional"], width, label="Proportional", color="#2A9D8F")
ax.bar(x + width/2, comparison_alloc["nh_neyman"], width, label="Neyman", color="#E76F51")
ax.set_xticks(x)
ax.set_xticklabels(comparison_alloc["stratum"])
ax.set_ylabel("Sample Size (n_h)")
ax.set_title("Stratified Allocation: Proportional vs Neyman")
ax.legend()
plt.tight_layout()
plt.show()""")
    ]

    # =========================================================================
    # Notebook 3: Systematic Sampling (Member 3)
    # =========================================================================
    nb3_cells = [
        md_cell("""# 📏 Member 3: Systematic Sampling & Periodicity Analysis
**Project:** Design, Estimation and Efficiency Comparison of Sampling Techniques on IPL Batting Data (2008–2024)

### Objectives:
1. Construct the sorted sampling frame: (date, match_id, inning, batting_position).
2. Justify sampling interval $k = 15$ ($N = 16,515 = 15 \\times 1,101$).
3. Draw a 1-in-15 systematic sample and compute single-sample estimators.
4. Enumerate all $k = 15$ possible systematic samples to obtain the exact empirical variance.
5. Diagnose periodicity resulting from $k \\approx 15$ matching the natural batting order per match.
6. Conduct One-Way ANOVA across systematic samples."""),
        code_cell("""import sys, os
sys.path.insert(0, os.path.abspath(".."))

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

import config
from sampling.frame import load_frame
from sampling import systematic, estimators as est
from sampling.tests import anova_systematic

frame = load_frame()
print(f"Frame sorted for systematic sampling. N = {len(frame):,}, k = {config.k}, n = {config.n}")"""),
        md_cell("""## 1. Single Systematic Sample Draw & Estimation"""),
        code_cell("""true_mean = float(frame["runs"].mean())
true_total = float(frame["runs"].sum())
true_prop = float((frame["runs"] >= 30).mean())

s_sys = systematic.draw_systematic(frame, k=config.k, start=0)
res_sys = systematic.analyse_systematic(s_sys, frame, k=config.k, N=config.N,
                                        true_mean=true_mean, true_total=true_total, true_prop=true_prop)

print(f"Systematic Sample Mean: {res_sys['mean']:.4f}")
print(f"SE (treat-as-SRS): {res_sys['se_mean']:.4f}")
print(f"Variance (successive differences): {res_sys['var_mean_succ_diff']:.6f}")
print(f"95% CI: ({res_sys['ci_mean'][0]:.2f}, {res_sys['ci_mean'][1]:.2f})")
print(f"Absolute Error: {res_sys['abs_error_mean']:.4f}")"""),
        md_cell("""## 2. Complete Enumeration across all $k = 15$ Starts
Because systematic sampling has exactly $k$ possible samples in the sample space, we can calculate the **exact population variance** of the estimator:
$$V(\\bar{y}_{sys}) = \\frac{1}{k} \\sum_{r=1}^k (\\bar{y}_r - \\bar{Y})^2$$"""),
        code_cell("""emp = systematic.empirical_variance_across_starts(frame, k=config.k)

print(f"Exact Systematic Variance V(y_sys): {emp['var_systematic_mean']:.6f}")
print(f"Analytic SRS Variance V(y_SRS):     {emp['var_srs_mean']:.6f}")
print(f"Relative Efficiency vs SRS:         {emp['relative_efficiency_vs_srs']:.4f}")
print(f"\\nPeriodicity insight:\\n{emp['periodicity_comment']}")

df_starts = pd.DataFrame({
    "start_r": range(config.k),
    "sample_mean": emp["sample_means"],
    "sample_prop": emp["sample_proportions"]
})
df_starts"""),
        md_cell("""## 3. ANOVA across Systematic Samples"""),
        code_cell("""sys_anova = anova_systematic(frame, k=config.k)
print(f"Test: {sys_anova['test']}")
print(f"F-value: {sys_anova['F_value']:.4f}, p-value: {sys_anova['p_value']:.4f}")
print(f"Decision: {sys_anova['decision']}")"""),
        md_cell("""## 4. Comb Visualisation (The 1-in-15 Pick Pattern)"""),
        code_cell("""show_n = 200
x = np.arange(show_n)
y = frame["runs"].values[:show_n]

fig, ax = plt.subplots(figsize=(14, 4))
ax.bar(x, y, color="#D3D3D3", width=1.0, label="Population Units")

colors = ["#264653", "#2A9D8F", "#E76F51"]
for i, start in enumerate([0, 5, 10]):
    picks = np.arange(start, show_n, config.k)
    ax.bar(picks, frame["runs"].values[picks], width=1.0, color=colors[i], alpha=0.85, label=f"Start r={start}")

ax.set_title(f"Systematic Sampling Comb (k = {config.k}): Selection Pattern")
ax.set_xlabel("Frame Index")
ax.set_ylabel("Runs")
ax.legend(loc="upper right")
plt.tight_layout()
plt.show()""")
    ]

    # =========================================================================
    # Notebook 4: Cluster & Comparison (Member 4)
    # =========================================================================
    nb4_cells = [
        md_cell("""# 🏟️ Member 4: Single-Stage Cluster Sampling & Unified Design Comparison
**Project:** Design, Estimation and Efficiency Comparison of Sampling Techniques on IPL Batting Data (2008–2024)

### Objectives:
1. Implement single-stage cluster sampling with clusters = matches ($M = 1,095$ clusters).
2. Compute the Ratio Estimator for mean $\\bar{y}_c$ and unbiased estimator for total.
3. Calculate Intraclass Correlation Coefficient (ICC, $\\rho$) from ANOVA mean squares.
4. Construct the unified comparison table across all 6 sampling designs.
5. Review Monte Carlo simulation (500 reps) results: Bias, SE, RMSE, and 95% CI coverage.
6. Conduct F-tests on design variance ratios."""),
        code_cell("""import sys, os
sys.path.insert(0, os.path.abspath(".."))

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

import config
from sampling.frame import load_frame
from sampling import cluster, estimators as est
from sampling.comparison import build_comparison_table
from sampling.simulation import summarise_simulation
from sampling.tests import anova_clusters, f_test_variance_ratio

frame = load_frame()
print(f"Loaded frame with {len(frame):,} rows and {frame['match_id'].nunique():,} match clusters.")"""),
        md_cell("""## 1. Cluster Sampling & Ratio Estimation
Because clusters have unequal sizes $m_i$, we use the ratio estimator:
$$\\bar{y}_c = \\frac{\\sum_{i=1}^m y_i}{\\sum_{i=1}^m m_i}$$"""),
        code_cell("""s_cl, m_actual = cluster.draw_cluster_sample(frame, rng=np.random.default_rng(config.SEED + 5))
res_cl = cluster.analyse_cluster(s_cl, frame, m_actual, "match_id", config.N,
                                 float(frame["runs"].mean()), float(frame["runs"].sum()), float((frame["runs"] >= 30).mean()))

print(f"Clusters Drawn: {m_actual} matches, Total units n_actual: {res_cl['n_actual']:,}")
print(f"Cluster Ratio Mean: {res_cl['mean']:.4f}, SE: {res_cl['se_mean']:.4f}")
print(f"95% CI: ({res_cl['ci_mean'][0]:.2f}, {res_cl['ci_mean'][1]:.2f})")
print(f"Unbiased Total: {res_cl['total']:,.0f}, SE: {res_cl['se_total']:,.0f}")"""),
        md_cell("""## 2. Intraclass Correlation (ICC) and Design Effect
From ANOVA mean squares:
$$\\hat{\\rho} = \\frac{MSB - MSW}{MSB + (\\bar{M}_0 - 1) MSW}, \\quad Deff = 1 + (\\bar{M}_0 - 1) \\hat{\\rho}$$"""),
        code_cell("""icc_match = cluster.compute_icc(frame, "match_id")
print("=== Match-Level Clustering ===")
print(f"ICC (ρ): {icc_match['ICC_rho']:.4f}")
print(f"Design Effect (Deff): {icc_match['design_effect']:.2f}")
print(f"MSB: {icc_match['MSB']:.4f}, MSW: {icc_match['MSW']:.4f}")
print(icc_match["interpretation"])

icc_venue = cluster.compute_venue_icc(frame)
print("\\n=== Venue-Level Clustering (Contrast) ===")
print(f"ICC (venue): {icc_venue['ICC_rho']:.4f}")"""),
        md_cell("""## 3. Master Cross-Design Comparison Table"""),
        code_cell("""comp_table = build_comparison_table(frame, save=False)
display_cols = ["design", "n", "mean", "se_mean", "ci_lower", "ci_upper", "proportion", "RE_vs_SRS", "abs_error_mean"]
comp_table[display_cols]"""),
        md_cell("""## 4. Monte Carlo Simulation Summary (500 Replications)"""),
        code_cell("""sim_df = pd.read_parquet("../results/simulation.parquet")
sim_summary = summarise_simulation(sim_df, float(frame["runs"].mean()), float((frame["runs"] >= 30).mean()))
sim_summary[["design", "emp_mean_of_means", "bias_mean", "se_mean", "rmse_mean", "coverage_mean", "RE_mean_vs_SRS"]]"""),
        md_cell("""## 5. Design Variance F-Tests"""),
        code_cell("""f_test = f_test_variance_ratio(
    comp_table[comp_table["design"]=="SRSWOR"]["var_mean"].iloc[0],
    comp_table[comp_table["design"]=="Stratified-Prop"]["var_mean"].iloc[0],
    config.n - 1, config.n - 1,
    "SRSWOR", "Stratified-Prop"
)
print(f"F-test: {f_test['test']}")
print(f"F-value: {f_test['F_value']:.4f}, p-value: {f_test['p_value']:.4e}")
print(f"Decision: {f_test['decision']}")""")
    ]

    notebooks = {
        "01_frame_and_srs.ipynb": nb1_cells,
        "02_stratified.ipynb": nb2_cells,
        "03_systematic.ipynb": nb3_cells,
        "04_cluster_comparison.ipynb": nb4_cells,
    }

    for name, cells in notebooks.items():
        path = nb_dir / name
        with open(path, "w", encoding="utf-8") as f:
            json.dump(create_notebook(cells), f, indent=2)
        print(f"✅ Generated notebook → {path}")

if __name__ == "__main__":
    build_all_notebooks()
