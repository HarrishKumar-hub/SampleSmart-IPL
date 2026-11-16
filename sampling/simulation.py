"""
simulation.py — Monte Carlo simulation (500 reps) for all sampling designs.

The standout feature of the project.

For each design, repeats 500 draws with a fixed seed, stores estimates,
and computes empirical bias, variance, SE, coverage, RMSE, and
relative efficiency vs SRS.

Ref: Robert & Casella (2004), Monte Carlo Statistical Methods.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from pathlib import Path

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import config
from sampling import estimators as est
from sampling import srs, stratified, systematic, cluster


def run_simulation(
    frame: pd.DataFrame,
    n_sim: int = config.N_SIM,
    seed: int = config.SEED,
    save: bool = True,
) -> pd.DataFrame:
    """
    Run Monte Carlo simulation for all sampling designs.

    For each of 500 replications, draw a sample under each design
    and record the estimated mean and proportion.

    Returns a long-form DataFrame with columns:
        design, rep, est_mean, est_proportion
    """
    rng = np.random.default_rng(seed)

    N = len(frame)
    true_mean = float(frame["runs"].mean())
    true_total = float(frame["runs"].sum())
    true_prop = float((frame["runs"] >= 30).mean())

    # Pre-compute allocations (fixed)
    alloc_prop  = stratified.compute_allocation(frame, config.n, "proportional")
    alloc_prop.attrs["method"] = "proportional"
    alloc_ney   = stratified.compute_allocation(frame, config.n, "neyman")
    alloc_ney.attrs["method"] = "neyman"

    # Cluster: compute m
    M = frame["match_id"].nunique()
    mean_cluster_size = N / M
    m_clusters = max(2, round(config.n / mean_cluster_size))

    records = []

    for rep in range(n_sim):
        # Fresh RNGs from the master sequence (ensures reproducibility)
        child_seed = rng.integers(0, 2**31)

        # ── SRSWOR ─────────────────────────────────────────────
        rng_wor = np.random.default_rng(child_seed)
        s_wor = srs.draw_srswor(frame, config.n, rng=rng_wor)
        records.append({
            "design": "SRSWOR", "rep": rep,
            "est_mean": float(s_wor["runs"].mean()),
            "est_proportion": float((s_wor["runs"] >= 30).mean()),
        })

        # ── SRSWR ──────────────────────────────────────────────
        rng_wr = np.random.default_rng(child_seed + 1)
        s_wr = srs.draw_srswr(frame, config.n, rng=rng_wr)
        records.append({
            "design": "SRSWR", "rep": rep,
            "est_mean": float(s_wr["runs"].mean()),
            "est_proportion": float((s_wr["runs"] >= 30).mean()),
        })

        # ── Stratified-Proportional ────────────────────────────
        rng_sp = np.random.default_rng(child_seed + 2)
        s_sp = stratified.draw_stratified(frame, alloc_prop, rng=rng_sp)
        a_sp = stratified.analyse_stratified(s_sp, frame, alloc_prop, N)
        records.append({
            "design": "Stratified-Prop", "rep": rep,
            "est_mean": a_sp["mean"],
            "est_proportion": a_sp["proportion"],
        })

        # ── Stratified-Neyman ──────────────────────────────────
        rng_sn = np.random.default_rng(child_seed + 3)
        s_sn = stratified.draw_stratified(frame, alloc_ney, rng=rng_sn)
        a_sn = stratified.analyse_stratified(s_sn, frame, alloc_ney, N)
        records.append({
            "design": "Stratified-Neyman", "rep": rep,
            "est_mean": a_sn["mean"],
            "est_proportion": a_sn["proportion"],
        })

        # ── Systematic ─────────────────────────────────────────
        rng_sys = np.random.default_rng(child_seed + 4)
        start = int(rng_sys.integers(0, config.k))
        s_sys = systematic.draw_systematic(frame, config.k, start=start)
        records.append({
            "design": "Systematic", "rep": rep,
            "est_mean": float(s_sys["runs"].mean()),
            "est_proportion": float((s_sys["runs"] >= 30).mean()),
        })

        # ── Cluster ────────────────────────────────────────────
        rng_cl = np.random.default_rng(child_seed + 5)
        s_cl, _ = cluster.draw_cluster_sample(frame, m=m_clusters, rng=rng_cl)
        total_y = s_cl["runs"].sum()
        total_m = len(s_cl)
        total_p = (s_cl["runs"] >= 30).sum()
        records.append({
            "design": "Cluster", "rep": rep,
            "est_mean": total_y / total_m,
            "est_proportion": total_p / total_m,
        })

    sim_df = pd.DataFrame(records)

    if save:
        Path("results").mkdir(parents=True, exist_ok=True)
        sim_df.to_parquet("results/simulation.parquet", index=False)

    return sim_df


def summarise_simulation(
    sim_df: pd.DataFrame,
    true_mean: float,
    true_prop: float,
    n: int = config.n,
    N: int = config.N,
) -> pd.DataFrame:
    """
    Summarise Monte Carlo results: bias, variance, SE, RMSE,
    coverage, and relative efficiency for each design.

    Coverage: proportion of replications where the true value
    falls within the 95% CI (ȳ ± 1.96 · empirical_SE).
    """
    summary_rows = []
    srs_var_mean = None
    srs_var_prop = None

    for design, grp in sim_df.groupby("design"):
        means = grp["est_mean"].values
        props = grp["est_proportion"].values

        # Mean estimates
        emp_mean = float(np.mean(means))
        bias_mean = emp_mean - true_mean
        var_mean = float(np.var(means, ddof=1))
        se_mean = float(np.sqrt(var_mean))
        rmse_mean = float(np.sqrt(np.mean((means - true_mean) ** 2)))

        # Coverage for mean
        ci_lower = means - config.Z * se_mean
        ci_upper = means + config.Z * se_mean
        coverage_mean = float(np.mean((ci_lower <= true_mean) & (true_mean <= ci_upper)))

        # Proportion estimates
        emp_prop = float(np.mean(props))
        bias_prop = emp_prop - true_prop
        var_prop = float(np.var(props, ddof=1))
        se_prop = float(np.sqrt(var_prop))
        rmse_prop = float(np.sqrt(np.mean((props - true_prop) ** 2)))

        ci_lower_p = props - config.Z * se_prop
        ci_upper_p = props + config.Z * se_prop
        coverage_prop = float(np.mean((ci_lower_p <= true_prop) & (true_prop <= ci_upper_p)))

        if design == "SRSWOR":
            srs_var_mean = var_mean
            srs_var_prop = var_prop

        summary_rows.append({
            "design": design,
            # Mean
            "emp_mean_of_means": round(emp_mean, 4),
            "bias_mean": round(bias_mean, 4),
            "var_mean": round(var_mean, 6),
            "se_mean": round(se_mean, 4),
            "rmse_mean": round(rmse_mean, 4),
            "coverage_mean": round(coverage_mean, 4),
            # Proportion
            "emp_mean_of_props": round(emp_prop, 4),
            "bias_prop": round(bias_prop, 4),
            "var_prop": round(var_prop, 8),
            "se_prop": round(se_prop, 4),
            "rmse_prop": round(rmse_prop, 4),
            "coverage_prop": round(coverage_prop, 4),
        })

    summary = pd.DataFrame(summary_rows)

    # Relative efficiency vs SRSWOR
    if srs_var_mean is not None:
        summary["RE_mean_vs_SRS"] = round(srs_var_mean / summary["var_mean"], 4)
        summary["RE_prop_vs_SRS"] = round(srs_var_prop / summary["var_prop"], 4)

    return summary


if __name__ == "__main__":
    from sampling.frame import load_frame

    print("Loading frame...")
    frame = load_frame()
    true_mean = float(frame["runs"].mean())
    true_prop = float((frame["runs"] >= 30).mean())

    print(f"Running {config.N_SIM} simulations...")
    sim_df = run_simulation(frame)
    print(f"Simulation complete. {len(sim_df)} records.")

    summary = summarise_simulation(sim_df, true_mean, true_prop)

    Path(config.TABLES_DIR).mkdir(parents=True, exist_ok=True)
    summary.to_csv(f"{config.TABLES_DIR}/simulation_summary.csv", index=False)

    print("\n" + "=" * 80)
    print("MONTE CARLO SIMULATION SUMMARY")
    print("=" * 80)
    print(summary.to_string(index=False))
    print(f"\nTrue mean: {true_mean:.4f}")
    print(f"True proportion (≥30): {true_prop:.4f}")
