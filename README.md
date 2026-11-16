# 🏏 Design, Estimation and Efficiency Comparison of Sampling Techniques on IPL Batting Data (2008–2024)

> **University Sampling Techniques Group Mini-Project (50 Marks)**  
> **Course:** Sampling Theory & Survey Design  
> **Evaluation Tier:** Senior Statistician + Python Engineering Specification  

---

## 📌 Executive Summary

This project applies five fundamental sampling designs to an empirical population of **16,515 batter-innings** from the Indian Premier League (2008–2024) derived from genuine Cricsheet records.

Because the complete population is known, we assess both **analytical design expectations** and **empirical sampling distributions** via a **500-repetition Monte Carlo simulation**, tracking bias, variance, standard errors, 95% confidence interval coverage, and relative efficiency ($RE = V_{\text{SRS}} / V_{\text{design}}$).

### Key Empirical Findings:
1. **Neyman Stratification Dominates:** Stratification by batting order position with Neyman optimal allocation reduces sampling variance by **42.2%** over SRSWOR (**$RE = 1.4224$**), substantially outperforming proportional allocation (**$RE = 1.3426$**).
2. **The Systematic Periodicity Penalty:** Systematic sampling using interval $k = 15$ incurs a precision penalty (**$RE = 0.8532$**) because $k = 15$ closely matches the natural match innings size ($\approx 15.08$ batters per match), repeatedly sampling similar batting positions.
3. **Cluster Sampling & Design Effect:** Single-stage match clustering exhibits a positive intra-cluster correlation (**$\rho = +0.0109$**) and a Design Effect of **$Deff = 1.15$**, demonstrating why national statistical systems (e.g., NSO/MoSPI) scale sample sizes to accommodate cluster homogeneity.

---

## 👥 4-Person Team Distribution

| Role & Lead | Core Modules | Jupyter Notebook | Streamlit App Tab | Report Sections |
|:---|:---|:---|:---|:---|
| **Member 1** | `sampling/frame.py`, `sampling/srs.py`, `config.py` | `01_frame_and_srs.ipynb` | **Tab 1:** Population & SRS | §1 Introduction & Frame, §2 SRSWOR/SRSWR, Data Quality Log |
| **Member 2** | `sampling/stratified.py` | `02_stratified.ipynb` | **Tab 2:** Stratified Sampling | §3 Stratified Allocation & ANOVA |
| **Member 3** | `sampling/systematic.py`, `sampling/figures.py` | `03_systematic.ipynb` | **Tab 3:** Systematic Sampling | §4 Systematic Sampling & Periodicity Analysis, All Figures |
| **Member 4** | `sampling/cluster.py`, `sampling/tests.py`, `simulation.py`, `comparison.py` | `04_cluster_comparison.ipynb` | **Tab 4:** Cluster & Comparison | §5 Cluster Sampling & ICC, §6 Comparison & Simulation, §7 MoSPI Context |

---

## 📊 Master Comparison Table ($n = 1,101$)

| Sampling Design | Achieved $n$ | Estimated Mean | SE(Mean) | 95% Confidence Interval | Prop $\ge 30$ | SE(Prop) | Abs Error | RE vs. SRS (Sample) | RE vs. SRS (Simulation) |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **SRSWOR** | 1,101 | 18.2770 | 0.5719 | [17.16, 19.40] | 0.2225 | 0.0121 | 1.6926 | **1.0000** | **1.0000** |
| **SRSWR** | 1,101 | 19.3206 | 0.6283 | [18.09, 20.55] | 0.2352 | 0.0128 | 0.6490 | 0.8285 | 0.9939 |
| **Stratified (Prop.)** | 1,101 | 20.4315 | 0.6044 | [19.25, 21.62] | 0.2460 | 0.0119 | 0.4619 | 0.8954 | **1.3426** |
| **Stratified (Neyman)** | 1,101 | 20.3287 | 0.5461 | [19.26, 21.40] | 0.2526 | 0.0115 | **0.3591** | **1.0969** | **1.4224** |
| **Systematic ($k=15$)** | 1,101 | 20.6576 | 0.6352 | [19.41, 21.90] | 0.2661 | 0.0129 | 0.6880 | 0.8107 | 0.8532 |
| **Cluster (Match)** | 1,125 | 19.0507 | 0.5602 | [17.95, 20.15] | 0.2293 | 0.0108 | 0.9189 | 1.0422 | 0.9586 |

*True Population Parameters:*  
- Mean $\mu = 19.9696$ runs  
- Population Standard Deviation $\sigma = 21.3509$ runs ($S = 21.3516$)  
- Total Runs $\tau = 329,798$ runs  
- Proportion $\ge 30$ Runs $P = 0.2488$ ($24.88\%$)  

---

## 🎰 Monte Carlo Simulation (500 Replications)

| Design | Empirical Mean | Empirical Bias | Empirical SE | RMSE | 95% CI Coverage | Empirical RE vs SRS |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| **Stratified (Neyman)** | 19.9978 | +0.0282 | **0.5349** | **0.5351** | **95.2%** | **1.4224** |
| **Stratified (Prop.)** | 19.9882 | +0.0186 | 0.5506 | 0.5504 | 95.4% | **1.3426** |
| **SRSWOR** | 19.9973 | +0.0277 | 0.6380 | 0.6379 | 95.8% | 1.0000 |
| **SRSWR** | 19.9823 | +0.0127 | 0.6399 | 0.6394 | 94.0% | 0.9939 |
| **Cluster (Match)** | 20.0160 | +0.0464 | 0.6516 | 0.6526 | 96.0% | 0.9586 |
| **Systematic ($k=15$)** | 19.9510 | -0.0186 | 0.6907 | 0.6903 | 94.0% | 0.8532 |

