#!/usr/bin/env python3
"""
run_all.py — Master runner that generates all results, tables, and figures.

Usage:  python3 run_all.py
"""

import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import numpy as np
import pandas as pd
from pathlib import Path

import config
from sampling.frame import build_frame, load_frame
from sampling import srs, stratified, systematic, cluster, estimators as est
from sampling.tests import run_all_tests, f_test_variance_ratio, normality_check
from sampling.simulation import run_simulation, summarise_simulation
from sampling.comparison import build_comparison_table

TABLES = Path(config.TABLES_DIR)
TABLES.mkdir(parents=True, exist_ok=True)


def main():
    print("=" * 70)
    print("  IPL SAMPLING PROJECT — MASTER RUN")
    print("=" * 70)

    # ── 1. Build frame ─────────────────────────────────────────
    print("\n📋 Step 1: Building sampling frame...")
    frame, quality_log = build_frame()
    N = len(frame)
    true_mean  = float(frame["runs"].mean())
    true_total = float(frame["runs"].sum())
    true_prop  = float((frame["runs"] >= 30).mean())

    print(f"   N = {N:,}")
    print(f"   True mean = {true_mean:.4f}")
    print(f"   True total = {true_total:,.0f}")
    print(f"   True proportion (≥30) = {true_prop:.4f}")

    # Save quality log
    ql_df = pd.DataFrame([
        {"metric": k, "value": str(v)}
        for k, v in quality_log.items()
        if not isinstance(v, dict)
    ])
    ql_df.to_csv(TABLES / "data_quality_log.csv", index=False)

    # ── 2. Sample size justification ──────────────────────────
    print("\n📐 Step 2: Sample size justification...")
    S = float(frame["runs"].std(ddof=1))
    P = true_prop
    ss_just = srs.sample_size_justification(S, P, N)
    print(f"   {ss_just['interpretation']}")
    pd.DataFrame([ss_just]).to_csv(TABLES / "sample_size_justification.csv", index=False)

    # ── 3. SRS (SRSWOR vs SRSWR) ──────────────────────────────
    print("\n🎲 Step 3: SRSWOR vs SRSWR...")
    comparison_srs = srs.compare_wor_wr(frame, rng=np.random.default_rng(config.SEED))
    for method in ["srswor", "srswr"]:
        a = comparison_srs[method]
        print(f"   {method.upper()}: mean={a['mean']:.4f}, SE={a['se_mean']:.4f}, "
              f"CI=({a['ci_mean'][0]:.2f}, {a['ci_mean'][1]:.2f})")
    print(f"   Var ratio theory (N-n)/(N-1) = {comparison_srs['var_ratio_theory']:.6f}")

    # ── 4. Stratified ─────────────────────────────────────────
    print("\n📊 Step 4: Stratified sampling...")
    alloc_prop = stratified.compute_allocation(frame, config.n, "proportional")
    alloc_prop.attrs["method"] = "proportional"
    alloc_ney = stratified.compute_allocation(frame, config.n, "neyman")
    alloc_ney.attrs["method"] = "neyman"

    print("   Proportional allocation:", alloc_prop[["stratum", "Nh", "nh"]].to_dict("records"))
    print("   Neyman allocation:", alloc_ney[["stratum", "Nh", "nh"]].to_dict("records"))

    alloc_prop.to_csv(TABLES / "allocation_proportional.csv", index=False)
    alloc_ney.to_csv(TABLES / "allocation_neyman.csv", index=False)

    # Draw & analyse
    s_sp = stratified.draw_stratified(frame, alloc_prop, rng=np.random.default_rng(config.SEED + 2))
    a_sp = stratified.analyse_stratified(s_sp, frame, alloc_prop, N, true_mean, true_total, true_prop)

    s_sn = stratified.draw_stratified(frame, alloc_ney, rng=np.random.default_rng(config.SEED + 3))
    a_sn = stratified.analyse_stratified(s_sn, frame, alloc_ney, N, true_mean, true_total, true_prop)

    var_srs_ref = comparison_srs["srswor"]["var_mean"]
    for label, a in [("Proportional", a_sp), ("Neyman", a_sn)]:
        gain = stratified.variance_gain(var_srs_ref, a["var_mean"])
        print(f"   {label}: mean={a['mean']:.4f}, SE={a['se_mean']:.4f}, {gain['interpretation']}")

    # ── 5. Systematic ─────────────────────────────────────────
    print("\n📏 Step 5: Systematic sampling...")
    emp_sys = systematic.empirical_variance_across_starts(frame, config.k)
    print(f"   k={config.k}, n={emp_sys['n_per_sample']}")
    print(f"   Var(systematic) = {emp_sys['var_systematic_mean']:.6f}")
    print(f"   Var(SRS)        = {emp_sys['var_srs_mean']:.6f}")
    print(f"   RE vs SRS       = {emp_sys['relative_efficiency_vs_srs']:.4f}")

    pd.DataFrame({
        "start": range(config.k),
        "mean": emp_sys["sample_means"],
        "proportion": emp_sys["sample_proportions"],
    }).to_csv(TABLES / "systematic_all_starts.csv", index=False)

    # ── 6. Cluster ────────────────────────────────────────────
    print("\n🏏 Step 6: Cluster sampling...")
    icc_match = cluster.compute_icc(frame, "match_id")
    print(f"   ICC (match) = {icc_match['ICC_rho']:.4f}")
    print(f"   Design effect = {icc_match['design_effect']:.2f}")
    print(f"   {icc_match['interpretation']}")

    icc_venue = cluster.compute_venue_icc(frame)
    print(f"   ICC (venue) = {icc_venue['ICC_rho']:.4f} (for contrast)")

    pd.DataFrame([{
        "cluster_type": "match",
        **{k: v for k, v in icc_match.items() if k != "interpretation"}
    }, {
        "cluster_type": "venue",
        **{k: v for k, v in icc_venue.items() if k != "interpretation"}
    }]).to_csv(TABLES / "icc_results.csv", index=False)

    # ── 7. ANOVA & F-tests ────────────────────────────────────
    print("\n🧪 Step 7: ANOVA & F-tests...")
    test_results = run_all_tests(frame)
    for name, res in test_results.items():
        f_val = res.get('F_value') or res.get('W_statistic', 0)
        p_val = res.get('p_value', 0)
        print(f"   {res['test']}: stat={f_val:.4f}, "
              f"p={p_val:.4e} → {res['decision'][:50]}...")

    # F-test: SRS vs Stratified variance
    f_srs_strat = f_test_variance_ratio(
        var_srs_ref, a_sp["var_mean"],
        config.n - 1, config.n - 1,
        "SRSWOR", "Stratified-Prop"
    )
    print(f"   F-test SRS vs Strat: F={f_srs_strat['F_value']:.4f}, p={f_srs_strat['p_value']:.4e}")

    # Save test results
    test_rows = []
    for name, res in test_results.items():
        test_rows.append({
            "test": res["test"],
            "H0": res["H0"],
            "F_value": res.get("F_value"),
            "p_value": res.get("p_value"),
            "decision": res["decision"],
        })
    test_rows.append({
        "test": f_srs_strat["test"],
        "H0": f_srs_strat["H0"],
        "F_value": f_srs_strat["F_value"],
        "p_value": f_srs_strat["p_value"],
        "decision": f_srs_strat["decision"],
    })
    pd.DataFrame(test_rows).to_csv(TABLES / "statistical_tests.csv", index=False)

    # ── 8. Monte Carlo Simulation ─────────────────────────────
    print(f"\n🎰 Step 8: Monte Carlo simulation ({config.N_SIM} reps)...")
    sim_df = run_simulation(frame, config.N_SIM, config.SEED, save=True)
    sim_summary = summarise_simulation(sim_df, true_mean, true_prop)
    sim_summary.to_csv(TABLES / "simulation_summary.csv", index=False)
    print(sim_summary[["design", "emp_mean_of_means", "bias_mean", "se_mean",
                        "coverage_mean", "RE_mean_vs_SRS"]].to_string(index=False))

    # ── 9. Comparison Table ───────────────────────────────────
    print("\n📋 Step 9: Building comparison table...")
    comp = build_comparison_table(frame, save=True)
    print(comp[["design", "mean", "se_mean", "ci_lower", "ci_upper",
                "RE_vs_SRS", "abs_error_mean"]].to_string(index=False))

    # ── 10. Figures ───────────────────────────────────────────
    print("\n📊 Step 10: Generating all figures...")
    from sampling.figures import generate_all
    generate_all(
        frame, sim_df, comp,
        test_results["strata_anova"],
        test_results["cluster_anova_match"],
        test_results["systematic_anova"],
        alloc_prop, alloc_ney,
    )

    # ── Done ──────────────────────────────────────────────────
    print("\n" + "=" * 70)
    print("  ✅ ALL DONE — Results in results/tables/ and results/figures/")
    print("=" * 70)


if __name__ == "__main__":
    main()
