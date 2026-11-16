"""
comparison.py — Build the unified comparison table across all designs.

One row per design: estimate, SE, 95% CI, RE vs SRS, absolute error.
"""

from __future__ import annotations
from pathlib import Path

import numpy as np
import pandas as pd

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import config
from sampling import estimators as est, srs, stratified, systematic, cluster


def build_comparison_table(frame: pd.DataFrame, save: bool = True) -> pd.DataFrame:
    """
    Run every sampling design once and build the comparison table.
    """
    N = len(frame)
    true_mean  = float(frame["runs"].mean())
    true_total = float(frame["runs"].sum())
    true_prop  = float((frame["runs"] >= 30).mean())

    rng = np.random.default_rng(config.SEED)

    # ── SRSWOR ─────────────────────────────────────────────────
    s_wor = srs.draw_srswor(frame, config.n, rng=np.random.default_rng(config.SEED))
    a_wor = srs.analyse_srs(s_wor, N, "srswor", true_mean, true_total, true_prop)

    # ── SRSWR ──────────────────────────────────────────────────
    s_wr = srs.draw_srswr(frame, config.n, rng=np.random.default_rng(config.SEED + 1))
    a_wr = srs.analyse_srs(s_wr, N, "srswr", true_mean, true_total, true_prop)

    # ── Stratified Proportional ────────────────────────────────
    alloc_p = stratified.compute_allocation(frame, config.n, "proportional")
    alloc_p.attrs["method"] = "proportional"
    s_sp = stratified.draw_stratified(frame, alloc_p, rng=np.random.default_rng(config.SEED + 2))
    a_sp = stratified.analyse_stratified(s_sp, frame, alloc_p, N, true_mean, true_total, true_prop)

    # ── Stratified Neyman ──────────────────────────────────────
    alloc_n = stratified.compute_allocation(frame, config.n, "neyman")
    alloc_n.attrs["method"] = "neyman"
    s_sn = stratified.draw_stratified(frame, alloc_n, rng=np.random.default_rng(config.SEED + 3))
    a_sn = stratified.analyse_stratified(s_sn, frame, alloc_n, N, true_mean, true_total, true_prop)

    # ── Systematic ─────────────────────────────────────────────
    s_sys = systematic.draw_systematic(frame, config.k, start=0)
    a_sys = systematic.analyse_systematic(s_sys, frame, config.k, N, true_mean, true_total, true_prop)

    # ── Cluster ────────────────────────────────────────────────
    s_cl, m_cl = cluster.draw_cluster_sample(frame, rng=np.random.default_rng(config.SEED + 5))
    a_cl = cluster.analyse_cluster(s_cl, frame, m_cl, "match_id", N, true_mean, true_total, true_prop)

    # ── Reference SRS variance ─────────────────────────────────
    var_srs = a_wor["var_mean"]

    # ── Build table ────────────────────────────────────────────
    rows = []
    for label, a in [
        ("SRSWOR", a_wor),
        ("SRSWR", a_wr),
        ("Stratified-Prop", a_sp),
        ("Stratified-Neyman", a_sn),
        ("Systematic", a_sys),
        ("Cluster", a_cl),
    ]:
        rows.append({
            "design": label,
            "n": a.get("n", a.get("n_actual", config.n)),
            "mean": round(a["mean"], 4),
            "se_mean": round(a["se_mean"], 4),
            "ci_lower": round(a["ci_mean"][0], 4),
            "ci_upper": round(a["ci_mean"][1], 4),
            "var_mean": a["var_mean"],
            "proportion": round(a["proportion"], 4),
            "se_prop": round(a["se_prop"], 4),
            "total": round(a["total"], 0),
            "abs_error_mean": round(a.get("abs_error_mean", 0), 4),
            "abs_error_prop": round(a.get("abs_error_prop", 0), 4),
            "RE_vs_SRS": round(var_srs / a["var_mean"], 4) if a["var_mean"] > 0 else float("inf"),
            "true_mean": true_mean,
            "true_total": true_total,
            "true_prop": true_prop,
        })

    comp = pd.DataFrame(rows)

    if save:
        Path(config.TABLES_DIR).mkdir(parents=True, exist_ok=True)
        comp.to_csv(f"{config.TABLES_DIR}/comparison_table.csv", index=False)
        print(f"✅ Comparison table saved → {config.TABLES_DIR}/comparison_table.csv")

    return comp


if __name__ == "__main__":
    from sampling.frame import load_frame

    frame = load_frame()
    comp = build_comparison_table(frame)

    print("\n" + "=" * 100)
    print("COMPARISON TABLE — ALL DESIGNS")
    print("=" * 100)
    display_cols = ["design", "n", "mean", "se_mean", "ci_lower", "ci_upper",
                    "proportion", "RE_vs_SRS", "abs_error_mean"]
    print(comp[display_cols].to_string(index=False))
