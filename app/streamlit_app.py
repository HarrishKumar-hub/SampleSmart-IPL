"""
Streamlit App — IPL Sampling Techniques Interactive Explorer

Four tabs, one per team member:
  Tab 1: Population & SRS (Member 1)
  Tab 2: Stratified Sampling (Member 2)
  Tab 3: Systematic Sampling (Member 3)
  Tab 4: Cluster + Comparison (Member 4)

Run:  streamlit run app/streamlit_app.py
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

import config
from sampling.frame import load_frame, build_frame
from sampling import srs, stratified, systematic, cluster, estimators as est
from sampling.tests import anova_strata, anova_clusters, anova_systematic, normality_check
from sampling.simulation import run_simulation, summarise_simulation

# ────────────────────────────────────────────────────────────────
# Page config
# ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="IPL Sampling Techniques",
    page_icon="🏏",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for a polished look
st.markdown("""
<style>
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] {
        padding: 10px 20px;
        background-color: #f0f2f6;
        border-radius: 8px 8px 0 0;
        font-weight: 600;
    }
    .stTabs [aria-selected="true"] {
        background-color: #264653;
        color: white;
    }
    .metric-card {
        background: linear-gradient(135deg, #264653 0%, #2A9D8F 100%);
        padding: 20px;
        border-radius: 12px;
        color: white;
        text-align: center;
    }
    div[data-testid="stMetric"] {
        background-color: #f8f9fa;
        border: 1px solid #e9ecef;
        padding: 15px;
        border-radius: 10px;
    }
</style>
""", unsafe_allow_html=True)


# ────────────────────────────────────────────────────────────────
# Load data (cached)
# ────────────────────────────────────────────────────────────────
@st.cache_data
def get_frame():
    try:
        return load_frame()
    except FileNotFoundError:
        frame, _ = build_frame()
        return frame

frame = get_frame()
N = len(frame)
TRUE_MEAN  = float(frame["runs"].mean())
TRUE_TOTAL = float(frame["runs"].sum())
TRUE_PROP  = float((frame["runs"] >= 30).mean())

# ────────────────────────────────────────────────────────────────
# Header
# ────────────────────────────────────────────────────────────────
st.markdown("# 🏏 IPL Batting Sampling Techniques Explorer")
st.markdown("**Design, Estimation and Efficiency Comparison of Sampling Techniques on IPL Batting Data (2008–2024)**")
st.markdown("---")

# ────────────────────────────────────────────────────────────────
# Tabs
# ────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Population & SRS",
    "📈 Stratified Sampling",
    "📏 Systematic Sampling",
    "🏟️ Cluster + Comparison",
])


# ================================================================
# TAB 1: Population & SRS (Member 1)
# ================================================================
with tab1:
    st.header("Population Overview & Simple Random Sampling")

    # Population metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Population Size (N)", f"{N:,}")
    with col2:
        st.metric("True Mean", f"{TRUE_MEAN:.2f} runs")
    with col3:
        st.metric("True SD", f"{frame['runs'].std(ddof=0):.2f}")
    with col4:
        st.metric("Prop. ≥ 30 runs", f"{TRUE_PROP:.1%}")

    st.markdown("---")

    # Histogram
    col_left, col_right = st.columns(2)
    with col_left:
        fig_hist = px.histogram(
            frame, x="runs", nbins=50,
            title="Distribution of Runs per Batter-Innings",
            color_discrete_sequence=["#264653"],
            labels={"runs": "Runs scored", "count": "Frequency"},
        )
        fig_hist.add_vline(x=TRUE_MEAN, line_dash="dash", line_color="#E76F51",
                           annotation_text=f"Mean = {TRUE_MEAN:.1f}")
        fig_hist.update_layout(height=400)
        st.plotly_chart(fig_hist, use_container_width=True)

    with col_right:
        fig_box = px.box(
            frame, x="stratum", y="runs",
            title="Runs by Batting Position Stratum",
            color="stratum",
            color_discrete_sequence=config.PALETTE[:4],
            category_orders={"stratum": config.STRATA_LABELS},
        )
        fig_box.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig_box, use_container_width=True)

    # SRS controls
    st.markdown("### 🎲 Simple Random Sampling")

    n_slider = st.slider("Sample size (n)", min_value=50, max_value=5000,
                         value=config.n, step=50, key="srs_n")

    col_wor, col_wr = st.columns(2)

    with col_wor:
        st.markdown("#### SRSWOR (Without Replacement)")
        s_wor = srs.draw_srswor(frame, n_slider, rng=np.random.default_rng(config.SEED))
        a_wor = srs.analyse_srs(s_wor, N, "srswor", TRUE_MEAN, TRUE_TOTAL, TRUE_PROP)

        c1, c2, c3 = st.columns(3)
        c1.metric("Estimated Mean", f"{a_wor['mean']:.2f}")
        c2.metric("SE", f"{a_wor['se_mean']:.4f}")
        c3.metric("Abs Error", f"{a_wor['abs_error_mean']:.4f}")
        st.write(f"**95% CI:** ({a_wor['ci_mean'][0]:.2f}, {a_wor['ci_mean'][1]:.2f})")
        st.write(f"**FPC:** {a_wor['fpc']:.4f}")

    with col_wr:
        st.markdown("#### SRSWR (With Replacement)")
        s_wr = srs.draw_srswr(frame, n_slider, rng=np.random.default_rng(config.SEED + 1))
        a_wr = srs.analyse_srs(s_wr, N, "srswr", TRUE_MEAN, TRUE_TOTAL, TRUE_PROP)

        c1, c2, c3 = st.columns(3)
        c1.metric("Estimated Mean", f"{a_wr['mean']:.2f}")
        c2.metric("SE", f"{a_wr['se_mean']:.4f}")
        c3.metric("Abs Error", f"{a_wr['abs_error_mean']:.4f}")
        st.write(f"**95% CI:** ({a_wr['ci_mean'][0]:.2f}, {a_wr['ci_mean'][1]:.2f})")

    # Variance ratio
    ratio = est.var_ratio_wor_wr(n_slider, N)
    st.info(f"**Variance Ratio (SRSWOR / SRSWR):** (N−n)/(N−1) = {ratio:.6f}  →  "
            f"SRSWOR is always more precise. At n={n_slider}, variance reduction = {(1-ratio)*100:.2f}%")

    # Sample size justification
    with st.expander("📐 Sample Size Justification"):
        S = float(frame["runs"].std(ddof=1))
        margin = est.achieved_margin(n_slider, S, N)
        st.write(f"At n = {n_slider}, achieved margin of error for the mean: **±{margin:.2f} runs** (95% CI)")
        st.write(f"n₀ = (z·S/e)² = ({config.Z}×{S:.2f}/e)²")
        st.write(f"With FPC: n = n₀/(1 + n₀/N)")


# ================================================================
# TAB 2: Stratified Sampling (Member 2)
# ================================================================
with tab2:
    st.header("Stratified Random Sampling")

    method = st.radio("Allocation method:", ["Proportional", "Neyman"],
                      horizontal=True, key="strat_method")

    alloc = stratified.compute_allocation(
        frame, config.n, method.lower()
    )
    alloc.attrs["method"] = method.lower()

    # Allocation table
    st.markdown("### Allocation Table")
    st.dataframe(
        alloc[["stratum", "Nh", "Wh", "Sh", "nh"]].style.format({
            "Wh": "{:.4f}", "Sh": "{:.2f}", "nh": "{:.0f}"
        }),
        use_container_width=True,
    )

    # Allocation comparison chart
    alloc_p = stratified.compute_allocation(frame, config.n, "proportional")
    alloc_n = stratified.compute_allocation(frame, config.n, "neyman")

    fig_alloc = go.Figure()
    fig_alloc.add_trace(go.Bar(
        name="Proportional", x=alloc_p["stratum"], y=alloc_p["nh"],
        marker_color="#2A9D8F", text=alloc_p["nh"], textposition="outside",
    ))
    fig_alloc.add_trace(go.Bar(
        name="Neyman", x=alloc_n["stratum"], y=alloc_n["nh"],
        marker_color="#E76F51", text=alloc_n["nh"], textposition="outside",
    ))
    fig_alloc.update_layout(
        title="Proportional vs Neyman Allocation",
        barmode="group", height=400,
        yaxis_title="Sample size (nₕ)",
    )
    st.plotly_chart(fig_alloc, use_container_width=True)

    # Draw & analyse
    s_strat = stratified.draw_stratified(frame, alloc, rng=np.random.default_rng(config.SEED))
    a_strat = stratified.analyse_stratified(s_strat, frame, alloc, N, TRUE_MEAN, TRUE_TOTAL, TRUE_PROP)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Combined Mean (ȳ_st)", f"{a_strat['mean']:.4f}")
    col2.metric("SE", f"{a_strat['se_mean']:.4f}")
    col3.metric("Abs Error", f"{a_strat.get('abs_error_mean', 0):.4f}")
    col4.metric("Proportion ≥30", f"{a_strat['proportion']:.4f}")

    st.write(f"**95% CI for mean:** ({a_strat['ci_mean'][0]:.2f}, {a_strat['ci_mean'][1]:.2f})")

    # Variance gain
    var_srs_est = est.var_srswor(frame["runs"].values[:config.n], N)
    # Use analytic SRS variance for comparison
    S2 = float(frame["runs"].var(ddof=1))
    var_srs_analytic = (1 - config.n / N) * S2 / config.n
    gain = stratified.variance_gain(var_srs_analytic, a_strat["var_mean"])
    st.success(f"**{gain['interpretation']}**")

    # Strata boxplots
    fig_strata = px.violin(
        frame, x="stratum", y="runs",
        color="stratum",
        category_orders={"stratum": config.STRATA_LABELS},
        color_discrete_sequence=config.PALETTE[:4],
        title="Distribution of Runs by Stratum",
        box=True, points=False,
    )
    fig_strata.update_layout(height=400, showlegend=False)
    st.plotly_chart(fig_strata, use_container_width=True)

    # ANOVA
    with st.expander("🧪 ANOVA: Strata Mean Differences"):
        anova_res = anova_strata(frame)
        st.write(f"**H₀:** {anova_res['H0']}")
        st.write(f"**H₁:** {anova_res['H1']}")
        st.write(f"**F = {anova_res['F_value']:.2f}, p = {anova_res['p_value']:.4e}**")
        st.write(f"**η² = {anova_res['eta_squared']:.4f}** (effect size)")
        st.write(f"→ {anova_res['decision']}")


# ================================================================
# TAB 3: Systematic Sampling (Member 3)
# ================================================================
with tab3:
    st.header("Systematic Sampling")

    col_k, col_start = st.columns(2)
    with col_k:
        # Only allow divisors of N
        divisors = [i for i in range(2, 100) if N % i == 0]
        k_choice = st.selectbox("Interval (k):", divisors,
                                index=divisors.index(config.k) if config.k in divisors else 0,
                                key="sys_k")
    with col_start:
        start_choice = st.slider("Starting point (r):", 0, k_choice - 1, 0, key="sys_start")

    n_sys = N // k_choice
    st.write(f"**n = N/k = {N}/{k_choice} = {n_sys}**")

    # Draw & analyse
    s_sys = systematic.draw_systematic(frame, k=k_choice, start=start_choice)
    a_sys = systematic.analyse_systematic(s_sys, frame, k=k_choice, N=N,
                                          true_mean=TRUE_MEAN, true_total=TRUE_TOTAL, true_prop=TRUE_PROP)

    col1, col2, col3 = st.columns(3)
    col1.metric("Mean", f"{a_sys['mean']:.4f}")
    col2.metric("SE", f"{a_sys['se_mean']:.4f}")
    col3.metric("Abs Error", f"{a_sys.get('abs_error_mean', 0):.4f}")

    st.write(f"**95% CI:** ({a_sys['ci_mean'][0]:.2f}, {a_sys['ci_mean'][1]:.2f})")

    # Comb plot
    show_n = min(300, N)
    x_vals = list(range(show_n))
    y_vals = frame["runs"].values[:show_n].tolist()
    picks = list(range(start_choice, show_n, k_choice))

    fig_comb = go.Figure()
    fig_comb.add_trace(go.Bar(x=x_vals, y=y_vals, name="Population",
                              marker_color="#D3D3D3", width=1))
    fig_comb.add_trace(go.Bar(
        x=picks, y=[frame["runs"].values[i] for i in picks],
        name=f"Systematic (r={start_choice})",
        marker_color="#264653", width=1,
    ))
    fig_comb.update_layout(
        title=f"Systematic Sampling Comb (k={k_choice}, r={start_choice}) — First {show_n} units",
        xaxis_title="Frame index", yaxis_title="Runs",
        height=350, barmode="overlay",
    )
    st.plotly_chart(fig_comb, use_container_width=True)

    # All starting points
    with st.expander(f"📊 Analysis across all {k_choice} starting points"):
        emp = systematic.empirical_variance_across_starts(frame, k=k_choice)
        st.write(f"Var(systematic) = {emp['var_systematic_mean']:.6f}")
        st.write(f"Var(SRS) = {emp['var_srs_mean']:.6f}")
        st.write(f"RE vs SRS = {emp['relative_efficiency_vs_srs']:.4f}")

        fig_starts = go.Figure()
        fig_starts.add_trace(go.Bar(
            x=list(range(k_choice)), y=emp["sample_means"],
            marker_color="#2A9D8F", name="Sample mean",
        ))
        fig_starts.add_hline(y=TRUE_MEAN, line_dash="dash", line_color="red",
                             annotation_text=f"True mean = {TRUE_MEAN:.2f}")
        fig_starts.update_layout(
            title=f"Sample Means across all {k_choice} starting points",
            xaxis_title="Starting point (r)", yaxis_title="Sample mean",
            height=350,
        )
        st.plotly_chart(fig_starts, use_container_width=True)

    # ANOVA
    with st.expander("🧪 ANOVA: Systematic Sample Differences"):
        sys_anova = anova_systematic(frame, k=k_choice)
        st.write(f"**H₀:** {sys_anova['H0']}")
        st.write(f"**F = {sys_anova['F_value']:.4f}, p = {sys_anova['p_value']:.4e}**")
        st.write(f"→ {sys_anova['decision']}")
        st.write(f"💡 {sys_anova['periodicity_comment']}")


# ================================================================
# TAB 4: Cluster + Comparison (Member 4)
# ================================================================
with tab4:
    st.header("Cluster Sampling & Design Comparison")

    tab4a, tab4b, tab4c = st.tabs(["🏟️ Cluster Sampling", "📋 Comparison", "🎰 Simulation"])

    with tab4a:
        M_total = frame["match_id"].nunique()
        m_default = max(2, round(config.n / (N / M_total)))

        m_select = st.slider("Number of clusters (m):", 5, min(200, M_total),
                             value=m_default, key="cl_m")

        s_cl, m_actual = cluster.draw_cluster_sample(frame, m=m_select,
                                                     rng=np.random.default_rng(config.SEED))
        a_cl = cluster.analyse_cluster(s_cl, frame, m_actual, "match_id", N,
                                       TRUE_MEAN, TRUE_TOTAL, TRUE_PROP)

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Ratio Estimate ȳ_c", f"{a_cl['mean']:.4f}")
        col2.metric("SE", f"{a_cl['se_mean']:.4f}")
        col3.metric("Actual n", f"{a_cl['n_actual']:,}")
        col4.metric("Abs Error", f"{a_cl.get('abs_error_mean', 0):.4f}")

        # ICC
        icc = cluster.compute_icc(frame)
        st.info(f"**ICC (ρ) = {icc['ICC_rho']:.4f}** | Design Effect = {icc['design_effect']:.2f} | "
                f"MSB = {icc['MSB']:.2f} | MSW = {icc['MSW']:.2f}")

        # Cluster means chart
        cluster_means = s_cl.groupby("match_id")["runs"].mean().sort_values()
        fig_cl = go.Figure()
        fig_cl.add_trace(go.Bar(
            x=list(range(len(cluster_means))),
            y=cluster_means.values,
            marker_color="#264653",
        ))
        fig_cl.add_hline(y=TRUE_MEAN, line_dash="dash", line_color="#E76F51",
                         annotation_text=f"True mean = {TRUE_MEAN:.2f}")
        fig_cl.update_layout(
            title=f"Cluster Means (m = {m_actual} matches)",
            xaxis_title="Cluster (sorted)", yaxis_title="Mean runs",
            height=350,
        )
        st.plotly_chart(fig_cl, use_container_width=True)

    with tab4b:
        st.markdown("### Comparison Table — All Designs")
        try:
            comp = pd.read_csv(f"{config.TABLES_DIR}/comparison_table.csv")
        except FileNotFoundError:
            from sampling.comparison import build_comparison_table
            comp = build_comparison_table(frame, save=True)

        display_cols = ["design", "n", "mean", "se_mean", "ci_lower", "ci_upper",
                        "proportion", "RE_vs_SRS", "abs_error_mean"]
        st.dataframe(
            comp[display_cols].style.format({
                "mean": "{:.4f}", "se_mean": "{:.4f}",
                "ci_lower": "{:.2f}", "ci_upper": "{:.2f}",
                "proportion": "{:.4f}", "RE_vs_SRS": "{:.4f}",
                "abs_error_mean": "{:.4f}",
            }).background_gradient(subset=["RE_vs_SRS"], cmap="RdYlGn"),
            use_container_width=True,
        )

        # Forest plot
        fig_forest = go.Figure()
        for i, row in comp.iterrows():
            fig_forest.add_trace(go.Scatter(
                x=[row["mean"]], y=[row["design"]],
                error_x=dict(type="data",
                             array=[row["ci_upper"] - row["mean"]],
                             arrayminus=[row["mean"] - row["ci_lower"]]),
                mode="markers",
                marker=dict(size=12, color=config.PALETTE[i % len(config.PALETTE)]),
                name=row["design"],
            ))
        fig_forest.add_vline(x=TRUE_MEAN, line_dash="dash", line_color="red",
                             annotation_text=f"True μ = {TRUE_MEAN:.2f}")
        fig_forest.update_layout(
            title="Forest Plot: Estimates ± 95% CI",
            xaxis_title="Estimated Mean", height=400,
            showlegend=False,
        )
        st.plotly_chart(fig_forest, use_container_width=True)

        # RE bar chart
        fig_re = px.bar(
            comp, x="RE_vs_SRS", y="design", orientation="h",
            color="RE_vs_SRS",
            color_continuous_scale=["#E76F51", "#E9C46A", "#2A9D8F"],
            title="Relative Efficiency vs SRSWOR",
        )
        fig_re.add_vline(x=1.0, line_dash="dash", line_color="black")
        fig_re.update_layout(height=350)
        st.plotly_chart(fig_re, use_container_width=True)

    with tab4c:
        st.markdown("### 🎰 Monte Carlo Simulation")

        n_sims = st.selectbox("Number of simulations:", [100, 200, 500],
                              index=2, key="n_sims")

        if st.button("▶️ Run Simulation", key="run_sim", type="primary"):
            with st.spinner(f"Running {n_sims} simulations..."):
                sim_df = run_simulation(frame, n_sim=n_sims, seed=config.SEED, save=False)
                sim_summary = summarise_simulation(sim_df, TRUE_MEAN, TRUE_PROP)

                # Violin plot
                fig_violin = px.violin(
                    sim_df, x="design", y="est_mean",
                    color="design",
                    color_discrete_sequence=config.PALETTE[:6],
                    title=f"Simulated Sample Means ({n_sims} reps per design)",
                    box=True,
                )
                fig_violin.add_hline(y=TRUE_MEAN, line_dash="dash", line_color="red",
                                     annotation_text=f"True μ = {TRUE_MEAN:.2f}")
                fig_violin.update_layout(height=500, showlegend=False)
                st.plotly_chart(fig_violin, use_container_width=True)

                # Summary table
                st.markdown("#### Simulation Summary")
                st.dataframe(
                    sim_summary.style.format({
                        "emp_mean_of_means": "{:.4f}", "bias_mean": "{:.4f}",
                        "se_mean": "{:.4f}", "rmse_mean": "{:.4f}",
                        "coverage_mean": "{:.3f}", "RE_mean_vs_SRS": "{:.4f}",
                    }).background_gradient(subset=["RE_mean_vs_SRS"], cmap="RdYlGn"),
                    use_container_width=True,
                )
        else:
            st.write("Click the button above to run the Monte Carlo simulation.")

            # Try to load pre-computed results
            try:
                sim_df = pd.read_parquet("results/simulation.parquet")
                sim_summary = summarise_simulation(sim_df, TRUE_MEAN, TRUE_PROP)

                fig_violin = px.violin(
                    sim_df, x="design", y="est_mean",
                    color="design",
                    color_discrete_sequence=config.PALETTE[:6],
                    title=f"Pre-computed Simulated Sample Means ({config.N_SIM} reps)",
                    box=True,
                )
                fig_violin.add_hline(y=TRUE_MEAN, line_dash="dash", line_color="red",
                                     annotation_text=f"True μ = {TRUE_MEAN:.2f}")
                fig_violin.update_layout(height=500, showlegend=False)
                st.plotly_chart(fig_violin, use_container_width=True)

                st.dataframe(
                    sim_summary.style.format({
                        "emp_mean_of_means": "{:.4f}", "bias_mean": "{:.4f}",
                        "se_mean": "{:.4f}", "rmse_mean": "{:.4f}",
                        "coverage_mean": "{:.3f}", "RE_mean_vs_SRS": "{:.4f}",
                    }).background_gradient(subset=["RE_mean_vs_SRS"], cmap="RdYlGn"),
                    use_container_width=True,
                )
            except FileNotFoundError:
                st.write("No pre-computed simulation results found. Run the simulation first.")


# ────────────────────────────────────────────────────────────────
# Sidebar info
# ────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ℹ️ About")
    st.markdown("""
    **IPL Sampling Techniques Project**

    A group mini-project comparing five sampling
    designs on real IPL batting data (2008–2024).

    **Population:** {:,} batter-innings
    **Study variable:** Runs per innings
    **Sample size:** n = {:,}

    ---
    **Team Members:**
    1. Frame, SRS, Sample Size
    2. Stratified Sampling
    3. Systematic Sampling
    4. Cluster & Comparison
    """.format(N, config.n))

    st.markdown("---")
    st.markdown(f"**True Mean:** {TRUE_MEAN:.4f}")
    st.markdown(f"**True Total:** {TRUE_TOTAL:,.0f}")
    st.markdown(f"**True Proportion (≥30):** {TRUE_PROP:.4f}")
