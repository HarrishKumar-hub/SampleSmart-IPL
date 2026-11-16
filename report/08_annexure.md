# Section 8: Annexure — Technical Specifications, Codebase & Data Listings
**Project:** Design, Estimation and Efficiency Comparison of Sampling Techniques on IPL Batting Data (2008–2024)

---

## 8.1 Software Environment & Pinned Dependencies
The codebase was developed under Python 3.11+ using strictly pinned package environments:
- `pandas>=2.1.0`
- `numpy>=1.26.0`
- `scipy>=1.12.0`
- `statsmodels>=0.14.0`
- `matplotlib>=3.8.0`
- `seaborn>=0.13.0`
- `plotly>=5.18.0`
- `streamlit>=1.31.0`
- `pytest>=8.0.0`
- `pyarrow>=15.0.0`
- `openpyxl>=3.1.0`

---

## 8.2 Reproducibility Protocol
Every random draw throughout the project is governed by seeded NumPy generators (`default_rng(seed)`), guaranteeing byte-for-byte reproducibility:
- Master Seed: `SEED = 42`
- Common Sample Size: `n = 1101`
- Systematic Interval: `k = 15`
- Significance Level: `ALPHA = 0.05`
- Monte Carlo Replications: `N_SIM = 500`

To reproduce all tables, figures, tests, and reports:
```bash
python3 run_all.py
python3 export_tables.py
pytest tests/
streamlit run app/streamlit_app.py
```

---

## 8.3 File Catalog & Output Artifacts
### Results Directory:
- `results/tables/comparison_table.csv` & `.xlsx`
- `results/tables/simulation_summary.csv`
- `results/tables/statistical_tests.csv`
- `results/tables/data_quality_log.csv`
- `results/tables/icc_results.csv`
- `results/tables/sample_size_justification.csv`
- `results/tables/systematic_all_starts.csv`
- `results/figures/01_histogram_boxplot.png`
- `results/figures/02_systematic_comb.png`
- `results/figures/03_allocation_comparison.png`
- `results/figures/04_variance_decomposition.png`
- `results/figures/05_cluster_means.png`
- `results/figures/06_simulation_violins.png`
- `results/figures/07_forest_plot.png`
- `results/figures/08_relative_efficiency.png`
- `results/figures/09_se_vs_n.png`
- `results/figures/comparison_table.png`