---

## 📁 Repository Structure

```
sampling_mini_project/
├── config.py                  # Single source of truth (N, n, k, seed, strata bins, alpha)
├── requirements.txt           # Pinned dependencies
├── README.md                  # Project overview, documentation and run instructions
├── CLAUDE.md                  # Developer guidelines and codebase conventions
├── run_all.py                 # Master pipeline: frame -> sampling -> tests -> simulation -> figures
├── export_tables.py           # Exports comparison_table.xlsx and formatted PNG image
├── generate_notebooks.py      # Generates 4 student Jupyter notebooks
├── generate_reports_clean.py  # Populates report markdown files from tables/*.csv
├── data/
│   ├── raw/                   # Raw deliveries.csv (260,920 rows) & matches.csv (1,095 rows)
│   └── processed/             # Cleaned frame.parquet & frame.csv (16,515 rows)
├── sampling/                  # Core statistical library
│   ├── __init__.py            # Package interface
│   ├── frame.py               # Frame construction, cleaning, and quality auditing
│   ├── estimators.py          # Cochran formulas: mean, total, proportion, CI, FPC, Deff
│   ├── srs.py                 # SRSWOR / SRSWR algorithms & sample size derivation
│   ├── stratified.py          # Proportional & Neyman allocations, stratified estimators
│   ├── systematic.py          # 1-in-k systematic sampling, k-start enumeration, periodicity
│   ├── cluster.py             # Single-stage cluster sampling, ratio estimators, ICC (rho)
│   ├── tests.py               # One-way ANOVA (strata, cluster, systematic) & F-tests
│   ├── simulation.py          # 500-run Monte Carlo simulation engine
│   ├── comparison.py          # Unified cross-design comparison builder
│   └── figures.py             # Publication-grade figures (300 DPI, color-blind safe)
├── notebooks/                 # 4 Interactive Student Jupyter Notebooks
│   ├── 01_frame_and_srs.ipynb
│   ├── 02_stratified.ipynb
│   ├── 03_systematic.ipynb
│   └── 04_cluster_comparison.ipynb
├── app/
│   └── streamlit_app.py       # Interactive Streamlit application (4 tabs with Plotly)
├── results/
│   ├── figures/               # 9 PNG figures + comparison_table.png (300 DPI)
│   └── tables/                # CSV and Excel output summaries
├── tests/
│   └── test_estimators.py     # 20 Pytest unit & regression tests
└── report/                    # 8 Markdown section skeletons + MASTER_REPORT.md
```

---

## 🚀 Quickstart & Execution Guide

### 1. Environment Setup
```bash
# Clone and enter directory
cd sampling_mini_project

# Install pinned dependencies
pip install -r requirements.txt
```

### 2. Run the Full Analytical Pipeline
Executes frame construction, sample size justification, all 5 sampling designs, ANOVA tests, 500-run Monte Carlo simulation, comparison table export, and all 9 publication figures:
```bash
python3 run_all.py
python3 export_tables.py
```

### 3. Run Pytest Suite
Verifies all statistical estimators against textbook proofs and verifies that simulation variance matches analytic variance within tolerance:
```bash
python3 -m pytest tests/ -v
```

### 4. Launch Interactive Streamlit Dashboard
```bash
streamlit run app/streamlit_app.py
```

---

## 📈 Visualisations Catalog (`results/figures/`)

1. `01_histogram_boxplot.png`: Distribution of runs per innings with stratum boxplots.
2. `02_systematic_comb.png`: The 1-in-15 systematic sample comb plot showing index selection.
3. `03_allocation_comparison.png`: Proportional vs. Neyman allocation across the 4 strata.
4. `04_variance_decomposition.png`: Percentage of variance between vs. within groups.
5. `05_cluster_means.png`: 50 randomly sampled cluster (match) means with 95% error bars.
6. `06_simulation_violins.png`: Violin plots of 500 simulated sample means per design (Headline Chart).
7. `07_forest_plot.png`: Forest plot showing 95% confidence intervals per design.
8. `08_relative_efficiency.png`: Relative efficiency and design effect bar charts.
9. `09_se_vs_n.png`: Standard error vs. sample size curves across designs.
10. `comparison_table.png`: Publication-ready styled comparison table.

---

## 📚 References & Theoretical Foundations
- **Cochran, W. G. (1977).** *Sampling Techniques* (3rd ed.). John Wiley & Sons.
- **Singh, D., & Chaudhary, F. S. (1986).** *Theory and Analysis of Sample Survey Designs*. New Age International.
- **Des Raj, & Chandhok, P. (1998).** *Sample Survey Theory*. Narosa Publishing House.
- **Wolter, K. M. (2007).** *Introduction to Variance Estimation* (2nd ed.). Springer.
- **Government of India, MoSPI / NSO (2023).** *Sample Design and Estimation Procedure of the Periodic Labour Force Survey (PLFS)*.
