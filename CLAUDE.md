# CLAUDE.md — Developer & Architecture Guidelines

## Project Architecture
This repository implements a rigorous 50-mark university group mini-project: **"Design, Estimation and Efficiency Comparison of Sampling Techniques on IPL Batting Data (2008–2024)"**.

### Core Modules
- `config.py`: Central configuration. Contains all global parameters (`N`, `n`, `k`, `SEED`, `ALPHA`, `PALETTE`, paths). **Never hard-code numbers in sampling logic.**
- `sampling/frame.py`: Ingestion, franchise and venue canonicalisation, batting position derivation, and data-quality audit log.
- `sampling/estimators.py`: Pure mathematical estimation functions for mean, total, proportion, finite population correction, confidence intervals, relative efficiency, and design effects.
- `sampling/srs.py`: Simple random sampling without replacement (SRSWOR) and with replacement (SRSWR).
- `sampling/stratified.py`: Proportional and Neyman optimal allocations using largest-remainder integer rounding; combined stratified estimators.
- `sampling/systematic.py`: 1-in-k systematic sampling on sorted frame, complete enumeration of all $k$ starting points, periodicity diagnosis.
- `sampling/cluster.py`: Single-stage cluster sampling (clusters = matches) with unequal cluster sizes; ratio estimator for mean; ANOVA mean squares and intra-cluster correlation (ICC, $\rho$).
- `sampling/tests.py`: One-way ANOVA tests across strata, clusters, and systematic samples; two-sample F-tests on design variance ratios; normality tests.
- `sampling/simulation.py`: Monte Carlo simulation engine (500 replications) measuring empirical bias, variance, SE, RMSE, and 95% CI coverage.
- `sampling/comparison.py`: Formats the unified cross-design comparison table.
- `sampling/figures.py`: Generates the 9 required figures at 300 DPI using color-blind safe palettes.
- `app/streamlit_app.py`: Interactive 4-tab Streamlit dashboard with Plotly charts.

---

## Coding Standards & Rules
1. **Python 3.11+ Style:** Use modern typing (`tuple[float, float]`, `list[int]`, `dict[str, Any]`, `np.ndarray`, `pd.DataFrame`).
2. **Textbook Formulas in Docstrings:** Every statistical function must explicitly state the textbook formula implemented (citing Cochran 1977, Singh & Chaudhary, or Des Raj).
3. **Reproducibility:** Never use unseeded random operations or bare `np.random.seed()`. Always pass an explicit seeded generator: `np.random.default_rng(config.SEED)`.
4. **No Hard-Coded Analysis Values:** All numbers flow dynamically from `config.py` and the computed sampling frame.
5. **No Data Fabrication:** Every reported statistic, variance, F-value, and p-value must be directly calculated from data.

---

## Command Reference
- Run test suite: `python3 -m pytest tests/ -v`
- Run master pipeline: `python3 run_all.py`
- Export Excel and image tables: `python3 export_tables.py`
- Regenerate Jupyter notebooks: `python3 generate_notebooks.py`
- Regenerate markdown reports: `python3 generate_reports_clean.py`
- Launch Streamlit application: `streamlit run app/streamlit_app.py`
